/**
 * Subviews (usually small side panels) for XBlockContainerPage.
 */
define(['jquery', 'underscore', 'gettext', 'js/views/baseview', 'common/js/components/utils/view_utils',
    'js/views/utils/xblock_utils', 'js/views/utils/move_xblock_utils', 'edx-ui-toolkit/js/utils/html-utils',
    'js/views/utils/tagging_drawer_utils'],
function($, _, gettext, BaseView, ViewUtils, XBlockViewUtils, MoveXBlockUtils, HtmlUtils, TaggingDrawerUtils) {
    'use strict';

    var disabledCss = 'is-disabled';

    /**
         * A view that refreshes the view when certain values in the XBlockInfo have changed
         * after a server sync operation.
         */
    var ContainerStateListenerView = BaseView.extend({

        // takes XBlockInfo as a model
        initialize: function() {
            this.model.on('sync', this.onSync, this);
        },

        onSync: function(model) {
            if (this.shouldRefresh(model)) {
                this.render();
            }
        },

        shouldRefresh: function(model) {
            return false;
        },

        render: function() {}
    });

    var ContainerAccess = ContainerStateListenerView.extend({
        initialize: function() {
            ContainerStateListenerView.prototype.initialize.call(this);
            this.template = this.loadTemplate('container-access');
        },

        shouldRefresh: function(model) {
            return ViewUtils.hasChangedAttributes(model, ['has_partition_group_components', 'user_partitions']);
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                HtmlUtils.HTML(
                    this.template({
                        hasPartitionGroupComponents: this.model.get('has_partition_group_components'),
                        userPartitionInfo: this.model.get('user_partition_info')
                    })
                )
            );
            return this;
        }
    });

    var MessageView = ContainerStateListenerView.extend({
        initialize: function() {
            ContainerStateListenerView.prototype.initialize.call(this);
            this.template = this.loadTemplate('container-message');
        },

        shouldRefresh: function(model) {
            return ViewUtils.hasChangedAttributes(model, ['currently_visible_to_students']);
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                HtmlUtils.HTML(
                    this.template({currentlyVisibleToStudents: this.model.get('currently_visible_to_students')})
                )
            );
            return this;
        }
    });

    /**
         * A controller for updating the "View Live" button.
         */
    var ViewLiveButtonController = ContainerStateListenerView.extend({
        shouldRefresh: function(model) {
            return ViewUtils.hasChangedAttributes(model, ['published']);
        },

        render: function() {
            var viewLiveAction = this.$el.find('.button-view');
            if (this.model.get('published')) {
                viewLiveAction.removeClass(disabledCss).attr('aria-disabled', false);
            } else {
                viewLiveAction.addClass(disabledCss).attr('aria-disabled', true);
            }
        }
    });

    /**
         * Publisher is a view that supports the following:
         * 1) Publishing of a draft version of an xblock.
         * 2) Discarding of edits in a draft version.
         * 3) Display of who last edited the xblock, and when.
         * 4) Display of publish status (published, published with changes, changes with no published version).
         */
    var Publisher = BaseView.extend({
        events: {
            'click .action-publish': 'publish',
            'click .action-discard': 'discardChanges',
            'click .action-staff-lock': 'toggleStaffLock',
            'click .action-copy': 'copyToClipboard'
        },

        // takes XBlockInfo as a model

        initialize: function() {
            BaseView.prototype.initialize.call(this);
            this.template = this.loadTemplate('publish-xblock');
            this.model.on('sync', this.onSync, this);
            this.renderPage = this.options.renderPage;
            this.clipboardBroadcastChannel = this.options.clipboardBroadcastChannel;
        },

        onSync: function(model) {
            if (ViewUtils.hasChangedAttributes(model, [
                'has_changes', 'published', 'edited_on', 'edited_by', 'visibility_state',
                'has_explicit_staff_lock'
            ])) {
                this.render();
            }
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                HtmlUtils.HTML(
                    this.template({
                        visibilityState: this.model.get('visibility_state'),
                        visibilityClass: XBlockViewUtils.getXBlockVisibilityClass(
                            this.model.get('visibility_state')
                        ),
                        hasChanges: this.model.get('has_changes'),
                        editedOn: this.model.get('edited_on'),
                        editedBy: this.model.get('edited_by'),
                        published: this.model.get('published'),
                        publishedOn: this.model.get('published_on'),
                        publishedBy: this.model.get('published_by'),
                        released: this.model.get('released_to_students'),
                        releaseDate: this.model.get('release_date'),
                        releaseDateFrom: this.model.get('release_date_from'),
                        hasExplicitStaffLock: this.model.get('has_explicit_staff_lock'),
                        hideFromTOC: this.model.get('hide_from_toc'),
                        staffLockFrom: this.model.get('staff_lock_from'),
                        enableCopyUnit: this.model.get('enable_copy_paste_units'),
                        course: window.course,
                        HtmlUtils: HtmlUtils
                    })
                )
            );

            return this;
        },

        publish: function(e) {
            var xblockInfo = this.model;
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            ViewUtils.runOperationShowingMessage(gettext('Publishing'),
                function() {
                    return xblockInfo.save({publish: 'make_public'}, {patch: true});
                }).always(function() {
                xblockInfo.set('publish', null);
                // Hide any move notification if present.
                MoveXBlockUtils.hideMovedNotification();
            }).done(function() {
                xblockInfo.fetch();
            });
        },

        copyToClipboard: function(e) {
            e.preventDefault();
            e.stopPropagation();
            const clipboardEndpoint = "/api/content-staging/v1/clipboard/";
            const usageKeyToCopy = this.model.get('id');
            // Start showing a "Copying" notification:
            ViewUtils.runOperationShowingMessage(gettext('Copying'), () => {
                return $.postJSON(
                    clipboardEndpoint,
                    { usage_key: usageKeyToCopy },
                ).then((data) => {
                    const status = data.content?.status;
                    if (status === "ready") {
                        // something that enables the paste button in the actions dropdown
                        this.clipboardBroadcastChannel.postMessage(data);
                        return data;
                    } else if (status === "loading") {
                        // The clipboard is being loaded asynchonously.
                        // Poll the endpoint until the copying process is complete:
                        const deferred = $.Deferred();
                        const checkStatus = () => {
                            $.getJSON(clipboardEndpoint, (pollData) => {
                                const newStatus = pollData.content?.status;
                                if (newStatus === "ready") {
                                    // something that enables the paste button in actions dropdown
                                    this.clipboardBroadcastChannel.postMessage(pollData);
                                    deferred.resolve(pollData);
                                } else if (newStatus === "loading") {
                                    setTimeout(checkStatus, 1_000);
                                } else {
                                    deferred.reject();
                                    throw new Error(`Unexpected clipboard status "${newStatus}" in successful API response.`);
                                }
                            })
                        }
                        setTimeout(checkStatus, 1_000);
                        return deferred;
                    } else {
                        throw new Error(`Unexpected clipboard status "${status}" in successful API response.`);
                    }
                });
            });
        },

        discardChanges: function(e) {
            var xblockInfo = this.model,
                renderPage = this.renderPage;
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            ViewUtils.confirmThenRunOperation(gettext('Discard Changes'),
                gettext('Are you sure you want to revert to the last published version of the unit? You cannot undo this action.'),
                gettext('Discard Changes'),
                function() {
                    ViewUtils.runOperationShowingMessage(gettext('Discarding Changes'),
                        function() {
                            return xblockInfo.save({publish: 'discard_changes'}, {patch: true});
                        }).always(function() {
                        xblockInfo.set('publish', null);
                        // Hide any move notification if present.
                        MoveXBlockUtils.hideMovedNotification();
                    }).done(function() {
                        renderPage();
                    });
                }
            );
        },

        toggleStaffLock: function(e) {
            var xblockInfo = this.model,
                self = this,
                enableStaffLock, hasInheritedStaffLock,
                saveAndPublishStaffLock, revertCheckBox;
            if (e && e.preventDefault) {
                e.preventDefault();
            }
            enableStaffLock = !xblockInfo.get('has_explicit_staff_lock');
            hasInheritedStaffLock = xblockInfo.get('ancestor_has_staff_lock');

            revertCheckBox = function() {
                self.checkStaffLock(!enableStaffLock);
            };

            saveAndPublishStaffLock = function() {
                // Setting staff lock to null when disabled will delete the field from this xblock,
                // allowing it to use the inherited value instead of using false explicitly.
                return xblockInfo.save({
                    publish: 'republish',
                    metadata: {visible_to_staff_only: enableStaffLock ? true : null}
                },
                {patch: true}
                ).always(function() {
                    xblockInfo.set('publish', null);
                }).done(function() {
                    xblockInfo.fetch();
                }).fail(function() {
                    revertCheckBox();
                });
            };

            this.checkStaffLock(enableStaffLock);
            if (enableStaffLock && !hasInheritedStaffLock) {
                ViewUtils.runOperationShowingMessage(gettext('Hiding from Students'),
                    _.bind(saveAndPublishStaffLock, self));
            } else if (enableStaffLock && hasInheritedStaffLock) {
                ViewUtils.runOperationShowingMessage(gettext('Explicitly Hiding from Students'),
                    _.bind(saveAndPublishStaffLock, self));
            } else if (!enableStaffLock && hasInheritedStaffLock) {
                ViewUtils.runOperationShowingMessage(gettext('Inheriting Student Visibility'),
                    _.bind(saveAndPublishStaffLock, self));
            } else {
                ViewUtils.confirmThenRunOperation(gettext('Make Visible to Students'),
                    gettext('If the unit was previously published and released to students, any changes you made to the unit when it was hidden will now be visible to students. Do you want to proceed?'),
                    gettext('Make Visible to Students'),
                    function() {
                        ViewUtils.runOperationShowingMessage(gettext('Making Visible to Students'),
                            _.bind(saveAndPublishStaffLock, self));
                    },
                    function() {
                        // On cancel, revert the check in the check box
                        revertCheckBox();
                    }
                );
            }
        },

        checkStaffLock: function(check) {
            this.$('.action-staff-lock i').removeClass('fa-check-square-o fa-square-o');
            this.$('.action-staff-lock i').addClass(check ? 'fa-check-square-o' : 'fa-square-o');
        }
    });

    /**
         * PublishHistory displays when and by whom the xblock was last published, if it ever was.
         */
    var PublishHistory = BaseView.extend({
        // takes XBlockInfo as a model

        initialize: function() {
            BaseView.prototype.initialize.call(this);
            this.template = this.loadTemplate('publish-history');
            this.model.on('sync', this.onSync, this);
        },

        onSync: function(model) {
            if (ViewUtils.hasChangedAttributes(model, ['published', 'published_on', 'published_by'])) {
                this.render();
            }
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                HtmlUtils.HTML(
                    this.template({
                        published: this.model.get('published'),
                        published_on: this.model.get('published_on'),
                        published_by: this.model.get('published_by')
                    })
                )
            );

            return this;
        }
    });

    /**
     * TagList displays the tags of a unit.
     */
    var TagList = BaseView.extend({
        // takes XBlockInfo as a model

        events: {
            'click .wrapper-tag-header': 'expandTagContainer',
            'click .tagging-label': 'expandContentTag',
            'click .manage-tag-button': 'openManageTagDrawer',
            'keydown .wrapper-tag-header': 'handleKeyDownOnHeader',
            'keydown .tagging-label': 'handleKeyDownOnContentTag',
            'keydown .manage-tag-button': 'handleKeyDownOnTagDrawer',
        },

        initialize: function() {
            BaseView.prototype.initialize.call(this);
            this.template = this.loadTemplate('tag-list');
            this.model.on('sync', this.onSync, this);
        },

        onSync: function(model) {
            if (ViewUtils.hasChangedAttributes(model, ['tags'])) {
                this.render();
            }
        },

        setupMessageListener: function () {
            window.addEventListener(
                "message", (event) => {
                    // Listen any message from Manage tags drawer.
                    var data = event.data;
                    var courseAuthoringUrl = new URL(this.model.get("course_authoring_url")).origin;
                    if (event.origin == courseAuthoringUrl
                        && data.type == 'authoring.events.tags.updated') {
                        // This message arrives when there is a change in the tag list.
                        // The message contains the new list of tags.
                        data = data.data
                        if (data.contentId == this.model.id) {
                            this.model.set('tags', this.buildTaxonomyTree(data));
                            this.render();
                        }
                    }
                },
            );
        },

        buildTaxonomyTree: function(data) {
            // TODO We can use this function for the initial request of tags
            // and avoid to use two functions (see get_unit_tags on contentstore/views/component.py)

            var taxonomyList = [];
            var totalCount = 0;
            var actualId = 0;
            data.taxonomies.forEach((taxonomy) => {
                // Build a tag tree for each taxonomy
                var rootTagsValues = [];
                var tags = {};
                taxonomy.tags.forEach((tag) => {
                    // Creates the tags for all the lineage of this tag
                    for (let i = tag.lineage.length - 1; i >= 0; i--){
                        var tagValue = tag.lineage[i]
                        var tagProcessedBefore = tags.hasOwnProperty(tagValue);
                        if (!tagProcessedBefore) {
                            tags[tagValue] = {
                                id: actualId,
                                value: tagValue,
                                children: [],
                            }
                            actualId++;
                            if (i == 0) {
                                rootTagsValues.push(tagValue);
                            }
                        }
                        if (i !== tag.lineage.length - 1) {
                            // Add a child into the children list
                            tags[tagValue].children.push(tags[tag.lineage[i + 1]])
                        }
                        if (tagProcessedBefore) {
                            // Break this loop if the tag has been processed before,
                            // we don't need to process lineage again to avoid duplicates.
                            break;
                        }
                    }
                })

                var tagCount = Object.keys(tags).length;
                // Add the tree to the taxonomy list
                taxonomyList.push({
                    id: taxonomy.taxonomyId,
                    value: taxonomy.name,
                    tags: rootTagsValues.map(rootValue => tags[rootValue]),
                    count: tagCount,
                });
                totalCount += tagCount;
            });

            return {
                count: totalCount,
                taxonomies: taxonomyList,
            };
        },

        handleKeyDownOnHeader: function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.expandTagContainer();
            }
        },

        handleKeyDownOnContentTag: function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.expandContentTag(event);
            }
        },

        handleKeyDownOnTagDrawer: function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.openManageTagDrawer();
            }
        },

        expandTagContainer: function() {
            var $content = this.$('.wrapper-tags .wrapper-tag-content'),
                $header = this.$('.wrapper-tags .wrapper-tag-header'),
                $icon = this.$('.wrapper-tags .wrapper-tag-header .icon');

            if ($content.hasClass('is-hidden')) {
                $content.removeClass('is-hidden');
                $icon.addClass('fa-caret-up');
                $icon.removeClass('fa-caret-down');
                $header.attr('aria-expanded', 'true');
            } else {
                $content.addClass('is-hidden');
                $icon.removeClass('fa-caret-up');
                $icon.addClass('fa-caret-down');
                $header.attr('aria-expanded', 'false');
            }
        },

        expandContentTag: function(event) {
            var contentId = event.target.id,
                $content = this.$(`.wrapper-tags .content-tags-${contentId}`),
                $header = this.$(`.wrapper-tags .tagging-label-${contentId}`),
                $icon = this.$(`.wrapper-tags .tagging-label-${contentId} .icon`);

            if ($content.hasClass('is-hidden')) {
                $content.removeClass('is-hidden');
                $icon.addClass('fa-caret-up');
                $icon.removeClass('fa-caret-down');
                $header.attr('aria-expanded', 'true');
            } else {
                $content.addClass('is-hidden');
                $icon.removeClass('fa-caret-up');
                $icon.addClass('fa-caret-down');
                $header.attr('aria-expanded', 'false');
            }
        },

        renderTagElements: function(tags, depth, parentId) {
            /* This function displays the tags in the sidebar of the legacy Unit Outline Page.
             * It is not used when the Authoring MFE iframes a component in the Unit Outline. */
            const parentElement = document.querySelector(`.content-tags-${parentId}`);
            if (!parentElement) return;

            const tagListElement = this;
            tags.forEach(function(tag) {
                var tagContentElement = document.createElement('div'),
                    tagValueElement = document.createElement('span');

                // Element that contains the tag value and the arrow icon
                tagContentElement.style.marginLeft = `${depth}em`;
                tagContentElement.className = `tagging-label tagging-label-tag-${tag.id}`;
                tagContentElement.id = `tag-${tag.id}`;

                // Element that contains the tag value
                tagValueElement.textContent = tag.value;
                tagValueElement.id = `tag-${tag.id}`;
                tagValueElement.className = 'tagging-label-value';

                tagContentElement.appendChild(tagValueElement);
                parentElement.appendChild(tagContentElement);

                if (tag.children.length > 0) {
                    var tagIconElement = document.createElement('span'),
                        tagChildrenElement = document.createElement('div');

                    // Arrow icon
                    tagIconElement.className = 'icon fa fa-caret-down';
                    tagIconElement.ariaHidden = 'true';
                    tagIconElement.id = `tag-${tag.id}`;

                    // Element that contains the children of this tag
                    tagChildrenElement.className = `content-tags-tag-${tag.id} is-hidden`;

                    tagContentElement.tabIndex = 0;
                    tagContentElement.role = "button";
                    tagContentElement.ariaExpanded = "false";
                    tagContentElement.setAttribute('aria-controls', `content-tags-tag-${tag.id}`);
                    tagContentElement.appendChild(tagIconElement);
                    tagContentElement.className += ' tagging-label-link';
                    parentElement.appendChild(tagChildrenElement);

                    // Render children
                    tagListElement.renderTagElements(tag.children, depth + 1, `tag-${tag.id}`);
                }
            });
        },

        renderTags: function() {
            if (this.model.get('tags') !== null) {
                const taxonomies = this.model.get('tags').taxonomies;
                const tagListElement = this;
                taxonomies.forEach(function(taxonomy) {
                    tagListElement.renderTagElements(taxonomy.tags, 1, `tax-${taxonomy.id}`);
                });
            }
        },

        openManageTagDrawer: function() {
            const taxonomyTagsWidgetUrl = this.model.get('taxonomy_tags_widget_url');
            const contentId = this.model.get('id');

            TaggingDrawerUtils.openDrawer(taxonomyTagsWidgetUrl, contentId);
        },

        render: function() {
            HtmlUtils.setHtml(
                this.$el,
                HtmlUtils.HTML(
                    this.template({
                        tags: this.model.get('tags'),
                    })
                )
            );

            this.renderTags();

            return this;
        }
    });

    return {
        MessageView: MessageView,
        ViewLiveButtonController: ViewLiveButtonController,
        Publisher: Publisher,
        PublishHistory: PublishHistory,
        ContainerAccess: ContainerAccess,
        TagList: TagList
    };
}); // end define();
