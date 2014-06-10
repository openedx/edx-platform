$(document).ajaxError(function (event, jXHR) {
    if (jXHR.status === 403) {
        alert(gettext('You\'re logged out. Redirecting on login page.'));
        window.location = '/accounts/login';
    }
});
