/////////////////////////////////////////////////////////////////////////////
//
//  Simple image input 
//
////////////////////////////////////////////////////////////////////////////////

// click on image, return coordinates
// put a dot at location of click, on imag

// window.image_input_click = function(id,event){

function image_input_click(id,event){
    iidiv = document.getElementById("imageinput_"+id);
    pos_x = event.offsetX?(event.offsetX):event.pageX-iidiv.offsetLeft;
    pos_y = event.offsetY?(event.offsetY):event.pageY-iidiv.offsetTop;
    result = "[" + pos_x + "," + pos_y + "]";
    cx = (pos_x-15) +"px";
    cy = (pos_y-15)  +"px" ;
    // alert(result);
    document.getElementById("cross_"+id).style.left = cx;
    document.getElementById("cross_"+id).style.top = cy;
    document.getElementById("cross_"+id).style.visibility = "visible" ;
    document.getElementById("input_"+id).value =result;
}
