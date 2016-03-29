// overwrite the loaded method and manually start the karma after a delay
// Somehow the code initialized in jQuery's onready doesn't get called before karma auto starts
window.__karma__.loaded = function () {
    setTimeout(function () {
        window.__karma__.start();
    }, 1000);
};