/*
jQuery loupeAndLightbox Plugin
* Version 1.0
* 05-10-2010
* Author: M.Biscan
* requires jQuery1.4.2
Copyright (c) 2010 M.Biscan

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Softwarevent.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
(function($){
  $.fn.loupeAndLightbox = function(options) {
    var settings = $.extend({}, $.fn.loupeAndLightbox.defaults, options);

    return this.each(function() {
      var $this = $(this),
          $targetImage = $this.find('> img'),
          $magnifiedImage = $('<img />'),
          $loupe = $('<div class="larger" style="overflow: hidden;">'),
          $lightbox = $('<div class="lal_lightbox">'),
          $errorMessage = $('<div class="lal_errorMessage">'),
          $loader = $('<div class="lal_loader">Loading...</div>');

      ///////////
      // Setup //
      ///////////
      $this.css({
        cursor:'default'
      });
      $targetImage.css({
        cursor: 'pointer'
      });
      $magnifiedImage.css({
        position: 'absolute',
        maxWidth: 'none'       //Override edx's max-width default
      });
      $loupe.css({
        cursor: 'none',
        display: 'none',
        border:settings.border,
        height:settings.height,
        overflow:'hidden',
        position:'absolute',
        bottom:0,
        left:-settings.width,
        width:settings.width,
        zIndex:settings.zIndex,
        borderRadius:'50%',
        background:'#FFF',
      });
      $lightbox.css({
        background:'#000',
        left:0,
        position:'absolute',
        top:0,
        zIndex:settings.zIndex-1,
        'opacity':0.75,
        'filter':'alpha(opacity=75)'
      });
      $errorMessage
        .text(settings.errorMessage)
        .css({
          height:settings.height,
          width:settings.width
        });
      $loader.css({
          height:settings.height,
          width:settings.width
        });

      ////////////
      // Events //
      ////////////
      $this.click(function(event) {
        event.preventDefault();
      });
      $targetImage.click(function(event) {
        if(!$loupe.hasClass('visible')) {
          var left = event.pageX,
              top = event.pageY;

          if(!$magnifiedImage.hasClass('appended')) {
            getMagnifiedImage();
          }

          setTimeout(function() {
            appendLoupe();
            magnify(left, top);
            if(settings.lightbox == true) {
              appendLightbox();
            }
          }, 100);
        }
      });
      $targetImage.mousemove(function(event) {
        var left = event.pageX,
            top = event.pageY,
            offsetTop = $targetImage.offset().top-($loupe.width()/2),
            offsetLeft = $targetImage.offset().left-($loupe.height()/2),
            offsetBottom = $targetImage.offset().top+$targetImage.height()+($loupe.height()/2),
            offsetRight = $targetImage.offset().left+$targetImage.width()+($loupe.width()/2);

        if(left < offsetLeft || left > offsetRight || top < offsetTop || top > offsetBottom) {
          $targetImage.css({cursor:'default'});
        } else {
          $targetImage.css({cursor:'crosshair'});
          magnify(left, top);
        }
      }).click(function() {
        detachLoupe();
        if(settings.lightbox == true) {
          detachLightbox();
        }
      }).mouseleave(function() {
        pulseLoupe();
      });

      // Detach when clicking outside of the loupe
      $(document).click(function(event) {
        if($loupe.hasClass('visible')) {
          detachLoupe();

          if(settings.lightbox == true) {
            detachLightbox();
          }
        }
      });

      // Resizes lightbox with window
      $(window).resize(function() {
        if($loupe.is(':visible')) {
          $loupe.css({
            //left:$targetImage.offset().left+($targetImage.width()/2)-($loupe.width()/2),
            //top:$targetImage.offset().top+($targetImage.height()/2)-($loupe.height()/2)
          });

          $magnifiedImage.css({
            left:-($magnifiedImage.width()/2)+($loupe.width()/2),
            top:-($magnifiedImage.height()/2)+($loupe.height()/2)
          });

          $lightbox.css({
            height:$(document).height(),
            width:$(document).width()
          });
        }
      });

      ///////////////////////
      // Private functions //
      ///////////////////////
      function magnify(left, top) {
        $loupe
          .css({
            //left:left-(settings.width/2),
            //top:top-(settings.height/2)
          });

        var heightDiff = $magnifiedImage.height()/$targetImage.height(),
            widthDiff = $magnifiedImage.width()/$targetImage.width(),
            magnifierTop = (-(top - $targetImage.offset().top)*heightDiff)+(settings.height/2),
            magnifierLeft = (-(left - $targetImage.offset().left)*widthDiff)+(settings.width/2);

        $magnifiedImage.css({
            top:magnifierTop,
            left:magnifierLeft
        });
      };

      function appendLoupe() {
        $loupe
          .appendTo($('div.place'))
          .append($magnifiedImage)
          .fadeIn(settings.fadeSpeed, function() {
            $(this).addClass('visible');
          });
      };

      function getMagnifiedImage() {
        var src = $this.attr('href');
        $loader.appendTo($loupe);

        $magnifiedImage
          .load(function() {
            $(this).addClass('appended');
            $loader.detach();
          })
          .error(function () {
            $(this).hide();
            $loupe
              .append($errorMessage)
              .addClass('lal_loadError');
            $loader.detach();
          })
          .attr('src', src);
      };

      function detachLoupe() {
        $loupe.fadeOut(settings.fadeSpeed, function() {
          $(this)
            .removeClass('visible')
            .detach();
        });
      };

      function appendLightbox() {
        $lightbox
          .appendTo('body')
          .css({
            height:$(document).height(),
            width:$(document).width()
          })
          .fadeIn(settings.fadeSpeed);
      };

      function detachLightbox() {
        $lightbox.fadeOut(settings.fadeSpeed, function() {
          $(this).detach();
        });
      };

      function pulseLoupe() {
        $loupe.fadeTo(150, 0.25, function() {
          $(this).fadeTo(150, 1.0);
        });
      };
    });
  };

  ////////////////////
  // Default optons //
  ////////////////////
  $.fn.loupeAndLightbox.defaults = {
    zIndex:1000,
    width:150,
    height:150,
    border:'2px solid #ccc',
    fadeSpeed:250,
    lightbox:true,
    errorMessage:'Image load error'
  };
})(jQuery);

