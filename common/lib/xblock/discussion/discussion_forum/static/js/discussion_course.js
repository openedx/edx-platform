var $$course_id = "{{course_id}}";

function DiscussionCourseBlock(runtime, element) {
  var el = $(element).find('section.discussion');
  el.data('pushState', 'false');

  var testUrl = runtime.handlerUrl(element, 'test');
  if (testUrl.match(/^(http|https):\/\//)) {
    var hostname = testUrl.match(/^(.*:\/\/[a-z\-.]+)\//)[1];
    DiscussionUtil.setBaseUrl(hostname);
  }
}
