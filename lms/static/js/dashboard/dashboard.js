var edx = edx || {};


(function ($) {
    'use strict';

    $(document).ready(function () {
        new CircleProgress();
    });
}(jQuery));


class CircleProgress {

    constructor() {
        let rings = [...document.querySelectorAll('.progress-ring')]
        rings.forEach((el) => {
            const percent = el.getAttribute('data-percent')
            this.setProgress(el, percent)
        })
    }

    setProgress(el, percent) {
        var circle = el.querySelector('.progress-ring__circle');
        var circleBg = el.querySelector('.progress-ring__circle-bg');
        var radius = circle.r.baseVal.value;
        var circumference = radius * 2 * Math.PI;
        const offset = circumference - percent / 100 * circumference;
        circle.style.strokeDashoffset = offset;
        circleBg.style.strokeDashoffset = circumference - 100 / 100 * circumference;
    }
}
