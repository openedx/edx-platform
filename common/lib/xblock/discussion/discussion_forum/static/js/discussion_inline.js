var $$course_id = "{{course_id}}";

function DiscussionInlineBlock(runtime, element) {
  var el = $(element).find('.discussion-module');

  var testUrl = runtime.handlerUrl(element, 'test');
  if (testUrl.match(/^(http|https):\/\//)) {
    var hostname = testUrl.match(/^(.*:\/\/[a-z0-9:\-.]+)\//)[1];
    DiscussionUtil.setBaseUrl(hostname);
    DiscussionUtil.force_async = true;
  }

  new DiscussionModuleView({ el: el });
}
