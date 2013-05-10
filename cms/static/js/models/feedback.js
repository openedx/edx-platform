CMS.Models.SystemFeedback = Backbone.Model.extend({
    defaults: {
        "type": null,  // "warning", "confirmation", "error", "announcement", "step-required", etc
        "title": null,
        "message": null,
        "shown": true,
        "close": false,  // show a close button?
        "icon": true,  // show an icon?
        "status": false  // example: "saving" popup
        /* could also have an "actions" hash: here is an example demonstrating
           the expected structure
        "actions": {
            "primary": {
                "text": "Save",
                "class": "action-save",
                "click": function(model) {
                    // do something when Save is clicked
                }
            },
            "secondary": [
                {
                    "text": "Cancel",
                    "class": "action-cancel",
                    "click": function(model) {}
                }, {
                    "text": "Discard Changes",
                    "class": "action-discard",
                    "click": function(model) {}
                }
            ]
        }
        */
    },
    show: function() {
        this.set("shown", true);
    },
    hide: function() {
        this.set("shown", false);
    }
});

CMS.Models.WarningMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "type": "warning"
    })
});

CMS.Models.ErrorMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "type": "error"
    })
});

CMS.Models.ConfirmationMessage = CMS.Models.SystemFeedback.extend({
    defaults: $.extend({}, CMS.Models.SystemFeedback.prototype.defaults, {
        "type": "confirmation"
    })
});
