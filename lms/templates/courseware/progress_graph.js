<%page args="grade_summary, grade_cutoffs, graph_div_id, show_grade_breakdown = True, show_grade_cutoffs = True, **kwargs"/>
<%!
import json
import math
%>

$(function () {
  function showTooltip(x, y, contents) {
      var $tooltip_div = $('<div id="tooltip"></div>').css({
              position: 'absolute',
              display: 'none',
              top: y + 5,
              left: x + 15,
              border: '1px solid #000',
              padding: '4px 6px',
              color: '#fff',
              'background-color': '#222',
              opacity: 0.90
          });
          
      edx.HtmlUtils.setHtml(
          $tooltip_div,
          edx.HtmlUtils.HTML(contents)
      );
      
      edx.HtmlUtils.append(
          $('body'),
          edx.HtmlUtils.HTML($tooltip_div)
      );
      
      $('#tooltip').fadeIn(200);
  }

  /* -------------------------------- Grade detail bars -------------------------------- */
    
  <%
  colors = ["#b72121", "#600101", "#666666", "#333333"]
  categories = {}

  tickIndex = 1
  sectionSpacer = 0.25
  sectionIndex = 0

  ticks = [] #These are the indices and x-axis labels for the data
  bottomTicks = [] #Labels on the bottom
  detail_tooltips = {} #This an dictionary mapping from 'section' -> array of detail_tooltips
  droppedScores = [] #These are the datapoints to indicate assignments which are not factored into the total score
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
          
      if 'mark' in section:
          droppedScores.append( [tickIndex, 0.05] )
          dropped_score_tooltips.append( section['mark']['detail'] )
        
      tickIndex += 1
    
      if section.get('prominent', False):
          tickIndex += sectionSpacer
          
  ## ----------------------------- Grade overviewew bar ------------------------- ##
  tickIndex += sectionSpacer
  
  series = categories.values()
  overviewBarX = tickIndex
  extraColorIndex = len(categories) #Keeping track of the next color to use for categories not in categories[]
  
  if show_grade_breakdown:    
    for section in grade_summary['grade_breakdown']:
        if section['percent'] > 0:
            if section['category'] in categories:
                color = categories[ section['category'] ]['color']
            else:
                color = colors[ extraColorIndex % len(colors) ]
                extraColorIndex += 1
        
            series.append({
                'label' : section['category'] + "-grade_breakdown",
                'data' : [ [overviewBarX, section['percent']] ],
                'color' : color
            })
            
            detail_tooltips[section['category'] + "-grade_breakdown"] = [ section['detail'] ]
  
    ticks += [ [overviewBarX, "Total"] ]
    tickIndex += 1 + sectionSpacer
  
  totalScore = grade_summary['percent']
  detail_tooltips['Dropped Scores'] = dropped_score_tooltips
  
  
  ## ----------------------------- Grade cutoffs ------------------------- ##
  
  grade_cutoff_ticks = [ [1, "100%"], [0, "0%"] ]
  if show_grade_cutoffs:
    grade_cutoff_ticks = [ [1, "100%"], [0, "0%"] ]
    descending_grades = sorted(grade_cutoffs, key=lambda x: grade_cutoffs[x], reverse=True)
    for grade in descending_grades:
        percent = grade_cutoffs[grade]
        grade_cutoff_ticks.append( [ percent, u"{0} {1:.0%}".format(grade, percent) ] )
  else:
    grade_cutoff_ticks = [ ]
  %>
  
  var series = ${ json.dumps( series ) };
  var ticks = ${ json.dumps(ticks) };
  var bottomTicks = ${ json.dumps(bottomTicks) };
  var detail_tooltips = ${ json.dumps(detail_tooltips) };
  var droppedScores = ${ json.dumps(droppedScores) };
  var grade_cutoff_ticks = ${ json.dumps(grade_cutoff_ticks) }
  
  var series_order_object = [];
  var c = 0, s, t;
  
  // loop through the series and extract the matching tick and the series label
  for (var k = 0; k < series.length; k++) {
    if (series[k]['data'].length > 1) {
        for (var m = 0; m < series[k]['data'].length; m++) {
            s = {};
            s.data = m;
            s.tick = series[k]['data'][m][0];
            s.label = series[k]['label'];
            series_order_object.push(s);
        }
    } else {
        s = {};
        s.data = 0;
        s.tick = series[k]['data'][0][0];
        s.label = series[k]['label'];
        series_order_object.push(s);
    }
  }

  // reorder the series_order_object object to match the ticks, which is the correct order
  series_order_object.sort(function(a, b) {
      return a.tick-b.tick;
  });
  
  // hide the vertical axis since they are audibly lacking context
  for (var i = 0; i < grade_cutoff_ticks.length; i++) {
      grade_cutoff_ticks[i][1] = edx.HtmlUtils.interpolateHtml(
          edx.HtmlUtils.HTML('<span aria-hidden="true">{cutoff}</span>'),
          {
              cutoff: grade_cutoff_ticks[i][1]
          }
      );
  }
    
  //Always be sure that one series has the xaxis set to 2, or the second xaxis labels won't show up
  series.push( {label: 'Dropped Scores', data: droppedScores, points: {symbol: "cross", show: true, radius: 3}, bars: {show: false}, color: "#333"} );
  
  // Allow for arbitrary grade markers e.g. ['A', 'B', 'C'], ['Pass'], etc.
  var ascending_grades = grade_cutoff_ticks.map(function (el) { return el[0]; }); // Percentage point (in decimal) of each grade cutoff
  ascending_grades.sort();

  var colors = ['#f3f3f3', '#e9e9e9', '#ddd'];
  var markings = [];
  for(var i=1; i<ascending_grades.length-1; i++) // Skip the i=0 marking, which starts from 0%
    markings.push({yaxis: {from: ascending_grades[i], to: ascending_grades[i+1]}, color: colors[(i-1) % colors.length]});

  var options = {
    series: {
        stack: true,
        lines: {
            show: false,
            steps: false
        },
        bars: {
            show: true,
            barWidth: 0.8,
            align: 'center',
            lineWidth: 0,
            fill: .8
        },
    },
    xaxis: {
        tickLength: 0,
        min: 0.0,
        max: ${tickIndex - sectionSpacer},
        ticks: function() {
            for (var i = 0; i < ticks.length; i++) {
                if (detail_tooltips[series_order_object[i]]) {
                    ticks[i][1] = edx.HtmlUtils.interpolateHtml(
                        edx.HtmlUtils.HTML('<span aria-hidden="true">{original}</span><span class="sr">{additional}</span>'),
                        {
                            original: ticks[i][1],
                            additional: detail_tooltips[series_order_object[i].label][series_order_object[i].data]
                        }
                    );
                }
            }
            return ticks;
        },
        labelAngle: 90
    },
    yaxis: {
        ticks: grade_cutoff_ticks,
        min: 0.0,
        max: 1.0,
        labelWidth: 100
    },
    grid: {
        hoverable: true,
        clickable: true,
        borderWidth: 1,
        markings: markings
    },
    legend: {
        show: false
    },
  };
  
  var $grade_detail_graph = $("#${graph_div_id}");
  if ($grade_detail_graph.length > 0) {
    var plot = $.plot($grade_detail_graph, series, options);
    
    %if show_grade_breakdown:
      var o = plot.pointOffset({x: ${overviewBarX} , y: ${totalScore}});
      $grade_detail_graph.append('<div style="position:absolute;left:' + (o.left - 12) + 'px;top:' + (o.top - 20) + 'px">${'{overall_wrap_start}{overall_text}{overall_wrap_close}{totalscore:.0%}'.format(overall_wrap_start="<span class=sr>", overall_wrap_close="</span>", overall_text="Overall score:", totalscore=totalScore)}</div>');
    %endif
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
