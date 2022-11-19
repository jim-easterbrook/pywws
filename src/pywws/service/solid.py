# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018-22  pywws contributors

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Upload data to your Solid Pod.

Solid is a specification that lets people store their data securely in decentralized data stores called Pods.

* Create account: https://solidproject.org/users/get-a-pod#get-a-pod-from-a-pod-provider
* Create OAuth client at https://login.inrupt.com/
* API: `<https://solidproject.org/TR/protocol>`_
* Additional dependency: http://docs.python-requests.org/
* Additional dependency: https://github.com/RDFLib/rdflib#installation
* Example ``weather.ini`` configuration::

    [solid]
    client_id = a262fake-14c3-4a4d-ad0b-221e86bb0504
    client_secret = c7dcfake-c136-4ffd-b8ef-be13a3f5ac34
    token_endpoint = https://login.inrupt.com/token
    slug = latest.ttl
    sensor_uri = https://github.com/jim-easterbrook/pywws
    container_uri = https://storage.inrupt.com/5115fa88-56b2-4473-a819-e6a00f6ebdbf/pywws/


    [logged]
    services = ['solid']

    [live]
    services = ['solid']

.. _Solid Project: https://solidproject.org/

"""

from __future__ import absolute_import, unicode_literals

import logging
import os
import sys
from contextlib import contextmanager
from datetime import datetime

import pywws.service
import requests
from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.CatchupDataService):

    config = {
        "client_id": ("", True, None),
        "client_secret": ("", True, None),
        "token_endpoint": ("https://login.inrupt.com/token", False, None),
        "container_uri": ("", True, None),
        "slug": ("latest.ttl", False, None),
        "content_type": ("text/turtle", False, None),
        "sensor_uri": ("https://github.com/jim-easterbrook/pywws", False, None),
    }
    template = """
#live#
#timezone utc#
#idx          "'dateutc'     : '%Y-%m-%d %H:%M:%S',"#
#temp_out          "'temperature'     : '%.1f',"#
#rain          "'rain'     : '%.1f',"#
"""
    logger = logger
    service_name = service_name

    __access_token = None

    def __generate_access_token(self) -> str:
        """Authenticate with a Solid OIDC server and generate an access token to use with the storage service"""

        client_id = self.context.params.get(service_name, "client_id")
        client_secret = self.context.params.get(service_name, "client_secret")
        token_endpoint = self.context.params.get(service_name, "token_endpoint")

        if self.__access_token:
            self.logger.info(f"Re-generating access token at {token_endpoint}")
        else:
            self.logger.info(f"Generating access token at {token_endpoint}")
            

        response = requests.post(
            token_endpoint,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()

        self.__access_token = response.json()["access_token"]

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session, "OK"

    def __describe_observations_as_graph(self, observation_identity: str, prepared_data: dict) -> Graph:
        """Generate a graph to represent the observations"""
        g = Graph()
        SOSA = Namespace("http://www.w3.org/ns/sosa/")
        g.bind("sosa", SOSA)

        QUDTUNIT = Namespace("http://qudt.org/vocab/unit/")
        g.bind("qudt-unit-1-1", QUDTUNIT)

        sensor_uri = self.context.params.get(service_name, "sensor_uri")
        sensor = URIRef(sensor_uri)

        resultTime = Literal(datetime.utcnow().isoformat() + "+00:00", datatype=XSD.dateTime)

        phenomenonTimePython = datetime.strptime(prepared_data["dateutc"], "%Y-%m-%d %H:%M:%S")
        phenomenonTime = Literal(phenomenonTimePython.isoformat() + "+00:00", datatype=XSD.dateTime)

        observation = URIRef(f"Observation/{observation_identity}#temperature")
        g.add((observation, RDF.type, SOSA.Observation))
        g.add(
            (
                observation,
                SOSA.hasSimpleResult,
                Literal(prepared_data["temperature"], datatype=QUDTUNIT.DEG_C),
            )
        )
        g.add((observation, SOSA.madeBySensor, sensor))
        g.add((observation, SOSA.resultTime, resultTime))
        g.add((observation, SOSA.phenomenonTime, phenomenonTime))

        observation = URIRef(f"Observation/{observation_identity}#rain_1h")
        g.add((observation, RDF.type, SOSA.Observation))
        g.add(
            (
                observation,
                SOSA.hasSimpleResult,
                Literal(prepared_data["rain"], datatype=QUDTUNIT.MilliM),
            )
        )
        g.add((observation, SOSA.madeBySensor, sensor))
        g.add((observation, SOSA.resultTime, resultTime))
        g.add((observation, SOSA.phenomenonTime, phenomenonTime))

        return g

    def __consider_retry_after_responding_to_status_code(self, status_code, container_uri_and_slug, headers) -> bool:
        """Some types of failure are worth a few attempts to resolve"""

        if status_code == 401:
            self.__generate_access_token()
            return True

        if status_code == 409:
            requests.delete(container_uri_and_slug, headers=headers)
            return True

        if status_code >=500 and status_code<600:
            return True

        return False

    def upload_data(self, session, prepared_data={}):
        """Uploads the data to a Solid server"""
        if prepared_data == {}:
            return True, "Nothing to do"

        observation_identity = "latest"

        data = self.__describe_observations_as_graph(observation_identity, prepared_data).serialize().encode("utf-8")

        container_uri = self.context.params.get(service_name, "container_uri")
        if container_uri is None:
            raise Exception("Did not get container uri")

        slug = self.context.params.get(service_name, "slug")
        content_type = self.context.params.get(service_name, "content_type")

        try:
            # Would love to use something like `tenacity` here, but it's another thing to install
            retryCounter = 5
            while retryCounter > 0:
                headers = {
                    "Authorization": f"Bearer {self.__access_token}",
                    "Content-Type":content_type,
                    "Slug": slug,
                    "User-Agent": "pywws",
                }

                self.logger.debug(f"Uploading observations to {slug}...")

                result = requests.post(container_uri, headers=headers, data=data)
                willing_to_retry = self.__consider_retry_after_responding_to_status_code(result.status_code, f"{container_uri}{slug}", headers)
                retryCounter = retryCounter - 1
                if willing_to_retry == False:
                    retryCounter = 0

            result.raise_for_status()

        except Exception as ex:
            self.logger.exception("Unexpected failure")
            return False, repr(ex)

        self.logger.info(f"Uploaded observation {prepared_data['dateutc']}: {result.status_code}")

        return (
            True,
            f"Uploaded observation {prepared_data['dateutc']}: {result.status_code}",
        )


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
