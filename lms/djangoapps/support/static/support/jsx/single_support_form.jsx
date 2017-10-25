/* global gettext */
/* eslint one-var: ["error", "always"] */
/* eslint no-alert: "error" */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';

import FileUpload from './file_upload';
import ShowErrors from './errors_list';
import LoggedInUser from './logged_in_user';
import LoggedOutUser from './logged_out_user';

// TODO
// edx zendesk APIs
// access token
// custom fields ids
// https://openedx.atlassian.net/browse/LEARNER-2736
// https://openedx.atlassian.net/browse/LEARNER-2735

class RenderForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      currentRequest: null,
      errorList: [],
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
    const url = 'https://arbisoft.zendesk.com/api/v2/tickets.json',
      $userInfo = $('.user-info'),
      request = new XMLHttpRequest(),
      $course = $('#course'),
      accessToken = 'd6ed06821334b6584dd9607d04007c281007324ed07e087879c9c44835c684da',
      data = {
        subject: $('#subject').val(),
        comment: {
          body: $('#message').val(),
          uploads: $.map($('.uploaded-files button'), n => n.id),
        },
      };

    let course;

    if ($userInfo.length) {
      data.requester = $userInfo.data('email');
      course = $course.find(':selected').text();
      if (!course.length) {
        course = $course.val();
      }
    } else {
      data.requester = $('#email').val();
      course = $course.val();
    }

    data.custom_fields = [{
      id: '114099484092',
      value: course,
    }];

    if (this.validateData(data)) {
      request.open('POST', url, true);
      request.setRequestHeader('Authorization', `Bearer ${accessToken}`);
      request.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');

      request.send(JSON.stringify({
        ticket: data,
      }));

      request.onreadystatechange = function success() {
        if (request.readyState === 4 && request.status === 201) {
          // TODO needs to remove after implementing success page
          const alert = 'Request submitted successfully.';
          alert();
        }
      };

      request.onerror = function error() {
        this.setErrorState([gettext('Something went wrong. Please try again later.')]);
      }.bind(this);
    }
  }

  validateData(data) {
    const errors = [],
      regex = /^([a-zA-Z0-9_.+-])+@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;

    if (!data.requester) {
      errors.push(gettext('Enter a valid email address.'));
      $('#email').closest('.form-group').addClass('has-error');
    } else if (!regex.test(data.requester)) {
      errors.push(gettext('Enter a valid email address.'));
      $('#email').closest('.form-group').addClass('has-error');
    }
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

  render() {
    let userElement;
    if (this.props.context.user) {
      userElement = <LoggedInUser userInformation={this.props.context.user} />;
    } else {
      userElement = <LoggedOutUser loginUrl={this.props.context.loginQuery} />;
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
            <p>{gettext('Your question might have already been answered.')}</p>
          </div>
        </div>

        <div className="row">
          <div className="col-sm-12">
            <a
              href={this.props.context.marketingUrl}
              className="btn btn-secondary help-button"
            >{gettext('Search the edX Help Center')}</a>
          </div>
        </div>

        {userElement}

        <div className="row">
          <div className="col-sm-12">
            <div className="form-group">
              <label htmlFor="subject">{gettext('Subject')}</label>
              <input type="text" className="form-control" id="subject" />
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-sm-12">
            <div className="form-group">
              <label htmlFor="message">{gettext('Details')}</label>
              <p
                className="message-desc"
              >{gettext('The more you tell us, the more quickly and helpfully we can respond!')}</p>
              <textarea
                aria-describedby="message"
                className="form-control"
                rows="7"
                id="message"
              />
            </div>
          </div>
        </div>

        <FileUpload setErrorState={this.setErrorState} />

        <div className="row">
          <div className="col-sm-12">
            <button
              className="btn btn-primary btn-submit"
              onClick={this.submitForm}
            >{gettext('Submit')}</button>
          </div>
        </div>
      </div>
    );
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
