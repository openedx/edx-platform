CMS.ServerError = function(model, error) {
    var m = new CMS.Models.SystemFeedback({
        "type": "error",
        "title": "Server Error",
        "message": error.responseText,
        "actions": {
            "primary": {
                "text": "Dismiss",
                "click": function(model) {
                    model.hide();
                }
            }
        }
    });
    new CMS.Views.Notification({model: m});
    return m;
};
