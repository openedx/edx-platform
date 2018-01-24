import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button  } from '@edx/paragon/static';

import ExperimentalCarousel from './ExperimentalCarousel.jsx';

// https://openedx.atlassian.net/browse/LEARNER-3583

export class UpsellExperimentModal extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            isOpen: true,
        }
    }

    render() {
        const slides = [
            (<div>
                <div className="my-stats-introduction">My Stats introduces new personalized views that help you track your progress towards completing your course!</div>
                <div className="my-stats-slide-header">With My Stats you will see your:</div>
                <ul className="upsell-modal-checkmark-group">
                    <li><span className="fa fa-check upsell-modal-checkmark" aria-hidden="true" />Course Activity Streak (log in every week to keep your streak alive)</li>
                    <li><span className="fa fa-check upsell-modal-checkmark" aria-hidden="true" />Grade Progress (see how you're tracking towards a passing grade)</li>
                    <li><span className="fa fa-check upsell-modal-checkmark" aria-hidden="true" />Discussion Forum Engagements (top learners use the forums - how do you measure up?)</li>
                </ul>
            </div>),
            (<div>
                <div className="slide-header"><b>Course Activity Streak</b></div>
                <span className="course-activity-streak-information">Did you know the learners most likely to complete a course log in every week? Let us help you track your weekly streak - log in every week and learn something new! You can also see how many of the other learners in your course logged in this week.</span>
                <img
                    className="feature-screenshot"
                    src="https://prod-edx-mktg-edit.edx.org/sites/default/files/week_streak.png"
                    alt=""
                />
            </div>),
            (<div>
                <div className="slide-header"><b>Grade Progress</b></div>
                <span className="grade-progress-information">Wonder how you're doing in the course so far? We can not only show you all your grades, and how much each assignment is worth, but also upcoming graded assignments. This is a great way to track what you might need to work on for a final exam.</span>
                <img
                    className="feature-screenshot"
                    src="https://prod-edx-mktg-edit.edx.org/sites/default/files/grading.png"
                    alt=""
                />
            </div>),
            (<div>
                <div className="slide-header"><b>Discussion engagements</b></div>
                <span className="discussion-engagements-information">A large percentage of successful learners are engaged on the discussion forums. Compare your forum stats to previous graduates!</span>
                <img
                    className="feature-screenshot"
                    src="https://prod-edx-mktg-edit.edx.org/sites/default/files/discussions.png"
                    alt=""
                />
            </div>),
        ];
        const body = (
            <div>
                <ExperimentalCarousel id="upsell-modal" slides={slides} />
                <img
                    className="upsell-certificate"
                    src="https://courses.edx.org/static/images/edx-verified-mini-cert.png"
                    alt=""
                />
            </div>
        );
        const { buttonDestinationURL } = this.props;
        return (
            <Modal
                open={this.state.isOpen}
                className="upsell-modal"
                title={"My Stats"}
                onClose={() => {}}
                body={body}
                buttons={[
                    (<Button
                        label={"Upgrade ($100 USD)"}
                        display={"Upgrade ($100 USD)"}
                        buttonType="success"
                        // unfortunately, Button components don't have an href component
                        onClick={() => window.location = buttonDestinationURL}
                    />),
                ]}
            />
        );
    }
}

UpsellExperimentModal.propTypes = {
    buttonDestinationURL: PropTypes.string.isRequired,
};