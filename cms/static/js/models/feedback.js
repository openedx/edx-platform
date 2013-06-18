CMS.Models.SystemFeedback = Backbone.Model.extend({
    defaults: {
        "intent": null,  // "warning", "confirmation", "error", "announcement", "step-required", etc
        "title": "",
        "message": ""
        /* could also have an "actions" hash: here is an example demonstrating
           the expected structure
        "actions": {
            "primary": {
                "text": "Save",
                "class": "action-save",
                "click": function() {
                    // do something when Save is clicked
                    // `this` refers to the model
                }
            },
            "secondary": [
                {
                    "text": "Cancel",
                    "class": "action-cancel",
                    "click": function() {}
                }, {
                    "text": "Discard Changes",
                    "class": "action-discard",
                    "click": function() {}
                }
            ]
        }
        */
    }
});

CMS.Models.WarningMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "intent": "warning"
    })
});

CMS.Models.ErrorMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "intent": "error"
    })
});

CMS.Models.ConfirmAssetDeleteMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "intent": "warning"
    })
});

CMS.Models.ConfirmationMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "intent": "confirmation"
    })
});
