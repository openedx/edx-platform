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

/* Cache a reference to our slider element */
var slider = $('#slider')

.slider({range: "min", slide:function(event,ui){seek_slide('slide',event.originalEvent,ui.value); handle.qtip('option', 'content.text', '' + ui.value);}, stop:function(event,ui){seek_slide('stop',event.originalEvent,ui.value);}}),

/* Grab and cache the newly created slider handle */
handle = $('.ui-slider-handle', slider);

/* 
	 * Selector needs changing here to match your elements.
	 * 
	 * Notice the second argument to the $() constructor, which tells
	 * jQuery to use that as the top-level element to seareh down from.
	 */
	handle.qtip({
		content: '' + slider.slider('option', 'value'), // Use the current value of the slider
		position: {
			my: 'bottom center',
			at: 'top center',
			container: handle // Stick it inside the handle element so it keeps the position synched up
		},
		hide: {
			delay: 700 // Give it a longer delay so it doesn't hide frequently as we move the handle
		},
		style: {
			classes: 'ui-tooltip-slider',
			widget: true // Make it Themeroller compatible
		}
	});

function good() {
    window['console'].log(ytplayer.getCurrentTime());
}

ajax_video=good;

// load the same video speed your last video was at in a sequence
// if the last speed played on video doesn't exist on another video just use 1.0 as default

function add_speed(key, stream) {
  var id = 'speed_' + stream;

  if (key == video_speed) {
    $("#video_speeds").append(' <li class="active" id="'+id+'">'+key+'x</li>');
    $("p.active").text(key + 'x');
  } else {
    $("#video_speeds").append(' <li id="'+id+'">'+key+'x</li>');
  }

  $("#"+id).click(function(){
    change_video_speed(key, stream);
    $(this).siblings().removeClass("active");
    $(this).addClass("active");
    var active = $(this).text();
    $("p.active").text(active);
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

$(document).ready(function() {
    video_speed = $.cookie("video_speed");

    //ugly hack to account for different formats in vid speed in the XML (.75 vs 0.75, 1.5 vs 1.50);
    if (( !video_speed ) || ( !streams[video_speed] && !streams[video_speed + "0"]) && !streams[video_speed.slice(0,-1)] && !streams[video_speed.slice(1)] && !streams["0" + video_speed]) {
      video_speed = "1.0";
    }

    if (streams[video_speed + "0"]){
      video_speed = video_speed + "0";
    } else if (streams[video_speed.slice(0, -1)]){
      video_speed = video_speed.slice(0, -1);
    } else if (streams[video_speed.slice(1)]) {
      video_speed = video_speed.slice(1);
    } else if (streams["0" + video_speed]) {
      video_speed = "0" + video_speed;
    }

    loadNewVideo(streams["1.0"], streams[video_speed], ${ position });

    for(var i=0; i<l.length; i++) {
      add_speed(l[i], streams[l[i]])
    }

});

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
