/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import { errorActions } from '../constants/actionTypes';

const displayError = (message, error) => ({
    type: errorActions.DISPLAY_ERROR,
    error: `${message}: ${error}`,
});

const dismissError = () => ({
    type: errorActions.DISMISS_ERROR,
});

export {
    displayError,
    dismissError,
};
