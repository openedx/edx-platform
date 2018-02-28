import { combineReducers } from 'redux';

import entitlements from './entitlements';
import modal from './modal';

const rootReducer = combineReducers({entitlements, modal})

export default rootReducer;