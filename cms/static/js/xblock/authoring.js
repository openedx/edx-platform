/**
 * Client-side logic to support XBlock authoring.
 */
(function($) {
    'use strict';

    function VisibilityEditorView(runtime, element) {
        this.getGroupAccess = function() {
            var groupAccess, userPartitionId, selectedGroupIds;
            if (element.find('.visibility-level-all').prop('checked')) {
                return {};
            }
            userPartitionId = element.find('.wrapper-visibility-specific').data('user-partition-id').toString();
            selectedGroupIds = [];
            element.find('.field-visibility-content-group input:checked').each(function(index, input) {
                selectedGroupIds.push(parseInt($(input).val()));
            });
            groupAccess = {};
            groupAccess[userPartitionId] = selectedGroupIds;
            return groupAccess;
        };

        element.find('.field-visibility-level input').change(function(event) {
            if ($(event.target).hasClass('visibility-level-all')) {
                element.find('.field-visibility-content-group input').prop('checked', false);
            }
        });
        element.find('.field-visibility-content-group input').change(function(event) {
            element.find('.visibility-level-all').prop('checked', false);
            element.find('.visibility-level-specific').prop('checked', true);
        });
    }

    VisibilityEditorView.prototype.collectFieldData = function collectFieldData() {
        return {
            metadata: {
                "group_access": this.getGroupAccess()
            }
        };
    };

    function initializeVisibilityEditor(runtime, element) {
        return new VisibilityEditorView(runtime, element);
    }

    // XBlock initialization functions must be global
    window.VisibilityEditorInit = initializeVisibilityEditor;
})($);
