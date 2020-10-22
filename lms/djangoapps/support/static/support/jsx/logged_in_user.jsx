/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';

import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import FileUpload from './file_upload';

function LoggedInUser({ userInformation, setErrorState, zendeskApiHost, submitForm }) {
  let courseElement;
  if (userInformation.enrollments) {
    courseElement = (<div>
      <label className="label-course" htmlFor="course">{gettext('Course Name')}</label>
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
          {courseElement}
        </div>
      </div>
    </div>

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

    {/* TODO file uploading will be done after initial release */}
    {/* <FileUpload */}
    {/* setErrorState={setErrorState} */}
    {/* zendeskApiHost={zendeskApiHost} */}
    {/* accessToken={accessToken} */}
    {/* /> */}

    <div className="row">
      <div className="col-sm-12">
        <button
          className="btn btn-primary btn-submit"
          onClick={submitForm}
        >{gettext('Submit')}</button>
      </div>
    </div>
  </div>);
}

LoggedInUser.propTypes = {
  setErrorState: PropTypes.func.isRequired,
  submitForm: PropTypes.func.isRequired,
  userInformation: PropTypes.arrayOf(PropTypes.object).isRequired,
  submitFormUrl: PropTypes.string.isRequired,
};

export default LoggedInUser;
