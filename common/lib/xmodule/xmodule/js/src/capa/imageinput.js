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

window.image_input_click = function (id, event) {
    var iiDiv = document.getElementById('imageinput_' + id),

        posX = event.offsetX ? event.offsetX : event.pageX - iiDiv.offsetLeft,
        posY = event.offsetY ? event.offsetY : event.pageY - iiDiv.offsetTop,

        cross = document.getElementById('cross_' + id),

        // To reduce differences between values returned by different kinds of
        // browsers, we round `posX` and `posY`.
        //
        // IE10: `posX` and `posY` - float.
        // Chrome, FF: `posX` and `posY` - integers.
        result = '[' + Math.round(posX) + ',' + Math.round(posY) + ']';

    cross.style.left = (posX - 15) + 'px';
    cross.style.top = (posY - 15) + 'px';
    cross.style.visibility = 'visible';

    document.getElementById('input_' + id).value = result;
};
