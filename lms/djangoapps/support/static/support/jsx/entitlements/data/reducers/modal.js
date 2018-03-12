import { modalActions, entitlementActions } from '../actions/constants';

const modal = (state = {}, action) => {
  switch (action.type) {
    case modalActions.OPEN_REISSUE_MODAL:
      console.log('opening reissue modal')
      return { ...state, isOpen: true, activeEntitlement: action.entitlement};
    case modalActions.OPEN_CREATION_MODAL:
      console.log('opening creation modal')
      return { ...state, isOpen: true, activeEntitlement: null};
    case modalActions.CLOSE_MODAL:
    case entitlementActions.UPDATE_ENTITLEMENT_SUCCESS:
    case entitlementActions.CREATE_ENTITLEMENT_SUCCESS:
      return clearModal();
    default:
      return state;
  }
};

const clearModal = state => ({
	...state,
	isOpen: false,
	activeEntitlement:null,
})

export default modal;
