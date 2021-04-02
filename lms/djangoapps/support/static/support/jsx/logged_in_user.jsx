/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';
import { Button, StatusAlert } from '@edx/paragon';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

function LoggedInUser({ userInformation, onChangeCallback, handleClick, showWarning, showDiscussionButton, reDirectUser, errorList }) {
  let courseElement;
  let detailElement;
  let discussionElement = '';
  if (userInformation.enrollments) {
    courseElement = (<div>
      <label className="label-course" htmlFor="course">{gettext('Course Name')}</label>
      <p className="message-desc"><i>
        {gettext('For inquiries regarding assignments, grades, or structure of a specific course, please post in the discussion forums for that course directly.')}
      </i></p>
      <select
        className="form-control select-course"
        id="course"
        defaultValue={userInformation.course_id}
      >
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
  const subjectElement = (<div>
    <label htmlFor="subject">{gettext('Subject')}</label>
    <select className="form-control select-subject" id="subject">
      <option value="">{gettext('Select a category')}</option>
      <option value="Account Settings">{gettext('Account Settings')}</option>
      <option value="Billing/Payment Options">{gettext('Billing/Payment Options')}</option>
      <option value="Certificates">{gettext('Certificates')}</option>
      <option value="Course Content">{gettext('Course Content')}</option>
      <option value="Deadlines">{gettext('Deadlines')}</option>
      <option value="Errors/Technical Issues">{gettext('Errors/Technical Issues')}</option>
      <option value="Financial Aid">{gettext('Financial Aid')}</option>
      <option value="Photo Verification">{gettext('Photo Verification')}</option>
      <option value="Proctoring">{gettext('Proctoring')}</option>
      <option value="Other">{gettext('Other')}</option>
    </select>
  </div>);
  if (showDiscussionButton) {
    discussionElement = (
      <div className="row">
        <div className="col-sm-12">
          <Button
            className={['btn', 'btn-primary', 'btn-submit']}
            onClick={reDirectUser}
            label={gettext('Course Discussion Forum')}
          />
        </div>
      </div>
    );
  }
  if (showWarning) {
    detailElement = (
      <div id="warning-msg">
        <div className="row">
          <div className="col-sm-12">
            <div className="form-group">
              <StatusAlert
                alertType="info"
                className={['in', 'pattern-library-shim']}
                dismissible={false}
                dialog={
                  gettext('While our support team is happy to assist with the edX platform, the course staff has the expertise for specific assignment questions, grading or the proper procedures in each course. Please post all course related questions within the Discussion Forum where the Course Staff can directly respond.')
                }
                open
              />
            </div>
          </div>
        </div>
        { discussionElement }
      </div>
    );
  } else {
    detailElement = (
      <div>
        <div className="row">
          <div className="col-sm-12">
            <div className={`form-group ${errorList.message ? 'has-error' : ''}`}>
              <label htmlFor="message">{gettext('Details')}</label>
              <p className="message-desc">{gettext('the more quickly and helpfully we can respond!')}</p>
              <textarea aria-describedby="message" className="form-control" rows="7" id="message" />
            </div>
          </div>
        </div>
        <div className="row">
          <div className="col-sm-12">
            <Button
              className={['btn', 'btn-primary', 'btn-submit']}
              type="button"
              onClick={handleClick}
              label={gettext('Create Support Ticket')}
            />
          </div>
        </div>
      </div>
    );
  }

  return (<form id="contact-us-form" onChange={onChangeCallback}>
    <div className="row">
      <hr className="col-sm-12" />
    </div>
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
        <div className={`form-group ${errorList.subject ? 'has-error' : ''}`}>
          {subjectElement}
        </div>
      </div>
    </div>

    <div className="row">
      <div className="col-sm-12">
        <div className={`form-group ${errorList.course ? 'has-error' : ''}`}>
          {courseElement}
        </div>
      </div>
    </div>
    {detailElement}
  </form>);
}

    /* TODO file uploading will be done after initial release */
    /* <FileUpload */
    /* setErrorState={setErrorState} */
    /* zendeskApiHost={zendeskApiHost} */
    /* accessToken={accessToken} */
    /* /> */

LoggedInUser.propTypes = {
  handleClick: PropTypes.func.isRequired,
  onChangeCallback: PropTypes.func.isRequired,
  reDirectUser: PropTypes.func.isRequired,
  userInformation: PropTypes.shape({
    course_id: PropTypes.string,
    username: PropTypes.string,
    email: PropTypes.string,
    enrollments: PropTypes.arrayOf(PropTypes.object),
  }).isRequired,
  showWarning: PropTypes.bool.isRequired,
  showDiscussionButton: PropTypes.bool.isRequired,
  errorList: PropTypes.objectOf(PropTypes.string).isRequired,
};

export default LoggedInUser;
