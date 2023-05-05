/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';

import rootReducer from './reducers/index';

const defaultState = {
    entitlements: [],
    error: '',
    form: {
        formType: '',
        isOpen: false,
        activeEntitlement: null,
    },
};

const configureStore = initialState => createStore(
    rootReducer,
    initialState,
    applyMiddleware(thunkMiddleware),
);

const store = configureStore(defaultState);

export default store;
