define(['jquery', 'underscore', 'js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils'],
function($, _, BaseView, HtmlUtils) {
    'use strict';

    /**
     * TagCountView displays the tag count of a unit/component
     * 
     * This component is being rendered in this way to allow receiving
     * messages from the Manage tags drawer and being able to update the count.
     */
    var TagCountView = BaseView.extend({
        // takes TagCountModel as a model

        initialize: function() {
            BaseView.prototype.initialize.call(this);
            this.template = this.loadTemplate('tag-count');
        },

        setupMessageListener: function () {
            window.addEventListener(
                'message', (event) => {
                    // Listen any message from Manage tags drawer.
                    var data = event.data;
                    var courseAuthoringUrl = this.model.get("course_authoring_url")
                    if (event.origin == courseAuthoringUrl
                        && data.includes('[Manage tags drawer] Count updated:')) {
                        // This message arrives when there is a change in the tag list.
                        // The message contains the new count of tags.
                        let jsonData = data.replace(/\[Manage tags drawer\] Count updated: /g, "");
                        jsonData = JSON.parse(jsonData);
                        if (jsonData.contentId == this.model.get("content_id")) {
                            this.model.set('tags_count', jsonData.count);
                            this.render();
                        }
                    }
                }
            );
        },
    
        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                HtmlUtils.HTML(
                    this.template({
                        tags_count: this.model.get("tags_count"),
                    })
                )
            );
            return this;
        }
    });

    return TagCountView;
});
