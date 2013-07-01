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
        console.log("hi");
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


    if ($(document).find('section[class="jsinput"]').length > jsinput.runs) {
        return;
    }


    /*                      Utils                               */


    jsinput._DEBUG = jsinput._DEBUG || true;

    var debuglog = function(text) { if (jsinput._DEBUG) { console.log(text);}};

    var eqTimeout = function(fn, pred, time, max) {
        var i = 0;
        while (pred(fn) && i < max) {
            setTimeout(fn, time);
        }
        return fn;
    };

    var isUndef = function (e) { return (typeof(e) === 'undefined'); };


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
        var sectattr = function (e) { return $(sect).attr(e); };
        var thisIFrame = $(spec.elem).
                        find('iframe[name^="iframe_"]').
                        get(0);
        var cWindow = thisIFrame.contentWindow;

        // Get the hidden input field to pass to customresponse
        function _inputfield() {
            var parent = $(spec.elem).parent();
            return parent.find('input[id^="input_"]');
        }
        var inputfield = _inputfield();

        // Get the grade function name
        var getgradefn = sectattr("data");
        // Get state getter
        var getgetstate = sectattr("data-getstate");
        // Get state setter
        var getsetstate = sectattr("data-setstate");
        // Get stored state
        var getstoredstate = sectattr("data-stored");



        // Put the return value of gradefn in the hidden inputfield.
        // If passed an argument, does not call gradefn, and instead directly
        // updates the inputfield with the passed value.
        var update = function (answer) {

            var ans;
            ans = _deepKey(cWindow, gradefn);
            // setstate presumes getstate, so don't getstate unless setstate is
            // defined.
            if (getgetstate && getsetstate) {
                var state, store;
                state = _deepKey(cWindow, getgetstate);
                store = {
                    answer: ans,
                    state:  state
                };

                debuglog("Store: " + store);
                inputfield.val(JSON.stringify(store));
            } else {
                inputfield.val(ans);
                debuglog("Answer: " + ans);
            }
            return;
        };

        // Find the update button, and bind the update function to its click
        // event.
        function bindUpdate() {
            var updatebutton = $(spec.elem).
                    find('button[class="update"]').
                    get(0);
            $(updatebutton).click(update);
        }

        /*                       Public methods                     */

        that.update = update;



        /*                      Initialization                          */

        jsinput.arr.push(that);

        // Put the update function as the value of the inputfield's "waitfor"
        // attribute so that it is called when the check button is clicked.
        function bindCheck() {
            debuglog("Update function: " + that.update);
            inputfield.data('waitfor', that.update);
            return;
        }

        var gradefn = getgradefn;
        debuglog("Gradefn: " + gradefn);

        if (spec.passive === false) {
            // If there is a separate "Update" button, bind update to it.
            bindUpdate();
        } else {
            // Otherwise, bind update to the check button.
            bindCheck();
        }

        bindCheck();

        // Check whether application takes in state and there is a saved
        // state to give it. If getsetstate is specified but calling it
        // fails, wait and try again, since the iframe might still be
        // loading.
        if (getsetstate && getstoredstate) {
            var sval;
            if (typeof(getstoredstate) === "object") {
                sval = getstoredstate["state"];
            } else {
                sval = getstoredstate;
            }

            debuglog("Stored state: "+ sval);
            debuglog("Set_statefn: " + getsetstate);

            function whileloop(n) {
                if (n < 10){
                    try {
                        _deepKey(cWindow, getsetstate)(sval);
                    } catch (err) {
                        setTimeout(whileloop(n+1), 200);
                    }
                }
                else {
                    debuglog("Error: could not set state");
                    _deepKey(cWindow, getsetstate)(sval);
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
                    passive: true
                });
            }
        });
    }

    // This is ugly, but without a timeout pages with multiple/heavy jsinputs
    // don't load properly.
    if ($.isReady) {
        setTimeout(walkDOM, 1000);
    } else {
        $(document).ready(setTimeout(walkDOM, 1000));
    }

})(window.jsinput = window.jsinput || false);
