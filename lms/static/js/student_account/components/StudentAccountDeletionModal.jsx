/* globals gettext */
/* eslint-disable react/no-danger */
import React from 'react';
import PropTypes from 'prop-types';
import { Button, Modal, Icon, InputText, StatusAlert } from '@edx/paragon/static';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import { deactivate } from '../AccountsClient';
import removeLoggedInCookies from './removeLoggedInCookies';

class StudentAccountDeletionConfirmationModal extends React.Component {
  constructor(props) {
    super(props);

    this.deleteAccount = this.deleteAccount.bind(this);
    this.handlePasswordInputChange = this.handlePasswordInputChange.bind(this);
    this.passwordFieldValidation = this.passwordFieldValidation.bind(this);
    this.handleConfirmationModalClose = this.handleConfirmationModalClose.bind(this);
    this.state = {
      password: '',
      passwordSubmitted: false,
      passwordValid: true,
      validationMessage: '',
      validationErrorDetails: '',
      accountQueuedForDeletion: false,
      responseError: false,
    };
  }

  handleConfirmationModalClose() {
    this.props.onClose();

    removeLoggedInCookies();
    window.location.href = 'https://www.edx.org';
  }

  deleteAccount() {
    return this.setState(
      { passwordSubmitted: true },
      () => (
        deactivate(this.state.password)
          .then(() => this.setState({
            accountQueuedForDeletion: true,
            responseError: false,
            passwordSubmitted: false,
            validationMessage: '',
            validationErrorDetails: '',
          }))
          .catch(error => this.failedSubmission(error))
      ),
    );
  }

  failedSubmission(error) {
    const { status } = error;
    const title = status === 403 ? gettext('Password is incorrect') : gettext('Unable to delete account');
    const body = status === 403 ? gettext('Please re-enter your password.') : gettext('Sorry, there was an error trying to process your request. Please try again later.');

    this.setState({
      passwordSubmitted: false,
      responseError: true,
      passwordValid: false,
      validationMessage: title,
      validationErrorDetails: body,
    });
  }

  handlePasswordInputChange(value) {
    this.setState({ password: value });
  }

  passwordFieldValidation(value) {
    let feedback = { passwordValid: true };

    if (value.length < 1) {
      feedback = {
        passwordValid: false,
        validationMessage: gettext('A Password is required'),
        validationErrorDetails: '',
      };
    }

    this.setState(feedback);
  }

  renderConfirmationModal() {
    const {
      passwordValid,
      password,
      passwordSubmitted,
      responseError,
      validationErrorDetails,
      validationMessage,
    } = this.state;
    const { onClose } = this.props;
    const loseAccessText = StringUtils.interpolate(
      gettext('You may also lose access to verified certificates and other program credentials like MicroMasters certificates. If you want to make a copy of these for your records before proceeding with deletion, follow the instructions for {htmlStart}printing or downloading a certificate{htmlEnd}.'),
      {
        htmlStart: '<a href="https://edx.readthedocs.io/projects/edx-guide-for-students/en/latest/SFD_certificates.html#printing-a-certificate" rel="noopener" target="_blank">',
        htmlEnd: '</a>',
      },
    );

    return (
      <div className="delete-confirmation-wrapper">
        <Modal
          title={gettext('Are you sure?')}
          renderHeaderCloseButton={false}
          onClose={onClose}
          aria-live="polite"
          open
          body={(
            <div>
              {responseError &&
                <StatusAlert
                  dialog={(
                    <div className="modal-alert">
                      <div className="icon-wrapper">
                        <Icon id="delete-confirmation-body-error-icon" className={['fa', 'fa-exclamation-circle']} />
                      </div>
                      <div className="alert-content">
                        <h3 className="alert-title">{ validationMessage }</h3>
                        <p>{ validationErrorDetails }</p>
                      </div>
                    </div>
                  )}
                  alertType="danger"
                  dismissible={false}
                  open
                />
              }

              <StatusAlert
                dialog={(
                  <div className="modal-alert">
                    <div className="icon-wrapper">
                      <Icon id="delete-confirmation-body-warning-icon" className={['fa', 'fa-exclamation-triangle']} />
                    </div>
                    <div className="alert-content">
                      <h3 className="alert-title">{ gettext('You have selected “Delete my account.” Deletion of your account and personal data is permanent and cannot be undone. EdX will not be able to recover your account or the data that is deleted.') }</h3>
                      <p>{ gettext('If you proceed, you will be unable to use this account to take courses on the edX app, edx.org, or any other site hosted by edX. This includes access to edx.org from your employer’s or university’s system and access to private sites offered by MIT Open Learning, Wharton Executive Education, and Harvard Medical School.') }</p>
                      <p dangerouslySetInnerHTML={{ __html: loseAccessText }} />
                    </div>
                  </div>
                )}
                dismissible={false}
                open
              />
              <p className="next-steps">{ gettext('If you still wish to continue and delete your account, please enter your account password:') }</p>
              <InputText
                name="confirm-password"
                label="Password"
                type="password"
                className={['confirm-password-input']}
                onBlur={this.passwordFieldValidation}
                isValid={passwordValid}
                validationMessage={validationMessage}
                onChange={this.handlePasswordInputChange}
                autoComplete="new-password"
                themes={['danger']}
              />
            </div>
          )}
          closeText={gettext('Cancel')}
          buttons={[
            <Button
              label={gettext('Yes, Delete')}
              onClick={this.deleteAccount}
              disabled={password.length === 0 || passwordSubmitted}
            />,
          ]}
        />
      </div>
    );
  }

  renderSuccessModal() {
    return (
      <div className="delete-success-wrapper">
        <Modal
          title={gettext('We\'re sorry to see you go! Your account will be deleted shortly.')}
          renderHeaderCloseButton={false}
          body={gettext('Account deletion, including removal from email lists, may take a few weeks to fully process through our system. If you want to opt-out of emails before then, please unsubscribe from the footer of any email.')}
          onClose={this.handleConfirmationModalClose}
          aria-live="polite"
          open
        />
      </div>
    );
  }

  render() {
    const { accountQueuedForDeletion } = this.state;

    return accountQueuedForDeletion ? this.renderSuccessModal() : this.renderConfirmationModal();
  }
}

StudentAccountDeletionConfirmationModal.propTypes = {
  onClose: PropTypes.func,
};

StudentAccountDeletionConfirmationModal.defaultProps = {
  onClose: () => {},
};

export default StudentAccountDeletionConfirmationModal;
