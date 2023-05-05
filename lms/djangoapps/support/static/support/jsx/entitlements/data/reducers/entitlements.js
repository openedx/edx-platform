/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { entitlementActions } from '../constants/actionTypes';

// eslint-disable-next-line default-param-last
const entitlements = (state = [], action) => {
    switch (action.type) {
    case entitlementActions.fetch.SUCCESS:
        return action.entitlements;
    case entitlementActions.create.SUCCESS:
        return [...state, action.entitlement];
    case entitlementActions.reissue.SUCCESS:
        return state.map((entitlement) => {
            if (entitlement.uuid === action.entitlement.uuid) {
                return action.entitlement;
            }
            return entitlement;
        });
    default:
        return state;
    }
};

export default entitlements;
