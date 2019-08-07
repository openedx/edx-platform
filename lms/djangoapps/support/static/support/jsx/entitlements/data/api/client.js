import 'whatwg-fetch';
import Cookies from 'js-cookie';

import { entitlementApi } from './endpoints';

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

const getEntitlements = username => fetch(
  `${entitlementApi}?user=${username}`, {
    credentials: 'same-origin',
    method: 'get',
  },
);

const postEntitlement = ({ username, courseUuid, mode, action, comments = null }) => fetch(
  `${entitlementApi}`, {
    credentials: 'same-origin',
    method: 'post',
    headers: HEADERS,
    body: JSON.stringify({
      course_uuid: courseUuid,
      user: username,
      mode,
      refund_locked: true,
      support_details: [{
        action,
        comments,
      }],
    }),
  },
);

const patchEntitlement = ({ uuid, action, unenrolledRun = null, comments = null }) => fetch(
  `${entitlementApi}${uuid}`, {
    credentials: 'same-origin',
    method: 'patch',
    headers: HEADERS,
    body: JSON.stringify({
      expired_at: null,
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
  postEntitlement,
  patchEntitlement,
};
