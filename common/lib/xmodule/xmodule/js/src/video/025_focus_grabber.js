(function (requirejs, require, define) {

// FocusGrabber module.
define(
'video/025_focus_grabber.js',
[],
function () {
    return function (state) {
        state.focusGrabber = {};

        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);
    };


    // Private functions.

    function _makeFunctionsPublic(state) {
        state.focusGrabber.enableFocusGrabber = _.bind(enableFocusGrabber, state);
        state.focusGrabber.disableFocusGrabber = _.bind(disableFocusGrabber, state);
        state.focusGrabber.onFocus = _.bind(onFocus, state);
        state.focusGrabber.onBlur = _.bind(onBlur, state);
    }

    function _renderElements(state) {
        state.focusGrabber.elFirst = state.el.find('.focus_grabber.first');
        state.focusGrabber.elLast = state.el.find('.focus_grabber.last');

        state.focusGrabber.disableFocusGrabber();
    }

    function _bindHandlers(state) {
        state.focusGrabber.elFirst.on('focus', state.focusGrabber.onFocus);
        state.focusGrabber.elLast.on('focus', state.focusGrabber.onFocus);

        state.focusGrabber.elFirst.on('blur', state.focusGrabber.onBlur);
        state.focusGrabber.elLast.on('blur', state.focusGrabber.onBlur);
    }


    // Public functions.

    function enableFocusGrabber() {
        var tabIndex;

        if ($(document.activeElement).parents().hasClass('video')) {
            tabIndex = -1;
        } else {
            tabIndex = 0;
        }

        this.focusGrabber.elFirst.attr('tabindex', tabIndex);
        this.focusGrabber.elLast.attr('tabindex', tabIndex);

        $(document.activeElement).blur();

        if (tabIndex === -1) {
            this.focusGrabber.elFirst.trigger(
                'focus',
                {
                    simpleFocus: true
                }
            );
        }
    }

    function disableFocusGrabber() {
        this.focusGrabber.elFirst.attr('tabindex', -1);
        this.focusGrabber.elLast.attr('tabindex', -1);
    }

    function onFocus(event, params) {
        if (params && params.simpleFocus) {
            this.focusGrabber.elFirst.attr('tabindex', 0);
            this.focusGrabber.elLast.attr('tabindex', 0);

            return;
        }

        this.el.trigger('mousemove');
        this.el.trigger('focus');

        $('html, body').animate({
            scrollTop: this.el.offset().top
        }, 200);

        this.focusGrabber.disableFocusGrabber();
    }

    function onBlur(event) {
        this.el.trigger('mousemove');
        this.el.trigger('focus');

        $('html, body').animate({
            scrollTop: this.el.offset().top
        }, 200);
    }
});
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
