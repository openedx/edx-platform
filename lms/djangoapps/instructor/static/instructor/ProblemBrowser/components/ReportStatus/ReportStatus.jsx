/* global gettext */
import { Icon } from '@edx/paragon';
import classNames from 'classnames';
import * as PropTypes from 'prop-types';
import * as React from 'react';

// eslint-disable-next-line react/function-component-definition
const ReportStatus = ({
    error, succeeded, inProgress, reportPath,
}) => {
    const progressMessage = (
        <div className="msg progress">
            {gettext('Your report is being generated...')}
            <Icon hidden className={['fa', 'fa-refresh', 'fa-spin', 'fa-fw']} />
        </div>
    );

    const successMessage = (
        <div className="msg success">
            {gettext('Your report has been successfully generated.')}
            {reportPath
      && (
          <a href={reportPath}>
              <Icon hidden className={['fa', 'fa-link']} />
              {gettext('View Report')}
          </a>
      )}
        </div>
    );

    const errorMessage = (
        <div className={classNames('msg', { error })}>
            {error && `${gettext('Error')}: `}
            {error}
        </div>
    );

    return (
        <div className="report-generation-status" aria-live="polite">
            {inProgress && progressMessage}
            {error && errorMessage}
            {succeeded && successMessage}
        </div>
    );
};

ReportStatus.propTypes = {
    error: PropTypes.string,
    succeeded: PropTypes.bool.isRequired,
    inProgress: PropTypes.bool.isRequired,
    reportPath: PropTypes.string,
};

ReportStatus.defaultProps = {
    error: null,
    reportPath: null,
    // eslint-disable-next-line react/default-props-match-prop-types
    reportPreview: null,
    // eslint-disable-next-line react/default-props-match-prop-types
    reportName: null,
};

export default ReportStatus;
