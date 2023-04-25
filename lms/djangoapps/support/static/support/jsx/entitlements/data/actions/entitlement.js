import camelize from 'camelize';

import { getEntitlements, patchEntitlement, postEntitlement } from '../api/client';
import { entitlementActions } from '../constants/actionTypes';
import { displayError } from './error';

const fetchEntitlementsSuccess = entitlements => ({
    type: entitlementActions.fetch.SUCCESS,
    entitlements,
});

const fetchEntitlementsFailure = error =>
    dispatch =>
        dispatch(displayError('Error Getting Entitlements', error));

const emptyEntitlementsFailure = error =>
    dispatch =>
        dispatch(displayError('No Entitlements Found', error));

const fetchEntitlements = username =>
    (dispatch) => {
        getEntitlements(username)
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error(response);
            })
            .then(
                (json) => {
                    if (json.count === 0) {
                        dispatch(emptyEntitlementsFailure(''));
                    } else {
                        dispatch(fetchEntitlementsSuccess(camelize(json.results)));
                    }
                },
                error => dispatch(fetchEntitlementsFailure(error)),
            );
    };

const reissueEntitlementSuccess = entitlement => ({
    type: entitlementActions.reissue.SUCCESS,
    entitlement,
});

const reissueEntitlementFailure = error =>
    dispatch =>
        dispatch(displayError('Error Reissuing Entitlement', error));

const reissueEntitlement = ({ entitlement, comments }) =>
    (dispatch) => {
        patchEntitlement({
            uuid: entitlement.uuid,
            action: 'REISSUE',
            unenrolledRun: entitlement.enrollmentCourseRun,
            comments,
        })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error(response);
            })
            .then(
                json => dispatch(reissueEntitlementSuccess(camelize(json))),
                error => dispatch(reissueEntitlementFailure(error)),
            );
    };

const createEntitlementSuccess = entitlement => ({
    type: entitlementActions.create.SUCCESS,
    entitlement,
});

const createEntitlementFailure = error =>
    dispatch =>
        dispatch(displayError('Error Creating Entitlement', error));

const createEntitlement = ({ username, courseUuid, mode, comments }) =>
    (dispatch) => {
        postEntitlement({
            username,
            courseUuid,
            mode,
            comments,
            action: 'CREATE',
        })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error(response);
            })
            .then(
                json => dispatch(createEntitlementSuccess(camelize(json))),
                error => dispatch(createEntitlementFailure(error)),
            );
    };

export {
    fetchEntitlements,
    fetchEntitlementsSuccess,
    fetchEntitlementsFailure,
    createEntitlement,
    createEntitlementSuccess,
    createEntitlementFailure,
    reissueEntitlement,
    reissueEntitlementSuccess,
    reissueEntitlementFailure,
};
