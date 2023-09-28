define(['backbone', 'gettext', 'underscore'], function(Backbone, gettext, _) {
    /**
     * Model for xblock validation messages as displayed in Studio.
     */
    var XBlockValidationModel = Backbone.Model.extend({
        defaults: {
            summary: {},
            messages: [],
            empty: true,
            xblock_id: null
        },

        WARNING: 'warning',
        ERROR: 'error',
        NOT_CONFIGURED: 'not-configured',

        parse: function(response) {
            if (!response.empty) {
                var summary = 'summary' in response ? response.summary : {};
                var messages = 'messages' in response ? response.messages : [];
                if (!summary.text) {
                    if (response.isUnit) {
                        summary.text = gettext('This unit has validation issues.');
                    } else {
                        summary.text = gettext('This component has validation issues.');
                    }
                }
                if (!summary.type) {
                    summary.type = this.WARNING;
                    // Possible types are ERROR, WARNING, and NOT_CONFIGURED. NOT_CONFIGURED is treated as a warning.
                    _.find(messages, function(message) {
                        if (message.type === this.ERROR) {
                            summary.type = this.ERROR;
                            return true;
                        }
                        return false;
                    }, this);
                }
                response.summary = summary;
                if (response.showSummaryOnly) {
                    messages = [];
                }
                response.messages = messages;
            }

            return response;
        }
    });
    return XBlockValidationModel;
});
