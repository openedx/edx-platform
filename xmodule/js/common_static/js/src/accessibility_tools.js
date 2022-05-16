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

var $focusedElementBeforeModal,
    focusableElementsString = 'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, *[tabindex], *[contenteditable]';

var reassignTabIndexesAndAriaHidden = function(focusableElementsFilterString, closeButtonId, modalId, mainPageId) {
    // Sets appropriate elements to tab indexable and properly sets aria_hidden on content outside of modal
    // "focusableElementsFilterString" is a string that indicates all elements that should be focusable
    // "closeButtonId" is the selector for the button that closes out the modal.
    // "modalId" is the selector for the modal being managed
    // "mainPageId" is the selector for the main part of the page
    // Returns a list of focusableItems
    var focusableItems;

    $(mainPageId).attr('aria-hidden', 'true');
    $(modalId).attr('aria-hidden', 'false');

    focusableItems = $(modalId).find('*')
        .filter(focusableElementsFilterString)
        .filter(':visible');

    focusableItems.attr('tabindex', '2');
    $(closeButtonId).attr('tabindex', '1').focus();

    return focusableItems;
};

var trapTabFocus = function(focusableItems, closeButtonId) {
    // Determines last element in modal and traps focus by causing tab
    // to focus on the first modal element (close button)
    // "focusableItems" all elements in the modal that are focusable
    // "closeButtonId" is the selector for the button that closes out the modal.
    // returns the last focusable element in the modal.
    var $last;
    if (focusableItems.length !== 0) {
        $last = focusableItems.last();
    } else {
        $last = $(closeButtonId);
    }

    // tab on last element in modal returns to the first one
    $last.on('keydown', function(e) {
        var keyCode = e.keyCode || e.which;
        // 9 is the js keycode for tab
        if (!e.shiftKey && keyCode === 9) {
            e.preventDefault();
            $(closeButtonId).focus();
        }
    });

    return $last;
};

var trapShiftTabFocus = function($last, closeButtonId) {
    $(closeButtonId).on('keydown', function(e) {
        var keyCode = e.keyCode || e.which;
        // 9 is the js keycode for tab
        if (e.shiftKey && keyCode === 9) {
            e.preventDefault();
            $last.focus();
        }
    });
};

var bindReturnFocusListener = function($previouslyFocusedElement, closeButtonId, modalId, mainPageId) {
    // Ensures that on modal close, focus is returned to the element
    // that had focus before the modal was opened.
    $('#lean_overlay, ' + closeButtonId).click(function() {
        $(mainPageId).attr('aria-hidden', 'false');
        $(modalId).attr('aria-hidden', 'true');
        $previouslyFocusedElement.focus();
    });
};

var bindEscapeKeyListener = function(modalId, closeButtonId) {
    $(modalId).on('keydown', function(e) {
        var keyCode = e.keyCode || e.which;
        // 27 is the javascript keycode for the ESC key
        if (keyCode === 27) {
            e.preventDefault();
            $(closeButtonId).click();
        }
    });
};

var trapFocusForAccessibleModal = function(
    $previouslyFocusedElement,
    focusableElementsFilterString,
    closeButtonId,
    modalId,
    mainPageId) {
    // Re assess the page for which items internal to the modal should be focusable,
    // Should be called after the content of the accessible_modal is changed in order
    // to ensure that the correct elements are accessible.
    var focusableItems, $last;
    focusableItems = reassignTabIndexesAndAriaHidden(
      focusableElementsFilterString,
      closeButtonId,
      modalId,
      mainPageId
    );
    $last = trapTabFocus(focusableItems, closeButtonId);
    trapShiftTabFocus($last, closeButtonId);
    bindReturnFocusListener($previouslyFocusedElement, closeButtonId, modalId, mainPageId);
    bindEscapeKeyListener(modalId, closeButtonId);
};

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
    var initialFocus
    $(trigger).click(function() {
        $focusedElementBeforeModal = $(trigger);

        trapFocusForAccessibleModal(
            $focusedElementBeforeModal,
            focusableElementsString,
            closeButtonId,
            modalId,
            mainPageId
        );

        // In IE, focus shifts to iframes when they load.
        // These lines ensure that focus is shifted back to the close button
        // in the case that a modal that contains an iframe is opened in IE.
        // see http://stackoverflow.com/questions/15792620/
        initialFocus = true;
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
    var href;
    if (e.which === 13) {
        href = $(this).attr('href');
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
            // This initialization sometimes gets done twice, so take to only create a single reader-feedback div.
            var readerFeedbackID = 'reader-feedback',
                $readerFeedbackSelector = $('#' + readerFeedbackID);

            if ($readerFeedbackSelector.length === 0) {
                edx.HtmlUtils.append(
                    $('body'),
                    edx.HtmlUtils.interpolateHtml(
                        edx.HtmlUtils.HTML('<div id="{readerFeedbackID}" class="sr" aria-live="polite"></div>'),
                        {readerFeedbackID: readerFeedbackID}
                    )
                );
            }
            this.el = $('#' + readerFeedbackID);
        }

        SRAlert.prototype.clear = function() {
            edx.HtmlUtils.setHtml(this.el, '');
        };

        SRAlert.prototype.readElts = function(elts) {
            var texts = [];
            $.each(elts, function(idx, value) {
                texts.push($(value).html());
            });
            return this.readTexts(texts);
        };

        SRAlert.prototype.readText = function(text) {
            return this.readTexts([text]);
        };

        SRAlert.prototype.readTexts = function(texts) {
            var htmlFeedback = edx.HtmlUtils.HTML('');
            $.each(texts, function(idx, value) {
                htmlFeedback = edx.HtmlUtils.interpolateHtml(
                    edx.HtmlUtils.HTML('{previous_feedback}<p>{value}</p>\n'),
                    // "value" may be HTML, if an element is being passed
                    {previous_feedback: htmlFeedback, value: edx.HtmlUtils.HTML(value)}
                );
            });
            edx.HtmlUtils.setHtml(this.el, htmlFeedback);
        };

        return SRAlert;
    }());

    window.SR = new SRAlert();
});
