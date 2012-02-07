$("#accordion").accordion({
  active: ${ active_chapter },
  header: 'h3',
  autoHeight: false,
});

$("#open_close_accordion").click(function(){
  if ($(".course-wrapper").hasClass("closed")){
    $(".course-wrapper").removeClass("closed");
  } else {
    $(".course-wrapper").addClass("closed");
  }
});

$('.ui-accordion').bind('accordionchange', function(event, ui) {
   var event_data = {'newheader':ui.newHeader.text(),
         'oldheader':ui.oldHeader.text()};
   log_event('accordion', event_data);
});
