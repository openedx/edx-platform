var streams=${ streams }

var params = { allowScriptAccess: "always", bgcolor: "#cccccc" };
var atts = { id: "myytplayer" };
swfobject.embedSWF("http://www.youtube.com/apiplayer?enablejsapi=1&playerapiid=ytplayer", 
		   "ytapiplayer", "600", "450", "8", null, null, params, atts);
var captions=0;
$("#slider").slider({slide:function(event,ui){seek_slide('slide',event.originalEvent,ui.value);},
                     stop:function(event,ui){seek_slide('stop',event.originalEvent,ui.value);}});

function good() {
    	window['console'].log(ytplayer.getCurrentTime());
}

ajax_video=good;

loadNewVideo(streams["1.0"], ${ video_time });

function add_speed(key, stream) {
    var id = 'speed_' + stream
    $("#video_speeds").append(' <span id="'+id+'">'+key+'X</span>');
    $("#"+id).click(function(){
	    change_video_speed(key, stream)
	});
}

var l=[]
for (var key in streams) {
    l.push(key);
}

function sort_by_value(a,b) {
    var x=parseFloat(a);
    var y=parseFloat(b);
    var r=((x < y) ? -1 : ((x > y) ? 1 : 0));
    return r;
}

l.sort(sort_by_value);

for(var i=0; i<l.length; i++) {
    add_speed(l[i], streams[l[i]])
}
