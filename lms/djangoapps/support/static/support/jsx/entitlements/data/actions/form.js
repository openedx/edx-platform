import { formActions } from '../constants/actionTypes';

const openReissueForm = entitlement => ({
    type: formActions.OPEN_REISSUE_FORM,
    entitlement,
});


const openCreationForm = () => ({
    type: formActions.OPEN_CREATION_FORM,
});

const closeForm = () => ({
    type: formActions.CLOSE_FORM,
});

export {
    openReissueForm,
    openCreationForm,
    closeForm,
};
