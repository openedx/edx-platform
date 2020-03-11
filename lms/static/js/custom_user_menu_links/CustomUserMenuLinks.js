import { getAuthenticatedUser } from '@edx/frontend-auth';
import { getLearnerPortalLinks } from '@edx/frontend-enterprise';

import apiClient from '../apiClient';

function CustomUserMenuLinks() {
  const authenticatedUser = getAuthenticatedUser();
  // Inject enterprise learner portal links
  getLearnerPortalLinks(apiClient, authenticatedUser).then((learnerPortalLinks) => {
    const $dashboardLink = $('#user-menu .dashboard');
    const classNames = 'mobile-nav-item dropdown-item dropdown-nav-item';
    for (let i = 0; i < learnerPortalLinks.length; i += 1) {
      const link = learnerPortalLinks[i];

      $dashboardLink.after( // xss-lint: disable=javascript-jquery-insertion
        `<div class="${classNames}"><a href="${link.url}" role="menuitem">${link.title} Dashboard</a></div>`,
      );
    }
  });
}

export { CustomUserMenuLinks }; // eslint-disable-line import/prefer-default-export
