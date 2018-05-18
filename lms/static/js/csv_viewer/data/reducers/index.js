import { combineReducers } from 'redux';

import csvViewerActions from '../actions/constants';

const processCSV = (csvData) => {
  const columnDefs = csvData.length
        ? Object.keys(csvData[0]).map(field => ({ field }))
        : [];
  return {
    rowData: csvData,
    columnDefs,
  };
};

const csvData = (state = { rowData: [], columnDefs: [], csvUrl: null }, action) => {
  switch (action.type) {
    case csvViewerActions.fetch.SUCCESS:
      return {csvUrl: action.csvUrl, ...processCSV(action.csvData)};
    default:
      return state;
  }
};

const error = (state = null, action) => {
  switch (action.type) {
    case csvViewerActions.fetch.FAILURE:
      return action.error;
    case csvViewerActions.fetch.SUCCESS:
      return null;
    default:
      return state;
  }
};

const loading = (state = false, action) => {
  switch (action.type) {
    case csvViewerActions.fetch.START:
      return true;
    case csvViewerActions.fetch.SUCCESS:
    case csvViewerActions.fetch.FAILURE:
      return false;
    default:
      return state;
  }
};

export default combineReducers({ csvData, error, loading });
