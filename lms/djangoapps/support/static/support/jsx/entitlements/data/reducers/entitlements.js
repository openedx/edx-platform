import { entitlementActions } from '../constants/actionTypes';

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
