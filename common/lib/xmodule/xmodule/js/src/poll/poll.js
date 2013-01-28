window.Poll = function (el) {
    console.log('one');
    RequireJS.require(['PollMain'], function (PollMain) {
        console.log('two');
        $(el).children('.poll').each(function (index, value) {
            console.log('three');
            PollMain.initialize($(value));
        });
    });
};
