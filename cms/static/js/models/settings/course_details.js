define(['backbone', 'underscore', 'gettext', 'js/models/validation_helpers', 'js/utils/date_utils',
    'edx-ui-toolkit/js/utils/string-utils'
],
function(Backbone, _, gettext, ValidationHelpers, DateUtils, StringUtils) {
    'use strict';

    var CourseDetails = Backbone.Model.extend({
        defaults: {
            org: '',
            course_id: '',
            run: '',
            language: '',
            start_date: null, // maps to 'start'
            end_date: null, // maps to 'end'
            certificates_display_behavior: '',
            certificate_available_date: null,
            enrollment_start: null,
            enrollment_end: null,
            syllabus: null,
            title: '',
            subtitle: '',
            duration: '',
            description: '',
            short_description: '',
            overview: '',
            intro_video: null,
            effort: null, // an int or null,
            license: null,
            course_image_name: '', // the filename
            course_image_asset_path: '', // the full URL (/c4x/org/course/num/asset/filename)
            banner_image_name: '',
            banner_image_asset_path: '',
            video_thumbnail_image_name: '',
            video_thumbnail_image_asset_path: '',
            pre_requisite_courses: [],
            entrance_exam_enabled: '',
            entrance_exam_minimum_score_pct: '50',
            learning_info: [],
            instructor_info: {},
            self_paced: null
        },

        validate: function(newattrs) {
        // Returns either nothing (no return call) so that validate works or an object of {field: errorstring} pairs
        // A bit funny in that the video key validation is asynchronous; so, it won't stop the validation.
            var errors = {};
            const CERTIFICATES_DISPLAY_BEHAVIOR_OPTIONS = {
                END: 'end',
                END_WITH_DATE: 'end_with_date',
                EARLY_NO_INFO: 'early_no_info'
            };

            newattrs = DateUtils.convertDateStringsToObjects(
                newattrs,
                ['start_date', 'end_date', 'certificate_available_date', 'enrollment_start', 'enrollment_end']
            );

            if (newattrs.start_date === null) {
                errors.start_date = gettext('The course must have an assigned start date.');
            }

            if (newattrs.start_date && newattrs.end_date && newattrs.start_date >= newattrs.end_date) {
                errors.end_date = gettext('The course end date must be later than the course start date.');
            }
            if (newattrs.start_date && newattrs.enrollment_start
                  && newattrs.start_date < newattrs.enrollment_start) {
                errors.enrollment_start = gettext(
                    'The course start date must be later than the enrollment start date.'
                );
            }
            if (newattrs.enrollment_start && newattrs.enrollment_end
                  && newattrs.enrollment_start >= newattrs.enrollment_end) {
                errors.enrollment_end = gettext(
                    'The enrollment start date cannot be after the enrollment end date.'
                );
            }
            if (newattrs.end_date && newattrs.enrollment_end && newattrs.end_date < newattrs.enrollment_end) {
                errors.enrollment_end = gettext('The enrollment end date cannot be after the course end date.');
            }
            if (this.showCertificateAvailableDate && newattrs.end_date && newattrs.certificate_available_date
                    && newattrs.certificate_available_date < newattrs.end_date) {
                errors.certificate_available_date = gettext(
                    'The certificate available date must be later than the course end date.'
                );
            }

            if (
                newattrs.certificates_display_behavior
                    && !(Object.values(CERTIFICATES_DISPLAY_BEHAVIOR_OPTIONS).includes(newattrs.certificates_display_behavior))
            ) {
                errors.certificates_display_behavior = StringUtils.interpolate(
                    gettext(
                        'The certificate display behavior must be one of: {behavior_options}'
                    ),
                    {
                        behavior_options: Object.values(CERTIFICATES_DISPLAY_BEHAVIOR_OPTIONS).join(', ')
                    }
                );
            }

            // Throw error if there's a value for certificate_available_date
            if (
                (newattrs.certificate_available_date && newattrs.certificates_display_behavior != CERTIFICATES_DISPLAY_BEHAVIOR_OPTIONS.END_WITH_DATE)
                    || (!newattrs.certificate_available_date && newattrs.certificates_display_behavior == CERTIFICATES_DISPLAY_BEHAVIOR_OPTIONS.END_WITH_DATE)
            ) {
                errors.certificates_display_behavior = StringUtils.interpolate(
                    gettext(
                        'The certificates display behavior must be {valid_option} if certificate available date is set.'
                    ),
                    {
                        valid_option: CERTIFICATES_DISPLAY_BEHAVIOR_OPTIONS.END_WITH_DATE
                    }
                );
            }

            if (newattrs.intro_video && newattrs.intro_video !== this.get('intro_video')) {
                if (this._videokey_illegal_chars.exec(newattrs.intro_video)) {
                    errors.intro_video = gettext('Key should only contain letters, numbers, _, or -');
                }
            // TODO check if key points to a real video using google's youtube api
            }
            if (_.has(newattrs, 'entrance_exam_minimum_score_pct')) {
                var range = {
                    min: 1,
                    max: 100
                };
                if (!ValidationHelpers.validateIntegerRange(newattrs.entrance_exam_minimum_score_pct, range)) {
                    errors.entrance_exam_minimum_score_pct = StringUtils.interpolate(gettext(
                        'Please enter an integer between %(min)s and %(max)s.'
                    ), range, true);
                }
            }
            if (!_.isEmpty(errors)) { return errors; }
        // NOTE don't return empty errors as that will be interpreted as an error state
        },

        _videokey_illegal_chars: /[^a-zA-Z0-9_-]/g,

        set_videosource: function(newsource) {
        // newsource either is <video youtube="speed:key, *"/> or just the "speed:key, *" string
        // returns the videosource for the preview which iss the key whose speed is closest to 1
            if (_.isEmpty(newsource)
                  && !_.isEmpty(this.get('intro_video'))) {
                this.set({intro_video: null}, {validate: true});
            } else {
                // TODO remove all whitespace w/in string
                if (this.get('intro_video') !== newsource) { this.set('intro_video', newsource, {validate: true}); }
            }

            return this.videosourceSample();
        },

        videosourceSample: function() {
            if (this.has('intro_video')) { return '//www.youtube.com/embed/' + this.get('intro_video'); } else { return ''; }
        },

        // Whether or not the course pacing can be toggled. If the course
        // has already started, returns false; otherwise, returns true.
        canTogglePace: function() {
            return new Date() <= new Date(this.get('start_date'));
        }
    });

    return CourseDetails;
}); // end define()
