/**
 * Service class to support CSRF.
 *
 * Temporarily copied from the edx/frontend-platform
 */
import axios from 'axios';
import { getUrlParts, processAxiosErrorAndThrow } from './utils';

export default class AxiosCsrfTokenService {
  constructor(csrfTokenApiPath) {
    this.csrfTokenApiPath = csrfTokenApiPath;
    this.httpClient = axios.create();
    // Set withCredentials to true. Enables cross-site Access-Control requests
    // to be made using cookies, authorization headers or TLS client
    // certificates. More on MDN:
    // https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/withCredentials
    this.httpClient.defaults.withCredentials = true;
    this.httpClient.defaults.headers.common['USE-JWT-COOKIE'] = true;

    this.csrfTokenCache = {};
    this.csrfTokenRequestPromises = {};
  }

  async getCsrfToken(url) {
    let urlParts;
    try {
      urlParts = getUrlParts(url);
    } catch (e) {
      // If the url is not parsable it's likely because a relative
      // path was supplied as the url. This is acceptable and in
      // this case we should use the current origin of the page.
      urlParts = getUrlParts(global.location.origin);
    }
    const { protocol, domain } = urlParts;
    const csrfToken = this.csrfTokenCache[domain];

    if (csrfToken) {
      return csrfToken;
    }

    if (!this.csrfTokenRequestPromises[domain]) {
      this.csrfTokenRequestPromises[domain] = this.httpClient
        .get(`${protocol}://${domain}${this.csrfTokenApiPath}`)
        .then((response) => {
          this.csrfTokenCache[domain] = response.data.csrfToken;
          return this.csrfTokenCache[domain];
        })
        .catch(processAxiosErrorAndThrow)
        .finally(() => {
          delete this.csrfTokenRequestPromises[domain];
        });
    }

    return this.csrfTokenRequestPromises[domain];
  }

  clearCsrfTokenCache() {
    this.csrfTokenCache = {};
  }

  getHttpClient() {
    return this.httpClient;
  }
}
