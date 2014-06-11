$(document).ajaxError(function (event, jXHR) {
    if (jXHR.status === 401) {
        alert(gettext("You're logged out. Redirecting on login page."));
        window.location.href = '/accounts/login?next=' + window.location.href;
    }
});
