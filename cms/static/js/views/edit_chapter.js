define(["backbone", "underscore", "underscore.string", "jquery", "gettext", "js/models/uploads", "js/views/uploads"],
        function(Backbone, _, str, $, gettext, FileUploadModel, UploadDialogView) {
    _.str = str; // used in template
    var EditChapter = Backbone.View.extend({
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
                order: this.model.get('order'),
                error: this.model.validationError
            }));
            return this;
        },
        events: {
            "change .chapter-name": "changeName",
            "change .chapter-asset-path": "changeAssetPath",
            "click .action-close": "removeChapter",
            "click .action-upload": "openUploadDialog",
            "submit": "uploadAsset"
        },
        changeName: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set({
                name: this.$(".chapter-name").val()
            }, {silent: true});
            return this;
        },
        changeAssetPath: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set({
                asset_path: this.$(".chapter-asset-path").val()
            }, {silent: true});
            return this;
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
            var msg = new FileUploadModel({
                title: _.template(gettext("Upload a new PDF to “<%= name %>”"),
                    {name: section.escape('name')}),
                message: "Files must be in PDF format.",
                mimeTypes: ['application/pdf']
            });
            var that = this;
            var view = new UploadDialogView({
                model: msg,
                onSuccess: function(response) {
                    var options = {};
                    if(!that.model.get('name')) {
                        options.name = response.asset.displayname;
                    }
                    options.asset_path = response.asset.url;
                    that.model.set(options);
                }
            });
            $(".wrapper-view").after(view.show().el);
        }
    });

    return EditChapter;
});
