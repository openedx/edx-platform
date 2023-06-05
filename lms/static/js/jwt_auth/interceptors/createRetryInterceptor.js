/**
 * Interceptor class to support JWT Token Authentication.
 *
 * Temporarily copied from the edx/frontend-platform
 */
import axios from 'axios';

// This default algorithm is a recreation of what is documented here
// https://cloud.google.com/storage/docs/exponential-backoff
const defaultGetBackoffMilliseconds = (nthRetry, maximumBackoffMilliseconds = 16000) => {
  // Retry at exponential intervals (2, 4, 8, 16...)
  const exponentialBackoffSeconds = 2 ** nthRetry;
  // Add some randomness to avoid sending retries from separate requests all at once
  const randomFractionOfASecond = Math.random();
  const backoffSeconds = exponentialBackoffSeconds + randomFractionOfASecond;
  const backoffMilliseconds = Math.round(backoffSeconds * 1000);
  return Math.min(backoffMilliseconds, maximumBackoffMilliseconds);
};

const createRetryInterceptor = (options = {}) => {
  const {
    httpClient = axios.create(),
    getBackoffMilliseconds = defaultGetBackoffMilliseconds,
    // By default only retry outbound request failures (not responses)
    shouldRetry = (error) => {
      const isRequestError = !error.response && error.config;
      return isRequestError;
    },
    // A per-request maxRetries can be specified in request config.
    defaultMaxRetries = 2,
  } = options;

  const interceptor = async (error) => {
    const { config } = error;

    // If no config exists there was some other error setting up the request
    if (!config) {
      return Promise.reject(error);
    }

    if (!shouldRetry(error)) {
      return Promise.reject(error);
    }

    const {
      maxRetries = defaultMaxRetries,
    } = config;

    const retryRequest = async (nthRetry) => {
      if (nthRetry > maxRetries) {
        // Reject with the original error
        return Promise.reject(error);
      }

      let retryResponse;

      try {
        const backoffDelay = getBackoffMilliseconds(nthRetry);
        // Delay (wrapped in a promise so we can await the setTimeout)
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
        // Make retry request
        retryResponse = await httpClient.request(config);
      } catch (e) {
        return retryRequest(nthRetry + 1);
      }

      return retryResponse;
    };

    return retryRequest(1);
  };

  return interceptor;
};

export default createRetryInterceptor;
export { defaultGetBackoffMilliseconds };
