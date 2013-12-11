/////////////////////////////////////////////////////////////////////////////
//
//  Simple image input
//
////////////////////////////////////////////////////////////////////////////////

// click on image, update coordinates
// put a dot at location of click, on image

window.image_input_click = function (id, event) {
    var iidiv = document.getElementById("imageinput_" + id),
        pos_x = event.offsetX ? (event.offsetX) : event.pageX - iidiv.offsetLeft,
        pos_y = event.offsetY ? (event.offsetY) : event.pageY - iidiv.offsetTop,
        // To reduce differences between values returned by different kinds of
        // browsers, we round `pos_x` and `pos_y`.
        // IE10: `pos_x` and `pos_y` - float.
        // Chrome, FF: `pos_x` and `pos_y` - integers.
        result = "[" + Math.round(pos_x) + "," + Math.round(pos_y) + "]",
        cx = (pos_x - 15) + "px",
        cy = (pos_y - 15) + "px",
        cross = document.getElementById("cross_" + id);

    cross.style.left = cx;
    cross.style.top = cy;
    cross.style.visibility = "visible" ;
    document.getElementById("input_" + id).value = result;
};
