/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';

function LoggedOutUser({ platformName, loginUrl }) {
  return (
    <div>
      <div className="row">
        <div className="col-sm-12">
          <p>{gettext(`Sign in to ${platformName} so we can help you better.`)}</p>
        </div>
      </div>

      <div className="row">
        <div className="col-sm-12">
          <a href={loginUrl} className="btn btn-primary btn-signin">{gettext('Sign in')}</a>
        </div>
      </div>

      <div className="row">
        <div className="col-sm-12">
          <div className="form-group">
            <label htmlFor="email">{gettext('Your Email Address')}</label>
            <input type="text" className="form-control" id="email" />
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-sm-12">
          <div className="form-group">
            <label
              htmlFor="course"
            >{gettext('Course Name')}<span> {gettext('(Optional)')}</span></label>
            <input type="text" className="form-control" id="course" />
          </div>
        </div>
      </div>
    </div>
  );
}

LoggedOutUser.propTypes = {
  platformName: PropTypes.string.isRequired,
  loginUrl: PropTypes.string.isRequired,
};

export default LoggedOutUser;
