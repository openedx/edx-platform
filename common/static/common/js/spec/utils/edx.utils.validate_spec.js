(function(define) {
    'use strict';
    define(['jquery', 'common/js/utils/edx.utils.validate'],
        function($, EdxUtilsValidate) {
            describe('EdxUtilsValidate', function() {
                var fixture = null,
                    field = null,
                    result = null,
                    MIN_LENGTH = 2,
                    MAX_LENGTH = 20,
                    VALID_STRING = 'xsy_is_awesome',
                    SHORT_STRING = 'x',
                    LONG_STRING = 'xsy_is_way_too_awesome',
                    EMAIL_ERROR_FRAGMENT = 'formatted',
                    MIN_ERROR_FRAGMENT = 'least',
                    MAX_ERROR_FRAGMENT = 'up to',
                    REQUIRED_ERROR_FRAGMENT = 'Please enter your',
                    CUSTOM_MESSAGE = 'custom message';

                var createFixture = function(type, name, required, minlength, maxlength, value) {
                    setFixtures('<input id="field" type=' + type + '>');

                    field = $('#field');
                    field.prop('required', required);
                    field.attr({
                        name: name,
                        minlength: minlength,
                        maxlength: maxlength,
                        value: value
                    });
                };

                var expectValid = function() {
                    result = EdxUtilsValidate.validate(field);
                    expect(result.isValid).toBe(true);
                };

                var expectInvalid = function(errorFragment) {
                    result = EdxUtilsValidate.validate(field);
                    expect(result.isValid).toBe(false);
                    expect(result.message).toMatch(errorFragment);
                };

                it('succeeds if an optional field is left blank', function() {
                    createFixture('text', 'username', false, MIN_LENGTH, MAX_LENGTH, '');
                    expectValid();
                });

                it('succeeds if a required field is provided a valid value', function() {
                    createFixture('text', 'username', true, MIN_LENGTH, MAX_LENGTH, VALID_STRING);
                    expectValid();
                });

                it('fails if a required field is left blank', function() {
                    createFixture('text', 'username', true, MIN_LENGTH, MAX_LENGTH, '');
                    expectInvalid(REQUIRED_ERROR_FRAGMENT);
                });

                it('fails if a field is provided a value below its minimum character limit', function() {
                    createFixture('text', 'username', false, MIN_LENGTH, MAX_LENGTH, SHORT_STRING);

                    // Verify optional field behavior
                    expectInvalid(MIN_ERROR_FRAGMENT);

                    // Verify required field behavior
                    field.prop('required', true);
                    expectInvalid(MIN_ERROR_FRAGMENT);
                });

                it('succeeds if a field with no minimum character limit is provided a value below its maximum character limit', function() {
                    createFixture('text', 'username', false, null, MAX_LENGTH, SHORT_STRING);

                    // Verify optional field behavior
                    expectValid();

                    // Verify required field behavior
                    field.prop('required', true);
                    expectValid();
                });

                it('fails if a required field with no minimum character limit is left blank', function() {
                    createFixture('text', 'username', true, null, MAX_LENGTH, '');
                    expectInvalid(REQUIRED_ERROR_FRAGMENT);
                });

                it('fails if a field is provided a value above its maximum character limit', function() {
                    createFixture('text', 'username', false, MIN_LENGTH, MAX_LENGTH, LONG_STRING);

                    // Verify optional field behavior
                    expectInvalid(MAX_ERROR_FRAGMENT);

                    // Verify required field behavior
                    field.prop('required', true);
                    expectInvalid(MAX_ERROR_FRAGMENT);
                });

                it('succeeds if a field with no maximum character limit is provided a value above its minimum character limit', function() {
                    createFixture('text', 'username', false, MIN_LENGTH, null, LONG_STRING);

                    // Verify optional field behavior
                    expectValid();

                    // Verify required field behavior
                    field.prop('required', true);
                    expectValid();
                });

                it('succeeds if a field with no character limits is provided a value', function() {
                    createFixture('text', 'username', false, null, null, VALID_STRING);

                    // Verify optional field behavior
                    expectValid();

                    // Verify required field behavior
                    field.prop('required', true);
                    expectValid();
                });

                it('fails if an email field is provided an invalid address', function() {
                    createFixture('email', 'email', false, MIN_LENGTH, MAX_LENGTH, 'localpart');

                    // Verify optional field behavior
                    expectInvalid(EMAIL_ERROR_FRAGMENT);

                    // Verify required field behavior
                    field.prop('required', false);
                    expectInvalid(EMAIL_ERROR_FRAGMENT);
                });

                it('succeeds if an email field is provided a valid address', function() {
                    createFixture('email', 'email', false, MIN_LENGTH, MAX_LENGTH, 'localpart@label.tld');

                    // Verify optional field behavior
                    expectValid();

                    // Verify required field behavior
                    field.prop('required', true);
                    expectValid();
                });

                it('succeeds if a checkbox is optional, or required and checked, but fails if a required checkbox is unchecked', function() {
                    createFixture('checkbox', 'checkbox', false, null, null, 'value');

                    // Optional, unchecked
                    expectValid();

                    // Optional, checked
                    field.prop('checked', true);
                    expectValid();

                    // Required, checked
                    field.prop('required', true);
                    expectValid();

                    // Required, unchecked
                    field.prop('checked', false);
                    expectInvalid(REQUIRED_ERROR_FRAGMENT);
                });

                it('succeeds if a select is optional, or required and default is selected, but fails if a required select has the default option selected', function() {
                    var select = [
                        '<select id="dropdown" name="country">',
                        '<option value="" data-isdefault="true">Please select a country</option>',
                        '<option value="BE">Belgium</option>',
                        '<option value="DE">Germany</option>',
                        '</select>'
                    ].join('');

                    setFixtures(select);

                    field = $('#dropdown');

                    // Optional
                    expectValid();

                    // Required, default text selected
                    field.attr('required', true);
                    expectInvalid(REQUIRED_ERROR_FRAGMENT);

                    // Required, country selected
                    field.val('BE');
                    expectValid();
                });

                it('returns a custom error message if an invalid field has one attached', function() {
                // Create a blank required field
                    createFixture('text', 'username', true, MIN_LENGTH, MAX_LENGTH, '');

                    // Attach a custom error message to the field
                    field.data('errormsg-required', CUSTOM_MESSAGE);

                    expectInvalid(CUSTOM_MESSAGE);
                });
            });
        });
}).call(this, define || RequireJS.define);
