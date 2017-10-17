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
                selectPreference,
                chooseProvider,
                transcriptPreferencesUrl = '/transcript_preferences/course-v1:edX+DemoX+Demo_Course',
                activeTranscriptPreferences = {
                    provider: 'Cielo24',
                    cielo24_fidelity: 'PROFESSIONAL',
                    cielo24_turnaround: 'PRIORITY',
                    three_play_turnaround: '',
                    video_source_language: 'en',
                    preferred_languages: ['fr', 'en'],
                    modified: '2017-08-27T12:28:17.421260Z'
                },
                transcriptionPlans = {
                    '3PlayMedia': {
                        languages: {
                            fr: 'French',
                            en: 'English',
                            ur: 'Urdu'
                        },
                        turnaround: {
                            default: '4-Day/Default',
                            same_day_service: 'Same Day',
                            rush_service: '24-hour/Rush',
                            extended_service: '10-Day/Extended',
                            expedited_service: '2-Day/Expedited'
                        },
                        translations: {
                            es: ['en'],
                            en: ['en', 'ur']
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

            selectPreference = function(preferenceSelector, preferanceValue) {
                var $preference = $courseVideoSettingsEl.find(preferenceSelector);
                // Select a vlaue for preference.
                $preference.val(preferanceValue);
                // Trigger on change event.
                $preference.change();
            };

            chooseProvider = function(selectedProvider) {
                $courseVideoSettingsEl.find('#transcript-provider-' + selectedProvider).click();
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
                expect($courseVideoSettingsEl.find('.transcript-turnaround').html()).toEqual('');
                expect($courseVideoSettingsEl.find('.transcript-fidelity').html()).toEqual('');
                expect($courseVideoSettingsEl.find('.video-source-language').html()).toEqual('');
                expect($courseVideoSettingsEl.find('.transcript-language-menu').html()).toEqual('');
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
                expect($courseVideoSettingsEl.find('.transcript-turnaround').val()).toEqual(
                    activeTranscriptPreferences.cielo24_turnaround
                );
                expect($courseVideoSettingsEl.find('.transcript-fidelity').val()).toEqual(
                    activeTranscriptPreferences.cielo24_fidelity
                );
                expect($courseVideoSettingsEl.find('.video-source-language').val()).toEqual(
                    activeTranscriptPreferences.video_source_language
                );
                expect($courseVideoSettingsEl.find('.transcript-language-container').length).toEqual(
                    activeTranscriptPreferences.preferred_languages.length
                );

                // Now check values are assigned correctly.
                expect(courseVideoSettingsView.selectedProvider, activeTranscriptPreferences.provider);
                expect(courseVideoSettingsView.selectedTurnaroundPlan, activeTranscriptPreferences.cielo24_turnaround);
                expect(courseVideoSettingsView.selectedFidelityPlan, activeTranscriptPreferences.cielo24_fidelity);
                expect(
                    courseVideoSettingsView.selectedSourceLanguage,
                    activeTranscriptPreferences.video_source_language
                );
                expect(courseVideoSettingsView.selectedLanguages, activeTranscriptPreferences.preferred_languages);
            });

            it('shows video source language directly in case of 3Play provider', function() {
                var sourceLanguages,
                    selectedProvider = '3PlayMedia';

                // Select CIELIO24 provider
                chooseProvider(selectedProvider);
                expect(courseVideoSettingsView.selectedProvider).toEqual(selectedProvider);

                // Verify source langauges menu is shown.
                sourceLanguages = courseVideoSettingsView.getSourceLanguages();
                expect($courseVideoSettingsEl.find('.video-source-language option')).toExist();
                expect($courseVideoSettingsEl.find('.video-source-language option').length).toEqual(
                    _.keys(sourceLanguages).length + 1
                );

                expect(_.keys(transcriptionPlans[selectedProvider].translations)).toEqual(_.keys(sourceLanguages));
            });

            it('shows source language when fidelity is selected', function() {
                var sourceLanguages,
                    selectedProvider = 'Cielo24',
                    selectedFidelity = 'PROFESSIONAL';

                renderCourseVideoSettingsView(null, transcriptionPlans);

                // Select CIELIO24 provider
                chooseProvider(selectedProvider);
                expect(courseVideoSettingsView.selectedProvider).toEqual(selectedProvider);

                // Verify source language is not shown.
                sourceLanguages = courseVideoSettingsView.getSourceLanguages();
                expect($courseVideoSettingsEl.find('.video-source-language option')).not.toExist();
                expect(sourceLanguages).toBeUndefined();

                // Select fidelity
                selectPreference('.transcript-fidelity', selectedFidelity);
                expect(courseVideoSettingsView.selectedFidelityPlan).toEqual(selectedFidelity);

                // Verify source langauges menu is shown.
                sourceLanguages = courseVideoSettingsView.getSourceLanguages();
                expect($courseVideoSettingsEl.find('.video-source-language option')).toExist();
                expect($courseVideoSettingsEl.find('.video-source-language option').length).toEqual(
                    _.keys(sourceLanguages).length + 1
                );

                // Verify getSourceLangaues return a list of langauges.
                expect(sourceLanguages).toBeDefined();
                expect(transcriptionPlans[selectedProvider].fidelity[selectedFidelity].languages).toEqual(
                    sourceLanguages
                );
            });

            it('shows target language when source language is selected', function() {
                var targetLanguages,
                    selectedSourceLanguage = 'en',
                    selectedProvider = 'Cielo24',
                    selectedFidelity = 'PROFESSIONAL';

                // Select CIELIO24 provider
                chooseProvider(selectedProvider);
                expect(courseVideoSettingsView.selectedProvider).toEqual(selectedProvider);

                // Select fidelity
                selectPreference('.transcript-fidelity', selectedFidelity);
                expect(courseVideoSettingsView.selectedFidelityPlan).toEqual(selectedFidelity);

                // Verify target langauges not shown.
                expect($courseVideoSettingsEl.find('.transcript-language-menu:visible option')).not.toExist();

                // Select source language
                selectPreference('.video-source-language', selectedSourceLanguage);
                expect(courseVideoSettingsView.selectedVideoSourceLanguage).toEqual(selectedSourceLanguage);

                // Verify target languages are shown.
                targetLanguages = courseVideoSettingsView.getTargetLanguages();
                expect($courseVideoSettingsEl.find('.transcript-language-menu:visible option')).toExist();
                expect($courseVideoSettingsEl.find('.transcript-language-menu:visible option').length).toEqual(
                    _.keys(targetLanguages).length + 1
                );
            });

            it('shows target language same as selected source language in case of mechanical fidelity', function() {
                var targetLanguages,
                    selectedSourceLanguage = 'en',
                    selectedProvider = 'Cielo24',
                    selectedFidelity = 'MECHANICAL';

                // Select CIELIO24 provider
                chooseProvider(selectedProvider);
                expect(courseVideoSettingsView.selectedProvider).toEqual(selectedProvider);

                // Select fidelity
                selectPreference('.transcript-fidelity', selectedFidelity);
                expect(courseVideoSettingsView.selectedFidelityPlan).toEqual(selectedFidelity);

                // Select source language
                selectPreference('.video-source-language', selectedSourceLanguage);
                expect(courseVideoSettingsView.selectedVideoSourceLanguage).toEqual(selectedSourceLanguage);

                // Verify target languages are shown.
                targetLanguages = courseVideoSettingsView.getTargetLanguages();
                expect($courseVideoSettingsEl.find('.transcript-language-menu:visible option')).toExist();
                expect($courseVideoSettingsEl.find('.transcript-language-menu:visible option').length).toEqual(
                    _.keys(targetLanguages).length + 1
                );

                // Also verify that target language are same as selected source language.
                expect(_.keys(targetLanguages).length).toEqual(1);
                expect(_.keys(targetLanguages)).toEqual([selectedSourceLanguage]);
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
                        video_source_language: activeTranscriptPreferences.video_source_language,
                        global: false
                    })
                );

                // Send successful response.
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

            it('removes transcript settings on update settings button click when no provider is selected', function() {
                var requests = AjaxHelpers.requests(this);

                // Set no provider selected
                courseVideoSettingsView.selectedProvider = null;
                $courseVideoSettingsEl.find('.action-update-course-video-settings').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'DELETE',
                    transcriptPreferencesUrl
                );

                // Send successful empty content response.
                AjaxHelpers.respondWithJson(requests, {});

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
                        video_source_language: activeTranscriptPreferences.video_source_language,
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
                selectPreference('.transcript-turnaround', activeTranscriptPreferences.cielo24_turnaround);
                selectPreference('.transcript-fidelity', activeTranscriptPreferences.cielo24_fidelity);
                selectPreference('.video-source-language', activeTranscriptPreferences.video_source_language);
                selectPreference('.transcript-language-menu', activeTranscriptPreferences.preferred_languages[0]);

                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-turnaround-wrapper'), false);
                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-fidelity-wrapper'), false);
                verifyPreferanceErrorState($courseVideoSettingsEl.find('.transcript-languages-wrapper'), false);
            });

            // TODO: Add more tests like clicking on add language, remove and their scenarios and some other tests
            // like N/A selected, specific provider selected tests, specific preferance selected tests etc.
        });
    }
);
