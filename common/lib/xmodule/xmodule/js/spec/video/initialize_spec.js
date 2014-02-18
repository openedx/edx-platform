(function (requirejs, require, define, undefined) {

'use strict';

require(
['video/01_initialize.js'],
function (Initialize) {
    describe('Initialize', function () {
        describe('saveState function', function () {
            var state, videoPlayerCurrentTime, newCurrentTime, speed;

            // We make sure that `currentTime` is a float. We need to test
            // that Math.round() is called.
            videoPlayerCurrentTime = 3.1242;

            // We have two times, because one is  stored in
            // `videoPlayer.currentTime`, and the other is passed directly to
            // `saveState` in `data` object. In each case, there is different
            // code that handles these times. They have to be different for
            // test completeness sake. Also, make sure it is float, as is the
            // time above.
            newCurrentTime = 5.4;

            speed = '0.75';

            beforeEach(function () {
                state = {
                    videoPlayer: {
                        currentTime: videoPlayerCurrentTime
                    },
                    storage: {
                        setItem: jasmine.createSpy()
                    },
                    config: {
                        saveStateUrl: 'http://example.com/save_user_state'
                    }
                };

                spyOn($, 'ajax');
                spyOn(Time, 'formatFull').andCallThrough();
            });

            afterEach(function () {
                state = undefined;
            });

            it('data is not an object, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: videoPlayerCurrentTime,
                    data: undefined,
                    ajaxData: {
                        saved_video_position: Time.formatFull(Math.round(videoPlayerCurrentTime))
                    }
                });
            });

            it('data contains speed, async is false', function () {
                itSpec({
                    asyncVal: false,
                    speedVal: speed,
                    positionVal: undefined,
                    data: {
                        speed: speed
                    },
                    ajaxData: {
                        speed: speed
                    }
                });
            });

            it('data contains float position, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: newCurrentTime,
                    data: {
                        saved_video_position: newCurrentTime
                    },
                    ajaxData: {
                        saved_video_position: Time.formatFull(Math.round(newCurrentTime))
                    }
                });
            });

            it('data contains speed and rounded position, async is false', function () {
                itSpec({
                    asyncVal: false,
                    speedVal: speed,
                    positionVal: Math.round(newCurrentTime),
                    data: {
                        speed: speed,
                        saved_video_position: Math.round(newCurrentTime)
                    },
                    ajaxData: {
                        speed: speed,
                        saved_video_position: Time.formatFull(Math.round(newCurrentTime))
                    }
                });
            });

            it('data contains empty object, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: undefined,
                    data: {},
                    ajaxData: {}
                });
            });

            it('data contains position 0, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: 0,
                    data: {
                        saved_video_position: 0
                    },
                    ajaxData: {
                        saved_video_position: Time.formatFull(Math.round(0))
                    }
                });
            });

            return;

            function itSpec(value) {
                var asyncVal    = value.asyncVal,
                    speedVal    = value.speedVal,
                    positionVal = value.positionVal,
                    data        = value.data,
                    ajaxData    = value.ajaxData;

                Initialize.prototype.saveState.call(state, asyncVal, data);

                if (speedVal) {
                    expect(state.storage.setItem).toHaveBeenCalledWith(
                        'speed',
                        speedVal,
                        true
                    );
                }
                if (positionVal) {
                    expect(state.storage.setItem).toHaveBeenCalledWith(
                        'savedVideoPosition',
                        positionVal,
                        true
                    );
                    expect(Time.formatFull).toHaveBeenCalledWith(
                        positionVal
                    );
                }
                expect($.ajax).toHaveBeenCalledWith({
                    url: state.config.saveStateUrl,
                    type: 'POST',
                    async: asyncVal,
                    dataType: 'json',
                    data: ajaxData
                });
            }
        });
    });

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
