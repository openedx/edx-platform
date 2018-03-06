import { applyMiddleware, createStore } from 'redux';

import rootReducer from './reducers';

const store = createStore(
  rootReducer,
  window.pageFactoryArguments
);

export default store;
