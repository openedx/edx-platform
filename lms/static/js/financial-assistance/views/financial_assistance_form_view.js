(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'js/financial-assistance/models/financial_assistance_model',
        'js/student_account/views/FormView',
        'text!../../../templates/financial-assistance/financial_assessment_form.underscore',
        'text!../../../templates/financial-assistance/financial_assessment_submitted.underscore',
        'text!templates/student_account/form_field.underscore',
        'edx-ui-toolkit/js/utils/html-utils',
        'string_utils'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             FinancialAssistanceModel,
             FormView,
             formViewTpl,
             successTpl,
             formFieldTpl,
             HtmlUtils
         ) {
             return FormView.extend({
                 el: '.financial-assistance-wrapper',
                 events: {
                     'click .js-submit-form': 'submitForm'
                 },
                 tpl: formViewTpl,
                 fieldTpl: formFieldTpl,
                 formType: 'financial-assistance',
                 successTpl: successTpl,
                 defaultFormErrorsTitle: gettext('Unable to submit application'),
                 requiredStr: '',
                 submitButton: '.js-submit-form',

                 initialize: function(data) {
                     var context = data.context,
                         fields = context.fields;

                    // Add default option to course array
                     this.addDefaultOption(fields, 0);
                    // Add default option to household income array
                     this.addDefaultOption(fields, 1);

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
                     this.model.set(context.user_details);
                     this.listenTo(this.model, 'error', this.saveError);
                     this.model.on('sync', this.renderSuccess, this);

                    // Build the form
                     this.buildForm(fields);
                 },

                 render: function(html) {
                     var data = _.extend(this.model.toJSON(), this.context, {
                         fields: html || ''
                     });

                     HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.tpl)(data));

                     this.postRender();
                     this.validateCountry();

                     return this;
                 },

                 renderSuccess: function() {
                     HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.successTpl)({
                         course: this.model.get('course'),
                         dashboard_url: this.context.dashboard_url
                     }));

                     $('.js-success-message').focus();
                 },

                 saveError: function(error) {
                    /* jslint maxlen: 500 */
                     var txt = [
                             'An error has occurred. Wait a few minutes and then try to submit the application again.',
                             'If you continue to have issues please contact support.'
                         ],
                         msg = gettext(txt.join(' '));

                     if (error.status === 0) {
                         msg = gettext('An error has occurred. Check your Internet connection and try again.');
                     }

                     this.errors = [HtmlUtils.joinHtml(
                        HtmlUtils.HTML('<li>'), msg, HtmlUtils.HTML('</li>')
                     ).toString()];
                     this.renderErrors(this.defaultFormErrorsTitle, this.errors);
                     this.toggleDisableButton(false);
                 },

                 setExtraData: function(data) {
                     return _.extend(data, this.user_details);
                 },

                 validateCountry: function() {
                     var $countryLabel = $('#user-country-title'),
                         txt = [
                             'Please go to your {link_start}profile page{link_end} ',
                             'and provide your country of residence.'
                         ],
                         msg = window.interpolate_text(
                            // Translators: link_start and link_end denote the html to link back to the profile page.
                            gettext(txt.join('')),
                             {
                                 link_start: HtmlUtils.joinHtml(
                                    HtmlUtils.HTML('<a href="'),
                                    this.context.account_settings_url,
                                    HtmlUtils.HTML('">')
                                 ).toString(),
                                 link_end: '</a>'
                             }
                        );

                     if (!this.model.get('country')) {
                         $countryLabel.addClass('error');
                         this.renderErrors(this.defaultFormErrorsTitle, [HtmlUtils.joinHtml(
                            HtmlUtils.HTML('<li>'),
                            msg,
                            HtmlUtils.HTML('</li>')
                         ).toString()]);
                         this.toggleDisableButton(true);
                     }
                 },

                 addDefaultOption: function(array, index) {
                     if (array[index].options.length > 1) {
                         array[index].options.unshift({
                             name: '- ' + gettext('Choose one') + ' -',
                             value: '',
                             default: true
                         });
                     }
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
