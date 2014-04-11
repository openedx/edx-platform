define(["js/views/baseview", "underscore", "jquery"], function(BaseView, _, $) {
    var ChecklistView = BaseView.extend({
        // takes CMS.Models.Checklists as model

        events : {
            'click .course-checklist .checklist-title' : "toggleChecklist",
            'click .course-checklist .task input' : "toggleTask",
            'click a[rel="external"]' : "popup"
        },

        initialize : function() {
            var self = this;
            this.template = this.loadTemplate('checklist');
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
                function(checklist, index) {
                    self.$el.append(self.renderTemplate(checklist, index));
                });

            return this;
        },

        renderTemplate: function (checklist, index) {
            var checklistItems = checklist.attributes['items'];
            var itemsChecked = 0;
            _.each(checklistItems,
                function(checklist) {
                    if (checklist['is_checked']) {
                        itemsChecked +=1;
                    }
                });
            var percentChecked = Math.round((itemsChecked/checklistItems.length)*100);
            return this.template({
                checklistIndex : index,
                checklistShortDescription : checklist.attributes['short_description'],
                items: checklistItems,
                itemsChecked: itemsChecked,
                percentChecked: percentChecked});
        },

        toggleChecklist : function(e) {
            e.preventDefault();
            $(e.target).closest('.course-checklist').toggleClass('is-collapsed');
        },

        toggleTask : function (e) {
            var self = this;

            var completed = 'is-completed';
            var $checkbox = $(e.target);
            var $task = $checkbox.closest('.task');
            $task.toggleClass(completed);

            var checklist_index = $checkbox.data('checklist');
            var task_index = $checkbox.data('task');
            var model = this.collection.at(checklist_index);
            model.attributes.items[task_index].is_checked = $task.hasClass(completed);

            model.save({},
                {
                    success : function() {
                        var updatedTemplate = self.renderTemplate(model, checklist_index);
                        self.$el.find('#course-checklist'+checklist_index).first().replaceWith(updatedTemplate);

                        analytics.track('Toggled a Checklist Task', {
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
    return ChecklistView;
});
