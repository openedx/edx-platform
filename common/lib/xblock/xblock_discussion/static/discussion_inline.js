/* global DiscussionModuleView */
/* exported DiscussionInlineBlock, $$course_id */
var $$course_id = "{{course_id}}";

function DiscussionInlineBlock(runtime, element) {
    'use strict';
    var el = $(element).find('.discussion-module');
    /* jshint nonew:false */
    new DiscussionModuleView({ el: el });
}
