import { entitlementActions } from '../actions/constants';

const entitlements = (state = [], action) => {
  switch (action.type) {
    case entitlementActions.fetch.SUCCESS:
      return action.entitlements;
    default:
      return state;
  }
};

export default entitlements;
