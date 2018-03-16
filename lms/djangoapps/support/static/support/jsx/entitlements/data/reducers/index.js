import { combineReducers } from 'redux';

import entitlements from './entitlements';
import error from './error';

const rootReducer = combineReducers({ entitlements, error });

export default rootReducer;
