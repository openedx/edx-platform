(function() {
    // eslint-disable-next-line no-undef
    update = function() {
        // eslint-disable-next-line camelcase
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
                    // eslint-disable-next-line camelcase
                    saved_div.html(edx.HtmlUtils.HTML(response.preview).toString());
                }
            });
        }

        /* eslint-disable-next-line camelcase, no-undef */
        prev_id = '#' + this.id + '_preview';
        /* eslint-disable-next-line camelcase, no-undef */
        preview_div = $(prev_id);

        // find the closest parent problems-wrapper and use that url
        // eslint-disable-next-line no-undef
        url = $(this).closest('.problems-wrapper').data('url');
        // grab the input id from the input
        /* eslint-disable-next-line camelcase, no-undef */
        input_id = $(this).data('input-id');

        // eslint-disable-next-line no-undef
        Problem.inputAjax(url, input_id, 'preview_chemcalc', {formula: this.value}, create_handler(preview_div));
    };

    // eslint-disable-next-line no-undef
    inputs = $('.chemicalequationinput input');
    // update on load
    // eslint-disable-next-line no-undef
    inputs.each(update);
    // and on every change
    // eslint-disable-next-line no-undef
    inputs.bind('input', update);
}).call(this);
