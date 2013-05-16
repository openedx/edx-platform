(function (requirejs, require, define) {

// VideoSpeedControl module.
define(
'videoalpha/display/video_speed_control.js',
[],
function () {

    // VideoSpeedControl() function - what this module "exports".
    return function (state) {
        state.videoSpeedControl = {};

        makeFunctionsPublic(state);
        renderElements(state);
        bindHandlers(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function makeFunctionsPublic(state) {
        state.videoSpeedControl.changeVideoSpeed = changeVideoSpeed.bind(state);
        state.videoSpeedControl.setSpeed = setSpeed.bind(state);
        state.videoSpeedControl.reRender = reRender.bind(state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        state.videoSpeedControl.speeds = state.speeds;

        state.videoSpeedControl.el = state.el.find('div.speeds');

        state.videoSpeedControl.videoSpeedsEl = state.videoSpeedControl.el.find('.video_speeds');

        state.videoControl.secondaryControlsEl.prepend(state.videoSpeedControl.el);

        $.each(state.videoSpeedControl.speeds, function(index, speed) {
            var link = $('<a href="#">' + speed + 'x</a>');

            state.videoSpeedControl.videoSpeedsEl.prepend($('<li data-speed="' + speed + '">' + link + '</li>'));
        });

        state.videoSpeedControl.setSpeed(state.speed);
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {
        state.videoSpeedControl.videoSpeedsEl.find('a').on('click', state.videoSpeedControl.changeVideoSpeed);

        if (onTouchBasedDevice()) {
            state.videoSpeedControl.el.on('click', function(event) {
                event.preventDefault();
                $(this).toggleClass('open');
            });
        } else {
            state.videoSpeedControl.el
                .on('mouseenter', function () {
                    $(this).addClass('open');
                })
                .on('mouseleave', function () {
                    $(this).removeClass('open');
                })
                .on('click', function (event) {
                    event.preventDefault();
                    $(this).removeClass('open');
                });
        }
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function setSpeed(speed) {
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.videoSpeedsEl.find("li[data-speed='" + speed + "']").addClass('active');
        this.videoSpeedControl.el.find('p.active').html('' + speed + 'x');
    }

    function changeVideoSpeed(event) {
        var parentEl = $(event.target).parent();

        event.preventDefault();

        if (!parentEl.hasClass('active')) {
            this.videoSpeedControl.currentSpeed = parentEl.data('speed');

            this.videoSpeedControl.setSpeed(
                // To meet the API expected format.
                parseFloat(this.videoSpeedControl.currentSpeed).toFixed(2).replace(/\.00$/, '.0')
            );

            this.trigger(['videoPlayer', 'onSpeedChange'], this.videoSpeedControl.currentSpeed);
        }
    }

    function reRender(params) {
        var _this = this;

        this.videoSpeedControl.videoSpeedsEl.empty();
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.speeds = params.newSpeeds;

        $.each(this.videoSpeedControl.speeds, function(index, speed) {
            var link, listItem;

            link = $('<a href="#">' + speed + 'x</a>');

            listItem = $('<li data-speed="' + speed + '">' + link + '</li>');

            if (speed === params.currentSpeed) {
                listItem.addClass('active');
            }

            _this.videoSpeedControl.videoSpeedsEl.prepend(listItem);
        });

        this.videoSpeedControl.videoSpeedsEl.find('a').on('click', this.videoSpeedControl.changeVideoSpeed);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
