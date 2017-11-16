/* global gettext */
/* eslint one-var: ["error", "always"] */

import React from 'react';
import PropTypes from 'prop-types';

import ShowProgress from './upload_progress';


class FileUpload extends React.Component {
  constructor(props) {
    super(props);

    this.uploadFile = this.uploadFile.bind(this);
    this.removeFile = this.removeFile.bind(this);
    this.state = {
      fileList: [],
      fileInProgress: null,
    };
  }

  removeFile(e) {
    e.preventDefault();
    const fileToken = e.target.id,
      $this = this,
      url = `${this.props.zendeskApiHost}/api/v2/uploads/${fileToken}.json`,
      request = new XMLHttpRequest();

    request.open('DELETE', url, true);
    request.setRequestHeader('Authorization', `Bearer ${this.props.accessToken}`);
    request.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');

    request.send();

    request.onreadystatechange = function removeFile() {
      if (request.readyState === 4 && request.status === 204) {
        $this.setState({
          fileList: $this.state.fileList.filter(file => file.fileToken !== fileToken),
        });
      }
    };
  }

  uploadFile(e) {
    const url = `${this.props.zendeskApiHost}/api/v2/uploads.json?filename=`,
      fileReader = new FileReader(),
      request = new XMLHttpRequest(),
      errorList = [],
      $this = this,
      file = e.target.files[0],
      maxFileSize = 5000000, // 5mb is max limit
      allowedFileTypes = ['gif', 'png', 'jpg', 'jpeg', 'pdf'];

    // remove file from input and upload it to zendesk after validation
    $(e.target).val('');

    if (file.size > maxFileSize) {
      errorList.push(gettext('Files that you upload must be smaller than 5MB in size.'));
    } else if ($.inArray(file.name.split('.').pop().toLowerCase(), allowedFileTypes) === -1) {
      errorList.push(gettext('Files that you upload must be PDFs or image files in .gif, .jpg, .jpeg, or .png format.'));
    }

    this.props.setErrorState(errorList);
    if (errorList.length > 0) {
      return;
    }

    request.open('POST', (url + file.name), true);
    request.setRequestHeader('Authorization', `Bearer ${this.props.accessToken}`);
    request.setRequestHeader('Content-Type', 'application/binary');

    fileReader.readAsArrayBuffer(file);

    fileReader.onloadend = function success() {
      $this.setState({
        fileInProgress: file.name,
        currentRequest: request,
      });
      request.send(fileReader.result);
    };

    request.upload.onprogress = function renderProgress(event) {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        $('.progress-bar-striped').css({ width: `${percentComplete}%` });
      }
    };

    request.onreadystatechange = function success() {
      if (request.readyState === 4 && request.status === 201) {
        const uploadedFile = {
          fileName: file.name,
          fileToken: JSON.parse(request.response).upload.token,
        };

        $this.setState(
          {
            fileList: $this.state.fileList.concat(uploadedFile),
            fileInProgress: null,
          },
        );
      }
    };

    request.onerror = function error() {
      $this.setState({
        fileInProgress: null,
        errorList: [gettext('Something went wrong. Please try again later.')],
      });
    };

    request.onabort = function abortUpload() {
      $this.setState({
        fileInProgress: null,
      });
    };
  }

  render() {
    return (
      <div className="file-container">
        <div className="row">
          <div className="col-sm-12">
            <div className="form-group">
              <label htmlFor="attachment">{gettext('Add Attachment')}
                <span> {gettext('(Optional)')}</span>
              </label>
              <input
                id="attachment"
                className="file file-loading"
                type="file"
                accept=".pdf, .jpeg, .png, .jpg, .gif"
                onChange={this.uploadFile}
              />
            </div>
          </div>
        </div>
        <div className="progress-container">
          {this.state.fileInProgress &&
          <ShowProgress
            fileName={this.state.fileInProgress}
            request={this.state.currentRequest}
          />
          }
        </div>
        <div className="uploaded-files">
          {
            this.state.fileList.map(file =>
              (<div key={file.fileToken} className="row">
                <div className="col-sm-12">
                  <span className="file-name">{file.fileName}</span>
                  <span className="file-action remove-upload">
                    <button className="btn btn-link" id={file.fileToken} onClick={this.removeFile}>{gettext('Remove file')}</button>
                  </span>
                </div>
              </div>),
            )
          }
        </div>
      </div>
    );
  }
}

FileUpload.propTypes = {
  setErrorState: PropTypes.func.isRequired,
  zendeskApiHost: PropTypes.string.isRequired,
  accessToken: PropTypes.string.isRequired,
};
export default FileUpload;
