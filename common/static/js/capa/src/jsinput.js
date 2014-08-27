/* 
 * JSChannel (https://github.com/mozilla/jschannel) will be loaded prior to this
 * script. We will use it use to let JSInput call 'gradeFn', and eventually 
 * 'stateGetter' & 'stateSetter' in the iframe's content even if it hasn't the 
 * same origin, therefore bypassing SOP:
 * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Same_origin_policy_for_JavaScript
 */    

var JSInput = (function ($, undefined) {
    // Initialize js inputs on current page.
    // N.B.: No library assumptions about the iframe can be made (including,
    // most relevantly, jquery). Keep in mind what happens in which context
    // when modifying this file.

    // When all the problems are first loaded, we want to make sure the
    // constructor only runs once for each iframe; but we also want to make
    // sure that if part of the page is reloaded (e.g., a problem is
    // submitted), the constructor is called again.

    /*                      Utils                               */


    // Take a string and find the nested object that corresponds to it. E.g.:
    //    _deepKey(obj, "an.example") -> obj["an"]["example"]
    function _deepKey(obj, path){
        for (var i = 0, p=path.split('.'), len = p.length; i < len; i++){
            obj = obj[p[i]];
        }
        return obj;
    };


    /*      END     Utils                                   */


    function jsinputConstructor(elem) {
        // Define an class that will be instantiated for each jsinput element
        // of the DOM

        /*                      Private methods                          */

        var section = $(elem).parent().find('section[class="jsinput"]'),
            sectionAttr = function (e) { return $(section).attr(e); },
            iframe = $(elem).find('iframe[name^="iframe_"]').get(0),
            cWindow = iframe.contentWindow,
            path = iframe.src.substring(0, iframe.src.lastIndexOf("/")+1),
            // Get the hidden input field to pass to customresponse
            inputField = $(elem).parent().find('input[id^="input_"]'),
            // Get the grade function name
            gradeFn = sectionAttr("data"),
            // Get state getter
            stateGetter = sectionAttr("data-getstate"),
            // Get state setter
            stateSetter = sectionAttr("data-setstate"),
            // Get stored state
            storedState = sectionAttr("data-stored"),
            // Get initial state
            initialState = sectionAttr("data-initial-state"),
            // Bypass single-origin policy only if this attribute is "false"
            // In that case, use JSChannel to do so.
            sop = sectionAttr("data-sop"),
            channel;
        
        sop = (sop !== "false");

        if (!sop) {
            channel = Channel.build({
                window: cWindow,
                origin: path,
                scope: "JSInput"
            });
         }   

        /*                       Public methods                     */
        
        // Only one public method that updates the hidden input field.
        var update = function (callback) {
            var answer, state, store;

            if (sop) {
                answer = _deepKey(cWindow, gradeFn)();
                // Setting state presumes getting state, so don't get state
                // unless set state is defined.
                if (stateGetter && stateSetter) {
                    state = unescape(_deepKey(cWindow, stateGetter)());
                    store = {
                        answer: answer,
                        state:  state
                    };
                    inputField.val(JSON.stringify(store));
                } else {
                    inputField.val(answer);
                }
                callback();
            } else {
                channel.call({
                    method: "getGrade",
                    params: "",
                    success: function(val) {
                        answer = decodeURI(val.toString());

                        // Setting state presumes getting state, so don't get
                        // state unless set state is defined.
                        if (stateGetter && stateSetter) {
                            channel.call({
                                method: "getState",
                                params: "",
                                success: function(val) {
                                    state = decodeURI(val.toString());
                                    store = {
                                        answer: answer,
                                        state:  state
                                    };
                                    inputField.val(JSON.stringify(store));
                                    callback();
                                }
                            });
                        } else {
                            inputField.val(answer);
                            callback();
                        }
                    }
                });
            }
        };

        /*                      Initialization                          */

        // Put the update function as the value of the inputField's "waitfor"
        // attribute so that it is called when the check button is clicked.
        inputField.data('waitfor', update);

        // Check whether application takes in state and there is a saved
        // state to give it. If stateSetter is specified but calling it
        // fails, wait and try again, since the iframe might still be
        // loading.
        if (stateSetter && (storedState || initialState)) {
            var stateValue, jsonValue;

            if (storedState) {
                try {
                    jsonValue = JSON.parse(storedState);
                } catch (err) {
                    jsonValue = storedState;
                }

                if (typeof(jsonValue) === "object") {
                    stateValue = jsonValue["state"];
                } else {
                    stateValue = jsonValue;
                }
            }
            else {
                // use initial_state string as the JSON string for stateValue.
                stateValue = initialState;
            }

            // Try calling setstate every 200ms while it throws an exception,
            // up to five times; give up after that.
            // (Functions in the iframe may not be ready when we first try
            // calling it, but might just need more time. Give the functions
            // more time.)
            // 200 ms and 5 times are arbitrary but this has functioned with the
            // only application that has ever used JSInput, jsVGL. Something 
            // more sturdy should be put in place.
            function whileloop(n) {
                if (n > 0){
                    try {
                        if (sop) {
                            _deepKey(cWindow, stateSetter)(stateValue);
                        } else {
                            channel.call({
                                method: "setState",
                                params: stateValue,
                                success: function() {
                                }    
                            });
                        }
                    } catch (err) {
                        setTimeout(function() { whileloop(n - 1); }, 200);
                    }
                }
                else {
                    console.debug("Error: could not set state");
                }
            }
            whileloop(5);
        }
    }

    function walkDOM() {
        var allSections = $('section.jsinput');
        // When a JSInput problem loads, its data-processed attribute is false,
        // so the jsconstructor will be called for it.
        // The constructor will not be called again on subsequent reruns of
        // this file by other JSInput. Only if it is reloaded, either with the
        // rest of the page or when it is submitted, will this constructor be
        // called again.
        allSections.each(function(index, value) {
            var dataProcessed = ($(value).attr("data-processed") === "true");
            if (!dataProcessed) {
                jsinputConstructor(value);
                $(value).attr("data-processed", 'true');
            }
        });
    }

    // This is ugly, but without a timeout pages with multiple/heavy jsinputs
    // don't load properly.
    // 300 ms is arbitrary but this has functioned with the only application 
    // that has ever used JSInput, jsVGL. Something more sturdy should be put in
    // place.
    if ($.isReady) {
        setTimeout(walkDOM, 300);
    } else {
        $(document).ready(setTimeout(walkDOM, 300));
    }

    return {
        jsinputConstructor: jsinputConstructor,
        walkDOM: walkDOM
    };
    
})(window.jQuery);
