import 'whatwg-fetch';
import Cookies from 'js-cookie';

const HEADERS = {
  Accept: 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

function initiateProblemResponsesRequest(endpoint, blockId) {
  const formData = new FormData();
    // xss-lint: disable=javascript-jquery-append
  formData.append('problem_location', blockId);

  return fetch(
        endpoint, {
          credentials: 'same-origin',
          method: 'post',
          headers: HEADERS,
          body: formData,
        },
    );
}

const fetchTaskStatus = (endpoint, taskId) => fetch(
    `${endpoint}?task_id=${taskId}`, {
      credentials: 'same-origin',
      method: 'get',
      headers: HEADERS,
    });

export {
    initiateProblemResponsesRequest,
    fetchTaskStatus,
};
