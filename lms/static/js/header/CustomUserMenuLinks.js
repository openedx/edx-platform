import { getAuthenticatedAPIClient } from '@edx/frontend-auth';
import { getLearnerPortalLinks } from '@edx/frontend-enterprise';
import { NewRelicLoggingService } from '@edx/frontend-logging';

function CustomUserMenuLinks() {
  const apiClient = getAuthenticatedAPIClient({
    appBaseUrl: 'https://lms.edxdev.org',
    authBaseUrl: 'https://lms.edxdev.org',
    loginUrl: 'https://lms.edxdev.org/login',
    logoutUrl: 'https://lms.edxdev.org/logout',
    csrfTokenApiPath: '/csrf/api/v1/token',
    refreshAccessTokenEndpoint: 'https://lms.edxdev.org/login_refresh',
    accessTokenCookieName: 'edx-jwt-cookie-header-payload',
    userInfoCookieName: 'edx-user-info',
    loggingService: NewRelicLoggingService,
  });
  getLearnerPortalLinks(apiClient).then((learnerPortalLinks) => {
    const $dashboardLink = $('#user-menu .dashboard');
    const classNames = 'mobile-nav-item dropdown-item dropdown-nav-item';
    for (let i = 0; i < learnerPortalLinks.length; i += 1) {
      const link = learnerPortalLinks[i];

      $dashboardLink.after(
        `<div class="${classNames}"><a href="${link.url}" role="menuitem">${link.title}</a></div>`
      );
    }
  });
}

export { CustomUserMenuLinks }; // eslint-disable-line import/prefer-default-export
