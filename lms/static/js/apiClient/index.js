import { getAuthenticatedAPIClient } from '@edx/frontend-auth';
import { NewRelicLoggingService } from '@edx/frontend-logging';

const apiClient = getAuthenticatedAPIClient({
  appBaseUrl: process.env.LMS_ROOT_URL,
  authBaseUrl: process.env.LMS_ROOT_URL,
  loginUrl: `${process.env.LMS_ROOT_URL}/login`,
  logoutUrl: `${process.env.LMS_ROOT_URL}/logout`,
  csrfTokenApiPath: '/csrf/api/v1/token',
  refreshAccessTokenEndpoint: `${process.env.LMS_ROOT_URL}/login_refresh`,
  accessTokenCookieName: process.env.JWT_AUTH_COOKIE_HEADER_PAYLOAD,
  userInfoCookieName: process.env.EDXMKTG_USER_INFO_COOKIE_NAME,
  loggingService: NewRelicLoggingService,
});

export default apiClient;
