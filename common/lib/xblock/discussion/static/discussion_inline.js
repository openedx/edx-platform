/* global DiscussionModuleView */
/* exported DiscussionInlineBlock, $$course_id */
var $$course_id = "{{course_id}}";

function DiscussionInlineBlock(runtime, element) {
    'use strict';
    var el = $(element).find('.discussion-module');
    new DiscussionModuleView({ el: el });
}