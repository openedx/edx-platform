<%page args="id_str_opened, id_str_grade, id_str_attempts, id_str_tooltip, i, course_id, **kwargs"/>
<%!
  import json
  from django.core.urlresolvers import reverse
%>

$(function () {
  var divTooltip = d3.select("#${id_str_tooltip}");
  
  var paramOpened = {
    width: $("#${id_str_opened}").width(),
    height: $("#${id_str_opened}").height()-25, // Account for header
    tag: "opened",
    bVerticalXAxisLabel : true,
    bLegend : false,
    margin: {left:0},
  };

  var paramGrade = {
    width: $("#${id_str_grade}").width(),
    height: $("#${id_str_grade}").height()-25, // Account for header
    tag: "grade",
    bVerticalXAxisLabel : true,
  };

  var paramAttempts = {
    width: $("#${id_str_attempts}").width(),
    height: $("#${id_str_attempts}").height()-25, // Account for header
    tag: "attempts",
    bVerticalXAxisLabel : true,
  };

  var barGraphOpened, barGraphGrade, barGraphAttempts;

  d3.json("${reverse('all_sequential_open_distribution', kwargs=dict(course_id=course_id))}", function(error, json) {
    paramOpened.data = json[${i}].data;

    if ( paramOpened.data.length > 0 ) {
      barGraphOpened = edx_d3CreateStackedBarGraph(paramOpened, d3.select("#${id_str_opened}").append("svg"), divTooltip);
      barGraphOpened.scale.stackColor.range(["#555555","#555555"]);

      barGraphOpened.drawGraph();
    }
  });

  d3.json("${reverse('section_problem_grade_distribution', kwargs={'course_id':course_id, 'section':str(i)})}", function(error, json) {
//  d3.json("${reverse('all_problem_grade_distribution', kwargs=dict(course_id=course_id))}", function(error, json) {
    paramGrade.data = json;
//    paramGrade.data = json[${i}].data;

    if ( paramGrade.data.length > 0 ) {
      barGraphGrade = edx_d3CreateStackedBarGraph(paramGrade, d3.select("#${id_str_grade}").append("svg"), divTooltip);
      
      barGraphGrade.scale.stackColor.domain([0,50,100]).range(["#e13f29","#cccccc","#17a74d"]);
      barGraphGrade.legend.width += 2;
      
      barGraphGrade.drawGraph();
    }
  });

  d3.json("${reverse('all_problem_attempt_distribution', kwargs=dict(course_id=course_id))}", function(error, json) {
    paramAttempts.data = json[${i}].data;

    if ( paramAttempts.data.length > 0 ) {
      barGraphAttempts = edx_d3CreateStackedBarGraph(paramAttempts, d3.select("#${id_str_attempts}").append("svg"),
                                                     divTooltip);
      barGraphAttempts.scale.stackColor
        .range(["#c3c4cd","#b0b4d1","#9ca3d6","#8993da","#7682de","#6372e3",
                "#4f61e7","#3c50eb","#2940ef","#1530f4","#021ff8"]);
      barGraphAttempts.legend.width += 2;
      
      barGraphAttempts.drawGraph();
    }
  });

});