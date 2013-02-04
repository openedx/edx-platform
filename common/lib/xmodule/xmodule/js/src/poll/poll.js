window.Poll = function (el) {
    RequireJS.require(['PollMain'], function (PollMain) {
        var pObj;

        pObj = new PollMain();
        pObj.vertModule = $(el).parent().parent();

        pObj.initializePollQuestion(pObj.vertModule.find('.poll_question'));

        pObj.vertModule.find('.xmodule_ConditionalModule').each(function (key, value) {
            pObj.initializePollConditional($(value));
        });
    });
};
