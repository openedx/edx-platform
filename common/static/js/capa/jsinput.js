(function (jsinput, undefined) {
    // Initialize js inputs on current page.
    // N.B.: No library assumptions about the iframe can be made (including,
    // most relevantly, jquery). Keep in mind what happens in which context
    // when modifying this file.

    // First time this function was called?
    var isFirst = typeof(jsinput.jsinputarr) != 'undefined';

    // Use this array to keep track of the elements that have already been
    // initialized.
    jsinput.jsinputarr = jsinput.jsinputarr || [];
    jsinput.jsinputarr.exists = function (id) {
        this.filter(function(e, i, a) {
            return e.id = id;
        });
    };
    

    function jsinputConstructor(spec) {
        // Define an class that will be instantiated for each jsinput element
        // of the DOM

        // 'that' is the object returned by the constructor. It has a single
        // public method, "update", which updates the hidden input field.
        var that = {};

        /*                      Private methods                          */

        var sect = $(spec.elem).parent().find('section[class="jsinput"]');
        // Get the hidden input field to pass to customresponse
        function inputfield() {
            var parent = $(spec.elem).parent();
            return parent.find('input[id^="input_"]');
        }

        // For the state and grade functions below, use functions instead of
        // storing their return values since we might need to call them
        // repeatedly, and they might change (e.g., they might not be defined
        // when we first try calling them).

        // Get the grade function name
        function getgradefn() {
            return $(sect).attr("data");
        }

        // Get state getter
        function getgetstate() {
            return $(sect).attr("data-getstate");
        }
        // Get state setter
        function getsetstate() {
            var gss  = $(sect).attr("data-setstate");
            return gss;
        }
        // Get stored state
        function getstoredstate() {
            return $(sect).attr("data-stored");
        }

        var thisIFrame = $(spec.elem).
                        find('iframe[name^="iframe_"]').
                        get(0);

        var cWindow = thisIFrame.contentWindow;

        // Put the return value of gradefn in the hidden inputfield.
        // If passed an argument, does not call gradefn, and instead directly
        // updates the inputfield with the passed value.
        var update = function (answer) {

            var ans;
            ans = cWindow[gradefn]();
            // setstate presumes getstate, so don't getstate unless setstate is
            // defined.
            if (getgetstate() && getsetstate()) {
                var state, store;
                state = cWindow[getgetstate()]();
                store = {
                    answer: ans,
                    state:  state
                };
                inputfield().val(JSON.stringify(store));
            } else {
                inputfield().val(ans);
            }
            return;
        };

        // Find the update button, and bind the update function to its click
        // event.
        function updateHandler() {
            var updatebutton = $(spec.elem).
                    find('button[class="update"]').get(0);
            $(updatebutton).click(update);
        }

        /*                       Public methods                     */

        that.update = update;



        /*                      Initialization                          */

        jsinput.jsinputarr.push(that);

        // Put the update function as the value of the inputfield's "waitfor"
        // attribute so that it is called when the check button is clicked.
        function bindCheck() {
            inputfield().data('waitfor', that.update);
            return;
        }

        var gradefn = getgradefn();

        if (spec.passive === false) {
            updateHandler();
            bindCheck();
            // Check whether application takes in state and there is a saved
            // state to give it. If getsetstate is specified but calling it
            // fails, wait and try again, since the iframe might still be
            // loading.
            if (getsetstate() && getstoredstate()) {
                var sval;
                if (typeof(getstoredstate()) === "object") {
                    sval = getstoredstate()["state"];
                } else {
                    sval = getstoredstate();
                }
                function whileloop(n) {
                    if (n < 10){
                        try {
                            cWindow[getsetstate()](sval);
                        } catch (err) {
                            setTimeout(whileloop(n+1), 200);
                        }
                    }
                    else {
                        console.log("Error: could not set state");
                    }
                }
                whileloop(0);
                
            }
        } else {
            // NOT CURRENTLY SUPPORTED
            // If set up to passively receive updates (intercept a function's
            // return value whenever the function is called) add an event
            // listener that listens to messages that match "that"'s id.
            // Decorate the iframe gradefn with updateDecorator.
            iframe.contentWindow[gradefn] = updateDecorator(iframe.contentWindow[gradefn]);
            iframe.contentWindow.addEventListener('message', function (e) {
                var id = e.data[0],
                    msg = e.data[1];
                if (id === spec.id) { update(msg); }
            });
        }


        return that;
    }

    function updateDecorator(fn, id) {
    // NOT CURRENTLY SUPPORTED
    // Simple function decorator that posts the output of a function to the
    // parent iframe before returning the original function's value.
    // Can be used to decorate one or more gradefn (instead of using an
    // explicit "Update" button) when gradefn is automatically called as part
    // of an application's natural behavior.
    // The id argument is used to specify which of the instances of jsinput on
    // the parent page the message is being posted to.
        return function () {
            var result = fn.apply(null, arguments);
            window.parent.contentWindow.postMessage([id, result], document.referrer);
            return result;
        };
    }

    function walkDOM() {
    // Find all jsinput elements, and create a jsinput object for each one
        var all = $(document).find('section[class="jsinput"]');
        var newid;
        all.each(function() {
            // Get just the mako variable 'id' from the id attribute
            newid = $(this).attr("id").replace(/^inputtype_/, "");
            if (! jsinput.jsinputarr.exists(newid)){
                var newJsElem = jsinputConstructor({
                    id: newid,
                    elem: this,
                    passive: false
                });
            }
        });
    }

    // TODO: Inject css into, and retrieve frame size from, the iframe (for non
    // "seamless"-supporting browsers).
    //var iframeInjection = {
        //injectStyles : function (style) {
            //$(document.body).css(style);
        //},
        //sendMySize : function () {
            //var height = html.height,
                //width = html.width;
            //window.parent.postMessage(['height', height], '*');
            //window.parent.postMessage(['width', width], '*');
        //}
    //};

   
    setTimeout(walkDOM, 100);
})(window.jsinput = window.jsinput || {})
