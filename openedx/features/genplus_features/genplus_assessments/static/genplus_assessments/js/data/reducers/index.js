import { combineReducers } from 'redux'; // eslint-disable-line
import { blocks, selectedBlock, rootBlock } from 'BlockBrowser/data/reducers'; // eslint-disable-line
import blockBrowserActions from 'BlockBrowser/data/actions/constants'; // eslint-disable-line

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
    case blockBrowserActions.SELECT_BLOCK:
      return initialState;
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
