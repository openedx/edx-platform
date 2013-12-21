/**
 * @fileoverview YouTube Media Controller - Wrapper for YouTube Media API
 */

/**
 * YouTube Media Controller - Wrapper for YouTube Media API
 * @param {videojs.Player|Object} player
 * @param {Object=} options
 * @param {Function=} ready
 * @constructor
 */
videojs.Youtube = videojs.MediaTechController.extend({
  init: function(player, options, ready){
    videojs.MediaTechController.call(this, player, options, ready);
    
    this.features.fullscreenResize = true;
    
    this.player_ = player;
    this.player_el_ = document.getElementById(this.player_.id());

    // Copy the Javascript options if they exist
    if (typeof options.source != 'undefined') {
      for (var key in options.source) {
        this.player_.options()[key] = options.source[key];
      }
    }
    
    // Disable lockShowing because YouTube controls are there
    if (this.player_.options().ytcontrols){
      this.player_.controls(false);
    }
    
    this.videoId = videojs.Youtube.parseVideoId(this.player_.options().src);
    
    if (typeof this.videoId != 'undefined') {
      // Show the YouTube poster only if we don't use YouTube poster (otherwise the controls pop, it's not nice)
      if (!this.player_.options().ytcontrols){
        // Set the YouTube poster only if none is specified
        if (typeof this.player_.poster() == 'undefined') {
          this.player_.poster('http://img.youtube.com/vi/' + this.videoId + '/0.jpg');
        }

        // Cover the entire iframe to have the same poster than YouTube
        // Doesn't exist right away because the DOM hasn't created it
        var self = this;
        setTimeout(function(){ self.player_.posterImage.el().style.backgroundSize = 'cover'; }, 50);
      }
    }

    this.id_ = this.player_.id() + '_youtube_api';

    this.el_ = videojs.Component.prototype.createEl('iframe', {
      id: this.id_,
      className: 'vjs-tech',
      scrolling: 'no',
      marginWidth: 0,
      marginHeight: 0,
      frameBorder: 0,
      webkitAllowFullScreen: '',
      mozallowfullscreen: '',
      allowFullScreen: ''
    });
    
    this.player_el_.insertBefore(this.el_, this.player_el_.firstChild);
    
    var params = {
      enablejsapi: 1,
      iv_load_policy: 3,
      playerapiid: this.id(),
      disablekb: 1,
      wmode: 'transparent',
      controls: (this.player_.options().ytcontrols)?1:0,
      showinfo: 0,
      modestbranding: 1,
      rel: 0,
      autoplay: (this.player_.options().autoplay)?1:0,
      loop: (this.player_.options().loop)?1:0,
      list: videojs.Youtube.parsePlaylist(this.player_.options().src)
    };
    
    if (typeof params.list == 'undefined') {
      delete params.list;
    }
    
    // Make autoplay work for iOS
    if (this.player_.options().autoplay) {
      this.playOnReady = true;
    }
    
    // If we are not on a server, don't specify the origin (it will crash)
    if (window.location.protocol != 'file:') {
      params.origin = window.location.protocol + '//' + window.location.host;
    }

    this.el_.src = 'http://www.youtube.com/embed/' + this.videoId + '?' + videojs.Youtube.makeQueryString(params);

    if (this.player_.options().ytcontrols){
      // Remove the big play button and the control bar, we use Vimeo controls
      // Doesn't exist right away because the DOM hasn't created it
      var self = this;
      setTimeout(function(){ 
        var bigPlayDom = self.player_.bigPlayButton.el();
        bigPlayDom.parentNode.removeChild(bigPlayDom);
        
        var controlBarDom = self.player_.controlBar.el();
        controlBarDom.parentNode.removeChild(controlBarDom);
      }, 50);
    }

    if (videojs.Youtube.apiReady){
      this.loadYoutube();
    } else {
      // Add to the queue because the YouTube API is not ready
      videojs.Youtube.loadingQueue.push(this);

      // Load the YouTube API if it is the first YouTube video
      if(!videojs.Youtube.apiLoading){
        var tag = document.createElement('script');
        tag.src = 'http://www.youtube.com/iframe_api';
        var firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        videojs.Youtube.apiLoading = true;
      }
    }
  }
});

videojs.Youtube.prototype.dispose = function(){
  if (this.el_){
    this.el_.parentNode.removeChild(this.el_);
  }
  
  if (this.ytplayer) {
    this.ytplayer.destroy();
  }
  
  videojs.MediaTechController.prototype.dispose.call(this);
};

videojs.Youtube.prototype.src = function(src){
  this.ytplayer.loadVideoById({
    videoId: videojs.Youtube.parseVideoId(src), 
    list: videojs.Youtube.parsePlaylist(src)
  });
};

videojs.Youtube.prototype.play = function(){
  if (this.isReady_){ 
    this.ytplayer.playVideo(); 
  } else { 
    // We will play it when the API will be ready
    this.playOnReady = true;
  }
};

videojs.Youtube.prototype.pause = function(){ this.ytplayer.pauseVideo(); };
videojs.Youtube.prototype.paused = function(){
  return this.lastState !== YT.PlayerState.PLAYING &&
         this.lastState !== YT.PlayerState.BUFFERING;
};

videojs.Youtube.prototype.currentTime = function(){ return this.ytplayer.getCurrentTime(); };

videojs.Youtube.prototype.setCurrentTime = function(seconds){
  this.ytplayer.seekTo(seconds, true);
  this.player_.trigger('timeupdate');
};

videojs.Youtube.prototype.duration = function(){ return this.ytplayer.getDuration(); };
videojs.Youtube.prototype.buffered = function(){
  var loadedBytes = this.ytplayer.getVideoBytesLoaded();
  var totalBytes = this.ytplayer.getVideoBytesTotal();
  if (!loadedBytes || !totalBytes) return 0;

  var duration = this.ytplayer.getDuration();
  var secondsBuffered = (loadedBytes / totalBytes) * duration;
  var secondsOffset = (this.ytplayer.getVideoStartBytes() / totalBytes) * duration;
  return videojs.createTimeRange(secondsOffset, secondsOffset + secondsBuffered);
};

videojs.Youtube.prototype.volume = function() { 
  if (isNaN(this.volumeVal)) {
    this.volumeVal = this.ytplayer.getVolume() / 100.0;
  }

  return this.volumeVal;
};

videojs.Youtube.prototype.setVolume = function(percentAsDecimal){
  if (percentAsDecimal && percentAsDecimal != this.volumeVal) {
    this.ytplayer.setVolume(percentAsDecimal * 100.0); 
    this.volumeVal = percentAsDecimal;
    this.player_.trigger('volumechange');
  }
};

videojs.Youtube.prototype.muted = function() { return this.ytplayer.isMuted(); };
videojs.Youtube.prototype.setMuted = function(muted) { 
  if (muted) {
    this.ytplayer.mute(); 
  } else { 
    this.ytplayer.unMute(); 
  } 

  var self = this;
  setTimeout(function() { self.player_.trigger('volumechange'); }, 50);
};

videojs.Youtube.prototype.onReady = function(){
  this.isReady_ = true;
  this.player_.trigger('techready');

  // Hide the poster when ready because YouTube has it's own
  this.triggerReady();
  this.player_.trigger('durationchange');
  
  // Play right away if we clicked before ready
  if (this.playOnReady){
    this.ytplayer.playVideo();
  }
};

videojs.Youtube.prototype.onStateChange = function(state){
  if (state != this.lastState){
    switch(state){
      case -1:
        this.player_.trigger('durationchange');
        break;

      case YT.PlayerState.ENDED:
        this.player_.trigger('ended');
        break;

      case YT.PlayerState.PLAYING:
        this.player_.trigger('timeupdate');
        this.player_.trigger('durationchange');
        this.player_.trigger('playing');
        this.player_.trigger('play');
        break;

      case YT.PlayerState.PAUSED:
        this.player_.trigger('pause');
        break;

      case YT.PlayerState.BUFFERING:
        this.player_.trigger('timeupdate');
        this.player_.trigger('waiting');
        break;

      case YT.PlayerState.CUED:
        break;
    }

    this.lastState = state;
  }
};

videojs.Youtube.prototype.onPlaybackQualityChange = function(quality){
  switch(quality){
    case 'medium':
      this.player_.videoWidth = 480;
      this.player_.videoHeight = 360;
      break;

    case 'large':
      this.player_.videoWidth = 640;
      this.player_.videoHeight = 480;
      break;

    case 'hd720':
      this.player_.videoWidth = 960;
      this.player_.videoHeight = 720;
      break;

    case 'hd1080':
      this.player_.videoWidth = 1440;
      this.player_.videoHeight = 1080;
      break;

    case 'highres':
      this.player_.videoWidth = 1920;
      this.player_.videoHeight = 1080;
      break;

    case 'small':
      this.player_.videoWidth = 320;
      this.player_.videoHeight = 240;
      break;

    default:
      this.player_.videoWidth = 0;
      this.player_.videoHeight = 0;
      break;
  }

  this.player_.trigger('ratechange');
};

videojs.Youtube.prototype.onError = function(error){
  this.player_.error = error;
  this.player_.trigger('error');
};

videojs.Youtube.isSupported = function(){
  return true;
};

videojs.Youtube.prototype.supportsFullScreen = function() {
  return false;
};

videojs.Youtube.canPlaySource = function(srcObj){
  return (srcObj.type == 'video/youtube');
};

// All videos created before YouTube API is loaded
videojs.Youtube.loadingQueue = [];

// Create the YouTube player
videojs.Youtube.prototype.loadYoutube = function(){
  this.ytplayer = new YT.Player(this.id_, {
    events: {
      onReady: function(e) { e.target.vjsTech.onReady(); },
      onStateChange: function(e) { e.target.vjsTech.onStateChange(e.data); },
      onPlaybackQualityChange: function(e){ e.target.vjsTech.onPlaybackQualityChange(e.data); },
      onError: function(e){ e.target.vjsTech.onError(e.data); }
    }
  });

  this.ytplayer.vjsTech = this;
};

videojs.Youtube.makeQueryString = function(args){
  var array = [];
  for (var key in args){
    if (args.hasOwnProperty(key)){
      array.push(encodeURIComponent(key) + '=' + encodeURIComponent(args[key]));
    }
  }

  return array.join('&');
};

videojs.Youtube.parseVideoId = function(src){
// Regex that parse the video ID for any YouTube URL
  var regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  var match = src.match(regExp);
  
  if (match && match[2].length == 11){
    return match[2];
  }
};

videojs.Youtube.parsePlaylist = function(src){
  // Check if we have a playlist
  var regExp = /[?&]list=([^#\&\?]+)/;
  var match = src.match(regExp);
  
  if (match != null && match.length > 1) {
    return match[1];
  }
};

// Called when YouTube API is ready to be used
window.onYouTubeIframeAPIReady = function(){
  var yt;
  while ((yt = videojs.Youtube.loadingQueue.shift())){
    yt.loadYoutube();
  }
  videojs.Youtube.loadingQueue = [];
  videojs.Youtube.apiReady = true;
}

