define(["jquery", "underscore", "gettext", "js/views/baseview", "js/models/asset", "js/views/paging",
        "js/views/asset", "js/views/paging_header", "common/js/components/views/paging_footer",
        "js/utils/modal", "common/js/components/utils/view_utils", "common/js/components/views/feedback_notification",
        "text!templates/asset-library.underscore",
        "jquery.fileupload-process", "jquery.fileupload-validate"],
    function($, _, gettext, BaseView, AssetModel, PagingView, AssetView, PagingHeader, PagingFooter,
             ModalUtils, ViewUtils, NotificationView, asset_library_template) {

        var CONVERSION_FACTOR_MBS_TO_BYTES = 1000 * 1000;

        var AssetsView = BaseView.extend({
            // takes AssetCollection as model

            events : {
                "click .column-sort-link": "onToggleColumn",
                "click .upload-button": "showUploadModal",
                "click .filterable-column .nav-item": "onFilterColumn",
                "click .filterable-column .column-filter-link": "toggleFilterColumn"
            },

            typeData: ['Images', 'Documents'],

            allLabel: 'ALL',

            initialize : function(options) {
                options = options || {};

                BaseView.prototype.initialize.call(this);
                var collection = this.collection;
                this.pagingView = this.createPagingView();
                this.listenTo(collection, 'destroy', this.handleDestroy);
                ViewUtils.showLoadingIndicator();
                // set default file size for uploads via template var,
                // and default to static old value if none exists
                this.uploadChunkSizeInMBs = options.uploadChunkSizeInMBs || 10;
                this.maxFileSizeInMBs = options.maxFileSizeInMBs || 10;
                this.uploadChunkSizeInBytes = this.uploadChunkSizeInMBs * CONVERSION_FACTOR_MBS_TO_BYTES;
                this.maxFileSizeInBytes = this.maxFileSizeInMBs * CONVERSION_FACTOR_MBS_TO_BYTES;
                this.maxFileSizeRedirectUrl = options.maxFileSizeRedirectUrl || '';
                // error message modal for large file uploads
                this.largeFileErrorMsg = null;
            },

            PagingAssetView: PagingView.extend({
                renderPageItems: function() {
                    var self = this,
                    assets = this.collection,
                    hasAssets = this.collection.assetType !== '' || assets.length > 0,
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
                    self.$('.assets-library').toggle(hasAssets);
                    self.$('.no-asset-content').toggle(!hasAssets);
                    return this;
                },

                getTableBody: function() {
                    var tableBody = this.tableBody;
                    if (!tableBody) {
                        ViewUtils.hideLoadingIndicator();

                        // Create the table
                        this.$el.html(_.template(asset_library_template, {typeData: this.typeData}));
                        tableBody = this.$('#asset-table-body');
                        this.tableBody = tableBody;
                        this.pagingHeader = new PagingHeader({view: this, el: $('#asset-paging-header')});
                        this.pagingFooter = new PagingFooter({collection: this.collection, el: $('#asset-paging-footer')});
                        this.pagingHeader.render();
                        this.pagingFooter.render();

                        // Hide the contents until the collection has loaded the first time
                        this.$('.assets-library').hide();
                        this.$('.no-asset-content').hide();
                    }
                    return tableBody;
                },

                onError: function() {
                    ViewUtils.hideLoadingIndicator();
                }
            }),

            createPagingView: function() {
                var pagingView = new this.PagingAssetView({
                    el: this.$el,
                    collection: this.collection
                });
                pagingView.registerSortableColumn('js-asset-name-col', gettext('Name'), 'display_name', 'asc');
                pagingView.registerSortableColumn('js-asset-date-col', gettext('Date Added'), 'date_added', 'desc');
                pagingView.registerFilterableColumn('js-asset-type-col', gettext('Type'), 'asset_type');
                pagingView.setInitialSortColumn('js-asset-date-col');
                pagingView.setInitialFilterColumn('js-asset-type-col');
                pagingView.setPage(0);
                return pagingView;
            },

            render: function() {
                this.pagingView.render();
                return this;
            },

            afterRender: function(){
                // Bind events with html elements
                $('li a.upload-button').on('click', _.bind(this.showUploadModal, this));
                $('.upload-modal .close-button').on('click', _.bind(this.hideModal, this));
                $('.upload-modal .choose-file-button').on('click', _.bind(this.showFileSelectionMenu, this));
                return this;
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
                this.pagingView.setInitialSortColumn('js-asset-date-col');
                this.pagingView.setInitialFilterColumn('js-asset-type-col');
                this.pagingView.setPage(0);

                analytics.track('Uploaded a File', {
                    'course': course_location_analytics,
                    'asset_url': model.get('url')
                });
            },

            onToggleColumn: function(event) {
                var columnName = event.target.id;
                this.pagingView.toggleSortOrder(columnName);
            },

            onFilterColumn: function(event) {
                this.openFilterColumn($(event.currentTarget));
                event.stopPropagation();
            },

            hideModal: function (event) {
                if (event) {
                    event.preventDefault();
                }
                $('.file-input').unbind('change.startUpload');
                ModalUtils.hideModal();
                if (this.largeFileErrorMsg) {
                  this.largeFileErrorMsg.hide();
                }
            },

            showUploadModal: function (event) {
                var self = this;
                event.preventDefault();
                self.resetUploadModal();
                ModalUtils.showModal();
                $('.modal-cover').on('click', self.hideModal);
                $('.file-input').bind('change', self.startUpload);
                $('.upload-modal .file-chooser').fileupload({
                    dataType: 'json',
                    type: 'POST',
                    maxChunkSize: self.uploadChunkSizeInBytes,
                    autoUpload: true,
                    progressall: function(event, data) {
                        var percentComplete = parseInt((100 * data.loaded) / data.total, 10);
                        self.showUploadFeedback(event, percentComplete);
                    },
                    maxFileSize: self.maxFileSizeInBytes,
                    maxNumberofFiles: 100,
                    done: function(event, data) {
                        self.displayFinishedUpload(data.result);
                    },
                    processfail: function(event, data) {
                        var filename = data.files[data.index].name;
                        var error = gettext("File {filename} exceeds maximum size of {maxFileSizeInMBs} MB")
                                    .replace("{filename}", filename)
                                    .replace("{maxFileSizeInMBs}", self.maxFileSizeInMBs)

                        // disable second part of message for any falsy value,
                        // which can be null or an empty string
                        if(self.maxFileSizeRedirectUrl) {
                            var instructions = gettext("Please follow the instructions here to upload a file elsewhere and link to it: {maxFileSizeRedirectUrl}")
                                    .replace("{maxFileSizeRedirectUrl}", self.maxFileSizeRedirectUrl);
                            error = error + " " + instructions;
                        }

                        self.largeFileErrorMsg = new NotificationView.Error({
                            "title": gettext("Your file could not be uploaded"),
                            "message": error
                        });
                        self.largeFileErrorMsg.show();

                        self.displayFailedUpload({
                            "msg": gettext("Max file size exceeded")
                        });
                    },
                    processdone: function(event, data) {
                        self.largeFileErrorMsg = null;
                    }
                });
            },

            showFileSelectionMenu: function(event) {
                event.preventDefault();
                if (this.largeFileErrorMsg) {
                  this.largeFileErrorMsg.hide();
                }
                $('.file-input').click();
            },

            startUpload: function (event) {
                var file = event.target.value;
                if (!this.largeFileErrorMsg) {
                    $('.upload-modal h1').text(gettext('Uploading'));
                    $('.upload-modal .file-name').html(file.substring(file.lastIndexOf("\\") + 1));
                    $('.upload-modal .choose-file-button').hide();
                    $('.upload-modal .progress-bar').removeClass('loaded').show();
                }
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

                this.largeFileErrorMsg = null;
            },

            showUploadFeedback: function (event, percentComplete) {
                var percentVal = percentComplete + '%';
                $('.upload-modal .progress-fill').width(percentVal);
                $('.upload-modal .progress-fill').html(percentVal);
            },

            openFilterColumn: function($this) {
                this.toggleFilterColumnState($this);
            },

            toggleFilterColumnState: function(menu, selected) {
                var $subnav = menu.find('.wrapper-nav-sub');
                var $title = menu.find('.title');
                var titleText = $title.find('.type-filter');
                var assettype = selected ? selected.data('assetfilter'): false;
                if(assettype) {
                    if(assettype === this.allLabel) {
                        titleText.text(titleText.data('alllabel'));
                    }
                    else {
                        titleText.text(assettype);
                    }
                }
                if ($subnav.hasClass('is-shown')) {
                    $subnav.removeClass('is-shown');
                    $title.removeClass('is-selected');
                } else {
                    $title.addClass('is-selected');
                    $subnav.addClass('is-shown');
                }
            },

            toggleFilterColumn: function(event) {
                event.preventDefault();
                var $filterColumn = $(event.currentTarget);
                this._toggleFilterColumn($filterColumn.data('assetfilter'), $filterColumn.text());
            },

            _toggleFilterColumn: function(assettype, assettypeLabel) {
                var collection = this.collection;
                var filterColumn = this.$el.find('.filterable-column');
                var resetFilter = filterColumn.find('.reset-filter');
                var title = filterColumn.find('.title');
                if(assettype === this.allLabel) {
                    collection.assetType = '';
                    resetFilter.hide();
                    title.removeClass('column-selected-link');
                }
                else {
                    collection.assetType = assettype;
                    resetFilter.show();
                    title.addClass('column-selected-link');
                }

                this.pagingView.filterableColumns['js-asset-type-col'].displayName = assettypeLabel;
                this.pagingView.selectFilter('js-asset-type-col');
                this.closeFilterPopup(this.$el.find(
                    '.column-filter-link[data-assetfilter="' + assettype + '"]'));
            },

            closeFilterPopup: function(element){
                var $menu = element.parents('.nav-dd > .nav-item');
                this.toggleFilterColumnState($menu, element);
            },

            displayFinishedUpload: function (resp) {
                var asset = resp.asset;

                $('.upload-modal h1').text(gettext('Upload New File'));
                $('.upload-modal .embeddable-xml-input').val(asset.portable_url).show();
                $('.upload-modal .embeddable').show();
                $('.upload-modal .file-name').hide();
                $('.upload-modal .progress-fill').html(resp.msg);
                $('.upload-modal .choose-file-button').text(gettext('Load Another File')).show();
                $('.upload-modal .progress-fill').width('100%');

                this.addAsset(new AssetModel(asset));
            },

            displayFailedUpload: function (resp) {
                $('.upload-modal h1').text(gettext('Upload New File'));
                $('.upload-modal .embeddable-xml-input').hide();
                $('.upload-modal .embeddable').hide();
                $('.upload-modal .file-name').hide();
                $('.upload-modal .progress-fill').html(resp.msg);
                $('.upload-modal .choose-file-button').text(gettext('Load Another File')).show();
                $('.upload-modal .progress-fill').width('0%');
            }
        });

        return AssetsView;
    }); // end define();
