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
                <div className="col-sm-6">
                    <a href={`/login${loginQuery}`} className="btn btn-primary btn-signin">{gettext('Sign in')}</a>
                </div>
                <div className="col-sm-6">
                    <a className="btn btn-secondary" href={`/register${loginQuery}`}>
                        {gettext('Create an Account')}
                    </a>
                </div>
            </div>

            <div className="row">
                <div className="col-sm-12">
                    <a href="/password_assistance" type="button" class="forgot-password field-link">{gettext('Need help logging in?')}</a>
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
