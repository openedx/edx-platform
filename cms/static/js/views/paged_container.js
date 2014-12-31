define(["jquery", "underscore", "js/views/container", "js/utils/module", "gettext",
        "js/views/feedback_notification", "js/views/paging_header", "js/views/paging_footer", "js/views/paging_mixin"],
    function ($, _, ContainerView, ModuleUtils, gettext, NotificationView, PagingHeader, PagingFooter, PagingMixin) {
        var PagedContainerView = ContainerView.extend(PagingMixin).extend({
            initialize: function(options){
                var self = this;
                ContainerView.prototype.initialize.call(this);
                this.page_size = this.options.page_size;
                // Reference to the page model
                this.page = options.page;
                // XBlocks are rendered via Django views and templates rather than underscore templates, and so don't
                // have a Backbone model for us to manipulate in a backbone collection. Here, we emulate the interface
                // of backbone.paginator so that we can use the Paging Header and Footer with this page. As a
                // consequence, however, we have to manipulate its members manually.
                this.collection = {
                    currentPage: 0,
                    totalPages: 0,
                    totalCount: 0,
                    sortDirection: "desc",
                    start: 0,
                    _size: 0,
                    // Paging header and footer expect this to be a Backbone model they can listen to for changes, but
                    // they cannot. Provide the bind function for them, but have it do nothing.
                    bind: function() {},
                    // size() on backbone collections shows how many objects are in the collection, or in the case
                    // of paginator, on the current page.
                    size: function() { return self.collection._size; }
                };
            },

            new_child_view: 'container_child_preview',

            render: function(options) {
                options = options || {};
                options.page_number = typeof options.page_number !== "undefined"
                    ? options.page_number
                    : this.collection.currentPage;
                return this.renderPage(options);
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
                        self.page.renderAddXBlockComponents();
                    }
                });
            },

            getRenderParameters: function(page_number) {
                return {
                    page_size: this.page_size,
                    enable_paging: true,
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

            processPaging: function(options){
                // We have the Django template sneak us the pagination information,
                // and we load it from a div here.
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
                // Rendering the container view detaches the header and footer from the DOM.
                // It's just as easy to recreate them as it is to try to shove them back into the tree.
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
                return gettext("Date added");  // TODO add support for sorting
            }
        });

        return PagedContainerView;
    }); // end define();
