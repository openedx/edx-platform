/* global gettext */
import { fetchTaskStatus, initiateProblemResponsesRequest } from '../api/client';
import problemResponsesPopupActions from './constants';

const getTaskStatusSuccess = (succeeded, inProgress, message, reportPath, reportPreview) => ({
  type: problemResponsesPopupActions.SUCCESS,
  succeeded,
  inProgress,
  message,
  reportPath,
  reportPreview,
});

const failure = error => ({
  type: problemResponsesPopupActions.ERROR,
  error,
});

const timeoutSet = timeout => ({
  type: problemResponsesPopupActions.TIMEOUT,
  timeout,
});

const reset = () => ({ type: problemResponsesPopupActions.RESET });

const getTaskStatus = (endpoint, taskId) => dispatch =>
  fetchTaskStatus(endpoint, taskId)
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      throw new Error(response);
    })
    .then(
      (json) => {
        if (json.in_progress) {
          const timeout = setTimeout(() => dispatch(getTaskStatus(endpoint, taskId)), 1000);
          dispatch(timeoutSet(timeout));
        }
        return dispatch(
          getTaskStatusSuccess(
            json.task_state === 'SUCCESS',
            json.in_progress,
            json.message,
            json.task_progress.report_path,
            json.task_progress.report_preview,
          ));
      },
      () => dispatch(failure(gettext('Error: Unable to get report generation status.'))),
    );

const createProblemResponsesReportTask = (
  initialEndpoint,
  taskStatusEndpoint,
  blockId,
) => dispatch =>
  initiateProblemResponsesRequest(initialEndpoint, blockId)
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      throw new Error(response);
    })
    .then(
      json => dispatch(getTaskStatus(taskStatusEndpoint, json.task_id)),
      () => dispatch(failure(gettext('Error: Unable to submit request to generate report.'))),
    );


export {
  failure,
  createProblemResponsesReportTask,
  getTaskStatusSuccess,
  getTaskStatus,
  reset,
};
