var formulaEquationPreview = {
    minDelay: 300,  // Minimum time between requests sent out.
    errorDelay: 1500  // Wait time before showing error (prevent frustration).
};

/** Setup the FormulaEquationInputs and associated javascript code. */
formulaEquationPreview.enable = function () {

    /**
     * Accumulate all the variables and attach event handlers.
     * This includes rate-limiting `sendRequest` and creating a closure for
     * its callback.
     */
    function setupInput() {
        var $this = $(this); // cache the jQuery object

        var $preview = $("#" + this.id + "_preview");
        var inputData = {
            // These are the mutable values

            lastSent: 0,
            isWaitingForRequest: false,
            requestVisible: 0,
            errorDelayTimeout: null,

            // The following don't change

            // Find the URL from the closest parent problems-wrapper.
            url: $this.closest('.problems-wrapper').data('url'),
            // Grab the input id from the input.
            inputId: $this.data('input-id'),

            // Store the DOM/MathJax elements in which visible output occurs.
            $preview: $preview,
            jax: null,  // Fill this in later.
            $img: $preview.find("img.loading"),

            requestCallback: null  // Fill it in in a bit.
        };

        // Give callback access to `inputData` (fill in first parameter).
        inputData.requestCallback = _.partial(updatePage, inputData);

        // Limit `sendRequest` and have it show the loading icon.
        var throttledRequest = _.throttle(
            sendRequest,
            formulaEquationPreview.minDelay,
            {leading: false}
        );
        // The following acts as a closure of `inputData`.
        var initializeRequest = function () {
            // Show the loading icon.
            inputData.$img.css('visibility', 'visible');

            // Say we are waiting for request.
            inputData.isWaitingForRequest = true;
            // First thing in `sendRequest`, say we aren't anymore.
            throttledRequest(inputData, this.value);
        };

        $this.on("input", initializeRequest);
        // Ask for initial preview.
        initializeRequest.call(this);
    }

    /**
     * Fire off a request for a preview of the current value.
     * Also send along the time it was sent, and store that locally.
     */
    function sendRequest(inputData, formula) {
        // Save the time.
        var now = Date.now();
        inputData.lastSent = now;
        // We're sending it.
        inputData.isWaitingForRequest = false;

        if (formula) {
            // Send the request.
            Problem.inputAjax(
                inputData.url,
                inputData.inputId,
                'preview_formcalc',
                {"formula" : formula, "request_start" : now},
                inputData.requestCallback
            );
            // ).fail(function () {
            //     // This is run when ajax call fails.
            //     // Have an error message and other stuff here?
            //     inputData.$img.css('visibility', 'hidden');
            // });
        }
        else {
            inputData.requestCallback({
                preview: '',
                request_start: now
            });
        }
    }

    /**
     * Respond to the preview request if need be.
     * Stop if it is outdated (i.e. a later request arrived back earlier)
     * Otherwise:
     * -Refresh the MathJax
     * -Stop the loading icon if this is the most recent request
     * -Save which request is visible
     */
    function updatePage(inputData, response) {
        var requestStart = response['request_start'];
        if (requestStart == inputData.lastSent &&
            !inputData.isWaitingForRequest) {
            // Disable icon.
            inputData.$img.css('visibility', 'hidden');
        }

        if (requestStart <= inputData.requestVisible) {
            // This is an old request.
            return;
        }

        // Save the value of the last response displayed.
        inputData.requestVisible = requestStart;

        // Prevent an old error message from showing.
        if (inputData.errorWaitTimeout != null) {
            window.clearTimeout(inputData.errorWaitTimeout);
        }

        function display(latex) {
            MathJax.Hub.Startup.signal.Interest(function (message) {
                if(message === "End") {
                    var previewElement = inputData.$preview[0];
                    MathJax.Hub.Queue(function () {
                        inputData.jax = MathJax.Hub.getAllJax(previewElement)[0];
                    });

                    MathJax.Hub.Queue(function () {
                        // Check if MathJax is loaded
                        if (inputData.jax) {
                            // Set the text as the latex code, and then update the MathJax.
                            MathJax.Hub.Queue(
                                ['Text', inputData.jax, latex]
                            );
                        } else if (latex) {
                            console.log("[FormulaEquationInput] Oops no mathjax for ", latex);
                            // Fall back to modifying the actual element.
                            var textNode = previewElement.childNodes[0];
                            textNode.data = "\\[" + latex + "\\]";
                            MathJax.Hub.Queue(["Typeset", MathJax.Hub, previewElement]);
                        }
                    });
                }
            });
        }

        if (response.error) {
            inputData.$img.css('visibility', 'visible');
            inputData.errorWaitTimeout = window.setTimeout(function () {
                display("\\text{" + response.error + "}");
                inputData.$img.css('visibility', 'hidden');
            }, formulaEquationPreview.errorDelay);
        } else {
            display(response.preview);
        }
    }

    // Invoke the setup method.
    $('.formulaequationinput input').each(setupInput);
};

formulaEquationPreview.enable();
