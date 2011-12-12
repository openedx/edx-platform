var load_id = 0;

function caption_at(index) {
    if (captions==0)
	return "&nbsp;";

    text_array=captions.text

    if ((index>=text_array.length) || (index < 0))
	return "&nbsp;";
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

    return time_array[index]/1000.0;
}

function caption_index(now) {
    // Returns the index of the current caption, given a time
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

function update_captions(t) {
    var i=caption_index(t);
    $("#std_n5").html(caption_at(i-5));
    $("#std_n4").html(caption_at(i-4));
    $("#std_n3").html(caption_at(i-3));
    $("#std_n2").html(caption_at(i-2));
    $("#std_n1").html(caption_at(i-1));
    $("#std_0").html(caption_at(i));
    $("#std_p1").html(caption_at(i+1));
    $("#std_p2").html(caption_at(i+2));
    $("#std_p3").html(caption_at(i+3));
    $("#std_p4").html(caption_at(i+4));
    $("#std_p5").html(caption_at(i+5));
    $("#std_p6").html(caption_at(i+6));
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

function onYouTubePlayerReady(playerId) {
    ytplayer = document.getElementById("myytplayer");
    setInterval(updateytplayerInfo, 1000);
    setInterval(ajax_video,1000);
    ytplayer.addEventListener("onStateChange", "onytplayerStateChange");
    ytplayer.addEventListener("onError", "onPlayerError");
    if((typeof load_id != "undefined") && (load_id != 0)) {
	var id=load_id;
	loadNewVideo(id, 0);
    }

}

function log_event(e) {
    //$("#eventlog").append("<br>");
    //$("#eventlog").append(JSON.stringify(e));
    window['console'].log(JSON.stringify(e));
}

function seek_slide(type,oe,value) {
    //log_event([type, value]);
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
	log_event([type, value]);
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
    log_event(['State Change',newState, get_state()]);
}

function onPlayerError(errorCode) {
    alert("An error occured: " + errorCode);
}

function updateytplayerInfo() {
    if(ytplayer.getPlayerState()!=3) {
	$("#slider").slider("option","max",ytplayer.getDuration());
	$("#slider").slider("option","value",ytplayer.getCurrentTime());
    }
    if (getPlayerState() == 1){
	update_captions(getCurrentTime());
    }

    //    updateHTML("videoduration", getDuration());
    //    updateHTML("videotime", getCurrentTime());
    //    updateHTML("startbytes", getStartBytes());
    //    updateHTML("volume", getVolume());
}

// functions for the api calls
function loadNewVideo(id, startSeconds) {
    $.getJSON("/static/subs/"+id+".srt.sjson", function(data) {
        captions=data;
    });
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
}

function pause() {
    if (ytplayer) {
	ytplayer.pauseVideo();
    }
}

function stop() {
    if (ytplayer) {
	ytplayer.stopVideo();
    }
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
    alert(ytplayer.getVideoEmbedCode());
}

function getVideoUrl() {
    alert(ytplayer.getVideoUrl());
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