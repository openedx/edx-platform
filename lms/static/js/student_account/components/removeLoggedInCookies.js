import cookie from 'js-cookie';

const removeLoggedInCookies = () => {
  cookie.remove('edxloggedin', { domain: window.domainName });
  cookie.remove('csrftoken', { domain: window.domainName });
  cookie.remove('edx-user-info', { domain: window.domainName });
};

export default removeLoggedInCookies;
