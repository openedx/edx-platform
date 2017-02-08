/*
There are three parameters:
(1) Parameter is of type object. Inside can include (* marks required):
  data* - Array of objects with key, value pairs that represent a single stack of bars:
    xValue - Corresponding value for the x-axis
    stackData - Array of objects with key, value pairs that represent a bar:
      color - Defines what "color" the bar will map to
      value - Maps to the height of the bar, along the y-axis
      tooltip - (Optional) Text to display on mouse hover
  
  height - Height of the SVG the graph will be displayed in (default: 500)

  width - Width of the SVG the graph will be displayed in (default: 500)

  margin - Object with key, value pairs for the graph's margins within the SVG (default for all: 10)
    top - Top margin
    bottom - Bottom margin
    right - Right margin
    left - Left margin

  yRange - Array of two values, representing the min and max respectively. (default: [0, <calculated max>])

  xRange - Array of either the min and max or ordered ordinals (default: calculated min and max or ordered ordinals given in data)

  colorRange - Array of either the min and max or ordered ordinals (default: calculated min and max or ordered ordinals given in data)

  bVerticalXAxisLabel - Boolean whether to make the labels in the x-axis veritcal (default: false)

  bLegend - Boolean if false does not create the graph with a legend (default: true)

(2) Parameter is a d3 pointer to the SVG the graph will draw itself in.

(3) Parameter is a d3 pointer to a div that will be used for the graph's tooltip.

****Does not actually draw graph.**** Returns an object that includes a function
  drawGraph, for when ready to draw graph. Reason for this is, because of all
  the defaults, some changes may be needed before drawing the graph

returns an object with the following:
  state - All information that can be put in parameters and adding:
    margin.axisX - margin to accomodate the x-axis
    margin.axisY - margin to acommodate the y-axis

  drawGraph - function to call when ready to draw graph

  scale - Object containing three d3 scales
    x - d3 scale for the x-axis
    y - d3 scale for the y-axis
    stackColor - d3 scale for the stack color

  axis - Object containg the graph's two d3 axis
    x - d3 axis for the x-axis
    y - d3 axis for the y-axis

  svg - d3 pointer to the svg holding the graph

  svgGroup - object holding the svg groups
    main - svg group holding all other groups
    xAxis - svg group holding the x-axis
    yAxis - svg group holding the x-axis
    bars - svg groups holding the bars

  yAxisLabel - d3 pointer to the text component that holds the y axis label

  divTooltip - d3 pointer to the div that is used as the tooltip for the graph

  rects - d3 collection of the rects used in the bars

  legend - object containing information for the legend
    height - height of the legend
    width - width of the legend (if change, need to update state.margin.axisY also)
    range - array of values that appears in the legend
    barHeight - height of a bar in the legend, based on height and length of range
*/

edx_d3CreateStackedBarGraph = function(parameters, svg, divTooltip) {
  var graph = {
    svg : svg,
    state : {
      data : undefined,
      height : 500,
      width : 500,
      margin: {top: 10, bottom: 10, right: 10, left: 10},
      yRange: [0],
      xRange : undefined,
      colorRange : undefined,
      tag : "",
      bVerticalXAxisLabel : false,
      bLegend : true,
    },
    divTooltip : divTooltip,
  };

  var state = graph.state;

  // Handle parameters
  state.data = parameters.data;

  if (parameters.margin != undefined) {
    for (var key in state.margin) {
      if ((state.margin.hasOwnProperty(key) &&
           (parameters.margin[key] != undefined))) {
        state.margin[key] = parameters.margin[key];
      }
    }
  }

  for (var key in state) {
    if ((key != "data") && (key != "margin")) {
      if (state.hasOwnProperty(key) && (parameters[key] != undefined)) {
        state[key] = parameters[key];
      }
    }
  }

  if (state.tag != "")
    state.tag = state.tag+"-";

  if ((state.xRange == undefined) || (state.yRange.length < 2 || 
                                      state.colorRange == undefined)) {
    var aryXRange = [];
    var bXIsOrdinal = false;
    var maxYRange = 0;
    var aryColorRange = [];
    var bColorIsOrdinal = false;

    for (var stackKey in state.data) {
      var stack = state.data[stackKey];
      aryXRange.push(stack.xValue);
      if (isNaN(stack.xValue))
        bXIsOrdinal = true;
      
      var valueTotal = 0;
      for (var barKey in stack.stackData) {
        var bar = stack.stackData[barKey];
        valueTotal += bar.value;

        if (isNaN(bar.color))
          bColorIsOrdinal = true;

        if (aryColorRange.indexOf(bar.color) < 0)
          aryColorRange.push(bar.color);
      }
      if (maxYRange < valueTotal)
        maxYRange = valueTotal;
    }

    if (state.xRange == undefined){
      if (bXIsOrdinal)
        state.xRange = aryXRange;
      else
        state.xRange = [
          Math.min.apply(null,aryXRange),
          Math.max.apply(null,aryXRange)
        ];
    }

    if (state.yRange.length < 2)
      state.yRange[1] = maxYRange;

    if (state.colorRange == undefined){
      if (bColorIsOrdinal)
        state.colorRange = aryColorRange;
      else
        state.colorRange = [
          Math.min.apply(null,aryColorRange),
          Math.max.apply(null,aryColorRange)
        ];
    }
  }

  // Find needed spacing for axes
  var tmpEl = graph.svg.append("text").text(state.yRange[1]+"1234")
    .attr("id",state.tag+"stacked-bar-graph-long-str");
  state.margin.axisY = document.getElementById(state.tag+"stacked-bar-graph-long-str")
    .getComputedTextLength()+state.margin.left;

  var longestXAxisStr = "";
  if (isNaN(state.xRange[0])) {
    for (var i in state.xRange) {
      if (longestXAxisStr.length < state.xRange[i].length)
        longestXAxisStr = state.xRange[i]+"1234";
    }
  } else {
    longestXAxisStr = state.xRange[1]+"1234";
  }

  tmpEl.text(longestXAxisStr);
  if (state.bVerticalXAxisLabel) {
    state.margin.axisX = document.getElementById(state.tag+"stacked-bar-graph-long-str")
      .getComputedTextLength()+state.margin.bottom;
  } else {
    state.margin.axisX = document.getElementById(state.tag+"stacked-bar-graph-long-str")
      .clientHeight+state.margin.bottom;
  }

  tmpEl.remove();

  // Add y0 and y1 of the y-axis based on the count and order of the colorRange.
  // First, case if color is a number range
  if ((state.colorRange.length == 2) && !(isNaN(state.colorRange[0])) &&
    !(isNaN(state.colorRange[1]))) {
    for (var stackKey in state.data) {
      var stack = state.data[stackKey];
      stack.stackData.sort(function(a,b) { return a.color - b.color; });

      var currTotal = 0;
      for (var barKey in stack.stackData) {
        var bar = stack.stackData[barKey];
        bar.y0 = currTotal;
        currTotal += bar.value;
        bar.y1 = currTotal;
      }
    }
  } else {
    for (var stackKey in state.data) {
      var stack = state.data[stackKey];
      
      var tmpStackData = [];
      for (var barKey in stack.stackData) {
        var bar = stack.stackData[barKey];
        tmpStackData[state.colorRange.indexOf(bar.color)] = bar;
      }
      stack.stackData = tmpStackData;

      var currTotal = 0;
      for (var barKey in stack.stackData) {
        var bar = stack.stackData[barKey];
        bar.y0 = currTotal;
        currTotal += bar.value;
        bar.y1 = currTotal;
      }
    }
  }

  // Add information to create legend
  if (state.bLegend) {
    graph.legend = {
      height : (state.height-state.margin.top-state.margin.axisX),
      width : 30,
      range : state.colorRange,
    };
    if ((state.colorRange.length == 2) && !(isNaN(state.colorRange[0])) &&
        !(isNaN(state.colorRange[1]))) {
      graph.legend.range = [];
      
      var i = 0;
      var min = state.colorRange[0];
      var max = state.colorRange[1];
      while (i <= 10) {
        graph.legend.range[i] = min+((max-min)/10)*i;
        i += 1;
      }
    }
    graph.legend.barHeight = graph.legend.height/graph.legend.range.length;
    
    // Shifting the axis over to make room
    graph.state.margin.axisY += graph.legend.width;
  }

  // Make the scales
  graph.scale = {
    x: d3.scale.ordinal()
      .domain(graph.state.xRange)
      .rangeRoundBands([
        (graph.state.margin.axisY),
        (graph.state.width-graph.state.margin.right)],
                       .3),

    y: d3.scale.linear()
      .domain(graph.state.yRange) // yRange is the range of the y-axis values
      .range([
        (graph.state.height-graph.state.margin.axisX),
        graph.state.margin.top
      ]),
    
    stackColor: d3.scale.ordinal()
      .domain(graph.state.colorRange)
      .range(["#ffeeee","#ffebeb","#ffd8d8","#ffc4c4","#ffb1b1","#ff9d9d","#ff8989","#ff7676","#ff6262","#ff4e4e","#ff3b3b"])
  };

  if ((state.colorRange.length == 2) && !(isNaN(state.colorRange[0])) &&
    !(isNaN(state.colorRange[1]))) {
    graph.scale.stackColor = d3.scale.linear()
      .domain(state.colorRange)
      .range(["#e13f29","#17a74d"]);
  }

  // Setup axes
  graph.axis = {
    x: d3.svg.axis()
      .scale(graph.scale.x),
    y: d3.svg.axis()
      .scale(graph.scale.y),
  }

  graph.axis.x.orient("bottom");
  graph.axis.y.orient("left");

  // Draw graph function, to call when ready.
  graph.drawGraph = function() {
    var graph = this;
    
    // Steup SVG
    graph.svg.attr("id", graph.state.tag+"stacked-bar-graph")
      .attr("class", "stacked-bar-graph")
      .attr("width", graph.state.width)
      .attr("height", graph.state.height);
    graph.svgGroup = {};

    graph.svgGroup.main = graph.svg.append("g");

    // Draw Bars
    graph.svgGroup.bars = graph.svgGroup.main.selectAll(".stacked-bar")
      .data(graph.state.data)
      .enter().append("g")
      .attr("class", "stacked-bar")
      .attr("transform", function(d) {
          return "translate("+graph.scale.x(d.xValue)+",0)";
      });

    graph.rects = graph.svgGroup.bars.selectAll("rect")
      .data(function(d) { return d.stackData; })
      .enter().append("rect")
      .attr("width", function(d) {
          return graph.scale.x.rangeBand()
      })
      .attr("y", function(d) { return graph.scale.y(d.y1); })
      .attr("height", function(d) {
        return graph.scale.y(d.y0) - graph.scale.y(d.y1);
      })
      .attr("id", function(d) { return d.module_url })
      .style("fill", function(d) { return graph.scale.stackColor(d.color); })
      .style("stroke", "white")
      .style("stroke-width", "0.5px");

    // Setup tooltip
    if (graph.divTooltip != undefined) {
      graph.divTooltip
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden");
    }

    graph.rects
      .on("mouseover", function(d) {
        var pos = d3.mouse(graph.divTooltip.node().parentNode);
        var left = pos[0]+10;
        var top = pos[1]-10;
        var width = $('#'+graph.divTooltip.attr("id")).width();

        // Construct the tooltip
        if (d.tooltip['type'] == 'subsection') {
	   stud_str = ngettext('%(num_students)s student opened Subsection', '%(num_students)s students opened Subsection', d.tooltip['num_students']);
	   stud_str = interpolate(stud_str, {'num_students': d.tooltip['num_students']}, true);
          tooltip_str = stud_str +  ' '  + d.tooltip['subsection_num'] + ': ' + d.tooltip['subsection_name'];
        }else if (d.tooltip['type'] == 'problem') {
	   stud_str = ngettext('%(num_students)s student', '%(num_students)s students', d.tooltip['count_grade']);
	   stud_str = interpolate(stud_str, {'num_students': d.tooltip['count_grade']}, true);
	   q_str = ngettext('%(num_questions)s question', '%(num_questions)s questions', d.tooltip['max_grade']);
	   q_str = interpolate(q_str, {'num_questions': d.tooltip['max_grade']}, true);

          tooltip_str = d.tooltip['label'] + ' ' + d.tooltip['problem_name'] + ' - ' \
                      + stud_str + ' (' + d.tooltip['student_count_percent'] + '%) (' \
                      + d.tooltip['percent'] + '%: ' + d.tooltip['grade'] +'/' \
	              + q_str + ')';
        }
        graph.divTooltip.style("visibility", "visible")
          .text(tooltip_str);

        if ((left+width+30) > $("#"+graph.divTooltip.node().parentNode.id).width())
          left -= (width+30);
        
        graph.divTooltip.style("top", top+"px")
          .style("left", left+"px");
      })
      .on("mouseout", function(d){
        graph.divTooltip.style("visibility", "hidden")
      });

    // Add legend
    if (graph.state.bLegend) {
      graph.svgGroup.legendG = graph.svgGroup.main.append("g")
        .attr("class","stacked-bar-graph-legend")
        .attr("transform","translate("+graph.state.margin.left+","+
              graph.state.margin.top+")");
      graph.svgGroup.legendGs = graph.svgGroup.legendG.selectAll(".stacked-bar-graph-legend-g")
        .data(graph.legend.range)
        .enter().append("g")
        .attr("class","stacked-bar-graph-legend-g")
        .attr("id",function(d,i) { return graph.state.tag+"legend-"+i; })
        .attr("transform", function(d,i) {
          return "translate(0,"+
            (graph.state.height-graph.state.margin.axisX-((i+1)*(graph.legend.barHeight))) + ")";
        });
      
      graph.svgGroup.legendGs.append("rect")
        .attr("class","stacked-bar-graph-legend-rect")
        .attr("height", graph.legend.barHeight)
        .attr("width", graph.legend.width)
        .style("fill", graph.scale.stackColor)
        .style("stroke", "white");

      graph.svgGroup.legendGs.append("text")
        .attr("class","axis-label")
        .attr("transform", function(d) {
          var str = "translate("+(graph.legend.width/2)+","+
            (graph.legend.barHeight/2)+")";
          return str;
        })
        .attr("dy", ".35em")
        .attr("dx", "-1px")
        .style("text-anchor", "middle")
        .text(function(d,i) { return d; });
    }


    // Draw Axes
    graph.svgGroup.xAxis = graph.svgGroup.main.append("g")
      .attr("class","stacked-bar-graph-axis")
      .attr("id",graph.state.tag+"x-axis");

    var tmpS = "translate(0,"+(graph.state.height-graph.state.margin.axisX)+")";
    if (graph.state.bVerticalXAxisLabel) {
      graph.axis.x.orient("left");
      tmpS = "rotate(270), translate(-"+(graph.state.height-graph.state.margin.axisX)+",0)";
    }
    graph.svgGroup.xAxis.attr("transform", tmpS)
      .call(graph.axis.x);

    graph.svgGroup.yAxis = graph.svgGroup.main.append("g")
      .attr("class","stacked-bar-graph-axis")
      .attr("id",graph.state.tag+"y-axis")
      .attr("transform","translate("+
            (graph.state.margin.axisY)+",0)")
      .call(graph.axis.y);
    graph.yAxisLabel = graph.svgGroup.yAxis.append("text")
      .attr("dy","1em")
      .attr("transform","rotate(-90)")
      .style("text-anchor","end")
      .text(gettext("Number of Students"));
  };

  return graph;
};
