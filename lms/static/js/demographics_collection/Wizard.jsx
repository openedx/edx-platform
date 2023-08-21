/* global gettext */
import React from 'react';
// eslint-disable-next-line import/no-extraneous-dependencies
import isFunction from 'lodash/isFunction';

const Page = ({children}) => children;
// eslint-disable-next-line react/function-component-definition
const Header = () => null;
// eslint-disable-next-line react/function-component-definition
const Closer = () => null;
// eslint-disable-next-line react/function-component-definition
const ErrorPage = () => null;
export default class Wizard extends React.Component {
    constructor(props) {
        super(props);
        this.findSubComponentByType = this.findSubComponentByType.bind(this);
        this.handleNext = this.handleNext.bind(this);
        this.state = {
            currentPage: 1,
            totalPages: 0,
            pages: [],
            // eslint-disable-next-line react/no-unused-state
            wizardContext: {},
        };

        this.wizardComplete = this.wizardComplete.bind(this);
    }

    componentDidMount() {
        const pages = this.findSubComponentByType(Wizard.Page.name);
        const totalPages = pages.length;
        const wizardContext = this.props.wizardContext;
        const closer = this.findSubComponentByType(Wizard.Closer.name)[0];
        pages.push(closer);
        // eslint-disable-next-line react/no-unused-state
        this.setState({pages, totalPages, wizardContext});
    }

    handleNext() {
        if (this.state.currentPage < this.props.children.length) {
            this.setState(prevState => ({currentPage: prevState.currentPage + 1}));
        }
    }

    findSubComponentByType(type) {
        return React.Children.toArray(this.props.children).filter(child => child.type.name === type);
    }

    // this needs to handle the case of no provided header
    // eslint-disable-next-line react/sort-comp
    renderHeader() {
        const header = this.findSubComponentByType(Wizard.Header.name)[0];
        return header.props.children({currentPage: this.state.currentPage, totalPages: this.state.totalPages});
    }

    renderPage() {
        if (this.state.totalPages) {
            const page = this.state.pages[this.state.currentPage - 1];
            if (page.type.name === Wizard.Closer.name) {
                return page.props.children;
            }

            if (isFunction(page.props.children)) {
                return page.props.children({wizardConsumer: this.props.wizardContext});
            } else {
                return page.props.children;
            }
        }
        return null;
    }

    // this needs to handle the case of no provided errorPage
    renderError() {
        const errorPage = this.findSubComponentByType(Wizard.ErrorPage.name)[0];
        return (
            <div className="wizard-container" role="dialog" aria-label={gettext('demographics questionnaire')}>
                <div className="wizard-header">
                    {errorPage.props.children}
                </div>
                <div className="wizard-footer justify-content-end h-100 d-flex flex-column">
                    {/* eslint-disable-next-line react/button-has-type, react/no-unknown-property */}
                    <button className="wizard-button colored" arial-label={gettext('close questionnaire')} onClick={this.props.onWizardComplete}>{gettext('Close')}</button>
                </div>
            </div>
        );
    }

    /**
   * Utility method that helps determine if the learner is on the final page of the modal.
   */
    onFinalPage() {
        return this.state.pages.length === this.state.currentPage;
    }

    /**
   * Utility method for closing the modal and returning the learner back to the Course Dashboard.
   * If a learner is on the final page of the modal, meaning they have answered all of the
   * questions, clicking the "Return to my dashboard" button will also dismiss the CTA from the
   * course dashboard.
   */
    async wizardComplete() {
        if (this.onFinalPage()) {
            this.props.dismissBanner();
        }

        this.props.onWizardComplete();
    }

    render() {
        const finalPage = this.onFinalPage();
        if (this.props.error) {
            return this.renderError();
        }
        return (
            <div className="wizard-container" role="dialog" aria-label={gettext('demographics questionnaire')}>
                <div className="wizard-header mb-4">
                    {this.state.totalPages >= this.state.currentPage && this.renderHeader()}
                </div>
                {this.renderPage()}
                <div className="wizard-footer justify-content-end h-100 d-flex flex-column">
                    {/* eslint-disable-next-line react/button-has-type */}
                    <button className={`wizard-button ${finalPage && 'colored'}`} onClick={this.wizardComplete} aria-label={gettext('finish later')}>{finalPage ? gettext('Return to my dashboard') : gettext('Finish later')}</button>
                    {/* eslint-disable-next-line react/button-has-type */}
                    <button className="wizard-button colored" hidden={finalPage} onClick={this.handleNext} aria-label={gettext('next page')}>{gettext('Next')}</button>
                </div>
            </div>
        );
    }
}

Wizard.Page = Page;
Wizard.Header = Header;
Wizard.Closer = Closer;
Wizard.ErrorPage = ErrorPage;
