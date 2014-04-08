define(["js/views/baseview", "underscore", "jquery"], function(BaseView, _, $) {
    var UtilityView = BaseView.extend({
        // takes CMS.Models.Utilities as model

        events : {
            'click .course-utility .utility-title' : "toggleUtility",
            'click .course-checkutilitylist .task input' : "toggleTask",
            'click a[rel="external"]' : "popup"
        },

        initialize : function() {
            var self = this;
            this.template = _.template($("#utility-tpl").text());
            this.collection.fetch({
                reset: true,
                complete: function() {
                    self.render();
                }
            });
        },

        render: function() {
            // catch potential outside call before template loaded
            if (!this.template) return this;

            this.$el.empty();

            var self = this;
            _.each(this.collection.models,
                function(utility, index) {
                    self.$el.append(self.renderTemplate(utility, index));
                });

            return this;
        },

        renderTemplate: function (utility, index) {
            var utilityItems = utility.attributes['items'];
            var itemsChecked = 0;
            _.each(utilityItems,
                function(utility) {
                    if (utility['is_checked']) {
                        itemsChecked +=1;
                    }
                });
            var percentChecked = Math.round((itemsChecked/utilityItems.length)*100);
            return this.template({
                utilityIndex : index,
                utilityShortDescription : utility.attributes['short_description'],
                items: utilityItems,
                itemsChecked: itemsChecked,
                percentChecked: percentChecked});
        },

        toggleUtility : function(e) {
            e.preventDefault();
            $(e.target).closest('.course-utility').toggleClass('is-collapsed');
        },

        toggleTask : function (e) {
            var self = this;

            var completed = 'is-completed';
            var $checkbox = $(e.target);
            var $task = $checkbox.closest('.task');
            $task.toggleClass(completed);

            var utility_index = $checkbox.data('utility');
            var task_index = $checkbox.data('task');
            var model = this.collection.at(utility_index);
            model.attributes.items[task_index].is_checked = $task.hasClass(completed);

            model.save({},
                {
                    success : function() {
                        var updatedTemplate = self.renderTemplate(model, utility_index);
                        self.$el.find('#course-utility'+utility_index).first().replaceWith(updatedTemplate);

                        analytics.track('Toggled a Utility Task', {
                            'course': course_location_analytics,
                            'task': model.attributes.items[task_index].short_description,
                            'state': model.attributes.items[task_index].is_checked
                        });
                    }
                });
        },
        popup: function(e) {
            e.preventDefault();
            window.open($(e.target).attr('href'));
        }
    });
    return UtilityView;
});
