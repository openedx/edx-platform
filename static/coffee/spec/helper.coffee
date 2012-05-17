jasmine.getFixtures().fixturesPath = "/_jasmine/fixtures/"

jasmine.stubbedMetadata =
  abc123:
    id: 'abc123'
    duration: 100
  def456:
    id: 'def456'
    duration: 200
  bogus:
    duration: 300

jasmine.stubbedCaption =
  start: [0, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
    100000, 110000, 120000]
  text: ['Caption at 0', 'Caption at 10000', 'Caption at 20000',
  'Caption at 30000', 'Caption at 40000', 'Caption at 50000', 'Caption at 60000',
  'Caption at 70000', 'Caption at 80000', 'Caption at 90000', 'Caption at 100000',
  'Caption at 110000', 'Caption at 120000']

jasmine.stubRequests = ->
  spyOn($, 'ajax').andCallFake (settings) ->
    if match = settings.url.match /youtube\.com\/.+\/videos\/(.+)\?v=2&alt=jsonc/
      settings.success data: jasmine.stubbedMetadata[match[1]]
    else if match = settings.url.match /static\/subs\/(.+)\.srt\.sjson/
      settings.success jasmine.stubbedCaption
    else if settings.url == '/calculate' ||
      settings.url == '/6002x/modx/sequential/1/goto_position' ||
      settings.url.match(/event$/) ||
      settings.url.match(/6002x\/modx\/problem\/.+\/problem_(check|reset|show|save)$/)
      # do nothing
    else
      throw "External request attempted for #{settings.url}, which is not defined."

jasmine.stubYoutubePlayer = ->
  YT.Player = -> jasmine.createSpyObj 'YT.Player', ['cueVideoById', 'getVideoEmbedCode',
    'getCurrentTime', 'getPlayerState', 'loadVideoById', 'playVideo', 'pauseVideo', 'seekTo']

jasmine.stubVideoPlayer = (context, enableParts) ->
  enableParts = [enableParts] unless $.isArray(enableParts)

  suite = context.suite
  currentPartName = suite.description while suite = suite.parentSuite
  enableParts.push currentPartName

  for part in ['VideoCaption', 'VideoSpeedControl', 'VideoProgressSlider']
    unless $.inArray(part, enableParts) >= 0
      spyOn window, part

  loadFixtures 'video.html'
  jasmine.stubRequests()
  YT.Player = undefined
  context.video = new Video 'example', '.75:abc123,1.0:def456'
  jasmine.stubYoutubePlayer()
  return new VideoPlayer context.video

spyOn(window, 'onunload')

# Stub Youtube API
window.YT =
  PlayerState:
    UNSTARTED: -1
    ENDED: 0
    PLAYING: 1
    PAUSED: 2
    BUFFERING: 3
    CUED: 5

# Stub jQuery.cookie
$.cookie = jasmine.createSpy('jQuery.cookie').andReturn '1.0'

# Stub jQuery.qtip
$.fn.qtip = jasmine.createSpy 'jQuery.qtip'

# Stub jQuery.scrollTo
$.fn.scrollTo = jasmine.createSpy 'jQuery.scrollTo'
