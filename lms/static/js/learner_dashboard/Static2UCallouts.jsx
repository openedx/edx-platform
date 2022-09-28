/* global gettext */
import React from 'react';

class Static2UCallouts extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      show2uLobs: false,
    };
  }

  componentDidMount() {
    const optimizely = window["optimizely"] || [];
    optimizely.push({
      "type": "user",
      "attributes": {
        "isEnterpriseUser": this.props.isEnterpriseUser.toString(),
      }
    });
    optimizely.push({
      type: "page",
      pageName: "van_1097_merchandise_2u_lobs_on_dashboard"
    });
    const experimentId = '22164741776';
    this.timer = setTimeout(() => {
      const selectedVariant = optimizely.get("state").getVariationMap()[experimentId];
      if (selectedVariant?.name === 'dashboard_with_2u_lobs'){
        this.setState({
          show2uLobs: true,
        })
      }
    }, 500 );
  }

  componentWillUnmount() {
    clearTimeout(this.timer);
  }

  render() {
    return (
      this.state.show2uLobs && (
        <div className="static-callouts-main">
          <div className="static-callouts-header">
            <div className="static-callouts-heading">
              <h2 className="static-callouts-heading-black">
                {gettext('More opportunities for you')}
                <h2 className="static-callouts-heading-red">{gettext(' to learn')}</h2>
              </h2>
            </div>
            <p className="static-callouts-subheading">
              {gettext('We\'ve added 500+ learning opportunities to create one of the world\'s most '
                + 'comprehensive free-to-degree online learning platforms.')}
            </p>
          </div>
          <div className="static-callouts-cards">
            <a
              href={`${this.props.executiveEducationUrl}?vanguards_click=execed`}
              target="_blank"
              rel="noopener noreferrer"
              className={
                this.props.countryCode !== 'US' ? (
                  'static-callouts-card static-callouts-card-no-bootcamp'
                ) : 'static-callouts-card'
              }
            >
              <div className="static-callouts-card-badge">
                New
              </div>
              <h3 className="static-callouts-card-heading">
                Executive Education
              </h3>
              <div className="static-callouts-card-description">
                Short courses to develop leadership skills
                <svg
                  width="30"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  role="img"
                  focusable="false"
                  aria-hidden="true"
                >
                  <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" fill="currentColor" />
                </svg>
              </div>
            </a>
            <div
              className={
                this.props.countryCode !== 'US' ? (
                  'static-callouts-cards-divider static-callouts-cards-divider-no-bootcamp'
                ) : 'static-callouts-cards-divider'
              }
            >
              <svg viewBox="2 0 25 95">
                <path d="M 0 120 l 30 -150" stroke="#EAE6E5" strokeWidth="4" fill="none" />
              </svg>
            </div>
            <a
              href={`${this.props.mastersDegreeUrl}?vanguards_click=masters`}
              target="_blank"
              rel="noopener noreferrer"
              className={
                this.props.countryCode !== 'US' ? (
                  'static-callouts-card static-callouts-card-no-bootcamp'
                ) : 'static-callouts-card'
              }
            >
              <div className="static-callouts-card-badge">
                New
              </div>
              <h3 className="static-callouts-card-heading">
                Master’s Degrees
              </h3>
              <div className="static-callouts-card-description">
                Online degree programs from top universities
                <svg
                  width="30"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  role="img"
                  focusable="false"
                  aria-hidden="true"
                >
                  <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" fill="currentColor" />
                </svg>
              </div>
            </a>
            <div
              className={
                this.props.countryCode !== 'US' ? (
                  'static-callouts-cards-divider static-callouts-cards-divider-no-bootcamp'
                ) : 'static-callouts-cards-divider static-callouts-cards-break'
              }
            >
              <svg viewBox="2 0 25 95">
                <path d="M 0 120 l 30 -150" stroke="#EAE6E5" strokeWidth="4" fill="none" />
              </svg>
            </div>
            <a
              href={`${this.props.bachelorsDegreeUrl}?vanguards_click=bachelors`}
              target="_blank" rel="noopener noreferrer"
              className={
                this.props.countryCode !== 'US' ? (
                  'static-callouts-card static-callouts-card-no-bootcamp'
                ) : 'static-callouts-card'
              }
            >
              <div className="static-callouts-card-badge">
                New
              </div>
              <h3 className="static-callouts-card-heading">
                Bachelor’s Degrees
              </h3>
              <div className="static-callouts-card-description">
                Begin or complete a degree; fully online
                <svg
                  width="30"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  role="img"
                  focusable="false"
                  aria-hidden="true"
                >
                  <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" fill="currentColor" />
                </svg>
              </div>
            </a>
            {this.props.countryCode === 'US' && (
              <div className="static-callouts-cards-divider">
                <svg viewBox="2 0 25 95">
                  <path d="M 0 120 l 30 -150" stroke="#EAE6E5" strokeWidth="4" fill="none" />
                </svg>
              </div>
            )}
            {this.props.countryCode === 'US' && (
              <a href={`${this.props.bootCampsUrl}?vanguards_click=bootcamps`}
                 target="_blank"
                 className="static-callouts-card">
                <div className="static-callouts-card-badge">
                  New
                </div>
                <h3 className="static-callouts-card-heading">
                  Boot Camps
                </h3>
                <div className="static-callouts-card-description">
                  Intensive, hands-on, project-based training
                  <svg
                    width="30"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    role="img"
                    focusable="false"
                    aria-hidden="true"
                  >
                    <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" fill="currentColor" />
                  </svg>
                </div>
              </a>
            )}
          </div>
        </div>)
      );
  }
}

export { Static2UCallouts };
