import React, { Component } from 'react';

const d3 = require('../d3.min.js');
import * as crossfilter from 'crossfilter2';

import Charts from '../Charts';
import Spacer from '../Spacer';

import PropTypes from 'prop-types';

/**
 * The CommunicatorContainer component is a self-contained widget that interacts with the
 * [Communicator](https://github.com/CAHLR/Communicator), an algorithm that predicts
 * whether students in online MOOCs are likely to drop out or fail to attain certification in a
 * course.
 * The Communicator component allows instructors in these MOOCs to send emails targeted specifically
 * at these demographics, providing more personalized and targeted instruction.
 */
class CommunicatorContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      /**
       * @param {Array<Object>} analyticsOptions Holds HTML <option /> components containing
       * past communications that have been sent in this course.
       * The value of each <option /> is a JavaScript object containing the following keys:
       * @param {Array<number>} attr Array of len 2 w the attrition graph bounds, from 0-100
       * @param {Array<number>} comp Array of len 2 w the completion graph bounds, from 0-100
       * @param {Array<number>} cert Array of len 2 w the certification graph bounds, from 0-100
       * @param {String} subject the saved email subject line
       * @param {String} body the saved email body
       * @param {String} reply the saved email's instructor email
       * @param {String} from the saved email's instructor name
       * @param {boolean} auto whether or not to use Automated Checking
       */
      analyticsOptions: [],
      /**
       * @param {String} dropdownValue An empty string representing an empty dropdown selection.
       */
      dropdownValue: '',
      /**
       * @param {String} instructorEmail the controlled state field for the instructor's email
       */
      instructorEmail: '',
      /**
       * @param {String} emailButtonError the error to display below the Send button
       */
      emailButtonError: '',
      /**
       * @param {boolean} analyticsRadio whether the graphs are in Analytics
       * (intelligent prediction) mode
       */
      analyticsRadio: true,
      /**
       * @param {String} analyticsDisplay the CSS `display` property to use for
       * the Charts div container
       */
      analyticsDisplay: 'block',
      /**
       * @param {boolean} allRadio whether the graphs are disabled (send to all students mode)
       */
      allRadio: false,
      /**
       * @param {boolean} emailButtonClicked whether or not the Send Email button has been clicked.
       * This determines if we show the warning/confirmation button or the Send button.
       */
      emailButtonClicked: false,
      /**
       * @param {number} totalActiveLearners a placeholder number set to
       * force the component to rerender.
       */
      totalActiveLearners: 0,
      /**
       * @param {String} emailSubject the controlled state field for the email's subject line
       */
      emailSubject: '',
      /**
       * @param {String} emailBody the controlled state field for the email's body content
       */
      emailBody: '',
      /**
       * @param {String} instructorName the controlled state field for the instructor's name
       */
      instructorName: '',
      /**
       * @param {String} emailSentMessage the message to display at the bottom
       * of the form after the email has been sent
       */
      emailSentMessage: '',
      /**
       * @param {String} oldSubject the stored subject line
       * of the original saved email that is being loaded
       */
      oldSubject: '',
      /**
       * @param {boolean} automatedChecked controlled state field for the
       * Automated Checking feature checkbox
       */
      automatedChecked: false,
      /**
       * @param {String} automatedDisplay the CSS `display` property for
       * the Automated Checking feature checkbox
       */
      automatedDisplay: 'inline',
      /**
       * @param {String} automated2Display the CSS `display` property
       * for the Automated Checking feature <p> descriptor
       */
      automated2Display: 'inline',
      /**
       * @param {String} saveChangesDisplay the CSS `display` property
       * for the Save Changes button. This button is only visible
       * when an existing sent email is being modified after being loaded.
       */
      saveChangesDisplay: 'none',
      /**
       * @param {String} tipDisplay the hover tooltip for the Automated
       * Checking feature
       */
      tipDisplay: 'none',
      /**
       * @param {String} allRecipientsDisplay the CSS `display` property
       * for the All Recipients count header
       */
      allRecipientsDisplay: 'none',
      /**
       * @param {String} recipientsDisplay the CSS `display` property
       * for the Recipients count header (only visible in Analytics mode)
       */
      recipientsDisplay: 'block',
      /**
       * @param {function} filter the filtering function set by the Charts
       * component. This function both filters on the underlying crossfilter
       * data object and modifies the graph UI elements accordingly.
       * This function is set only after the Charts component mounts.
       */
      filter: () => {},
      /**
       * @param {Object} filterLimits the filter limits, in percentiles,
       * for each graph. This should NOT ever be set in the Communicator
       * component, as the values in this object are set by and synced from
       * the Charts component. The object is duplicated from the Charts
       * component to allow for network request functions in the Communicator
       * component to access the filter limits.
       */
      filterLimits: {
        'completion-chart': [0, 100],
        'attrition-chart': [0, 100],
        'certification-chart': [0, 100],
      },
    };

    // bind all class functions to `this`
    this.onEmailButtonClick = this.onEmailButtonClick.bind(this);
    this.onLoad = this.onLoad.bind(this);
    this.onAnalyticsRadioClick = this.onAnalyticsRadioClick.bind(this);
    this.onAllRadioClick = this.onAllRadioClick.bind(this);
    this.getAnalytics = this.getAnalytics.bind(this);
    this.getAll = this.getAll.bind(this);
    this.setInstructorEmail = this.setInstructorEmail.bind(this);
    this.setEmailSubject = this.setEmailSubject.bind(this);
    this.clearDrop = this.clearDrop.bind(this);
    this.makeName = this.makeName.bind(this);
    this.sendEmails = this.sendEmails.bind(this);
    this.sendPolicy = this.sendPolicy.bind(this);
    this.loadData = this.loadData.bind(this);
    this.onAutomatedClick = this.onAutomatedClick.bind(this);
    this.setEmailBody = this.setEmailBody.bind(this);
    this.setInstructorName = this.setInstructorName.bind(this);
    this.optSelected = this.optSelected.bind(this);
    this.onCheckTipMouseOver = this.onCheckTipMouseOver.bind(this);
    this.onCheckTipMouseOut = this.onCheckTipMouseOut.bind(this);
    this.saveChanges = this.saveChanges.bind(this);
    this.onSaveChangesClick = this.onSaveChangesClick.bind(this);
    this.forceRerender = this.forceRerender.bind(this);
    this.syncChart = this.syncChart.bind(this);

    // initialize the current instance with empty crossfilter objects
    // so we can call crossfilter methods
    this.allStudents = crossfilter([]);
    this.filteredStudents = crossfilter([]);
    // keep a pointer to the anon_user_id dimension in this class so we can
    // access the filtered list of students from Charts
    this.anonUserId = this.filteredStudents.dimension(d => d.anon_user_id);
  }

  componentWillMount() {
    this.onLoad();
  }

  /**
   * Event hook for clicking the Automated Checking checkbox.
   * @param {MouseEvent} event the event object
   */
  onAutomatedClick(event) {
    this.setState({
      automatedChecked: event.target.checked,
    });
  }

  /**
   * Event hook for clicking the Send Email button. First checks
   * to see if the instructor email is valid, then sends emails,
   * saves the new email as a template, and regets student data.
   */
  async onEmailButtonClick() {
    if (this.state.instructorEmail === '' || !this.state.instructorEmail.includes('@')) {
      this.setState({
        emailButtonError: 'You have entered an invalid Instructor Email',
      });
    } else if (this.state.emailButtonClicked) {
      await this.sendEmails(this.anonUserId.top(Infinity).map(d => d.anon_user_id));
      await this.sendPolicy(
        this.anonUserId.top(Infinity).map(d => d.anon_user_id),
        this.state.filterLimits['completion-chart'],
        this.state.filterLimits['attrition-chart'],
        this.state.filterLimits['certification-chart'],
      );
      if (this.state.analyticsRadio) {
        await this.getAnalytics();
      } else {
        await this.getAll();
      }

      this.setState({
        emailButtonClicked: false,
      });
    } else {
      this.setState({
        emailButtonClicked: true,
      });
    }
  }

  /**
   * Function triggered on component mount to fetch data from the server.
   */
  async onLoad() {
    await this.loadData(`${this.props.backendUrl}/api/predictions`);
    await this.getAnalytics();
  }

  /**
   * Event hook for clicking the All radio button. Sets filters to
   * include all students and removes the graph interface.
   */
  onAllRadioClick() {
    this.setState({
      analyticsDisplay: 'none',
      allRadio: true,
      analyticsRadio: false,
      automatedDisplay: 'none',
      automated2Display: 'none',
      allRecipientsDisplay: 'block',
      recipientsDisplay: 'none',
      saveChangesDisplay: 'none',
    });
    this.state.filter([[0, 100], [0, 100], [0, 100]]);
    this.getAll();
  }

  /**
   * Event hook for clicking the Analytics radio button. Resets
   * all filters to null (off) and enables the graph interface.
   */
  onAnalyticsRadioClick() {
    this.setState({
      analyticsDisplay: 'block',
      automatedDisplay: 'inline',
      automated2Display: 'inline',
      allRecipientsDisplay: 'none',
      recipientsDisplay: 'block',
      analyticsRadio: true,
      allRadio: false,
    });
    this.state.filter([null, null, null]);
    this.getAnalytics();
  }

  /**
   * Event hook for removing the Tip upon unhovering over text/button.
   */
  onCheckTipMouseOut() {
    this.setState({
      tipDisplay: 'none',
    });
  }

  /**
   * Event hook for displaying the Tip upon unhovering over text/button.
   */
  onCheckTipMouseOver() {
    this.setState({
      tipDisplay: 'block',
    });
  }

  /**
   * Event hook for saving changes to the current loaded
   * saved email/template. Calls the server to save the current
   * filter limits and selected students.
   */
  async onSaveChangesClick() {
    await this.saveChanges(
      this.anonUserId.top(Infinity).map(d => d.anon_user_id),
      this.state.filterLimits['completion-chart'],
      this.state.filterLimits['attrition-chart'],
      this.state.filterLimits['certification-chart'],
    );
    await this.getAnalytics();
  }

  /**
   * Event hook for email body changes.
   * @param {Event} event the Event object
   */
  setEmailBody(event) {
    this.setState({
      emailBody: event.target.value,
    });
  }

  /**
   * Event hook for email subject changes.
   * @param {Event} event the Event object
   */
  setEmailSubject(event) {
    this.setState({
      emailSubject: event.target.value,
    });
  }

  /**
   * Event hook for instructor email changes.
   * @param {Event} event the Event object
   */
  setInstructorEmail(event) {
    this.setState({
      instructorEmail: event.target.value,
    });
  }

  /**
   * Calls the server to fetch saved emails for
   * all students in the course, then loads the resulting
   * saved email templates into the selection dropdown.
   */
  async getAll() {
    let settings = await fetch(`${this.props.backendUrl}/api/all`, {
      method: 'GET',
    });
    settings = await settings.json();
    if (settings) {
      const analyticsOptions = [
        <option
          selected
          value={JSON.stringify({
            subject: '',
            comp: null,
            attr: null,
            cert: null,
            body: '',
            reply: '',
            from: '',
          })}
        >
          Load Past Communications
        </option>,
      ];
      const keys = Object.keys(settings);
      for (let i = 0; i < keys.length; i += 1) {
        const name = this.makeName(settings[keys[i]].timestamp, settings[keys[i]].subject);
        analyticsOptions.push(<option value={JSON.stringify(settings[keys[i]])}>{name}</option>);
      }
      this.setState({
        analyticsOptions,
      });
    }
  }

  /**
   * Fetches prediction metrics for all students in the course,
   * along with sent email templates. Email templates are then loaded
   * into the selection dropdown.
   */
  async getAnalytics() {
    let analyticsApiResult = await fetch(`${this.props.backendUrl}/api/analytics`, {
      method: 'GET',
    });
    analyticsApiResult = await analyticsApiResult.json();
    if (analyticsApiResult) {
      this.clearDrop();
      const appendedOptions = [];
      // TODO(Jeff): use a better variable name here
      const analyticsKeys = Object.keys(analyticsApiResult);
      for (let i = 0; i < analyticsKeys.length; i += 1) {
        let name = this.makeName(
          analyticsApiResult[analyticsKeys[i]].timestamp,
          analyticsApiResult[analyticsKeys[i]].subject,
        );
        if (analyticsApiResult[analyticsKeys[i]].auto === 'true') {
          name = `(Active) ${name}`;
        }
        appendedOptions.push((
          <option value={JSON.stringify(analyticsApiResult[analyticsKeys[i]])}>
            {name}
          </option>
        ));
      }

      this.setState({
        analyticsOptions: [...this.state.analyticsOptions, ...appendedOptions],
      });
    }
  }

  /**
   * Event hook for changes to the instructor name.
   * @param {Event} event the Event object
   */
  setInstructorName(event) {
    this.setState({
      instructorName: event.target.value,
    });
  }

  /**
   * Syncs whatever fields/functions are needed from the Charts component
   * to the Communicator state. This is used to sync the graph `filter`
   * function as well as sync `filterLimits` from Charts.
   * @param {Object} _ an object with the fields you wish to set in Communicator's state
   */
  syncChart(_) {
    this.setState({
      ..._,
    });
  }

  /**
   * Sends emails to students.
   * @param {Array<String>} ids an Array of anonymized student id Strings
   */
  async sendEmails(ids) {
    const ann = this.state.allRadio;

    // get the course ID
    const course = this.props.courseId;
    // TODO(Jeff): resolve XSS when we host on edx servers
    const settings = await fetch(`${this.props.backendUrl}/api/email`, {
      method: 'POST',
      body: JSON.stringify({
        ids,
        subject: this.state.emailSubject,
        body: this.state.emailBody,
        reply: this.state.instructorEmail,
        from: this.state.instructorName,
        anonUserId: this.props.anonUserId,
        ann,
        course,
      }),
    });

    // if we succeeded in sending, save the current email template
    // and reload our data
    if (settings) {
      await this.saveChanges(
        this.anonUserId.top(Infinity).map(d => d.anon_user_id),
        this.state.filterLimits['completion-chart'],
        this.state.filterLimits['attrition-chart'],
        this.state.filterLimits['certification-chart'],
      );
      if (this.state.analyticsRadio) {
        this.getAnalytics();
      } else {
        this.getAll();
      }
      this.setState({
        emailSentMessage: 'Successfully Sent!',
        emailButtonClicked: false,
      });
      setTimeout(() => {
        this.setState({
          emailSentMessage: '',
        });
      }, 7500);
    }
  }

  /**
   * Saves changes to an existing sent email/template.
   * @param {Array<String>} ids an Array of anonymized student ID Strings
   * @param {Array<number>} comp the Completion filter limits, from 0-100. Array length 2
   * @param {Array<number>} attr the Attrition filter limits, from 0-100. Array length 2
   * @param {Array<number>} cert the Certification filter limits, from 0-100. Array length 2
   */
  async saveChanges(ids, comp, attr, cert) {
    const automated = this.state.automatedChecked;

    const settings = await fetch(`${this.props.backendUrl}/api/changes`, {
      method: 'POST',
      body: JSON.stringify({
        old_subject: this.state.oldSubject,
        ids,
        from: this.state.instructorName,
        reply: this.state.instructorEmail,
        subject: this.state.emailSubject,
        body: this.state.emailBody,
        comp,
        attr,
        cert,
        auto: automated,
      }),
    });

    if (settings) {
      console.log('Policy Successfully Saved!');
    }
  }

  /**
   * Saves a newly created, successfully sent email template
   * to the server for future reuse.
   * @param {Array<String>} ids an Array of anonymized student ID Strings
   * @param {Array<number>} comp the Completion filter limits, from 0-100. Array length 2
   * @param {Array<number>} attr the Attrition filter limits, from 0-100. Array length 2
   * @param {Array<number>} cert the Certification filter limits, from 0-100. Array length 2
   */
  async sendPolicy(ids, comp, attr, cert) {
    const automated = this.state.automatedChecked;
    const analytics = this.state.analyticsRadio;

    const settings = await fetch(`${this.props.backendUrl}/api/save`, {
      method: 'POST',
      body: JSON.stringify({
        ids,
        from: this.state.instructorName,
        reply: this.state.instructorEmail,
        subject: this.state.emailSubject,
        body: this.state.emailBody,
        comp,
        attr,
        cert,
        auto: automated,
        analytics,
        timestamp: new Date(),
      }),
    });
    if (settings) {
      console.log('Policy Successfullly Sent!');
    }
  }

  /**
   * Resets the selection dropdown.
   */
  clearDrop() {
    this.setState({
      dropdownValue: '',
      analyticsOptions: [
        <option
          selected
          value={JSON.stringify({
            subject: '',
            comp: null,
            attr: null,
            cert: null,
            body: '',
            reply: '',
            from: '',
          })}
        >
          Load Past Communications
        </option>,
      ],
    });
  }

  /**
   * Forces the Communicator to rerender by setting a useless state field.
   * This is needed because filtering on the crossfilter objects does not
   * set state or change props (since it mutates an existing object), so we
   * need to manually trigger rerenders whenever a filter call occurs.
   */
  forceRerender() {
    console.log(this.state.totalActiveLearners);
    this.setState({
      totalActiveLearners: 0,
    });
  }

  /**
   * Loads analytics/student data from the server into d3 and crossfilter.
   * @param {String} dataUrl the URL to fetch the secured CSV from
   * @param {String} json a JSON string containing the data to use instead of secure CSV
   */
  async loadData(dataUrl, json) {
    // if we're given the json, use that instead
    let response;
    if (json) {
      response = await d3.json(dataUrl);
    } else {
      // otherwise fetch the secured CSV and parse it
      response = await fetch(dataUrl, {
        headers: {
          Authorization: `Basic ${btoa(`${this.props.anonUserId}:edx`)}`,
        },
        method: 'GET',
      });
      response = await response.text();
      response = d3.csv.parse(response);
    }

    const students = response;
    // relabel some fields to conform with the way our component expects it
    for (let i = 0; i < students.length; i += 1) {
      students[i].index = i;
      students[i].completion_prediction = +students[i].completion_prediction;
      students[i].attrition_prediction = +students[i].attrition_prediction;
      students[i].certification_prediction = +students[i].certification_prediction;
    }
    // initialize the crossfilter objects on the Communicator instance
    // note that calling filter methods on these objects does NOT trigger
    // a rerender, meaning you MUST manually call rerender for the DOM
    // to update correctly.
    this.allStudents = crossfilter(students);
    this.filteredStudents = crossfilter(students);
    this.anonUserId = this.filteredStudents.dimension(d => d.anon_user_id);
  }

  /**
   * Creates the name for the dropdown which includes the date and subject.
   * @param {String} timestamp the timestamp of the dropdown option, in ISO8601 string form
   * @param {String} subject the subject of the dropdown option
   */
  makeName(timestamp, subject) {
    const formattedDate = new Date(timestamp).toDateString().split(' ');
    return `${formattedDate[1]} ${formattedDate[2]} ${formattedDate[3]} - ${subject}`;
  }

  /**
   * Event hook for selecting an option from the dropdown menu.
   * Loads the selected saved email/template into the form/graphs.
   * @param {Object} response the selected <option/> 's value containing the attributes below
   * @param {Array<number>} attr Array of len 2 containing the attrition graph bounds, from 0-100
   * @param {Array<number>} comp Array of len 2 containing the completion graph bounds, from 0-100
   * @param {Array<number>} cert Array of len 2 containng the certification graph bounds, from 0-100
   * @param {String} subject the saved email subject line
   * @param {String} body the saved email body
   * @param {String} reply the saved email's instructor email
   * @param {String} from the saved email's instructor name
   * @param {boolean} auto whether Automated Checking is enabled
   */
  optSelected(response) {
    const r = JSON.parse(response);
    this.setState({
      oldSubject: r.subject,
    });
    this.state.filter([r.comp, r.attr, r.cert]);
    this.setState({
      emailSubject: r.subject,
      emailBody: r.body,
      instructorEmail: r.reply,
      instructorName: r.from,
    });
    if (r.auto === 'true') {
      this.setState({
        automatedChecked: true,
        saveChangesDisplay: 'none',
      });
    } else {
      this.setState({
        automatedChecked: false,
        saveChangesDisplay: 'none',
      });
    }
    if (r.analytics === 'true') {
      this.setState({
        saveChangesDisplay: 'inline-block',
      });
    }
  }

  render() {
    return (
      <div style={{ padding: 20 }}>
        <h3>Select recipients by:</h3>
        <Spacer />
        {/* whether predictive Analytics should be used or if we should send to everyone */}
        <form className="radios">
          <div>
            <input type="radio" id="analyticsRadio" name="type" value="analytics" checked={this.state.analyticsRadio} onChange={this.onAnalyticsRadioClick} />
            Analytics
            <input type="radio" id="allRadio" name="type" value="all" checked={this.state.allRadio} onChange={this.onAllRadioClick} />
            All Learners
          </div>
        </form>

        {/* dropdown for selecting previously sent emails as templates */}
        <select id="myDropdown" onChange={(event) => { this.optSelected(event.target.value); }} >
          {this.state.dropdownValue}
          {this.state.analyticsOptions}
        </select>

        {/* Analytics charts, only displayed in Analytics mode */}
        <div id="analytics" style={{ display: this.state.analyticsDisplay }} >
          <Charts
            allStudents={this.allStudents}
            filteredStudents={this.filteredStudents}
            forceRerender={this.forceRerender}
            syncChart={this.syncChart}
          />
        </div>

        {/* form for composing the email to send to students */}
        <form style={{
          borderStyle: 'solid',
          padding: '20px',
          marginTop: '50px',
          minHeight: 550,
          }}
        >
          <h3>Compose Email</h3>
          <Spacer />
          <h6 id="recipients" style={{ display: this.state.recipientsDisplay }}>Recipients: {this.anonUserId.top(Infinity).length} Learners</h6>
          <h6 id="all-recipients" style={{ display: this.state.allRecipientsDisplay }}>Recipients: {this.anonUserId.top(Infinity).length} Learners</h6>

          <div style={{ marginTop: '20px' }}>
            <h4>From</h4>
            <Spacer />
            <input id="from-name" type="text" placeholder="Instructor Name" value={this.state.instructorName} onChange={this.setInstructorName} />
            <input id="reply-to" type="text" placeholder="Instructor Email" value={this.state.instructorEmail} onChange={this.setInstructorEmail} />
            <p id="email-button-error">{this.state.emailButtonError}</p>
            <div>
              <Spacer />
              <h4>Subject</h4>
              <input id="email-subject" type="text" placeholder="Subject" value={this.state.emailSubject} onChange={this.setEmailSubject} />
              <Spacer />
              <h4>Body</h4>
              <textarea
                id="email-body"
                placeholder="Use [:fullname:] to insert learner's full name and [:firstname:] to insert learner's last name"
                value={this.state.emailBody}
                onChange={this.setEmailBody}
              />
              <Spacer />
              <button
                type="button"
                id="emailButton"
                onClick={this.onEmailButtonClick}
                style={{
                  backgroundColor: this.state.emailButtonClicked ? 'red' : '#e4e4e4',
                  backgroundImage: this.state.emailButtonClicked ? 'linear-gradient(red,#8b0000)' : 'linear-gradient(#e4e4e4,#d1c9c9)',
                }}
              >
                {(() => {
                  if (this.state.emailButtonClicked) {
                    if (!this.state.analyticsRadio) {
                      return `Are you sure you want to send this email to ${this.anonUserId.top(Infinity).length} students?`;
                    }
                    return `Are you sure you want to send this email to ${this.anonUserId.top(Infinity).length} students?`;
                  }
                  return 'Send email to selected learners';
                })()}
              </button>
              <input
                id="automated"
                type="checkbox"
                checked={this.state.automatedChecked}
                onChange={this.onAutomatedClick}
                onMouseOver={this.onCheckTipMouseOver}
                onMouseOut={this.onCheckTipMouseOut}
                onFocus={() => {}}
                onBlur={() => {}}
                style={{ display: this.state.automatedDisplay }}
              />
              <p
                id="automated2"
                style={{ display: this.state.automated2Display, marginTop: -10 }}
                onMouseOver={this.onCheckTipMouseOver}
                onMouseOut={this.onCheckTipMouseOut}
                onFocus={() => {}}
                onBlur={() => {}}
              >
                Automatically check for and send to new matches found daily
              </p>
              <p id="tip" style={{ display: this.state.tipDisplay }}>Tip: Enabling this feature will check everyday for learners who meet the analytics criteria of this communication and will send this email to them (learners will never recieve an email twice).</p>
              <p style={{ color: 'green' }} >{this.state.emailSentMessage}</p>
              <p>
                *Please check the maximum daily recipient limit of your email provider.
                For example, Gmail is 500 per day.*
              </p>
            </div>
          </div>
        </form>
        <button
          href="#"
          type="button"
          id="saveChanges"
          className="save"
          style={{ display: this.state.saveChangesDisplay }}
          onClick={this.onSaveChangesClick}
        >
        Save Changes
        </button>
      </div>
    );
  }
}

CommunicatorContainer.propTypes = {

}

export default CommunicatorContainer;
