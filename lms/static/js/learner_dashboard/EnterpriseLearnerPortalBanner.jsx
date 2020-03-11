import React, { Component } from 'react';
import { getAuthenticatedUser } from '@edx/frontend-auth';
import { getLearnerPortalLinks } from '@edx/frontend-enterprise';
import { StatusAlert } from '@edx/paragon';

import apiClient from '../apiClient';

const LOCAL_STORAGE_KEY = 'has-viewed-enterprise-learner-portal-banner';

function getAlertHtml(learnerPortalLinks) {
  let html = '';
  for (let i = 0; i < learnerPortalLinks.length; i += 1) {
    const link = learnerPortalLinks[i];
    html += `<div class="copy-content">
      ${link.title} has a dedicated page where you can see all of your sponsored courses.
      Go to <a href="${link.url}">your learner portal</a>.
    </div>`;
  }
  return html;
}

function setViewedBanner() {
  window.localStorage.setItem(LOCAL_STORAGE_KEY, true);
}

function hasViewedBanner() {
  return window.localStorage.getItem(LOCAL_STORAGE_KEY) != null;
}

class EnterpriseLearnerPortalBanner extends Component {
  constructor(props) {
    super(props);

    this.onClose = this.onClose.bind(this);

    this.state = {
      open: false,
      alertHtml: '',
    };
  }

  componentDidMount() {
    if (!hasViewedBanner()) {
      const authenticatedUser = getAuthenticatedUser();
      getLearnerPortalLinks(apiClient, authenticatedUser).then((learnerPortalLinks) => {
        this.setState({
          open: true,
          alertHtml: getAlertHtml(learnerPortalLinks),
        });
      });
    }
  }

  onClose() {
    this.setState({ open: false });
    setViewedBanner();
  }

  render() {
    const { alertHtml, open } = this.state;

    if (open && alertHtml) {
      return (
        <div className="edx-enterprise-learner-portal-banner-wrapper">
          <StatusAlert
            className={['edx-enterprise-learner-portal-banner']}
            open={open}
            // eslint-disable-next-line react/no-danger
            dialog={(<span dangerouslySetInnerHTML={{ __html: alertHtml }} />)}
            onClose={this.onClose}
          />
        </div>
      );
    }

    return null;
  }
}

export { EnterpriseLearnerPortalBanner }; // eslint-disable-line import/prefer-default-export
