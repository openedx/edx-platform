/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { combineReducers } from 'redux';

import entitlements from './entitlements';
import error from './error';
import form from './form';

const rootReducer = combineReducers({ entitlements, error, form });

export default rootReducer;
