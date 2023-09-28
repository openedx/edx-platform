/**
 * Client-side logic to support XBlock authoring.
 */
(function($) {
    'use strict';

    function VisibilityEditorView(runtime, element) {
        this.getGroupAccess = function() {
            var groupAccess = {},
                partitionId,
                groupId;

            // Get the selected user partition (only allowed to select one).
            partitionId = parseInt(element.find('.partition-visibility select').val(), 10);

            // "All Learners and Staff" is selected (or "Select a group type", which is only shown when
            // current visibility is "All Learners and Staff" at the time the dialog is opened).
            if (partitionId === -1) {
                return {};
            }

            // Otherwise get the checked groups within the selected partition.
            element.find(
                '.partition-group-visibility-' + partitionId + ' input:checked'
            ).each(function(index, input) {
                groupId = parseInt($(input).val(), 10);

                if (groupAccess.hasOwnProperty(partitionId)) {
                    groupAccess[partitionId].push(groupId);
                } else {
                    groupAccess[partitionId] = [groupId];
                }
            });

            return groupAccess;
        };

        element.find('.partition-visibility select').change(function(event) {
            var partitionId;

            // Hide all the partition group options.
            element.find('.partition-group-control').addClass('is-hidden');

            // If a partition is selected, display its groups.
            partitionId = parseInt($(event.target).val(), 10);
            if (partitionId >= 0) {
                element.find('.partition-group-control-' + partitionId).removeClass('is-hidden');
            }
        });
    }

    VisibilityEditorView.prototype.collectFieldData = function collectFieldData() {
        return {metadata: {group_access: this.getGroupAccess()}};
    };

    function initializeVisibilityEditor(runtime, element) {
        return new VisibilityEditorView(runtime, element);
    }

    // XBlock initialization functions must be global
    window.VisibilityEditorInit = initializeVisibilityEditor;
}($));
