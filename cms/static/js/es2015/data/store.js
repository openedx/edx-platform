import { applyMiddleware, createStore } from 'redux';

import rootReducer from './reducers';

const StudioStore = createStore(
  rootReducer,
  window.pageFactoryArguments
);

export { StudioStore };
