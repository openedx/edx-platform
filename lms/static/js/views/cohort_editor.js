(function(Backbone, _, $) {
    var CohortMessageView = Backbone.View.extend({
        events : {
            "click .action-expand": "showAllErrors"
        },

        initialize: function() {
            this.template = _.template($('#cohort-messages-tpl').text());
        },

        render: function() {
            this.showMessages(false);
            return this;
        },

        showAllErrors: function(event) {
            event.preventDefault();
            this.showMessages(true);
        },

        showMessages: function(showAllErrors) {
            var numAdded = this.model.get("added").length + this.model.get("changed").length;
            var movedByCohort = {};
            _.each(this.model.get("changed"), function (changedInfo) {
                var oldCohort = changedInfo.previous_cohort;
                if (oldCohort in movedByCohort) {
                    movedByCohort[oldCohort] = movedByCohort[oldCohort] + 1;
                }
                else {
                    movedByCohort[oldCohort] = 1;
                }
            });

            this.$el.html(this.template({
                numAdded: numAdded,
                moved: movedByCohort,
                numPresent: this.model.get("present").length,
                unknown: this.model.get("unknown"),
                showAllErrors: showAllErrors
            }));
        }
    });

    this.CohortMessageView = CohortMessageView;
}).call(this, Backbone, _, $);

(function(Backbone, _, $, CohortMessageView, CohortMessageModel) {
    var CohortEditorView = Backbone.View.extend({
        events : {
            // NOTE: this is causing a bug because listeners are never unregistered
            // when a different cohort is shown (so any cohort that has ever been shown
            // will handle the event).
            "submit .cohort-management-group-add-form": "addStudents"
        },

        initialize: function() {
            this.template = _.template($('#cohort-editor-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model
            }));
            return this;
        },

        addStudents: function(event) {
            event.preventDefault();
            var input = this.$('.cohort-management-group-add-students'),
                add_url = this.model.url() + '/add',
                data = {'users': input.val()},
                addNotifications = this.addNotifications;
            $.post(add_url, data).done(function(modifiedUsers) {
                addNotifications(modifiedUsers);
            });
        },

        addNotifications: function(modifiedUsers) {
            console.log("in addNotifications");
            this.messages = new CohortMessageView({
                el: this.$('.cohort-messages'),
                model: new CohortMessageModel(modifiedUsers)
            });
            this.messages.render();
        }
    });

    this.CohortEditorView = CohortEditorView;
}).call(this, Backbone, _, $, CohortMessageView, CohortMessageModel);



