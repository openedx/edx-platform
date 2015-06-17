;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Model.extend({
        defaults: {
            in_timed_exam: true,
            is_proctored: true,
            exam_display_name: 'Midterm',
            exam_url_path: '',
            time_remaining_seconds: 45, //2 * 60 + 15,
            low_threshold: 30,
            critically_low_threshold: 15,
            lastFetched: new Date()
        },
        getRemainingSeconds: function() {
            var currentTime = (new Date()).getTime();
            var lastFetched = this.get('lastFetched').getTime();
            var totalSeconds = this.get('time_remaining_seconds') - (currentTime - lastFetched)/1000;
            return (totalSeconds > 0) ? totalSeconds : 0;
        },
        getFormattedRemainingTime: function() {
            var totalSeconds = this.getRemainingSeconds();
            var hours = parseInt( totalSeconds / 3600 ) % 24;
            var minutes = parseInt( totalSeconds / 60 ) % 60;
            var seconds = Math.floor( totalSeconds % 60 );

            return hours + ":" + (minutes < 10 ? "0" + minutes : minutes)
                + ":" + (seconds  < 10 ? "0" + seconds : seconds);

        },
        getRemainingTimeState: function() {
            var totalSeconds = this.getRemainingSeconds();
            if (totalSeconds > this.get('low_threshold')) {
                return "";
            }
            else if (totalSeconds <= this.get('low_threshold') && totalSeconds > this.get('critically_low_threshold')) {
                return "low-time warning";
            }
            else {
                return "low-time critical";
            }
        }
    });

});

})(define || RequireJS.define);
