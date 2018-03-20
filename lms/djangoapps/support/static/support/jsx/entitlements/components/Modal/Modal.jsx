import React from 'react';
import { Button, InputSelect, InputText, TextArea } from '@edx/paragon';
import { Modal } from '@edx/paragon';

class EntitlementModal extends React.Component{
  constructor(props){
    super(props);
    this.state = {
      isReissue: false,
      courseUuid: '',
      username: '',
      mode: '',
      comments: "Add any additional comments here",
    }
    this.handleCourseUUIDChange = this.handleCourseUUIDChange.bind(this);
    this.handleUsernameChange = this.handleUsernameChange.bind(this);
    this.handleModeChange = this.handleModeChange.bind(this);
    this.handleCommentsChange = this.handleCommentsChange.bind(this);
    this.submitForm = this.submitForm.bind(this);
    this.onClose = this.onClose.bind(this);
  }

  componentWillReceiveProps(nextProps){
  // Component Lifecycle function
  // updates state to reflect incoming props 
  // This prepopulates the re-issue modal with the correct values.
    const isReissue = nextProps.entitlement != null && nextProps.entitlement != undefined;
    this.setState({
      isReissue,
      comments: 'Add any additional comments here',
    })
    if(isReissue){
      const {courseUuid, mode, user} = nextProps.entitlement;
      this.setState({
        courseUuid,
        mode,
        username: user,
      });
    }
  }

  handleCourseUUIDChange(courseUuid){
    this.setState({ courseUuid });
  }

  handleUsernameChange(username){
    this.setState({ username });
  }

  handleModeChange(mode){
    this.setState({ mode });
  }

  handleCommentsChange(comments){
    this.setState({ comments });
  }

  submitForm(){
    if(this.state.isReissue) {//if there is an active entitlement we are updating an entitlement
      const { comments } = this.state;
      const { entitlement } = this.props;
      console.log('trying to reissue entitlement: ', entitlement)
      this.props.reissueEntitlement({entitlement, comments});
    }
    else { // if there is no active entitlement we are creating a new entitlement
      const {courseUuid, user, mode, reason, comments} = this.state;
      this.props.createEntitlement({courseUuid, user, mode, reason, comments});
    }
  }

  onClose(){
    this.props.closeModal();
  }

  render(){
    const { isReissue, courseUuid , username, mode, comments} = this.state
    const title = isReissue ? "Re-issue Entitlement" : "Create Entitlement"

    //Prepare body of the modal, if the Paragon Modal took children this could be 
    // moved into the return inside of the Modal component (instead of as body)

    //Note some fields are disabled when re-issuing an entitlement as they should not change
    const body = (
      <div>
        <InputText 
          disabled={ isReissue }
          name="courseUuid"
          label="Course UUID" 
          value={courseUuid} 
          onChange={this.handleCourseUUIDChange}
        />
        <InputText 
          disabled={ isReissue }
          name="username"
          label="Username" 
          value={username} 
          onChange={this.handleUsernameChange}
        />
        <InputSelect
          disabled={ isReissue }
          name="mode"
          label="Mode"
          value={mode}
          options={[
            { label: '--', value: '' },
            { label: 'Verified', value: 'verified' },
            { label: 'Professional', value: 'professional' }
          ]}
          onChange={this.handleModeChange}
        />
        <TextArea
          name="comments"
          label="Comments"
          value={comments}
          onChange={this.handleCommentsChange}
        />
      </div>
    )

    return (
      <div>
        <Modal  
          open={this.props.isOpen} 
          className="entitlement-modal"
          title={title}
          body={body}
          buttons={[
            <Button
              label="Submit"
              buttonType="primary"
              onClick={this.submitForm}
            />,
          ]}
          onClose={this.onClose}
        />
      </div>
    )
  }
}

export default EntitlementModal;