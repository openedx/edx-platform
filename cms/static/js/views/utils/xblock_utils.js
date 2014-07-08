/**
 * Provides utilities for views to work with xblocks.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils", "js/utils/module"],
    function($, _, gettext, ViewUtils, ModuleUtils) {
        var addXBlock, deleteXBlock, createUpdateRequestData, updateXBlockField, VisibilityState,
            getXBlockVisibilityClass, getXBlockListTypeClass, updateXBlockFields;

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
            staffOnly: 'staff_only'
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
            return ViewUtils.runOperationShowingMessage(gettext('Adding&hellip;'),
                function() {
                    var addOperation = $.Deferred();
                    analytics.track('Created a ' + category, {
                        'course': course_location_analytics,
                        'display_name': displayName
                    });
                    $.postJSON(ModuleUtils.getUpdateUrl(),
                        {
                            'parent_locator': parentLocator,
                            'category': category,
                            'display_name': displayName
                        }, function(data) {
                            var locator = data.locator;
                            addOperation.resolve(locator);
                        });
                    return addOperation.promise();
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
                xblockType = xblockType || gettext('component');
            ViewUtils.confirmThenRunOperation(
                interpolate(gettext('Delete this %(xblock_type)s?'), { xblock_type: xblockType }, true),
                interpolate(
                    gettext('Deleting this %(xblock_type)s is permanent and cannot be undone.'),
                    { xblock_type: xblockType }, true
                ),
                interpolate(gettext('Yes, delete this %(xblock_type)s'), { xblock_type: xblockType }, true),
                function() {
                    ViewUtils.runOperationShowingMessage(gettext('Deleting&hellip;'),
                        function() {
                            return $.ajax({
                                type: 'DELETE',
                                url: url
                            }).success(function() {
                                deletion.resolve();
                            });
                        });
                });
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
            return ViewUtils.runOperationShowingMessage(gettext('Saving&hellip;'),
                function() {
                    return xblockInfo.save(requestData, { patch: true });
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
            options = _.extend({}, { patch: true }, options);
            return ViewUtils.runOperationShowingMessage(gettext('Saving&hellip;'),
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

        getXBlockListTypeClass = function (xblockType) {
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

        return {
            'VisibilityState': VisibilityState,
            'addXBlock': addXBlock,
            'deleteXBlock': deleteXBlock,
            'updateXBlockField': updateXBlockField,
            'getXBlockVisibilityClass': getXBlockVisibilityClass,
            'getXBlockListTypeClass': getXBlockListTypeClass,
            'updateXBlockFields': updateXBlockFields
        };
    });
