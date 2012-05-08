<%!
  import json
  import math
%>


var rawData = ${json.dumps(histogram)};

var maxx = 1;
var maxy = 1.5;
var xticks = Array();
var yticks = Array();
var data = Array();
for (var i = 0; i < rawData.length; i++) {
  var score = rawData[i][0];
  var count = rawData[i][1];
  var log_count = Math.log(count + 1);
  
  data.push( [score, log_count] );
  
  xticks.push( [score, score.toString()] );
  yticks.push( [log_count, count.toString()] );
  
  maxx = Math.max( score + 1, maxx );
  maxy = Math.max(log_count*1.1, maxy );
}

$.plot($("#histogram_${module_id}"), [{
    data: data,
    bars: { show: true,
            align: 'center',
            lineWidth: 0, 
            fill: 1.0 },
    color: "#b72121",
  }],
  {
    xaxis: {min: -1, max: maxx, ticks: xticks, tickLength: 0},
    yaxis: {min: 0.0, max: maxy, ticks: yticks, labelWidth: 50},
  }
);
