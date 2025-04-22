// eslint-disable-next-line no-shadow
function format(time, formatFull) {
    var hours, minutes, seconds;

    if (!_.isFinite(time) || time < 0) {
        time = 0;
    }

    seconds = Math.floor(time);
    minutes = Math.floor(seconds / 60);
    hours = Math.floor(minutes / 60);
    seconds %= 60;
    minutes %= 60;

    if (formatFull) {
        return '' + _pad(hours) + ':' + _pad(minutes) + ':' + _pad(seconds % 60);
    } else if (hours) {
        return '' + hours + ':' + _pad(minutes) + ':' + _pad(seconds % 60);
    } else {
        return '' + minutes + ':' + _pad(seconds % 60);
    }
}

function formatFull(time) {
    // The returned value will not be user-facing. So no need for
    // internationalization.
    return format(time, true);
}

function convert(time, oldSpeed, newSpeed) {
    // eslint-disable-next-line no-mixed-operators
    return (time * oldSpeed / newSpeed).toFixed(3);
}

function _pad(number) {
    if (number < 10) {
        return '0' + number;
    } else {
        return '' + number;
    }
}

export default {format, formatFull, convert};
