/**
 * Client-side logic to support XBlock authoring.
 */
(function($) {
    'use strict';

    function VisibilityEditorView(runtime, element) {
        var inputVal, deselectAllOtherPartitions;

        this.getGroupAccess = function() {
            var groupAccess = {},
                checkboxValues,
                partitionId,
                groupId;

            if (element.find('.visibility-all').prop('checked')) {
                return {};
            }

            // user partitions (user is allowed to select more than one)
            element.find(
                '.partition-group-visibility input:checked'
            ).each(function(index, input) {
                checkboxValues = $(input).val().split('-');
                partitionId = parseInt(checkboxValues[0], 10);
                groupId = parseInt(checkboxValues[1], 10);

                if (groupAccess.hasOwnProperty(partitionId)) {
                    groupAccess[partitionId].push(groupId);
                } else {
                    groupAccess[partitionId] = [groupId];
                }
            });

            return groupAccess;
        };

        deselectAllOtherPartitions = function(selectedPartition) {
            element.find('.visibility-all input').prop('checked', false);
            element.find('.visibility-specific-partition').each(function(index, item) {
                if (!$(item).hasClass('visibility-specific-partition-' + selectedPartition)) {
                    $(item).find('input').prop('checked', false);
                }
            });
            element.find('.partition-group-visibility').each(function(index, item) {
                if (!$(item).hasClass('partition-group-visibility-' + selectedPartition)) {
                    $(item).find('input').prop('checked', false);
                }
            });
        };

        // User has selected "All Students and Staff".
        element.find('.visibility-all input').change(function() {
            // Deselect all partition groups.
            element.find('.partition-group-visibility input').prop('checked', false);
        });

        // User has selected a particular user partition.
        element.find('.visibility-specific-partition input').change(function(event) {
            // Deselect all other partitions and their groups, as well as "All Students and Staff".
            inputVal = $(event.target).val();
            deselectAllOtherPartitions(inputVal);
        });

        // User has selected a particular group.
        element.find('.partition-group-visibility input').change(function(event) {
            // Deselect all other partitions and their groups, as well as "All Students and Staff".
            inputVal = parseInt($(event.target).val().split('-')[0], 10);
            deselectAllOtherPartitions(inputVal);
            // Select the parent user partition.
            element.find('.visibility-specific-partition-' + inputVal + ' input').prop('checked', true);
        });
    }

    VisibilityEditorView.prototype.collectFieldData = function collectFieldData() {
        return {
            metadata: {
                'group_access': this.getGroupAccess()
            }
        };
    };

    function initializeVisibilityEditor(runtime, element) {
        return new VisibilityEditorView(runtime, element);
    }

    // XBlock initialization functions must be global
    window.VisibilityEditorInit = initializeVisibilityEditor;
})($);
