export const entitlementActions = {
    fetch: {
        SUCCESS: 'FETCH_ENTITLEMENTS_SUCCESS',
        FAILURE: 'FETCH_ENTITLEMENTS_FAILURE',
    },
    reissue: {
        SUCCESS: 'REISSUE_ENTITLEMENT_SUCCESS',
        FAILURE: 'REISSUE_ENTITLEMENT_FAILURE',
    },
    create: {
        SUCCESS: 'CREATE_ENTITLEMENT_SUCCESS',
        FAILURE: 'CREATE_ENTITLEMENT_FAILURE',
    },
};

export const errorActions = {
    DISPLAY_ERROR: 'DISPLAY_ERROR',
    DISMISS_ERROR: 'DISMISS_ERROR',
};

export const formActions = {
    OPEN_REISSUE_FORM: 'OPEN_REISSUE_FORM',
    OPEN_CREATION_FORM: 'OPEN_CREATION_FORM',
    CLOSE_FORM: 'CLOSE_FORM',
};
