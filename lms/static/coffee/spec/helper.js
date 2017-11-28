/*
 * decaffeinate suggestions:
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
jasmine.stubbedMetadata = {
  slowerSpeedYoutubeId: {
    id: 'slowerSpeedYoutubeId',
    duration: 300
  },
  normalSpeedYoutubeId: {
    id: 'normalSpeedYoutubeId',
    duration: 200
  },
  bogus: {
    duration: 100
  }
};

jasmine.stubbedCaption = {
  start: [0, 10000, 20000, 30000],
  text: ['Caption at 0', 'Caption at 10000', 'Caption at 20000', 'Caption at 30000']
};

jasmine.stubRequests = () =>
  spyOn($, 'ajax').and.callFake(function(settings) {
    let match;
    if (match = settings.url.match(/youtube\.com\/.+\/videos\/(.+)\?v=2&alt=jsonc/)) {
      return settings.success({data: jasmine.stubbedMetadata[match[1]]});
    } else if (match = settings.url.match(/static\/subs\/(.+)\.srt\.sjson/)) {
      return settings.success(jasmine.stubbedCaption);
    } else if (settings.url.match(/modx\/.+\/problem_get$/)) {
      return settings.success({html: readFixtures('problem_content.html')});
    } else if ((settings.url === '/calculate') ||
      settings.url.match(/modx\/.+\/goto_position$/) ||
      settings.url.match(/event$/) ||
      settings.url.match(/modx\/.+\/problem_(check|reset|show|save)$/)) {
      // do nothing
    } else {
      throw `External request attempted for ${settings.url}, which is not defined.`;
    }
  })
;

jasmine.stubYoutubePlayer = () =>
  YT.Player = () => jasmine.createSpyObj('YT.Player', ['cueVideoById', 'getVideoEmbedCode',
    'getCurrentTime', 'getPlayerState', 'getVolume', 'setVolume', 'loadVideoById',
    'playVideo', 'pauseVideo', 'seekTo'])
;

jasmine.stubVideoPlayer = function(context, enableParts, createPlayer) {
  let currentPartName;
  if (createPlayer == null) { createPlayer = true; }
  if (!$.isArray(enableParts)) { enableParts = [enableParts]; }

  let { suite } = context;
  while ((suite = suite.parentSuite)) { currentPartName = suite.description; }
  enableParts.push(currentPartName);

  for (let part of ['VideoCaption', 'VideoSpeedControl', 'VideoVolumeControl', 'VideoProgressSlider']) {
    if (!($.inArray(part, enableParts) >= 0)) {
      spyOn(window, part);
    }
  }

  loadFixtures('video.html');
  jasmine.stubRequests();
  YT.Player = undefined;
  context.video = new Video('example', '.75:slowerSpeedYoutubeId,1.0:normalSpeedYoutubeId');
  jasmine.stubYoutubePlayer();
  if (createPlayer) {
    return new VideoPlayer({video: context.video});
  }
};

// Stub Youtube API
window.YT = {
  PlayerState: {
    UNSTARTED: -1,
    ENDED: 0,
    PLAYING: 1,
    PAUSED: 2,
    BUFFERING: 3,
    CUED: 5
  }
};

// Stub jQuery.cookie
$.cookie = jasmine.createSpy('jQuery.cookie').and.returnValue('1.0');

// Stub jQuery.qtip
$.fn.qtip = jasmine.createSpy('jQuery.qtip');

// Stub jQuery.scrollTo
$.fn.scrollTo = jasmine.createSpy('jQuery.scrollTo');
