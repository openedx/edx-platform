import 'whatwg-fetch'; // fetch polyfill
import Cookies from 'js-cookie';

import endpoints from './endpoints';

export function requestEntitlements(username_or_email) {
	console.log('called requestEntitlements api function');
  return fetch(
    `${endpoints.entitlementList}/${username_or_email}`, {
      credentials: 'same-origin',
      method: 'get'
    },
  );
}

export function createEntitlement(course_uuid, user, mode, reason, comments) {
  return fetch(
    `${endpoints.entitlementList}/${user}`, {
      credentials: 'same-origin',
      method: 'post',
      headers:{
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
      body: JSON.stringify({
        course_uuid: course_uuid,
        user: user,
        mode: mode,
        reason: reason,
        comments: comments
      })
    }
  );
}

export function updateEntitlement(email, reason, entitlement_uuid, comments) {
  //Only requires an 'email' parameter to construct the url, not actually sent in the call
  return fetch(
    `${endpoints.entitlementList}/${email}`, {
      credentials: 'same-origin',
      method: 'put',
      headers:{
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
      body:JSON.stringify({
      	entitlement_uuid: entitlement_uuid,
        reason: reason,
      	comments: comments
      }),
    }
  );
}