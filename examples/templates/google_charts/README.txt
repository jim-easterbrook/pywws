How to get google visualisation charts working with pywws

1) Set up a template in pywws to generate JSON data
2) Extract the JSON data using jquery and generate the google charts using javascript

1) Setting up a template in pywws:
  JSON format is a similar concept to XML in that key identifiers are used to 
  separate data elements. Reference site is: http://www.json.org/
  The "[" bracket is used to contain an array, whilst objects are contained within 
  the "{" bracket. WARNING: The jquery function for extracting JSON data is very very
  sensitive so make sure you have brackets and commas in the correct place. Below is an
  example template that generates the last 6 x 10 minute intervals of data.
  
live_json.txt ------------------------- (don't include this line in the template)

[
#timezone local#
#raw#
#jump -7#
#jump 1#
#loop 6#
  {
      "Date": "#idx "%m/%d/%Y %H:%M"#",
      "Time": " #idx "%H:%M %Z"# ",
      "TempOut": #temp_out "%.1f"#,
      "FeelsLike": #calc "apparent_temp(data['temp_out'], data['hum_out'], data['wind_ave'])" "%.1f"#,
      "HumidityOut": #hum_out "%d"#,
      "WindDirection": " #wind_dir "%s" "-" "winddir_text(x)"# ",
      "WindAvg": #wind_ave "%.0f" "" "x"#,
      "WindGust": #wind_gust "%.0f" "" "x"#,
      "Rain": #calc "data['rain']-prevdata['rain']" "%0.1f"#,
      "AbsPressure": #abs_pressure "%.1f"#
  },
#jump 1#
#endloop#
#jump 1#
  {
      "Date": "#idx "%m/%d/%Y %H:%M"#",
      "Time": " #idx "%H:%M %Z"# ",
      "TempOut": #temp_out "%.1f"#,
      "FeelsLike": #calc "apparent_temp(data['temp_out'], data['hum_out'], data['wind_ave'])" "%.1f"#,
      "HumidityOut": #hum_out "%d"#,
      "WindDirection": " #wind_dir "%s" "-" "winddir_text(x)"# ",
      "WindAvg": #wind_ave "%.0f" "" "x"#,
      "WindGust": #wind_gust "%.0f" "" "x"#,
      "Rain": #calc "data['rain']-prevdata['rain']" "%0.1f"#,
      "AbsPressure": #abs_pressure "%.1f"#
  }
]

-----------end of file-------- (don't include this line in the template)

  Note that the data is each section is identical, however the last "object" contained 
  in the curly brackets"{}" lacks a trailing comma. Also the last element (AbsPressure) 
  lacks a trailing comma. Don't forget the "[]" at the start and end of the template.
  Finally to keep things simple I removed spaces from the data names.
  
  Set this up to run at whatever interval you wish and then upload the resultant data to
  your website (I use the built in ftp settings in pywws).
  
2) Extracting the data and generating the google charts:
  This example will work through a table chart (http://code.google.com/apis/chart/interactive/docs/gallery/table.html)
  This documentation is based on using the google visualization API. The homepage for this
  library is http://code.google.com/apis/chart/ 
  
  In the head section of your html page, you need to setup the jquery reference and the 
  google api reference (lines 1 and 2 of extract below). Then you need to load the "table"
  package for our example - there are other packages you will need if you are making other
  charts.
  
----------extract of HTML HEAD STUFF -------------------  
  <script src="http://code.jquery.com/jquery-latest.js"></script>
  <script type='text/javascript' src='https://www.google.com/jsapi'></script>
  
  <script type="text/javascript" language="javascript">
    //load the table package
    google.load('visualization', '1', {packages:['table']});
---------END of HTML STUFF ------------------

  Then in the document ready function (which is part of jquery and is called as the page
  is rendered) we need to create a datatable to hold the data and extract the data from 
  the JSON file into the datatable. Finally we create an instance of the google table chart
  and assign it to a <div> in your html body. An example is shown below
  
----------extract of HTML HEAD STUFF -------------------  

$(document).ready(function() {
        
        var datatbl = new google.visualization.DataTable();
        
        //get the data from the file and load it into the google datatable
        $.getJSON('live_json.txt', function(data) {
        
            //create the rows and columns in the datatable
        	var noElements = data.length; 
            datatbl.addColumn('datetime', 'Date');
            datatbl.addColumn('string', 'Time');
            datatbl.addColumn('number', 'Outside Temp');
            datatbl.addColumn('number', 'Apparent Temp');
            datatbl.addColumn('number', 'Humidity Outside (%)');
            datatbl.addColumn('string', 'Wind Direction');
            datatbl.addColumn('number', 'Wind Avg Speed (kph)');
            datatbl.addColumn('number', 'Wind Gust (kph)');
            datatbl.addColumn('number', 'Rain (mm)');
            datatbl.addColumn('number', 'Abs Pressure (hPa)');
            datatbl.addRows(noElements);
            
            //Put the data into the datatable
            $.each(data, function(i,v) {
                 // set the values for both the name and the population
                 datatbl.setValue(i, 0, new Date(v.Date));
                 datatbl.setValue(i, 1, v.Time);
                 datatbl.setValue(i, 2, v.TempOut);
                 datatbl.setValue(i, 3, v.FeelsLike);
                 datatbl.setValue(i, 4, v.HumidityOut);
                 datatbl.setValue(i, 5, v.WindDirection);
                 datatbl.setValue(i, 6, v.WindAvg);
                 datatbl.setValue(i, 7, v.WindGust);
                 datatbl.setValue(i, 8, v.Rain);
                 datatbl.setValue(i, 9, v.AbsPressure);
            }); 
            
            //create an instance of the google table chart
            var table = new google.visualization.Table(document.getElementById('table_div'));
            
            //draw the table chart
            table.draw(datatable);
        
        });
});
---------END of HTML STUFF ------------------

  To make this appear in your html page, you will need a <div> called 'table_div' in this
  example as follows:

----------extract of HTML BODY STUFF -------------------
<body>
  <div id='table_div'></div>
</body>
---------END of HTML STUFF ------------------

  An example is available at http://ash-min.com/weather/live.php
  
  

