import 'whatwg-fetch';
import Cookies from 'js-cookie';

const HEADERS = {
  Accept: 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

function initiateProblemResponsesRequest(endpoint, blockId) {
  const formData = new FormData();
  formData.set('problem_location', blockId);

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
    `${endpoint}/?task_id=${taskId}`, {
      credentials: 'same-origin',
      method: 'get',
      headers: HEADERS,
    },
  );

const fetchDownloadsList = (endpoint, reportName) => {
  const formData = new FormData();
  formData.set('report_name', reportName);

  return fetch(
    endpoint, {
      credentials: 'same-origin',
      method: 'POST',
      headers: HEADERS,
      body: formData,
    },
  );
};

export {
    initiateProblemResponsesRequest,
    fetchTaskStatus,
    fetchDownloadsList,
};
