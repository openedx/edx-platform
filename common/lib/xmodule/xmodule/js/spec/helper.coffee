# Stub Youtube API
window.YT =
  PlayerState:
    UNSTARTED: -1
    ENDED: 0
    PLAYING: 1
    PAUSED: 2
    BUFFERING: 3
    CUED: 5

window.TYPES =
  'undefined'        : 'undefined'
  'number'           : 'number'
  'boolean'          : 'boolean'
  'string'           : 'string'
  '[object Function]': 'function'
  '[object RegExp]'  : 'regexp'
  '[object Array]'   : 'array'
  '[object Date]'    : 'date'
  '[object Error]'   : 'error'

window.TOSTRING = Object.prototype.toString
window.STATUS = window.YT.PlayerState

window.whatType = (o) ->
  TYPES[typeof o] || TYPES[TOSTRING.call(o)] || (o ? 'object' : 'null');

# Time waitsFor() should wait for before failing a test.
window.WAIT_TIMEOUT = 1000

jasmine.getFixtures().fixturesPath = 'xmodule/js/fixtures'

jasmine.stubbedMetadata =
  slowerSpeedYoutubeId:
    id: 'slowerSpeedYoutubeId'
    duration: 300
  normalSpeedYoutubeId:
    id: 'normalSpeedYoutubeId'
    duration: 200
  bogus:
    duration: 100

jasmine.fireEvent = (el, eventName) ->
  if document.createEvent
    event = document.createEvent "HTMLEvents"
    event.initEvent eventName, true, true
  else
    event = document.createEventObject()
    event.eventType = eventName
  event.eventName = eventName
  if document.createEvent
    el.dispatchEvent(event)
  else
    el.fireEvent("on" + event.eventType, event)

jasmine.stubbedCaption =
  start: [0, 10000, 20000, 30000]
  text: ['Caption at 0', 'Caption at 10000', 'Caption at 20000', 'Caption at 30000']

jasmine.stubbedHtml5Speeds = ['0.75', '1.0', '1.25', '1.50']

jasmine.stubRequests = ->
  spyOn($, 'ajax').andCallFake (settings) ->
    if match = settings.url.match /youtube\.com\/.+\/videos\/(.+)\?v=2&alt=jsonc/
      settings.success data: jasmine.stubbedMetadata[match[1]]
    else if match = settings.url.match /static(\/.*)?\/subs\/(.+)\.srt\.sjson/
      settings.success jasmine.stubbedCaption
    else if settings.url.match /.+\/problem_get$/
      settings.success html: readFixtures('problem_content.html')
    else if settings.url == '/calculate' ||
      settings.url.match(/.+\/goto_position$/) ||
      settings.url.match(/event$/) ||
      settings.url.match(/.+\/problem_(check|reset|show|save)$/)
      # do nothing
    else
      throw "External request attempted for #{settings.url}, which is not defined."

jasmine.stubYoutubePlayer = ->
  YT.Player = ->
    obj = jasmine.createSpyObj 'YT.Player', ['cueVideoById', 'getVideoEmbedCode',
    'getCurrentTime', 'getPlayerState', 'getVolume', 'setVolume', 'loadVideoById',
    'playVideo', 'pauseVideo', 'seekTo', 'getDuration', 'getAvailablePlaybackRates', 'setPlaybackRate']
    obj['getAvailablePlaybackRates'] = jasmine.createSpy('getAvailablePlaybackRates').andReturn [0.75, 1.0, 1.25, 1.5]
    obj

jasmine.stubVideoPlayer = (context, enableParts, createPlayer=true) ->
  enableParts = [enableParts] unless $.isArray(enableParts)
  suite = context.suite
  currentPartName = suite.description while suite = suite.parentSuite
  enableParts.push currentPartName

  loadFixtures 'video.html'
  jasmine.stubRequests()
  YT.Player = undefined
  videosDefinition = '0.75:slowerSpeedYoutubeId,1.0:normalSpeedYoutubeId'
  context.video = new Video '#example', videosDefinition
  jasmine.stubYoutubePlayer()
  if createPlayer
    return new VideoPlayer(video: context.video)

jasmine.stubVideoPlayerAlpha = (context, enableParts, html5=false) ->
  console.log('stubVideoPlayerAlpha called')
  suite = context.suite
  currentPartName = suite.description while suite = suite.parentSuite
  if html5 == false
    loadFixtures 'videoalpha.html'
  else
    loadFixtures 'videoalpha_html5.html'
  jasmine.stubRequests()
  YT.Player = undefined
  window.OldVideoPlayerAlpha = undefined
  jasmine.stubYoutubePlayer()
  return new VideoAlpha '#example', '.75:slowerSpeedYoutubeId,1.0:normalSpeedYoutubeId'


# Stub jQuery.cookie
$.cookie = jasmine.createSpy('jQuery.cookie').andReturn '1.0'

# Stub jQuery.qtip
$.fn.qtip = jasmine.createSpy 'jQuery.qtip'

# Stub jQuery.scrollTo
$.fn.scrollTo = jasmine.createSpy 'jQuery.scrollTo'
