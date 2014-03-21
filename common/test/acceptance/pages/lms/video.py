"""
Video player in the courseware.
"""

import time
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from bok_choy.javascript import wait_for_js, js_defined


@js_defined('window.Video')
class VideoPage(PageObject):
    """
    Video player in the courseware.
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='div.xmodule_VideoModule').present

    @property
    def elapsed_time(self):
        """
        Amount of time elapsed since the start of the video, in seconds.
        """
        elapsed, _ = self._video_time()
        return elapsed

    @property
    def duration(self):
        """
        Total duration of the video, in seconds.
        """
        _, duration = self._video_time()
        return duration

    @property
    def is_playing(self):
        """
        Return a boolean indicating whether the video is playing.
        """
        return self.q(css='a.video_control').present and self.q(css='a.video_control.pause').present

    @property
    def is_paused(self):
        """
        Return a boolean indicating whether the video is paused.
        """
        return self.q(css='a.video_control').present and self.q(css='a.video_control.play').present

    @wait_for_js
    def play(self):
        """
        Start playing the video.
        """
        self.q(css='a.video_control.play').first.click()
        EmptyPromise(lambda: self.is_playing, "Video is playing")

    @wait_for_js
    def pause(self):
        """
        Pause the video.
        """
        self.q(css='a.video_control.pause').first.click()
        EmptyPromise(lambda: self.is_paused, "Video is paused")

    def _video_time(self):
        """
        Return a tuple `(elapsed_time, duration)`, each in seconds.
        """
        # The full time has the form "0:32 / 3:14"
        all_times = self.q(css='div.vidtime').text

        if len(all_times) == 0:
            self.warning('Could not find video time')

        else:
            full_time = all_times[0]

            # Split the time at the " / ", to get ["0:32", "3:14"]
            elapsed_str, duration_str = full_time.split(' / ')

            # Convert each string to seconds
            return self._parse_time_str(elapsed_str), self._parse_time_str(duration_str)

    def _parse_time_str(self, time_str):
        """
        Parse a string of the form 1:23 into seconds (int).
        """
        time_obj = time.strptime(time_str, '%M:%S')
        return time_obj.tm_min * 60 + time_obj.tm_sec
