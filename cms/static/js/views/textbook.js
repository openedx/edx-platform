CMS.Views.ShowTextbook = Backbone.View.extend({
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
        this.$el.html(this.template(this.model.attributes));
        return this;
    },
    editTextbook: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.model.set("editing", true);
    },
    confirmDelete: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        var textbook = this.model, collection = this.model.collection;
        var msg = new CMS.Views.Prompt.Warning({
            title: _.str.sprintf(gettext("Delete “%s”?"),
                textbook.escape('name')),
            message: gettext("Deleting a textbook cannot be undone and once deleted any reference to it in your courseware's navigation will also be removed."),
            actions: {
                primary: {
                    text: gettext("Delete"),
                    click: function(view) {
                        view.hide();
                        collection.remove(textbook);
                        var delmsg = new CMS.Views.Notification.Saving({
                            title: gettext("Deleting&hellip;"),
                            closeIcon: false,
                            minShown: 1250
                        }).show();
                        collection.save({
                            complete: function() {
                                delmsg.hide();
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
CMS.Views.EditTextbook = Backbone.View.extend({
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
        var view = new CMS.Views.EditChapter({model: chapter});
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
        var saving = new CMS.Views.Notification.Saving({
            title: gettext("Saving&hellip;")
        });
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
        // if the textbook has no content, remove it from the collection
        if(this.model.isEmpty()) {
            textbooks.remove(this.model);
        } else {
            // remove empty chapters from textbook
            var chapters = this.model.get("chapters");
            var emptyChapters = chapters.filter(function(chapter) {
                return chapter.isEmpty(); });
            if (chapters.length === emptyChapters.length) {
                // make sure that there's always at least one chapter remaining
                // in the chapterset, even if it's empty
                emptyChapters = _.tail(emptyChapters);
            }
            chapters.remove(emptyChapters);
            // don't forget to tell the model that it's no longer being edited
            this.model.set("editing", false);
        }
        return this;
    }
});
CMS.Views.ListTextbooks = Backbone.View.extend({
    initialize: function() {
        this.emptyTemplate = _.template($("#no-textbooks-tpl").text());
        this.listenTo(this.collection, 'all', this.render);
    },
    tagName: "div",
    className: "textbooks-list",
    render: function() {
        var textbooks = this.collection;
        if(textbooks.length === 0) {
            this.$el.html(this.emptyTemplate());
        } else {
            this.$el.empty();
            var that = this;
            textbooks.each(function(textbook) {
                var view;
                if (textbook.get("editing")) {
                    view = new CMS.Views.EditTextbook({model: textbook});
                } else {
                    view = new CMS.Views.ShowTextbook({model: textbook});
                }
                that.$el.append(view.render().el);
            });
        }
        return this;
    },
    events: {
        "click .new-button": "addOne"
    },
    addOne: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.collection.add([{editing: true}]);
    }
});
CMS.Views.EditChapter = Backbone.View.extend({
    initialize: function() {
        this.template = _.template($("#edit-chapter-tpl").text());
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
        this.model.set({
            name: this.$("input.chapter-name").val(),
            asset_path: this.$("input.chapter-asset-path").val()
        });
        var msg = new CMS.Models.FileUpload({
            title: _.str.sprintf(gettext("Upload a new asset to %s"),
                section.escape('name')),
            message: "Files must be in PDF format."
        });
        var view = new CMS.Views.UploadDialog({model: msg, chapter: this.model});
        $(".wrapper-view").after(view.show().el);
    }
});

CMS.Views.UploadDialog = Backbone.View.extend({
    options: {
        shown: true,
        successMessageTimeout: 2000 // 2 seconds
    },
    initialize: function() {
        this.template = _.template($("#upload-dialog-tpl").text());
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this.model, "invalid", this.handleInvalid);
    },
    render: function() {
        if(!this.model.isValid()) {return this;}
        var selectedFile = this.model.get('selectedFile');
        var oldInput = this.$("input[type=file]").get(0);
        this.$el.html(this.template({
            shown: this.options.shown,
            url: CMS.URL.UPLOAD_ASSET,
            title: this.model.escape('title'),
            message: this.model.escape('message'),
            selectedFile: selectedFile,
            uploading: this.model.get('uploading'),
            uploadedBytes: this.model.get('uploadedBytes'),
            totalBytes: this.model.get('totalBytes'),
            finished: this.model.get('finished'),
            error: this.model.get('error')
        }));
        // ideally, we'd like to tell the browser to pre-populate the
        // <input type="file"> with the selectedFile if we have one -- but
        // browser security prohibits that. So instead, we'll swap out the
        // new input (that has no file selected) with the old input (that
        // already has the selectedFile selected).
        if (selectedFile) {
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
        this.model.set({
            selectedFile: e.target.files[0] || null,
            error: null
        });
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
    handleInvalid: function(model, error, options) {
        model.set({
            selectedFile: null,
            error: error
        });
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
        this.model.set({
            uploading: false,
            finished: true
        });
        var chapter = this.options.chapter;
        if(chapter) {
            var options = {};
            if(!chapter.get("name")) {
                options.name = response.displayname;
            }
            options.asset_path = response.url;
            chapter.set(options);
        }
        var that = this;
        this.removalTimeout = setTimeout(function() {
            that.hide().remove();
        }, this.options.successMessageTimeout);
    },
    error: function() {
        this.model.set({
            "uploading": false,
            "uploadedBytes": 0,
            "title": gettext("We're sorry, there was an error")
        });
    }
});
