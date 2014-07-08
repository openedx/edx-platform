define(['js/views/baseview', 'jquery', 'js/views/group_configuration_details'],
function(BaseView, $, GroupConfigurationDetailsView) {
    'use strict';
    var GroupConfigurationsList = BaseView.extend({
        tagName: 'div',
        className: 'group-configurations-list',
        events: { },

        initialize: function() {
            this.emptyTemplate = this.loadTemplate('no-group-configurations');
            this.listenTo(this.collection, 'all', this.render);
        },

        render: function() {
            var configurations = this.collection;
            if(configurations.length === 0) {
                this.$el.html(this.emptyTemplate());
            } else {
                var frag = document.createDocumentFragment();

                configurations.each(function(configuration) {
                    var view = new GroupConfigurationDetailsView({
                        model: configuration
                    });

                    frag.appendChild(view.render().el);
                });

                this.$el.html([frag]);
            }
            return this;
        }
    });

    return GroupConfigurationsList;
});
