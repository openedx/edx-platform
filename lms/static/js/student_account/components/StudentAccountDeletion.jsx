/* globals gettext */
/* eslint-disable react/no-danger, import/prefer-default-export */
import React from 'react';
import { Button } from '@edx/paragon/static';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';
import StudentAccountDeletionModal from './StudentAccountDeletionModal';

export class StudentAccountDeletion extends React.Component {
  constructor(props) {
    super(props);
    this.closeDeletionModal = this.closeDeletionModal.bind(this);
    this.loadDeletionModal = this.loadDeletionModal.bind(this);
    this.state = { deletionModalOpen: false };
  }

  closeDeletionModal() {
    this.setState({ deletionModalOpen: false });
    this.modalTrigger.focus();
  }

  loadDeletionModal() {
    this.setState({ deletionModalOpen: true });
  }

  render() {
    const { deletionModalOpen } = this.state;
    const loseAccessText = StringUtils.interpolate(
      gettext('You may also lose access to verified certificates and other program credentials like MicroMasters certificates. If you want to make a copy of these for your records before proceeding with deletion, follow the instructions for {htmlStart}printing or downloading a certificate{htmlEnd}.'),
      {
        htmlStart: '<a href="http://edx.readthedocs.io/projects/edx-guide-for-students/en/latest/SFD_certificates.html#printing-a-certificate" target="_blank">',
        htmlEnd: '</a>',
      },
    );

    return (
      <div className="account-deletion-details">
        <p className="account-settings-header-subtitle">{ gettext('We’re sorry to see you go!') }</p>
        <p className="account-settings-header-subtitle">{ gettext('Please note: Deletion of your account and personal data is permanent and cannot be undone. EdX will not be able to recover your account or the data that is deleted.') }</p>
        <p className="account-settings-header-subtitle">{ gettext('Once your account is deleted, you cannot use it to take courses on the edX app, edx.org, or any other site hosted by edX. This includes access to edx.org from your employer’s or university’s system and access to private sites offered by MIT Open Learning, Wharton Executive Education, and Harvard Medical School.') }</p>
        <p
          className="account-settings-header-subtitle"
          dangerouslySetInnerHTML={{ __html: loseAccessText }}
        />

        <Button
          id="delete-account-btn"
          className={['btn-outline-primary']}
          label={gettext('Delete My Account')}
          inputRef={(input) => { this.modalTrigger = input; }}
          onClick={this.loadDeletionModal}
        />
        {deletionModalOpen && <StudentAccountDeletionModal onClose={this.closeDeletionModal} />}
      </div>
    );
  }
}
