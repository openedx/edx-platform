import { combineReducers } from 'redux'; // eslint-disable-line
import { blocks, selectedBlock, rootBlock } from 'BlockBrowser/data/reducers'; // eslint-disable-line
import {
  REPORT_GENERATION_ERROR,
  REPORT_GENERATION_SUCCESS,
  REPORT_GENERATION_REFRESH_STATUS,
  REPORT_GENERATION_REQUEST,
} from '../actions/constants';

const initialState = {
  error: null,
  inProgress: false,
  succeeded: false,
  reportPath: null,
  reportName: null,
  timeout: null,
};

export const reportStatus = (state = initialState, action) => {
  switch (action.type) {
    case REPORT_GENERATION_REQUEST:
      return initialState;
    case REPORT_GENERATION_SUCCESS:
      return {
        ...state,
        inProgress: action.inProgress,
        succeeded: action.succeeded,
        reportPath: action.reportPath,
        reportName: action.reportName,
        error: null,
      };
    case REPORT_GENERATION_ERROR:
      return { ...state, error: action.error, succeeded: false };
    case REPORT_GENERATION_REFRESH_STATUS:
      return { ...state, timeout: action.timeout };
    default:
      return state;
  }
};

export default combineReducers({
  blocks,
  selectedBlock,
  rootBlock,
  reportStatus,
});
