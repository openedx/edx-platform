CMS.Views.UploadDialog = Backbone.View.extend({
    options: {
        shown: true,
        successMessageTimeout: 2000 // 2 seconds
    },
    initialize: function() {
        this.template = _.template($("#upload-dialog-tpl").text());
        this.listenTo(this.model, "change", this.render);
    },
    render: function() {
        var isValid = this.model.isValid();
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
            error: this.model.validationError
        }));
        // Ideally, we'd like to tell the browser to pre-populate the
        // <input type="file"> with the selectedFile if we have one -- but
        // browser security prohibits that. So instead, we'll swap out the
        // new input (that has no file selected) with the old input (that
        // already has the selectedFile selected). However, we only want to do
        // this if the selected file is valid: if it isn't, we want to render
        // a blank input to prompt the user to upload a different (valid) file.
        if (selectedFile && isValid) {
            $(oldInput).removeClass("error");
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
            selectedFile: e.target.files[0] || null
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
    upload: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        this.model.set('uploading', true);
        this.$("form").ajaxSubmit({
            success: _.bind(this.success, this),
            error: _.bind(this.error, this),
            uploadProgress: _.bind(this.progress, this),
            data: {
                // don't show the generic error notification; we're in a modal,
                // and we're better off modifying it instead.
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
        if(this.options.onSuccess) {
            this.options.onSuccess(response, statusText, xhr, form);
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
