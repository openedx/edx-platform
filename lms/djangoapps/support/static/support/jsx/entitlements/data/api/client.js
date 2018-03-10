import 'whatwg-fetch';
import Cookies from 'js-cookie';

import { entitlementApi } from './endpoints';

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

const requestEntitlements = ({ username }) => fetch(
  `${entitlementApi}/?user=${username}`, {
    credentials: 'same-origin',
    method: 'get',
  },
);


const createEntitlement = ({ username, courseUuid, mode, action, comments }) => fetch(
  `${entitlementApi}`, {
    credentials: 'same-origin',
    method: 'post',
    headers: HEADERS,
    body: JSON.stringify({
      course_uuid: courseUuid,
      user: username,
      mode,
      support_details: [{
        action,
        comments,
      }],
    }),
  },
);


const updateEntitlement = ({ entitlementUuid, unenrolledRun, action, comments }) => fetch(
  `${entitlementApi}/${entitlementUuid}`, {
    credentials: 'same-origin',
    method: 'patch',
    headers: HEADERS,
    body: JSON.stringify({
      expired_at: null,
      enrollment_run: null,
      support_details: [{
        unenrolled_run: unenrolledRun,
        action,
        comments,
      }],
    }),
  },
);


export {
  requestEntitlements,
  createEntitlement,
  updateEntitlement,
};
