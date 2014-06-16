define(["jquery", "underscore", "js/views/xblock", "js/utils/module", "gettext", "js/views/feedback_notification",
    "jquery.ui"], // The container view uses sortable, which is provided by jquery.ui.
    function ($, _, XBlockView, ModuleUtils, gettext, NotificationView) {
        var reorderableClass = '.reorderable-container',
            sortableInitializedClass = '.ui-sortable',
            studioXBlockWrapperClass = '.studio-xblock-wrapper';

        var ContainerView = XBlockView.extend({

            xblockReady: function () {
                XBlockView.prototype.xblockReady.call(this);
                var reorderableContainer = this.$(reorderableClass),
                    alreadySortable = this.$(sortableInitializedClass),
                    newParent,
                    oldParent,
                    self = this;

                alreadySortable.sortable("destroy");

                reorderableContainer.sortable({
                    handle: '.drag-handle',

                    stop: function (event, ui) {
                        var saving, hideSaving, removeFromParent;

                        if (_.isUndefined(oldParent)) {
                            // If no actual change occurred,
                            // oldParent will never have been set.
                            return;
                        }

                        saving = new NotificationView.Mini({
                            title: gettext('Saving&hellip;')
                        });
                        saving.show();

                        hideSaving = function () {
                            saving.hide();
                        };

                        // If moving from one container to another,
                        // add to new container before deleting from old to
                        // avoid creating an orphan if the addition fails.
                        if (newParent) {
                            removeFromParent = oldParent;
                            self.updateChildren(newParent, function () {
                                self.updateChildren(removeFromParent, hideSaving);
                            });
                        } else {
                            // No new parent, only reordering within same container.
                            self.updateChildren(oldParent, hideSaving);
                        }

                        oldParent = undefined;
                        newParent = undefined;
                    },
                    update: function (event, ui) {
                        // When dragging from one ol to another, this method
                        // will be called twice (once for each list). ui.sender will
                        // be null if the change is related to the list the element
                        // was originally in (the case of a move within the same container
                        // or the deletion from a container when moving to a new container).
                        var parent = $(event.target).closest(studioXBlockWrapperClass);
                        if (ui.sender) {
                            // Move to a new container (the addition part).
                            newParent = parent;
                        } else {
                            // Reorder inside a container, or deletion when moving to new container.
                            oldParent = parent;
                        }
                    },
                    helper: "original",
                    opacity: '0.5',
                    placeholder: 'component-placeholder',
                    forcePlaceholderSize: true,
                    axis: 'y',
                    items: '> .is-draggable',
                    connectWith: reorderableClass,
                    tolerance: "pointer"

                });
            },

            updateChildren: function (targetParent, successCallback) {
                var children, childLocators, xblockInfo=this.model;

                // Find descendants with class "studio-xblock-wrapper" whose parent === targetParent.
                // This is necessary to filter our grandchildren, great-grandchildren, etc.
                children = targetParent.find(studioXBlockWrapperClass).filter(function () {
                    var parent = $(this).parent().closest(studioXBlockWrapperClass);
                    return parent.data('locator') === targetParent.data('locator');
                });

                childLocators = _.map(
                    children,
                    function (child) {
                        return $(child).data('locator');
                    }
                );
                $.ajax({
                    url: ModuleUtils.getUpdateUrl(targetParent.data('locator')),
                    type: 'PUT',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        children: childLocators
                    }),
                    success: function () {
                        // change data-parent on the element moved.
                        if (successCallback) {
                            successCallback();
                        }
                        // Update publish and last modified information from the server.
                        xblockInfo.fetch();
                    }
                });
            },

            refresh: function() {
                this.$(sortableInitializedClass).sortable('refresh');
            }
        });

        return ContainerView;
    }); // end define();
