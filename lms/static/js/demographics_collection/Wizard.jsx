import React from 'react';
import isFunction from 'lodash/isFunction';

const Page = ({ children }) => children;
const Header = () => null;
const Closer = () => null;
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
      wizardContext: {},
    }
  }

  componentDidMount() {
    const pages = this.findSubComponentByType('Page');
    const totalPages = pages.length;
    const wizardContext = this.props.wizardContext;
    const closer = this.findSubComponentByType('Closer')[0];
    pages.push(closer);
    this.setState({ pages, totalPages, wizardContext });
  }

  handleNext() {
    if (this.state.currentPage < this.props.children.length) {
      this.setState(prevState => ({ currentPage: prevState.currentPage + 1 }))
    }
  }

  findSubComponentByType(type) {
    return this.props.children.filter((child) => child.type.name === type)
  }

  // this needs to handle the case of no provided header
  renderHeader() {
    const header = this.findSubComponentByType('Header')[0];
    return header.props.children({ currentPage: this.state.currentPage, totalPages: this.state.totalPages })
  }

  renderPage() {
    if (this.state.totalPages) {
      const page = this.state.pages[this.state.currentPage - 1];
      if(page.type.name === 'Closer') {
        return page.props.children;
      }

      if (isFunction(page.props.children)) {
        return page.props.children({ wizardConsumer: this.props.wizardContext });
      } else {
        return page.props.children;
      }
    }
    return null;
  }

  // this needs to handle the case of no provided errorPage
  renderError() {
    const errorPage = this.findSubComponentByType('ErrorPage')[0];
    return (
      <div className="wizard-container">
        <div className="wizard-header">
          {errorPage.props.children}
        </div>
        <div className="wizard-footer justify-content-end h-100 d-flex flex-column">
          <button className="wizard-button blue" onClick={this.props.onWizardComplete}>Close</button>
        </div>
      </div>
    )
  }

  render() {
    const finalPage = this.state.pages.length === this.state.currentPage;
    console.log(this.props.error)
    if(this.props.error) {
      return this.renderError();
    }
    return (
      <div className="wizard-container">
        <div className="mb-3">
          {this.state.totalPages >= this.state.currentPage && this.renderHeader()}
        </div>
        {this.renderPage()}
        <div className="wizard-footer justify-content-end h-100 d-flex flex-column">
          <button className={`wizard-button ${finalPage && 'blue'}`} onClick={this.props.onWizardComplete}>{finalPage ? "Return to my dashboard" : "Finish later"}</button>
          <button className="wizard-button blue" hidden={finalPage} onClick={this.handleNext}>Next</button>
        </div>
      </div>
    );
  }
}

Wizard.Page = Page;
Wizard.Header = Header;
Wizard.Closer = Closer;
Wizard.ErrorPage = ErrorPage;