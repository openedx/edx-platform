var $$course_id = "{{course_id}}";

function DiscussionInlineBlock(runtime, element) {
    var el = $(element).find('.discussion-module');
    new DiscussionModuleView({ el: el });
}