// eslint-disable-next-line no-undef
define(['js/views/validation',
    'jquery',
    'underscore',
    'gettext',
    'codemirror',
    'js/views/modals/validation_error_modal',
    'edx-ui-toolkit/js/utils/html-utils'],
function(ValidatingView, $, _, gettext, CodeMirror, ValidationErrorModal, HtmlUtils) {
    // eslint-disable-next-line no-var
    var AdvancedView = ValidatingView.extend({
        error_saving: 'error_saving',
        successful_changes: 'successful_changes',
        render_deprecated: false,

        // Model class is CMS.Models.Settings.Advanced
        events: {
            'focus :input': 'focusInput',
            'blur :input': 'blurInput'
        // TODO enable/disable save based on validation (currently enabled whenever there are changes)
        },
        initialize: function() {
            this.template = HtmlUtils.template(
                $('#advanced_entry-tpl').text()
            );
            this.listenTo(this.model, 'invalid', this.handleValidationError);
            this.render();
        },
        render: function() {
        // catch potential outside call before template loaded
            if (!this.template) { return this; }

            // eslint-disable-next-line no-var
            var listEle$ = this.$el.find('.course-advanced-policy-list');
            listEle$.empty();

            // b/c we've deleted all old fields, clear the map and repopulate
            this.fieldToSelectorMap = {};
            this.selectorToField = {};

            // iterate through model and produce key : value editors for each property in model.get
            // eslint-disable-next-line no-var
            var self = this;
            _.each(_.sortBy(_.keys(this.model.attributes), function(key) { return self.model.get(key).display_name; }),
                function(key) {
                    if (self.render_deprecated || !self.model.get(key).deprecated) {
                        HtmlUtils.append(listEle$, self.renderTemplate(key, self.model.get(key)));
                    }
                });

            this.codeMirrors = [];
            // eslint-disable-next-line no-var
            var policyValues = listEle$.find('.json');
            _.each(policyValues, this.attachJSONEditor, this);
            return this;
        },
        attachJSONEditor: function(textarea) {
        // Since we are allowing duplicate keys at the moment, it is possible that we will try to attach
        // JSON Editor to a value that already has one. Therefore only attach if no CodeMirror peer exists.
            if ($(textarea).siblings().hasClass('CodeMirror')) {
                return;
            }

            // eslint-disable-next-line no-var
            var self = this;
            // eslint-disable-next-line no-var
            var oldValue = $(textarea).val();
            // eslint-disable-next-line no-var
            var cm = CodeMirror.fromTextArea(textarea, {
                mode: 'application/json',
                lineNumbers: false,
                lineWrapping: false
            });
            // eslint-disable-next-line no-unused-vars
            cm.on('change', function(instance, changeobj) {
                instance.save();
                // this event's being called even when there's no change :-(
                if (instance.getValue() !== oldValue) {
                    // eslint-disable-next-line no-var
                    var message = gettext('Your changes will not take effect until you save your progress. Take care with key and value formatting, as validation is not implemented.');
                    self.showNotificationBar(message,
                        _.bind(self.saveView, self),
                        _.bind(self.revertView, self));
                }
            });
            // eslint-disable-next-line no-unused-vars
            cm.on('focus', function(mirror) {
                $(textarea).parent().children('label').addClass('is-focused');
            });
            cm.on('blur', function(mirror) {
                $(textarea).parent().children('label').removeClass('is-focused');
                // eslint-disable-next-line no-var
                var key = $(mirror.getWrapperElement()).closest('.field-group').children('.key').attr('id');
                // eslint-disable-next-line no-var
                var stringValue = $.trim(mirror.getValue());
                // update CodeMirror to show the trimmed value.
                mirror.setValue(stringValue);
                /* eslint-disable-next-line no-undef-init, no-var */
                var JSONValue = undefined;
                try {
                    JSONValue = JSON.parse(stringValue);
                } catch (e) {
                    // If it didn't parse, try converting non-arrays/non-objects to a String.
                    // But don't convert single-quote strings, which are most likely errors.
                    // eslint-disable-next-line no-var
                    var firstNonWhite = stringValue.substring(0, 1);
                    if (firstNonWhite !== '{' && firstNonWhite !== '[' && firstNonWhite !== "'") {
                        try {
                            stringValue = '"' + stringValue + '"';
                            JSONValue = JSON.parse(stringValue);
                            mirror.setValue(stringValue);
                        } catch (quotedE) {
                            // TODO: validation error
                            // console.log("Error with JSON, even after converting to String.");
                            // console.log(quotedE);
                            JSONValue = undefined;
                        }
                    }
                }
                if (JSONValue !== undefined) {
                    // eslint-disable-next-line no-var
                    var modelVal = self.model.get(key);
                    modelVal.value = JSONValue;
                    self.model.set(key, modelVal);
                }
            });
            this.codeMirrors.push(cm);
        },
        validateJSON: function() {
            // eslint-disable-next-line no-var
            var jsonValidationErrors = [];
            _.each(this.codeMirrors, function(mirror) {
                // eslint-disable-next-line no-var
                var keyDiv = $(mirror.getWrapperElement()).closest('.field-group').children('.key');
                // eslint-disable-next-line no-var
                var key = keyDiv.attr('id');
                // eslint-disable-next-line no-var
                var displayName = keyDiv.children('.title').text();
                // eslint-disable-next-line no-var
                var stringValue = mirror.getValue();
                try {
                    JSON.parse(stringValue);
                } catch (e) {
                    jsonValidationErrors.push({
                        key: key,
                        message: 'Incorrectly formatted JSON',
                        model: {display_name: displayName}
                    });
                }
            });
            return jsonValidationErrors;
        },
        saveView: function() {
            // eslint-disable-next-line no-var
            var self = this;
            // eslint-disable-next-line no-var
            var jsonValidationErrors = self.validateJSON();
            if (jsonValidationErrors.length) {
                self.showErrorModal(jsonValidationErrors);
                return;
            }
            this.model.save({}, {
                success: function() {
                    // eslint-disable-next-line no-var
                    var title = gettext('Your policy changes have been saved.');
                    // eslint-disable-next-line no-var
                    var message = gettext('No validation is performed on policy keys or value pairs. If you are having difficulties, check your formatting.'); // eslint-disable-line max-len
                    self.render();
                    self.showSavedBar(title, message);
                    // eslint-disable-next-line no-undef
                    analytics.track('Saved Advanced Settings', {
                        /* eslint-disable-next-line camelcase, no-undef */
                        course: course_location_analytics
                    });
                },
                silent: true,
                // eslint-disable-next-line no-unused-vars
                error: function(model, response, options) {
                    // eslint-disable-next-line no-var
                    var jsonResponse;

                    /* Check that the server came back with a bad request error */
                    if (response.status === 400) {
                        jsonResponse = $.parseJSON(response.responseText);
                        self.showErrorModal(jsonResponse);
                    }
                }
            });
        },
        showErrorModal: function(content) {
            /* initialize and show validation error modal */
            // eslint-disable-next-line no-var
            var self, errModal;
            self = this;
            errModal = new ValidationErrorModal();
            errModal.setContent(content);
            errModal.setResetCallback(function() { self.revertView(); });
            errModal.show();
        },
        revertView: function() {
            // eslint-disable-next-line no-var
            var self = this;
            this.model.fetch({
                success: function() { self.render(); },
                reset: true
            });
        },
        renderTemplate: function(key, model) {
            // eslint-disable-next-line no-var
            var newKeyId = _.uniqueId('policy_key_'),
                newEle = this.template({
                    key: key,
                    display_name: model.display_name,
                    help: model.help,
                    value: JSON.stringify(model.value, null, 4),
                    deprecated: model.deprecated,
                    keyUniqueId: newKeyId,
                    valueUniqueId: _.uniqueId('policy_value_'),
                    hidden: model.hidden
                });

            this.fieldToSelectorMap[key] = newKeyId;
            this.selectorToField[newKeyId] = key;
            return newEle;
        },
        focusInput: function(event) {
            $(event.target).prev().addClass('is-focused');
        },
        blurInput: function(event) {
            $(event.target).prev().removeClass('is-focused');
        }
    });

    return AdvancedView;
});
