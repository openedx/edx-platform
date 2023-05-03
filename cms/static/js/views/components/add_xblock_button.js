define(['js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils'],
    function(BaseView, HtmlUtils) {
        'use strict';
        return BaseView.extend({
            tagName: 'li',
            initialize: function() {
                var attributes = {
                    type: this.model.type,
                    templates: this.model.templates,
                    display_name: this.model.display_name
                };
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('add-xblock-component-button');
                this.$el.html(HtmlUtils.HTML(this.template(attributes)).toString()
                );
            }
        });
    }); // end define();
