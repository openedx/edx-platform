/* global gettext */
import { Button, Modal } from '@edx/paragon/static';
import * as classNames from 'classnames';
import * as PropTypes from 'prop-types';
import * as React from 'react';

const PopupModal = ({ open, onHide, message, error, succeeded, reportPath, reportPreview }) => {
  const previewButton = (
    <Button
      label={gettext('Preview CSV')}
      onClick={() =>
        window.open(reportPreview, '_blank')
      }
    />
  );
  const downloadButton = (
    <Button
      label={gettext('Download CSV')}
      onClick={() =>
        window.open(reportPath, '_blank')
      }
    />
  );

  const buttons = (reportPath && !error)
    ? [previewButton, downloadButton]
    : [];

  const progress = (!reportPath && !error && !message) && (
    <div className="title progress">
      <span className={'fa fa-refresh fa-spin fa-fw'}/>
      <b>{gettext('Your report is being created...')}</b>
    </div>
  );

  const body = (
    <div className="report-popup-modal-body">
      {progress}
      <p>
        {gettext('Once it\'s ready, you can view or download it using the buttons below. You can also close ' +
          'this popup now, and download the report later, from the "Reports Available for Download" area ' +
          'below.')}
      </p>
      {(!succeeded || error) &&
      <div className={classNames('msg', { warning: !succeeded, error })}>
        {error && `${gettext('Error')}:`}
        {error || message}
      </div>}
    </div>
  );

  return (
    <Modal
      title={gettext('Learner Response Report')}
      body={body}
      buttons={buttons}
      onClose={onHide}
      open={open}
      closeText={gettext('Close')}
    />
  );
};

PopupModal.propTypes = {
  open: PropTypes.bool,
  onHide: PropTypes.func.isRequired,
  message: PropTypes.string,
  error: PropTypes.string,
  succeeded: PropTypes.bool.isRequired,
  reportPath: PropTypes.string,
  reportPreview: PropTypes.string,
};

PopupModal.defaultProps = {
  open: false,
  message: null,
  error: null,
  reportPath: null,
  reportPreview: null,
};

export default PopupModal;
