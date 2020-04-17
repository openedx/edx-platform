/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';

import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import FileUpload from './file_upload';


function LoggedInUser({ userInformation, setErrorState, zendeskApiHost, setDisplay, submitForm, showDisplay, reDirectUser}) {
  let courseElement;
  if (userInformation.enrollments) {
    courseElement = (<div>
      <label className="label-course" htmlFor="course">{gettext('Course Name')}</label>
      <p className="message-desc"><i>
      {gettext('For inquiries regarding assignments, grades, or structure of a specific course, please post in the discussion forums for that course directly.')}
      </i></p>
      <select className="form-control select-course" id="course" defaultValue={userInformation.course_id}>
        <option key="select-course" value="">--------</option>
        <option key="not-course-specific" value="Not specific to a course">
          {gettext('Not specific to a course')}
        </option>
        {userInformation.enrollments.map(enrollment =>
                (<option key={enrollment.course_id} value={enrollment.course_id}>
                  {enrollment.course_name}
                </option>),
              )}
      </select>
    </div>);
  } else {
    courseElement = (<div>
      <label htmlFor="course">{gettext('Course Name')}</label>
      <input type="text" className="form-control" id="course" />
    </div>);
  }

  let subjectElement;
  subjectElement = (<div>
    <label htmlFor="subject">{gettext('Subject')}</label>
    <select className="form-control select-subject" id="subject" onChange={setDisplay}>
      <option value="">--------</option>
      <option value="Account Settings">{gettext('Account Settings')}</option>
      <option value="Billing/Payment Options">{gettext('Billing/Payment Options')}</option>
      <option value="Certificates">{gettext('Certificates')}</option>
      <option value="Course Content">{gettext('Course Content')}</option>
      <option value="Deadlines">{gettext('Deadlines')}</option>
      <option value="Errors/Technical Issues">{gettext('Errors/Technical Issues')}</option>
      <option value="Financial Aid">{gettext('Financial Aid')}</option>
      <option value="Masters">{gettext('Masters')}</option>
      <option value="MicroMasters">{gettext('MicroMasters')}</option>
      <option value="MicroBachelors">{gettext('MicroBachelors')}</option>
      <option value="Photo Verification">{gettext('Photo Verification')}</option>
      <option value="Proctoring">{gettext('Proctoring')}</option>
      <option value="Security">{gettext('Security')}</option>
      <option value="Other">{gettext('Other')}</option>
    </select>
  </div>);

  return (<div>
    <div className="row">
      <div
        className="col-sm-12 user-info"
        data-username={userInformation.username}
        data-email={userInformation.email}
      >
        <p>
          {StringUtils.interpolate(
            gettext('What can we help you with, {username}?'),
            { username: userInformation.username },
          )}
        </p>
      </div>
    </div>

    <div className="row">
      <div className="col-sm-12">
        <div className="form-group">
          {subjectElement}
        </div>
      </div>
    </div>

    <div className="row">
      <div className="col-sm-12">
        <div className="form-group">
          {courseElement}
        </div>
      </div>
    </div>


{  showDisplay ? (
  <div>
    <div className="row">
      <div className="col-sm-12">
        <div className="form-group">
          <label htmlFor="message">{gettext('Details')}</label>
          <p
            className="message-desc"
          >{gettext('the more quickly and helpfully we can respond!')}</p>
          <textarea
            aria-describedby="message"
            className="form-control"
            rows="7"
            id="message"
          />
        </div>
      </div>
    </div>
    )

    <div className="row">
      <div className="col-sm-12">
        <button
          className="btn btn-primary btn-submit"
          onClick={submitForm}
        >{gettext('Submit')}</button>
      </div>
    </div>
  </div>
    ) : ( 
  <div>
    <div className="row">
      <div className="col-sm-12">
        <div className="form-group">
          <p> "While our support team is happy to assist with the edX platform. We are unable to assist with specific assignment questions, grading or the proper procedures in each course. Please post all course related questions within the Discussion Forum where the Course Staff can directly respond."</p>
        </div>
      </div>
    </div>

    <div className="row">
      <div className="col-sm-12">
        <button
          className="btn btn-primary btn-submit"
          onClick={reDirectUser}
        >{gettext('Course Discussion Forum')}</button>
      </div>
    </div>
  </div>
    )
}

  </div>);
}

    {/* TODO file uploading will be done after initial release */}
    {/* <FileUpload */}
    {/* setErrorState={setErrorState} */}
    {/* zendeskApiHost={zendeskApiHost} */}
    {/* accessToken={accessToken} */}
    {/* /> */}

LoggedInUser.propTypes = {
  setErrorState: PropTypes.func.isRequired,
  submitForm: PropTypes.func.isRequired,
  userInformation: PropTypes.arrayOf(PropTypes.object).isRequired,
  submitFormUrl: PropTypes.string.isRequired,
};

export default LoggedInUser;
