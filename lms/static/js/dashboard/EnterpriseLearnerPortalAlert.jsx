import PropTypes from 'prop-types';
import React, { createContext, useMemo } from 'react';
import ReactDOM from 'react-dom';
import Cookies from 'universal-cookie';
import FocusLock from 'react-focus-lock';
import { Modal } from '@edx/paragon/static'

class Portal extends React.Component {
  constructor(props) {
    super(props);
    this.rootName = 'paragon-portal-root';
    // istanbul ignore if
    if (typeof document === 'undefined') {
      this.rootElement = null;
    } else if (document.getElementById(this.rootName)) {
      this.rootElement = document.getElementById(this.rootName);
    } else {
      const rootElement = document.createElement('div');
      rootElement.setAttribute('id', this.rootName);
      this.rootElement = document.body.appendChild(rootElement);
    }
  }

  render() {
    // istanbul ignore else
    if (this.rootElement) {
      return ReactDOM.createPortal(
        this.props.children,
        this.rootElement,
      );
    }
    // istanbul ignore next
    return null;
  }
}

Portal.propTypes = {
  children: PropTypes.node.isRequired,
};

// istanbul ignore next
const ModalBackdrop = ({ onClick }) => (

  // Focus lock is handling the keyboard eventfor us. Though adding a role="button"
  // would be appropriate, modal dialogs provide their own close button and this
  // would create a duplicative control.
  // eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events
  <div className="pgn__modal-backdrop" onClick={onClick} />
);

ModalBackdrop.propTypes = {
  onClick: PropTypes.func,
};

ModalBackdrop.defaultProps = {
  onClick: undefined,
};

// istanbul ignore next
const ModalContentContainer = ({ children }) => (
  <div className="pgn__modal-content-container">{children}</div>
);

ModalContentContainer.propTypes = {
  children: PropTypes.node,
};

ModalContentContainer.defaultProps = {
  children: null,
};

/**
 * The ModalLayer should be used for any component that wishes to engage the user
 * in a "mode" where a layer on top of the application is interactive while the
 * rest of the application is made non-interactive. The assumption made by this
 * component is that if a modal object is visible then it is "enabled"
 */
const ModalLayer = ({
  children, onClose, isOpen, isBlocking,
}) => {
  if (!isOpen) {
    return null;
  }

  const onClickOutside = !isBlocking ? onClose : null;

  return (
      <Portal>
        <FocusLock
          scrollLock
          enabled={isOpen}
          onEscapeKey={onClose}
          onClickOutside={onClickOutside}
          className="pgn__modal-layer"
        >
          <ModalContentContainer>
            <ModalBackdrop onClick={onClickOutside} />
            {children}
          </ModalContentContainer>
        </FocusLock>
      </Portal>
  );
};

ModalLayer.propTypes = {
  children: PropTypes.node.isRequired,
  onClose: PropTypes.func.isRequired,
  isOpen: PropTypes.bool.isRequired,
  isBlocking: PropTypes.bool,
};

ModalLayer.defaultProps = {
  isBlocking: false,
};

class EnterpriseLearnerPortalAlert extends React.Component {
    constructor(props) {
        super(props);
        this.closeModal = this.closeModal.bind(this);

        this.cookies = new Cookies();
        this.modalDismissedCookieName = "ENTERPRISE_LEARNER_PORTAL_MODAL_DISMISSED";
        const learnerPortalModalDismissed = this.cookies.get(this.modalDismissedCookieName);
        this.state = { open: true };
    }

    closeModal() {
        this.cookies.set(
            this.modalDismissedCookieName,
            true,
            { SameSite: 'strict' },
        );
        this.setState({ open: false });
    }

    render() {
        const customerName = this.props.enterpriseCustomerName;
        const modalTitle = `You have access to the ${customerName} dashboard`;
        const modalBody = `To access the courses available to you through ${customerName}, visit the ${customerName} dashboard.`;
        return (
            <ModalLayer
                isOpen={this.state.open}
                isBlocking={true}
                onClose={this.closeModal}
            >
                <div role="dialog" aria-label="My dialog" className="mw-sm p-5 bg-white mx-auto my-5">
                    <Modal
                        body={modalBody}
                        title={modalTitle}
                        onClose={this.closeModal}
                    />
                </div>
            </ModalLayer>
        );
    }
}

EnterpriseLearnerPortalAlert.propTypes = {
    enterpriseCustomerName: PropTypes.string.isRequired,
    enterpriseCustomerSlug: PropTypes.string.isRequired,
};

export { EnterpriseLearnerPortalAlert };
