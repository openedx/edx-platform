// Things to abstract out to another file

// We do sync AJAX for just the page close event. 
// TODO: This should _really_ not be a global. 
var log_close_event = false; 

function log_close() {
    var d=new Date();
    var t=d.getTime();
    //close_event_logged = "waiting";
    log_close_event = true;
    log_event('page_close', {});
    log_close_event = false;
    // Google Chrome will close without letting the event go through.
    // This causes the page close to be delayed until we've hit the
    // server. The code below fixes it, but breaks Firefox. 
    // TODO: Check what happens with no network. 
    /*while((close_event_logged != "done") && (d.getTime() < t+500)) {
	console.log(close_event_logged);
    }*/
}

window.onbeforeunload = log_close;

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
	var cookies = document.cookie.split(';');
	for (var i = 0; i < cookies.length; i++) {
	    var cookie = jQuery.trim(cookies[i]);
	    // Does this cookie string begin with the name we want?
	    if (cookie.substring(0, name.length + 1) == (name + '=')) {
		cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
		break;
	    }
	}
    }
    return cookieValue;
}

function postJSON(url, data, callback) {
    $.ajax({type:'POST',
	    url: url,
		dataType: 'json',
		data: data,
		success: callback,
		headers : {'X-CSRFToken':getCookie('csrftoken')}
  });
}

function postJSONAsync(url, data, callback) {
    $.ajax({type:'POST',
	    url: url,
		dataType: 'json',
		data: data,
		success: callback,
		headers : {'X-CSRFToken':getCookie('csrftoken')},
		async:true
		});
}

// For easy embedding of CSRF in forms
$(function() {
    $('#csrfmiddlewaretoken').attr("value", getCookie('csrftoken'))
});

// For working with circuits in wiki: 

function submit_circuit(circuit_id) {
    $("input.schematic").each(function(index,element){ element.schematic.update_value(); });
    postJSON('/save_circuit/'+circuit_id, 
	     {'schematic': $('#schematic_'+circuit_id).attr("value")}, 
	     function(data){ if (data.results=='success') alert("Saved");});
    return false;
}

// Video player

var load_id = 0;
var caption_id;
var video_speed = "1.0";

var updateytPlayerInterval;
var ajax_videoInterval;

function change_video_speed(speed, youtube_id) {
    new_position = ytplayer.getCurrentTime() * video_speed / speed;
    video_speed = speed;
    ytplayer.loadVideoById(youtube_id, new_position);
    syncPlayButton();
    log_event("speed", {"new_speed":speed, "clip":youtube_id});

    $.cookie("video_speed", speed, {'expires':3650, 'path':'/'});
}

function caption_at(index) {
    if (captions==0)
	return "";

    text_array=captions.text

    if ((index>=text_array.length) || (index < 0))
	return "";
    return text_array[index];
}

function caption_time_at(index) {
    if (captions==0)
	return 0;

    time_array=captions.start;

    if (index < 0)
	return 0;
    if (index>=time_array.length)
	return ytplayer.getDuration();

    return time_array[index] / 1000.0 / video_speed;
}

function caption_index(now) {
    // Returns the index of the current caption, given a time
    now = now * video_speed;

    if (captions==0)
	return 0;

    time_array=captions.start

    // TODO: Bisection would be better, or something incremental
    var i; 
    for(i=0;i<captions.start.length; i++) {
	if(time_array[i]>(now*1000)) {
	    return i-1;
	}
    }
    return i-1;
}

function format_time(t)
{
    seconds = Math.floor(t);
    minutes = Math.floor(seconds / 60);
    hours = Math.floor(minutes / 60);
    seconds = seconds % 60;
    minutes = minutes % 60;

    if (hours) {
      return hours+":"+((minutes < 10)?"0":"")+minutes+":"+((seconds < 10)?"0":"")+(seconds%60);
    } else {
      return minutes+":"+((seconds < 10)?"0":"")+(seconds%60);
    }
}

function update_captions(t) {
    var i=caption_index(t);
    $("#vidtime").html(format_time(ytplayer.getCurrentTime())+' / '+format_time(ytplayer.getDuration()));
    var j;
    for(j=1; j<9; j++) {
	$("#std_n"+j).html(caption_at(i-j));
	$("#std_p"+j).html(caption_at(i+j));
    }
    $("#std_0").html(caption_at(i));
}

function title_seek(i) {
    // Seek video forwards or backwards by i subtitles
    current=caption_index(getCurrentTime());
    new_time=caption_time_at(current+i);
    
    ytplayer.seekTo(new_time, true);
}

function updateHTML(elmId, value) {
    document.getElementById(elmId).innerHTML = value;
}

function setytplayerState(newState) {
    //    updateHTML("playerstate", newState);
}

// Updates server with location in video so we can resume from the same place
// IMPORTANT TODO: Load test
// POSSIBLE FIX: Move to unload() event and similar
var ajax_video=function(){};
var ytplayer;

function onYouTubePlayerReady(playerId) {
    ytplayer = document.getElementById("myytplayer");
    updateytplayerInfoInterval = setInterval(updateytplayerInfo, 500);
    ajax_videoInterval = setInterval(ajax_video,5000);
    ytplayer.addEventListener("onStateChange", "onytplayerStateChange");
    ytplayer.addEventListener("onError", "onPlayerError");
    if((typeof load_id != "undefined") && (load_id != 0)) {
	var id=load_id;
	loadNewVideo(caption_id, id, 0);
    }
}

/* HTML5 YouTube iFrame API Specific */
function onYouTubePlayerAPIReady() {
  ytplayer = new YT.Player('html5_player', {
    events: { 
      'onReady': onPlayerReady,
      'onStateChange': onPlayerStateChange
    }
  });
  updateytplayerInfoInterval = setInterval(updateHTML5ytplayerInfo, 200);
  //ajax_videoInterval = setInterval(ajax_video, 5000);
}

// Need this function to call the API ready callback when we switch to a tab with AJAX that has a video
// That callback is not being fired when we switch tabs. 
function loadHTML5Video() {
    if (!ytplayer && switched_tab){
      onYouTubePlayerAPIReady();
    }
}

function isiOSDevice(){
  var iphone = "iphone";
  var ipod = "ipod";
  var ipad = "ipad";
  var uagent = navigator.userAgent.toLowerCase();

  //alert(uagent);
  if (uagent.search(ipad) > -1 || uagent.search(iphone) > -1
      || uagent.search(ipod) > -1) {
    return true;
  }
  return false;
}

function onPlayerReady(event) {
  //do not want to autoplay on iOS devices since its not enabled
  //and leads to confusing behavior for the user
  if (!isiOSDevice()) {
    event.target.playVideo();
  }
}

function onPlayerStateChange(event) {
  if (event.data == YT.PlayerState.PLAYING) {
  }
}

/* End HTML5 Specific */


var switched_tab = false; // switch to true when we destroy so we know to call onYouTubePlayerAPIReady()
// clear pings to video status when we switch to a different sequence tab with ajax
function videoDestroy(id) {
//    postJSON('/modx/video/'+id+'/goto_position',
//	     {'position' :  ytplayer.getCurrentTime()});

    load_id = 0;
    clearInterval(updateytplayerInfoInterval);
    clearInterval(ajax_videoInterval);
    ytplayer = false;
    switched_tab = true;
}

function log_event(e, d) {
    data = {
	"event_type" : e, 
	"event" : JSON.stringify(d),
	"page" : document.URL
    }
    $.ajax({type:'GET',
	    url: '/event',
	    dataType: 'json',
	    data: data,
	    async: !log_close_event, // HACK: See comment on log_close_event
	    success: function(){},
	    headers : {'X-CSRFToken':getCookie('csrftoken')}
	   });

    /*, // Commenting out Chrome bug fix, since it breaks FF
	  function(data) {
	      console.log("closing");
	      if (close_event_logged == "waiting") {
		  close_event_logged = "done";
	      console.log("closed");
	  }
	  });*/
}

function seek_slide(type,oe,value) {
    //log_event('video', [type, value]);
    if(type=='slide') {
	 // HACK/TODO: Youtube recommends this be false for slide and true for stop.
	 // Works better on my system with true/true. 
	 // We should test both configurations on low/high bandwidth 
	 // connections, and different browsers
	 // One issue is that we query the Youtube window every 250ms for position/state
	 // With false, it returns the old one (ignoring the new seek), and moves the
         // scroll bar to the wrong spot. 
	ytplayer.seekTo(value, true);
    } else if (type=='stop') {
	ytplayer.seekTo(value, true);
	log_event('video', [type, value]);
    }

    update_captions(value);
}

function get_state() {
    if (ytplayer)
	return [ytplayer.getPlayerState(),
		ytplayer.getVideoUrl(),
		ytplayer.getDuration(), ytplayer.getCurrentTime(), 
		ytplayer.getVideoBytesLoaded(), ytplayer.getVideoBytesTotal(), 
		ytplayer.getVideoStartBytes(), 
		ytplayer.getVolume(),ytplayer.isMuted(),
		ytplayer.getPlaybackQuality(),
		ytplayer.getAvailableQualityLevels()];
    return [];
}

function onytplayerStateChange(newState) {
    setytplayerState(newState);
    log_event('video', ['State Change',newState, get_state()]);
}

function onPlayerError(errorCode) {
    //    alert("An error occured: " + errorCode);
    log_event("player_error", {"error":errorCode});
}

// Currently duplicated to check for if video control changed by clicking the video for HTML5
// Hacky b/c of lack of control over YT player
function updateHTML5ytplayerInfo() {
    var player_state = getPlayerState();
    if(player_state != 3) {
      $("#slider").slider("option","max",ytplayer.getDuration());
      $("#slider").slider("option","value",ytplayer.getCurrentTime());
    }
    if (player_state == 1){
      update_captions(getCurrentTime());
    }
    if (player_state == 1 && $("#video_control").hasClass("play"))
      $("#video_control").removeClass().addClass("pause");
    else if (player_state == 2 && $("#video_control").hasClass("pause"))
      $("#video_control").removeClass().addClass("play");
}

function updateytplayerInfo() {
    var player_state = getPlayerState();
    if(player_state != 3) {
      $("#slider").slider("option","max",ytplayer.getDuration());
      $("#slider").slider("option","value",ytplayer.getCurrentTime());
    }
    if (player_state == 1){
      update_captions(getCurrentTime());
      handle = $('.ui-slider-handle',  $('#slider'));
      handle.qtip('option', 'content.text', '' +  format_time(getCurrentTime()));
    }
       // updateHTML("videoduration", getDuration());
    //    updateHTML("videotime", getCurrentTime());
    //    updateHTML("startbytes", getStartBytes());
    //    updateHTML("volume", getVolume());
}

// functions for the api calls
function loadNewVideo(cap_id, id, startSeconds) {
    captions={"start":[0],"end":[0],"text":["Attempting to load captions..."]};
    $.getJSON("/static/subs/"+cap_id+".srt.sjson", function(data) {
        captions=data;
    });
    caption_id = cap_id;
    load_id = id;
    //if ((typeof ytplayer != "undefined") && (ytplayer.type=="application/x-shockwave-flash")) {
    // Try it every time. If we fail, we want the error message for now. 
    // TODO: Add try/catch
    try {
	ytplayer.loadVideoById(id, parseInt(startSeconds));
        load_id=0;
    }
    catch(e) {
	window['console'].log(JSON.stringify(e));
    }
    log_event("load_video", {"id":id,"start":startSeconds});
    //$("#slider").slider("option","value",startSeconds);
    //seekTo(startSeconds);
}

function syncPlayButton(){
  var state = getPlayerState();
  if (state == 1 || state == 3) {
    $("#video_control").removeClass("play").addClass("pause");
  } else if (state == 2 || state == -1 || state == 0){
    $("#video_control").removeClass("pause").addClass("play");
  }
}

function cueNewVideo(id, startSeconds) {
    if (ytplayer) {
	ytplayer.cueVideoById(id, startSeconds);
    }
}

function play() {
    if (ytplayer) {
	ytplayer.playVideo();
    }
    log_event("play_video", {"id":getCurrentTime(), "code":getEmbedCode()});
}

function pause() {
    if (ytplayer) {
	ytplayer.pauseVideo();
    }
    log_event("pause_video", {"id":getCurrentTime(), "code":getEmbedCode()});
}

function stop() {
    if (ytplayer) {
	ytplayer.stopVideo();
    }
    log_event("stop_video", {"id":getCurrentTime(), "code":getEmbedCode()});
}

function getPlayerState() {
    if (ytplayer) {
      return ytplayer.getPlayerState();
    }
}

function seekTo(seconds) {
    if (ytplayer) {
	ytplayer.seekTo(seconds, true);
    }
}

function getBytesTotal() {
    if (ytplayer) {
	return ytplayer.getVideoBytesTotal();
    }
}

function getCurrentTime() {
    if (ytplayer) {
	return ytplayer.getCurrentTime();
    }
}

function getDuration() {
    if (ytplayer) {
	return ytplayer.getDuration();
    }
}

function getStartBytes() {
    if (ytplayer) {
	return ytplayer.getVideoStartBytes();
    }
}

function mute() {
    if (ytplayer) {
	ytplayer.mute();
    }
}

function unMute() {
    if (ytplayer) {
	ytplayer.unMute();
    }
}

function getEmbedCode() {
    if(ytplayer) {
	ytplayer.getVideoEmbedCode();
    }
}

function getVideoUrl() {
    if(ytplayer) {
	ytplayer.getVideoUrl();
    }
}

function setVolume(newVolume) {
    if (ytplayer) {
	ytplayer.setVolume(newVolume);
    }
}

function getVolume() {
    if (ytplayer) {
	return ytplayer.getVolume();
    }
}

function clearVideo() {
    if (ytplayer) {
	ytplayer.clearVideo();
    }
}
