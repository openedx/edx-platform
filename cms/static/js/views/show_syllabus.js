define(["js/views/baseview", "underscore", "gettext", "js/views/feedback_notification", "js/views/feedback_prompt"],
        function(BaseView, _, gettext, NotificationView, PromptView) {
    var ShowSyllabus = BaseView.extend({
        initialize: function() {
            this.template = _.template($("#show-syllabus-tpl").text());
            this.listenTo(this.model, "change", this.render);
        },
        tagName: "section",
        className: "syllabus",
        events: {
            "click .edit": "editSyllabus",
            "click .delete": "confirmDelete",
            "click .show-topics": "showTopics",
            "click .hide-topics": "hideTopics"
        },
        render: function() {
            var attrs = $.extend({}, this.model.attributes);
            attrs.bookindex = this.model.collection.indexOf(this.model);
            attrs.course = window.course.attributes;
            this.$el.html(this.template(attrs));
            return this;
        },
        editSyllabus: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set("editing", true);
        },
        confirmDelete: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            var syllabus = this.model, collection = this.model.collection;
            var msg = new PromptView.Warning({
                title: _.template(gettext("Delete “<%= name %>”?"),
                    {name: syllabus.escape('name')}),
                message: gettext("Deleting a syllabus cannot be undone and once deleted any reference to it in your courseware's navigation will also be removed."),
                actions: {
                    primary: {
                        text: gettext("Delete"),
                        click: function(view) {
                            view.hide();
                            var delmsg = new NotificationView.Mini({
                                title: gettext("Deleting") + "&hellip;"
                            }).show();
                            syllabus.destroy({
                                complete: function() {
                                    delmsg.hide();
                                }
                            });
                        }
                    },
                    secondary: {
                        text: gettext("Cancel"),
                        click: function(view) {
                            view.hide();
                        }
                    }
                }
            }).show();
        },
        showTopics: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showTopics', true);
        },
        hideTopics: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showTopics', false);
        }
    });
    return ShowSyllabus;
});
