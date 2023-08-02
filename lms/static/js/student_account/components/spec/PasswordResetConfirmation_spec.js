/* globals setFixtures */

import ReactDOM from 'react-dom';
import React from 'react';
import sinon from 'sinon'; // eslint-disable-line import/no-extraneous-dependencies
import { PasswordResetConfirmation } from '../PasswordResetConfirmation';

describe('PasswordResetConfirmation', () => {
    beforeEach(() => {
        setFixtures('<div id="wrapper"></div>');
        sinon.stub(window, 'fetch');
    });

    afterEach(() => {
        window.fetch.restore();
    });

    function init(submitError) {
        ReactDOM.render(
            React.createElement(PasswordResetConfirmation, {
                csrfToken: 'csrfToken',
                errorMessage: submitError,
            }, null),
            document.getElementById('wrapper'),
        );
    }

    function triggerValidation() {
        // eslint-disable-next-line no-undef
        $('#new_password1').focus();
        // eslint-disable-next-line no-undef
        $('#new_password1').val('a');
        // eslint-disable-next-line no-undef
        $('#new_password2').focus();

        expect(window.fetch.calledWithMatch(
            '/api/user/v1/validation/registration',
            { body: JSON.stringify({ password: 'a' }) },
        ));
    }

    function prepareValidation(validationError, done) {
        window.fetch.reset();
        window.fetch.callsFake(() => {
            done();
            return Promise.resolve({
                json: () => ({ validation_decisions: { password: validationError } }),
            });
        });
    }

    it('shows submit error', () => {
        init('Submit error.');

        // eslint-disable-next-line no-undef
        expect($('.alert-dialog')).toExist();
        // eslint-disable-next-line no-undef
        expect($('.alert-dialog')).not.toBeHidden();
        // eslint-disable-next-line no-undef
        expect($('.alert-dialog')).toHaveText('Submit error.');
    });

    describe('validation', () => {
        beforeEach((done) => {
            init('');
            prepareValidation('Validation error.', done);
            triggerValidation();
        });

        it('shows validation error', () => {
            // eslint-disable-next-line no-undef
            expect($('#error-new_password1')).toContainText('Validation error.');
        });
    });
});
