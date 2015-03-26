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
    // escape all regex interpretable chars
    fromRe = from.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    var regex = new RegExp("(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}([-a-zA-Z0-9@:%_\+.~#?&//=]*))?"+fromRe, 'g');
    return content.replace(regex, replacer);
};
