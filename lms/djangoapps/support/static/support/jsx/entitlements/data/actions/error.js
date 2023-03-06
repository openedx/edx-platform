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
