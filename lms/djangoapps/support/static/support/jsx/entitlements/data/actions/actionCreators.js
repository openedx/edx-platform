import * as clientApi from '../api/client';

export const entitlementActions = {
	FETCH_ENTITLEMENTS_REQUEST: 'FETCH_ENTITLEMENTS_REQUEST',
	FETCH_ENTITLEMENTS_SUCCESS: 'FETCH_ENTITLEMENTS_SUCCESS',
	FETCH_ENTITLEMENTS_FAILURE: 'FETCH_ENTITLEMENTS_FAILURE'

}

export function fetchEntitlements(username_or_email){
	console.log("fetchEntitlements action creation")
	return dispatch => {
		clientApi.requestEntitlements(username_or_email)
		.then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.log('throwing error');
      throw new Error(response);
    })
    .then((json) => {
      if (json) {
      	console.log('got out some json', JSON.stringify(json))
        return dispatch(fetchEntitlementsSuccess(json));
      }
      return Promise.resolve();
    })
    .catch((error) => {
    	console.log('catching error');
      return dispatch(fetchEntitlementsFailure(error));  
    });
	}
}

export function fetchEntitlementsRequest(username_or_email){
	return {
		type:'FETCH_ENTITLEMENTS_REQUEST',
		username_or_email
	}
}

export function fetchEntitlementsSuccess(entitlements){
	return {
		type:'FETCH_ENTITLEMENTS_SUCCESS',
		entitlements
	}
}

export function fetchEntitlementsFailure(error){
	return {
		type:'FETCH_ENTITLEMENTS_FAILURE',
		error
	}
}

export function updateEntitlement(email, reason, entitlement_uuid, comments){
	console.log("fetchEntitlements action creation")
	return dispatch => {
		clientApi.updateEntitlement(email, reason, entitlement_uuid, comments)
		.then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.log('throwing error');
      throw new Error(response);
    })
    .then((json) => {
      if (json) {
      	console.log('got out some json', JSON.stringify(json))
        return dispatch(updateEntitlementSuccess(json));
      }
      return Promise.resolve();
    })
    .catch((error) => {
    	console.log('catching error');
      return dispatch(updateEntitlementFailure(error));  
    });
	}
}

export function updateEntitlementRequest(reason, entitlement_uuid, comments){
	return {
		type:'UPDATE_ENTITLEMENT_REQUEST',
		email,
		username,
		course_key
	}
}

export function updateEntitlementSuccess(entitlement){
	console.log('creating updateEntittlementSuccess with entitlement',entitlement)
	return {
		type:'UPDATE_ENTITLEMENT_SUCCESS',
		entitlement
	}
}

export function updateEntitlementFailure(error){
	return {
		type:'UPDATE_ENTITLEMENT_FAILURE',
		error
	}
}


export function createEntitlement(course_uuid, user, mode, reason, comments){
	console.log("createEntitlements action creation with data: ",course_uuid, user, mode, reason, comments)
	return dispatch => {
		clientApi.createEntitlement(course_uuid, user, mode, reason, comments)
		.then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.log('throwing error');
      throw new Error(response);
    })
    .then((json) => {
      if (json) {
      	console.log('got out some json', JSON.stringify(json))
        return dispatch(createEntitlementSuccess(json));
      }
      return Promise.resolve();
    })
    .catch((error) => {
    	console.log('catching error, error:', error);
      return dispatch(createEntitlementFailure(error));  
    });
	}
}
export function createEntitlementRequest(){
	return {
		type:'UPDATE_ENTITLEMENT_REQUEST',
	}
}

export function createEntitlementSuccess(entitlement){
	return {
		type:'CREATE_ENTITLEMENT_SUCCESS',
		entitlement
	}
}

export function createEntitlementFailure(error){
	return {
		type:'CREATE_ENTITLEMENT_FAILURE',
		error
	}
}


export function openReissueModal(entitlement){
	return {
		type:'OPEN_REISSUE_MODAL',
		entitlement
	}
}

export function openCreationModal(){
	return {
		type:'OPEN_CREATION_MODAL',
	}
}

export function closeModal(){
	return {
		type:'CLOSE_MODAL',
	}
}