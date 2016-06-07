define(["domReady", "jquery", "underscore", "js/views/utils/create_course_utils", "common/js/components/utils/view_utils"],
    function (domReady, $, _, CreateCourseUtilsFactory, ViewUtils) {
        var CreateCourseUtils = new CreateCourseUtilsFactory({
            name: '.rerun-course-name',
            org: '.rerun-course-org',
            number: '.rerun-course-number',
            run: '.rerun-course-run',
            save: '.rerun-course-save',
            errorWrapper: '.wrapper-error',
            errorMessage: '#course_rerun_error',
            tipError: 'span.tip-error',
            error: '.error',
            allowUnicode: '.allow-unicode-course-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hidden',
            disabled: 'is-disabled',
            error: 'error'
        });

        var saveRerunCourse = function (e) {
            e.preventDefault();

            if (CreateCourseUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newCourseForm = $(this).closest('#rerun-course-form');
            var display_name = $newCourseForm.find('.rerun-course-name').val();
            var org = $newCourseForm.find('.rerun-course-org').val();
            var number = $newCourseForm.find('.rerun-course-number').val();
            var run = $newCourseForm.find('.rerun-course-run').val();

            course_info = {
                source_course_key: source_course_key,
                org: org,
                number: number,
                display_name: display_name,
                run: run
            };

            analytics.track('Reran a Course', course_info);
            CreateCourseUtils.create(course_info, function (errorMessage) {
                $('.wrapper-error').addClass('is-shown').removeClass('is-hidden');
                $('#course_rerun_error').html('<p>' + errorMessage + '</p>');
                $('.rerun-course-save').addClass('is-disabled').attr('aria-disabled', true).removeClass('is-processing').html(gettext('Create Re-run'));
                $('.action-cancel').removeClass('is-hidden');
            });

            // Go into creating re-run state
            $('.rerun-course-save').addClass('is-disabled').attr('aria-disabled', true).addClass('is-processing').html(
               '<i class="icon fa fa-refresh fa-spin"></i>' + gettext('Processing Re-run Request')
            );
            $('.action-cancel').addClass('is-hidden');
        };

        var cancelRerunCourse = function (e) {
            e.preventDefault();
            // Clear out existing fields and errors
            $('.rerun-course-run').val('');
            $('#course_rerun_error').html('');
            $('wrapper-error').removeClass('is-shown').addClass('is-hidden');
            $('.rerun-course-save').off('click');
            ViewUtils.redirect('/course/');
        };

        var onReady = function () {
            var $cancelButton = $('.rerun-course-cancel');
            var $courseRun = $('.rerun-course-run');
            $courseRun.focus().select();
            $('.rerun-course-save').on('click', saveRerunCourse);
            $cancelButton.bind('click', cancelRerunCourse);
            $('.cancel-button').bind('click', cancelRerunCourse);

            CreateCourseUtils.configureHandlers();
        };

        domReady(onReady);

        // Return these functions so that they can be tested
        return {
            saveRerunCourse: saveRerunCourse,
            cancelRerunCourse: cancelRerunCourse,
            onReady: onReady
        };
    });
