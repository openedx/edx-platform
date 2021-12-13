/* global gettext */
/* eslint one-var: ["error", "always"] */
/* eslint no-alert: "error" */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';

import ShowErrors from './errors_list';
import LoggedInUser from './logged_in_user';
import LoggedOutUser from './logged_out_user';
import Success from './success';

const initialFormErrors = {
  course: undefined,
  subject: undefined,
  message: undefined,
  request: undefined,
};

class RenderForm extends React.Component {
  constructor(props) {
    super(props);
    this.submitFormUrl = this.props.context.submitFormUrl;
    this.userInformation = this.props.context.user;
    const course = this.userInformation ? this.userInformation.course_id : '';
    this.courseDiscussionURL = '/courses/{course_id}/discussion/forum';
    this.learnerSupportCenterURL = 'https://support.edx.org';
    this.zendeskApiUrl = 'https://edxsupport.zendesk.com';
    this.submitButton = null;
    this.state = {
      currentRequest: null,
      errorList: initialFormErrors,
      success: false,
      activeSuggestion: 0,
      suggestions: [],
      typingTimeout: 0,
      formData: {
        course,
        subject: '',
        message: '',
      },
    };
    this.formValidationErrors = {
      course: gettext('Select a course or select "Not specific to a course" for your support request.'),
      subject: gettext('Select a subject for your support request.'),
      message: gettext('Enter some details for your support request.'),
      request: gettext('Something went wrong. Please try again later.'),
    };
    this.handleClick = this.handleClick.bind(this);
    this.reDirectUser = this.reDirectUser.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.formOnChangeCallback = this.formOnChangeCallback.bind(this);
    this.handleSearchButton = this.handleSearchButton.bind(this);
    this.onKeyDown = this.onKeyDown.bind(this);
    this.handleSuggestionClick = this.handleSuggestionClick.bind(this);
    this.ignoreBlur = false;
    this.handleBlur = this.handleBlur.bind(this);
  }

  setIgnoreBlur(ignore) {
    this.ignoreBlur = ignore;
  }

  getFormDataFromState() {
    return this.state.formData;
  }

  getFormErrorsFromState() {
    return this.state.errorList;
  }

  clearErrorState() {
    const formErrorsInState = this.getFormErrorsFromState();
    Object.keys(formErrorsInState).map((index) => {
      formErrorsInState[index] = undefined;
      return formErrorsInState;
    });
  }

  // eslint-disable-next-line class-methods-use-this
  scrollToTop() {
    return window.scrollTo(0, 0);
  }

  formHasErrors() {
    const errorsList = this.getFormErrorsFromState();
    return Object.keys(errorsList).filter(err => errorsList[err] !== undefined).length > 0;
  }

  updateErrorInState(key, error) {
    const errorList = this.getFormErrorsFromState();
    errorList[key] = error;
    this.setState({
      errorList,
    });
  }

  formOnChangeCallback(event) {
    const formData = this.getFormDataFromState();
    formData[event.target.id] = event.target.value;
    this.setState({ formData });
  }

  showWarningMessage() {
    const formData = this.getFormDataFromState(),
      selectedSubject = formData.subject;
    return formData && selectedSubject === 'Course Content';
  }

  showDiscussionButton() {
    const formData = this.getFormDataFromState(),
      selectedCourse = formData.course;
    return formData && (selectedCourse !== '' && selectedCourse !== 'Not specific to a course');
  }

  reDirectUser(event) {
    event.preventDefault();
    const formData = this.getFormDataFromState();
    window.location.href = this.courseDiscussionURL.replace('{course_id}', formData.course);
  }

  handleClick(event) {
    event.preventDefault();
    this.submitButton = event.currentTarget;
    this.submitButton.setAttribute('disabled', true);
    const formData = this.getFormDataFromState();
    this.clearErrorState();
    this.validateFormData(formData);
    if (this.formHasErrors()) {
      this.submitButton.removeAttribute('disabled');
      return this.scrollToTop();
    }
    this.createZendeskTicket(formData);
  }

  createZendeskTicket(formData) {
    const url = this.submitFormUrl,
      request = new XMLHttpRequest(),
      data = {
        comment: {
          body: formData.message,
        },
        subject: formData.subject, // Zendesk API requires 'subject'
        custom_fields: [
        {
          id: this.props.context.customFields.course_id,
          value: formData.course,
        },
        {
          id: this.props.context.customFields.referrer,
          value: document.referrer ? document.referrer : "Direct Contact Us Page Request",
        }
        ],
        tags: this.props.context.tags,
      };
    request.open('POST', url, true);
    request.setRequestHeader('Content-type', 'application/json;charset=UTF-8');
    request.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
    request.send(JSON.stringify(data));
    request.onreadystatechange = function success() {
      if (request.readyState === 4) {
        this.submitButton.removeAttribute('disabled');
        if (request.status === 201) {
          this.setState({
            success: true,
          });
        }
      }
    }.bind(this);

    request.onerror = function error() {
      this.updateErrorInState('request', this.formValidationErrors.request);
      this.submitButton.removeAttribute('disabled');
      this.scrollToTop();
    }.bind(this);
  }
  validateFormData(formData) {
    const { course, subject, message } = formData;

    let courseError,
      subjectError,
      messageError;

    courseError = (course === '') ? this.formValidationErrors.course : undefined;
    this.updateErrorInState('course', courseError);
    subjectError = (subject === '') ? this.formValidationErrors.subject : undefined;
    this.updateErrorInState('subject', subjectError);
    messageError = (message === '') ? this.formValidationErrors.message : undefined;
    this.updateErrorInState('message', messageError);
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

  handleInputChange(event) {
    event.preventDefault();
    const queryString = event.target.value;
    const { typingTimeout } = this.state;
    if (queryString.length > 3) {
      if (typingTimeout) { clearTimeout(typingTimeout); }
      const getSuggestions = async () => {
        const response = await fetch(`${this.zendeskApiUrl}/api/v2/help_center/articles/search.json?query=${queryString}`, {
          headers: {
            'Content-Type': 'application/json',
          },
        });
        let suggestions = await response.json();
        suggestions = suggestions.results.slice(0, 6);
        this.setState({ suggestions });
      };
      this.setState({
        typingTimeout: setTimeout(async () => {
          getSuggestions();
        }, 500),
      });
    } else {
      this.setState({
        suggestions: [],
        activeSuggestion: 0,
      });
    }
  }

  onKeyDown(event) {
    const { activeSuggestion, suggestions } = this.state;
    const enterKeyCode = 13,
      upArrowKeyCode = 38,
      downArrowKeyCode = 40;

    if (event.keyCode === enterKeyCode) {
      window.location.href = suggestions[activeSuggestion].html_url;
    } else if (event.keyCode === upArrowKeyCode) {
      (activeSuggestion === 0) ?
        this.setState({ activeSuggestion: suggestions.length - 1 }) :
        this.setState({ activeSuggestion: activeSuggestion - 1 });
    } else if (event.keyCode === downArrowKeyCode) {
      (activeSuggestion + 1 === suggestions.length) ?
        this.setState({ activeSuggestion: 0 }) :
        this.setState({ activeSuggestion: activeSuggestion + 1 });
    }
  }

  handleBlur(event) {
    if (!this.ignoreBlur) {
      this.setState({
        suggestions: [],
        activeSuggestion: 0,
      });
    }
  }

  handleSearchButton(query) {
    const queryString = query.replace(' ', '+');

    window.location.href = `${this.learnerSupportCenterURL}/hc/en-us/search?&query=${queryString}`;
  }

  handleSuggestionClick(url) {
    window.location.href = url;
  }

  renderSupportForm() {
    const { activeSuggestion, suggestions } = this.state;
    let userElement,
      suggestionsListComponent = null;
    if (this.userInformation) {
      userElement = (<LoggedInUser
        userInformation={this.userInformation}
        onChangeCallback={this.formOnChangeCallback}
        handleClick={this.handleClick}
        showWarning={this.showWarningMessage()}
        showDiscussionButton={this.showDiscussionButton()}
        reDirectUser={this.reDirectUser}
        errorList={this.getFormErrorsFromState()}
      />);
    } else {
      userElement = (<LoggedOutUser
        platformName={this.props.context.platformName}
        loginQuery={this.props.context.loginQuery}
        supportEmail={this.props.context.supportEmail}
      />);
    }
    if (suggestions !== null && suggestions.length) {
      suggestionsListComponent = (
        <ul className="suggestions">
          {suggestions.map((suggestion, index) => (
            <li
              className={index === activeSuggestion ? 'suggestion-active' : null}
              key={index}
              onMouseDown={() => this.setIgnoreBlur(true)}
              onClick={() => this.handleSuggestionClick(suggestion.html_url)}
              onMouseOver={() => this.setState({ activeSuggestion: index })}
            >
              <div dangerouslySetInnerHTML={{ __html: suggestion.title }} />
            </li>
            ))}
        </ul>
      );
    }

    return (
      <div className="contact-us-wrapper">

        {/* Note: not using Paragon bc component shows in the DOM but not rendered, even when using
         version 2.6.4. */}

        <div className="row">
          <div className="col-sm-12">
            <h2>{gettext('Contact Us')}</h2>
          </div>
        </div>
        <div className="row form-errors">
          <ShowErrors errorList={this.getFormErrorsFromState()} hasErrors={this.formHasErrors()} />
        </div>

        <div className="row">
          <div className="col-sm-12">
            <p>{gettext('Find answers to the top questions asked by learners.')}</p>
          </div>
        </div>

        <div className="row">
          <div className="col-sm-8">
            <label className="sr-only">Search the Learner Help Center</label>
            <input
              type="search"
              className="form-control"
              id="query"
              placeholder="Search the Learner Help Center"
              autoComplete="off"
              onChange={this.handleInputChange}
              onKeyDown={this.onKeyDown}
              onBlur={this.handleBlur}
            />
          </div>
          <div className="col-sm-4">
            <button
              className="btn btn-primary btn-submit btn"
              type="button"
              onClick={() => this.handleSearchButton(document.getElementById('query').value)}
            >
              Search
            </button>
          </div>
        </div>
        <div className="row">
          <div className="col-sm-8">
            {suggestionsListComponent}
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
