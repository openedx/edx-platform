/**
 * XBlockContainerView is used to display an xblock which has children, and allows the
 * user to interact with the children.
 */
define(["jquery", "underscore", "gettext", "js/views/feedback_notification", "js/views/feedback_prompt", "js/views/baseview", "js/views/xblock", "js/views/modals/edit_xblock", "js/models/xblock_info"],
    function ($, _, gettext, NotificationView, PromptView, BaseView, XBlockView, EditXBlockModal, XBlockInfo) {

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

            getURLRoot: function() {
                return this.xblockView.model.urlRoot;
            },

            addButtonActions: function(element) {
                var self = this;
                element.find('.edit-button').click(function(event) {
                    var modal,
                        target = event.target,
                        xblockElement = self.findXBlockElement(target);
                    event.preventDefault();
                    modal = new EditXBlockModal({ });
                    modal.edit(xblockElement, self.model,
                        {
                            refresh: function(xblockInfo) {
                                self.refreshXBlock(xblockInfo, xblockElement);
                            }
                        });
                });
                element.find('.duplicate-button').click(function(event) {
                    event.preventDefault();
                    self.duplicateComponent(
                        self.findXBlockElement(event.target)
                    );
                });
                element.find('.delete-button').click(function(event) {
                    event.preventDefault();
                    self.deleteComponent(
                        self.findXBlockElement(event.target)
                    );
                });
            },

            duplicateComponent: function(xblockElement) {
                var self = this,
                    parentElement = self.findXBlockElement(xblockElement.parent()),
                    duplicating = new NotificationView.Mini({
                        title: gettext('Duplicating&hellip;')
                    });

                duplicating.show();
                return $.postJSON(self.getURLRoot(), {
                    duplicate_source_locator: xblockElement.data('locator'),
                    parent_locator: parentElement.data('locator')
                }, function(data) {
                    // copy the element
                    var duplicatedElement = xblockElement.clone(false);

                    // place it after the original element
                    xblockElement.after(duplicatedElement);

                    // update its locator id
                    duplicatedElement.attr('data-locator', data.locator);

                    // have it refresh itself
                    self.refreshXBlockElement(duplicatedElement);

                    // hide the notification
                    duplicating.hide();
                });
            },


            deleteComponent: function(xblockElement) {
                var self = this, deleting;
                return new PromptView.Warning({
                    title: gettext('Delete this component?'),
                    message: gettext('Deleting this component is permanent and cannot be undone.'),
                    actions: {
                        primary: {
                            text: gettext('Yes, delete this component'),
                            click: function(prompt) {
                                prompt.hide();
                                deleting = new NotificationView.Mini({
                                    title: gettext('Deleting&hellip;')
                                });
                                deleting.show();
                                return $.ajax({
                                    type: 'DELETE',
                                    url:
                                        self.getURLRoot() + "/" +
                                            xblockElement.data('locator') + "?" +
                                            $.param({recurse: true, all_versions: true})
                                }).success(function() {
                                    deleting.hide();
                                    xblockElement.remove();
                                });
                            }
                        },
                        secondary: {
                            text: gettext('Cancel'),
                            click: function(prompt) {
                                return prompt.hide();
                            }
                        }
                    }
                }).show();
            },

            refreshXBlockElement: function(xblockElement) {
                this.refreshXBlock(
                    new XBlockInfo({
                        id: xblockElement.data('locator')
                    }),
                    xblockElement
                );
            },

            refreshXBlock: function(xblockInfo, xblockElement) {
                var self = this, temporaryView;

                // There is only one Backbone view created on the container page, which is
                // for the container xblock itself. Any child xblocks rendered inside the
                // container do not get a Backbone view. Thus, create a temporary XBlock
                // around the child element so that it can be refreshed.
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

