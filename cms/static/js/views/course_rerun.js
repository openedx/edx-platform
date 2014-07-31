require(["domReady", "jquery", "underscore", "js/utils/cancel_on_escape"],
    function (domReady, $, _, CancelOnEscape) {

        var saveRerunCourse = function (e) {
            e.preventDefault();
            alert('saving rerun');
            // One final check for empty values
            var errors = _.reduce(
                ['.rerun-course-name', '.rerun-course-org', '.rerun-course-number', '.rerun-course-run'],
                function (acc, ele) {
                    var $ele = $(ele);
                    var error = validateRequiredField($ele.val());
                    setNewCourseFieldInErr($ele.parent('li'), error);
                    return error ? true : acc;
                },
                false
            );

            if (errors) {
                return;
            }

            var $newCourseForm = $(this).closest('#rerun-course-form');
            var display_name = $newCourseForm.find('.rerun-course-name').val();
            var org = $newCourseForm.find('.rerun-course-org').val();
            var number = $newCourseForm.find('.rerun-course-number').val();
            var run = $newCourseForm.find('.rerun-course-run').val();

            analytics.track('Reran a Course', {
                'source_course_key': source_course_key,
                'org': org,
                'number': number,
                'display_name': display_name,
                'run': run
            });
            $.postJSON('/course/', {
                    'source_course_key': source_course_key,
                    'org': org,
                    'number': number,
                    'display_name': display_name,
                    'run': run
                },
                function (data) {
                    if (data.url !== undefined) {
                        window.location = data.url;
                    } else if (data.ErrMsg !== undefined) {
                        $('.wrapper-error').addClass('is-shown').removeClass('is-hidden');
                        $('#course_rerun_error').html('<p>' + data.ErrMsg + '</p>');
                        $('.rerun-course-save').addClass('is-disabled');
                    }
                }
            );
            // Go into creating re-run state
            $('.rerun-course-save').addClass('is-disabled').addClass('is-processing').html(
                gettext('Processing Re-run Request')
            );
            $('.action-cancel').addClass('is-hidden')
        };

        var cancelRerunCourse = function (e) {
            e.preventDefault();
            // Clear out existing fields and errors
            _.each(
                ['.rerun-course-name', '.rerun-course-org', '.rerun-course-number', '.rerun-course-run'],
                function (field) {
                    $(field).val('');
                }
            );
            $('#course_rerun_error').html('');
            $('wrapper-error').removeClass('is-shown').addClass('is-hidden');
            $('.rerun-course-save').off('click');
            window.location.href = '/course/'
        };

        var validateRequiredField = function (msg) {
            return msg.length === 0 ? gettext('Required field.') : '';
        };

        var setNewCourseFieldInErr = function (el, msg) {
            if(msg) {
                el.addClass('error');
                el.children('span.tip-error').addClass('is-shown').removeClass('is-hidden').text(msg);
                $('.rerun-course-save').addClass('is-disabled');
            }
            else {
                el.removeClass('error');
                el.children('span.tip-error').addClass('is-hidden').removeClass('is-shown');
                // One "error" div is always present, but hidden or shown
                if($('.error').length === 1) {
                    $('.rerun-course-save').removeClass('is-disabled');
                }
            }
        };

        domReady(function () {
            var $cancelButton = $('.rerun-course-cancel');
            var $courseName = $('.rerun-course-name');
            $courseName.focus().select();
            $('.rerun-course-save').on('click', saveRerunCourse)
            $cancelButton.bind('click', cancelRerunCourse)
            CancelOnEscape($cancelButton)

            // Check that a course (org, number, run) doesn't use any special characters
            var validateCourseItemEncoding = function (item) {
                var required = validateRequiredField(item);
                if (required) {
                    return required;
                }
                if ($('.allow-unicode-course-id').val() === 'True'){
                    if (/\s/g.test(item)) {
                        return gettext('Please do not use any spaces in this field.');
                    }
                }
                else{
                   if (item !== encodeURIComponent(item)) {
                       return gettext('Please do not use any spaces or special characters in this field.');
                   }
                }
                return '';
            };

            // Ensure that org/course_num/run < 65 chars.
            var validateTotalCourseItemsLength = function () {
                var totalLength = _.reduce(
                    ['.rerun-course-org', '.rerun-course-number', '.rerun-course-run'],
                    function (sum, ele) {
                        return sum + $(ele).val().length;
                    }, 0
                );
                if (totalLength > 65) {
                    $('.wrap-error').addClass('is-shown');
                    $('#course_creation_error').html('<p>' + gettext('The combined length of the organization, course number, and course run fields cannot be more than 65 characters.') + '</p>');
                    $('.rerun-course-save').addClass('is-disabled');
                }
                else {
                    $('.wrap-error').removeClass('is-shown');
                }
            };

            // Handle validation asynchronously
            _.each(
                ['.rerun-course-org', '.rerun-course-number', '.rerun-course-run'],
                function (ele) {
                    var $ele = $(ele);
                    $ele.on('keyup', function (event) {
                        // Don't bother showing "required field" error when
                        // the user tabs into a new field; this is distracting
                        // and unnecessary
                        if (event.keyCode === 9) {
                            return;
                        }
                        var error = validateCourseItemEncoding($ele.val());
                        setNewCourseFieldInErr($ele.parent('li'), error);
                        validateTotalCourseItemsLength();
                    });
                }
            );
            var $name = $('.rerun-course-name');
            $name.on('keyup', function () {
                var error = validateRequiredField($name.val());
                setNewCourseFieldInErr($name.parent('li'), error);
                validateTotalCourseItemsLength();
            });
        });
    });