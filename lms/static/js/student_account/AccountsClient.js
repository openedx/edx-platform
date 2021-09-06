import 'whatwg-fetch';
import Cookies from 'js-cookie';

const deactivate = (password) => fetch('/api/user/v1/accounts/deactivate_logout/', {
  method: 'POST',
  credentials: 'same-origin',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-CSRFToken': Cookies.get('csrftoken'),
  },
  // URLSearchParams + polyfill doesn't work in IE11
  body: `password=${encodeURIComponent(password)}`,
}).then((response) => {
  if (response.ok) {
    return response;
  }

  throw new Error(response.status);
});

export {
  deactivate,
};
