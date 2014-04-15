// checks whether or not the url is external to the local site.
// generously provided by StackOverflow: http://stackoverflow.com/questions/6238351/fastest-way-to-detect-external-urls
window.isExternal = function (url) {
    // parse the url into protocol, host, path, query, and fragment. More information can be found here: http://tools.ietf.org/html/rfc3986#appendix-B
    var match = url.match(/^([^:\/?#]+:)?(?:\/\/([^\/?#]*))?([^?#]+)?(\?[^#]*)?(#.*)?/);
    // match[1] matches a protocol if one exists in the url
    // if the protocol in the url does not match the protocol in the window's location, this url is considered external
    if (typeof match[1] === "string" &&
            match[1].length > 0 &&
            match[1].toLowerCase() !== location.protocol)
        return true;
    // match[2] matches the host if one exists in the url
    // if the host in the url does not match the host of the window location, this url is considered external
    if (typeof match[2] === "string" &&
            match[2].length > 0 &&
            // this regex removes the port number if it patches the current location's protocol
            match[2].replace(new RegExp(":("+{"http:":80,"https:":443}[location.protocol]+")?$"), "") !== location.host)
        return true;
    return false;
};

// Utility method for replacing a portion of a string.
window.rewriteStaticLinks = function(content, from, to) {
    if (from === null || to === null) {
        return content;
    }
    // replace only relative urls
    function replacer(match){
        if (match === from){
            return to;
        }
        else {
            return match;
        }
    }
    // change all relative urls only which may be embedded inside other tags in content.
    // handle http and https
    // note: add other protocols here
    var regex = new RegExp("(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}([-a-zA-Z0-9@:%_\+.~#?&//=]*))?"+from, 'g');
    return content.replace(regex, replacer);
};

// Appends a parameter to a path; useful for indicating initial or return signin, for example
window.appendParameter = function(path, key, value) {
    // Check if the given path already contains a query string by looking for the ampersand separator
    if (path.indexOf("?") > -1) {
        var splitPath = path.split("?");
        var parameters = window.parseQueryString(splitPath[1]);
        // Check if the provided key already exists in the query string
        if (key in parameters) {
            // Overwrite the existing key's value with the provided value
            parameters[key] = value;

            // Reconstruct the path, including the overwritten key/value pair
            var reconstructedPath = splitPath[0] + "?";
            for (var k in parameters) {
                reconstructedPath = reconstructedPath + k + "=" + parameters[k] + "&";
            }
            // Strip the trailing ampersand
            return reconstructedPath.slice(0, -1);
        } else {
            // Check for a trailing ampersand
            if (path[path.length - 1] != "&") {
                // Append signin parameter to the existing query string
                return path + "&" + key + "=" + value;
            } else {
                // Append signin parameter to the existing query string, excluding the ampersand
                return path + key + "=" + value;
            }
        }
    } else {
        // Append new query string containing the provided parameter
        return path + "?" + key + "=" + value;
    }
};

// Convert a query string to a key/value object
window.parseQueryString = function(queryString) {
    var parameters = {}, queries, pair, i, l;

    // Split the query string into key/value pairs
    queries = queryString.split("&");

    // Break the array of strings into an object
    for (i = 0, l = queries.length; i < l; i++) {
        pair = queries[i].split('=');
        parameters[pair[0]] = pair[1];
    }

    return parameters
};

// Check if the user recently enrolled in a course by looking at a referral URL
window.checkRecentEnrollment = function(referrer) {
    var enrolledIn = null;
    
    // Check if the referrer URL contains a query string
    if (referrer.indexOf("?") > -1) {
        referrerQueryString = referrer.split("?")[1];
    } else {
        referrerQueryString = "";
    }

    if (referrerQueryString != "") {
        // Convert a non-empty query string into a key/value object
        var referrerParameters = window.parseQueryString(referrerQueryString);
        if ("course_id" in referrerParameters && "enrollment_action" in referrerParameters) {
            if (referrerParameters.enrollment_action == "enroll") {
                enrolledIn = referrerParameters.course_id;
            }
        }
    }

    return enrolledIn
};

window.assessUserSignIn = function(parameters, userID, email, username) {
    // Check if the user has logged in to enroll in a course - designed for when "Register" button registers users on click (currently, this could indicate a course registration when there may not have yet been one)
    var enrolledIn = window.checkRecentEnrollment(document.referrer);

    // Check if the user has just registered
    if (parameters.signin == "initial") {
        window.trackAccountRegistration(enrolledIn, userID, email, username);
    } else {
        window.trackReturningUserSignIn(enrolledIn, userID, email, username);
    }
};

window.trackAccountRegistration = function(enrolledIn, userID, email, username) {
    // Alias the user's anonymous history with the user's new identity (for Mixpanel)
    analytics.alias(userID);

    // Map the user's activity to their newly assigned ID
    analytics.identify(userID, {
        email: email,
        username: username
    });

    // Track the user's account creation
    analytics.track("edx.bi.user.account.registered", {
        category: "conversion",
        label: enrolledIn != null ? enrolledIn : "none"
    });
};

window.trackReturningUserSignIn = function(enrolledIn, userID, email, username) {
    // Map the user's activity to their assigned ID
    analytics.identify(userID, {
        email: email,
        username: username
    });

    // Track the user's sign in
    analytics.track("edx.bi.user.account.authenticated", {
        category: "conversion",
        label: enrolledIn != null ? enrolledIn : "none"
    });
};

window.identifyUser = function(userID, email, username) {
    // If the signin parameter isn't present but the query string is non-empty, map the user's activity to their assigned ID
    analytics.identify(userID, {
        email: email,
        username: username
    });    
};
