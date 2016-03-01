;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone'],
        function (gettext, $, _, Backbone) {

        return Backbone.View.extend({
            srFullscreenText: gettext('Click to toggle distraction-free mode'),

            events: {
                'click': 'toggleFullscreen',
            },

            initialize: function (options) {
                this.in_fullscreen=false;
                var $fullscreenElement = $('.xblock-student_view-sequential');
                $(document).focusin(this.exitIfNothingFocused.bind(this));
            },

            toggleFullscreen: function(event) {
                event.preventDefault();

                if (this.$el.hasClass('in_fullscreen')) {
                    this.exitFullscreen();
                } else {
                    this.enterFullscreen();
                }
            },

            exitIfNothingFocused: function() {
                if(this.in_fullscreen) {
                    setTimeout(function(exitFtn) {
                        var $fullscreenElement = $('.xblock-student_view-sequential');
                        var focusedChildren = $fullscreenElement.find(':focus'); 
                        if (focusedChildren.length < 1 && document.activeElement.tabIndex != -1) {
                            exitFtn();
                        }
                    }, 10, this.exitFullscreen.bind(this));
                }
            },

            launchIntoFullscreen: function(element) {
                if(element.requestFullscreen) {
                    element.requestFullscreen();
                } else if(element.mozRequestFullScreen) {
                    element.mozRequestFullScreen();
                } else if(element.webkitRequestFullscreen) {
                    element.webkitRequestFullscreen();
                } else if(element.msRequestFullscreen) {
                    element.msRequestFullscreen();
                }
            },

            enterFullscreen: function() {
                this.$el.addClass('in_fullscreen');
                this.in_fullscreen=true;
                var $fullscreenElement = $('.xblock-student_view-sequential');
                $fullscreenElement.addClass('fullscreen-element');
                var $fullscreenBreadcrumb = $('.course-wrapper .course-content .sequence .path');
                $fullscreenBreadcrumb.addClass('in_fullscreen');
                this.launchIntoFullscreen($fullscreenElement[0]);
            },

            exitFullscreen: function() {
                this.$el.removeClass('in_fullscreen');
                this.in_fullscreen=false;
                var $fullscreenElement = $('.xblock-student_view-sequential');
                $fullscreenElement.removeClass('fullscreen-element');
                var $fullscreenBreadcrumb = $('.course-wrapper .course-content .sequence .path');
                $fullscreenBreadcrumb.removeClass('in_fullscreen');
                if(document.exitFullscreen) {
                    document.exitFullscreen();
                } else if(document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if(document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
