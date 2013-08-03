<%page args="id_str, i, data, width, height, tag, **kwargs"/>
<%!
  import json
%>

$(function () {
  var data${i} = ${json.dumps(data)}
  console.log("Section ${i}")
  console.log(data${i});

  if (data${i}.length > 0) {
    var svg${i} = d3.select("#${id_str}").append("svg")
      .attr("id", "attempts_svg_${i}");
    var div${i} = d3.select("#${id_str}").append("div");
    var param${i} = {
      data: data${i},
      width: ${width},
      height: ${height},
      tag: "${tag}",
    };
    var barGraph${i} = edx_d3CreateStackedBarGraph(param${i}, svg${i}, div${i});
    barGraph${i}.drawGraph();
  } else {
    d3.select("#${id_str}").append("div")
      .append("p").text("No problems for this section");
  }
});