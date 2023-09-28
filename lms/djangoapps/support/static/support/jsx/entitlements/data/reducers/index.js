import { combineReducers } from 'redux';

import entitlements from './entitlements';
import error from './error';
import form from './form';

const rootReducer = combineReducers({ entitlements, error, form });

export default rootReducer;
