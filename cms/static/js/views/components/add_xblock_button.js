define(['js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils'],
    function(BaseView, HtmlUtils) {
        'use strict';

        return BaseView.extend({
            tagName: 'li',
            initialize: function() {
                var attributes = {
                    type: this.model.type,
                    templates: this.model.templates,
<<<<<<< HEAD
                    display_name: this.model.display_name
=======
                    display_name: this.model.display_name,
                    beta: this.model.beta,
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                };
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('add-xblock-component-button');
                this.$el.html(HtmlUtils.HTML(this.template(attributes)).toString()
                );
            }
        });
    }); // end define();
