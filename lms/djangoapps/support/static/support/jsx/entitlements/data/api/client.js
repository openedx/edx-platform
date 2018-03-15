import 'whatwg-fetch';
import Cookies from 'js-cookie';

import { entitlementApi } from './endpoints';

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

const getEntitlements = username => fetch(
  `${entitlementApi}/?user=${username}`, {
    credentials: 'same-origin',
    method: 'get',
  },
);

const createEntitlement = ({ username, courseUuid, mode, action, comments = null }) => fetch(
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

const updateEntitlement = ({ uuid, action, unenrolledRun = null, comments = null }) => fetch(
  `${entitlementApi}/${uuid}`, {
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
  getEntitlements,
  createEntitlement,
  updateEntitlement,
};
