//////////////////////////////////////////////////////////////////////////////
//
//  Simple schematic capture
//
////////////////////////////////////////////////////////////////////////////////

// Chris Terman, Nov. 2011

// add schematics to a document with 
//
//   <input type="hidden" class="schematic" name="unique_form_id" value="...schematic/netlist info..." .../>
//
// other attributes you can add to the input tag:
//   width -- width in pixels of diagram
//   height -- height in pixels of diagram
//   parts -- comma-separated list of parts for parts bin (see parts_map)

// TO DO:

// - read initial diagram from value of hidden input field
// - write diagram state into value of hidden input field
// - wire labels?
// - devices: diode, nfet, pfet, opamp, scope probe
// - icons for test equipment? (scope, sig gen, counter, ...)

// - rotate multiple objects around their center of mass
// - rubber band wires when moving components
// - add help messages/tooltips
// - tool bar (zoom in/zoom out, rotate, mode: wire/select, save/restore, simulate, help)
// - scroll canvas
// - freeze_diagram, freeze_properties attributes (freeze certain components/properties?)
// - add thumb to resize work area

// - label nodes, extract component netlist
// - simulation: operating points, trans, ac analysis, sweeps?
// - how to integrate plot display? 

// add ourselves to the tasks that get performed when window is loaded
window.onload = add_schematic_handler(window.onload);

function update_schematics() {
    // set up each schematic on the page
    var schematics = document.getElementsByClassName('schematic');
    for (var i = schematics.length - 1; i >= 0; i--)
	if (schematics[i].getAttribute("loaded") != "true") {
	    new Schematic(schematics[i]);
	    schematics[i].setAttribute("loaded","true");
	}
}

function add_schematic_handler(other_onload) {
    return function() {
	// execute othe onload functions first
	if (other_onload) other_onload();
	
	update_schematics();
    }
}

background_style = 'rgb(200,255,200)';
element_style = 'rgb(255,255,255)';

// list of all the defined parts
parts_map = {
    'g': Ground,
    'v': VSource,
    'i': ISource,
    'r': Resistor,
    'c': Capacitor,
    'l': Inductor,
};

///////////////////////////////////////////////////////////////////////////////
//
//  Schematic = diagram + parts bin + status area
//
////////////////////////////////////////////////////////////////////////////////

// setup a schematic by populating the <div> with the appropriate children
function Schematic(input) {
    var div = document.createElement('div');
    // set up div so we can position elements inside of it
    div.style.position = 'relative';

    // grab attributes from the <div> that created us
    this.div = div;
    this.grid = 8;

    this.scale = 2;
    this.origin_x = 0;
    this.origin_y = 0;

    // start with a background element with normal positioning
    this.background = document.createElement('canvas');
    this.background.style.backgroundColor = background_style;

    this.status_div = document.createElement('div');
    this.status_div.style.borderStyle = 'solid';
    this.status_div.style.borderWidth = '1px';
    this.status_div.style.position = 'absolute';
    this.status_div.style.padding = '2px';
    this.status_div.style.backgroundColor = element_style;
    this.status = document.createTextNode('Ready.');
    this.status_div.appendChild(this.status);

    this.connection_points = new Array();  // location string => list of cp's
    this.components = [];

    // this is where schematic is rendered
    this.canvas = document.createElement('canvas');
    this.canvas.tabIndex = 1; // so we get keystrokes
    this.canvas.style.borderStyle = 'solid';
    this.canvas.style.borderWidth = '1px';
    this.canvas.style.position = 'absolute';

    this.canvas.schematic = this;
    this.canvas.addEventListener('mousemove',this.mouse_move,false);
    this.canvas.addEventListener('mouseover',this.mouse_enter,false);
    this.canvas.addEventListener('mouseout',this.mouse_leave,false);
    this.canvas.addEventListener('mousedown',this.mouse_down,false);
    this.canvas.addEventListener('mouseup',this.mouse_up,false);
    this.canvas.addEventListener('dblclick',this.double_click,false);
    this.canvas.addEventListener('keydown',this.key_down,false);
    this.canvas.addEventListener('keypress',this.key_press,false);

    // make the canvas "clickable" by registering a dummy click handler
    // this should make things work on the iPad
    this.canvas.addEventListener('click',function(){},false);

    this.dragging = false;
    this.drawCursor = false;
    this.cursor_x = 0;
    this.cursor_y = 0;
    this.draw_cursor = null;
    this.select_rect = null;
    this.wire = null;

    // repaint simply draws this buffer and then adds selected elements on top
    this.bg_image = document.createElement('canvas');

    // use user-supplied list of parts if supplied
    // else just populate parts bin with all the parts
    var parts = input.getAttribute('parts');
    if (parts) parts = parts.split(',');
    else {
	parts = new Array();
	for (var p in parts_map) parts.push(p);
    }

    // now add the parts to the parts bin
    var parts_left = this.width + 3 + background_margin;
    var parts_top = background_margin;
    this.parts_bin = [];
    for (var i = 0; i < parts.length; i++) {
	var part = new Part(this);
	part.set_component(new parts_map[parts[i]](part,0,0,0));
	this.parts_bin.push(part);
    }

    // add all elements to the DOM
    div.appendChild(this.background);
    div.appendChild(this.canvas);
    div.appendChild(this.status_div);
    for (var i = 0; i < this.parts_bin.length; i++)
	div.appendChild(this.parts_bin[i].canvas);
    input.parentNode.insertBefore(div,input.nextSibling);

    // make sure other code can find us!
    input.schematic = this;
    this.input = input;

    // set locations of all the elements in the editor
    var w = parseInt(input.getAttribute('width'));
    var h = parseInt(input.getAttribute('height'));
    this.set_locations(w,h);
}

background_margin = 5;
part_w = 56;   // size of a parts bin compartment
part_h = 56;
status_height = 18;
thumb_style = 'rgb(128,128,128)';

// w,h are the dimensions of the canvas, everyone else is positioned accordingly
Schematic.prototype.set_locations = function(w,h) {
    // limit the shrinkage factor
    w = Math.max(w,120);
    h = Math.max(h,120);

    this.width = w;
    this.height = h;
    this.bg_image.width = w;
    this.bg_image.height = h;

    this.min_x = 0;
    this.min_y = 0;
    this.max_x = w/this.scale;
    this.max_y = h/this.scale;

    // configure canvas
    this.canvas.style.left = background_margin + 'px';
    this.canvas.style.top = background_margin + 'px';
    this.canvas.width = w;
    this.canvas.height = h;
    this.redraw_background();   // redraw diagram

    // configure status bar
    this.status_div.style.left = background_margin + 'px';
    this.status_div.style.top = this.canvas.offsetTop + this.canvas.offsetHeight + 3 + 'px';
    this.status_div.style.width = (w - 4) + 'px';   // subtract interior padding
    this.status_div.style.height = status_height + 'px';

    // configure parts bin
    var total_w = this.canvas.offsetLeft + this.canvas.offsetWidth;
    var parts_left = total_w + 3;
    var parts_top = background_margin;
    var parts_h_limit = this.canvas.offsetTop + this.canvas.offsetHeight;
    for (var i = 0; i < this.parts_bin.length; i++) {
	var part = this.parts_bin[i];
	part.set_location(parts_left,parts_top);

	total_w = part.right();
	parts_top = part.bottom()-1;
	if (parts_top + part_h > parts_h_limit) {
	    parts_left = total_w - 1;
	    parts_top = background_margin;
	}
    }

    // configure background
    var total_h = this.status_div.offsetTop + this.status_div.offsetHeight + background_margin;
    total_w += background_margin;
    this.background.height = total_h;
    this.background.width = total_w;

    /* enable when there's support for resizing schematic
    // redraw thumb
    var c = this.background.getContext('2d');
    c.clearRect(0,0,w,h);
    c.strokeStyle = thumb_style;
    c.lineWidth = 1;
    c.beginPath();
    w = total_w - 1;
    h = total_h - 1;
    c.moveTo(w,h-4); c.lineTo(w-4,h);
    c.moveTo(w,h-8); c.lineTo(w-8,h);
    c.moveTo(w,h-12); c.lineTo(w-12,h);
    c.stroke();
    */
}

// update the value field of our corresponding input field with JSON
// representation of schematic
Schematic.prototype.update_value = function() {
    // to do: fill in this.input.value
}

Schematic.prototype.add_component = function(new_c) {
    this.components.push(new_c);

    // create undoable edit record here
}

Schematic.prototype.remove_component = function(c) {
    var index = this.components.indexOf(c);
    if (index != -1) this.components.splice(index,1);
}

// add connection point to list of connection points at that location
Schematic.prototype.add_connection_point = function(cp) {
    cplist = this.connection_points[cp.location]
    if (cplist) cplist.push(cp);
    else {
	cplist = [cp];
	this.connection_points[cp.location] = cplist;
    }

    // return list of conincident connection points
    return cplist;
}

// remove connection point from the list points at the old location
Schematic.prototype.remove_connection_point = function(cp,old_location) {
    // remove cp from list at old location
    var cplist = this.connection_points[old_location];
    if (cplist) {
	var index = cplist.indexOf(cp);
	if (index != -1) {
	    cplist.splice(index,1);
	    // if no more connections at this location, remove
	    // entry from array to keep our search time short
	    if (cplist.length == 0)
		delete this.connection_points[old_location];
	}
    }
}

// connection point has changed location: remove, then add
Schematic.prototype.update_connection_point = function(cp,old_location) {
    this.remove_connection_point(cp,old_location);
    return this.add_connection_point(cp);
}

// add a wire to the schematic
Schematic.prototype.add_wire = function(x1,y1,x2,y2) {
    var new_wire = new Wire(this,x1,y1,x2,y2);
    this.add_component(new_wire);
    new_wire.move_end();
    return new_wire;
}

// see if connection points of component c split any wires
Schematic.prototype.check_wires = function(c) {
    for (var i = this.components.length - 1; i >=0; --i) {
	var cc = this.components[i];
	if (cc != c) {  // don't check a component against itself
	    // only wires will do return non-null from a bisect call
	    var cp = cc.bisect(c);
	    if (cp) {
		// cc is a wire bisected by connection point cp

		// remove biscted wire
		cc.delete();

		// add two new wires with cp in the middle
		this.add_wire(cc.x,cc.y,cp.x,cp.y);
		this.add_wire(cc.x+cc.dx,cc.y+cc.dy,cp.x,cp.y);
		this.redraw_background();
		break;
	    }
	}
    }
}

///////////////////////////////////////////////////////////////////////////////
//
//  Drawing support -- deals with scaling and scrolling of diagrama
//
////////////////////////////////////////////////////////////////////////////////

// here to redraw background image containing static portions of the schematic.
// Also redraws dynamic portion.
Schematic.prototype.redraw_background = function() {
    var c = this.bg_image.getContext('2d');
    var w = this.bg_image.width;
    var h = this.bg_imageheight;

    // paint background color
    c.fillStyle = element_style;
    c.fillRect(0,0,this.width,this.height);

    // border
    //c.strokeStyle = "rgb(0,0,0)";
    //c.strokeRect(0,0,this.width,this.height);

    // grid
    c.strokeStyle = "rgb(128,128,128)";
    var first_x = this.min_x;
    var last_x = this.max_x;
    var first_y = this.min_y;
    var last_y = this.max_y;
    for (var i = first_x; i < last_x; i += this.grid)
	this.draw_line(c,i,first_y,i,last_y,0.1);
    for (var i = first_y; i < last_y; i += this.grid)
	this.draw_line(c,first_x,i,last_x,i,0.1);

    // unselected components
    for (var i = this.components.length - 1; i >= 0; --i) {
	var component = this.components[i];
	if (!component.selected) component.draw(c);
    }

    this.redraw();   // background changed, redraw on screen
}

// redraw what user sees = static image + dynamic parts
Schematic.prototype.redraw = function() {
    var c = this.canvas.getContext('2d');

    // put static image in the background
    c.drawImage(this.bg_image, 0, 0);

    // selected components
    for (var i = this.components.length - 1; i >= 0; --i) {
	var component = this.components[i];
	if (component.selected) component.draw(c);
    }

    // connection points: draw one at each location
    for (var location in this.connection_points) {
	var cplist = this.connection_points[location];
	cplist[0].draw(c,cplist.length);
    }
    
    // draw new wire
    if (this.wire) {
	var r = this.wire;
	c.strokeStyle = selected_style;
	this.draw_line(c,r[0],r[1],r[2],r[3],1);
    }

    // draw selection rectangle
    if (this.select_rect) {
	var r = this.select_rect;
	c.lineWidth = 1;
	c.strokeStyle = selected_style;
	c.beginPath();
	c.moveTo(r[0],r[1]);
	c.lineTo(r[0],r[3]);
	c.lineTo(r[2],r[3]);
	c.lineTo(r[2],r[1]);
	c.lineTo(r[0],r[1]);
	c.stroke();
    }
    
    // finally overlay cursor
    if (this.drawCursor && this.draw_cursor) {
	//var x = this.cursor_x;
	//var y = this.cursor_y;
	//this.draw_text(c,'('+x+','+y+')',x+this.grid,y-this.grid,10);
	this.draw_cursor(c,this.cursor_x,this.cursor_y);
    }
}

// draws a cross cursor
Schematic.prototype.cross_cursor = function(c,x,y) {
    this.draw_line(c,x-this.grid,y,x+this.grid,y,1);
    this.draw_line(c,x,y-this.grid,x,y+this.grid,1);
}

Schematic.prototype.draw_line = function(c,x1,y1,x2,y2,width) {
    c.lineWidth = width*this.scale;
    c.beginPath();
    c.moveTo((x1 - this.origin_x) * this.scale,(y1 - this.origin_y) * this.scale);
    c.lineTo((x2 - this.origin_x) * this.scale,(y2 - this.origin_y) * this.scale);
    c.stroke();
}

Schematic.prototype.draw_arc = function(c,x,y,radius,start_radians,end_radians,anticlockwise,width,filled) {
    c.lineWidth = width*this.scale;
    c.beginPath();
    c.arc((x - this.origin_x)*this.scale,(y - this.origin_y)*this.scale,radius*this.scale,
	  start_radians,end_radians,anticlockwise);
    if (filled) c.fill();
    else c.stroke();
}

Schematic.prototype.draw_text = function(c,text,x,y,size) {
    c.font = size*this.scale+'pt sans-serif'
    c.fillText(text,(x - this.origin_x) * this.scale,(y - this.origin_y) * this.scale);
}

// add method to canvas to compute relative coords for event
HTMLCanvasElement.prototype.relMouseCoords = function(event){
    // run up the DOM tree to figure out coords for top,left of canvas
    var totalOffsetX = 0;
    var totalOffsetY = 0;
    var canvasY = 0;
    var currentElement = this;
    do {
        totalOffsetX += currentElement.offsetLeft;
        totalOffsetY += currentElement.offsetTop;
    }
    while(currentElement = currentElement.offsetParent);

    // now compute relative position of click within the canvas
    this.mouse_x = event.pageX - totalOffsetX;
    this.mouse_y = event.pageY - totalOffsetY;
}

///////////////////////////////////////////////////////////////////////////////
//
//  Event handling
//
////////////////////////////////////////////////////////////////////////////////

// process special keys here since they don't get delivered correctly on keypress
Schematic.prototype.key_down = function(event) {
    if (!event) event = window.event;
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;
    var code = event.keyCode;

    if (code == 8 || code == 46) {
	// delete selected components
	for (var i = sch.components.length - 1; i >= 0; --i) {
	    var component = sch.components[i];
	    if (component.selected) component.delete(1);
	}
	sch.redraw();
	event.preventDefault();
	return false;
    }
    return true;
}

// process normal characters
Schematic.prototype.key_press = function(event) {
    if (!event) event = window.event;
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;
    var code = window.event ? event.keyCode : event.charCode;
    var char = String.fromCharCode(code);

    if (char == 'r' || char == 'R') {
	// rotate
	for (var i = sch.components.length - 1; i >= 0; --i) {
	    var component = sch.components[i];
	    if (component.selected) component.rotate(1);
	}
	sch.redraw();
	event.preventDefault();
	return false;
    }
    return true;
}

Schematic.prototype.mouse_enter = function(event) {
    if (!event) event = window.event;
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

    // see if user has selected a new part
    if (sch.new_part) {
	// grab incoming part, turn off selection of parts bin
	var part = sch.new_part;
	sch.new_part = null;
	part.select(false);

	// make a clone of the component in the parts bin
	part = part.component.clone(sch,sch.cursor_x,sch.cursor_y);

	// unselect everything else in the schematic, add part and select it
	sch.unselect_all(-1);
	sch.redraw_background();  // so we see any components that got unselected
	sch.add_component(part);
	part.set_select(true);

	// and start dragging it
	sch.drag_begin();
    }

    sch.drawCursor = true;
    sch.redraw();
    sch.canvas.focus();  // capture key strokes
}

Schematic.prototype.mouse_leave = function(event) {
    if (!event) event = window.event;
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;
    sch.drawCursor = false;
    sch.redraw();
}

Schematic.prototype.unselect_all = function(which) {
    for (var i = this.components.length - 1; i >= 0; --i)
	if (i != which) this.components[i].set_select(false);
}

Schematic.prototype.mouse_down = function(event) {
    if (!event) event = window.event;
    else event.preventDefault();
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

    // determine where event happened in schematic coordinates
    sch.canvas.relMouseCoords(event);
    var x = sch.canvas.mouse_x/sch.scale + sch.origin_x;
    var y = sch.canvas.mouse_y/sch.scale + sch.origin_y;
    sch.cursor_x = Math.round(x/sch.grid) * sch.grid;
    sch.cursor_y = Math.round(y/sch.grid) * sch.grid;

    // is mouse over a connection point?  If so, start dragging a wire
    var cplist = sch.connection_points[sch.cursor_x + ',' + sch.cursor_y];
    if (cplist && !event.shiftKey) {
	sch.unselect_all(-1);
	sch.wire = [sch.cursor_x,sch.cursor_y,sch.cursor_x,sch.cursor_y];
    } else {
	// give all components a shot at processing the selection event
	var which = -1;
	for (var i = sch.components.length - 1; i >= 0; --i)
	    if (sch.components[i].select(x,y,event.shiftKey)) {
		if (sch.components[i].selected) {
		    sch.drag_begin();
		    which = i;  // keep track of component we found
		}
		break;
	    }
	// did we just click on a previously selected component?
	var reselect = which!=-1 && sch.components[which].was_previously_selected;

	if (!event.shiftKey) {
	    // if shift key isn't pressed and we didn't click on component
	    // that was already selected, unselect everyone except component
	    // we just clicked on
	    if (!reselect) sch.unselect_all(which);

	    // if there's nothing to drag, set up a selection rectangle
	    if (!sch.dragging) sch.select_rect = [sch.canvas.mouse_x,sch.canvas.mouse_y,
						  sch.canvas.mouse_x,sch.canvas.mouse_y];
	}
    }

    sch.redraw_background();
}

Schematic.prototype.mouse_up = function(event) {
    if (!event) event = window.event;
    else event.preventDefault();
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

    // drawing a new wire
    if (sch.wire) {
	var r = sch.wire;
	sch.wire = null;

	if (r[0]!=r[2] || r[1]!=r[3]) {
	    // insert wire component
	    sch.add_wire(r[0],r[1],r[2],r[3]);
	    sch.redraw_background();
	} else sch.redraw();
    }

    // dragging
    if (sch.dragging) sch.drag_end();

    // selection rectangle
    if (sch.select_rect) {
	var r = sch.select_rect;

	// if select_rect is a point, we've already dealt with selection
	// in mouse_down handler
	if (r[0]!=r[2] || r[1]!=r[3]) {
	    // convert to schematic coordinates
	    var s = [r[0]/sch.scale + sch.origin_x, r[1]/sch.scale + sch.origin_y,
		     r[2]/sch.scale + sch.origin_x, r[3]/sch.scale + sch.origin_y];
	    canonicalize(s);
	    
	    if (!event.shiftKey) sch.unselect_all();

	    // select components that intersect selection rectangle
	    for (var i = sch.components.length - 1; i >= 0; --i)
		sch.components[i].select_rect(s,event.shiftKey);
	}

	sch.select_rect = null;
	sch.redraw_background();
    }
}

Schematic.prototype.double_click = function(event) {
    if (!event) event = window.event;
    else event.preventDefault();
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

    // determine where event happened in schematic coordinates
    sch.canvas.relMouseCoords(event);
    var x = sch.canvas.mouse_x/sch.scale + sch.origin_x;
    var y = sch.canvas.mouse_y/sch.scale + sch.origin_y;
    sch.cursor_x = Math.round(x/sch.grid) * sch.grid;
    sch.cursor_y = Math.round(y/sch.grid) * sch.grid;

    // see if we double-clicked a component.  If so, edit it's properties
    for (var i = sch.components.length - 1; i >= 0; --i)
	if (sch.components[i].edit_properties(x,y)) break;
}

Schematic.prototype.drag_begin = function() {
    // let components know they're about to move
    for (var i = this.components.length - 1; i >= 0; --i) {
	var component = this.components[i];
	if (component.selected) component.move_begin();
    }

    // remember where drag started
    this.drag_x = this.cursor_x;
    this.drag_y = this.cursor_y;
    this.dragging = true;
}

Schematic.prototype.drag_end = function() {
    // let components know they're done moving
    for (var i = this.components.length - 1; i >= 0; --i) {
	var component = this.components[i];
	if (component.selected) component.move_end();
    }
    this.dragging = false;
}

Schematic.prototype.mouse_move = function(event) {
    if (!event) event = window.event;
    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

    sch.canvas.relMouseCoords(event);
    var x = sch.canvas.mouse_x/sch.scale + sch.origin_x;
    var y = sch.canvas.mouse_y/sch.scale + sch.origin_y;
    sch.cursor_x = Math.round(x/sch.grid) * sch.grid;
    sch.cursor_y = Math.round(y/sch.grid) * sch.grid;

    if (sch.wire) {
	// update new wire end point
	sch.wire[2] = sch.cursor_x;
	sch.wire[3] = sch.cursor_y;
    } else if (sch.dragging) {
	// see how far we moved
	var dx = sch.cursor_x - sch.drag_x;
	var dy = sch.cursor_y - sch.drag_y;
	if (dx != 0 || dy != 0) {
	    // update position for next time
	    sch.drag_x = sch.cursor_x;
	    sch.drag_y = sch.cursor_y;

	    // give all components a shot at processing the event
	    for (var i = sch.components.length - 1; i >= 0; --i) {
		var component = sch.components[i];
		if (component.selected) component.move(dx,dy);
	    }
	}
    } else if (sch.select_rect) {
	// update moving corner of selection rectangle
	sch.select_rect[2] = sch.canvas.mouse_x;
	sch.select_rect[3] = sch.canvas.mouse_y;
	//sch.message(sch.select_rect.toString());
    }
    
    // just redraw dynamic components
    sch.redraw();
}

///////////////////////////////////////////////////////////////////////////////
//
//  Status message and dialogs
//
////////////////////////////////////////////////////////////////////////////////

Schematic.prototype.message = function(message) {
    this.status.nodeValue = message;
    this.recompute_height();
}

Schematic.prototype.append_message = function(message) {
    this.status.nodeValue += ' / '+message;
    this.recompute_height();
}
    
// set up a dialog with specified title, content and two buttons at
// the bottom: OK and Cancel.  If Cancel is clicked, dialog goes away
// and we're done.  If OK is clicked, dialog goes away and the
// callback function is called with the content as an argument (so
// that the values of any fields can be captured).
Schematic.prototype.dialog = function(title,content,callback) {
    // create the div for the top level of the dialog, add to DOM
    var dialog = document.createElement('div');
    dialog.sch = this;
    dialog.content = content;

    // div to hold the title
    var head = document.createElement('div');
    head.style.backgroundColor = 'black';
    head.style.color = 'white';
    head.style.textAlign = 'center';
    head.style.padding = '5px';
    head.appendChild(document.createTextNode(title));
    dialog.appendChild(head);

    // div to hold the content
    var body = document.createElement('div');
    body.appendChild(content);
    body.style.padding = '5px';
    dialog.appendChild(body);

    // OK button
    var ok_button = document.createElement('span');
    ok_button.appendChild(document.createTextNode('OK'));
    ok_button.dialog = dialog;   // for the handler to use
    ok_button.addEventListener('click',dialog_okay,false);
    ok_button.style.border = '1px solid';
    ok_button.style.padding = '5px';
    ok_button.style.margin = '10px';

    // cancel button
    var cancel_button = document.createElement('span');
    cancel_button.appendChild(document.createTextNode('Cancel'));
    cancel_button.dialog = dialog;   // for the handler to use
    cancel_button.addEventListener('click',dialog_cancel,false);
    cancel_button.style.border = '1px solid';
    cancel_button.style.padding = '5px';
    cancel_button.style.margin = '10px';

    // div to hold the two buttons
    var buttons = document.createElement('div');
    buttons.appendChild(ok_button);
    buttons.appendChild(cancel_button);
    buttons.style.padding = '5px';
    buttons.style.margin = '10px';
    dialog.appendChild(buttons);

    // add to DOM
    dialog.style.background = 'white';
    dialog.style.zindex = '1000';
    dialog.style.position = 'absolute';
    dialog.style.left = this.canvas.mouse_x+'px';
    dialog.style.top = this.canvas.mouse_y+'px';
    dialog.style.border = '2px solid';
    dialog.callback = callback;
    this.div.appendChild(dialog);
}

// callback when user click "Cancel" in a dialog
function dialog_cancel(event) {
    if (!event) event = window.event;
    var dialog = (window.event) ? event.srcElement.dialog : event.target.dialog;

    // remove the dialog from the top-level div of the schematic
    dialog.parentNode.removeChild(dialog);
}

// callback when user click "OK" in a dialog
function dialog_okay(event) {
    if (!event) event = window.event;
    var dialog = (window.event) ? event.srcElement.dialog : event.target.dialog;

    // remove the dialog from the top-level div of the schematic
    dialog.parentNode.removeChild(dialog);

    // invoke the callback with the dialog contents as the argument
    if (dialog.callback) dialog.callback(dialog.content);
}

///////////////////////////////////////////////////////////////////////////////
//
//  Parts bin
//
////////////////////////////////////////////////////////////////////////////////

// one instance will be created for each part in the parts bin
function Part(sch) {
    this.sch = sch;
    this.component = null;
    this.selected = false;

    // set up canvas
    this.canvas = document.createElement('canvas');
    this.canvas.style.borderStyle = 'solid';
    this.canvas.style.borderWidth = '1px';
    this.canvas.style.position = 'absolute';
    this.canvas.height = part_w;
    this.canvas.width = part_h;
    this.canvas.part = this;

    this.canvas.addEventListener('mousedown',this.mouse_down,false);
    this.canvas.addEventListener('mouseup',this.mouse_up,false);

    // make the part "clickable" by registering a dummy click handler
    // this should make things work on the iPad
    this.canvas.addEventListener('click',function(){},false);
}

Part.prototype.set_location = function(left,top) {
    this.canvas.style.left = left + 'px';
    this.canvas.style.top = top + 'px';
}

Part.prototype.right = function() {
    return this.canvas.offsetLeft + this.canvas.offsetWidth;
}

Part.prototype.bottom = function() {
    return this.canvas.offsetTop + this.canvas.offsetHeight;
}

Part.prototype.set_component = function(component) {
    this.component = component;

    // figure out scaling and centering of parts icon
    var b = component.bounding_box;
    var dx = b[2] - b[0];
    var dy = b[3] - b[1];
    this.scale = 1; //Math.min(part_w/(1.2*dx),part_h/(1.2*dy));
    this.origin_x = this.scale*(b[0] + dx/2.0) - part_w/2.0;
    this.origin_y = this.scale*(b[1] + dy/2.0) - part_h/2.0;

    this.redraw();
}

Part.prototype.redraw = function(part) {
    var c = this.canvas.getContext('2d');

    // paint background color
    c.fillStyle = this.selected ? selected_style : element_style;
    c.fillRect(0,0,part_w,part_h);

    if (this.component) this.component.draw(c);
}

Part.prototype.select = function(which) {
    this.selected = which;
    this.redraw();
}

Part.prototype.update_connection_point = function(cp,old_location) {
    // no connection points in the parts bin
}

Part.prototype.draw_line = function(c,x1,y1,x2,y2,width) {
    c.lineWidth = width*this.scale;
    c.beginPath();
    c.moveTo((x1 - this.origin_x) * this.scale,(y1 - this.origin_y) * this.scale);
    c.lineTo((x2 - this.origin_x) * this.scale,(y2 - this.origin_y) * this.scale);
    c.stroke();
}

Part.prototype.draw_arc = function(c,x,y,radius,start_radians,end_radians,anticlockwise,width,filled) {
    c.lineWidth = width*this.scale;
    c.beginPath();
    c.arc((x - this.origin_x)*this.scale,(y - this.origin_y)*this.scale,radius*this.scale,
	  start_radians,end_radians,anticlockwise);
    if (filled) c.fill();
    else c.stroke();
}

Part.prototype.draw_text = function(c,text,x,y,size) {
    // no text displayed for the parts icon
}

Part.prototype.mouse_down = function(event) {
    if (!event) event = window.event;
    var part = (window.event) ? event.srcElement.part : event.target.part;

    part.select(true);
    part.sch.new_part = part;
}

Part.prototype.mouse_up = function(event) {
    if (!event) event = window.event;
    var part = (window.event) ? event.srcElement.part : event.target.part;

    part.select(false);
    part.sch.new_part = null;
}

////////////////////////////////////////////////////////////////////////////////
//
//  Rectangle helper functions
//
////////////////////////////////////////////////////////////////////////////////

// rect is an array of the form [left,top,right,bottom]

// ensure left < right, top < bottom
function canonicalize(r) {
    var temp;

    // canonicalize bounding box
    if (r[0] > r[2]) {
	temp = r[0];
	r[0] = r[2];
	r[2] = temp;
    }
    if (r[1] > r[3]) {
	temp = r[1];
	r[1] = r[3];
	r[3] = temp;
    }
}
    
function between(x,x1,x2) {
    return x1 <= x && x <= x2;
}

function inside(rect,x,y) {
    return between(x,rect[0],rect[2]) && between(y,rect[1],rect[3]);
}

// only works for manhattan rectangles
function intersect(r1,r2) {
    // look for non-intersection, negate result
    var result = !(r2[0] > r1[2] ||
		   r2[2] < r1[0] ||
		   r2[1] > r1[3] ||
		   r2[3] < r1[1]);

    // if I try to return the above expression, javascript returns undefined!!!
    return result;
}

////////////////////////////////////////////////////////////////////////////////
//
//  Component base class
//
////////////////////////////////////////////////////////////////////////////////

property_size = 5;  // point size for Component property text
normal_style = 'rgb(0,0,0)';  // color for unselected components
selected_style = 'rgb(64,255,64)';  // highlight color for selected components

function Component(sch,x,y,rotation) {
    this.sch = sch;
    this.x = x;
    this.y = y;
    this.rotation = rotation;
    this.selected = false;
    this.properties = new Array();
    this.bounding_box = [0,0,0,0];   // in device coords [left,top,right,bottom]
    this.bbox = this.bounding_box;   // in absolute coords
    this.connections = [];
}

Component.prototype.add_connection = function(offset_x,offset_y) {
    this.connections.push(new ConnectionPoint(this,offset_x,offset_y));
}

Component.prototype.update_coords = function() {
    var x = this.x;
    var y = this.y;

    // update bbox
    var b = this.bounding_box;
    this.bbox[0] = this.transform_x(b[0],b[1]) + x;
    this.bbox[1] = this.transform_y(b[0],b[1]) + y;
    this.bbox[2] = this.transform_x(b[2],b[3]) + x;
    this.bbox[3] = this.transform_y(b[2],b[3]) + y;
    canonicalize(this.bbox);

    // update connections
    for (var i = this.connections.length - 1; i >= 0; --i)
	this.connections[i].update_location();
}

Component.prototype.rotate = function(amount) {
    var old_rotation = this.rotation;
    this.rotation = (this.rotation + amount) % 8;
    this.update_coords();

    // create an undoable edit record here
    // using old_rotation
}

Component.prototype.move_begin = function() {
    // remember where we started this move
    this.move_x = this.x;
    this.move_y = this.y;
}

Component.prototype.move = function(dx,dy) {
    // update coordinates
    this.x += dx;
    this.y += dy;
    this.update_coords();
}
    
Component.prototype.move_end = function() {
    var dx = this.x - this.move_x;
    var dy = this.y - this.move_y;

    if (dx != 0 || dy != 0) {
	// create an undoable edit record here

	this.sch.check_wires(this);
    }
}

Component.prototype.delete = function() {
    // remove connection points from schematic
    for (var i = this.connections.length - 1; i >= 0; --i) {
	var cp = this.connections[i];
	this.sch.remove_connection_point(cp,cp.location);
    }

    // remove component from schematic
    this.sch.remove_component(this);

    // create an undoable edit record here
}

Component.prototype.transform_x = function(x,y) {
    var rot = this.rotation;
    if (rot == 0 || rot == 6) return x;
    else if (rot == 1 || rot == 5) return -y;
    else if (rot == 2 || rot == 4) return -x;
    else return y;
}

Component.prototype.transform_y = function(x,y) {
    var rot = this.rotation;
    if (rot == 1 || rot == 7) return x;
    else if (rot == 2 || rot == 6) return -y;
    else if (rot == 3 || rot == 5) return -x;
    else return y;
}

Component.prototype.draw_line = function(c,x1,y1,x2,y2) {
    c.strokeStyle = this.selected ? selected_style : normal_style;
    var nx1 = this.transform_x(x1,y1) + this.x;
    var ny1 = this.transform_y(x1,y1) + this.y;
    var nx2 = this.transform_x(x2,y2) + this.x;
    var ny2 = this.transform_y(x2,y2) + this.y;
    this.sch.draw_line(c,nx1,ny1,nx2,ny2,1);
}

Component.prototype.draw_circle = function(c,x,y,radius,filled) {
    if (filled) c.fillStyle = this.selected ? selected_style : normal_style;
    else c.strokeStyle = this.selected ? selected_style : normal_style;
    var nx = this.transform_x(x,y) + this.x;
    var ny = this.transform_y(x,y) + this.y;

    this.sch.draw_arc(c,nx,ny,radius,0,2*Math.PI,false,1,filled);
}

rot_angle = [
  0.0,		// NORTH (identity)
  Math.PI/2,	// EAST (rot270)
  Math.PI,	// SOUTH (rot180)
  3*Math.PI/2,  // WEST (rot90)
  0.0,		// RNORTH (negy)
  Math.PI/2,	// REAST (int-neg)
  Math.PI,	// RSOUTH (negx)
  3*Math.PI/2,	// RWEST (int-pos)
];

Component.prototype.draw_arc = function(c,x,y,radius,start_radians,end_radians) {
    c.strokeStyle = this.selected ? selected_style : normal_style;
    var nx = this.transform_x(x,y) + this.x;
    var ny = this.transform_y(x,y) + this.y;
    this.sch.draw_arc(c,nx,ny,radius,
		      start_radians+rot_angle[this.rotation],end_radians+rot_angle[this.rotation],
		      false,1,false);
}

Component.prototype.draw = function(c) {
}

// result of rotating an alignment [rot*9 + align]
aOrient = [
  0, 1, 2, 3, 4, 5, 6, 7, 8,		// NORTH (identity)
  2, 5, 8, 1, 4, 7, 0, 3, 6, 		// EAST (rot270)
  8, 7, 6, 5, 4, 3, 2, 1, 0,		// SOUTH (rot180)
  6, 3, 0, 7, 4, 1, 8, 5, 3,		// WEST (rot90)
  2, 1, 0, 5, 4, 3, 8, 7, 6,		// RNORTH (negy)
  8, 5, 2, 7, 4, 1, 6, 3, 0, 		// REAST (int-neg)
  6, 7, 8, 3, 4, 5, 0, 1, 2,		// RSOUTH (negx)
  0, 3, 6, 1, 4, 7, 2, 5, 8		// RWEST (int-pos)
];

textAlign = [
 'left', 'center', 'right',
 'left', 'center', 'right',
 'left', 'center', 'right'
];

textBaseline = [
 'top', 'top', 'top',
 'middle', 'middle', 'middle',
 'bottom', 'bottom', 'bottom'
];

Component.prototype.draw_text = function(c,text,x,y,alignment,size) {
    var a = aOrient[this.rotation*9 + alignment];
    c.textAlign = textAlign[a];
    c.textBaseline = textBaseline[a];
    c.fillStyle = this.selected ? selected_style : normal_style;
    this.sch.draw_text(c,text,
		       this.transform_x(x,y) + this.x,
		       this.transform_y(x,y) + this.y,
		       size);
}

Component.prototype.set_select = function(which) {
    if (which != this.selected) {
	this.selected = which;
	// create an undoable edit record here
    }
}
    
Component.prototype.select = function(x,y,shiftKey) {
    this.was_previously_selected = this.selected;
    if (inside(this.bbox,x,y)) {
	this.set_select(shiftKey ? !this.selected : true);
	return true;
    } else return false;
}

Component.prototype.select_rect = function(s) {
    this.was_previously_selected = this.selected;
    if (intersect(this.bbox,s))
	this.set_select(true);
}

// if connection point of component c bisects the
// wire represented by this compononent, return that
// connection point.  Otherwise return null.
Component.prototype.bisect = function(c) {
    return null;
}

Component.prototype.edit_properties = function(x,y) {
    if (inside(this.bbox,x,y)) {
	var content = document.createElement('table');
	content.style.marginBotton = '5px';
	content.fields = [];

	// add an <input> field for each property
	for (var i in this.properties) {
	    var label = document.createTextNode(i + ': ');
	    var field = document.createElement('input');
	    field.type = 'text';
	    field.value = this.properties[i];
	    field.size = 10;
	    content.fields.push([i,field]);

	    var col1 = document.createElement('td');
	    col1.appendChild(label);
	    var col2 = document.createElement('td');
	    col2.appendChild(field);
	    var row = document.createElement('tr');
	    row.appendChild(col1);
	    row.appendChild(col2);
	    row.style.verticalAlign = 'center';

	    content.appendChild(row);
	}

	var component = this;  // capture in closure below
	this.sch.dialog('Edit Properties',content,function(content) {
		var fields = content.fields;
		for (var i = fields.length - 1; i >= 0; i--)
		    component.properties[fields[i][0]] = fields[i][1].value;
		component.sch.redraw();  // component is selected, so this will redraw it
	    });
	return true;
    } else return false;
}

////////////////////////////////////////////////////////////////////////////////
//
//  Connection point
//
////////////////////////////////////////////////////////////////////////////////

connection_point_radius = 2;

function ConnectionPoint(parent,x,y) {
    this.parent = parent;
    this.offset_x = x;
    this.offset_y = y;
    this.location = '';
    this.update_location();
}

ConnectionPoint.prototype.toString = function() {
    return '<ConnectionPoint ('+this.offset_x+','+this.offset_y+') '+this.parent.toString()+'>';
}

ConnectionPoint.prototype.update_location = function() {
    // update location string which we use as a key to find coincident connection points
    var old_location = this.location;
    var parent = this.parent;
    var nx = parent.transform_x(this.offset_x,this.offset_y) + parent.x;
    var ny = parent.transform_y(this.offset_x,this.offset_y) + parent.y;
    this.x = nx;
    this.y = ny;
    this.location = nx + ',' + ny;

    // add ourselves to the connection list for the new location
    parent.sch.update_connection_point(this,old_location);
}

ConnectionPoint.prototype.coincident = function(x,y) {
    return this.x==x && this.y==y;
}

ConnectionPoint.prototype.draw = function(c,n) {
    if (n != 2)
	this.parent.draw_circle(c,this.offset_x,this.offset_y,connection_point_radius,n > 2);
}

////////////////////////////////////////////////////////////////////////////////
//
//  Wire
//
////////////////////////////////////////////////////////////////////////////////

near_distance = 2;   // how close to wire counts as "near by"

function Wire(sch,x1,y1,x2,y2) {
    // arbitrarily call x1,y1 the origin
    Component.call(this,sch,x1,y1,0);
    this.dx = x2 - x1;
    this.dy = y2 - y1;
    this.add_connection(0,0);
    this.add_connection(this.dx,this.dy);

    // compute bounding box (expanded slightly)
    var r = [0,0,this.dx,this.dy];
    canonicalize(r);
    r[0] -= near_distance;
    r[1] -= near_distance;
    r[2] += near_distance;
    r[3] += near_distance;
    this.bounding_box = r;
    this.update_coords();    // update bbox

    // used in selection calculations
    this.len = Math.sqrt(this.dx*this.dx + this.dy*this.dy);
}
Wire.prototype = new Component();
Wire.prototype.constructor = Wire;

Wire.prototype.toString = function() {
    return '<Wire ('+this.x+','+this.y+') ('+(this.x+this.dx)+','+(this.y+this.dy)+')>';
}
    
Wire.prototype.draw = function(c) {
    this.draw_line(c,0,0,this.dx,this.dy);
}

Wire.prototype.clone = function(sch,x,y) {
    return new Wire(sch,x,y,x+this.dx,y+this.dy);
}

Wire.prototype.near = function(x,y) {
    // crude check: (x,y) within expanded bounding box of wire
    if (inside(this.bbox,x,y)) {
	// compute distance between x,y and nearst point on line
	// http://www.allegro.cc/forums/thread/589720
	var D = Math.abs((x - this.x)*this.dy - (y - this.y)*this.dx)/this.len;
	if (D <= near_distance) return true;
    }
    return false;
}

Wire.prototype.select = function(x,y,shiftKey) {
    this.was_previously_selected = this.selected;
    if (this.near(x,y)) {
	this.set_select(shiftKey ? !this.selected : true);
	return true;
    } else return false;
}

// selection rectangle selects wire only if it includes
// one of the end points
Wire.prototype.select_rect = function(s) {
    this.was_previously_selected = this.selected;
    if (inside(s,this.x,this.y) || inside(s,this.x+this.dx,this.y+this.dy))
	this.set_select(true);
}

// if connection point of component c bisects the
// wire represented by this compononent, return that
// connection point.  Otherwise return null.
Wire.prototype.bisect = function(c) {
    for (var i = c.connections.length - 1; i >= 0; --i) {
	var cp = c.connections[i];
	var x = cp.x;
	var y = cp.y;

	// crude check: (x,y) within expanded bounding box of wire
	if (inside(this.bbox,x,y)) {
	    // compute distance between x,y and nearst point on line
	    // http://www.allegro.cc/forums/thread/589720
	    var D = Math.abs((x - this.x)*this.dy - (y - this.y)*this.dx)/this.len;
	    // final check: ensure point isn't an end point of the wire
	    if (D < 1 && !this.connections[0].coincident(x,y) && !this.connections[1].coincident(x,y))
		return cp;
	}
    }
    return null;
}

Wire.prototype.move_end = function() {
    this.sch.check_wires(this);
}

////////////////////////////////////////////////////////////////////////////////
//
//  Ground
//
////////////////////////////////////////////////////////////////////////////////

function Ground(sch,x,y,rotation) {
    Component.call(this,sch,x,y,rotation);
    this.add_connection(0,0);
    this.bounding_box = [-6,0,6,8];
    this.update_coords();
}
Ground.prototype = new Component();
Ground.prototype.constructor = Ground;

Ground.prototype.toString = function() {
    return '<Ground ('+this.x+','+this.y+')>';
}
    
Ground.prototype.draw = function(c) {
    this.draw_line(c,0,0,0,8);
    this.draw_line(c,-6,8,6,8);
}

Ground.prototype.clone = function(sch,x,y) {
    return new Ground(sch,x,y,this.rotation);
}

////////////////////////////////////////////////////////////////////////////////
//
//  Resistor
//
////////////////////////////////////////////////////////////////////////////////

function Resistor(sch,x,y,rotation,name,r) {
    Component.call(this,sch,x,y,rotation);
    this.properties['name'] = name;
    this.properties['r'] = r ? r : '1';
    this.add_connection(0,0);
    this.add_connection(0,48);
    this.bounding_box = [-4,0,4,48];
    this.update_coords();
}
Resistor.prototype = new Component();
Resistor.prototype.constructor = Resistor;

Resistor.prototype.toString = function() {
    return '<Resistor '+this.properties['r']+' ('+this.x+','+this.y+')>';
}
    
Resistor.prototype.draw = function(c) {
    this.draw_line(c,0,0,0,12);
    this.draw_line(c,0,12,4,14);
    this.draw_line(c,4,14,-4,18);
    this.draw_line(c,-4,18,4,22);
    this.draw_line(c,4,22,-4,26);
    this.draw_line(c,-4,26,4,30);
    this.draw_line(c,4,30,-4,34);
    this.draw_line(c,-4,34,0,36);
    this.draw_line(c,0,36,0,48);
    if (this.properties['r'])
	this.draw_text(c,this.properties['r']+'\u03A9',5,24,3,property_size);
    if (this.properties['name'])
	this.draw_text(c,this.properties['name'],-5,24,5,property_size);
}

Resistor.prototype.clone = function(sch,x,y) {
    return new Resistor(sch,x,y,this.rotation,'',this.properties['r']);
}

////////////////////////////////////////////////////////////////////////////////
//
//  Capacitor
//
////////////////////////////////////////////////////////////////////////////////

function Capacitor(sch,x,y,rotation,name,c) {
    Component.call(this,sch,x,y,rotation);
    this.properties['name'] = name;
    this.properties['c'] = c ? c : '1p';
    this.add_connection(0,0);
    this.add_connection(0,48);
    this.bounding_box = [-8,0,8,48];
    this.update_coords();
}
Capacitor.prototype = new Component();
Capacitor.prototype.constructor = Capacitor;

Capacitor.prototype.toString = function() {
    return '<Capacitor '+this.properties['r']+' ('+this.x+','+this.y+')>';
}
    
Capacitor.prototype.draw = function(c) {
    this.draw_line(c,0,0,0,22);
    this.draw_line(c,-8,22,8,22);
    this.draw_line(c,-8,26,8,26);
    this.draw_line(c,0,26,0,48);
    if (this.properties['c'])
	this.draw_text(c,this.properties['c']+'F',9,24,3,property_size);
    if (this.properties['name'])
	this.draw_text(c,this.properties['name'],-9,24,5,property_size);
}

Capacitor.prototype.clone = function(sch,x,y) {
    return new Capacitor(sch,x,y,this.rotation,'',this.properties['c']);
}

////////////////////////////////////////////////////////////////////////////////
//
//  Inductor
//
////////////////////////////////////////////////////////////////////////////////

function Inductor(sch,x,y,rotation,name,l) {
    Component.call(this,sch,x,y,rotation);
    this.properties['name'] = name;
    this.properties['l'] = l ? l : '1n';
    this.add_connection(0,0);
    this.add_connection(0,48);
    this.bounding_box = [-4,0,5,48];
    this.update_coords();
}
Inductor.prototype = new Component();
Inductor.prototype.constructor = Inductor;

Inductor.prototype.toString = function() {
    return '<Inductor '+this.properties['l']+' ('+this.x+','+this.y+')>';
}
    
Inductor.prototype.draw = function(c) {
    this.draw_line(c,0,0,0,14);
    this.draw_arc(c,0,18,4,6*Math.PI/4,3*Math.PI/4);
    this.draw_arc(c,0,24,4,5*Math.PI/4,3*Math.PI/4);
    this.draw_arc(c,0,30,4,5*Math.PI/4,2*Math.PI/4);
    this.draw_line(c,0,34,0,48);

    if (this.properties['l'])
	this.draw_text(c,this.properties['l']+'H',6,24,3,property_size);
    if (this.properties['name'])
	this.draw_text(c,this.properties['name'],-3,24,5,property_size);
}

Inductor.prototype.clone = function(sch,x,y) {
    return new Inductor(sch,x,y,this.rotation,'',this.properties['l']);
}

////////////////////////////////////////////////////////////////////////////////
//
//  Source
//
////////////////////////////////////////////////////////////////////////////////

function Source(sch,x,y,rotation,name,type,value) {
    Component.call(this,sch,x,y,rotation);
    this.type = type;
    this.properties['name'] = name;
    this.properties['value'] = value ? value : '1';
    this.add_connection(0,0);
    this.add_connection(0,48);
    this.bounding_box = [-12,0,12,48];
    this.update_coords();
}
Source.prototype = new Component();
Source.prototype.constructor = Source;

Source.prototype.toString = function() {
    return '<'+this.type+'source '+this.properties['params']+' ('+this.x+','+this.y+')>';
}
    
Source.prototype.draw = function(c) {
    this.draw_line(c,0,0,0,12);
    this.draw_circle(c,0,24,12,false);
    this.draw_line(c,0,36,0,48);

    if (this.type == 'v') {  // voltage source
	// draw + and -
	this.draw_line(c,8,5,8,11);
	this.draw_line(c,5,8,11,8);
	this.draw_line(c,5,40,11,40);
	// draw V
	this.draw_line(c,-3,20,0,28);
	this.draw_line(c,3,20,0,28);
    } else if (this.type == 'i') {  // current source
	// draw arrow: pos to neg
	this.draw_line(c,0,16,0,32);
	this.draw_line(c,-3,24,0,32);
	this.draw_line(c,3,24,0,32);
    }

    if (this.properties['name'])
	this.draw_text(c,this.properties['name'],-13,24,5,property_size);
    if (this.properties['value'])
	this.draw_text(c,this.properties['value']+(this.type=='v'?'V':'A'),13,24,3,property_size);
}

Source.prototype.clone = function(sch,x,y) {
    return new Source(sch,x,y,this.rotation,'',this.type,this.properties['value']);
}

function VSource(sch,x,y,rotation,name,value) {
    Source.call(this,sch,x,y,rotation,name,'v',value);

}
VSource.prototype = new Component();
VSource.prototype.constructor = VSource;
VSource.prototype.toString = Source.prototype.toString;
VSource.prototype.draw = Source.prototype.draw;
VSource.prototype.clone = Source.prototype.clone;

function ISource(sch,x,y,rotation,name,value) {
    Source.call(this,sch,x,y,rotation,name,'i',value);

}
ISource.prototype = new Component();
ISource.prototype.constructor = ISource;
ISource.prototype.toString = Source.prototype.toString;
ISource.prototype.draw = Source.prototype.draw;
ISource.prototype.clone = Source.prototype.clone;
