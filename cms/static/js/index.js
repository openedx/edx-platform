define(["domReady", "jquery", "underscore", "js/utils/cancel_on_escape", "js/views/utils/create_course_utils",
    "js/views/utils/view_utils"],
    function (domReady, $, _, CancelOnEscape, CreateCourseUtilsFactory, ViewUtils) {
        var CreateCourseUtils = CreateCourseUtilsFactory({
            name: '.new-course-name',
            org: '.new-course-org',
            number: '.new-course-number',
            run: '.new-course-run',
            save: '.new-course-save',
            errorWrapper: '.wrap-error',
            errorMessage: '#course_creation_error',
            tipError: 'span.tip-error',
            error: '.error',
            allowUnicode: '.allow-unicode-course-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hiding',
            disabled: 'is-disabled',
            error: 'error'
        });

        var saveNewCourse = function (e) {
            e.preventDefault();

            if (CreateCourseUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newCourseForm = $(this).closest('#create-course-form');
            var display_name = $newCourseForm.find('.new-course-name').val();
            var org = $newCourseForm.find('.new-course-org').val();
            var number = $newCourseForm.find('.new-course-number').val();
            var run = $newCourseForm.find('.new-course-run').val();

            course_info = {
                org: org,
                number: number,
                display_name: display_name,
                run: run
            };

            analytics.track('Created a Course', course_info);
            CreateCourseUtils.createCourse(course_info, function (errorMessage) {
                $('.wrap-error').addClass('is-shown');
                $('#course_creation_error').html('<p>' + errorMessage + '</p>');
                $('.new-course-save').addClass('is-disabled');
            });
        };

        var cancelNewCourse = function (e) {
            e.preventDefault();
            $('.new-course-button').removeClass('is-disabled');
            $('.wrapper-create-course').removeClass('is-shown');
            // Clear out existing fields and errors
            _.each(
                ['.new-course-name', '.new-course-org', '.new-course-number', '.new-course-run'],
                function (field) {
                    $(field).val('');
                }
            );
            $('#course_creation_error').html('');
            $('.wrap-error').removeClass('is-shown');
            $('.new-course-save').off('click');
        };

        var addNewCourse = function (e) {
            e.preventDefault();
            $('.new-course-button').addClass('is-disabled');
            $('.new-course-save').addClass('is-disabled');
            var $newCourse = $('.wrapper-create-course').addClass('is-shown');
            var $cancelButton = $newCourse.find('.new-course-cancel');
            var $courseName = $('.new-course-name');
            $courseName.focus().select();
            $('.new-course-save').on('click', saveNewCourse);
            $cancelButton.bind('click', cancelNewCourse);
            CancelOnEscape($cancelButton);

            CreateCourseUtils.configureHandlers();
        };

        var onReady = function () {
            $('.new-course-button').bind('click', addNewCourse);
            $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function () {
                ViewUtils.reload();
            }));
            $('.action-reload').bind('click', ViewUtils.reload);
        };

        domReady(onReady);

        return {
            onReady: onReady
        };
    });
