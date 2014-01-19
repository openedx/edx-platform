/**
 * Simple image input
 *
 *
 * Click on image. Update the coordinates of a dot on the image.
 * The new coordinates are the location of the click.
 */

/**
 * 'The wise adapt themselves to circumstances, as water molds itself to the
 * pitcher.'
 *
 * ~ Chinese Proverb
 */

window.ImageInput = (function ($, undefined) {
    var ImageInput = ImageInputConstructor;

    ImageInput.prototype = {
        constructor: ImageInputConstructor,
        clickHandler: clickHandler
    };

    return ImageInput;

    function ImageInputConstructor(elementId) {
        var _this = this;

        this.elementId = elementId;

        this.el = $('#imageinput_' + this.elementId);
        this.crossEl = $('#cross_' + this.elementId);
        this.inputEl = $('#input_' + this.elementId);

        this.el.on('click', function (event) {
            _this.clickHandler(event);
        });
    }

    function clickHandler(event) {
        var posX = event.offsetX ?
                event.offsetX : event.pageX - this.el[0].offsetLeft,
            posY = event.offsetY ?
                event.offsetY : event.pageY - this.el[0].offsetTop,

            // To reduce differences between values returned by different kinds
            // of browsers, we round `posX` and `posY`.
            //
            // IE10: `posX` and `posY` - float.
            // Chrome, FF: `posX` and `posY` - integers.
            result = '[' + Math.round(posX) + ',' + Math.round(posY) + ']';

        this.crossEl.css({
            left: posX - 15,
            top: posY - 15,
            visibility: 'visible'
        });

        this.inputEl.val(result);
    }
}).call(this, window.jQuery);
