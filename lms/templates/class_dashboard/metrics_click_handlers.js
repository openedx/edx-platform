<%page args="section_data"/>

$(function () {

  // Click handler for x axis major ticks
  $('.metrics-container').on('click', '.stacked-bar-graph-axis .tick.major', function () {

    var stackedBarElement;
    var xValue;
    var moduleId;
    var tickIdentifier = d3.select(this).text();
    var i;
    var stackedBars;
    var stackedBarElement;
    var url;

    stackedBars = $(this).parent().siblings();
    for (i = 0; i < stackedBars.length; i++) {
      stackedBarElement = stackedBars[i];
      if (stackedBarElement.getAttribute('class') === 'stacked-bar') {
        xValue = d3.select(stackedBarElement).data()[0].xValue;
        if (xValue === tickIdentifier) {
          moduleId = d3.select(stackedBarElement).data()[0].stackData[0].module_url;
          break;
        }
      }
    }

    url = [
        '/courses',
        "${section_data['course_id']}",
        'jump_to',
        moduleId
    ].join('/');
    window.location.href = url;
  });
});
