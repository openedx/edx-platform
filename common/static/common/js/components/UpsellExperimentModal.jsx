import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button  } from '@edx/paragon/static';

import Carousel from './Carousel.jsx';

// https://openedx.atlassian.net/browse/LEARNER-3583

export class UpsellExperimentModal extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            isOpen: this.props.isOpen,
        }
    }

    render() {
        const {
            slides,
            modalTitle,
            buttonLabel,
            buttonDisplay,
            buttonDestinationURL,
        } = this.props;
        const body = (
            <div>
                <Carousel id="upsell-modal" slides={slides} />
                <img
                    className="upsell-certificate"
                    src="https://courses.edx.org/static/images/edx-verified-mini-cert.png"
                    alt=""
                />
            </div>
        );
        return (
            <Modal
                open={this.state.isOpen}
                className="upsell-modal"
                title={modalTitle}
                onClose={() => {}}
                body={body}
                buttons={[
                    (<Button
                        label={buttonLabel}
                        display={buttonDisplay}
                        buttonType="success"
                        // unfortunately, Button components don't have an href component
                        onClick={() => window.location = buttonDestinationURL}
                    />),
                ]}
            />
        );
    }
}

UpsellExperimentModal.defaultProps = {
    isOpen: true,
};

UpsellExperimentModal.propTypes = {
    isOpen: PropTypes.bool,
    slides: PropTypes.arrayOf(PropTypes.node).isRequired,
    modalTitle: PropTypes.string.isRequired,
    buttonLabel: PropTypes.string.isRequired,
    buttonDisplay: PropTypes.string.isRequired,
    buttonDestinationURL: PropTypes.string.isRequired,
};
