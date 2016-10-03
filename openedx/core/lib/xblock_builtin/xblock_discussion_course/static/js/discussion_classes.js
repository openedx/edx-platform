// Add RequireJS definitions for each discussion class

var discussionClasses = [
    ['Discussion', 'common/js/discussion/discussion'],
    ['DiscussionModuleView', 'common/js/discussion/discussion_module_view'],
    ['DiscussionThreadView', 'common/js/discussion/views/discussion_thread_view'],
    ['DiscussionThreadListView', 'common/js/discussion/views/discussion_thread_list_view'],
    ['DiscussionThreadProfileView', 'common/js/discussion/views/discussion_thread_profile_view'],
    ['DiscussionUtil', 'common/js/discussion/utils'],
    ['NewPostView', 'common/js/discussion/views/new_post_view']
];

var defineDiscussionClasses = function(define) {
    'use strict';
    discussionClasses.forEach(function(discussionClass) {
        define(
            discussionClass[1],
            [],
            function() {
                return window[discussionClass[0]];
            }
        );
    });
};

if (typeof RequireJS === 'undefined') {
    var vendorScript = document.createElement("script");
    vendorScript.onload = function() {
        'use strict';
        defineDiscussionClasses(define);
    };
    vendorScript.src = "/static/js/vendor/requirejs/require.js";
    document.body.appendChild(vendorScript);

} else {
    defineDiscussionClasses(RequireJS.define);
}
