$(function() {
    var icons = {
        header: 'ui-icon-carat-1-e',
        activeHeader: 'ui-icon-carat-1-s'
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
