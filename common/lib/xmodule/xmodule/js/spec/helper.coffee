# Stub Youtube API
window.YT =
  PlayerState:
    UNSTARTED: -1
    ENDED: 0
    PLAYING: 1
    PAUSED: 2
    BUFFERING: 3
    CUED: 5

window.STATUS = window.YT.PlayerState

oldAjaxWithPrefix = window.jQuery.ajaxWithPrefix

window.onTouchBasedDevice = ->
    navigator.userAgent.match /iPhone|iPod|iPad/i

jasmine.stubbedCaption =
      end: [3120, 6270, 8490, 21620, 24920, 25750, 27900, 34380, 35550, 40250]
      start: [1180, 3120, 6270, 14910, 21620, 24920, 25750, 27900, 34380, 35550]
      text: [
        "MICHAEL CIMA: So let's do the first one here.",
        "Vacancies, where do they come from?",
        "Well, imagine a perfect crystal.",
        "Now we know at any temperature other than absolute zero there's enough",
        "energy going around that some atoms will have more energy",
        "than others, right?",
        "There's a distribution.",
        "If I plot energy here and number, these atoms in the crystal will have a",
        "distribution of energy.",
        "And some will have quite a bit of energy, just for a moment."
      ]

# For our purposes, we need to make sure that the function $.ajaxWithPrefix
# does not fail when during tests a captions file is requested.
# It is originally defined in
#
#     common/static/coffee/src/ajax_prefix.js
#
# We will replace it with a function that does:
#
#     1.) Return a hard coded captions object if the file name contains 'Z5KLxerq05Y'.
#     2.) Behaves the same a as the origianl in all other cases.

window.jQuery.ajaxWithPrefix = (url, settings) ->
  if not settings
      settings = url
      url = settings.url
      success = settings.success
      data = settings.data

  if url.match(/Z5KLxerq05Y/g) isnt null or url.match(/7tqY6eQzVhE/g) isnt null or url.match(/cogebirgzzM/g) isnt null
    if window.jQuery.isFunction(success) is true
      success jasmine.stubbedCaption
    else if window.jQuery.isFunction(data) is true
      data jasmine.stubbedCaption
  else
    oldAjaxWithPrefix.apply @, arguments

# Time waitsFor() should wait for before failing a test.
window.WAIT_TIMEOUT = 1000

jasmine.getFixtures().fixturesPath += 'fixtures'

jasmine.stubbedMetadata =
  '7tqY6eQzVhE':
    id: '7tqY6eQzVhE'
    duration: 300
  'cogebirgzzM':
    id: 'cogebirgzzM'
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

jasmine.stubbedHtml5Speeds = ['0.75', '1.0', '1.25', '1.50']

jasmine.stubRequests = ->
  spyOn($, 'ajax').andCallFake (settings) ->
    if match = settings.url.match /youtube\.com\/.+\/videos\/(.+)\?v=2&alt=jsonc/
      status = match[1].split('_')
      if status and status[0] is 'status'
        {
          always: (callback) ->
            callback.call(window, {}, status[1])
          error: (callback) ->
            callback.call(window, {}, status[1])
          done: (callback) ->
            callback.call(window, {}, status[1])
        }
      else if settings.success
        # match[1] - it's video ID
        settings.success data: jasmine.stubbedMetadata[match[1]]
      else {
          always: (callback) ->
            callback.call(window, {}, 'success')
          done: (callback) ->
            callback.call(window, {}, 'success')
        }
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

jasmine.stubVideoPlayer = (context, enableParts, html5=false) ->
  suite = context.suite
  currentPartName = suite.description while suite = suite.parentSuite
  if html5 == false
    loadFixtures 'video.html'
  else
    loadFixtures 'video_html5.html'
  jasmine.stubRequests()
  YT.Player = undefined
  window.OldVideoPlayer = undefined
  jasmine.stubYoutubePlayer()
  return new Video '#example', '.75:7tqY6eQzVhE,1.0:cogebirgzzM'


# Stub jQuery.cookie
$.cookie = jasmine.createSpy('jQuery.cookie').andReturn '1.0'

# Stub jQuery.qtip
$.fn.qtip = jasmine.createSpy 'jQuery.qtip'

# Stub jQuery.scrollTo
$.fn.scrollTo = jasmine.createSpy 'jQuery.scrollTo'
