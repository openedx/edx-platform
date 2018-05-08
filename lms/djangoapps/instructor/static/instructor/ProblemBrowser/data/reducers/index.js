import { combineReducers } from 'redux';
import { blocks, selectedBlock, rootBlock } from 'BlockBrowser/data/reducers';
import problemResponsesPopupActions from '../actions/constants';

const popupInitialState = {
  message: null,
  error: null,
  inProgress: false,
  succeeded: false,
  reportPath: null,
  reportPreview: null,
  timeout: null,
};

export const popupTask = (state = popupInitialState, action) => {
  switch (action.type) {
    case problemResponsesPopupActions.SUCCESS:
      return {
        ...state,
        message: action.message,
        inProgress: action.inProgress,
        succeeded: action.succeeded,
        reportPath: action.reportPath,
        reportPreview: action.reportPreview,
        error: null,
      };
    case problemResponsesPopupActions.ERROR:
      return { ...state, error: action.error, succeeded: false };
    case problemResponsesPopupActions.TIMEOUT:
      return { ...state, timeout: action.timeout };
    case problemResponsesPopupActions.RESET:
      return popupInitialState;
    default:
      return state;
  }
};

export default combineReducers({
  blocks,
  selectedBlock,
  rootBlock,
  popupTask,
});
