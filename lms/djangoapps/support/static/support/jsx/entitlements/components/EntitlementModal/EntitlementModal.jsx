import React from 'react';
import { Modal, Button, InputSelect, InputText, TextArea } from '@edx/paragon';

class EntitlementModal extends React.Component{
	constructor(props){
		super(props);
		this.state = {
			courseUuid: '',
			user: '',
			mode: '',
			reason: '',
			comments: '',
		}
	}

	componentWillReceiveProps(nextProps){
		// Component Lifecycle function
		// updates state to reflect incoming props 
		// This prepopulates the re-issue modal with the correct values.
		if (nextProps !== this.props){ 
			this.setState({
				courseUuid: nextProps.courseUuid,
				user: nextProps.user,
				mode: nextProps.mode,
				reason: this.props.supportReasons[0].value, //Set reason to the default (first) reason in the list
				comments: '',
			})
		}
	}

	handleCourseUUIDChange(event){
		this.setState({courseUuid: event});
	}

	handleUserChange(event){
		this.setState({user: event});
	}

	handleModeChange(event){
		this.setState({mode: event});
	}

	handleReasonChange(event){
		this.setState({reason: event});
	}

	handleCommentsChange(event){
		this.setState({comments: event});
	}

	submitForm(){
		if(this.props.isReissue) {//if there is an active entitlement we are updating an entitlement
			const { user, reason, comments } = this.state;
			const entitlementUuid = this.props.entitlementUuid
			this.props.updateEntitlement(user, reason, entitlementUuid, comments);
		}
		else { // if there is no active entitlement we are creating a new entitlement
			const {courseUuid, user, mode, reason, comments} = this.state;
			this.props.createEntitlement(courseUuid, user, mode, reason, comments);
		}
	}

	onClose(){
		this.props.closeModal();
	}

	render(){
		const isReissue = this.props.isReissue
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
		      value={this.state.courseUuid} 
		      onChange={this.handleCourseUUIDChange.bind(this)}
		    />
				<InputText 
					disabled={ isReissue }
					name="user"
		      label="User" 
		      value={this.state.user} 
		      onChange={this.handleUserChange.bind(this)}
		    />
				<InputSelect
					disabled={ isReissue }
		      name="mode"
		      label="Mode"
		      value={this.state.mode}
		      options={[
		      	{ label: '--', value: '' },
		        { label: 'Verified', value: 'verified' },
		        { label: 'Professional', value: 'professional' }
		      ]}
		      onChange={this.handleModeChange.bind(this)}
		    />
				<InputSelect
					disabled={ isReissue }
		      name="reason"
		      label="Reason"
		      value={this.state.reason}
		      options={this.props.supportReasons}
		      onChange={this.handleReasonChange.bind(this)}
		    />
        <TextArea
		      name="comments"
		      label="Comments"
		      value="Add any additional comments here"
		      onChange={this.handleCommentsChange.bind(this)}
		    />
			</div>)

		return (
			<div>
      	<Modal  open={this.props.isOpen} 
      	className="entitlement-modal"
      	title={title}
	      body={body}
	      buttons={[
	      	<Button
	          label="Submit"
	          buttonType="primary"
	          onClick={this.submitForm.bind(this)}/>,
	     	]}
	      onClose={this.onClose.bind(this)}/>
	    </div>
   	)
	}
}

export default EntitlementModal;