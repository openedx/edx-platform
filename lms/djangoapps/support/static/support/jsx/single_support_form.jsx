/* global gettext */
/* eslint one-var: ["error", "always"] */
/* eslint no-alert: "error" */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';

import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import ShowErrors from './errors_list';
import LoggedInUser from './logged_in_user';
import LoggedOutUser from './logged_out_user';
import Success from './success';


class RenderForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      currentRequest: null,
      errorList: [],
      success: false,
    };
    this.submitForm = this.submitForm.bind(this);
    this.setErrorState = this.setErrorState.bind(this);
  }

  setErrorState(errors) {
    this.setState({
      errorList: errors,
    });
  }

  submitForm() {
    const url = this.props.context.submitFormUrl,
      $userInfo = $('.user-info'),
      request = new XMLHttpRequest(),
      $course = $('#course'),
      data = {
        subject: $('#subject').val(),
        comment: {
          body: $('#message').val(),
        },
        tags: this.props.context.tags,
      },
      errors = [];

    let course;
    this.clearErrors();

    data.requester = {
      email: $userInfo.data('email'),
      name: $userInfo.data('username'),
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
    if (!data.subject) {
      errors.push(gettext('Enter a subject for your support request.'));
      $('#subject').closest('.form-group').addClass('has-error');
    }
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
        isLoggedIn={this.props.context.user !== undefined}
      />
    );
  }

  renderSupportForm() {
    let userElement;
    if (this.props.context.user) {
      userElement = (<LoggedInUser
        userInformation={this.props.context.user}
        submitFormUrl={this.props.context.submitFormUrl}
        setErrorState={this.setErrorState}
        submitForm={this.submitForm}
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
  context: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export class SingleSupportForm {
  constructor(context) {
    ReactDOM.render(
      <RenderForm context={context} />,
      document.getElementById('root'),
    );
  }
}
