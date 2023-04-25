/**
 * Service class to support JWT Token Authentication.
 *
 * Temporarily copied from the edx/frontend-platform
 */
import Cookies from 'universal-cookie';
import jwtDecode from 'jwt-decode';
import axios from 'axios';
import createRetryInterceptor from './interceptors/createRetryInterceptor';
import { processAxiosErrorAndThrow } from './utils';

export default class AxiosJwtTokenService {
    static isTokenExpired(token) {
        return !token || token.exp < Date.now() / 1000;
    }

    constructor(tokenCookieName, tokenRefreshEndpoint) {
        this.tokenCookieName = tokenCookieName;
        this.tokenRefreshEndpoint = tokenRefreshEndpoint;

        this.httpClient = axios.create();
        // Set withCredentials to true. Enables cross-site Access-Control requests
        // to be made using cookies, authorization headers or TLS client
        // certificates. More on MDN:
        // https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/withCredentials
        this.httpClient.defaults.withCredentials = true;
        // Add retries to this axios instance
        this.httpClient.interceptors.response.use(
            response => response,
            createRetryInterceptor({ httpClient: this.httpClient }),
        );

        this.cookies = new Cookies();
        this.refreshRequestPromises = {};
    }

    getHttpClient() {
        return this.httpClient;
    }

    decodeJwtCookie() {
        const cookieValue = this.cookies.get(this.tokenCookieName);

        if (cookieValue) {
            try {
                return jwtDecode(cookieValue);
            } catch (e) {
                const error = Object.create(e);
                error.message = 'Error decoding JWT token';
                error.customAttributes = { cookieValue };
                throw error;
            }
        }

        return null;
    }

    refresh() {
        if (this.refreshRequestPromises[this.tokenCookieName] === undefined) {
            const makeRefreshRequest = async () => {
                let axiosResponse;
                try {
                    try {
                        axiosResponse = await this.httpClient.post(this.tokenRefreshEndpoint);
                    } catch (error) {
                        processAxiosErrorAndThrow(error);
                    }
                } catch (error) {
                    const userIsUnauthenticated = error.response && error.response.status === 401;
                    if (userIsUnauthenticated) {
                        // Clean up the cookie if it exists to eliminate any situation
                        // where the cookie is not expired but the jwt is expired.
                        this.cookies.remove(this.tokenCookieName);
                        const decodedJwtToken = null;
                        return decodedJwtToken;
                    }

                    // TODO: Network timeouts and other problems will end up in
                    // this block of code. We could add logic for retrying token
                    // refreshes if we wanted to.
                    throw error;
                }

                const decodedJwtToken = this.decodeJwtCookie();

                if (!decodedJwtToken) {
                    // This is an unexpected case. The refresh endpoint should
                    // set the cookie that is needed. See ARCH-948 for more
                    // information on a similar situation that was happening
                    // prior to this refactor in Oct 2019.
                    const error = new Error('Access token is still null after successful refresh.');
                    error.customAttributes = { axiosResponse };
                    throw error;
                }

                return decodedJwtToken;
            };

            this.refreshRequestPromises[this.tokenCookieName] = makeRefreshRequest().finally(() => {
                delete this.refreshRequestPromises[this.tokenCookieName];
            });
        }

        return this.refreshRequestPromises[this.tokenCookieName];
    }

    async getJwtToken() {
        try {
            const decodedJwtToken = this.decodeJwtCookie(this.tokenCookieName);
            if (!AxiosJwtTokenService.isTokenExpired(decodedJwtToken)) {
                return decodedJwtToken;
            }
        } catch (e) {
            // Log unexpected error and continue with attempt to refresh it.
            throw e;
        }

        try {
            return await this.refresh();
        } catch (e) {
            throw e;
        }
    }
}
