$(function() {
    var icons = {
        header: 'ui-icon-carat-1-e',
        activeHeader: 'ui-icon-carat-1-s'
    };
    var proctoringAccordionPane = $('#proctoring-accordion');
    proctoringAccordionPane.accordion(
        {
            heightStyle: 'content',
            activate: function(event, ui) {
                var active = proctoringAccordionPane.accordion('option', 'active');
                $.cookie('saved_index', null);
                $.cookie('saved_index', active);
            },
            animate: 400,
            header: '> .wrap > .hd',
            icons: icons,
            active: isNaN(parseInt($.cookie('saved_index'))) ? 0 : parseInt($.cookie('saved_index')),
            collapsible: true
        }
    );
});
