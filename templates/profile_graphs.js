<%page args="grade_summary, graph_div_id, **kwargs"/>
<%!
  import json
%>

$(function () {
  function showTooltip(x, y, contents) {
    $('<div id="tooltip">' + contents + '</div>').css( {
      position: 'absolute',
      display: 'none',
      top: y + 5,
      left: x + 5,
      border: '1px solid #000',
      padding: '4px 6px',
      color: '#fff',
      'background-color': '#333',
      opacity: 0.90
    }).appendTo("body").fadeIn(200);
  }
      
  /* -------------------------------- Grade detail bars -------------------------------- */
  
  <%
  colors = ["#b72121", "#600101", "#666666", "#333333"]
  categories = {}
  #'
  tickIndex = 1
  sectionSpacer = 0.5
  sectionIndex = 0

  series = []
  ticks = [] #These are the indices and x-axis labels for the data
  bottomTicks = [] #Labels on the bottom
  detail_tooltips = {} #This an dictionary mapping from 'section' -> array of detail_tooltips
  droppedScores = [] #These are the datapoints to indicate assignments which aren't factored into the total score
  dropped_score_tooltips = []

  for section in grade_summary['section_breakdown']:
      if section.get('prominent', False):
          tickIndex += sectionSpacer
            
      if section['category'] not in categories:
          colorIndex = len(categories) % len(colors)
          categories[ section['category'] ] = {'label' : section['category'], 
                                              'data' : [], 
                                              'color' : colors[colorIndex]}
        
      categoryData = categories[ section['category'] ]
    
      categoryData['data'].append( [tickIndex, section['percent']] )
      ticks.append( [tickIndex, section['label'] ] )
    
    
      if section['category'] in detail_tooltips:
          detail_tooltips[ section['category'] ].append( section['detail'] )
      else:
          detail_tooltips[ section['category'] ] = [ section['detail'], ]
        
      tickIndex += 1
    
      if section.get('prominent', False):
          tickIndex += sectionSpacer
  %>
  
  var series = ${ json.dumps(series) };
  var ticks = ${ json.dumps(ticks) };
  var bottomTicks = ${ json.dumps(bottomTicks) };
  var detail_tooltips = ${ json.dumps(detail_tooltips) };
  var droppedScores = ${ json.dumps(droppedScores) };
  
  //Alwasy be sure that one series has the xaxis set to 2, or the second xaxis labels won't show up
  series.push( {label: 'Dropped Scores', data: droppedScores, points: {symbol: "cross", show: true, radius: 3}, bars: {show: false}, color: "#333"} );
  
  var options = {
    series: {stack: true,
              lines: {show: false, steps: false },
              bars: {show: true, barWidth: 0.8, align: 'center', lineWidth: 0, fill: .8 },},
    xaxis: {tickLength: 0, min: 0.0, max: ${tickIndex - sectionSpacer}, ticks: ticks, labelAngle: 90},
    yaxis: {ticks: [[1, "100%"], [0.87, "A 87%"], [0.7, "B 70%"], [0.6, "C 60%"], [0, "0%"]], min: 0.0, max: 1.0, labelWidth: 50},
    grid: { hoverable: true, clickable: true, borderWidth: 1,
      markings: [ {yaxis: {from: 0.87, to: 1 }, color: "#ddd"}, {yaxis: {from: 0.7, to: 0.87 }, color: "#e9e9e9"}, 
                  {yaxis: {from: 0.6, to: 0.7 }, color: "#f3f3f3"}, ] },
    legend: {show: false},
  };
  
  var $grade_detail_graph = $("#${graph_div_id}");
  if ($grade_detail_graph.length > 0) {
    var plot = $.plot($grade_detail_graph, series, options);
    
    var o = plot.pointOffset({x: ${overviewBarX} , y: ${totalScore}});
    $grade_detail_graph.append('<div style="position:absolute;left:' + (o.left - 12) + 'px;top:' + (o.top - 20) + 'px">${"{totalscore:.0%}".format(totalscore=totalScore)}</div>');
  }
      
  var previousPoint = null;
  $grade_detail_graph.bind("plothover", function (event, pos, item) {
    $("#x").text(pos.x.toFixed(2));
    $("#y").text(pos.y.toFixed(2));
    if (item) {
      if (previousPoint != (item.dataIndex, item.seriesIndex)) {
        previousPoint = (item.dataIndex, item.seriesIndex);
            
        $("#tooltip").remove();
            
        if (item.series.label in detail_tooltips) {
          var series_tooltips = detail_tooltips[item.series.label];
          if (item.dataIndex < series_tooltips.length) {
            var x = item.datapoint[0].toFixed(2), y = item.datapoint[1].toFixed(2);
                
            showTooltip(item.pageX, item.pageY, series_tooltips[item.dataIndex]);
          }
        }

      }
    } else {
      $("#tooltip").remove();
      previousPoint = null;            
    }
  });
});
