/**
 * Provides utilities to open and close the library content picker.
 * 
 * To use this picker you need to add the following code into your template:
 * 
 * ```
 * <div id="library-content-picker" class="picker"></div>
 * <div class="picker-cover"></div>
 * ```
 */
define(['jquery'],
function($) {
    'use strict';

    const closePicker = (picker, pickerCover) => {
        $(pickerCover).css('display', 'none');
        $(picker).empty();
        $(picker).css('display', 'none');
        $('body').removeClass('picker-open');
    };

    const openPicker = (contentPickerUrl, picker, pickerCover) => {
        // Add event listen to close picker when the iframe tells us to
        window.addEventListener("message", function (event) {
            if (event.data === 'closeComponentPicker') {
                closePicker(picker, pickerCover);
            }
        }.bind(this));

        $(pickerCover).css('display', 'block');
        // xss-lint: disable=javascript-jquery-html
        $(picker).html(
            `<iframe src="${contentPickerUrl}" onload="this.contentWindow.focus()" frameborder="0" style="width: 100%; height: 100%;"></iframe>`
        );
        $(picker).css('display', 'block');

        // Prevent background from being scrollable when picker is open
        $('body').addClass('picker-open');
    };

    const createComponent = (contentPickerUrl) => {
      const picker = document.querySelector("#library-content-picker");
      const pickerCover = document.querySelector(".picker-cover");

      return openPicker(contentPickerUrl, picker, pickerCover);
    };

    return {
        createComponent: createComponent,
    };
});
