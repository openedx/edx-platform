<%!
  import json
  import math
%>

<%
data = []
xticks = []
yticks = []
maxx = 1
maxy = 1.5
#Here we change the y-axis (count) to be logorithmic. We also define better ticks
for score, count in histogram:
    score = score or 0 #Sometimes score is None. This fixes that
        
    log_count = math.log(count + 1)
    
    data.append( [score, log_count] )
    
    yticks.append( [log_count, str(count)] )
    xticks.append( [score, str(int(score))] )
    
    maxx = max( score + 1, maxx )
    maxy = max( log_count*1.1, maxy  )
%>


$.plot($("#histogram_${module_id}"), [{
    data: ${ json.dumps(data) },
    bars: { show: true,
            align: 'center',
            lineWidth: 0, 
            fill: 1.0 },
    color: "#b72121",
  }],
  {
    xaxis: {min: -1, max: ${maxx}, ticks: ${ json.dumps(xticks) }, tickLength: 0},
    yaxis: {min: 0.0, max: ${maxy}, ticks: ${ json.dumps(yticks) }, labelWidth: 50},
  });
