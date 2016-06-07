define(["jquery"], function($) {
    // Trigger "Change" event on "Enter" keyup event
    var triggerChangeEventOnEnter = function (e) {
        if(e.which == 13)
        {
            $(this).trigger("change").blur();
        }
    };

    return triggerChangeEventOnEnter;
});
