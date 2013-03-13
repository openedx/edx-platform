(function (requirejs, require, define) {

// VideoSpeedControl module.
define(
'videoalpha/display/video_speed_control.js',
['videoalpha/display/bind.js'],
function (bind) {

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
        state.videoSpeedControl.changeVideoSpeed = bind(changeVideoSpeed, state);
        state.videoSpeedControl.setSpeed = bind(setSpeed, state);
        state.videoSpeedControl.reRender = bind(reRender, state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        state.videoSpeedControl.speeds = state.speeds;

        state.videoSpeedControl.el = $(
            '<div class="speeds">' +
                '<a href="#">' +
                    '<h3>Speed</h3>' +
                    '<p class="active"></p>' +
                '</a>' +
                '<ol class="video_speeds"></ol>' +
            '</div>'
        );

        state.videoSpeedControl.videoSpeedsEl = state.videoSpeedControl.el.find('.video_speeds');

        state.videoControl.secondaryControlsEl.prepend(state.videoSpeedControl.el);

        $.each(state.videoSpeedControl.speeds, function(index, speed) {
            var link;

            link = $('<a>').attr({
                'href': '#'
             }).html('' + speed + 'x');

            state.videoSpeedControl.videoSpeedsEl.prepend($('<li>').attr('data-speed', speed).html(link));
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
            state.videoSpeedControl.el.on('mouseenter', function() {
                $(this).addClass('open');
            });

            state.videoSpeedControl.el.on('mouseleave', function() {
                $(this).removeClass('open');
            });

            state.videoSpeedControl.el.on('click', function(event) {
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
        event.preventDefault();

        if (!$(event.target).parent().hasClass('active')) {
            this.videoSpeedControl.currentSpeed = $(event.target).parent().data('speed');

            this.videoSpeedControl.setSpeed(
                parseFloat(this.videoSpeedControl.currentSpeed).toFixed(2).replace(/\.00$/, '.0')
            );

            this.trigger(['videoPlayer', 'onSpeedChange'], this.videoSpeedControl.currentSpeed, 'method');
        }
    }

    function reRender(params /*newSpeeds, currentSpeed*/) {
        var _this;

        this.videoSpeedControl.videoSpeedsEl.empty();
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.speeds = params.newSpeeds;

        _this = this;
        $.each(this.videoSpeedControl.speeds, function(index, speed) {
            var link, listItem;

            link = $('<a>').attr({
                'href': '#'
            }).html('' + speed + 'x');

            listItem = $('<li>').attr('data-speed', speed).html(link);

            if (speed === params.currentSpeed) {
                listItem.addClass('active');
            }

            _this.videoSpeedControl.videoSpeedsEl.prepend(listItem);
        });

        this.videoSpeedControl.videoSpeedsEl.find('a').on('click', this.videoSpeedControl.changeVideoSpeed);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
