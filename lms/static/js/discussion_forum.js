/* globals DiscussionApp, DiscussionProfileApp */
function loadDiscussionApp() {
    $("section.discussion").each(function(index, elem) {
        DiscussionApp.start(elem);
    });
    $("section.discussion-user-threads").each(function(index, elem) {
        DiscussionProfileApp.start(elem);
    });
}
$(loadDiscussionApp);
