import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';

import rootReducer from './reducers/index';

const defaultState = {
  entitlements: [],
  error: '',
  modal: {
    isOpen: false,
    activeEntitlement: null
  }
};

const configureStore = initialState =>
  createStore(
    rootReducer,
    initialState,
    applyMiddleware(thunkMiddleware),
  );


const store = configureStore(defaultState);

export default store;
