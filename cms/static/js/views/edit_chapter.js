/*global course */

define(['underscore', 'jquery', 'gettext', 'edx-ui-toolkit/js/utils/html-utils',
        'js/views/baseview', 'js/models/uploads', 'js/views/uploads', 'text!templates/edit-chapter.underscore'],
    function(_, $, gettext, HtmlUtils, BaseView, FileUploadModel, UploadDialogView, editChapterTemplate) {
        'use strict';

        var EditChapter = BaseView.extend({
            initialize: function() {
                this.template = HtmlUtils.template(editChapterTemplate);
                this.listenTo(this.model, 'change', this.render);
            },
            tagName: 'li',
            className: function() {
                return 'field-group chapter chapter' + this.model.get('order');
            },
            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        name: this.model.get('name'),
                        asset_path: this.model.get('asset_path'),
                        order: this.model.get('order'),
                        error: this.model.validationError
                    })
                );
                return this;
            },
            events: {
                'change .chapter-name': 'changeName',
                'change .chapter-asset-path': 'changeAssetPath',
                'click .action-close': 'removeChapter',
                'click .action-upload': 'openUploadDialog',
                'submit': 'uploadAsset'
            },
            changeName: function(e) {
                if(e && e.preventDefault) { e.preventDefault(); }
                this.model.set({
                    name: this.$('.chapter-name').val()
                }, {silent: true});
                return this;
            },
            changeAssetPath: function(e) {
                if(e && e.preventDefault) { e.preventDefault(); }
                this.model.set({
                    asset_path: this.$('.chapter-asset-path').val()
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
                    name: this.$('input.chapter-name').val(),
                    asset_path: this.$('input.chapter-asset-path').val()
                });
                var msg = new FileUploadModel({
                    title: _.template(gettext('Upload a new PDF to “<%= name %>”'))(
                        {name: course.escape('name')}),
                    message: gettext('Please select a PDF file to upload.'),
                    mimeTypes: ['application/pdf']
                });
                var that = this;
                var view = new UploadDialogView({
                    model: msg,
                    onSuccess: function(response) {
                        var options = {};
                        if (!that.model.get('name')) {
                            options.name = response.asset.displayname;
                        }
                        options.asset_path = response.asset.portable_url;
                        that.model.set(options);
                    }
                });
                view.show();
            }
        });

        return EditChapter;
    });
