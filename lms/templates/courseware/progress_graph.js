<%page args="grade_summary, grade_cutoffs, graph_div_id, show_grade_breakdown = True, show_grade_cutoffs = True, **kwargs"/>
<%!
    import bleach
    import json
    import math
    import six

    from openedx.core.djangolib.js_utils import (
        dump_js_escaped_json, js_escaped_string
    )
%>

$(function () {
  function showTooltip(x, y, contents) {
      $("#tooltip").remove();
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

      ## Because this is Python (Mako) embedded in JavaScript, our xss linting script is
      ## thoroughly confused. We should rewrite this file to remove Python/Mako.
      ## xss-lint: disable=javascript-jquery-append
      categoryData['data'].append( [tickIndex, section['percent']] )

      ## Note that some courses had stored images in the Abbreviation. We are no longer
      ## allowing the display of such images, and remove any previously stored HTML
      ## to prevent ugly HTML from being shown to learners.
      ## xss-lint: disable=javascript-jquery-append
      ticks.append( [tickIndex, bleach.clean(section['label'], tags=set(), strip=True)] )

      if section['category'] in detail_tooltips:
          ## xss-lint: disable=javascript-jquery-append
          detail_tooltips[ section['category'] ].append( section['detail'] )
      else:
          detail_tooltips[ section['category'] ] = [ section['detail'], ]

      if 'mark' in section:
          ## xss-lint: disable=javascript-jquery-append
          droppedScores.append( [tickIndex, 0.05] )
          ## xss-lint: disable=javascript-jquery-append
          dropped_score_tooltips.append( section['mark']['detail'] )

      tickIndex += 1

      if section.get('prominent', False):
          tickIndex += sectionSpacer

  ## ----------------------------- Grade overview bar ------------------------- ##
  tickIndex += sectionSpacer

  series = list(categories.values())
  overviewBarX = tickIndex
  extraColorIndex = len(categories) #Keeping track of the next color to use for categories not in categories[]

  if show_grade_breakdown:
    for section in six.itervalues(grade_summary['grade_breakdown']):
        if section['percent'] > 0:
            if section['category'] in categories:
                color = categories[ section['category'] ]['color']
            else:
                color = colors[ extraColorIndex % len(colors) ]
                extraColorIndex += 1
            ## xss-lint: disable=javascript-jquery-append
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
        ## xss-lint: disable=javascript-jquery-append
        grade_cutoff_ticks.append( [ percent, u"{0} {1:.0%}".format(grade, percent) ] )
  else:
    grade_cutoff_ticks = [ ]
  %>

  var series = ${ series | n, dump_js_escaped_json };
  var ticks = ${ ticks | n, dump_js_escaped_json };
  var bottomTicks = ${ bottomTicks | n, dump_js_escaped_json };
  var detail_tooltips = ${ detail_tooltips | n, dump_js_escaped_json };
  var droppedScores = ${ droppedScores | n, dump_js_escaped_json };
  var grade_cutoff_ticks = ${ grade_cutoff_ticks | n, dump_js_escaped_json }

  var yAxisTooltips={};

    /*
    series looks like:
    [
        {
            color: "#600101",
            label: "Homework",
            data: [[1, 0.06666666666666667], [2, 1], [3.25, .53]]
        },
        ...
    ]

    detail_tooltips looks like:
    {
        "Dropped Scores": [0: "The lowest 1...:],
        "Homework": [
            0: "Homework 1 -- Homework -- Question Styles 7% (1/15)",
            1: "Homework 2 -- Homework -- Get Social 100% (1/1)",
            2: "Homework Average = 53%"
        ],
        ...
    }
    */

  // loop through the series and extract the matching tick and the series label
  for (var seriesIndex = 0; seriesIndex < series.length; seriesIndex++) {
      for (var dataIndex = 0; dataIndex < series[seriesIndex]['data'].length; dataIndex++) {
          var tickIndex = series[seriesIndex]['data'][dataIndex][0];
          // There may be more than one detail tooltip for a given tickIndex. If so,
          // push the new tooltip on the existing list.
          if (tickIndex in yAxisTooltips) {
              yAxisTooltips[tickIndex].push(detail_tooltips[series[seriesIndex]['label']][dataIndex]);
          } else {
              yAxisTooltips[tickIndex] = [detail_tooltips[series[seriesIndex]['label']][dataIndex]];
          }
          // If this item was a dropped score, add the tooltip message about that.
          for (var droppedIndex = 0; droppedIndex < droppedScores.length; droppedIndex++) {
              if (tickIndex === droppedScores[droppedIndex][0]) {
                  yAxisTooltips[tickIndex].push(detail_tooltips["Dropped Scores"][droppedIndex]);
              }
          }
      }
  }

  // hide the vertical axis since they are audibly lacking context
  for (var i = 0; i < grade_cutoff_ticks.length; i++) {
      grade_cutoff_ticks[i][1] = edx.HtmlUtils.joinHtml(
          edx.HtmlUtils.HTML('<span aria-hidden="true">'),
          grade_cutoff_ticks[i][1],
          edx.HtmlUtils.HTML('</span>')
      ).text;
  }

  //Always be sure that one series has the xaxis set to 2, or the second xaxis labels won't show up
  series.push( {label: 'Dropped Scores', data: droppedScores, points: {symbol: "cross", show: true, radius: 3}, bars: {show: false}, color: "#333"} );

  // Allow for arbitrary grade markers e.g. ['A', 'B', 'C'], ['Pass'], etc.
  var ascending_grades = grade_cutoff_ticks.map(function (el) { return el[0]; }); // Percentage point (in decimal) of each grade cutoff
  ascending_grades.sort();

  // var colors = ['$gray-100', '$gray-200', '$gray-300'];
  var colors = ['#f8f9fa', '#e9ecef', '#dee2e6'];
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
        }
    },
    xaxis: {
        tickLength: 0,
        min: 0.0,
        max: ${tickIndex - sectionSpacer | n, dump_js_escaped_json},
        ticks: function() {
            for (var i = 0; i < ticks.length; i++) {
                var tickLabel = edx.HtmlUtils.joinHtml(
                    // The very last tick will be for the total, and it usually is composed of a number of different
                    // grading types. To help clarify, do NOT make the label ("Total") aria-hidden in that case.
                    edx.HtmlUtils.HTML(i < ticks.length - 1 ? '<span aria-hidden="true">' : '<span>'),
                    ticks[i][1],
                    edx.HtmlUtils.HTML('</span>')
                );
                var elementTooltips = yAxisTooltips[ticks[i][0]];
                if (elementTooltips) {
                    for (var tooltipIndex = 0; tooltipIndex < elementTooltips.length; tooltipIndex++) {
                        tickLabel = edx.HtmlUtils.joinHtml(
                            tickLabel,
                            edx.HtmlUtils.HTML('<span class="sr">'),
                            elementTooltips[tooltipIndex],
                            edx.HtmlUtils.HTML('<br></span>')
                        );
                    }
                }
                ticks[i][1] = tickLabel;
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
        borderColor: "#707070", // gray-500
        markings: markings
    },
    legend: {
        show: false
    },
  };

  var $grade_detail_graph = $("#${graph_div_id | n, js_escaped_string}");
  $grade_detail_graph.width($grade_detail_graph.parent().width());
  if ($grade_detail_graph.length > 0) {
    var plot = $.plot($grade_detail_graph, series, options);

    %if show_grade_breakdown:
      var o = plot.pointOffset(
          {x: ${overviewBarX | n, dump_js_escaped_json} , y: ${totalScore | n, dump_js_escaped_json}}
      );

      edx.HtmlUtils.append(
          $grade_detail_graph,
          edx.HtmlUtils.joinHtml(
              // xss-lint: disable=javascript-concat-html
              edx.HtmlUtils.HTML('<div class="overallGrade" style="position:absolute;left:' + (o.left - 12) + 'px;top:' + (o.top - 20) + 'px">'),
              edx.HtmlUtils.HTML('<span class=sr>'),
              gettext('Overall Score'),
              edx.HtmlUtils.HTML('<br></span>'),
              '${'{totalscore:.0%}'.format(totalscore=totalScore) | n, js_escaped_string}',
              edx.HtmlUtils.HTML('</div>')
          )
      );

    %endif

    $grade_detail_graph.find('.xAxis .tickLabel').attr('tabindex', '0').focus(function(event) {
        var $target = $(event.target), srElements = $target.find('.sr'), srText="", i;
        if (srElements.length > 0) {
            for (i = 0; i < srElements.length; i++) {
                srText += srElements[i].innerHTML;
            }
            // Position the tooltip slightly above the tick label.
            showTooltip($target.offset().left - 70, $target.offset().top - 120, srText);
        }
    });

    $grade_detail_graph.focusout(function(){
        $("#tooltip").remove();
    });
  }


  var previousPoint = null;
  $grade_detail_graph.bind("plothover", function (event, pos, item) {
    if (item) {
      if (previousPoint != (item.dataIndex, item.seriesIndex)) {
        previousPoint = (item.dataIndex, item.seriesIndex);

        if (item.series.label in detail_tooltips) {
          var series_tooltips = detail_tooltips[item.series.label];
          if (item.dataIndex < series_tooltips.length) {
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
