define(
    [
        'js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils', 'text!templates/video-status.underscore'
    ],
    function(BaseView, HtmlUtils, videoStatusTemplate) {
        'use strict';

        var VideoStatusView = BaseView.extend({
            tagName: 'div',

            initialize: function(options) {
                this.status = options.status;
                this.showError = options.showError;
                this.errorDescription = options.errorDescription;
                this.template = HtmlUtils.template(videoStatusTemplate);
            },

            /*
            Renders status view.
            */
            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        status: this.status,
                        show_error: this.showError,
                        error_description: this.errorDescription
                    })
                );

                return this;
            }
        });

        return VideoStatusView;
    }
);
