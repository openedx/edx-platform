(function() {
    update = function() {
        function create_handler(saved_div) {
            return (function(response) {
                if (response.error) {
                    edx.HtmlUtils.setHtml(
                        saved_div,
                        edx.HtmlUtils.joinHtml(
                            edx.HtmlUtils.HTML("<span class='error'>"),
                            response.error,
                            edx.HtmlUtils.HTML('</span>')
                        )
                    );
                } else {
                    saved_div.html(edx.HtmlUtils.HTML(response.preview).toString());
                }
            });
        }

        prev_id = '#' + this.id + '_preview';
        preview_div = $(prev_id);

        // find the closest parent problems-wrapper and use that url
        url = $(this).closest('.problems-wrapper').data('url');
        // grab the input id from the input
        input_id = $(this).data('input-id');

        Problem.inputAjax(url, input_id, 'preview_chemcalc', {formula: this.value}, create_handler(preview_div));
    };

    inputs = $('.chemicalequationinput input');
    // update on load
    inputs.each(update);
    // and on every change
    inputs.bind('input', update);
}).call(this);
