$(function() {
    var icons = {
        header: 'ui-icon-carat-1-s',
        activeHeader: 'ui-icon-carat-1-n'
    };
    var $proctoringAccordionPane = $('#proctoring-accordion');
    $proctoringAccordionPane.accordion(
        {
            heightStyle: 'content',
            animate: 400,
            header: '> .wrap > .hd',
            icons: icons,
            collapsible: true
        }
    );
});
