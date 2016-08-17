define(["js/views/baseview", "underscore", "gettext", "common/js/components/views/feedback_notification",
        "common/js/components/views/feedback_prompt"],
        function(BaseView, _, gettext, NotificationView, PromptView) {
    var ShowTextbook = BaseView.extend({
        initialize: function() {
            this.template = _.template($("#show-textbook-tpl").text());
            this.listenTo(this.model, "change", this.render);
        },
        tagName: "section",
        className: "textbook",
        events: {
            "click .edit": "editTextbook",
            "click .delete": "confirmDelete",
            "click .show-chapters": "showChapters",
            "click .hide-chapters": "hideChapters"
        },
        render: function() {
            var attrs = $.extend({}, this.model.attributes);
            attrs.bookindex = this.model.collection.indexOf(this.model);
            attrs.course = window.course.attributes;
            this.$el.html(this.template(attrs));
            return this;
        },
        editTextbook: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set("editing", true);
        },
        confirmDelete: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            var textbook = this.model, collection = this.model.collection;
            var msg = new PromptView.Warning({
                title: _.template(gettext("Delete “<%= name %>”?"),
                    {name: textbook.escape('name')}),
                message: gettext("Deleting a textbook cannot be undone and once deleted any reference to it in your courseware's navigation will also be removed."),
                actions: {
                    primary: {
                        text: gettext("Delete"),
                        click: function(view) {
                            view.hide();
                            var delmsg = new NotificationView.Mini({
                                title: gettext("Deleting")
                            }).show();
                            textbook.destroy({
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
        showChapters: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showChapters', true);
        },
        hideChapters: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showChapters', false);
        }
    });
    return ShowTextbook;
});
