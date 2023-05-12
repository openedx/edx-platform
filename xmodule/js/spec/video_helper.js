(function() {
    'use strict';

    // Stub window.Video.loadYouTubeIFrameAPI()
    // eslint-disable-next-line no-undef
    window.Video.loadYouTubeIFrameAPI = jasmine.createSpy('window.Video.loadYouTubeIFrameAPI').and.returnValue(
        function(scriptTag) {
            var event = document.createEvent('Event');
            // eslint-disable-next-line no-undef
            if (fixture === 'video.html') {
                event.initEvent('load', false, false);
            } else {
                event.initEvent('error', false, false);
            }
            scriptTag.dispatchEvent(event);
        }
    );
}).call(this);
