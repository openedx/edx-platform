import { createStore, compose, applyMiddleware } from 'redux';
import thunkMiddleware from "redux-thunk"; 

// import root reducer
import rootReducer from './data/reducers/index';

const defaultState = {
	entitlements: initial_entitlements,
	modal: {
    isOpen: false,
    activeEntitlement: null
  }
}

function configureStore(initialState){
  return createStore(
    rootReducer,
    initialState,
    applyMiddleware(thunkMiddleware),
  );
}

const store = configureStore(defaultState);

export default store;