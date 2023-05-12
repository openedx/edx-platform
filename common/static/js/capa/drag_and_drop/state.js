(function(requirejs, require, define) {
    define([], function() {
        // eslint-disable-next-line no-use-before-define
        return State;

        function State(problemId) {
            // eslint-disable-next-line no-var
            var state;

            state = {
                config: null,

                baseImageEl: null,
                baseImageLoaded: false,

                containerEl: null,

                sliderEl: null,

                problemId: problemId,

                draggables: [],
                numDraggablesInSlider: 0,
                currentMovingDraggable: null,

                targets: [],

                updateArrowOpacity: null,

                uniqueId: 0,
                // eslint-disable-next-line no-use-before-define
                salt: makeSalt(),

                // eslint-disable-next-line no-use-before-define
                getUniqueId: getUniqueId
            };

            $(document).mousemove(function(event) {
                // eslint-disable-next-line no-use-before-define
                documentMouseMove(state, event);
            });

            return state;
        }

        function getUniqueId() {
            this.uniqueId += 1;

            return this.salt + '_' + this.uniqueId.toFixed(0);
        }

        function makeSalt() {
            // eslint-disable-next-line no-var
            var text, possible, i;

            text = '';
            possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

            for (i = 0; i < 5; i += 1) {
                text += possible.charAt(Math.floor(Math.random() * possible.length));
            }

            return text;
        }

        function documentMouseMove(state, event) {
            if (state.currentMovingDraggable !== null) {
                state.currentMovingDraggable.iconEl.css(
                    'left',
                    event.pageX
                    - state.baseImageEl.offset().left
                    - state.currentMovingDraggable.iconWidth * 0.5
                    - state.currentMovingDraggable.iconElLeftOffset
                );
                state.currentMovingDraggable.iconEl.css(
                    'top',
                    event.pageY
                    - state.baseImageEl.offset().top
                    - state.currentMovingDraggable.iconHeight * 0.5
                );

                if (state.currentMovingDraggable.labelEl !== null) {
                    state.currentMovingDraggable.labelEl.css(
                        'left',
                        event.pageX
                        - state.baseImageEl.offset().left
                        - state.currentMovingDraggable.labelWidth * 0.5
                        - 9 // Account for padding, border.
                    );
                    state.currentMovingDraggable.labelEl.css(
                        'top',
                        event.pageY
                        - state.baseImageEl.offset().top
                        + state.currentMovingDraggable.iconHeight * 0.5
                        + 5
                    );
                }
            }
        }
    }); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
