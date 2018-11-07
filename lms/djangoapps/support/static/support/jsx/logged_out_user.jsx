/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';

import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

function LoggedOutUser({ platformName, loginQuery, supportEmail }) {
  return (
    <div>
      <div className="row">
        <div className="col-sm-12">
          <p>{StringUtils.interpolate(
            gettext('Sign in to {platform} so we can help you better.'),
            { platform: platformName },
          )}</p>
        </div>
      </div>

      <div className="row">
        <div className="col-sm-12">
          <a href={`/login${loginQuery}`} className="btn btn-primary btn-signin">{gettext('Sign in')}</a>
        </div>
      </div>

      <div className="row">
        <div className="col-sm-12">
          <a className="create-account" href={`/register${loginQuery}`}>
            {StringUtils.interpolate(
              // FIXME: not all platforms start with a vowel
              gettext('Create an {platform} account'),
              { platform: platformName },
            )}
          </a>
          <p className="create-account-note">
            {StringUtils.interpolate(
              gettext('If you are unable to access your account contact us via email using {email}.'),
              { email: supportEmail },
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

LoggedOutUser.propTypes = {
  platformName: PropTypes.string.isRequired,
  loginQuery: PropTypes.string.isRequired,
  supportEmail: PropTypes.string.isRequired,
};

export default LoggedOutUser;
