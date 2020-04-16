/* global gettext */
/* eslint one-var: ["error", "always"] */
/* eslint no-alert: "error" */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import { StatusAlert } from '@edx/paragon';

import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import ShowErrors from './errors_list';
import LoggedInUser from './logged_in_user';
import LoggedOutUser from './logged_out_user';
import Success from './success';


class RenderForm extends React.Component {
  constructor(props) {
    super(props);
    this.userInformation = this.props.context.user;
    const course = this.userInformation ? this.userInformation.course_id : '';
    this.state = {
      currentRequest: null,
      errorList: [],
      success: false,
      formData: {
        subject: '',
        message: '',
        course,
      },
    };
    this.submitForm = this.submitForm.bind(this);
    this.reDirectUser = this.reDirectUser.bind(this);
    this.setErrorState = this.setErrorState.bind(this);
    this.formOnChangeCallback = this.formOnChangeCallback.bind(this);
    this.showWarningMessage = this.showWarningMessage.bind(this);
    this.showDiscussionButton = this.showDiscussionButton.bind(this);
  }

  setErrorState(errors) {
    this.setState({
      errorList: errors,
    });
  }

  formOnChangeCallback(event) {
    const eventTarget = event.target;
    let formData = this.state.formData;
    formData[eventTarget.id] = eventTarget.value;
    this.setState({ formData });
  }

  showWarningMessage() {
    return this.state.formData && this.state.formData.subject === 'Course Content';
  }

  showDiscussionButton() {
    const selectCourse = this.state.formData.course;
    return this.state.formData && (selectCourse !== '' && selectCourse !== 'Not specific to a course');
  }

  reDirectUser(event) {
    event.preventDefault();
    window.location.href = `/courses/${this.state.formData.course}/discussion/forum`;
  }

  submitForm(event) {
    event.preventDefault();
    let subject,
      course;
    const url = this.props.context.submitFormUrl,
      request = new XMLHttpRequest(),
      $course = $('#course'),
      $subject = $('#subject'),
      data = {
        comment: {
          body: this.state.formData.message,
        },
        tags: this.props.context.tags,
      },
      errors = [];

    this.clearErrors();

    data.requester = {
      email: this.userInformation.email,
      name: this.userInformation.username,
    };

    course = $course.find(':selected').val();
    if (!course) {
      course = $course.val();
    }
    if (!course) {
      $('#course').closest('.form-group').addClass('has-error');
      errors.push(gettext('Select a course or select "Not specific to a course" for your support request.'));
    }
    data.custom_fields = [{
      id: this.props.context.customFields.course_id,
      value: course,
    }];
    subject = $subject.find(':selected').val();
    if (!subject) {
      subject = $subject.val();
    }
    if (!subject) {
      $subject.closest('.form-group').addClass('has-error');
      errors.push(gettext('Select a subject for your support request.'));
    }
    data.subject = subject; // Zendesk API requires 'subject'

    if (this.validateData(data, errors)) {
      request.open('POST', url, true);
      request.setRequestHeader('Content-type', 'application/json;charset=UTF-8');
      request.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));

      request.send(JSON.stringify(data));

      request.onreadystatechange = function success() {
        if (request.readyState === 4 && request.status === 201) {
          this.setState({
            success: true,
          });
        }
      }.bind(this);

      request.onerror = function error() {
        this.setErrorState([gettext('Something went wrong. Please try again later.')]);
      }.bind(this);
    }
  }

  clearErrors() {
    this.setErrorState([]);
    $('.form-group').removeClass('has-error');
  }

  validateData(data, errors) {
    if (!data.comment.body) {
      errors.push(gettext('Enter some details for your support request.'));
      $('#message').closest('.form-group').addClass('has-error');
    }

    if (!errors.length) {
      return true;
    }

    this.setErrorState(errors);
    return false;
  }

  renderSuccess() {
    return (
      <Success
        platformName={this.props.context.platformName}
        homepageUrl={this.props.context.homepageUrl}
        dashboardUrl={this.props.context.dashboardUrl}
        isLoggedIn={this.userInformation !== undefined}
      />
    );
  }

  renderSupportForm() {
    let userElement;
    if (this.userInformation) {
      userElement = (<LoggedInUser
        userInformation={this.userInformation}
        onChangeCallback={this.formOnChangeCallback}
        submitForm={this.submitForm}
        showWarning={this.showWarningMessage()}
        showDiscussionButton={this.showDiscussionButton()}
        reDirectUser={this.reDirectUser}
      />);
    } else {
      userElement = (<LoggedOutUser
        platformName={this.props.context.platformName}
        loginQuery={this.props.context.loginQuery}
        supportEmail={this.props.context.supportEmail}
      />);
    }

    return (
      <div className="contact-us-wrapper">

        {/* Note: not using Paragon bc component shows in the DOM but not rendered, even when using
         version 2.6.4. */}
        <div className="alert alert-warning" role="alert" style={{ marginBottom: '1rem', padding: '1.5rem', left: '0px', fontSize: '16px', backgroundColor: '#fffaed', color: '#171C29', border: '1px solid #FFD875', borderRadius: '0.3rem' }}>
          <div>{gettext('Due to the recent increase in interest in online education and edX, we are currently experiencing an unusually high volume of support requests. We appreciate your patience as we work to review each request. Please check the ')}<a href="https://support.edx.org/hc/en-us" className="alert-link">Help Center</a>{gettext(' as many questions may have already been answered.')}</div>
        </div>

        <div className="row">
          <div className="col-sm-12">
            <h2>{gettext('Contact Us')}</h2>
          </div>
        </div>

        <div className="row form-errors">
          <ShowErrors errorList={this.state.errorList} />
        </div>

        <div className="row">
          <div className="col-sm-12">
            <p>{gettext('Find answers to the top questions asked by learners.')}</p>
          </div>
        </div>

        <div className="row">
          <div className="col-sm-12">
            <a
              href={this.props.context.marketingUrl}
              className="btn btn-secondary help-button"
            >
              {StringUtils.interpolate(
                gettext('Search the {platform} Help Center'),
                { platform: this.props.context.platformName },
              )}
            </a>
          </div>
        </div>

        {userElement}
      </div>
    );
  }

  render() {
    if (this.state.success) {
      return this.renderSuccess();
    }

    return this.renderSupportForm();
  }
}

RenderForm.propTypes = {
  context: PropTypes.shape({
    customFields: PropTypes.object,
    dashboardUrl: PropTypes.string,
    homepageUrl: PropTypes.string,
    marketingUrl: PropTypes.string,
    loginQuery: PropTypes.string,
    platformName: PropTypes.string,
    submitFormUrl: PropTypes.string,
    supportEmail: PropTypes.string,
    tags: PropTypes.arrayOf(PropTypes.string),
    user: PropTypes.object,
  }).isRequired,
};

export class SingleSupportForm {
  constructor(context) {
    ReactDOM.render(
      <RenderForm context={context} />,
      document.getElementById('root'),
    );
  }
}
