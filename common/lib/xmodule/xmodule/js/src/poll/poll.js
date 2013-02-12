window.Poll = function (el) {
    RequireJS.require(['PollMain'], function (PollMain) {
        new PollMain(el);
    });
};
