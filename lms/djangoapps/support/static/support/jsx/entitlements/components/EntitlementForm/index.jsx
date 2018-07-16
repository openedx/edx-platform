import React from 'react';
import PropTypes from 'prop-types';

import { Button, InputSelect, InputText, TextArea } from '@edx/paragon';
import { formTypes } from '../../data/constants/formTypes';

class EntitlementForm extends React.Component {
  constructor(props) {
    super(props);

    if (props.formType === formTypes.REISSUE) {
      const { courseUuid, mode, user } = props.entitlement;
      this.state = {
        courseUuid,
        mode,
        username: user,
        comments: '',
      };
    } else {
      this.state = {
        courseUuid: '',
        mode: '',
        username: '',
        comments: '',
      };
    }

    this.onClose = this.onClose.bind(this);
    this.handleCourseUUIDChange = this.handleCourseUUIDChange.bind(this);
    this.handleUsernameChange = this.handleUsernameChange.bind(this);
    this.handleModeChange = this.handleModeChange.bind(this);
    this.handleCommentsChange = this.handleCommentsChange.bind(this);
    this.submitForm = this.submitForm.bind(this);
  }

  onClose() {
    this.props.closeForm();
  }

  handleCourseUUIDChange(courseUuid) {
    this.setState({ courseUuid });
  }

  handleUsernameChange(username) {
    this.setState({ username });
  }

  handleModeChange(mode) {
    this.setState({ mode });
  }

  handleCommentsChange(comments) {
    this.setState({ comments });
  }

  submitForm() {
    const { courseUuid, username, mode, comments } = this.state;
    const { formType, entitlement } = this.props;
    if (formType === formTypes.REISSUE) { // if there is an active entitlement we are updating an entitlement
      this.props.reissueEntitlement({ entitlement, comments });
    } else { // if there is no active entitlement we are creating a new entitlement
      this.props.createEntitlement({ courseUuid, username, mode, comments });
    }
  }

  render() {
    const { courseUuid, username, mode, comments } = this.state;
    const isReissue = this.props.formType === formTypes.REISSUE;
    const title = isReissue ? 'Re-issue Entitlement' : 'Create Entitlement';

    const body = (
      <div>
        <h3> {title} </h3>
        <InputText
          disabled={isReissue}
          name="courseUuid"
          label="Course UUID"
          value={courseUuid}
          onChange={this.handleCourseUUIDChange}
        />
        <InputText
          disabled={isReissue}
          name="username"
          label="Username"
          value={username}
          onChange={this.handleUsernameChange}
        />
        <InputSelect
          disabled={isReissue}
          name="mode"
          label="Mode"
          value={mode}
          options={[
            { label: '--', value: '' },
            { label: 'Verified', value: 'verified' },
            { label: 'Professional', value: 'professional' },
            { label: 'No ID Professional', value: 'no-id-professional' },
          ]}
          onChange={this.handleModeChange}
        />
        <TextArea
          name="comments"
          label="Comments"
          value={comments}
          onChange={this.handleCommentsChange}
        />
        <div>
          <Button
            className={['btn', 'btn-secondary']}
            label="Close"
            onClick={this.onClose}
          />
          <Button
            className={['btn', 'btn-primary']}
            label="Submit"
            onClick={this.submitForm}
          />
        </div>
      </div>
    );

    return this.props.isOpen && body;
  }
}

EntitlementForm.propTypes = {
  formType: PropTypes.string.isRequired,
  isOpen: PropTypes.bool.isRequired,
  entitlement: PropTypes.shape({
    uuid: PropTypes.string.isRequired,
    courseUuid: PropTypes.string.isRequired,
    created: PropTypes.string.isRequired,
    modified: PropTypes.string.isRequired,
    expiredAt: PropTypes.string,
    mode: PropTypes.string.isRequired,
    orderNumber: PropTypes.string,
    supportDetails: PropTypes.arrayOf(PropTypes.shape({
      supportUser: PropTypes.string,
      action: PropTypes.string,
      comments: PropTypes.string,
      unenrolledRun: PropTypes.string,
    })),
    user: PropTypes.string.isRequired,
  }),
  createEntitlement: PropTypes.func.isRequired,
  reissueEntitlement: PropTypes.func.isRequired,
  closeForm: PropTypes.func.isRequired,
};

EntitlementForm.defaultProps = {
  entitlement: {
    uuid: '',
    courseUuid: '',
    created: '',
    modified: '',
    expiredAt: '',
    mode: 'verified',
    orderNumber: '',
    supportDetails: [],
    user: '',
  },
};

export default EntitlementForm;
