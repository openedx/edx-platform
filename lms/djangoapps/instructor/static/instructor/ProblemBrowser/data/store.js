import {applyMiddleware, createStore} from 'redux';
import thunkMiddleware from 'redux-thunk';

import rootReducer from './reducers/index';

const defaultState = {
    blocks: [],
    selectedBlock: null,
    rootBlock: null,
};

const configureStore = initialState => createStore(
    rootReducer,
    initialState,
    applyMiddleware(thunkMiddleware),
);


const store = configureStore(defaultState);

export default store;
