define(['poll/poll_main.js'], function(PollMain) {
    'use strict';

    function Poll(el) {
        return new PollMain(el);
    }

    window.Poll = Poll;

    return Poll;
});
