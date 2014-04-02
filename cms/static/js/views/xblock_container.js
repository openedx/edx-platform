/**
 * XBlockContainerView is used to display an xblock which has children, and allows the
 * user to interact with the children.
 */
define(["jquery", "underscore", "js/views/baseview", "js/views/xblock", "js/views/modals/edit_xblock"],
    function ($, _, BaseView, XBlockView, EditXBlockModal) {

        var XBlockContainerView = BaseView.extend({
            // takes XBlockInfo as a model

            view: 'container_preview',

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.noContentElement = this.$('.no-container-content');
                this.xblockView = new XBlockView({
                    el: this.$('.wrapper-xblock'),
                    model: this.model,
                    view: this.view
                });
            },

            render: function(options) {
                var self = this,
                    noContentElement = this.noContentElement,
                    xblockView = this.xblockView,
                    loadingElement = this.$('.ui-loading');
                loadingElement.removeClass('is-hidden');

                // Hide both blocks until we know which one to show
                noContentElement.addClass('is-hidden');
                xblockView.$el.addClass('is-hidden');

                // Add actions to any top level buttons, e.g. "Edit" of the container itself
                self.addButtonActions(this.$el);

                // Render the xblock
                xblockView.render({
                    success: function(xblock) {
                        if (xblockView.hasChildXBlocks()) {
                            xblockView.$el.removeClass('is-hidden');
                            self.addButtonActions(xblockView.$el);
                        } else {
                            noContentElement.removeClass('is-hidden');
                        }
                        loadingElement.addClass('is-hidden');
                        self.delegateEvents();
                    }
                });
            },

            findXBlockElement: function(target) {
                return $(target).closest('[data-locator]');
            },

            addButtonActions: function(element) {
                var self = this;
                element.find('.edit-button').click(function(event) {
                    var modal,
                        target = event.target,
                        xblockElement = self.findXBlockElement(target);
                    event.preventDefault();
                    modal = new EditXBlockModal({
                        el: $('.edit-xblock-modal')
                    });
                    modal.edit(xblockElement, self.model,
                        {
                            refresh: function(xblockInfo) {
                                self.refreshXBlock(xblockInfo, xblockElement);
                            }
                        });
                });
            },

            refreshXBlock: function(xblockInfo, xblockElement) {
                var self = this,
                    temporaryView;
                // Create a temporary view to render the updated XBlock into
                temporaryView = new XBlockView({
                    el: xblockElement,
                    model: xblockInfo,
                    view: this.view
                });
                temporaryView.render({
                    success: function() {
                        temporaryView.unbind();  // Remove the temporary view
                        self.addButtonActions(xblockElement);
                    }
                });
            }
        });

        return XBlockContainerView;
    }); // end define();
