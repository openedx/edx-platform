import { modalActions, entitlementActions } from '../actions/constants';

const clearModal = state => ({
  ...state,
  isOpen: false,
  activeEntitlement: null,
});

const modal = (state = {}, action) => {
  switch (action.type) {
    case modalActions.OPEN_REISSUE_MODAL:
      return { ...state, isOpen: true, activeEntitlement: action.entitlement };
    case modalActions.OPEN_CREATION_MODAL:
      return { ...state, isOpen: true, activeEntitlement: null };
    case modalActions.CLOSE_MODAL:
    case entitlementActions.UPDATE_ENTITLEMENT_SUCCESS:
    case entitlementActions.CREATE_ENTITLEMENT_SUCCESS:
      return clearModal();
    default:
      return state;
  }
};

export default modal;
