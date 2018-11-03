define(function(require) {
    var $ = require('jquery');
    var Jupyter = require('base/js/namespace');

   function load() {
        if (!Jupyter.notebook_list) return;
        var base_url = Jupyter.notebook_list.base_url;
        $("#tabs").append(
            $('<li>')
            .append(
                $('<a>')
                .attr('href', base_url + 'formgrader')
                .attr('target', '_blank')
                .text('Formgrader')
            )
        );
    }
    return {
        load_ipython_extension: load
    };
});
