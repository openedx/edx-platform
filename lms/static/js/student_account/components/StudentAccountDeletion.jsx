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
    const appsemblerAccountRemovalText = StringUtils.interpolate(
      gettext('If you require your account on this site to be deleted, please submit a request via email to {htmlStart}account.deletions@appsembler.com{htmlEnd}. Please submit your request from the email address linked to your user account, and in the email body, include any other profile details you wish to share to enable us to verify your identity, as well as clearly stating that you wish for your account to be deleted. We will endeavor to action your request within 30 days, and intend to further automate this process in the future for a more immediate response. There is no way to undo this request once it has been actioned, and should only be undertaken if absolutely necessary.'),
      {
        htmlStart: '<a href="mailto:account.deletions@appsembler.com">',
        htmlEnd: '</a>',
      },
    )
    const loseAccessText = StringUtils.interpolate(
      gettext('You may also lose access to verified certificates and other program credentials like MicroMasters certificates. If you want to make a copy of these for your records before proceeding with deletion, follow the instructions for {htmlStart}printing or downloading a certificate{htmlEnd}.'),
      {
        htmlStart: '<a href="http://edx.readthedocs.io/projects/edx-guide-for-students/en/latest/SFD_certificates.html#printing-a-certificate" target="_blank">',
        htmlEnd: '</a>',
      },
    );

    const showError = socialAuthConnected || !isActive;

    const socialAuthError = StringUtils.interpolate(
      gettext('Before proceeding, please {htmlStart}unlink all social media accounts{htmlEnd}.'),
      {
        htmlStart: '<a href="https://support.edx.org/hc/en-us/articles/207206067" target="_blank">',
        htmlEnd: '</a>',
      },
    );

    const activationError = StringUtils.interpolate(
      gettext('Before proceeding, please {htmlStart}activate your account{htmlEnd}.'),
      {
        htmlStart: '<a href="https://support.edx.org/hc/en-us/articles/115000940568-How-do-I-activate-my-account-" target="_blank">',
        htmlEnd: '</a>',
      },
    );

    return (
      <div className="account-deletion-details">
        <p className="account-settings-header-subtitle">{ gettext('We’re sorry to see you go!') }</p>
        <p
          className="account-settings-header-subtitle"
          dangerouslySetInnerHTML={{ __html: appsemblerAccountRemovalText }}
        />
        <p
          className="account-settings-header-subtitle"
          dangerouslySetInnerHTML={{ __html: loseAccessText }}
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
        {deletionModalOpen && <StudentAccountDeletionModal onClose={this.closeDeletionModal} />}
      </div>
    );
  }
}

StudentAccountDeletion.propTypes = {
  isActive: PropTypes.bool.isRequired,
  socialAccountLinks: PropTypes.shape({
    providers: PropTypes.arrayOf(PropTypes.object),
  }).isRequired,
};
