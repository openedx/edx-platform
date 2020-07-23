import React from 'react';

const Page = ({ children }) => children || null;
const Header = ({ children }) => children || null;
const Closer = ({ children }) => children || null;

export class Wizard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      currentPage: this.props.setPage || 1,
      totalPages: 0,
      pages: [],
    }
    this.handleNext = this.handleNext.bind(this);
    this.findSubComponentByType = this.findSubComponentByType.bind(this);
    this.renderPages = this.renderPages.bind(this);
  }

  handleNext() {
    if (this.state.currentPage < this.props.children.length) {
      this.setState(prevState => ({ currentPage: prevState.currentPage + 1 }))
    }
  }

  findSubComponentByType(type) {
    return this.props.children.filter((child) => child.type.name === type)
  }

  componentDidMount() {
    const pages = this.findSubComponentByType('Page')
    const totalPages = pages.length;
    const closer = this.findSubComponentByType("Closer")[0];
    if (closer) {
      pages.push(closer);
    }
    this.setState({ pages, totalPages })
  }

  renderPages() {
    return this.state.pages.find((page, i) => i + 1 === this.state.currentPage);
  }

  renderHeader() {
    const header = this.findSubComponentByType("Header")[0];
    return header.props.children({ currentPage: this.state.currentPage, totalPages: this.state.totalPages })
  }

  render() {
    return (
      <div className="wizard-container">
        <div className="wizard-header">
          {this.state.totalPages >= this.state.currentPage && this.renderHeader()}
        </div>
        <div>
          {this.renderPages()}
        </div>
        <br />
        <div className="wizard-footer">
          <button className="wizard-button" onClick={() => { }}>Finish Later</button>
          <button className="wizard-button blue" hidden={this.state.pages.length === this.state.currentPage} onClick={this.handleNext}>Next</button>
        </div>
      </div>
    );
  }
}

Wizard.Page = Page;
Wizard.Header = Header;
Wizard.Closer = Closer;