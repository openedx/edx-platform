CMS.Models.SystemFeedback = Backbone.Model.extend({
    defaults: {
        "type": null,  // "warning", "confirmation", "error", "announcement", "step-required"
        "title": null,
        "message": null,
        "shown": true,
        "close": false  // show a close button?
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
    }
});
