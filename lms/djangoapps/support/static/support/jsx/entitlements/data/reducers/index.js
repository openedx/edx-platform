import { combineReducers } from 'redux';

import entitlements from './entitlements';
import error from './error';
import modal from './modal';

const rootReducer = combineReducers({ entitlements, error, modal });

export default rootReducer;
