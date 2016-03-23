;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'js/financial-assistance/models/financial_assistance_model',
            'js/student_account/views/FormView',
            'text!../../../templates/financial-assistance/financial_assessment_form.underscore',
            'text!../../../templates/financial-assistance/financial_assessment_submitted.underscore',
            'text!templates/student_account/form_field.underscore'
         ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             FinancialAssistanceModel,
             FormView,
             formViewTpl,
             successTpl,
             formFieldTpl
         ) {
            return FormView.extend({
                el: '.financial-assistance-wrapper',
                events: {
                    'click .js-submit-form': 'submitForm'
                },
                tpl: formViewTpl,
                fieldTpl: formFieldTpl,
                formType: 'financial-assistance',
                requiredStr: '',
                submitButton: '.js-submit-form',

                initialize: function(data) {
                    var context = data.context,
                        fields = context.fields;

                    // Add default option to array
                    if ( fields[0].options.length > 1 ) {
                        fields[0].options.unshift({
                            name: '- ' + gettext('Choose one') + ' -',
                            value: '',
                            default: true
                        });
                    }

                    // Set non-form data needed to render the View
                    this.context = {
                        dashboard_url: context.dashboard_url,
                        header_text: context.header_text,
                        platform_name: context.platform_name,
                        student_faq_url: context.student_faq_url,
                        account_settings_url: context.account_settings_url
                    };

                    // Make the value accessible to this View
                    this.user_details = context.user_details;

                    // Initialize the model and set user details
                    this.model = new FinancialAssistanceModel({
                        url: context.submit_url
                    });
                    this.model.set( context.user_details );
                    this.listenTo( this.model, 'error', this.saveError );
                    this.model.on('sync', this.renderSuccess, this);

                    // Build the form
                    this.buildForm( fields );
                },

                render: function(html) {
                    var data = _.extend( this.model.toJSON(), this.context, {
                        fieldsHtml: html || '',
                        HtmlUtils: HtmlUtils
                    });

                    HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.tpl)(data));

                    this.postRender();
                    this.validateCountry();

                    return this;
                },

                renderSuccess: function() {
                    HtmlUtils.setHtml(this.$el, HtmlUtils.template(successTpl)({
                        course: this.model.get('course'),
                        dashboard_url: this.context.dashboard_url
                    }));

                    $('.js-success-message').focus();
                },

                saveError: function(error) {
                    var msg = gettext(
                        'An error has occurred. Wait a few minutes and then try to submit the application again. If you continue to have issues please contact support.' // jshint ignore:line
                    );

                    if (error.status === 0) {
                        msg = gettext('An error has occurred. Check your Internet connection and try again.');
                    }

                    this.errors = [HtmlUtils.joinHtml('<li>', msg, '</li>')];
                    this.setErrors();
                    this.element.hide( this.$resetSuccess );
                    this.toggleDisableButton(false);
                },

                setExtraData: function(data) {
                    return _.extend(data, this.user_details);
                },

                validateCountry: function() {
                    var $submissionContainer = $('.submission-error'),
                        $errorMessageContainer = $submissionContainer.find('.message-copy'),
                        $countryLabel = $('#user-country-title'),
                        msg = HtmlUtils.interpolateHtml(
                            // Translators: link_start and link_end
                            // denote the html to link back to the
                            // profile page.
                            gettext('Please go to your {link_start}profile page{link_end} and provide your country of residence.'), // jshint ignore:line
                            {
                                link_start: HtmlUtils.joinHtml('<a href="', this.context.account_settings_url, '">'),
                                link_end: HtmlUtils.HTML('</a>')
                            }
                        );

                    if( !this.model.get('country') ){
                        $countryLabel.addClass('error');
                        HtmlUtils.append($errorMessageContainer, HtmlUtils.joinHtml(
                            HtmlUtils.HTML("<li>"),
                            msg,
                            HtmlUtils.HTML("</li>")
                        ));
                        this.toggleDisableButton(true);
                        $submissionContainer.removeClass('hidden');
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
