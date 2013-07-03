(function () {
    update = function() {
        function create_handler(saved_div) {
            return (function(response) {
                if (saved_div.data('last-response') > response['request-start']) {
                    return;
                }
                else {
                    saved_div.data('last-response', response['request-start']);
                }

                var jax = MathJax.Hub.getAllJax(saved_div[0])[0];
                var math_code;
                if (response.error) {
                    math_code = "\text{" + response.error + "}";
                    //saved_div.html("<span class='error'>" + response.error + "</span>");
                } else {
                    math_code = response.preview;
                    //saved_div.html(response.preview);
                }
                MathJax.Hub.Queue(['Text', jax, math_code],
                                  ['Reprocess', jax]);
            });
        }

        prev_id = "#" + this.id + "_preview";
        preview_div = $(prev_id);

        // find the closest parent problems-wrapper and use that url
        url = $(this).closest('.problems-wrapper').data('url');
        // grab the input id from the input
        input_id = $(this).data('input-id')

        Problem.inputAjax(url, input_id, 'preview_formcalc', {
          "formula" : this.value,
          "request-start" : Date.now()
        }, create_handler(preview_div));
    }

    inputs = $('.formulaequationinput input');
    // set last-response to 0 on all inputs
    inputs.each(function () {
        prev_id = "#" + this.id + "_preview";
        $(prev_id).data('last-response', 0);
    });
    // update on load
    inputs.each(update); 
    // and on every change
    inputs.bind("input", update);
}).call(this);
