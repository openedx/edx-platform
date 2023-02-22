/* globals gettext */
/* eslint-disable react/no-danger, import/prefer-default-export */
import React from 'react';
import PropTypes from 'prop-types';
import { Button, Icon, StatusAlert } from '@edx/paragon/static';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';
import StudentAccountDeletionModal from './StudentAccountDeletionModal';

export class StudentAccountDeletion extends React.Component {
    constructor(props) {
        super(props);
        this.closeDeletionModal = this.closeDeletionModal.bind(this);
        this.loadDeletionModal = this.loadDeletionModal.bind(this);
        this.state = {
            deletionModalOpen: false,
            isActive: props.isActive,
            socialAuthConnected: this.getConnectedSocialAuth(),
        };
    }

    getConnectedSocialAuth() {
        const { socialAccountLinks } = this.props;
        if (socialAccountLinks && socialAccountLinks.providers) {
            return socialAccountLinks.providers.reduce((acc, value) => acc || value.connected, false);
        }

        return false;
    }

    closeDeletionModal() {
        this.setState({ deletionModalOpen: false });
        this.modalTrigger.focus();
    }

    loadDeletionModal() {
        this.setState({ deletionModalOpen: true });
    }

    render() {
        const { deletionModalOpen, socialAuthConnected, isActive } = this.state;
        const loseAccessText = StringUtils.interpolate(
            gettext('You may also lose access to verified certificates and other program credentials like MicroMasters certificates. If you want to make a copy of these for your records before proceeding with deletion, follow the instructions for {htmlStart}printing or downloading a certificate{htmlEnd}.'),
            {
                htmlStart: '<a href="https://edx.readthedocs.io/projects/open-edx-learner-guide/en/latest/OpenSFD_certificates.html#print-a-web-certificate" rel="noopener" target="_blank">',
                htmlEnd: '</a>',
            },
        );

        const showError = socialAuthConnected || !isActive;

        const socialAuthError = StringUtils.interpolate(
            gettext('Before proceeding, please {htmlStart}unlink all social media accounts{htmlEnd}.'),
            {
                htmlStart: '<a href="https://support.edx.org/hc/en-us/articles/207206067" rel="noopener" target="_blank">',
                htmlEnd: '</a>',
            },
        );

        const activationError = StringUtils.interpolate(
            gettext('Before proceeding, please {htmlStart}{emailMsg}{htmlEnd}.'),
            {
                htmlStart: '<a href="https://support.edx.org/hc/en-us/articles/115000940568-How-do-I-activate-my-account-" rel="noopener" target="_blank">',
                htmlEnd: '</a>',
                emailMsg: this.props.mktgEmailOptIn ? 'confirm your email' : 'activate your account',
            },
        );

        const changeAcctInfoText = StringUtils.interpolate(
            gettext('{htmlStart}Want to change your email, name, or password instead?{htmlEnd}'),
            {
                htmlStart: '<a href="https://support.edx.org/hc/en-us/sections/115004139268-Manage-Your-Account-Settings" rel="noopener" target="_blank">',
                htmlEnd: '</a>',
            },
        );

        const acctDeletionWarningText = StringUtils.interpolate(
            gettext('{strongStart}Warning: Account deletion is permanent.{strongEnd} Please read the above carefully before proceeding. This is an irreversible action, and {strongStart}you will no longer be able to use the same email on {platformName}.{strongEnd}'),
            {
                strongStart: '<strong>',
                strongEnd: '</strong>',
                platformName: this.props.platformName,
            },
        );

        const noteDeletion = StringUtils.interpolate(
            gettext('Please note: Deletion of your account and personal data is permanent and cannot be undone. {platformName} will not be able to recover your account or the data that is deleted.'),
            {
                platformName: this.props.platformName,
            },
        );

        const bodyDeletion = StringUtils.interpolate(
            gettext('Once your account is deleted, you cannot use it to take courses on the {platformName} app, {siteName}, or any other site hosted by {platformName}.'),
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
            <div className="account-deletion-details">
                <p className="account-settings-header-subtitle">{ gettext('We’re sorry to see you go!') }</p>
                <p className="account-settings-header-subtitle">{noteDeletion}</p>
                <p className="account-settings-header-subtitle">
                    <span>{bodyDeletion} </span>
                    <span>{bodyDeletion2}</span>
                </p>
                <p
                    className="account-settings-header-subtitle"
                    dangerouslySetInnerHTML={{ __html: loseAccessText }}
                />
                <p
                    className="account-settings-header-subtitle-warning"
                    dangerouslySetInnerHTML={{ __html: acctDeletionWarningText }}
                />
                <p
                    className="account-settings-header-subtitle"
                    dangerouslySetInnerHTML={{ __html: changeAcctInfoText }}
                />
                <Button
                    id="delete-account-btn"
                    className={['btn-outline-primary']}
                    disabled={showError}
                    label={gettext('Delete My Account')}
                    inputRef={(input) => { this.modalTrigger = input; }}
                    onClick={this.loadDeletionModal}
                />
                {showError &&
          <StatusAlert
              dialog={(
                  <div className="modal-alert">
                      <div className="icon-wrapper">
                          <Icon id="delete-confirmation-body-error-icon" className={['fa', 'fa-exclamation-circle']} />
                      </div>
                      <div className="alert-content">
                          {socialAuthConnected && isActive &&
                    <p dangerouslySetInnerHTML={{ __html: socialAuthError }} />
                          }
                          {!isActive && <p dangerouslySetInnerHTML={{ __html: activationError }} /> }
                      </div>
                  </div>
              )}
              alertType="danger"
              dismissible={false}
              open
          />
                }
                {deletionModalOpen && <StudentAccountDeletionModal
                    onClose={this.closeDeletionModal}
                    additionalSiteSpecificDeletionText={this.props.additionalSiteSpecificDeletionText}
                    mktgRootLink={this.props.mktgRootLink}
                    platformName={this.props.platformName}
                    siteName={this.props.siteName}
                />}
            </div>
        );
    }
}

StudentAccountDeletion.propTypes = {
    isActive: PropTypes.bool.isRequired,
    socialAccountLinks: PropTypes.shape({
        providers: PropTypes.arrayOf(PropTypes.object),
    }).isRequired,
    additionalSiteSpecificDeletionText: PropTypes.string,
    mktgRootLink: PropTypes.string,
    platformName: PropTypes.string,
    siteName: PropTypes.string,
    mktgEmailOptIn: PropTypes.bool.isRequired,
};

StudentAccountDeletion.defaultProps = {
    additionalSiteSpecificDeletionText: '',
    mktgRootLink: '',
    platformName: '',
    siteName: '',
};
