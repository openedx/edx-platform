/* global gettext */
import React from 'react';
import Cookies from 'js-cookie';
import { DemographicsCollectionModal } from './DemographicsCollectionModal';

export class DemographicsCollectionBanner extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            modalOpen: false,
            hideBanner: false
        }

        this.dismissBanner = this.dismissBanner.bind(this);
    }

    /**
   * Utility function that controls hiding the CTA from the Course Dashboard where appropriate.
   * This can be called one of two ways - when a user clicks the "dismiss" button on the CTA
   * itself, or when the learner completes all of the questions within the modal.
   * 
   * The dismiss button itself is nested inside of an <a>, so we need to call stopPropagation()
   * here to prevent the Modal from _also_ opening when the Dismiss button is clicked.
   */
    async dismissBanner(e) {
    // Since this function also doubles as a callback in the Modal, we check if e is null/undefined
    // before calling stopPropagation()
        if (e) {
            e.stopPropagation();
        }

        const requestOptions = {
            method: 'PATCH',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': Cookies.get('csrftoken'),
            },
            body: JSON.stringify({
                show_call_to_action: false,
            })
        };

        await fetch(`${this.props.lmsRootUrl}/api/demographics/v1/demographics/status/`, requestOptions);
        // No matter what the response is from the API call we always allow the learner to dismiss the 
        // banner when clicking the dismiss button
        this.setState({ hideBanner: true });
    }

    render() {
        if (!(this.state.hideBanner)) {
            return (
                <div>
                    <a id="demographics-banner-link" className="btn" onClick={() => this.setState({ modalOpen: true })}>
                        <div
                            className="demographics-banner d-flex justify-content-lg-between flex-row py-1 px-2 mb-2 mb-lg-4"
                            role="dialog"
                            aria-modal="false"
                            aria-label="demographics questionnaire pitch"
                        >
                            <div className="d-flex justify-content-left align-items-lg-center flex-column flex-lg-row  w-100">
                                <img className="demographics-banner-icon d-none d-lg-inline-block" src={this.props.bannerLogo} alt="" aria-hidden="true" />
                                <div className="demographics-banner-prompt d-inline-block font-weight-bold text-white mr-4 py-3 px-2 px-lg-3">
                                    {gettext('Want to make edX better for everyone?')}
                                </div>
                                <button className="demographics-banner-btn d-flex align-items-center bg-white font-weight-bold border-0 py-2 px-3 mx-2 mb-3 m-lg-0 shadow justify-content-center">
                                    <span className="fa fa-thumbs-up px-2" aria-hidden="true"></span>
                                    {gettext('Get started')}
                                </button>
                            </div>
                            <div className="demographics-dismiss-container md-flex justify-content-right align-self-start align-self-lg-center  ml-lg-auto">
                                <button type="button" className="demographics-dismiss-btn btn btn-default px-0" id="demographics-dismiss" aria-label="close">
                                    <i className="fa fa-times-circle text-white px-2" aria-hidden="true" onClick={this.dismissBanner}></i>
                                </button>
                            </div>
                        </div>
                    </a>
                    <div>
                        {this.state.modalOpen &&
              <DemographicsCollectionModal
                  {...this.props}
                  user={this.props.user}
                  open={this.state.modalOpen}
                  closeModal={() => this.setState({ modalOpen: false })}
                  dismissBanner={this.dismissBanner}
              />
                        }
                    </div>
                </div>
            )
        } else {
            return null;
        }
    }
}
