<%page args="id_opened_prefix, id_grade_prefix, id_attempt_prefix, id_tooltip_prefix, course_id, allSubsectionTooltipArr, allProblemTooltipArr, **kwargs"/>
<%!
  import json
  from django.core.urlresolvers import reverse
%>

$(function () {

  d3.json("${reverse('all_sequential_open_distrib', kwargs=dict(course_id=course_id.to_deprecated_string()))}", function(error, json) {
    var section, paramOpened, barGraphOpened, error;
    var i, curr_id;
    var errorMessage = gettext('Unable to retrieve data, please try again later.');

    error = json.error;
    if (error) {
      $('.metrics-left .loading').text(errorMessage);
      return
    }
    
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
      
      // Construct array of tooltips for all sections for the "Download Subsection Data" button.
      var sectionTooltipArr = new Array();
      paramOpened.data.forEach( function(element, index, array) {
    	sectionTooltipArr[index] = element.stackData[0].tooltip;
      });
      allSubsectionTooltipArr[i] = sectionTooltipArr;
      
      barGraphOpened = edx_d3CreateStackedBarGraph(paramOpened, d3.select(curr_id).append("svg"),
              d3.select("#${id_tooltip_prefix}"+i));
      barGraphOpened.scale.stackColor.range(["#555555","#555555"]);
      
      if (paramOpened.data.length > 0) {
        barGraphOpened.drawGraph();
        
        $('svg').siblings('.loading').remove();
      } else {
    	  $('svg').siblings('.loading').text(errorMessage);
      }

      i+=1;
    }
  });

  d3.json("${reverse('all_problem_grade_distribution', kwargs=dict(course_id=course_id.to_deprecated_string()))}", function(error, json) {
    var section, paramGrade, barGraphGrade, error;
    var i, curr_id;
    var errorMessage = gettext('Unable to retrieve data, please try again later.');

    error = json.error;
    if (error) {
      $('.metrics-right .loading').text(errorMessage);
      return
    }
    
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
      
      // Construct array of tooltips for all sections for the "Download Problem Data" button.
      var sectionTooltipArr = new Array();
      paramGrade.data.forEach( function(element, index, array) {
    	var stackDataArr = new Array();
    	for (var j = 0; j < element.stackData.length; j++) {
    		stackDataArr[j] = element.stackData[j].tooltip
    	}
    	sectionTooltipArr[index] = stackDataArr;
      });
      allProblemTooltipArr[i] = sectionTooltipArr;

      barGraphGrade = edx_d3CreateStackedBarGraph(paramGrade, d3.select(curr_id).append("svg"),
              d3.select("#${id_tooltip_prefix}"+i));
      barGraphGrade.scale.stackColor.domain([0,50,100]).range(["#e13f29","#cccccc","#17a74d"]);
      barGraphGrade.legend.width += 2;
      
      if ( paramGrade.data.length > 0 ) {
        barGraphGrade.drawGraph();
        
        $('svg').siblings('.loading').remove();
      } else {
    	  $('svg').siblings('.loading').text(errorMessage);
      }

      i+=1;
    }
    
  });
  
});