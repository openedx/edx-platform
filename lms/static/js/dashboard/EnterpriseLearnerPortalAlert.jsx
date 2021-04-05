import PropTypes from 'prop-types';
import React from 'react';
import Cookies from 'universal-cookie';

import { Modal } from '@edx/paragon/static'; // Does this need to be static?


class EnterpriseLearnerPortalAlert extends React.Component {
    constructor(props) {
        super(props);
        this.closeModal = this.closeModal.bind(this);

        this.cookies = new Cookies();
        this.modalDismissedCookieName = "ENTERPRISE_LEARNER_PORTAL_MODAL_DISMISSED";
        const learnerPortalModalDismissed = this.cookies.get(this.modalDismissedCookieName);
        this.state = { open: !learnerPortalModalDismissed };
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
            <Modal
                open={this.state.open}
                title={modalTitle}
                body={modalBody}
                onClose={this.closeModal}
            />
        );
    }
}

EnterpriseLearnerPortalAlert.propTypes = {
    enterpriseCustomerName: PropTypes.string.isRequired,
    enterpriseCustomerSlug: PropTypes.string.isRequired,
};

export { EnterpriseLearnerPortalAlert };
