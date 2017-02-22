define(['jquery', 'underscore', 'common/js/components/utils/view_utils', 'js/views/container', 'js/utils/module', 'gettext',
        'common/js/components/views/feedback_notification', 'js/views/paging_header', 'common/js/components/views/paging_footer'],
    function($, _, ViewUtils, ContainerView, ModuleUtils, gettext, NotificationView, PagingHeader, PagingFooter) {
        var PagedContainerView = ContainerView.extend({

            initialize: function(options) {
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
                    sortDirection: 'desc',
                    start: 0,
                    _size: 0,
                    // Paging header and footer expect this to be a Backbone model they can listen to for changes, but
                    // they cannot. Provide the bind function for them, but have it do nothing.
                    bind: function() {},
                    // size() on backbone collections shows how many objects are in the collection, or in the case
                    // of paginator, on the current page.
                    size: function() { return self.collection._size; },
                    // Toggles the functionality for showing and hiding child previews.
                    showChildrenPreviews: true,

                    // PagingFooter expects to be able to control paging through the collection instead of the view,
                    // so we just make these functions act as pass-throughs
                    setPage: function(page) {
                        self.setPage(page - 1);
                    },

                    nextPage: function() {
                        self.nextPage();
                    },

                    previousPage: function() {
                        self.previousPage();
                    },

                    getPage: function() {
                        return self.collection.currentPage + 1;
                    },

                    hasPreviousPage: function() {
                        return self.collection.currentPage > 0;
                    },

                    hasNextPage: function() {
                        return self.collection.currentPage < self.collection.totalPages - 1;
                    },

                    getTotalPages: function() {
                        return this.totalPages;
                    },

                    getPageNumber: function() {
                        return this.getPage();
                    },

                    getTotalRecords: function() {
                        return this.totalCount;
                    },

                    getPageSize: function() {
                        return self.page_size;
                    }
                };
            },

            new_child_view: 'container_child_preview',

            render: function(options) {
                options = options || {};
                options.page_number = typeof options.page_number !== 'undefined'
                    ? options.page_number
                    : this.collection.currentPage;
                return this.renderPage(options);
            },

            renderPage: function(options) {
                var self = this,
                    view = this.view,
                    xblockInfo = this.model,
                    xblockUrl = xblockInfo.url();

                return $.ajax({
                    url: decodeURIComponent(xblockUrl) + '/' + view,
                    type: 'GET',
                    cache: false,
                    data: this.getRenderParameters(options.page_number, options.force_render),
                    headers: {Accept: 'application/json'},
                    success: function(fragment) {
                        self.handleXBlockFragment(fragment, options);
                        self.processPaging({requested_page: options.page_number});
                        self.page.updatePreviewButton(self.collection.showChildrenPreviews);
                        self.page.renderAddXBlockComponents();
                        if (options.force_render) {
                            var target = $('.studio-xblock-wrapper[data-locator="' + options.force_render + '"]');
                            // Scroll us to the element with a little buffer at the top for context.
                            ViewUtils.setScrollOffset(target, ($(window).height() * .10));
                        }
                    }
                });
            },

            getRenderParameters: function(page_number, force_render) {
                // Options should at least contain page_number.
                return {
                    page_size: this.page_size,
                    enable_paging: true,
                    page_number: page_number,
                    force_render: force_render
                };
            },

            getPageCount: function(total_count) {
                if (total_count === 0) {
                    return 1;
                }
                return Math.ceil(total_count / this.page_size);
            },

            setPage: function(page_number, additional_options) {
                additional_options = additional_options || {};
                var options = _.extend({page_number: page_number}, additional_options);
                this.render(options);
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

            processPaging: function(options) {
                // We have the Django template sneak us the pagination information,
                // and we load it from a div here.
                var $element = this.$el.find('.xblock-container-paging-parameters'),
                    total = $element.data('total'),
                    displayed = $element.data('displayed'),
                    start = $element.data('start'),
                    previews = $element.data('previews');

                this.collection.currentPage = options.requested_page;
                this.collection.totalCount = total;
                this.collection.totalPages = this.getPageCount(total);
                this.collection.start = start;
                this.collection._size = displayed;
                this.collection.showChildrenPreviews = previews;

                this.processPagingHeaderAndFooter();
            },

            processPagingHeaderAndFooter: function() {
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
                    collection: this.collection,
                    el: this.$el.find('.container-paging-footer')
                });

                this.pagingHeader.render();
                this.pagingFooter.render();
            },

            refresh: function(xblockView, block_added, is_duplicate) {
                if (!block_added) {
                    return;
                }
                if (is_duplicate) {
                    // Duplicated blocks can be inserted onto the current page.
                    var xblock = xblockView.xblock.element.parents('.studio-xblock-wrapper').first();
                    var all_xblocks = xblock.parent().children('.studio-xblock-wrapper');
                    var index = all_xblocks.index(xblock);
                    if ((index + 1 <= this.page_size) && (all_xblocks.length > this.page_size)) {
                        // Pop the last XBlock off the bottom.
                        all_xblocks[all_xblocks.length - 1].remove();
                        return;
                    }
                }
                this.collection.totalCount += 1;
                this.collection._size += 1;
                if (this.collection.totalCount == 1) {
                    this.render();
                    return;
                }
                this.collection.totalPages = this.getPageCount(this.collection.totalCount);
                var target_page = this.collection.totalPages - 1;
                // If we're on a new page due to overflow, or this is the first item, set the page.
                if (((this.collection.currentPage) != target_page) || this.collection.totalCount == 1) {
                    var force_render = xblockView.model.id;
                    if (is_duplicate) {
                        // The duplicate should be on the next page if we've gotten here.
                        target_page = this.collection.currentPage + 1;
                    }
                    this.setPage(
                        target_page,
                        {force_render: force_render}
                    );
                } else {
                    this.pagingHeader.render();
                    this.pagingFooter.render();
                }
            },

            acknowledgeXBlockDeletion: function(locator) {
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
                    this.setPage(total_pages - 1);
                } else if ((current_page + 1) != total_pages) {
                    // Refresh page to get any blocks shifted from the next page.
                    this.setPage(current_page);
                } else {
                    // We're on the last page, just need to update the numbers in the
                    // pagination interface.
                    this.pagingHeader.render();
                    this.pagingFooter.render();
                }
            },

            sortDisplayName: function() {
                return gettext('Date added');  // TODO add support for sorting
            },

            togglePreviews: function() {
                var self = this,
                    xblockUrl = this.model.url();
                return $.ajax({
                    // No runtime, so can't get this via the handler() call.
                    url: '/preview' + decodeURIComponent(xblockUrl) + '/handler/trigger_previews',
                    type: 'POST',
                    data: JSON.stringify({showChildrenPreviews: !this.collection.showChildrenPreviews}),
                    dataType: 'json'
                })
                .then(self.render).promise();
            }
        });

        return PagedContainerView;
    }); // end define();
