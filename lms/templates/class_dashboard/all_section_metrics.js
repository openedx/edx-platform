<%page args="id_opened_prefix, id_grade_prefix, id_attempt_prefix, id_tooltip_prefix, course_id, **kwargs"/>
<%!
  import json
  from django.core.urlresolvers import reverse
%>

$(function () {

  d3.json("${reverse('all_sequential_open_distribution', kwargs=dict(course_id=course_id))}", function(error, json) {
    var section, paramOpened, barGraphOpened;
    var i, curr_id;

    i = 0;
    for (section in json) {
      curr_id = "#${id_opened_prefix}"+i;
      paramOpened = {
        data: json[section].data,
        width: $(curr_id).width(),
        height: $(curr_id).height()-25, // Account for header
        tag: "opened"+i,
        bVerticalXAxisLabel : true,
        bLegend : false,
        margin: {left:0},
      };
      
      if (paramOpened.data.length > 0) {
        barGraphOpened = edx_d3CreateStackedBarGraph(paramOpened, d3.select(curr_id).append("svg"),
                                                     d3.select("#${id_tooltip_prefix}"+i));
        barGraphOpened.scale.stackColor.range(["#555555","#555555"]);
        
        barGraphOpened.drawGraph();
        
        $('svg').siblings('.loading').remove();
      }

      i+=1;
    }
  });

  d3.json("${reverse('all_problem_grade_distribution', kwargs=dict(course_id=course_id))}", function(error, json) {
    var section, paramGrade, barGraphGrade;
    var i, curr_id;

    i = 0;
    for (section in json) {
      curr_id = "#${id_grade_prefix}"+i;
      paramGrade = {
        data: json[section].data,
        width: $(curr_id).width(),
        height: $(curr_id).height()-25, // Account for header
        tag: "grade"+i,
        bVerticalXAxisLabel : true,
      };
      
      if ( paramGrade.data.length > 0 ) {
        barGraphGrade = edx_d3CreateStackedBarGraph(paramGrade, d3.select(curr_id).append("svg"),
                                                    d3.select("#${id_tooltip_prefix}"+i));
        barGraphGrade.scale.stackColor.domain([0,50,100]).range(["#e13f29","#cccccc","#17a74d"]);
        barGraphGrade.legend.width += 2;
        
        barGraphGrade.drawGraph();
        
        $('svg').siblings('.loading').remove();
      }

      i+=1;
    }
  });
  
});