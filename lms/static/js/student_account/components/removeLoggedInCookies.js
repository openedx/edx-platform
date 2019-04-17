import cookie from 'js-cookie';

const removeLoggedInCookies = () => {
  cookie.remove('edxloggedin', window.domainName);
  cookie.remove('csrftoken', window.domainName);
  cookie.remove('edx-user-info', window.domainName);
};

export default removeLoggedInCookies;
