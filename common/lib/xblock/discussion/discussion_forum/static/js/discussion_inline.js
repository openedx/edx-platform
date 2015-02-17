var $$course_id = "{{course_id}}";

function DiscussionInlineBlock(runtime, element) {
  var el = $(element).find('.discussion-module');

  var testUrl = runtime.handlerUrl(element, 'test');
  if (testUrl.match(/^(http|https):\/\//)) {
    var hostname = testUrl.match(/^(.*:\/\/[a-z0-9:\-.]+)\//)[1];
    DiscussionUtil.setBaseUrl(hostname);
  }

  if (runtime.local_overrides && runtime.local_overrides.discussion) {
      runtime.local_overrides.discussion(element, DiscussionUtil);
  }

  new DiscussionModuleView({ el: el });
}
