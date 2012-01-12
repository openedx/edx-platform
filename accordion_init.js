$("#accordion").accordion({
  active: ${ active_chapter },
  autoHeight: false
});

$('.ui-accordion').bind('accordionchange', function(event, ui) {
   var event_data = {'newheader':ui.newHeader.text(),
		     'oldheader':ui.oldHeader.text()};
   log_event('accordion', event_data);
});
