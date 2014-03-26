define(["jquery", "underscore", "gettext", "js/views/paging", "js/views/asset", "js/views/paging_header", "js/views/paging_footer"],
    function($, _, gettext, PagingView, AssetView, PagingHeader, PagingFooter) {

        var AssetsView = PagingView.extend({
            // takes AssetCollection as model

            events : {
                "click .column-sort-link": "onToggleColumn"
            },

            initialize : function() {
                PagingView.prototype.initialize.call(this);
                var collection = this.collection;
                this.template = _.template($("#asset-library-tpl").text());
                this.listenTo(collection, 'destroy', this.handleDestroy);
                this.registerSortableColumn('js-asset-name-col', gettext('Name'), 'display_name', 'asc');
                this.registerSortableColumn('js-asset-date-col', gettext('Date Added'), 'date_added', 'desc');
                this.setInitialSortColumn('js-asset-date-col');
                this.showLoadingIndicator();
            },

            render: function() {
                // Wait until the content is loaded the first time to render
                return this;
            },

            getTableBody: function() {
                var tableBody = this.tableBody;
                if (!tableBody) {
                    this.hideLoadingIndicator();

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
                this.hideLoadingIndicator();
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
            }
        });

        return AssetsView;
    }); // end define();
