var streams=${ streams }
var params = { allowScriptAccess: "always", bgcolor: "#cccccc", wmode: "transparent", allowFullScreen: "true" };
var atts = { id: "myytplayer" };

// If the user doesn't have flash, use the HTML5 Video instead. YouTube's
// iFrame API which supports HTML5 is still developmental so it is not default
if (swfobject.hasFlashPlayerVersion("10.1")){
  swfobject.embedSWF("http://www.youtube.com/apiplayer?enablejsapi=1&playerapiid=ytplayer?wmode=transparent",
        "ytapiplayer", "640", "385", "8", null, null, params, atts);
} else {

  $("#html5_player").attr("src", "http://www.youtube.com/embed/" + streams["1.0"] + "?enablejsapi=1&controls=0&origin=" + document.domain);
  $("#html5_player").show();

  var tag = document.createElement('script');
  tag.src = "http://www.youtube.com/player_api";
  var firstScriptTag = document.getElementsByTagName('script')[0];
  firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

  // Make sure the callback is called once API ready, YT seems to be buggy
  loadHTML5Video();
}
var captions=0;
$("#slider").slider({slide:function(event,ui){seek_slide('slide',event.originalEvent,ui.value);},
                     stop:function(event,ui){seek_slide('stop',event.originalEvent,ui.value);}});

function good() {
    window['console'].log(ytplayer.getCurrentTime());
}

ajax_video=good;

loadNewVideo(streams["1.0"], ${ position });

function add_speed(key, stream) {
    var id = 'speed_' + stream;
    $("#video_speeds").append(' <span id="'+id+'">'+key+'X</span>');
    $("#"+id).click(function(){
      change_video_speed(key, stream);
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
