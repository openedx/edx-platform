/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { errorActions, entitlementActions } from '../constants/actionTypes';

// eslint-disable-next-line default-param-last
const error = (state = '', action) => {
    switch (action.type) {
    case errorActions.DISPLAY_ERROR:
        return action.error;
    case errorActions.DISMISS_ERROR:
    case entitlementActions.fetch.SUCCESS:
        return '';
    default:
        return state;
    }
};

export default error;
