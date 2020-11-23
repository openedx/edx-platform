import { formActions, entitlementActions } from '../constants/actionTypes';
import { formTypes } from '../constants/formTypes';
const clearFormState = {
  formType: '',
  isOpen: false,
  activeEntitlement: null,
};

const form = (state = {}, action) => {
  switch (action.type) {
    case formActions.OPEN_REISSUE_FORM:
      return { ...state, formType: formTypes.REISSUE, isOpen: true, activeEntitlement: action.entitlement };
    case formActions.OPEN_CREATION_FORM:
      return { ...state, formType: formTypes.CREATE, isOpen: true, activeEntitlement: null };
    case formActions.CLOSE_FORM:
    case entitlementActions.reissue.SUCCESS:
    case entitlementActions.create.SUCCESS:
      return clearFormState;
    default:
      return state;
  }
};

export default form;
