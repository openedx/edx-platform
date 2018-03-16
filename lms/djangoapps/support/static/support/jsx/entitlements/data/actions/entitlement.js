import camelize from 'camelize';

import { getEntitlements } from '../api/client';
import { entitlementActions } from './constants';
import { displayError } from './error';

const fetchEntitlementsSuccess = entitlements => ({
  type: entitlementActions.fetch.SUCCESS,
  entitlements,
});

const fetchEntitlementsFailure = error =>
  dispatch =>
    dispatch(displayError('Error Getting Entitlements', error));

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
      json => dispatch(fetchEntitlementsSuccess(camelize(json.results))),
      error => dispatch(fetchEntitlementsFailure(error)),
    );
  };

export {
  fetchEntitlements,
  fetchEntitlementsSuccess,
  fetchEntitlementsFailure,
};
