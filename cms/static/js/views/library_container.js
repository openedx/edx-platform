define(["jquery", "underscore", "js/views/container", "js/utils/module", "gettext", "js/views/feedback_notification",
        "js/views/paging_header", "js/views/paging_footer"],
    function ($, _, ContainerView, ModuleUtils, gettext, NotificationView, PagingHeader, PagingFooter) {
        var LibraryContainerView = ContainerView.extend({
            // Store the request token of the first xblock on the page (which we know was rendered by Studio when
            // the page was generated). Use that request token to filter out user-defined HTML in any
            // child xblocks within the page.

            initialize: function(options){
                var self = this;
                ContainerView.prototype.initialize.call(this);
                this.page_size = this.options.page_size || 10;
                this.page_reload_callback = options.page_reload_callback || function () {};
                // emulating Backbone.paginator interface
                this.collection = {
                    currentPage: 0,
                    totalPages: 0,
                    totalCount: 0,
                    sortDirection: "desc",
                    start: 0,
                    _size: 0,

                    bind: function() {},  // no-op
                    size: function() { return self.collection._size; }
                };
            },

            render: function(options) {
                var eff_options = options || {};
                eff_options.page_number = typeof eff_options.page_number !== "undefined"
                    ? eff_options.page_number
                    : this.collection.currentPage;
                return this.renderPage(eff_options);
            },

            renderPage: function(options){
                var self = this,
                    view = this.view,
                    xblockInfo = this.model,
                    xblockUrl = xblockInfo.url();
                return $.ajax({
                    url: decodeURIComponent(xblockUrl) + "/" + view,
                    type: 'GET',
                    cache: false,
                    data: this.getRenderParameters(options.page_number),
                    headers: { Accept: 'application/json' },
                    success: function(fragment) {
                        self.handleXBlockFragment(fragment, options);
                        self.processPaging({ requested_page: options.page_number });
                        // This is expected to render the add xblock components menu.
                        self.page_reload_callback(self.$el)
                    }
                });
            },

            getRenderParameters: function(page_number) {
                return {
                    enable_paging: true,
                    page_size: this.page_size,
                    page_number: page_number
                };
            },

            getPageCount: function(total_count){
                if (total_count===0) return 1;
                return Math.ceil(total_count / this.page_size);
            },

            setPage: function(page_number) {
                this.render({ page_number: page_number});
            },

            nextPage: function() {
                var collection = this.collection,
                    currentPage = collection.currentPage,
                    lastPage = collection.totalPages - 1;
                if (currentPage < lastPage) {
                    this.setPage(currentPage + 1);
                }
            },

            previousPage: function() {
                var collection = this.collection,
                    currentPage = collection.currentPage;
                if (currentPage > 0) {
                    this.setPage(currentPage - 1);
                }
            },

            processPaging: function(options){
                var $element = this.$el.find('.xblock-container-paging-parameters'),
                    total = $element.data('total'),
                    displayed = $element.data('displayed'),
                    start = $element.data('start');

                this.collection.currentPage = options.requested_page;
                this.collection.totalCount = total;
                this.collection.totalPages = this.getPageCount(total);
                this.collection.start = start;
                this.collection._size = displayed;

                this.processPagingHeaderAndFooter();
            },

            processPagingHeaderAndFooter: function(){
                if (this.pagingHeader)
                    this.pagingHeader.undelegateEvents();
                if (this.pagingFooter)
                    this.pagingFooter.undelegateEvents();

                this.pagingHeader = new PagingHeader({
                    view: this,
                    el: this.$el.find('.container-paging-header')
                });
                this.pagingFooter = new PagingFooter({
                    view: this,
                    el: this.$el.find('.container-paging-footer')
                });

                this.pagingHeader.render();
                this.pagingFooter.render();
            },

            xblockReady: function () {
                ContainerView.prototype.xblockReady.call(this);

                this.requestToken = this.$('div.xblock').first().data('request-token');
            },

            refresh: function(block_added) {
                if (block_added) {
                    this.collection.totalCount += 1;
                    this.collection._size +=1;
                    if (this.collection.totalCount == 1) {
                        this.render();
                        return
                    }
                    this.collection.totalPages = this.getPageCount(this.collection.totalCount);
                    var new_page = this.collection.totalPages - 1;
                    // If we're on a new page due to overflow, or this is the first item, set the page.
                    if (((this.collection.currentPage) != new_page) || this.collection.totalCount == 1) {
                        this.setPage(new_page);
                    } else {
                        this.pagingHeader.render();
                        this.pagingFooter.render();
                    }
                }
            },

            acknowledgeXBlockDeletion: function (locator){
                this.notifyRuntime('deleted-child', locator);
                this.collection._size -= 1;
                this.collection.totalCount -= 1;
                var current_page = this.collection.currentPage;
                var total_pages = this.getPageCount(this.collection.totalCount);
                this.collection.totalPages = total_pages;
                // Starts counting from 0
                if ((current_page + 1) > total_pages) {
                    // The number of total pages has changed. Move down.
                    // Also, be mindful of the off-by-one.
                    this.setPage(total_pages - 1)
                } else if ((current_page + 1) != total_pages) {
                    // Refresh page to get any blocks shifted from the next page.
                    this.setPage(current_page)
                } else {
                    // We're on the last page, just need to update the numbers in the
                    // pagination interface.
                    this.pagingHeader.render();
                    this.pagingFooter.render();
                }
            },

            sortDisplayName: function() {
                return "Date added";  // TODO add support for sorting
            }
        });

        return LibraryContainerView;
    }); // end define();
