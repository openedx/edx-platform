define(["backbone", "underscore", "jquery", "js/views/edit_chapter", "js/views/feedback_notification"],
        function(Backbone, _, $, EditChapterView, NotificationView) {
    var EditTextbook = Backbone.View.extend({
        initialize: function() {
            this.template = _.template($("#edit-textbook-tpl").text());
            this.listenTo(this.model, "invalid", this.render);
            var chapters = this.model.get('chapters');
            this.listenTo(chapters, "add", this.addOne);
            this.listenTo(chapters, "reset", this.addAll);
            this.listenTo(chapters, "all", this.render);
        },
        tagName: "section",
        className: "textbook",
        render: function() {
            this.$el.html(this.template({
                name: this.model.escape('name'),
                error: this.model.validationError
            }));
            this.addAll();
            return this;
        },
        events: {
            "change input[name=textbook-name]": "setName",
            "submit": "setAndClose",
            "click .action-cancel": "cancel",
            "click .action-add-chapter": "createChapter"
        },
        addOne: function(chapter) {
            var view = new EditChapterView({model: chapter});
            this.$("ol.chapters").append(view.render().el);
            return this;
        },
        addAll: function() {
            this.model.get('chapters').each(this.addOne, this);
        },
        createChapter: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.setValues();
            this.model.get('chapters').add([{}]);
        },
        setName: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set("name", this.$("#textbook-name-input").val(), {silent: true});
        },
        setValues: function() {
            this.setName();
            var that = this;
            _.each(this.$("li"), function(li, i) {
                var chapter = that.model.get('chapters').at(i);
                if(!chapter) { return; }
                chapter.set({
                    "name": $(".chapter-name", li).val(),
                    "asset_path": $(".chapter-asset-path", li).val()
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
            var textbooks = this.model.collection;
            this.remove();
            if(this.model.isNew()) {
                // if the textbook has never been saved, remove it
                textbooks.remove(this.model);
            }
            // don't forget to tell the model that it's no longer being edited
            this.model.set("editing", false);
            return this;
        }
    });
    return EditTextbook;
});
