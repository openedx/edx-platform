define(
    ['jquery', 'underscore', 'backbone', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/views/course_video_settings', 'common/js/spec_helpers/template_helpers'],
    function($, _, Backbone, AjaxHelpers, CourseVideoSettingsView, TemplateHelpers) {
        'use strict';
        describe('CourseVideoSettingsView', function() {
            var $courseVideoSettingsEl,
                courseVideoSettingsView,
                renderCourseVideoSettingsView,
                destroyCourseVideoSettingsView,
                verifyPreferanceErrorState,
                transcriptPreferencesUrl = '/transcript_preferences/course-v1:edX+DemoX+Demo_Course',
                activeTranscriptPreferences = {
                    provider: 'Cielo24',
                    cielo24_fidelity: 'PROFESSIONAL',
                    cielo24_turnaround: 'PRIORITY',
                    three_play_turnaround: '',
                    preferred_languages: ['fr', 'en'],
                    modified: '2017-08-27T12:28:17.421260Z'
                },
                transcriptionPlans = {
                    '3PlayMedia': {
                        languages: {
                            fr: 'French',
                            en: 'English'
                        },
                        turnaround: {
                            default: '4-Day/Default',
                            same_day_service: 'Same Day',
                            rush_service: '24-hour/Rush',
                            extended_service: '10-Day/Extended',
                            expedited_service: '2-Day/Expedited'
                        },
                        display_name: '3PlayMedia'
                    },
                    Cielo24: {
                        turnaround: {
                            PRIORITY: 'Priority, 24h',
                            STANDARD: 'Standard, 48h'
                        },
                        fidelity: {
                            PROFESSIONAL: {
                                languages: {
                                    ru: 'Russian',
                                    fr: 'French',
                                    en: 'English'
                                },
                                display_name: 'Professional, 99% Accuracy'
                            },
                            PREMIUM: {
                                languages: {
                                    en: 'English'
                                },
                                display_name: 'Premium, 95% Accuracy'
                            },
                            MECHANICAL: {
                                languages: {
                                    fr: 'French',
                                    en: 'English',
                                    nl: 'Dutch'
                                },
                                display_name: 'Mechanical, 75% Accuracy'
                            }
                        },
                        display_name: 'Cielo24'
                    }
                };

            renderCourseVideoSettingsView = function(activeTranscriptPreferencesData, transcriptionPlansData) {
                courseVideoSettingsView = new CourseVideoSettingsView({
                    activeTranscriptPreferences: activeTranscriptPreferencesData || null,
                    videoTranscriptSettings: {
                        transcript_preferences_handler_url: transcriptPreferencesUrl,
                        transcription_plans: transcriptionPlansData || null
                    }
                });
                $courseVideoSettingsEl = courseVideoSettingsView.render().$el;
            };

            destroyCourseVideoSettingsView = function() {
                if (courseVideoSettingsView) {
                    courseVideoSettingsView.closeCourseVideoSettings();
                    courseVideoSettingsView = null;
                }
            };

            verifyPreferanceErrorState = function($preferanceContainerEl, hasError) {
                var $errorIconHtml = hasError ? '<span class="icon fa fa-info-circle" aria-hidden="true"></span>' : '',
                    requiredText = hasError ? 'Required' : '';
                expect($preferanceContainerEl.hasClass('error')).toEqual(hasError);
                expect($preferanceContainerEl.find('.error-icon').html()).toEqual($errorIconHtml);
                expect($preferanceContainerEl.find('.error-info').html()).toEqual(requiredText);
            };

            beforeEach(function() {
                setFixtures(
                    '<div class="video-transcript-settings-wrapper"></div>' +
                    '<button class="button course-video-settings-button"></button>'
                );
                TemplateHelpers.installTemplate('course-video-settings');
                renderCourseVideoSettingsView(activeTranscriptPreferences, transcriptionPlans);
            });

            afterEach(function() {
                destroyCourseVideoSettingsView();
            });

            it('renders as expected', function() {
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).toExist();
            });

            it('closes course video settings pane when close button is clicked', function() {
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).toExist();
                $courseVideoSettingsEl.find('.action-close-course-video-settings').click();
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).not.toExist();
            });

            it('closes course video settings pane when clicked outside course video settings pane', function() {
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).toExist();
                $('body').click();
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).not.toExist();
            });

            it('does not close course video settings pane when clicked inside course video settings pane', function() {
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).toExist();
                $courseVideoSettingsEl.find('.transcript-provider-group').click();
                expect($courseVideoSettingsEl.find('.course-video-settings-container')).toExist();
            });

            it('does not populate transcription plans if transcription plans are not provided', function() {
                // First detroy old referance to the view.
                destroyCourseVideoSettingsView();

                // Create view with empty data.
                renderCourseVideoSettingsView(null, null);

                expect($courseVideoSettingsEl.find('.transcript-provider-group').html()).toEqual('');
                expect($courseVideoSettingsEl.find('#transcript-turnaround').html()).toEqual('');
                expect($courseVideoSettingsEl.find('#transcript-fidelity').html()).toEqual('');
                expect($courseVideoSettingsEl.find('#transcript-language').html()).toEqual('');
            });

            it('populates transcription plans correctly', function() {
                // Only check transcript-provider radio buttons for now, because other preferances are based on either
                // user selection or activeTranscriptPreferences.
                expect($courseVideoSettingsEl.find('.transcript-provider-group').html()).not.toEqual('');
            });

            it('populates active preferances correctly', function() {
                // First check preferance are selected correctly in HTML.
                expect($courseVideoSettingsEl.find('.transcript-provider-group input:checked').val()).toEqual(
                    activeTranscriptPreferences.provider
                );
                expect($courseVideoSettingsEl.find('#transcript-turnaround').val()).toEqual(
                    activeTranscriptPreferences.cielo24_turnaround
                );
                expect($courseVideoSettingsEl.find('#transcript-fidelity').val()).toEqual(
                    activeTranscriptPreferences.cielo24_fidelity
                );
                expect($courseVideoSettingsEl.find('.transcript-language-container').length).toEqual(
                    activeTranscriptPreferences.preferred_languages.length
                );

                // Now check values are assigned correctly.
                expect(courseVideoSettingsView.selectedProvider, activeTranscriptPreferences.provider);
                expect(courseVideoSettingsView.selectedTurnaroundPlan, activeTranscriptPreferences.cielo24_turnaround);
                expect(courseVideoSettingsView.selectedFidelityPlan, activeTranscriptPreferences.cielo24_fidelity);
                expect(courseVideoSettingsView.selectedLanguages, activeTranscriptPreferences.preferred_languages);
            });

            it('saves transcript settings on update settings button click if preferances are selected', function() {
                var requests = AjaxHelpers.requests(this);
                $courseVideoSettingsEl.find('.action-update-course-video-settings').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    transcriptPreferencesUrl,
                    JSON.stringify({
                        provider: activeTranscriptPreferences.provider,
                        cielo24_fidelity: activeTranscriptPreferences.cielo24_fidelity,
                        cielo24_turnaround: activeTranscriptPreferences.cielo24_turnaround,
                        three_play_turnaround: activeTranscriptPreferences.three_play_turnaround,
                        preferred_languages: activeTranscriptPreferences.preferred_languages,
                        global: false
                    })
                );

                // Send successful upload response.
                AjaxHelpers.respondWithJson(requests, {
                    transcript_preferences: activeTranscriptPreferences
                });

                // Verify that success message is shown.
                expect($courseVideoSettingsEl.find('.course-video-settings-message-wrapper.success').html()).toEqual(
                    '<div class="course-video-settings-message">' +
                    '<span class="icon fa fa-check-circle" aria-hidden="true"></span>' +
                    '<span>Settings updated</span>' +
                    '</div>'
                );
            });

            it('shows error message if server sends error', function() {
                var requests = AjaxHelpers.requests(this);
                $courseVideoSettingsEl.find('.action-update-course-video-settings').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    transcriptPreferencesUrl,
                    JSON.stringify({
                        provider: activeTranscriptPreferences.provider,
                        cielo24_fidelity: activeTranscriptPreferences.cielo24_fidelity,
                        cielo24_turnaround: activeTranscriptPreferences.cielo24_turnaround,
                        three_play_turnaround: activeTranscriptPreferences.three_play_turnaround,
                        preferred_languages: activeTranscriptPreferences.preferred_languages,
                        global: false
                    })
                );

                // Send error response.
                AjaxHelpers.respondWithError(requests, 400, {
                    error: 'Error message'
                });

                // Verify that error message is shown.
                expect($courseVideoSettingsEl.find('.course-video-settings-message-wrapper.error').html()).toEqual(
                    '<div class="course-video-settings-message">' +
                    '<span class="icon fa fa-info-circle" aria-hidden="true"></span>' +
                    '<span>Error message</span>' +
                    '</div>'
                );
            });

            it('implies preferences are required if not selected when saving preferances', function() {
                // Reset so that no preferance is selected.
                courseVideoSettingsView.selectedTurnaroundPlan = '';
                courseVideoSettingsView.selectedFidelityPlan = '';
                courseVideoSettingsView.selectedLanguages = [];

                $courseVideoSettingsEl.find('.action-update-course-video-settings').click();

                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-turnaround-wrapper'), true);
                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-fidelity-wrapper'), true);
                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-languages-wrapper'), true);
            });

            it('removes error state on preferances if selected', function() {
                // Provide values for preferances.
                $courseVideoSettingsEl.find('#transcript-turnaround').val('test-value');
                $courseVideoSettingsEl.find('#transcript-fidelity').val('test-value');
                $courseVideoSettingsEl.find('#transcript-language-menu').val('test-value');

                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-turnaround-wrapper'), false);
                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-fidelity-wrapper'), false);
                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-languages-wrapper'), false);
            });

            // TODO: Add more tests like clicking on add language, remove and their scenarios and some other tests
            // like N/A selected, specific provider selected tests, specific preferance selected tests etc.
        });
    }
);
