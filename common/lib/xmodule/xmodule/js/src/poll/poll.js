window.Poll = function (el) {
    RequireJS.require(['PollMain'], function (PollMain) {
        $(el).children('.poll').each(function (index, value) {
            PollMain.initialize($(value));
        });
    });
};
