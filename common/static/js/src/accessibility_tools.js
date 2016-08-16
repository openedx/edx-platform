/*

============================================
License for Application
============================================

This license is governed by United States copyright law, and with respect to matters
of tort, contract, and other causes of action it is governed by North Carolina law,
without regard to North Carolina choice of law provisions.  The forum for any dispute
resolution shall be in Wake County, North Carolina.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list
   of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this
   list of conditions and the following disclaimer in the documentation and/or other
   materials provided with the distribution.

3. The name of the author may not be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

*/
var focusedElementBeforeModal;

var accessible_modal = function(trigger, closeButtonId, modalId, mainPageId) {
  // Modifies a lean modal to optimize focus management.
  // "trigger" is the selector for the link element that triggers the modal.
  // "closeButtonId" is the selector for the button that closes out the modal.
  // "modalId" is the selector for the modal being managed
  // "mainPageId" is the selector for the main part of the page
  //
  // based on http://accessibility.oit.ncsu.edu/training/aria/modal-window/modal-window.js
  //
  // see http://accessibility.oit.ncsu.edu/blog/2013/09/13/the-incredible-accessible-modal-dialog/
  // for more information on managing modals
  //
    var focusableElementsString = 'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, *[tabindex], *[contenteditable]';

    $(trigger).click(function() {
        focusedElementBeforeModal = $(trigger);

    // when modal is opened, adjust tabindexes and aria-hidden attributes
        $(mainPageId).attr('aria-hidden', 'true');
        $(modalId).attr('aria-hidden', 'false');

        var focusableItems = $(modalId).find('*').filter(focusableElementsString).filter(':visible');

        focusableItems.attr('tabindex', '2');
        $(closeButtonId).attr('tabindex', '1');
        $(closeButtonId).focus();

    // define the last tabbable element to complete tab cycle
        var last;
        if (focusableItems.length !== 0) {
            last = focusableItems.last();
        } else {
            last = $(closeButtonId);
        }

    // tab on last element in modal returns to the first one
        last.on('keydown', function(e) {
            var keyCode = e.keyCode || e.which;
      // 9 is the js keycode for tab
            if (!e.shiftKey && keyCode === 9) {
                e.preventDefault();
                $(closeButtonId).focus();
            }
        });

    // shift+tab on first element in modal returns to the last one
        $(closeButtonId).on('keydown', function(e) {
            var keyCode = e.keyCode || e.which;
      // 9 is the js keycode for tab
            if (e.shiftKey && keyCode == 9) {
                e.preventDefault();
                last.focus();
            }
        });

    // manage aria-hidden attrs, return focus to trigger on close
        $('#lean_overlay, ' + closeButtonId).click(function() {
            $(mainPageId).attr('aria-hidden', 'false');
            $(modalId).attr('aria-hidden', 'true');
            focusedElementBeforeModal.focus();
        });

    // get modal to exit on escape key
        $('.modal').on('keydown', function(e) {
            var keyCode = e.keyCode || e.which;
      // 27 is the javascript keycode for the ESC key
            if (keyCode === 27) {
                e.preventDefault();
                $(closeButtonId).click();
            }
        });

    // In IE, focus shifts to iframes when they load.
    // These lines ensure that focus is shifted back to the close button
    // in the case that a modal that contains an iframe is opened in IE.
    // see http://stackoverflow.com/questions/15792620/how-to-get-focus-back-for-parent-window-from-an-iframe-programmatically-in-javas
        var initialFocus = true;
        $(modalId).find('iframe').on('focus', function() {
            if (initialFocus) {
                $(closeButtonId).focus();
                initialFocus = false;
            }
        });
    });
};

// NOTE: This is a gross hack to make the skip links work for Webkit browsers
// see http://stackoverflow.com/questions/6280399/skip-links-not-working-in-chrome/12720183#12720183

// handle things properly for clicks
$('.nav-skip').click(function() {
    var href = $(this).attr('href');
    if (href) {
        $(href).attr('tabIndex', -1).focus();
    }
});
// and for the enter key
$('.nav-skip').keypress(function(e) {
    if (e.which == 13) {
        var href = $(this).attr('href');
        if (href) {
            $(href).attr('tabIndex', -1).focus();
        }
    }
});

// Creates a window level SR object that can be used for giving audible feedback to screen readers.
$(function() {
    var SRAlert;

    SRAlert = (function() {
        function SRAlert() {
            $('body').append('<div id="reader-feedback" class="sr" style="display:none" aria-hidden="false" aria-atomic="true" aria-live="assertive"></div>');
            this.el = $('#reader-feedback');
        }

        SRAlert.prototype.clear = function() {
            return this.el.html(' ');
        };

        SRAlert.prototype.readElts = function(elts) {
            var feedback = '';
            $.each(elts, function(idx, value) {
                return feedback += '<p>' + $(value).html() + '</p>\n';
            });
            return this.el.html(feedback);
        };

        SRAlert.prototype.readText = function(text) {
            return this.el.text(text);
        };

        return SRAlert;
    })();

    window.SR = new SRAlert;
});
