/**
 * XBlockContainerPage is used to display Studio's container page for an xblock which has children.
 * This page allows the user to understand and manipulate the xblock and its children.
 */
define(["jquery", "underscore", "gettext", "js/views/baseview", "js/models/xblock_info",
        "js/views/xblock", "js/views/modals/edit_xblock"],
    function ($, _, gettext, BaseView, XBlockInfo, XBlockView, EditXBlockModal) {
        var DashboardPage = BaseView.extend({
            // takes XBlockTypes as a model

            initialize: function() {
                BaseView.prototype.initialize.call(this);
            },

            render: function() {
                var xblockType = this.model.get(this.options.xblockTypeName),
                    loadingElement = this.$('.ui-loading');
                loadingElement.removeClass('is-hidden');
                if (xblockType) {
                    this.$('.dashboard-section-features').hide();
                    this.renderXBlockType(xblockType);
                } else {
                    this.$('.dashboard-section-components').hide();
                    this.renderXBlockTypeList();
                }
                loadingElement.addClass('is-hidden');
                return this;
            },

            onXBlockRefresh: function(xblockView) {
                this.addButtonActions(xblockView.$el);
                this.$('.article').hide();
            },

            addButtonActions: function(element) {
                var self = this;
                element.find('.edit-button').click(function(event) {
                    event.preventDefault();
                    self.editComponent(self.findXBlockElement(event.target));
                });
                element.find('.duplicate-button').click(function(event) {
                    event.preventDefault();
                    self.duplicateComponent(self.findXBlockElement(event.target));
                });
                element.find('.delete-button').click(function(event) {
                    event.preventDefault();
                    self.deleteComponent(self.findXBlockElement(event.target));
                });
            },

            renderXBlockTypeList: function() {
                var parentElement = this.$('.dashboard-section-features'),
                    i, xblockType, usedXBlocksTable, unusedXBlocksListElement;

                parentElement.append('<h3>Features used in this course</h3>');
                usedXBlocksTable = $('<table class="feature-table"></table>').appendTo(parentElement);
                usedXBlocksTable.append('<thead><tr><th>Name</th><th>Count</th><th>Publish Status</th></tr></thead>');
                for (i=0; i < this.model.length; i++) {
                    xblockType = this.model.at(i);
                    if (xblockType.get('locators').length > 0) {
                        usedXBlocksTable.append(interpolate('<tr><td><a href="%(studio_url)s">%(display_name)s</a></td><td>%(count)s</td><td>%(publish_status)s</td></tr>', {
                                studio_url: xblockType.get('studio_url'),
                                display_name: xblockType.get('display_name'),
                                count: xblockType.get('locators').length,
                                publish_status: xblockType.get('publish_status')
                            },
                            true));
                    }
                }

                parentElement.append('<h3>Unused features</h3>');
                unusedXBlocksListElement = $('<ul></ul>').appendTo(parentElement);
                for (i=0; i < this.model.length; i++) {
                    xblockType = this.model.at(i);
                    if (xblockType.get('locators').length === 0) {
                        unusedXBlocksListElement.append(interpolate('<li><a href="%(studio_url)s">%(display_name)s</a></li>', {
                                studio_url: xblockType.get('studio_url'),
                                display_name: xblockType.get('display_name')
                            },
                            true));
                    }
                }
            },

            renderXBlockType: function(xblockType) {
                var locators = xblockType.get('locators'),
                    parentElement = this.$('.dashboard-section-components'),
                    locator, i, placeholderElement,
                    hasDashboardView = xblockType.get('views').indexOf('author_dashboard_view') >= 0;
                placeholderElement = $('<div></div>').appendTo(parentElement);
                if (hasDashboardView) {
                    this.refreshXBlockTypeView(placeholderElement, xblockType, 'author_dashboard_view');
                    placeholderElement = parentElement.append('<hr></hr><h3>Course Components</h3>');
                }
                for (i=0; i < locators.length; i++) {
                    locator = locators[i];
                    placeholderElement = $('<div data-locator="' + locator + '"></div>').appendTo(parentElement);
                    this.refreshChildXBlock(placeholderElement, true);
                }
            },

            findXBlockElement: function(target) {
                return $(target).closest('.studio-xblock-wrapper');
            },

            editComponent: function(xblockElement) {
                var self = this,
                    modal = new EditXBlockModal({ });
                modal.edit(xblockElement, this.model, {
                    refresh: function() {
                        self.refreshChildXBlock(xblockElement);
                    }
                });
            },

            deleteComponent: function(xblockElement) {
                var self = this;
                this.confirmThenRunOperation(gettext('Delete this component?'),
                    gettext('Deleting this component is permanent and cannot be undone.'),
                    gettext('Yes, delete this component'),
                    function() {
                        self.runOperationShowingMessage(gettext('Deleting&hellip;'),
                            function() {
                                var urlRoot = self.model.models[0].urlRoot;
                                return $.ajax({
                                    type: 'DELETE',
                                    url: urlRoot + "/" +
                                        xblockElement.data('locator') + "?" +
                                        $.param({recurse: true, all_versions: false})
                                }).success(function() {
                                    xblockElement.remove();
                                });
                            });
                    });
            },

            /**
             * Refresh an xblock element inline on the page, using the specified xblockInfo.
             * Note that the element is removed and replaced with the newly rendered xblock.
             * @param xblockElement The xblock element to be refreshed.
             * @returns {promise} A promise representing the complete operation.
             */
            refreshChildXBlock: function(xblockElement, collapsed, viewName) {
                var self = this,
                    xblockInfo,
                    TemporaryXBlockView,
                    temporaryView;
                xblockInfo = new XBlockInfo({
                    id: xblockElement.data('locator')
                });
                if (!viewName) {
                    viewName = collapsed ? 'dashboard_collapsed_view' : 'dashboard_view';
                }
                // There is only one Backbone view created on the container page, which is
                // for the container xblock itself. Any child xblocks rendered inside the
                // container do not get a Backbone view. Thus, create a temporary view
                // to render the content, and then replace the original element with the result.
                TemporaryXBlockView = XBlockView.extend({
                    updateHtml: function(element, html) {
                        // Replace the element with the new HTML content, rather than adding
                        // it as child elements.
                        this.$el = $(html).replaceAll(element);
                    }
                });
                temporaryView = new TemporaryXBlockView({
                    model: xblockInfo,
                    view: viewName,
                    el: xblockElement
                });
                return temporaryView.render({
                    success: function() {
                        self.onXBlockRefresh(temporaryView);
                        temporaryView.unbind();  // Remove the temporary view
                    }
                });
            },

            /**
             * Refresh an xblock element inline on the page, using the specified xblockInfo.
             * Note that the element is removed and replaced with the newly rendered xblock.
             * @param xblockElement The xblock element to be refreshed.
             * @returns {promise} A promise representing the complete operation.
             */
            refreshXBlockTypeView: function(xblockElement, xblockType, viewName) {
                var self = this,
                    TemporaryXBlockTypeView,
                    temporaryView;
                TemporaryXBlockTypeView = XBlockView.extend({
                    updateHtml: function(element, html) {
                        // Replace the element with the new HTML content, rather than adding
                        // it as child elements.
                        this.$el = $(html).replaceAll(element);
                    },

                    getXBlockURL: function() {
                        var studio_url = xblockType.get('studio_url'),
                            course_key_index = studio_url.indexOf('/slashes:'),
                            course_key_string = studio_url.substring(course_key_index),
                            xblockUrl = '/xblock_type' + course_key_string;
                        return decodeURIComponent(xblockUrl) + "/" + viewName;
                    }
                });
                temporaryView = new TemporaryXBlockTypeView({
                    model: xblockType,
                    view: viewName,
                    el: xblockElement
                });
                return temporaryView.render({
                    success: function() {
                        self.onXBlockRefresh(temporaryView);
                        temporaryView.unbind();  // Remove the temporary view
                    }
                });
            }
        });

        return DashboardPage;
    }); // end define();
