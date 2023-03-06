/* global gettext */
import { fetchDownloadsList, fetchTaskStatus, initiateProblemResponsesRequest } from '../api/client';
import {
    REPORT_GENERATION_ERROR,
    REPORT_GENERATION_REQUEST,
    REPORT_GENERATION_SUCCESS,
    REPORT_GENERATION_REFRESH_STATUS,
} from './constants';

const taskStatusSuccess = (succeeded, inProgress, reportName, downloadsData) => ({
    type: REPORT_GENERATION_SUCCESS,
    succeeded,
    inProgress,
    reportName,
    downloadsData,
});

const problemResponsesRequest = blockId => ({
    type: REPORT_GENERATION_REQUEST,
    blockId,
});

const problemResponsesFailure = error => ({
    type: REPORT_GENERATION_ERROR,
    error,
});

const problemResponsesRefreshStatus = timeout => ({
    type: REPORT_GENERATION_REFRESH_STATUS,
    timeout,
});

const getTaskStatus = (taskStatusEndpoint, reportDownloadEndpoint, taskId) => dispatch =>
    fetchTaskStatus(taskStatusEndpoint, taskId)
        .then((response) => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(response);
        })
        .then(
            (statusData) => {
                if (statusData.in_progress) {
                    const timeout = setTimeout(
                        () => dispatch(getTaskStatus(taskStatusEndpoint, reportDownloadEndpoint, taskId)),
                        2000,
                    );
                    return dispatch(problemResponsesRefreshStatus(timeout));
                }
                if (statusData.task_state === 'SUCCESS') {
                    const taskProgress = statusData.task_progress;
                    const reportName = taskProgress && taskProgress.report_name;
                    return fetchDownloadsList(reportDownloadEndpoint, reportName)
                        .then(response => response.json())
                        .then(
                            data => dispatch(
                                taskStatusSuccess(
                                    true,
                                    statusData.in_progress,
                                    reportName,
                                    data.downloads,
                                ),
                            ),
                            () => dispatch(problemResponsesFailure(gettext('There was an error generating the report link.'))),
                        );
                }
                return dispatch(problemResponsesFailure(gettext('There was an error generating your report.')));
            },
            () => dispatch(
                problemResponsesFailure(gettext('Unable to get report generation status.')),
            ),
        );

const createProblemResponsesReportTask = (
    problemResponsesEndpoint,
    taskStatusEndpoint,
    reportDownloadEndpoint,
    blockId,
) => (dispatch) => {
    dispatch(problemResponsesRequest(blockId));
    initiateProblemResponsesRequest(problemResponsesEndpoint, blockId)
        .then((response) => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(response);
        })
        .then(
            json => dispatch(getTaskStatus(taskStatusEndpoint, reportDownloadEndpoint, json.task_id)),
            () => dispatch(problemResponsesFailure(gettext('Unable to submit request to generate report.'))),
        );
};

export {
    problemResponsesFailure,
    createProblemResponsesReportTask,
    problemResponsesRequest,
    getTaskStatus,
};
