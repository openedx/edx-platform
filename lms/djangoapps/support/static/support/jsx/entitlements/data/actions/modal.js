import { modalActions } from './constants';

const openReissueModal = entitlement => ({
  type: modalActions.OPEN_REISSUE_MODAL,
  entitlement
});

const openCreationModal = () => ({
  type: modalActions.OPEN_CREATION_MODAL,
});

const closeModal = () => ({
  type: modalActions.CLOSE_MODAL,
});

export {
  openReissueModal,
  openCreationModal,
  closeModal,
};
