// eslint-disable-next-line no-undef
define(['domReady', 'jquery', 'underscore', 'js/views/utils/create_course_utils',
    'common/js/components/utils/view_utils', 'edx-ui-toolkit/js/utils/html-utils'],
function(domReady, $, _, CreateCourseUtilsFactory, ViewUtils, HtmlUtils) {
    'use strict';

    // eslint-disable-next-line no-var
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

    // eslint-disable-next-line no-var
    var saveRerunCourse = function(e) {
        // eslint-disable-next-line no-var
        var courseInfo;
        e.preventDefault();

        if (CreateCourseUtils.hasInvalidRequiredFields()) {
            return;
        }

        // eslint-disable-next-line no-var
        var $newCourseForm = $(this).closest('#rerun-course-form');
        /* eslint-disable-next-line camelcase, no-var */
        var display_name = $newCourseForm.find('.rerun-course-name').val();
        // eslint-disable-next-line no-var
        var org = $newCourseForm.find('.rerun-course-org').val();
        // eslint-disable-next-line no-var
        var number = $newCourseForm.find('.rerun-course-number').val();
        // eslint-disable-next-line no-var
        var run = $newCourseForm.find('.rerun-course-run').val();

        courseInfo = {
            /* eslint-disable-next-line camelcase, no-undef */
            source_course_key: source_course_key,
            org: org,
            number: number,
            // eslint-disable-next-line camelcase
            display_name: display_name,
            run: run
        };

        analytics.track('Reran a Course', courseInfo); // eslint-disable-line no-undef
        CreateCourseUtils.create(courseInfo, function(errorMessage) {
            $('.wrapper-error').addClass('is-shown').removeClass('is-hidden');
            $('#course_rerun_error').html(HtmlUtils.joinHtml(HtmlUtils.HTML('<p>'), errorMessage, HtmlUtils.HTML('</p>')).toString()); // eslint-disable-line max-len
            $('.rerun-course-save').addClass('is-disabled').attr('aria-disabled', true)
                .removeClass('is-processing')
                .text(gettext('Create Re-run'));
            $('.action-cancel').removeClass('is-hidden');
        });

        // Go into creating re-run state
        $('.rerun-course-save').addClass('is-disabled').attr('aria-disabled', true)
            .addClass('is-processing')
            .html(HtmlUtils.joinHtml(HtmlUtils.HTML('<span class="icon fa fa-refresh fa-spin" aria-hidden="true"></span>'), gettext('Processing Re-run Request')).toString()); // eslint-disable-line max-len
        $('.action-cancel').addClass('is-hidden');
    };

    // eslint-disable-next-line no-var
    var cancelRerunCourse = function(e) {
        e.preventDefault();
        // Clear out existing fields and errors
        $('.rerun-course-run').val('');
        $('#course_rerun_error').html('');
        $('wrapper-error').removeClass('is-shown').addClass('is-hidden');
        $('.rerun-course-save').off('click');
        ViewUtils.redirect('/course/');
    };

    // eslint-disable-next-line no-var
    var onReady = function() {
        // eslint-disable-next-line no-var
        var $cancelButton = $('.rerun-course-cancel');
        // eslint-disable-next-line no-var
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
