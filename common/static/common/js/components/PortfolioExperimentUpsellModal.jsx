import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button  } from '@edx/paragon/static';

import ExperimentalCarousel from './ExperimentalCarousel.jsx';

// https://openedx.atlassian.net/browse/LEARNER-3926

export class PortfolioExperimentUpsellModal extends React.Component {
    constructor(props) {
        super(props);

        this.state = { isOpen: true };
    }

    render() {
        const slides = [
            (<div className='portfolio-slide-0'>
                <p className='description'>Upgrade to access new content: a guide for building an online portfolio and creating your first project.</p>
                <div className='checkmark-group-header'>By following the guide you will:</div>
                <ul className='upsell-modal-checkmark-group'>
                    <li><span className='fa fa-check upsell-modal-checkmark' aria-hidden='true' />Use your new coding skills</li>
                    <li><span className='fa fa-check upsell-modal-checkmark' aria-hidden='true' />Begin to build your portfolio</li>
                    <li><span className='fa fa-check upsell-modal-checkmark' aria-hidden='true' />Share what you can do!</li>
                </ul>
            </div>),
            (<div className='portfolio-slide-1'>
                <h3 className='slide-header'><b>Use Your New Coding Skills</b></h3>
                <p>Want to practice what you've learned? We'll give you the project idea to create your own portfolio. Get creative!</p>
            </div>),
            (<div className='portfolio-slide-2'>
                <h3 className='slide-header'><b>Build Your Portfolio</b></h3>
                <p>Apply your knowledge and show them you can code - this project is the perfect start to your portfolio.</p>
            </div>),
            (<div className='portfolio-slide-3'>
                <h3 className='slide-header'><b>Share What You Can Do</b></h3>
                <p>Get tips on where to store your project and the best way to share it with employers.</p>
            </div>),
        ];

        const body = (
            <div>
                <ExperimentalCarousel id='portfolio-upsell-modal' slides={slides} />
                <img
                    className="upsell-certificate"
                    src="https://courses.edx.org/static/images/edx-verified-mini-cert.png"
                    alt="Sample verified certificate"
                />
            </div>
        );

        return (
            <Modal
                open={this.state.isOpen}
                className='portfolio-upsell-modal'
                title={'Portfolio Builder: My First Project'}
                onClose={() => {}}
                body={body}
                buttons={[
                    (<Button
                        label={'Upgrade ($100 USD)'}
                        display={'Upgrade ($100 USD)'}
                        buttonType='success'
                        // unfortunately, Button components don't have an href attribute
                        onClick={() => {}}
                    />),
                ]}
            />
        );
    }
}
