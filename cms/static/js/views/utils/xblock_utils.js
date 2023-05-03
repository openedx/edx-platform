/**
 * Provides utilities for views to work with xblocks.
 */
define(['jquery', 'underscore', 'gettext', 'common/js/components/utils/view_utils', 'js/utils/module',
    'js/models/xblock_info', 'edx-ui-toolkit/js/utils/string-utils'],
function($, _, gettext, ViewUtils, ModuleUtils, XBlockInfo, StringUtils) {
    'use strict';
    var addXBlock, duplicateXBlock, deleteXBlock, createUpdateRequestData, updateXBlockField, VisibilityState,
        getXBlockVisibilityClass, getXBlockListTypeClass, updateXBlockFields, getXBlockType, findXBlockInfo,
        moveXBlock;

    /**
         * Represents the possible visibility states for an xblock:
         *
         *   live - the block and all of its descendants are live to students (excluding staff only)
         *     Note: Live means both published and released.
         *
         *   ready - the block is ready to go live and all of its descendants are live or ready (excluding staff only)
         *     Note: content is ready when it is published and scheduled with a release date in the future.
         *
         *   unscheduled - the block and all of its descendants have no release date (excluding staff only)
         *     Note: it is valid for items to be published with no release date in which case they are unscheduled.
         *
         *   needsAttention - the block or its descendants need attention
         *     i.e. there is some content that is not fully live, ready, unscheduled or staff only.
         *     For example: one subsection has draft content, or there's both unreleased and released content
         *     in one section.
         *
         *   staffOnly - all of the block's content is to be shown to staff only
         *     Note: staff only items do not affect their parent's state.
         */
    VisibilityState = {
        live: 'live',
        ready: 'ready',
        unscheduled: 'unscheduled',
        needsAttention: 'needs_attention',
        staffOnly: 'staff_only',
        gated: 'gated'
    };

    /**
         * Adds an xblock based upon the data attributes of the specified add button. A promise
         * is returned, and the new locator is passed to all done handlers.
         * @param target The add button that was clicked upon.
         * @returns {jQuery promise} A promise representing the addition of the xblock.
         */
    addXBlock = function(target) {
        var parentLocator = target.data('parent'),
            category = target.data('category'),
            displayName = target.data('default-name');
        return ViewUtils.runOperationShowingMessage(gettext('Adding'),
            function() {
                var addOperation = $.Deferred();
                analytics.track('Created a ' + category, {
                    course: course_location_analytics,
                    display_name: displayName
                });
                $.postJSON(ModuleUtils.getUpdateUrl(),
                    {
                        parent_locator: parentLocator,
                        category: category,
                        display_name: displayName
                    }, function(data) {
                        var locator = data.locator;
                        addOperation.resolve(locator);
                    });
                return addOperation.promise();
            });
    };

    /**
         * Duplicates the specified xblock element in its parent xblock.
         * @param {jquery Element}  xblockElement  The xblock element to be duplicated.
         * @param {jquery Element}  parentElement  Parent element of the xblock element to be duplicated,
         *      new duplicated xblock would be placed under this xblock.
         * @returns {jQuery promise} A promise representing the duplication of the xblock.
         */
    duplicateXBlock = function(xblockElement, parentElement) {
        return ViewUtils.runOperationShowingMessage(gettext('Duplicating'),
            function() {
                var duplicationOperation = $.Deferred();
                $.postJSON(ModuleUtils.getUpdateUrl(), {
                    duplicate_source_locator: xblockElement.data('locator'),
                    parent_locator: parentElement.data('locator')
                }, function(data) {
                    duplicationOperation.resolve(data);
                })
                    .fail(function() {
                        duplicationOperation.reject();
                    });
                return duplicationOperation.promise();
            });
    };

    /**
         * Moves the specified xblock in a new parent xblock.
         * @param {String}  sourceLocator  Locator of xblock element to be moved.
         * @param {String}  targetParentLocator  Locator of the target parent xblock, moved xblock would be placed
         *      under this xblock.
         * @param {Integer}  targetIndex  Intended index position of the xblock in parent xblock. If provided,
         *      xblock would be placed at the particular index in the parent xblock.
         * @returns {jQuery promise} A promise representing the moving of the xblock.
         */
    moveXBlock = function(sourceLocator, targetParentLocator, targetIndex) {
        var moveOperation = $.Deferred(),
            operationText = targetIndex !== undefined ? gettext('Undo moving') : gettext('Moving');
        return ViewUtils.runOperationShowingMessage(operationText,
            function() {
                $.patchJSON(ModuleUtils.getUpdateUrl(), {
                    move_source_locator: sourceLocator,
                    parent_locator: targetParentLocator,
                    target_index: targetIndex
                }, function(response) {
                    moveOperation.resolve(response);
                })
                    .fail(function() {
                        moveOperation.reject();
                    });
                return moveOperation.promise();
            });
    };

    /**
         * Deletes the specified xblock.
         * @param xblockInfo The model for the xblock to be deleted.
         * @param xblockType A string representing the type of the xblock to be deleted.
         * @returns {jQuery promise} A promise representing the deletion of the xblock.
         */
    deleteXBlock = function(xblockInfo, xblockType) {
        var deletion = $.Deferred(),
            url = ModuleUtils.getUpdateUrl(xblockInfo.id),
            operation = function() {
                ViewUtils.runOperationShowingMessage(gettext('Deleting'),
                    function() {
                        return $.ajax({
                            type: 'DELETE',
                            url: url
                        }).success(function() {
                            deletion.resolve();
                        });
                    }
                );
            },
            messageBody;
        xblockType = xblockType || 'component'; // eslint-disable-line no-param-reassign
        messageBody = StringUtils.interpolate(
            gettext('Deleting this {xblock_type} is permanent and cannot be undone.'),
            {xblock_type: xblockType},
            true
        );

        if (xblockInfo.get('is_prereq')) {
            messageBody += ' ' + gettext('Any content that has listed this content as a prerequisite will also have access limitations removed.');   // eslint-disable-line max-len
            ViewUtils.confirmThenRunOperation(
                StringUtils.interpolate(
                    gettext('Delete this {xblock_type} (and prerequisite)?'),
                    {xblock_type: xblockType},
                    true
                ),
                messageBody,
                StringUtils.interpolate(
                    gettext('Yes, delete this {xblock_type}'),
                    {xblock_type: xblockType},
                    true
                ),
                operation
            );
        } else {
            ViewUtils.confirmThenRunOperation(
                StringUtils.interpolate(
                    gettext('Delete this {xblock_type}?'),
                    {xblock_type: xblockType},
                    true
                ),
                messageBody,
                StringUtils.interpolate(
                    gettext('Yes, delete this {xblock_type}'),
                    {xblock_type: xblockType},
                    true
                ),
                operation
            );
        }
        return deletion.promise();
    };

    createUpdateRequestData = function(fieldName, newValue) {
        var metadata = {};
        metadata[fieldName] = newValue;
        return {
            metadata: metadata
        };
    };

    /**
         * Updates the specified field of an xblock to a new value.
         * @param {Backbone Model} xblockInfo The XBlockInfo model representing the xblock.
         * @param {String} fieldName The xblock field name to be updated.
         * @param {*} newValue The new value for the field.
         * @returns {jQuery promise} A promise representing the updating of the field.
         */
    updateXBlockField = function(xblockInfo, fieldName, newValue) {
        var requestData = createUpdateRequestData(fieldName, newValue);
        return ViewUtils.runOperationShowingMessage(gettext('Saving'),
            function() {
                return xblockInfo.save(requestData, {patch: true});
            });
    };

    /**
         * Updates the specified fields of an xblock to a new values.
         * @param {Backbone Model} xblockInfo The XBlockInfo model representing the xblock.
         * @param {Object} xblockData Object representing xblock data as accepted on server.
         * @param {Object} [options] Hash with options.
         * @returns {jQuery promise} A promise representing the updating of the xblock values.
         */
    updateXBlockFields = function(xblockInfo, xblockData, options) {
        options = _.extend({}, {patch: true}, options);
        return ViewUtils.runOperationShowingMessage(gettext('Saving'),
            function() {
                return xblockInfo.save(xblockData, options);
            }
        );
    };

    /**
         * Returns the CSS class to represent the specified xblock visibility state.
         */
    getXBlockVisibilityClass = function(visibilityState) {
        if (visibilityState === VisibilityState.staffOnly) {
            return 'is-staff-only';
        }
        if (visibilityState === VisibilityState.gated) {
            return 'is-gated';
        }
        if (visibilityState === VisibilityState.live) {
            return 'is-live';
        }
        if (visibilityState === VisibilityState.ready) {
            return 'is-ready';
        }
        if (visibilityState === VisibilityState.needsAttention) {
            return 'has-warnings';
        }
        return '';
    };

    getXBlockListTypeClass = function(xblockType) {
        var listType = 'list-unknown';
        if (xblockType === 'course') {
            listType = 'list-sections';
        } else if (xblockType === 'section') {
            listType = 'list-subsections';
        } else if (xblockType === 'subsection') {
            listType = 'list-units';
        }
        return listType;
    };

    getXBlockType = function(category, parentInfo, translate) {
        var xblockType = category;
        if (category === 'chapter') {
            xblockType = translate ? gettext('section') : 'section';
        } else if (category === 'sequential') {
            xblockType = translate ? gettext('subsection') : 'subsection';
        } else if (category === 'vertical' && (!parentInfo || parentInfo.get('category') === 'sequential')) {
            xblockType = translate ? gettext('unit') : 'unit';
        }
        return xblockType;
    };

    findXBlockInfo = function(xblockWrapperElement, defaultXBlockInfo) {
        var xblockInfo = defaultXBlockInfo,
            xblockElement,
            displayName,
            hasChildren;
        if (xblockWrapperElement.length > 0) {
            xblockElement = xblockWrapperElement.find('.xblock');
            displayName = xblockWrapperElement.find(
                '.xblock-header .header-details .xblock-display-name'
            ).text().trim();
            // If not found, try looking for the old unit page style rendering.
            // Only used now by static pages.
            if (!displayName) {
                displayName = xblockElement.find('.component-header').text().trim();
            }
            hasChildren = defaultXBlockInfo ? defaultXBlockInfo.get('has_children') : false;
            xblockInfo = new XBlockInfo({
                id: xblockWrapperElement.data('locator'),
                courseKey: xblockWrapperElement.data('course-key'),
                category: xblockElement.data('block-type'),
                display_name: displayName,
                has_children: hasChildren
            });
        }
        return xblockInfo;
    };

    return {
        VisibilityState: VisibilityState,
        addXBlock: addXBlock,
        moveXBlock: moveXBlock,
        duplicateXBlock: duplicateXBlock,
        deleteXBlock: deleteXBlock,
        updateXBlockField: updateXBlockField,
        getXBlockVisibilityClass: getXBlockVisibilityClass,
        getXBlockListTypeClass: getXBlockListTypeClass,
        updateXBlockFields: updateXBlockFields,
        getXBlockType: getXBlockType,
        findXBlockInfo: findXBlockInfo
    };
});
