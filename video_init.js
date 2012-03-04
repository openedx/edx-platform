var streams=${ streams }
var params = { allowScriptAccess: "always", bgcolor: "#cccccc", wmode: "transparent", allowFullScreen: "true" };
var atts = { id: "myytplayer" };

// If the user doesn't have flash, use the HTML5 Video instead. YouTube's
// iFrame API which supports HTML5 is still developmental so it is not default
if (swfobject.hasFlashPlayerVersion("10.1")){
  swfobject.embedSWF(document.location.protocol +  "//www.youtube.com/apiplayer?enablejsapi=1&playerapiid=ytplayer?wmode=transparent",
        "ytapiplayer", "640", "385", "8", null, null, params, atts);
} else {

  //end of this URL may need &origin=http://..... once pushed to production to prevent XSS
  $("#html5_player").attr("src", document.location.protocol +  "//www.youtube.com/embed/" + streams["1.0"] + "?enablejsapi=1&controls=0");
  $("#html5_player").show();

  var tag = document.createElement('script');
  tag.src = document.location.protocol +  "//www.youtube.com/player_api";
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

    $("#video_speeds").append(' <li id="'+id+'">'+key+'x</li>');

    $("#"+id).click(function(){
      change_video_speed(key, stream);
      $(this).siblings().removeClass("active");
      $(this).addClass("active");
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

function toggleVideo(){
  if ($("#video_control").hasClass("play")){
    play();
    $("#video_control").removeClass().addClass("pause");
  } else {
    pause();
    $("#video_control").removeClass().addClass("play");
  }
}

$("#video_control").click(toggleVideo);

// space bar to pause video
$(".video-wrapper").keyup(function(e){
  active = document.activeElement;
  if (e.which == 32) {
    e.preventDefault();
    $("#video_control").click();
  }
});
