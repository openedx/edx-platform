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

window.ImageInput = (function($, undefined) {
    var ImageInput = ImageInputConstructor;

    ImageInput.prototype = {
        constructor: ImageInputConstructor,
        clickHandler: clickHandler
    };

    return ImageInput;

    function ImageInputConstructor(elementId) {
        this.el = $('#imageinput_' + elementId);
        this.crossEl = $('#cross_' + elementId);
        this.inputEl = $('#input_' + elementId);

        this.el.on('click', this.clickHandler.bind(this));
    }

    function clickHandler(event) {
        var offset = this.el.offset(),
            posX = event.offsetX ?
                event.offsetX : event.pageX - offset.left,
            posY = event.offsetY ?
                event.offsetY : event.pageY - offset.top,

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
