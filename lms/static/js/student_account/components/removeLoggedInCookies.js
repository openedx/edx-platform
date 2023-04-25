import cookie from 'js-cookie';

const removeLoggedInCookies = () => {
    const hostname = window.location.hostname;
    const isLocalhost = hostname.indexOf('localhost') >= 0;
    const isStage = hostname.indexOf('stage') >= 0;

    let domain = '.edx.org';
    if (isLocalhost) {
        domain = 'localhost';
    } else if (isStage) {
        domain = '.stage.edx.org';
    }

    cookie.remove('edxloggedin', { domain });

    if (isLocalhost) {
    // localhost doesn't have prefixes
        cookie.remove('csrftoken', { domain });
        cookie.remove('edx-user-info', { domain });
    } else {
    // does not take sandboxes into account
        const prefix = isStage ? 'stage' : 'prod';
        // both stage and prod csrf tokens are set to .edx.org
        cookie.remove(`${prefix}-edx-csrftoken`, { domain: '.edx.org' });
        cookie.remove(`${prefix}-edx-user-info`, { domain });
    }
};

export default removeLoggedInCookies;
