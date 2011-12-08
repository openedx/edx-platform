var captions=0;
$("#slider").slider({slide:function(event,ui){seek_slide('slide',event.originalEvent,ui.value);},
                     stop:function(event,ui){seek_slide('stop',event.originalEvent,ui.value);}});
loadNewVideo('${id}');
