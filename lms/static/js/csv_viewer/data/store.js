import thunkMiddleware from 'redux-thunk';
import { applyMiddleware, createStore } from 'redux';

import rootReducer from './reducers/index';
import { fetchCSVData } from './actions/csvFetcher';

const store = createStore(
  rootReducer,
  applyMiddleware(thunkMiddleware),
);

// We need to use this custom function instead of URLSearchParams since
// we need to use decodeURI for the csvUrl instead of decodeURIComponent
function getCsvUrl() {
  const query = window.location.search.substring(1);
  const vars = query.split('&');
  for (let i = 0; i < vars.length; i += 1) {
    const pair = vars[i].split('=');
    if (pair[0] === 'csvUrl') {
      return decodeURI(pair[1]);
    }
  }
  return null;
}

const csvUrl = getCsvUrl();

store.dispatch(fetchCSVData(csvUrl));

export default store;
