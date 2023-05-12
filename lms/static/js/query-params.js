// http://james.padolsey.com/javascript/bujs-1-getparameterbyname/
// eslint-disable-next-line no-unused-vars
function getParameterByName(name) {
    // eslint-disable-next-line no-var
    var match = RegExp('[?&]' + name + '=([^&]*)')
        .exec(window.location.search);

    return match
        ? decodeURIComponent(match[1].replace(/\+/g, ' '))
        : null;
}
