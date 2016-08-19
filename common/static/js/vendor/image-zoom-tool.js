/*
 * edX Image Zoom Tool
 * v0.0.1
 *
 * This script was modified from our jquery.loupeAndLightbox.js script, but 
 * goes further and adds keyboard accessibility to the zooming controls.
*/

(function($){
    $.fn.edxImageZoomTool = function(options) {
        var settings = $.extend({}, $.fn.edxImageZoomTool.defaults, options),
            keys = {
                up: 38,
                down: 40,
                left: 37,
                right: 39,
                space: 32,
                enter: 13,
                esc: 27,
                tab: 9
            };

        return this.each(function() {
            var $this = $(this),
                $targetImage = $this.find('> img'),
                $magnifiedImage = $('<img />'),
                $zoomed = $('<div class="larger" style="overflow: hidden;" tabindex="-1">'),
                $lightbox = $('<div class="edx_imagezoom_lightbox">'),
                $errorMessage = $('<div class="edx_imagezoom_errorMessage">'),
                $loader = $('<div class="edx_imagezoom_loader">Loading...</div>'),
                $zoomArea = $('.zooming-image-place'),
                $imageArea = $('.zooming-image-place a'),
                $indicator = $('.zooming-image-place .indicator'),
                $disc = $('.edx-zoom-loop');

            $this.css({
                cursor: 'default'
            });

            $targetImage.css({
                cursor: 'pointer'
            });

            $magnifiedImage.css({
                position: 'absolute',
                maxWidth: 'none'
            });

            $lightbox.css({
                position: 'absolute',
                left: 0,
                top: 0,
                zIndex: settings.zIndex-1,
                opacity: 0.75,
                filter: 'alpha(opacity=75)',
                background: '#000'
            });

            $errorMessage
                .text(settings.errorMessage)
                    .css({
                        height: settings.height,
                        width: settings.width
                    });

            $loader.css({
                height: settings.height,
                width: settings.width
            });

            $targetImage.on('click', function(event) {
                event.preventDefault();

                if (!$zoomed.hasClass('is-visible')) {
                    var left = event.pageX,
                        top = event.pageY;

                    if (!$magnifiedImage.hasClass('is-appended')) {
                        getMagnifiedImage();
                    }

                    setTimeout(function() {
                        appendZoomed(true);
                        magnifyWithMouse(left, top);

                        if (settings.lightbox == true) {
                            appendLightbox();
                        }
                    }, 100);
                }
            }).mousemove(function(event) {
                var left = event.pageX,
                    top = event.pageY,
                    offsetTop = $targetImage.offset().top - ($zoomed.width() / 2),
                    offsetLeft = $targetImage.offset().left - ($zoomed.height() / 2),
                    offsetBottom = $targetImage.offset().top + $targetImage.height() + ($zoomed.height() / 2),
                    offsetRight = $targetImage.offset().left + $targetImage.width() + ($zoomed.width() / 2);

                if (left < offsetLeft || left > offsetRight || top < offsetTop || top > offsetBottom) {
                    $targetImage.css({ cursor: 'default' });
                } else {
                    $targetImage.css({ cursor: 'crosshair' });
                    magnifyWithMouse(left, top);
                }
            }).click(function() {
                detachZoomed();

                if (settings.lightbox == true) {
                    detachLightbox();
                }
            }).mouseleave(function() {
                pulseZoomed();
            });

            $imageArea.on('keydown', function(event) {
                var left = event.pageX,
                    top = event.pageY;

                switch (event.which) {
                    case keys.enter:
                    case keys.space:
                        event.preventDefault();

                        if (!$zoomed.hasClass('is-visible')) {

                            if (!$magnifiedImage.hasClass('is-appended')) {
                                getMagnifiedImage();
                            }

                            setTimeout(function() {
                                appendZoomed(true);
                                addZoomLocationDisc();
                                magnifyWithMouse(left, top, true);

                                if (settings.lightbox == true) {
                                    appendLightbox();
                                }
                            }, 100);
                        }
                        break;

                    default:
                        return true;
                }
            });

            $zoomed.on('keydown', function(event) {
                var left,
                    top,
                    $zoomedImage = $zoomed.find('img'),
                    offsetTop = $targetImage.offset().top - ($zoomed.width() / 2),
                    offsetLeft = $targetImage.offset().left - ($zoomed.height() / 2),
                    offsetBottom = $targetImage.offset().top + $targetImage.height() + ($zoomed.height() / 2),
                    offsetRight = $targetImage.offset().left + $targetImage.width() + ($zoomed.width() / 2);

                switch (event.which) {
                    case keys.esc:
                        if ($zoomed.hasClass('is-visible')) {
                            detachZoomed();
                            removeZoomLocationDisc();

                            if (settings.lightbox == true) {
                                detachLightbox();
                                removeZoomLocationDisc();
                            }

                            $imageArea.focus();
                        }
                        break;

                    case keys.up:
                        // we move five spaces at a time
                        magnifyWithKeyboard(0, 10, event);
                        break;

                    case keys.down:
                        // we move five spaces at a time
                        magnifyWithKeyboard(0, -10, event);
                        break;

                    case keys.left:
                        // we move five spaces at a time
                        magnifyWithKeyboard(10, 0, event);
                        break;

                    case keys.right:
                        // we move five spaces at a time
                        magnifyWithKeyboard(-10, 0, event);
                        break;

                    default:
                        return true;
                }
            });

            $(document).click(function(event) {
                if ($zoomed.hasClass('is-visible')) {
                    detachZoomed();
                    removeZoomLocationDisc();

                    if (settings.lightbox == true) {
                        detachLightbox();
                        removeZoomLocationDisc();
                    }
                }
            });

            $(window).resize(function() {
                if ($zoomed.is(':visible')) {
                    $magnifiedImage.css({
                        left: -($magnifiedImage.width() / 2) + ($zoomed.width() / 2),
                        top: -($magnifiedImage.height() / 2) + ($zoomed.height() / 2)
                    });

                    $lightbox.css({
                        height: $(document).height(),
                        width: $(document).width()
                    });
                }
            });
            
            function addZoomLocationDisc() {
                if ($zoomArea.find($('.edx-zoom-loop'))) {
                    $('.edx-zoom-loop').remove();
                }

                var discHeight = $zoomed.height() / 5,
                    discWidth = $zoomed.width() / 5,
                    zoomAreaHeight = $zoomArea.height(),
                    zoomAreaWidth = $zoomArea.width(),
                    zoomAreaCenterX = (zoomAreaWidth / 2) - (discWidth / 2),
                    zoomAreaCenterY = (zoomAreaHeight / 2) - (discHeight / 2);

                $disc = $('<div class="edx-zoom-loop"></div>')
                    .height(discHeight)
                    .width(discWidth)
                    .css({
                        left: zoomAreaCenterX,
                        top: zoomAreaCenterY
                    });
                    
                $zoomArea.append($disc);
            };
            
            function removeZoomLocationDisc() {
                $disc.remove();
            };

            function magnifyWithMouse(left, top, centered) {
                var heightDiff = $magnifiedImage.height() / $targetImage.height(),
                    widthDiff = $magnifiedImage.width() / $targetImage.width(),
                    magnifierTop,
                    magnifierLeft;

                if (centered) {
                    magnifierTop = (-$magnifiedImage.height() / 2) + ($zoomed.height() / 2);
                    magnifierLeft = (-$magnifiedImage.width() / 2) + ($zoomed.width() / 2);
                } else {
                    magnifierTop = (-(top - $targetImage.offset().top) * heightDiff) + (settings.height / 2);
                    magnifierLeft = (-(left - $targetImage.offset().left) * widthDiff) + (settings.width / 2);
                }

                $magnifiedImage.css({
                    top: magnifierTop,
                    left: magnifierLeft
                });
            };

            function magnifyWithKeyboard(left, top, event) {
                var largeLeft,
                    largeTop,
                    smallLeft,
                    smallTop;

                event.preventDefault();

                largeLeft = $magnifiedImage.css('left');
                largeLeft = largeLeft.replace('px', '');
                largeLeft = parseInt(largeLeft) + left;

                largeTop = $magnifiedImage.css('top');
                largeTop = largeTop.replace('px', '');
                largeTop = parseInt(largeTop) + top;

                smallLeft = $disc.css('left');
                smallLeft = smallLeft.replace('px', '');
                smallLeft = parseInt(smallLeft) - (left / 10);

                smallTop = $disc.css('top');
                smallTop = smallTop.replace('px', '');
                smallTop = parseInt(smallTop) - (top / 10);

                $magnifiedImage.css({
                    top: largeTop + 'px',
                    left: largeLeft + 'px'
                });

                $disc.css({
                    top: smallTop + 'px',
                    left: smallLeft + 'px'
                });
            };

            function appendZoomed(focus) {
                $zoomed.appendTo($('.zooming-image-place'))
                    .append($magnifiedImage)
                        .fadeIn(settings.fadeSpeed, function() {
                            $(this).addClass('is-visible');
                        });

                if (focus) {
                    $zoomed.focus();
                }
            };

            function getMagnifiedImage() {
                var src = $this.attr('href');

                $loader.appendTo($zoomed);

                $magnifiedImage.load(function() {
                    $(this).addClass('is-appended');
                    $loader.detach();
                })
                .error(function () {
                    $(this).hide();

                    $zoomed.append($errorMessage)
                        .addClass('edx_imagezoom_loadError');

                    $loader.detach();
                })
                .attr('src', src);
            };

            function detachZoomed() {
                $zoomed.fadeOut(settings.fadeSpeed, function() {
                    $(this).removeClass('is-visible')
                        .detach();
                });
            };

            function appendLightbox() {
                $lightbox.appendTo('body')
                    .css({
                        height: $(document).height(),
                        width: $(document).width()
                    })
                    .fadeIn(settings.fadeSpeed);
            };

            function detachLightbox() {
                $lightbox.fadeOut(settings.fadeSpeed, function() {
                    $(this).detach();
                });
            };

            function pulseZoomed() {
                $zoomed.fadeTo(150, 0.25, function() {
                    $(this).fadeTo(150, 1.0);
                });
            };
        });
    };

    $.fn.edxImageZoomTool.defaults = {
        zIndex: 1000,
        fadeSpeed: 250,
        lightbox: true,
        errorMessage: 'Image load error'
    };
})(jQuery);
