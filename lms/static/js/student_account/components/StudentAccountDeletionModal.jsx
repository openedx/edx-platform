/* globals gettext */
import React from 'react';
import PropTypes from 'prop-types';
import {
    Button, ModalDialog, Icon, Form, Alert,
} from '@openedx/paragon';
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
        window.location.href = this.props.mktgRootLink;
    }

    // eslint-disable-next-line react/sort-comp
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
        const title = error.message === '403' ? gettext('Password is incorrect') : gettext('Unable to delete account');
        const body = error.message === '403' ? gettext('Please re-enter your password.') : gettext('Sorry, there was an error trying to process your request. Please try again later.');

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
        const loseAccessText = gettext('You may also lose access to verified certificates and other program credentials. You can make a copy of these for your records before proceeding with deletion.')

        const noteDeletion = StringUtils.interpolate(
            gettext('You have selected “Delete my account.” Deletion of your account and personal data is permanent and cannot be undone. {platformName} will not be able to recover your account or the data that is deleted.'),
            {
                platformName: this.props.platformName,
            },
        );

        const bodyDeletion = StringUtils.interpolate(
            gettext('If you proceed, you will be unable to use this account to take courses on the {platformName} app, {siteName}, or any other site hosted by {platformName}.'),
            {
                platformName: this.props.platformName,
                siteName: this.props.siteName,
            },
        );

        const bodyDeletion2 = StringUtils.interpolate(
            gettext('This includes access to {siteName} from your employer’s or university’s system{additionalSiteSpecificDeletionText}.'),
            {
                siteName: this.props.siteName,
                additionalSiteSpecificDeletionText: this.props.additionalSiteSpecificDeletionText,
            },
        );

        return (
            <div className="delete-confirmation-wrapper">
                <ModalDialog
                    title={gettext('Are you sure?')}
                    renderHeaderCloseButton={false}
                    onClose={onClose}
                    aria-live="polite"
                    isOpen
                    body={(
                        <div>
                            {responseError
                && (
                    <Alert
                        variant="danger"
                        dismissible={false}
                        show
                    >
                        <div className="modal-alert">
                            <div className="icon-wrapper">
                                <Icon src="fa fa-exclamation-circle" id="delete-confirmation-body-error-icon" />
                            </div>
                            <div className="alert-content">
                                <h3 className="alert-title">{ validationMessage }</h3>
                                <p>{ validationErrorDetails }</p>
                            </div>
                        </div>
                    </Alert>
                )}

                            <Alert
                                variant="warning"
                                dismissible={false}
                                show
                            >
                                <div className="modal-alert">
                                    <div className="icon-wrapper">
                                        <Icon src="fa fa-exclamation-triangle" id="delete-confirmation-body-warning-icon" />
                                    </div>
                                    <div className="alert-content">
                                        <h3 className="alert-title">{noteDeletion}</h3>
                                        <p>
                                            <span>{bodyDeletion} </span>
                                            <span>{bodyDeletion2}</span>
                                        </p>
                                        {/* eslint-disable-next-line react/no-danger */}
                                        <p>{loseAccessText}</p>
                                    </div>
                                </div>
                            </Alert>
                            <p className="next-steps">{ gettext('If you still wish to continue and delete your account, please enter your account password:') }</p>
                            <Form.Control
                                name="confirm-password"
                                type="password"
                                className="confirm-password-input"
                                onBlur={this.passwordFieldValidation}
                                isInvalid={!passwordValid}
                                onChange={(e) => this.handlePasswordInputChange(e.target.value)}
                                autoComplete="new-password"
                            />
                            <Form.Control.Feedback type="invalid">
                                {validationMessage}
                            </Form.Control.Feedback>
                        </div>
                    )}
                    closeText={gettext('Cancel')}
                    footerNode={
                        <Button
                            onClick={this.deleteAccount}
                            disabled={password.length === 0 || passwordSubmitted}
                        >
                            {gettext('Yes, Delete')}
                        </Button>
                    }
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
                    isOpen
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
    additionalSiteSpecificDeletionText: PropTypes.string,
    mktgRootLink: PropTypes.string,
    platformName: PropTypes.string,
    siteName: PropTypes.string,
};

StudentAccountDeletionConfirmationModal.defaultProps = {
    onClose: () => {},
    additionalSiteSpecificDeletionText: '',
    mktgRootLink: '',
    platformName: '',
    siteName: '',
};

export default StudentAccountDeletionConfirmationModal;
