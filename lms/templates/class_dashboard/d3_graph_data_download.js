/*
Parameters:
(1) csvstring
    A newline joined, comma separated datapoints. It must have a header and one of the columns must be named 'Date'
   example: "Date,New Threads,Responses,Comments\n2014-10-10,2,0,0\n2014-10-11,1,1,0\n2014-10-12,1,5,2It draws
(2) className
    Class of the html element to draw the svg in
 */

d3_graph_data_download = function(csvstring, className) {
    data = d3.csv.parse(csvstring);
    var margin = {top: 20, right: 80, bottom: 30, left: 50},
        width = $('.report-downloads-graph').parent().width() - margin.left - margin.right;
        height = 500 - margin.top - margin.bottom;
    var parseDate = d3.time.format("%Y-%m-%d").parse;
    var color = d3.scale.category10();
    var barWidth =  (width-300)/data.length;
    //leaving extra space to the right for the legend
    var x = d3.time.scale()
        .range([20, width-barWidth-70]);

    var y = d3.scale.linear()
        .rangeRound([height, 0]);

    //these colors don't exactly correspond to the exact elements in the graph but to generate them
    //we read the header to generate the colors
    var header = d3.keys(data[0]);
    var coloredHeader = header.map(color);

    var color = d3.scale.ordinal()
        .range(coloredHeader);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .ticks(Math.min(5, data.length));
    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .tickFormat(d3.format(".2s"));

    //clear div in case there is another graph in it
    $("."+className).html("");
    var svg = d3.select(".report-downloads-graph").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    color.domain(d3.keys(data[0]).filter(function(key) { return key !== "Date"; }));

    data.forEach(function(d) {
        d.date = parseDate(d.Date);
        var y0 = 0;
        d.counts = color.domain().map(function(name) {
            return {
                name: name, y0: y0, y1: y0 += +d[name]}; });
        d.total = d.counts[d.counts.length - 1].y1;
    });

    x.domain(d3.extent(data, function(d) { return d.date; }));
    y.domain([0, d3.max(data, function(d) { return d.total; })]);

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate("+  barWidth/2 +"," +height + ")")
        .call(xAxis);
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Count");

    var state = svg.selectAll(".state")
        .data(data)
        .enter().append("g")
        .attr("class", "g")
        .attr("transform", function(d) {
            var st = "translate(" + x(d.date) + ",0)";
            return st;
        });

    state.selectAll("rect")
        .data(function(d) { return d.counts; })
        .enter().append("rect")
        .attr("width", barWidth)
        .attr("y", function(d) { return y(d.y1); })
        .attr("height", function(d) { return y(d.y0) - y(d.y1); })
        .style("fill", function(d) { return color(d.name); });

    var legend = svg.selectAll(".legend")
        .data(color.domain().slice().reverse())
        .enter().append("g")
        .attr("class", "legend")
        .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("rect")
        .attr("x", width )
        .attr("width", 18)
        .attr("height", 18)
        .style("fill", color);

    legend.append("text")
        .attr("x", width-5)
        .attr("y", 9)
        .attr("dy", ".35em")
        .style("text-anchor", "end")
        .text(function(d) { return d; });

};
