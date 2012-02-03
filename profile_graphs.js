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
      border: '1px solid #fdd',
      padding: '2px',
      'background-color': '#fee',
      opacity: 0.90
    }).appendTo("body").fadeIn(200);
  }
      
  /* -------------------------------- Grade detail graph -------------------------------- */
  var colors = [$.color.parse("#E8B800"), $.color.parse("#A0CEFA"), $.color.parse("#BD3738"), $.color.parse("#429A2E")];
  //var colors = [$.color.parse("#1B2045"), $.color.parse("#557a00"), $.color.parse("#F5600"), $.color.parse("#FEBA2C")];
  //var colors = [$.color.parse("#E7C856"), $.color.parse("#CD462E"), $.color.parse("#B01732"), $.color.parse("#41192A")];
  //var colors = [$.color.parse("#434F5E"), $.color.parse("#BEF731"), $.color.parse("#FB5455"), $.color.parse("#44C4B7")];
  //var colors = [$.color.parse("#147A7D"), $.color.parse("#C0C900"), $.color.parse("#C9005B"), $.color.parse("#FCF9A5")];
      
      
      
  var series = [];
  var ticks = []; //These are the indices and x-axis labels for the data
  var bottomTicks = []; //Labels on the bottom
  var detail_tooltips = {}; //This an dictionary mapping from 'section' -> array of detail_tooltips
  var droppedScores = []; //These are the datapoints to indicate assignments which aren't factored into the total score
  detail_tooltips['Dropped Scores'] = [];
  <%
  tickIndex = 1
  sectionSpacer = 0.5
  sectionIndex = 0
  %>
  %for section in grade_summary:
    %if 'subscores' in section: ##This is for sections like labs or homeworks, with several smaller components and a total
      series.push({label: "${section['category']}",
        data: ${ json.dumps( [[i + tickIndex, score['percentage']] for i,score in enumerate(section['subscores'])] ) },
        color: colors[${sectionIndex}].toString(),
      });
      ticks = ticks.concat( ${ json.dumps( [[i + tickIndex, str(i + 1)] for i,score in enumerate(section['subscores'])] ) } );
      bottomTicks.push( [ ${tickIndex + len(section['subscores'])/2}, "${section['category']}" ] );
      detail_tooltips["${section['category']}"] = ${ json.dumps([score['summary'] for score in section['subscores']]  ) };
          
      droppedScores = droppedScores.concat(${ json.dumps( [[tickIndex + index, 0.05] for index in section['dropped_indices']]) });
      <% dropExplanation = "The lowest {} {} scores are dropped".format( len(section['dropped_indices']), section['category'] ) %>
      detail_tooltips['Dropped Scores'] = detail_tooltips['Dropped Scores'].concat( ${json.dumps( [dropExplanation] * len(section['dropped_indices']) )} );
          
      <% tickIndex += len(section['subscores']) + sectionSpacer %>
          
      ##Now put on the aggregate score
      series.push({label: "${section['category']} Total",
        data: [[${tickIndex}, ${section['totalscore']['score']}]],
        color: colors[${sectionIndex}].toString(),
      });
      ticks = ticks.concat( [ [${tickIndex}, "Total"] ] );
      detail_tooltips["${section['category']} Total"] = [ "${section['totalscore']['summary']}" ];
      <% tickIndex += 1 + sectionSpacer %>
          
    %else: ##This is for sections like midterm or final, which have no smaller components
      series.push({label: "${section['category']}",
        data: [[${tickIndex}, ${section['totalscore']['score']}]],
        color: colors[${sectionIndex}].toString(),
      });
      %if section['category'] == "Midterm":
      bottomTicks = bottomTicks.concat( [ [${tickIndex}, "${section['category']}"] ] );
      %else:
      ticks = ticks.concat( [ [${tickIndex}, "${section['category']}"] ] );
      %endif
          
      detail_tooltips["${section['category']}"] = [ "${section['totalscore']['summary']}" ];

      <% tickIndex += 1 + sectionSpacer %>
    %endif
    <%sectionIndex += 1 %>
  %endfor
      
  //Alwasy be sure that one series has the xaxis set to 2, or the second xaxis labels won't show up
  series.push( {label: 'Dropped Scores', data: droppedScores, points: {symbol: "cross", show: true, radius: 3}, bars: {show: false}, color: "red", xaxis: 2} );
      
  var options = {
    series: {lines: {show: false, steps: false },
    bars: {show: true, barWidth: 0.6, align: 'center', lineWidth: 1},},
    xaxis: {tickLength: 0, min: 0.0, max: ${tickIndex - sectionSpacer}},
    xaxes: [{ticks: ticks}, {ticks: bottomTicks}],
    yaxis: {ticks: [[1, "100%"], [0.87, "A 87%"], [0.7, "B 70%"], [0.6, "C 60%"], [0, "0%"]], min: 0.0, max: 1.0, labelWidth: 50},
    grid: { hoverable: true, clickable: true, borderWidth: 1,
      markings: [ {yaxis: {from: 0.87, to: 1 }, color: "#EBFFD5"}, {yaxis: {from: 0.7, to: 0.87 }, color: "#E6FFFF"}, 
                  {yaxis: {from: 0.6, to: 0.7 }, color: "#FFF2E3"}, ] },
    legend: {show: false},
  };
  
  if ($("#grade-detail-graph").length > 0) {
    $.plot($("#grade-detail-graph"), series, options);
  }
      
  var previousPoint = null;
  $("#grade-detail-graph").bind("plothover", function (event, pos, item) {
    $("#x").text(pos.x.toFixed(2));
    $("#y").text(pos.y.toFixed(2));
    if (item) {
      if (previousPoint != item.dataIndex) {
        previousPoint = item.dataIndex;
            
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
