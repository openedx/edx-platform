import { createStore, compose, applyMiddleware } from 'redux';
//import { syncHistoryWithStore } from 'react-router-redux';
//import { browserHistory } from 'react-router';
import thunkMiddleware from "redux-thunk"; 

// import root reducer
import rootReducer from './data/reducers/index';

import entitlements from './data/entitlements';



const initial_entitlements = [];

//create default data
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

const store = configureStore(defaultState);//, enhancers);


export default store;