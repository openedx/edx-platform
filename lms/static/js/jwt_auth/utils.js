/**
 * Utils file to support JWT Token Authentication.
 *
 * Temporarily copied from the edx/frontend-platform
 */

// Lifted from here: https://regexr.com/3ok5o
const urlRegex = /([a-z]{1,2}tps?):\/\/((?:(?!(?:\/|#|\?|&)).)+)(?:(\/(?:(?:(?:(?!(?:#|\?|&)).)+\/))?))?(?:((?:(?!(?:\.|$|\?|#)).)+))?(?:(\.(?:(?!(?:\?|$|#)).)+))?(?:(\?(?:(?!(?:$|#)).)+))?(?:(#.+))?/;
const getUrlParts = (url) => {
  const found = url.match(urlRegex);
  try {
    const [
      fullUrl,
      protocol,
      domain,
      path,
      endFilename,
      endFileExtension,
      query,
      hash,
    ] = found;

    return {
      fullUrl,
      protocol,
      domain,
      path,
      endFilename,
      endFileExtension,
      query,
      hash,
    };
  } catch (e) {
    throw new Error(`Could not find url parts from ${url}.`);
  }
};

const logFrontendAuthError = (loggingService, error) => {
  const prefixedMessageError = Object.create(error);
  prefixedMessageError.message = `[frontend-auth] ${error.message}`;
  loggingService.logError(prefixedMessageError, prefixedMessageError.customAttributes);
};

const processAxiosError = (axiosErrorObject) => {
  const error = Object.create(axiosErrorObject);
  const { request, response, config } = error;

  if (!config) {
    error.customAttributes = {
      ...error.customAttributes,
      httpErrorType: 'unknown-api-request-error',
    };
    return error;
  }

  const {
    url: httpErrorRequestUrl,
    method: httpErrorRequestMethod,
  } = config;
  /* istanbul ignore else: difficult to enter the request-only error case in a unit test */
  if (response) {
    const { status, data } = response;
    const stringifiedData = JSON.stringify(data) || '(empty response)';
    const responseIsHTML = stringifiedData.includes('<!DOCTYPE html>');
    // Don't include data if it is just an HTML document, like a 500 error page.
    /* istanbul ignore next */
    const httpErrorResponseData = responseIsHTML ? '<Response is HTML>' : stringifiedData;
    error.customAttributes = {
      ...error.customAttributes,
      httpErrorType: 'api-response-error',
      httpErrorStatus: status,
      httpErrorResponseData,
      httpErrorRequestUrl,
      httpErrorRequestMethod,
    };
    error.message = `Axios Error (Response): ${status} ${httpErrorRequestUrl} ${httpErrorResponseData}`;
  } else if (request) {
    error.customAttributes = {
      ...error.customAttributes,
      httpErrorType: 'api-request-error',
      httpErrorMessage: error.message,
      httpErrorRequestUrl,
      httpErrorRequestMethod,
    };
    // This case occurs most likely because of intermittent internet connection issues
    // but it also, though less often, catches CORS or server configuration problems.
    error.message = `Axios Error (Request): ${error.message} (possible local connectivity issue) ${httpErrorRequestMethod} ${httpErrorRequestUrl}`;
  } else {
    error.customAttributes = {
      ...error.customAttributes,
      httpErrorType: 'api-request-config-error',
      httpErrorMessage: error.message,
      httpErrorRequestUrl,
      httpErrorRequestMethod,
    };
    error.message = `Axios Error (Config): ${error.message} ${httpErrorRequestMethod} ${httpErrorRequestUrl}`;
  }

  return error;
};

const processAxiosErrorAndThrow = (axiosErrorObject) => {
  throw processAxiosError(axiosErrorObject);
};

export {
  getUrlParts,
  logFrontendAuthError,
  processAxiosError,
  processAxiosErrorAndThrow,
};
