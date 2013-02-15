(function (requirejs, require, define) {

// Main module
require(
['videoalpha/display/initialize.js', 'videoalpha/display/video_player.js'],
function (Initialize, VideoPlayer) {
    window.VideoAlpha = function (element) {
        var state;

        state = {};

        new Initialize(state, element);
        new VideoPlayer(state);

        console.log('Finished constructing "state" object. state = ');
        console.log(state);
    };
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
