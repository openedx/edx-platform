<%page args="class_dashboard_results, **kwargs"/>
<%!
  import json
%>

$(function () {
  var d3_prob_grade_distrib = ${json.dumps(class_dashboard_results['d3_prob_grade_distrib'])}
  console.log(d3_prob_grade_distrib);

  var svg = d3.select("#class_dashboard").append("svg");
  var div = d3.select("#class_dashboard").append("div");
  var param = {
    data: d3_prob_grade_distrib,
    width: 1000,
    height: 800,
    bVerticalXAxisLabel: true,
  };
  var barGraph = edx_d3CreateStackedBarGraph(param, svg, div);
  barGraph.drawGraph();
});