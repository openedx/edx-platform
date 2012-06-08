<%page args="grade_summary, graph_div_id, **kwargs"/>
<%!
  import json
  import math
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
  
  tickIndex = 1
  sectionSpacer = 0.5
  sectionIndex = 0

  series = []
  ticks = [] #These are the indices and x-axis labels for the data
  bottomTicks = [] #Labels on the bottom
  detail_tooltips = {} #This an dictionary mapping from 'section' -> array of detail_tooltips
  droppedScores = [] #These are the datapoints to indicate assignments which aren't factored into the total score
  dropped_score_tooltips = []

  for section in grade_summary:
    if 'subscores' in section: ##This is for sections like labs or homeworks, with several smaller components and a total
        series.append({
            'label' : section['category'],
            'data' : [[i + tickIndex, score['percentage']] for i,score in enumerate(section['subscores'])],
            'color' : colors[sectionIndex]
        })
        
        ticks += [[i + tickIndex, score['label'] ] for i,score in enumerate(section['subscores'])]
        bottomTicks.append( [tickIndex + len(section['subscores'])/2, section['category']] )
        detail_tooltips[ section['category'] ] = [score['summary'] for score in section['subscores']]
        
        droppedScores += [[tickIndex + index, 0.05] for index in section['dropped_indices']]
        
        dropExplanation = "The lowest {0} {1} scores are dropped".format( len(section['dropped_indices']), section['category'] )
        dropped_score_tooltips += [dropExplanation] * len(section['dropped_indices'])
        
        
        tickIndex += len(section['subscores']) + sectionSpacer
        
        
        category_total_label = section['category'] + " Total"
        series.append({
            'label' : category_total_label,
            'data' : [ [tickIndex, section['totalscore']] ],
            'color' : colors[sectionIndex]
        })
        
        ticks.append( [tickIndex, section['totallabel']] )
        detail_tooltips[category_total_label] = [section['totalscore_summary']]
    else:
        series.append({
            'label' : section['category'],
            'data' : [ [tickIndex, section['totalscore']] ],
            'color' : colors[sectionIndex]
        })
        
        ticks.append( [tickIndex, section['totallabel']] )
        detail_tooltips[section['category']] = [section['totalscore_summary']]
        
    tickIndex += 1 + sectionSpacer
    sectionIndex += 1


  detail_tooltips['Dropped Scores'] = dropped_score_tooltips    
    
  ## ----------------------------- Grade overviewew bar ------------------------- ##
  totalWeight = 0.0
  sectionIndex = 0
  totalScore = 0.0
  overviewBarX = tickIndex
     
  for section in grade_summary:
      weighted_score = section['totalscore'] * section['weight']
      summary_text = "{0} - {1:.1%} of a possible {2:.0%}".format(section['category'], weighted_score, section['weight'])
      
      weighted_category_label = section['category'] + " - Weighted"
         
      if section['totalscore'] > 0:
          series.append({
              'label' : weighted_category_label,
              'data' : [ [overviewBarX, weighted_score] ],
              'color' : colors[sectionIndex]
          })
            
      detail_tooltips[weighted_category_label] = [ summary_text ]
      sectionIndex += 1
      totalWeight += section['weight']
      totalScore += section['totalscore'] * section['weight']
        
  ticks += [ [overviewBarX, "Total"] ]
  tickIndex += 1 + sectionSpacer
  
  totalScore = math.floor(totalScore * 100) / 100 #We floor it to the nearest percent, 80.9 won't show up like a 90 (an A)
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
