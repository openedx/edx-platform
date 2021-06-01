/* global gettext */
import React from 'react';
import FocusLock, { AutoFocusInside } from 'react-focus-lock';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

class EnterpriseLearnerPortalModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isModalOpen: false,
    };

    this.openModal = this.openModal.bind(this);
    this.closeModal = this.closeModal.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.handleEsc = this.handleEsc.bind(this);
  }

  componentDidMount() {
    const storageKey = `enterprise_learner_portal_modal__${this.props.enterpriseCustomerUUID}`;
    const hasViewedModal = window.sessionStorage.getItem(storageKey);
    if (!hasViewedModal) {
      this.openModal();
      document.addEventListener('mousedown', this.handleClick, false);
      window.sessionStorage.setItem(storageKey, true);
      document.addEventListener('keydown', this.handleEsc, false);
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.state.isModalOpen !== prevState.isModalOpen) {
      if (this.state.isModalOpen) {
        // add a class here to prevent scrolling on anything that is not the modal
        document.body.classList.add('modal-open');
      } else {
        // remove the class to allow the dashboard content to scroll
        document.body.classList.remove('modal-open');
      }
    }
  }

  componentWillUnmount() {
    // remove the class to allow the dashboard content to scroll
    document.body.classList.remove('modal-open');
    document.removeEventListener('mousedown', this.handleClick, false);
    document.removeEventListener('keydown', this.handleEsc, false);
  }

  handleClick(e) {
    if (this.modalRef && this.modalRef.contains(e.target)) {
      // click is inside modal, don't close it
      return;
    }

    this.closeModal();
  }

  handleEsc(e) {
    const { key } = e;
    if (key === "Escape") {
      this.closeModal();
    }
  }

  closeModal() {
    this.setState({
      isModalOpen: false,
    });
  }

  openModal() {
    this.setState({
      isModalOpen: true,
    });
  }

  getLearnerPortalUrl() {
    const baseUrlWithSlug = `${this.props.enterpriseLearnerPortalBaseUrl}/${this.props.enterpriseCustomerSlug}`;
    return `${baseUrlWithSlug}?utm_source=lms_dashboard_modal`;
  }

  render() {
    if (!this.state.isModalOpen) {
      return null;
    }

    return (
      <div
        role="dialog"
        className="modal-wrapper d-flex align-items-center justify-content-center"
      >
        <FocusLock>
          <div
            className="modal-content p-4 bg-white"
            ref={(node) => { this.modalRef = node; }}
          >
            <div className="mb-3 font-weight-bold">
              {StringUtils.interpolate(
                gettext('You have access to the {enterpriseName} dashboard'),
                {
                  enterpriseName: this.props.enterpriseCustomerName,
                }
              )}
            </div>
            <p>
              {StringUtils.interpolate(
                gettext('To access the courses available to you through {enterpriseName}, visit the {enterpriseName} dashboard.'),
                {
                  enterpriseName: this.props.enterpriseCustomerName,
                }
              )}
            </p>
            <div className="mt-4 d-flex align-content-center justify-content-end">
              <button
                className="btn-link mr-3"
                onClick={() => this.closeModal()}
              >
                {gettext('Cancel')}
              </button>
              <AutoFocusInside>
                <a
                  href={this.getLearnerPortalUrl()}
                  className="btn btn-primary"
                >
                  {gettext('Go to dashboard')}
                </a>
              </AutoFocusInside>
            </div>
          </div>
        </FocusLock>
      </div>
    );
  }
}

export { EnterpriseLearnerPortalModal }; 
