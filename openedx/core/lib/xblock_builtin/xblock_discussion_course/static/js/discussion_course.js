/* globals DiscussionUtil, DiscussionApp, DiscussionProfileApp */
var $$course_id = "{{course_id}}";

function DiscussionCourseBlock(runtime, element) {
    var testUrl = runtime.handlerUrl(element, 'test');
    if (testUrl.match(/^(http|https):\/\//)) {
        var hostname = testUrl.match(/^(.*:\/\/[a-z0-9:\-.]+)\//)[1];
        DiscussionUtil.setBaseUrl(hostname);
    }

    DiscussionUtil.force_async = true;

    loadDiscussionApp();
}
