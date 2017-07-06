;(function(define) {
    'use strict';

    define(['jquery', 'common/js/components/utils/view_utils'],
        function($, ViewUtils) {
            return function(options) {

                var $selectElement = $('.action-preview-select'),
                    $userNameElement = $('.action-preview-username'),
                    $userNameContainer = $('.action-preview-username-container');

                if (options.disableStudentAccess) {
                    $selectElement.attr('disabled', true);
                    $selectElement.attr('title', gettext('Course is not yet visible to students.'));
                }

                if (options.specificStudentSelected) {
                    $userNameContainer.css('display', 'inline-block');
                    $userNameElement.val(options.masqueradeUsername);
                }

                $selectElement.change(function() {
                    var selectedOption;
                    if ($selectElement.attr('disabled')) {
                        return alert(gettext('You cannot view the course as a student or beta tester before the course release date.'));  // jshint ignore:line
                    }
                    selectedOption = $selectElement.find('option:selected');
                    if (selectedOption.val() === 'specific student') {
                        $userNameContainer.css('display', 'inline-block');
                    } else {
                        $userNameContainer.hide();
                        masquerade(selectedOption);
                    }
                });

                $userNameElement.keypress(function(event) {
                    if (event.keyCode === 13) {
                        // Avoid submitting the form on enter, since the submit action isn't implemented.
                        // Instead, blur the element to trigger a change event in case the value was edited,
                        // which in turn will trigger an AJAX request to update the masquerading data.
                        $userNameElement.blur();
                        return false;
                    }
                    return true;
                });

                $userNameElement.change(function() {
                    masquerade($selectElement.find('option:selected'));
                });

                function masquerade(selectedOption) {
                    var data = {
                        role: selectedOption.val() === 'staff' ? 'staff' : 'student',
                        user_partition_id: options.cohortedUserPartitionId,
                        group_id: selectedOption.data('group-id'),
                        user_name: selectedOption.val() === 'specific student' ? $userNameElement.val() : null
                    };
                    $.ajax({
                        url: '/courses/' + options.courseId + '/masquerade',
                        type: 'POST',
                        dataType: 'json',
                        contentType: 'application/json',
                        data: JSON.stringify(data),
                        success: function(result) {
                            if (result.success) {
                                ViewUtils.reload();
                            } else {
                                alert(result.error);
                            }
                        },
                        error: function() {
                            alert('Error: cannot connect to server');
                        }
                    });
                }
            };
        });
}).call(this, define || RequireJS.define);
