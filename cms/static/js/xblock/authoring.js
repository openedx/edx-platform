/**
 * Client-side logic to support XBlock authoring.
 */
(function($) {
    'use strict';

    function VisibilityEditorView(runtime, element) {
        this.getGroupAccess = function() {
            var groupAccess = {},
                checkboxValues,
                partitionId,
                groupId,

                // This constant MUST match the group ID
                // defined by VerificationPartitionScheme on the backend!
                ALLOW_GROUP_ID = 1;

            if (element.find('.visibility-level-all').prop('checked')) {
                return {};
            }

            // Cohort partitions (user is allowed to select more than one)
            element.find('.field-visibility-content-group input:checked').each(function(index, input) {
                checkboxValues = $(input).val().split("-");
                partitionId = parseInt(checkboxValues[0], 10);
                groupId = parseInt(checkboxValues[1], 10);

                if (groupAccess.hasOwnProperty(partitionId)) {
                    groupAccess[partitionId].push(groupId);
                } else {
                    groupAccess[partitionId] = [groupId];
                }
            });

            // Verification partitions (user can select exactly one)
            if (element.find('#verification-access-checkbox').prop('checked')) {
                partitionId = parseInt($('#verification-access-dropdown').val(), 10);
                groupAccess[partitionId] = [ALLOW_GROUP_ID];
            }

            return groupAccess;
        };

        // When selecting "all students and staff", uncheck the specific groups
        element.find('.field-visibility-level input').change(function(event) {
            if ($(event.target).hasClass('visibility-level-all')) {
                element.find('.field-visibility-content-group input, .field-visibility-verification input')
                    .prop('checked', false);
            }
        });

        // When selecting a specific group, deselect "all students and staff" and
        // select "specific content groups" instead.`
        element.find('.field-visibility-content-group input, .field-visibility-verification input')
            .change(function() {
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
