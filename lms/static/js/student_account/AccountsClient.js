import 'url-search-params-polyfill';
import 'whatwg-fetch';
import Cookies from 'js-cookie';

const deactivate = (password) => fetch('/api/user/v1/accounts/deactivate_logout/', {
  method: 'POST',
  credentials: 'same-origin',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-CSRFToken': Cookies.get('csrftoken'),
  },
  body: new URLSearchParams({ password }),
}).then((response) => {
  if (response.ok) {
    return response;
  }

  throw new Error(response);
});

export {
  deactivate,
};
