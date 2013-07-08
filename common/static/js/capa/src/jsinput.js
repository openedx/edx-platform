(function (jsinput, undefined) {
    // Initialize js inputs on current page.
    // N.B.: No library assumptions about the iframe can be made (including,
    // most relevantly, jquery). Keep in mind what happens in which context
    // when modifying this file.

    /*      Check whether there is anything to be done      */

    // When all the problems are first loaded, we want to make sure the
    // constructor only runs once for each iframe; but we also want to make
    // sure that if part of the page is reloaded (e.g., a problem is
    // submitted), the constructor is called again.

    if (!jsinput) {
        jsinput = {
            runs : 1,
            arr : [],
            exists : function(id) {
                jsinput.arr.filter(function(e, i, a) {
                    return e.id = id;
                });
            }
        };
    }

    jsinput.runs++;


    /*                      Utils                               */


    // Take a string and find the nested object that corresponds to it. E.g.:
    //    deepKey(obj, "an.example") -> obj["an"]["example"]
    var _deepKey = function(obj, path){
        for (var i = 0, p=path.split('.'), len = p.length; i < len; i++){
            obj = obj[p[i]];
        }
        return obj;
    };


    /*      END     Utils                                   */




    function jsinputConstructor(spec) {
        // Define an class that will be instantiated for each jsinput element
        // of the DOM

        // 'that' is the object returned by the constructor. It has a single
        // public method, "update", which updates the hidden input field.
        var that = {};

        /*                      Private methods                          */

        var sect = $(spec.elem).parent().find('section[class="jsinput"]');
        var sectAttr = function (e) { return $(sect).attr(e); };
        var thisIFrame = $(spec.elem).
                        find('iframe[name^="iframe_"]').
                        get(0);
        var cWindow = thisIFrame.contentWindow;

        // Get the hidden input field to pass to customresponse
        function _inputField() {
            var parent = $(spec.elem).parent();
            return parent.find('input[id^="input_"]');
        }
        var inputField = _inputField();

        // Get the grade function name
        var getGradeFn = sectAttr("data");
        // Get state getter
        var getStateGetter = sectAttr("data-getstate");
        // Get state setter
        var getStateSetter = sectAttr("data-setstate");
        // Get stored state
        var getStoredState = sectAttr("data-stored");



        // Put the return value of gradeFn in the hidden inputField.
        var update = function () {
            var ans;

            ans = _deepKey(cWindow, gradeFn)();
            // setstate presumes getstate, so don't getstate unless setstate is
            // defined.
            if (getStateGetter && getStateSetter) {
                var state, store;
                state = unescape(_deepKey(cWindow, getStateGetter)());
                store = {
                    answer: ans,
                    state:  state
                };
                inputField.val(JSON.stringify(store));
            } else {
                inputField.val(ans);
            }
            return;
        };

        /*                       Public methods                     */

        that.update = update;



        /*                      Initialization                          */

        jsinput.arr.push(that);

        // Put the update function as the value of the inputField's "waitfor"
        // attribute so that it is called when the check button is clicked.
        function bindCheck() {
            inputField.data('waitfor', that.update);
            return;
        }

        var gradeFn = getGradeFn;


        bindCheck();

        // Check whether application takes in state and there is a saved
        // state to give it. If getStateSetter is specified but calling it
        // fails, wait and try again, since the iframe might still be
        // loading.
        if (getStateSetter && getStoredState) {
            var sval, jsonVal;

            try {
              jsonVal = JSON.parse(getStoredState);
            } catch (err) {
              jsonVal = getStoredState;
            }

            if (typeof(jsonVal) === "object") {
                sval = jsonVal["state"];
            } else {
                sval = jsonVal;
            }


            // Try calling setstate every 200ms while it throws an exception,
            // up to five times; give up after that.
            // (Functions in the iframe may not be ready when we first try
            // calling it, but might just need more time. Give the functions
            // more time.)
            function whileloop(n) {
                if (n < 5){
                    try {
                        _deepKey(cWindow, getStateSetter)(sval);
                    } catch (err) {
                        setTimeout(whileloop(n+1), 200);
                    }
                }
                else {
                    console.debug("Error: could not set state");
                }
            }
            whileloop(0);

        }


        return that;
    }


    function walkDOM() {
        var newid;

        // Find all jsinput elements, and create a jsinput object for each one
        var all = $(document).find('section[class="jsinput"]');

        all.each(function(index, value) {
            // Get just the mako variable 'id' from the id attribute
            newid = $(value).attr("id").replace(/^inputtype_/, "");


            if (!jsinput.exists(newid)){
                var newJsElem = jsinputConstructor({
                    id: newid,
                    elem: value,
                });
            }
        });
    }

    // This is ugly, but without a timeout pages with multiple/heavy jsinputs
    // don't load properly.
    if ($.isReady) {
        setTimeout(walkDOM, 300);
    } else {
        $(document).ready(setTimeout(walkDOM, 300));
    }

})(window.jsinput = window.jsinput || false);
