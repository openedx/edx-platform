$("#accordion").accordion({
  active: ${ active_chapter },
  header: 'h3',
  autoHeight: false,
});

$("#open_close_accordion").click(function(){
  if ($("#accordion").hasClass("closed")){
    $("#accordion").removeClass("closed");
  } else {
    $("#accordion").addClass("closed");
  }
});

$('.ui-accordion').bind('accordionchange', function(event, ui) {
   var event_data = {'newheader':ui.newHeader.text(),
         'oldheader':ui.oldHeader.text()};
   log_event('accordion', event_data);
});
