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
                verifyTranscriptPreferences,
                verifyTranscriptPreferencesView,
                verifyOrganizationCredentialsView,
                verifyOrganizationCredentialField,
                verifyMessage,
                verifyPreferanceErrorState,
                selectPreference,
                verifyProviderList,
                verifyProviderSelectedView,
                resetProvider,
                changeProvider,
                transcriptPreferencesUrl = '/transcript_preferences/course-v1:edX+DemoX+Demo_Course',
                transcriptCredentialsHandlerUrl = '/transcript_credentials/course-v1:edX+DemoX+Demo_Course',
                activeTranscriptPreferences = {
                    provider: 'Cielo24',
                    cielo24_fidelity: 'PROFESSIONAL',
                    cielo24_turnaround: 'PRIORITY',
                    three_play_turnaround: '',
                    video_source_language: 'en',
                    preferred_languages: ['fr', 'en'],
                    modified: '2017-08-27T12:28:17.421260Z'
                },
                transcriptOrganizationCredentials = {
                    Cielo24: true,
                    '3PlayMedia': true
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
                },
                providers = {
                    none: {
                        key: 'none',
                        value: '',
                        displayName: 'N/A'
                    },
                    Cielo24: {
                        key: 'Cielo24',
                        value: 'Cielo24',
                        displayName: 'Cielo24'
                    },
                    '3PlayMedia': {
                        key: '3PlayMedia',
                        value: '3PlayMedia',
                        displayName: '3Play Media'
                    }
                };

            renderCourseVideoSettingsView = function(activeTranscriptPreferencesData, transcriptionPlansData, transcriptOrganizationCredentialsData) {  // eslint-disable-line max-len
                // First destroy old referance to the view if present.
                destroyCourseVideoSettingsView();

                courseVideoSettingsView = new CourseVideoSettingsView({
                    activeTranscriptPreferences: activeTranscriptPreferencesData || null,
                    videoTranscriptSettings: {
                        transcript_preferences_handler_url: transcriptPreferencesUrl,
                        transcript_credentials_handler_url: transcriptCredentialsHandlerUrl,
                        transcription_plans: transcriptionPlansData || null
                    },
                    transcriptOrganizationCredentials: transcriptOrganizationCredentialsData || null
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

            verifyMessage = function(state, message) {
                var icon = state === 'error' ? 'fa-info-circle' : 'fa-check-circle';
                expect($courseVideoSettingsEl.find('.course-video-settings-message-wrapper.' + state).html()).toEqual(
                    '<div class="course-video-settings-message">' +
                    '<span class="icon fa ' + icon + '" aria-hidden="true"></span>' +
                    '<span>' + message + '</span>' +
                    '</div>'
                );
            };

            verifyProviderList = function(selectedProvider) {
                var $transcriptProvidersListEl = $courseVideoSettingsEl.find('.transcript-provider-wrapper .transcript-provider-group');    // eslint-disable-line max-len
                // Check N/A provider is selected.
                expect($transcriptProvidersListEl.find('input[type=radio]:checked').val()).toEqual(selectedProvider.value); // eslint-disable-line max-len
                _.each(providers, function(provider, key) {
                    $transcriptProvidersListEl.find('label[for=transcript-provider-' + key + ']').val(provider.displayName);    // eslint-disable-line max-len
                });
            };

            verifyTranscriptPreferences = function() {
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
                expect(courseVideoSettingsView.selectedTurnaroundPlan, activeTranscriptPreferences.cielo24_turnaround);
                expect(courseVideoSettingsView.selectedFidelityPlan, activeTranscriptPreferences.cielo24_fidelity);
                expect(courseVideoSettingsView.selectedLanguages, activeTranscriptPreferences.preferred_languages);
            };

            verifyProviderSelectedView = function() {
                // Verify provider
                expect(
                    $courseVideoSettingsEl.find('.selected-transcript-provider .title').html()
                ).toEqual(courseVideoSettingsView.selectedProvider);

                expect($courseVideoSettingsEl.find('.selected-transcript-provider .action-change-provider')).toExist();
                expect(
                    $courseVideoSettingsEl.find('.selected-transcript-provider .action-change-provider .sr').html()
                ).toEqual('Press change to change selected transcript provider.');
            };

            verifyTranscriptPreferencesView = function() {
                expect($courseVideoSettingsEl.find('.course-video-transcript-preferances-wrapper')).toExist();
            };

            verifyOrganizationCredentialsView = function() {
                expect($courseVideoSettingsEl.find('.organization-credentials-content')).toExist();
            };

            verifyOrganizationCredentialField = function(fieldName, label) {
                var elementSelector = courseVideoSettingsView.selectedProvider + '-' + fieldName;
                // Verify that correct label is shown.
                expect(
                    $courseVideoSettingsEl.find('.' + elementSelector + '-wrapper label .title').html()
                ).toEqual(label);

                // Verify that credential field is shown.
                expect(
                    $courseVideoSettingsEl.find('.' + elementSelector + '-wrapper .' + elementSelector)
                ).toExist();
            };

            changeProvider = function(selectedProvider) {
                // If Provider Selected view is show, first click on "Change Provider" button to
                // show all list of providers.
                if ($courseVideoSettingsEl.find('.selected-transcript-provider').length) {
                    $courseVideoSettingsEl.find('.selected-transcript-provider .action-change-provider').click();
                }
                $courseVideoSettingsEl.find('#transcript-provider-' + selectedProvider).click();
            };

            resetProvider = function() {
                var requests = AjaxHelpers.requests(this);
                // Set no provider selected
                changeProvider('none');
                $courseVideoSettingsEl.find('.action-update-course-video-settings').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'DELETE',
                    transcriptPreferencesUrl
                );

                // Send successful empty content response.
                AjaxHelpers.respondWithJson(requests, {});
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
                // Create view with empty data.
                renderCourseVideoSettingsView();
                // Checking turnaround is sufficient to check preferences are are shown or not.
                expect($courseVideoSettingsEl.find('.transcript-turnaround-wrapper')).not.toExist();
            });

            it('populates transcription plans correctly', function() {
                // Only check transcript-provider radio buttons for now, because other preferances are based on either
                // user selection or activeTranscriptPreferences.
                expect($courseVideoSettingsEl.find('.transcript-provider-group').html()).not.toEqual('');
            });

            it('populates active preferances correctly', function() {
                // First check preferance are selected correctly in HTML.
                verifyTranscriptPreferences();
            });

            it('shows video source language directly in case of 3Play provider', function() {
                var sourceLanguages,
                    selectedProvider = '3PlayMedia';

                renderCourseVideoSettingsView(null, transcriptionPlans, transcriptOrganizationCredentials);

                // Select provider
                changeProvider(selectedProvider);
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

                renderCourseVideoSettingsView(null, transcriptionPlans, transcriptOrganizationCredentials);

                // Select provider
                changeProvider(selectedProvider);
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

                renderCourseVideoSettingsView(null, transcriptionPlans, transcriptOrganizationCredentials);

                // Select provider
                changeProvider(selectedProvider);
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

                renderCourseVideoSettingsView(null, transcriptionPlans, transcriptOrganizationCredentials);

                // Select provider
                changeProvider(selectedProvider);
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
                verifyMessage('success', 'Settings updated');
            });

            it('removes transcript settings on update settings button click when no provider is selected', function() {
                // Reset to N/A provider
                resetProvider();
                verifyProviderList(providers.none);

                // Verify that success message is shown.
                verifyMessage('success', 'Settings updated');
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
                verifyMessage('error', 'Error message');
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

            it('shows provider selected view if active provider is present', function() {
                var $selectedProviderContainerEl = $courseVideoSettingsEl.find('.transcript-provider-wrapper .selected-transcript-provider');   // eslint-disable-line max-len
                expect($selectedProviderContainerEl.find('span').html()).toEqual(courseVideoSettingsView.selectedProvider); // eslint-disable-line max-len
                expect($selectedProviderContainerEl.find('button.action-change-provider')).toExist();
                // Verify provider list view is not shown.
                expect($courseVideoSettingsEl.find('.transcript-provider-wrapper .transcript-provider-group')).not.toExist();   // eslint-disable-line max-len
            });

            it('does not show transcript preferences or organization credentials if N/A provider is saved', function() {
                renderCourseVideoSettingsView(null, transcriptionPlans);

                // Check N/A provider
                resetProvider();
                verifyProviderList(providers.none);

                // Verify selected provider view is not shown.
                expect($courseVideoSettingsEl.find('.transcript-provider-wrapper .selected-transcript-provider')).not.toExist();    // eslint-disable-line max-len
            });

            it('does not show transcript preferences or organization credentials if N/A provider is checked', function() {  // eslint-disable-line max-len
                renderCourseVideoSettingsView(null, transcriptionPlans);

                // Check N/A provider
                resetProvider();
                verifyProviderList(providers.none);

                // Verify selected provider view is not shown.
                expect($courseVideoSettingsEl.find('.transcript-provider-wrapper .selected-transcript-provider')).not.toExist();    // eslint-disable-line max-len
                // Verify transcript preferences are not shown.
                expect($courseVideoSettingsEl.find('.course-video-transcript-preferances-wrapper')).not.toExist();
                // Verify org credentials are not shown.
                expect($courseVideoSettingsEl.find('.organization-credentials-content')).not.toExist();
            });

            it('shows organization credentials when organization credentials for selected provider are not present', function() {   // eslint-disable-line max-len
                renderCourseVideoSettingsView(null, transcriptionPlans);

                // Check Cielo24 provider
                changeProvider(providers.Cielo24.key);
                verifyProviderList(providers.Cielo24);

                // Verify organization credentials are shown.
                verifyOrganizationCredentialsView();

                // Verify transcript preferences are not shown.
                expect($courseVideoSettingsEl.find('.course-video-transcript-preferances-wrapper')).not.toExist();
            });

            it('shows transcript preferences when organization credentials for selected provider are present', function() { // eslint-disable-line max-len
                renderCourseVideoSettingsView(null, transcriptionPlans, transcriptOrganizationCredentials);

                // Check Cielo24 provider
                changeProvider('Cielo24');
                verifyProviderList(providers.Cielo24);

                // Verify organization credentials are not shown.
                expect($courseVideoSettingsEl.find('.organization-credentials-content')).not.toExist();

                // Verify transcript preferences are shown.
                verifyTranscriptPreferencesView();
            });

            it('shows organization credentials view if clicked on change provider button', function() {
                // Verify organization credentials view is not shown initially.
                expect($courseVideoSettingsEl.find('.organization-credentials-content')).not.toExist();

                verifyProviderSelectedView();
                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Verify organization credentials is now shown.
                verifyOrganizationCredentialsView();
            });

            it('shows api secret input field if selected provider is 3Play Media', function() {
                // Set selected provider to 3Play Media
                changeProvider('3PlayMedia');

                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Verify 3play api secret and api key are present.
                verifyOrganizationCredentialField('api-secret', 'API Secret');
                verifyOrganizationCredentialField('api-key', 'API Key');
            });

            it('does not show api secret input field if selected provider is not 3Play Media', function() {
                verifyProviderSelectedView();
                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Verify 3Play Media api secret is not present.
                expect(
                    $courseVideoSettingsEl.find('.' + courseVideoSettingsView.selectedProvider + '-api-secret')
                ).not.toExist();

                // Verify api key is present.
                verifyOrganizationCredentialField('api-key', 'API Key');
            });

            it('shows warning message when changing organization credentials if present already', function() {
                // Set selectedProvider organization credentials.
                courseVideoSettingsView.transcriptOrganizationCredentials[courseVideoSettingsView.selectedProvider] = true; // eslint-disable-line max-len

                verifyProviderSelectedView();
                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Verify credentials are shown
                verifyOrganizationCredentialsView();
                // Verify warning message is shown.
                expect($courseVideoSettingsEl.find('.transcription-account-details.warning')).toExist();
                // Verify message
                expect($courseVideoSettingsEl.find('.transcription-account-details').html()).toEqual(
                    '<span>By entering the set of credntials below, ' +
                    'you will be overwriting your organization\'s credentials.</span>'
                );
            });

            it('does not show warning message when changing organization credentials if not present already', function() {  // eslint-disable-line max-len
                verifyProviderSelectedView();
                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Verify warning message is not shown.
                expect($courseVideoSettingsEl.find('.transcription-account-details.warning')).not.toExist();
                // Initial detail message is shown instead.
                expect($courseVideoSettingsEl.find('.transcription-account-details').html()).toEqual(
                    '<span>Please enter your organization\'s account information. ' +
                    'Remember that all courses in your organization will use this account.</span>'
                );
            });

            it('shows validation errors if no organization credentials are provided when saving credentials', function() {  // eslint-disable-line max-len
                // Set selected provider to 3Play Media
                changeProvider('3PlayMedia');

                // Click save organization credentials button to save credentials.
                $courseVideoSettingsEl.find('.action-update-org-credentials').click();

                verifyPreferanceErrorState(
                    $courseVideoSettingsEl.find('.' + courseVideoSettingsView.selectedProvider + '-api-key-wrapper'),
                    true
                );

                verifyPreferanceErrorState(
                    $courseVideoSettingsEl.find('.' + courseVideoSettingsView.selectedProvider + '-api-secret-wrapper'),
                    true
                );
            });

            it('saves organization credentials on clicking save credentials button', function() {
                var requests = AjaxHelpers.requests(this);

                verifyProviderSelectedView();
                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Set organization credentials so as to pass validations.
                $courseVideoSettingsEl.find('.' + courseVideoSettingsView.selectedProvider + '-api-key').val('testkey');

                // Click save organization credentials button to save credentials.
                $courseVideoSettingsEl.find('.action-update-org-credentials').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    transcriptCredentialsHandlerUrl,
                    JSON.stringify({
                        provider: activeTranscriptPreferences.provider,
                        global: false
                    })
                );

                // Send empty response.
                AjaxHelpers.respondWithJson(requests, {});

                // Verify that success message is shown.
                verifyMessage(
                    'success',
                    transcriptionPlans[courseVideoSettingsView.selectedProvider].display_name + ' credentials saved'
                );
            });

            it('shows selected provider view afer organization credentials saved', function() {
                var requests = AjaxHelpers.requests(this);
                renderCourseVideoSettingsView(null, transcriptionPlans);

                // Verify selected provider view is not shown.
                expect(
                    $courseVideoSettingsEl.find('.transcript-provider-wrapper .selected-transcript-provider')
                ).not.toExist();

                // Verify provider list view is shown.
                verifyProviderList(providers.none);

                // Check Cielo24 provider
                changeProvider('Cielo24');
                verifyProviderList(providers.Cielo24);

                // Set organization credentials so as to pass validations.
                $courseVideoSettingsEl.find('.' + courseVideoSettingsView.selectedProvider + '-api-key').val('testkey');

                // Click save organization credentials button to save credentials.
                $courseVideoSettingsEl.find('.action-update-org-credentials').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    transcriptCredentialsHandlerUrl,
                    JSON.stringify({
                        provider: activeTranscriptPreferences.provider,
                        global: false
                    })
                );

                // Send empty response.
                AjaxHelpers.respondWithJson(requests, {});

                // Verify that success message is shown.
                verifyMessage(
                    'success',
                    transcriptionPlans[courseVideoSettingsView.selectedProvider].display_name + ' credentials saved'
                );

                // Shows selected provider view after credentials are saved.
                verifyProviderSelectedView();

                // Verify provider list view is not shown.
                expect(
                    $courseVideoSettingsEl.find('.transcript-provider-wrapper .transcript-provider-group')
                ).not.toExist();
            });

            it('shows error message on saving organization credentials if server sends error', function() {
                var requests = AjaxHelpers.requests(this);

                verifyProviderSelectedView();
                // Click change button to render organization credentials view.
                $courseVideoSettingsEl.find('.action-change-provider').click();

                // Set organization credentials so as to pass validations.
                $courseVideoSettingsEl.find('.' + courseVideoSettingsView.selectedProvider + '-api-key').val('testkey');

                // Click save organization credentials button to save credentials.
                $courseVideoSettingsEl.find('.action-update-org-credentials').click();

                AjaxHelpers.expectRequest(
                    requests,
                    'POST',
                    transcriptCredentialsHandlerUrl,
                    JSON.stringify({
                        provider: activeTranscriptPreferences.provider,
                        global: false
                    })
                );

                // Send error response.
                AjaxHelpers.respondWithError(requests, 400, {
                    error: 'Error message'
                });

                // Verify that error message is shown.
                verifyMessage('error', 'Error message');
            });

            // TODO: Add more tests like clicking on add language, remove and their scenarios and some other tests
            // for specific preferance selected tests etc. - See EDUCATOR-1478
        });
    }
);
