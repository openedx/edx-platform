(function () {
    var min_delay = 300; // milliseconds between AJAX requests

    // Dictionary holding information indexed by the IDs of the problems
    var preview_data = {};

    function update() {
        /**
           Given a user input, either send a request or enqueue one to be sent.

           Don't call `send_request` if it's been less than `min_delay` ms.
           Also, indicate that it is loading (using the loading icon).
         */
        var data = preview_data[this.id];

        var time_since_last = Date.now() - data.last_sent;
        var bound_send_request = send_request.bind(this);

        if (time_since_last >= min_delay) {
            // If it's been long enough, just send the request
            bound_send_request();
        }
        else {
            // Otherwise, enqueue.
            if (data.timeout_id !== null) {
                // Clear any other queued requests.
                window.clearTimeout(data.timeout_id);
            }

            // Wait for the rest of the `min_delay`.
            // Store `timeout_id`
            var wait_time = min_delay - time_since_last;
            data.timeout_id = window.setTimeout(bound_send_request, wait_time);
        }

        // Show the loading icon.
        data.$loading.show();
    }

    function send_request() {
        /**
           Fire off a request for a preview of the current value.

           Also send along the time it was sent, and store that locally.
        */
        var data = preview_data[this.id];
        data.timeout_id = null;

        var $this = $(this); // cache the jQuery object

        // Save the time.
        var now = Date.now();
        data.last_sent = now;

        // Find the closest parent problems-wrapper and use that url.
        var url = $this.closest('.problems-wrapper').data('url');
        // Grab the input id from the input.
        var input_id = $this.data('input-id')

        Problem.inputAjax(url, input_id, 'preview_formcalc', {
          "formula" : this.value,
          "request_start" : now
        }, create_handler(data));
        // TODO what happens when an AJAX call is lost?
    }

    function create_handler(data) {
        /** Create a closure for `data` */
        return (function (response) {
            /**
               Respond to the preview request

               Optionally, stop if it is outdated (a later request arrived
               back earlier)

               Otherwise:
               -Refresh the MathJax
               -Stop the loading icon if need be
               -Save which request this is
            */
            if (response.request_start == data.last_sent &&
                data.timeout_id === null) {
                data.$loading.hide();  // Disable icon
            }

            if (response.request_start <= data.request_visible) {
                return;  // This is an old request.
            }

            // Save the value of the last response displayed.
            data.request_visible = response.request_start;

            var jax = MathJax.Hub.getAllJax(data.$preview[0])[0];
            var math_code;
            if (response.error) {
                // TODO: wait for a bit to display error
                math_code = "\text{" + response.error + "}";
            } else {
                math_code = response.preview;
            }

            // Set the text as the latex code, and then update the MathJax.
            MathJax.Hub.Queue(
                ['Text', jax, math_code],
                ['Reprocess', jax]
            );
        });
    }

    inputs = $('.formulaequationinput input');
    // Store information for each input and cache the jQuery objects
    inputs.each(function () {
        var prev_id = "#" + this.id + "_preview";
        preview_data[this.id] = {
            $preview: $(prev_id),
            $loading: $(prev_id + " img.loading").hide(),
            last_sent: 0,  // The time of the one that was last sent
            request_visible: 0,  // The original time of the visible request
            timeout_id: null  // If there is a timeout, store its ID here
        };
    });
    // update on load
    inputs.each(update);
    // and on every change
    inputs.bind("input", update);
}).call(this);
