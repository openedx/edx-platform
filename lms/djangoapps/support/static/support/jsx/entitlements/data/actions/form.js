/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
