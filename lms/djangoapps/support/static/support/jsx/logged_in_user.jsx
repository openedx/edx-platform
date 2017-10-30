/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';

function LoggedInUser({ userInformation }) {
  return (<div>
    <div className="row">
      <div
        className="col-sm-12 user-info"
        data-username={userInformation.username}
        data-email={userInformation.email}
      >
        <p>{gettext(`What can we help you with, ${userInformation.username}?`)}</p>
      </div>
    </div>

    <div className="row">
      <div className="col-sm-12">
        <div className="form-group">
          {userInformation.enrollments.length === 0 &&
          <div>
            <label htmlFor="course">{gettext('Course Name')}<span> {gettext('(Optional)')}</span></label>
            <input type="text" className="form-control" id="course" />
          </div>
          }
          {userInformation.enrollments.length > 0 &&
          <div>
            <label className="label-course" htmlFor="course">{gettext('Course Name')}</label>
            <select className="form-control select-course" id="course">
              {userInformation.enrollments.map(enrollment =>
                (<option key={enrollment.course_id} value={enrollment.course_id}>
                  {enrollment.course_name}
                </option>),
              )}
            </select>
          </div>
          }
        </div>
      </div>
    </div>
  </div>);
}

LoggedInUser.propTypes = {
  userInformation: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default LoggedInUser;
