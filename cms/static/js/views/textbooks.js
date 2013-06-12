CMS.Views.TextbookShow = Backbone.View.extend({
    initialize: function() {
        this.template = _.template($("#show-textbook-tpl").text());
        this.listenTo(this.model, "change", this.render);
    },
    tagName: "li",
    events: {
        "click .edit": "editTextbook",
        "click .delete": "confirmDelete",
        "click .show-chapters": "showChapters",
        "click .hide-chapters": "hideChapters"
    },
    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },
    editTextbook: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.model.collection.trigger("editOne", this.model);
    },
    confirmDelete: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        var textbook = this.model, collection = this.model.collection;
        var msg = new CMS.Models.WarningMessage({
            title: _.str.sprintf(gettext("Delete “%s”?"),
                textbook.escape('name')),
            message: gettext("Deleting a textbook cannot be undone and once deleted any reference to it in your courseware's navigation will also be removed."),
            actions: {
                primary: {
                    text: gettext("Delete"),
                    click: function(view) {
                        view.hide();
                        collection.remove(textbook);
                        var delmsg = new CMS.Models.SystemFeedback({
                            intent: "saving",
                            title: gettext("Deleting&hellip;")
                        });
                        var notif = new CMS.Views.Notification({
                            model: delmsg,
                            closeIcon: false,
                            minShown: 1250
                        });
                        collection.save({
                            complete: function() {
                                notif.hide();
                            }
                        });
                    }
                },
                secondary: [{
                    text: gettext("Cancel"),
                    click: function(view) {
                        view.hide();
                    }
                }]
            }
        });
        var prompt = new CMS.Views.Prompt({model: msg});
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
CMS.Views.TextbookEdit = Backbone.View.extend({
    initialize: function() {
        this.template = _.template($("#new-textbook-tpl").text());
        var chapters = this.model.get('chapters');
        this.listenTo(chapters, "add", this.addOne);
        this.listenTo(chapters, "reset", this.addAll);
        this.listenTo(chapters, "all", this.render);
        this.listenTo(this.model.collection, "editOne", this.remove);
    },
    tagName: "li",
    render: function() {
        this.$el.html(this.template({
            name: this.model.escape('name'),
            errors: null
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
        var view = new CMS.Views.ChapterEdit({model: chapter});
        this.$("ol.chapters").append(view.render().el)
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
            chapter.set({
                "name": $(".chapter-name", li).val(),
                "asset_path": $(".chapter-asset-path", li).val()
            })
        });
        return this;
    },
    setAndClose: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.setValues();
        msg = new CMS.Models.SystemFeedback({
            intent: "saving",
            title: gettext("Saving&hellip;")
        });
        notif = new CMS.Views.Notification({
            model: msg,
            closeIcon: false,
            minShown: 1250
        });
        var that = this;
        this.model.collection.save({
            success: function() {
                that.close();
            },
            complete: function() {
                notif.hide();
            }
        });
    },
    cancel: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        return this.close();
    },
    close: function() {
        var textbooks = this.model.collection;
        delete textbooks.editing;
        this.remove();
        // if the textbook has no content, remove it from the collection
        if(this.model.isEmpty()) {
            textbooks.remove(this.model);
        }
        textbooks.trigger('render');
        return this;
    }
});
CMS.Views.ListTextbooks = Backbone.View.extend({
    initialize: function() {
        this.emptyTemplate = _.template($("#no-textbooks-tpl").text());
        this.listenTo(this.collection, 'all', this.render);
    },
    tagName: "ul",
    className: "textbooks",
    render: function() {
        var textbooks = this.collection;
        if(textbooks.length === 0) {
            this.$el.html(this.emptyTemplate());
        } else {
            var $el = this.$el;
            $el.empty();
            textbooks.each(function(textbook) {
                var view;
                if (textbook === textbooks.editing) {
                    view = new CMS.Views.TextbookEdit({model: textbook});
                } else {
                    view = new CMS.Views.TextbookShow({model: textbook});
                }
                $el.append(view.render().el);
            });
        }
        return this;
    },
    events: {
        "click .new-button": "addOne"
    },
    addOne: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        // if the existing edited textbook is empty, don't do anything
        if(this.collection.editing && this.collection.editing.isEmpty()) { return; }
        var m = new this.collection.model();
        this.collection.add(m);
        this.collection.trigger("editOne", m);
    }
});
CMS.Views.ChapterEdit = Backbone.View.extend({
    initialize: function() {
        this.template = _.template($("#new-chapter-tpl").text());
        this.listenTo(this.model, "change", this.render);
    },
    tagName: "li",
    className: function() {
        return "field-group chapter chapter" + this.model.get('order');
    },
    render: function() {
        this.$el.html(this.template({
            name: this.model.escape('name'),
            asset_path: this.model.escape('asset_path'),
            order: this.model.get('order')
        }));
        return this;
    },
    events: {
        "click .action-close": "removeChapter",
        "click .action-upload": "openUploadDialog",
        "submit": "uploadAsset"
    },
    removeChapter: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.model.collection.remove(this.model);
        return this.remove();
    },
    openUploadDialog: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        var msg = new CMS.Models.FileUpload({
            title: _.str.sprintf(gettext("Upload a new asset to %s"),
                section.escape('name')),
            message: "This is sample text about asset upload requirements, like no bigger than 2MB, must be in PDF format or whatever."
        });
        var view = new CMS.Views.UploadDialog({model: msg, chapter: this.model});
        $(".wrapper-view").after(view.show().el);
    }
});

CMS.Views.UploadDialog = Backbone.View.extend({
    options: {
        shown: true
    },
    initialize: function() {
        this.template = _.template($("#upload-dialog-tpl").text());
        this.listenTo(this.model, "change", this.render);
    },
    render: function() {
        // some browsers (like Chrome) allow you to assign to the .files attribute
        // of an <input type="file"> DOM element -- for those browsers, we can
        // create a new DOM element and assign the old content to it. Other browsers
        // (like Firefox) make this attribute read-only, and we have to save the
        // old DOM element in order to save it's content. For compatibility purposes,
        // we'll just save the old element every time.
        var oldInput = this.$("input[type=file]").get(0), selectedFile;
        if (oldInput && oldInput.files.length) {
            selectedFile = oldInput.files[0];
        }
        this.$el.html(this.template({
            shown: this.options.shown,
            url: UPLOAD_ASSET_CALLBACK_URL,
            title: this.model.escape('title'),
            message: this.model.escape('message'),
            selectedFile: selectedFile,
            uploading: this.model.get('uploading'),
            uploadedBytes: this.model.get('uploadedBytes'),
            totalBytes: this.model.get('totalBytes')
        }));
        if (oldInput) {
            this.$('input[type=file]').replaceWith(oldInput);
        }

        return this;
    },
    events: {
        "change input[type=file]": "selectFile",
        "click .action-cancel": "hideAndRemove",
        "click .action-upload": "upload"
    },
    selectFile: function(e) {
        this.model.set('fileList', e.target.files);
    },
    show: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.options.shown = true;
        $body.addClass('dialog-is-shown');
        return this.render();
    },
    hide: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.options.shown = false;
        $body.removeClass('dialog-is-shown');
        return this.render();
    },
    hideAndRemove: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        return this.hide().remove();
    },
    upload: function(e) {
        this.model.set('uploading', true);
        this.$("form").ajaxSubmit({
            success: _.bind(this.success, this),
            error: _.bind(this.error, this),
            uploadProgress: _.bind(this.progress, this),
            data: {
                notifyOnError: false
            }
        });
    },
    progress: function(event, position, total, percentComplete) {
        this.model.set({
            "uploadedBytes": position,
            "totalBytes": total
        });
    },
    success: function(response, statusText, xhr, form) {
        this.model.set('uploading', false);
        var chapter = this.options.chapter;
        if(chapter) {
            var options = {};
            if(!chapter.get("name")) {
                options.name = response.displayname;
            }
            options.asset_path = response.url;
            chapter.set(options);
        }
        this.remove();
    },
    error: function() {
        this.model.set({
            "uploading": false,
            "uploadedBytes": 0,
            "title": gettext("We're sorry, there was an error")
        });
    }
});
