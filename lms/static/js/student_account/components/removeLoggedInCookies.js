import cookie from 'js-cookie';

const removeLoggedInCookies = () => {
  cookie.remove('edxloggedin');
  cookie.remove('csrftoken');
  cookie.remove('edx-user-info');
};

export default removeLoggedInCookies;
