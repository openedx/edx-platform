define(["jquery", "underscore", "gettext", "js/models/asset", "js/views/paging", "js/views/asset",
    "js/views/paging_header", "js/views/paging_footer", "js/utils/modal", "js/views/utils/view_utils"],
    function($, _, gettext, AssetModel, PagingView, AssetView, PagingHeader, PagingFooter, ModalUtils, ViewUtils) {

        var AssetsView = PagingView.extend({
            // takes AssetCollection as model

            events : {
                "click .column-sort-link": "onToggleColumn",
                "click .upload-button": "showUploadModal"
            },

            initialize : function() {
                PagingView.prototype.initialize.call(this);
                var collection = this.collection;
                this.template = this.loadTemplate("asset-library");
                this.listenTo(collection, 'destroy', this.handleDestroy);
                this.registerSortableColumn('js-asset-name-col', gettext('Name'), 'display_name', 'asc');
                this.registerSortableColumn('js-asset-date-col', gettext('Date Added'), 'date_added', 'desc');
                this.setInitialSortColumn('js-asset-date-col');
                ViewUtils.showLoadingIndicator();
                this.setPage(0);
                assetsView = this;
            },

            render: function() {
                // Wait until the content is loaded the first time to render
                return this;
            },

            afterRender: function(){
                // Bind events with html elements
                $('li a.upload-button').on('click', this.showUploadModal);
                $('.upload-modal .close-button').on('click', this.hideModal);
                $('.upload-modal .choose-file-button').on('click', this.showFileSelectionMenu);
                return this;
            },

            getTableBody: function() {
                var tableBody = this.tableBody;
                if (!tableBody) {
                    ViewUtils.hideLoadingIndicator();

                    // Create the table
                    this.$el.html(this.template());
                    tableBody = this.$('#asset-table-body');
                    this.tableBody = tableBody;
                    this.pagingHeader = new PagingHeader({view: this, el: $('#asset-paging-header')});
                    this.pagingFooter = new PagingFooter({view: this, el: $('#asset-paging-footer')});
                    this.pagingHeader.render();
                    this.pagingFooter.render();

                    // Hide the contents until the collection has loaded the first time
                    this.$('.asset-library').hide();
                    this.$('.no-asset-content').hide();
                }
                return tableBody;
            },

            renderPageItems: function() {
                var self = this,
                assets = this.collection,
                hasAssets = assets.length > 0,
                tableBody = this.getTableBody();
                tableBody.empty();
                if (hasAssets) {
                    assets.each(
                        function(asset) {
                            var view = new AssetView({model: asset});
                            tableBody.append(view.render().el);
                        }
                    );
                }
                self.$('.asset-library').toggle(hasAssets);
                self.$('.no-asset-content').toggle(!hasAssets);
                return this;
            },

            onError: function() {
                ViewUtils.hideLoadingIndicator();
            },

            handleDestroy: function(model) {
                this.collection.fetch({reset: true}); // reload the collection to get a fresh page full of items
                analytics.track('Deleted Asset', {
                    'course': course_location_analytics,
                    'id': model.get('url')
                });
            },

            addAsset: function (model) {
                // Switch the sort column back to the default (most recent date added) and show the first page
                // so that the new asset is shown at the top of the page.
                this.setInitialSortColumn('js-asset-date-col');
                this.setPage(0);

                analytics.track('Uploaded a File', {
                    'course': course_location_analytics,
                    'asset_url': model.get('url')
                });
            },

            onToggleColumn: function(event) {
                var columnName = event.target.id;
                this.toggleSortOrder(columnName);
            },

            hideModal: function (event) {
                if (event) {
                    event.preventDefault();
                }
                $('.file-input').unbind('change.startUpload');
                ModalUtils.hideModal();
            },

            showUploadModal: function (event) {
                var self = assetsView;
                event.preventDefault();
                self.resetUploadModal();
                ModalUtils.showModal();
                $('.file-input').bind('change', self.startUpload);
                $('.upload-modal .file-chooser').fileupload({
                    dataType: 'json',
                    type: 'POST',
                    maxChunkSize: 100 * 1000 * 1000,      // 100 MB
                    autoUpload: true,
                    progressall: function(event, data) {
                        var percentComplete = parseInt((100 * data.loaded) / data.total, 10);
                        self.showUploadFeedback(event, percentComplete);
                    },
                    maxFileSize: 100 * 1000 * 1000,   // 100 MB
                    maxNumberofFiles: 100,
                    add: function(event, data) {
                        data.process().done(function () {
                            data.submit();
                        });
                    },
                    done: function(event, data) {
                        self.displayFinishedUpload(data.result);
                    }

                });
            },

            showFileSelectionMenu: function(event) {
                event.preventDefault();
                $('.file-input').click();
            },

            startUpload: function (event) {
                var file = event.target.value;

                $('.upload-modal h1').text(gettext('Uploading…'));
                $('.upload-modal .file-name').html(file.substring(file.lastIndexOf("\\") + 1));
                $('.upload-modal .choose-file-button').hide();
                $('.upload-modal .progress-bar').removeClass('loaded').show();
            },

            resetUploadModal: function () {
                // Reset modal so it no longer displays information about previously
                // completed uploads.
                var percentVal = '0%';
                $('.upload-modal .progress-fill').width(percentVal);
                $('.upload-modal .progress-fill').html(percentVal);
                $('.upload-modal .progress-bar').hide();

                $('.upload-modal .file-name').show();
                $('.upload-modal .file-name').html('');
                $('.upload-modal .choose-file-button').text(gettext('Choose File'));
                $('.upload-modal .embeddable-xml-input').val('');
                $('.upload-modal .embeddable').hide();
            },

            showUploadFeedback: function (event, percentComplete) {
                var percentVal = percentComplete + '%';
                $('.upload-modal .progress-fill').width(percentVal);
                $('.upload-modal .progress-fill').html(percentVal);
            },

            displayFinishedUpload: function (resp) {
                var asset = resp.asset;

                $('.upload-modal h1').text(gettext('Upload New File'));
                $('.upload-modal .embeddable-xml-input').val(asset.portable_url);
                $('.upload-modal .embeddable').show();
                $('.upload-modal .file-name').hide();
                $('.upload-modal .progress-fill').html(resp.msg);
                $('.upload-modal .choose-file-button').text(gettext('Load Another File')).show();
                $('.upload-modal .progress-fill').width('100%');

                assetsView.addAsset(new AssetModel(asset));
            }
        });

        return AssetsView;
    }); // end define();
