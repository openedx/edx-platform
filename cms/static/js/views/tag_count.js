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
                    var courseAuthoringUrl = new URL(this.model.get("course_authoring_url")).origin;
                    if (event.origin == courseAuthoringUrl
                        && data.type == 'authoring.events.tags.count.updated') {
                        // This message arrives when there is a change in the tag list.
                        // The message contains the new count of tags.
                        data = data.data
                        if (data.contentId == this.model.get("content_id")) {
                            this.model.set('tags_count', data.count);
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
