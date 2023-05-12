$(function() {
    // eslint-disable-next-line no-var
    var icons = {
        header: 'ui-icon-carat-1-s',
        activeHeader: 'ui-icon-carat-1-n'
    };
    // eslint-disable-next-line no-var
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
