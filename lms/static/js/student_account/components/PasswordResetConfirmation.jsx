/* globals gettext */

import 'whatwg-fetch';
import PropTypes from 'prop-types';
import React from 'react';

import { Button, StatusAlert } from '@edx/paragon/static';

import PasswordResetInput from './PasswordResetInput';

// NOTE: Use static paragon with this because some internal classes (StatusAlert at least)
// conflict with some standard LMS ones ('alert' at least). This means that you need to do
// something like the following on any templates that use this class:
//
// <link type='text/css' rel='stylesheet' href='${STATIC_URL}paragon/static/paragon.min.css'>
//

class PasswordResetConfirmation extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      password: '',
      passwordConfirmation: '',
      showMatchError: false,
      isValid: true,
      validationMessage: '',
    };
    this.onBlurPassword1 = this.onBlurPassword1.bind(this);
    this.onBlurPassword2 = this.onBlurPassword2.bind(this);
  }

  onBlurPassword1(password) {
    this.updatePasswordState(password, this.state.passwordConfirmation);
    this.validatePassword(password);
  }

  onBlurPassword2(passwordConfirmation) {
    this.updatePasswordState(this.state.password, passwordConfirmation);
  }

  updatePasswordState(password, passwordConfirmation) {
    this.setState({
      password,
      passwordConfirmation,
      showMatchError: !!password && !!passwordConfirmation && (password !== passwordConfirmation),
    });
  }

  validatePassword(password) {
    fetch('/api/user/v1/validation/registration', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        password,
      }),
    })
    .then(res => res.json())
    .then((response) => {
      let validationMessage = '';
      // Be careful about grabbing this message, since we could have received an HTTP error or the
      // endpoint didn't give us what we expect. We only care if we get a clear error message.
      if (response.validation_decisions && response.validation_decisions.password) {
        validationMessage = response.validation_decisions.password;
      }
      this.setState({
        isValid: !validationMessage,
        validationMessage,
      });
    });
  }

  render() {
    return (
      <section id="password-reset-confirm-anchor" className="form-type">
        <div id="password-reset-confirm-form" className="form-wrapper" aria-live="polite">
          <StatusAlert
            alertType="danger"
            dismissible={false}
            open={!!this.props.errorMessage}
            dialog={this.props.errorMessage}
          />

          <form id="passwordreset-form" method="post" action="">
            <h2 className="section-title lines">
              <span className="text">
                {this.props.formTitle}
              </span>
            </h2>

            <p className="action-label" id="new_password_help_text">
              {gettext('Enter and confirm your new password.')}
            </p>

            <PasswordResetInput
              name="new_password1"
              describedBy="new_password_help_text"
              label={gettext('New Password')}
              onBlur={this.onBlurPassword1}
              isValid={this.state.isValid}
              validationMessage={this.state.validationMessage}
            />

            <PasswordResetInput
              name="new_password2"
              describedBy="new_password_help_text"
              label={gettext('Confirm Password')}
              onBlur={this.onBlurPassword2}
              isValid={!this.state.showMatchError}
              validationMessage={gettext('Passwords do not match.')}
            />

            <input
              type="hidden"
              id="csrf_token"
              name="csrfmiddlewaretoken"
              value={this.props.csrfToken}
            />

            <Button
              type="submit"
              className={['action', 'action-primary', 'action-update', 'js-reset']}
              label={this.props.primaryActionButtonLabel}
            />
          </form>
        </div>
      </section>
    );
  }
}

PasswordResetConfirmation.propTypes = {
  csrfToken: PropTypes.string.isRequired,
  errorMessage: PropTypes.string,
  primaryActionButtonLabel: PropTypes.string,
  formTitle: PropTypes.string,
};

PasswordResetConfirmation.defaultProps = {
  errorMessage: '',
  primaryActionButtonLabel: gettext('Reset My Password'),
  formTitle: gettext('Reset Your Password'),
};

export { PasswordResetConfirmation }; // eslint-disable-line import/prefer-default-export
