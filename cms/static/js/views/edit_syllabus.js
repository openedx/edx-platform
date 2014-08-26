define(["js/views/baseview", "underscore", "jquery", "js/views/edit_topic", "js/views/feedback_notification"],
        function(Baseview, _, $, EditTopicView, NotificationView) {
    var EditSyllabus = Backbone.View.extend({
        initialize: function() {
            this.template = _.template($("#edit-syllabus-tpl").text());
            this.listenTo(this.model, "invalid", this.render);
            var topics = this.model.get('topics');
            this.listenTo(topics, "add", this.addOne);
            this.listenTo(topics, "reset", this.addAll);
            this.listenTo(topics, "all", this.render);
        },
        tagName: "section",
        className: "syllabus",
        render: function() {
            this.$el.html(this.template({
                name: this.model.escape('name'),
                error: this.model.validationError
            }));
            this.addAll();
            return this;
        },
        events: {
            "change input[name=syllabus-name]": "setName",
            "submit": "setAndClose",
            "click .action-cancel": "cancel",
            "click .action-add-topic": "createTopic"
        },
        addOne: function(topic) {
            var view = new EditTopicView({model: topic});
            this.$("ol.topics").append(view.render().el);
            return this;
        },
        addAll: function() {
            this.model.get('topics').each(this.addOne, this);
        },
        createTopic: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.setValues();
            this.model.get('topics').add([{}]);
        },
        setName: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set("name", this.$("#syllabus-name-input").val(), {silent: true});
        },
        setValues: function() {
            this.setName();
            var that = this;
            _.each(this.$("li"), function(li, i) {
                var topic = that.model.get('topics').at(i);
                if(!topic) { return; }
                topic.set({
                    "name": $(".topic-name", li).val(),
                    "description": $(".topic-description", li).val()
                });
            });
            return this;
        },
        setAndClose: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.setValues();
            if(!this.model.isValid()) { return; }
            var saving = new NotificationView.Mini({
                title: gettext("Saving") + "&hellip;"
            }).show();
            var that = this;
            this.model.save({}, {
                success: function() {
                    that.model.setOriginalAttributes();
                    that.close();
                },
                complete: function() {
                    saving.hide();
                }
            });
        },
        cancel: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.reset();
            return this.close();
        },
        close: function() {
            var syllabuses = this.model.collection;
            this.remove();
            if(this.model.isNew()) {
                // if the textbook has never been saved, remove it
                syllabuses.remove(this.model);
            }
            // don't forget to tell the model that it's no longer being edited
            this.model.set("editing", false);
            return this;
        }
    });
    return EditSyllabus;
});
