/////////////////////////////////////////////////////////////////////////////
//
//  Simple schematic capture
//
////////////////////////////////////////////////////////////////////////////////

// Copyright (C) 2011 Massachusetts Institute of Technology

// add schematics to a document with 
//
//   <input type="hidden" class="schematic" name="unique_form_id" value="JSON netlist..." .../>
//
// other attributes you can add to the input tag:
//   width -- width in pixels of diagram
//   height -- height in pixels of diagram
//   parts -- comma-separated list of parts for parts bin (see parts_map),
//            parts="" disables editing of diagram

// JSON schematic representation:
//  sch :=  [part, part, ...]
//  part := [type, coords, properties, connections]
//  type := string (see parts_map)
//  coords := [number, ...]  // (x,y,rot) or (x1,y1,x2,y2)
//  properties := {name: value, ...}
//  connections := [node, ...]   // one per connection point in canoncial order
//  node := string
// need a netlist? just use the part's type, properites and connections

// TO DO:
// - wire labels?
// - zoom/scroll canvas
// - rotate multiple objects around their center of mass
// - rubber band wires when moving components

// set up each schematic entry widget
function update_schematics() {
    // set up each schematic on the page
    var schematics = document.getElementsByClassName('schematic');
    for (var i = 0; i < schematics.length; ++i)
	if (schematics[i].getAttribute("loaded") != "true") {
	    try {
		new schematic.Schematic(schematics[i]);
	    } catch (err) {
		var msgdiv = document.createElement('div');
		msgdiv.style.border = 'thick solid #FF0000';
		msgdiv.style.margins = '20px';
		msgdiv.style.padding = '20px';
		var msg = document.createTextNode('Sorry, there a browser error in starting the schematic tool.  The tool is known to be compatible with the latest versions of Firefox and Chrome, which we recommend you use.');
		msgdiv.appendChild(msg);
		schematics[i].parentNode.insertBefore(msgdiv,schematics[i]);
	    }
	    schematics[i].setAttribute("loaded","true");
	}
}

// add ourselves to the tasks that get performed when window is loaded
function add_schematic_handler(other_onload) {
    return function() {
	// execute othe onload functions first
	if (other_onload) other_onload();

	update_schematics();
    }
}
window.onload = add_schematic_handler(window.onload);

// ask each schematic input widget to update its value field for submission
function prepare_schematics() {
    var schematics = document.getElementsByClassName('schematic');
    for (var i = schematics.length - 1; i >= 0; i--)
	schematics[i].schematic.update_value();
}

schematic = (function() {
	background_style = 'rgb(220,220,220)';
	element_style = 'rgb(255,255,255)';
	thumb_style = 'rgb(128,128,128)';
	normal_style = 'rgb(0,0,0)';  // default drawing color
	component_style = 'rgb(64,64,255)';  // color for unselected components
	selected_style = 'rgb(64,255,64)';  // highlight color for selected components
	grid_style = "rgb(128,128,128)";
	annotation_style = 'rgb(255,64,64)';  // color for diagram annotations

	property_size = 5;  // point size for Component property text
	annotation_size = 6;  // point size for diagram annotations

	// list of all the defined parts
	parts_map = {
	    'g': [Ground, 'Ground connection'],
	    'L': [Label, 'Node label'],
	    'v': [VSource, 'Voltage source'],
	    'i': [ISource, 'Current source'],
	    'r': [Resistor, 'Resistor'],
	    'c': [Capacitor, 'Capacitor'],
	    'l': [Inductor, 'Inductor'],
	    'o': [OpAmp, 'Op Amp'],
	    'd': [Diode, 'Diode'],
	    'n': [NFet, 'NFet'],
	    'p': [PFet, 'PFet'],
	    's': [Probe, 'Voltage Probe'],
	    'a': [Ammeter, 'Current Probe'],
	};

	// global clipboard
	if (typeof sch_clipboard == 'undefined')
	    sch_clipboard = [];

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Schematic = diagram + parts bin + status area
	//
	////////////////////////////////////////////////////////////////////////////////

	// setup a schematic by populating the <div> with the appropriate children
	function Schematic(input) {
	    // set up diagram viewing parameters
	    this.show_grid = true;
	    this.grid = 8;
	    this.scale = 2;
	    this.origin_x = input.getAttribute("origin_x");
	    if (this.origin_x == undefined) this.origin_x = 0;
	    this.origin_y = input.getAttribute("origin_y");
	    if (this.origin_y == undefined) this.origin_y = 0;
	    this.cursor_x = 0;
	    this.cursor_y = 0;

	    this.window_list = [];  // list of pop-up windows in increasing z order

	    // use user-supplied list of parts if supplied
	    // else just populate parts bin with all the parts
	    this.edits_allowed = true;
	    var parts = input.getAttribute('parts');
	    if (parts == undefined || parts == 'None') {
		parts = new Array();
		for (var p in parts_map) parts.push(p);
	    } else if (parts == '') {
		this.edits_allowed = false;
		parts = [];
	    } else parts = parts.split(',');

	    // now add the parts to the parts bin
	    this.parts_bin = [];
	    for (var i = 0; i < parts.length; i++) {
		var part = new Part(this);
		var pm = parts_map[parts[i]];
		part.set_component(new pm[0](0,0,0),pm[1]);
		this.parts_bin.push(part);
	    }

	    // use user-supplied list of analyses, otherwise provide them all
	    // analyses="" means no analyses
	    var analyses = input.getAttribute('analyses');
	    if (analyses == undefined || analyses == 'None')
		analyses = ['dc','ac','tran'];
	    else if (analyses == '') analyses = [];
	    else analyses = analyses.split(',');

	    if (parts.length == 0 && analyses.length == 0) this.diagram_only = true;
	    else this.diagram_only = false;

	    // see what we need to submit.  Expecting attribute of the form
	    // submit_analyses="{'tran':[[node_name,t1,t2,t3],...],
	    //                   'ac':[[node_name,f1,f2,...],...]}"
	    var submit = input.getAttribute('submit_analyses');
	    if (submit && submit.indexOf('{') != -1)
		this.submit_analyses = JSON.parse(submit);
	    else
		this.submit_analyses = undefined;

	    // toolbar
	    this.tools = new Array();
	    this.toolbar = [];

	    if (!this.diagram_only) {
		this.tools['help'] = this.add_tool(help_icon,'Help: display help page',this.help);
		this.enable_tool('help',true);
		this.toolbar.push(null);  // spacer
	    }

	    if (this.edits_allowed) {
		this.tools['grid'] = this.add_tool(grid_icon,'Grid: toggle grid display',this.toggle_grid);
		this.enable_tool('grid',true);
		this.tools['cut'] = this.add_tool(cut_icon,'Cut: move selected components from diagram to the clipboard',this.cut);
		this.tools['copy'] = this.add_tool(copy_icon,'Copy: copy selected components into the clipboard',this.copy);
		this.tools['paste'] = this.add_tool(paste_icon,'Paste: copy clipboard into the diagram',this.paste);
		this.toolbar.push(null);  // spacer
	    }

	    // simulation interface if cktsim.js is loaded
	    if (typeof cktsim != 'undefined') {
		if (analyses.indexOf('dc') != -1) {
		    this.tools['dc'] = this.add_tool('DC','DC Analysis',this.dc_analysis);
		    this.enable_tool('dc',true);
		    this.dc_max_iters = '1000';  // default values dc solution
		}

		if (analyses.indexOf('ac') != -1) {
		    this.tools['ac'] = this.add_tool('AC','AC Small-Signal Analysis',this.setup_ac_analysis);
		    this.enable_tool('ac',true);
		    this.ac_npts = '50'; // default values for AC Analysis
		    this.ac_fstart = '10';
		    this.ac_fstop = '1G';
		    this.ac_source_name = undefined;
		}

		if (analyses.indexOf('tran') != -1) {
		    this.tools['tran'] = this.add_tool('TRAN','Transient Analysis',this.transient_analysis);
		    this.enable_tool('tran',true);
		    this.tran_npts = '100';  // default values for transient analysis
		    this.tran_tstop = '1';
		}
	    }
 
	    // set up diagram canvas
	    this.canvas = document.createElement('canvas');
	    this.width = input.getAttribute('width');
	    this.width = parseInt(this.width == undefined ? '400' : this.width);
	    this.canvas.width = this.width;
	    this.height = input.getAttribute('height');
	    this.height = parseInt(this.height == undefined ? '300' : this.height);
	    this.canvas.height = this.height;

	    this.sctl_r = 16;   // scrolling control parameters
	    this.sctl_x = this.sctl_r + 8;   // upper left
	    this.sctl_y = this.sctl_r + 8;
	    this.zctl_left = this.sctl_x - 8;
	    this.zctl_top = this.sctl_y + this.sctl_r + 8;

	    // repaint simply draws this buffer and then adds selected elements on top
	    this.bg_image = document.createElement('canvas');
	    this.bg_image.width = this.width;
	    this.bg_image.height = this.height;

	    if (!this.diagram_only) {
		this.canvas.tabIndex = 1; // so we get keystrokes
		this.canvas.style.borderStyle = 'solid';
		this.canvas.style.borderWidth = '1px';
		this.canvas.style.borderColor = grid_style;
		this.canvas.style.outline = 'none';
	    }

	    this.canvas.schematic = this;
	    if (this.edits_allowed) {
		this.canvas.addEventListener('mousemove',schematic_mouse_move,false);
		this.canvas.addEventListener('mouseover',schematic_mouse_enter,false);
		this.canvas.addEventListener('mouseout',schematic_mouse_leave,false);
		this.canvas.addEventListener('mousedown',schematic_mouse_down,false);
		this.canvas.addEventListener('mouseup',schematic_mouse_up,false);
		this.canvas.addEventListener('mousewheel',schematic_mouse_wheel,false);
		this.canvas.addEventListener('DOMMouseScroll',schematic_mouse_wheel,false);  // for FF
		this.canvas.addEventListener('dblclick',schematic_double_click,false);
		this.canvas.addEventListener('keydown',schematic_key_down,false);
		this.canvas.addEventListener('keyup',schematic_key_up,false);
	    }

	    // set up message area
	    if (!this.diagram_only) {
		this.status_div = document.createElement('div');
		this.status = document.createTextNode('');
		this.status_div.appendChild(this.status);
		this.status_div.style.height = status_height + 'px';
	    } else this.status_div = undefined;

	    this.connection_points = new Array();  // location string => list of cp's
	    this.components = [];

	    this.dragging = false;
	    this.select_rect = undefined;
	    this.wire = undefined;

	    this.operating_point = undefined;  // result from DC analysis
	    this.dc_results = undefined;   // saved analysis results for submission
	    this.ac_results = undefined;   // saved analysis results for submission
	    this.transient_results = undefined;   // saved analysis results for submission

	    // state of modifier keys
	    this.ctrlKey = false;
	    this.shiftKey = false;
	    this.altKey = false;
	    this.cmdKey = false;

	    // make sure other code can find us!
	    input.schematic = this;
	    this.input = input;

	    // set up DOM -- use nested tables to do the layout
	    var table,tr,td;
	    table = document.createElement('table');
	    table.rules = 'none';
	    if (!this.diagram_only) {
		table.frame = 'box';
		table.style.borderStyle = 'solid';
		table.style.borderWidth = '2px';
		table.style.borderColor = normal_style;
		table.style.backgroundColor = background_style;
	    }

	    // add tools to DOM
	    if (this.toolbar.length > 0) {
		tr = document.createElement('tr');
		table.appendChild(tr);
		td = document.createElement('td');
		td.style.verticalAlign = 'top';
		td.colSpan = 2;
		tr.appendChild(td);
		for (var i = 0; i < this.toolbar.length; ++i) {
		    var tool = this.toolbar[i];
		    if (tool != null) td.appendChild(tool);
		}
	    }
	    
	    // add canvas and parts bin to DOM
	    tr = document.createElement('tr');
	    table.appendChild(tr);

	    td = document.createElement('td');
	    tr.appendChild(td);
	    var wrapper = document.createElement('div'); // for inserting pop-up windows
	    td.appendChild(wrapper);
	    wrapper.style.position = 'relative';  // so we can position subwindows
	    wrapper.appendChild(this.canvas);

	    td = document.createElement('td');
	    td.style.verticalAlign = 'top';
	    tr.appendChild(td);
	    var parts_table = document.createElement('table');
	    td.appendChild(parts_table);
	    parts_table.rules = 'none';
	    parts_table.frame = 'void';
	    parts_table.cellPadding = '0';
	    parts_table.cellSpacing = '0';

	    // fill in parts_table
	    var parts_per_column = Math.floor(this.height / (part_h + 5));  // mysterious extra padding
	    for (var i = 0; i < parts_per_column; ++i) {
		tr = document.createElement('tr');
		parts_table.appendChild(tr);
		for (var j = i; j < this.parts_bin.length; j += parts_per_column) {
		    td = document.createElement('td');
		    tr.appendChild(td);
		    td.appendChild(this.parts_bin[j].canvas);
		}
	    }

	    if (this.status_div != undefined) {
		tr = document.createElement('tr');
		table.appendChild(tr);
		td = document.createElement('td');
		tr.appendChild(td);
		td.colSpan = 2;
		td.appendChild(this.status_div);
	    }

	    // add to dom
	    // avoid Chrome bug that changes to text cursor whenever
	    // drag starts.  Just do this in schematic tool...
	    var toplevel = document.createElement('div');
	    toplevel.onselectstart = function(){ return false; };
	    toplevel.appendChild(table);
	    this.input.parentNode.insertBefore(toplevel,this.input.nextSibling);

	    // process initial contents of diagram
	    this.load_schematic(this.input.getAttribute('value'),
				this.input.getAttribute('initial_value'));

	    // start by centering diagram on the screen
	    this.zoomall();
	}

	part_w = 42;   // size of a parts bin compartment
	part_h = 42;
	status_height = 18;

	Schematic.prototype.add_component = function(new_c) {
	    this.components.push(new_c);

	    // create undoable edit record here
	}

	Schematic.prototype.remove_component = function(c) {
	    var index = this.components.indexOf(c);
	    if (index != -1) this.components.splice(index,1);
	}

	Schematic.prototype.find_connections = function(cp) {
	    return this.connection_points[cp.location];
	}

	// add connection point to list of connection points at that location
	Schematic.prototype.add_connection_point = function(cp) {
	    var cplist = this.connection_points[cp.location];
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
	    var new_wire = new Wire(x1,y1,x2,y2);
	    new_wire.add(this);
	    new_wire.move_end();
	    return new_wire;
	}

	Schematic.prototype.split_wire = function(w,cp) {
	    // remove bisected wire
	    w.remove();

	    // add two new wires with connection point cp in the middle
	    this.add_wire(w.x,w.y,cp.x,cp.y);
	    this.add_wire(w.x+w.dx,w.y+w.dy,cp.x,cp.y);
	}

	// see if connection points of component c split any wires
	Schematic.prototype.check_wires = function(c) {
	    for (var i = 0; i < this.components.length; i++) {
		var cc = this.components[i];
		if (cc != c) {  // don't check a component against itself
		    // only wires will return non-null from a bisect call
		    var cp = cc.bisect(c);
		    if (cp) {
			// cc is a wire bisected by connection point cp
			this.split_wire(cc,cp);
			this.redraw_background();
		    }
		}
	    }
	}

	// see if there are any existing connection points that bisect wire w
	Schematic.prototype.check_connection_points = function(w) {
	    for (var locn in this.connection_points) {
		var cplist = this.connection_points[locn];
		if (cplist && w.bisect_cp(cplist[0])) {
		    this.split_wire(w,cplist[0]);
		    this.redraw_background();

		    // stop here, new wires introduced by split will do their own checks
		    return;
		}
	    }
	}

	// merge collinear wires sharing an end point
	Schematic.prototype.clean_up_wires = function() {
	    for (var locn in this.connection_points) {
		var cplist = this.connection_points[locn];
		if (cplist && cplist.length == 2) {
		    // found a connection with just two connections, see if they're wires
		    var c1 = cplist[0].parent;
		    var c2 = cplist[1].parent;
		    if (c1.type == 'w' && c2.type == 'w') {
			var e1 = c1.other_end(cplist[0]);
			var e2 = c2.other_end(cplist[1]);
			var e3 = cplist[0];  // point shared by the two wires
			if (collinear(e1,e2,e3)) {
			    c1.remove();
			    c2.remove();
			    this.add_wire(e1.x,e1.y,e2.x,e2.y);
			}
		    }
		}
	    }
	}

	Schematic.prototype.unselect_all = function(which) {
	    this.operating_point = undefined;  // remove annotations

	    for (var i = this.components.length - 1; i >= 0; --i)
		if (i != which) this.components[i].set_select(false);
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

	    this.clean_up_wires();
	    this.redraw_background();
	}

	Schematic.prototype.help = function() {
	    window.open('/static/handouts/schematic_tutorial.pdf');
	}

	// zoom diagram around given coords
	Schematic.prototype.rescale = function(nscale,cx,cy) {
	    if (cx == undefined) {
		// use current center point if no point has been specified
		cx = this.origin_x + this.width/(2*this.scale);
		cy = this.origin_y + this.height/(2*this.scale);
	    }

	    this.origin_x += cx*(this.scale - nscale);
	    this.origin_y += cy*(this.scale - nscale);
	    this.scale = nscale;


	    //this.origin_x = cx - this.width/(2*this.scale);
	    //this.origin_y = cy - this.height/(2*this.scale);

	    this.redraw_background();
	}

	Schematic.prototype.toggle_grid = function() {
	    this.show_grid = !this.show_grid;
	    this.redraw_background();
	}

	zoom_factor = 1.25;    // scaling is some power of zoom_factor
	zoom_min = 0.5;
	zoom_max = 4.0;
	origin_min = -200;    // in grids
	origin_max = 200;

	Schematic.prototype.zoomin = function() {
	    var nscale = this.scale * zoom_factor;

	    if (nscale < zoom_max) {
		// keep center of view unchanged
		this.origin_x += (this.width/2)*(1.0/this.scale - 1.0/nscale);
		this.origin_y += (this.height/2)*(1.0/this.scale - 1.0/nscale);
		this.scale = nscale;
		this.redraw_background();
	    }
	}

	Schematic.prototype.zoomout = function() {
	    var nscale = this.scale / zoom_factor;

	    if (nscale > zoom_min) {
		// keep center of view unchanged
		this.origin_x += (this.width/2)*(1.0/this.scale - 1.0/nscale);
		this.origin_y += (this.height/2)*(1.0/this.scale - 1.0/nscale);
		this.scale = nscale;
		this.redraw_background();
	    }
	}

	Schematic.prototype.zoomall = function() {
	    // w,h for schematic including a 25% margin on all sides
	    var sch_w = 1.5*(this.bbox[2] - this.bbox[0]);
	    var sch_h = 1.5*(this.bbox[3] - this.bbox[1]);

	    if (sch_w == 0 && sch_h == 0) {
		this.origin_x = 0;
		this.origin_y = 0;
		this.scale = 2;
	    } else {
		// compute scales that would make schematic fit, choose smallest
		var scale_x = this.width/sch_w;
		var scale_y = this.height/sch_h;
		this.scale = Math.pow(zoom_factor,Math.ceil(Math.log(Math.min(scale_x,scale_y))/Math.log(zoom_factor)));
		if (this.scale < zoom_min) this.scale = zoom_min;
		else if (this.scale > zoom_max) this.scale = zoom_max;

		// center the schematic
		this.origin_x = (this.bbox[2] + this.bbox[0])/2 - this.width/(2*this.scale);
		this.origin_y = (this.bbox[3] + this.bbox[1])/2 - this.height/(2*this.scale);
	    }

	    this.redraw_background();
	}

	Schematic.prototype.cut = function() {
	    // clear previous contents
	    sch_clipboard = [];

	    // look for selected components, move them to clipboard.
	    for (var i = this.components.length - 1; i >=0; --i) {
		var c = this.components[i];
		if (c.selected) {
		    c.remove();
		    sch_clipboard.push(c);
		}
	    }

	    // update diagram view
	    this.redraw();
	}

	Schematic.prototype.copy = function() {
	    // clear previous contents
	    sch_clipboard = [];

	    // look for selected components, copy them to clipboard.
	    for (var i = this.components.length - 1; i >=0; --i) {
		var c = this.components[i];
		if (c.selected)
		    sch_clipboard.push(c.clone(c.x,c.y));
	    }
	}

	Schematic.prototype.paste = function() {
	    // compute left,top of bounding box for origins of
	    // components in the clipboard
	    var left = undefined;
	    var top = undefined;
	    for (var i = sch_clipboard.length - 1; i >= 0; --i) {
		var c = sch_clipboard[i];
		left = left ? Math.min(left,c.x) : c.x;
		top = top ? Math.min(top,c.y) : c.y;
	    }

	    this.message('cursor '+this.cursor_x+','+this.cursor_y);

	    // clear current selections
	    this.unselect_all(-1);
	    this.redraw_background();  // so we see any components that got unselected

	    // make clones of components on the clipboard, positioning
	    // them relative to the cursor
	    for (var i = sch_clipboard.length - 1; i >= 0; --i) {
		var c = sch_clipboard[i];
		var new_c = c.clone(this.cursor_x + (c.x - left),this.cursor_y + (c.y - top));
		new_c.set_select(true);
		new_c.add(this);
	    }

	    // see what we've wrought
	    this.redraw();
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Netlist and Simulation interface
	//
	////////////////////////////////////////////////////////////////////////////////

	// load diagram from JSON representation
	Schematic.prototype.load_schematic = function(value,initial_value) {
	    // use default value if no schematic info in value
	    if (value == undefined || value.indexOf('[') == -1)
		value = initial_value;
	    
	    if (value && value.indexOf('[') != -1) {
		// convert string value into data structure
		var json = JSON.parse(value);

		// top level is a list of components
		for (var i = json.length - 1; i >= 0; --i) {
		    var c = json[i];
		    if (c[0] == 'view') {
			// special hack: view component lets us recreate view
			// ignore saved view parameters as they sometimes screw students
			//this.origin_x = c[1];
			//this.origin_y = c[2];
			//this.scale = c[3];
			//this.ac_npts = c[4];
			this.ac_fstart = c[5];
			this.ac_fstop = c[6];
			this.ac_source_name = c[7];
			this.tran_npts = c[8];
			this.tran_tstop = c[9];
			this.dc_max_iters = c[10];
		    } else if (c[0] == 'w') {
			// wire
			this.add_wire(c[1][0],c[1][1],c[1][2],c[1][3]);
		    } else if (c[0] == 'dc') {
			this.dc_results = c[1];
		    } else if (c[0] == 'transient') {
			this.transient_results = c[1];
		    } else if (c[0] == 'ac') {
			this.ac_results = c[1];
		    } else {
			// ordinary component
			//  c := [type, coords, properties, connections]
			var type = c[0];
			var coords = c[1];
			var properties = c[2];

			// make the part
			var part = new parts_map[type][0](coords[0],coords[1],coords[2]);

			// give it its properties
			for (var name in properties)
			    part.properties[name] = properties[name];

			// add component to the diagram
			part.add(this);
		    }
		}
	    }

	    // see what we've got!
	    this.redraw_background();
	}

	// label all the nodes in the circuit
	Schematic.prototype.label_connection_points = function() {
	    // start by clearing all the connection point labels
	    for (var i = this.components.length - 1; i >=0; --i)
		this.components[i].clear_labels();

	    // components are in charge of labeling their unlabeled connections.
	    // labels given to connection points will propagate to coincident connection
	    // points and across Wires.

	    // let special components like GND label their connection(s)
	    for (var i = this.components.length - 1; i >=0; --i)
		this.components[i].add_default_labels();

	    // now have components generate labels for unlabeled connections
	    this.next_label = 0;
	    for (var i = this.components.length - 1; i >=0; --i)
		this.components[i].label_connections();
	}

	// generate a new label
	Schematic.prototype.get_next_label = function() {
	    // generate next label in sequence
	    this.next_label += 1;
	    return this.next_label.toString();
	}

	// propagate label to coincident connection points
	Schematic.prototype.propagate_label = function(label,location) {
	    var cplist = this.connection_points[location];
	    for (var i = cplist.length - 1; i >= 0; --i)
		cplist[i].propagate_label(label);
	}

	// update the value field of our corresponding input field with JSON
	// representation of schematic
	Schematic.prototype.update_value = function() {
	    // label connection points
	    this.label_connection_points();

	    // build JSON data structure, convert to string value for
	    // input field
	    this.input.value = JSON.stringify(this.json_with_analyses());
	}

	// produce a JSON representation of the diagram
	Schematic.prototype.json = function() {
	    var json = [];

	    // output all the components/wires in the diagram
	    var n = this.components.length;
	    for (var i = 0; i < n; i++)
		json.push(this.components[i].json(i));

	    // capture the current view parameters
	    json.push(['view',this.origin_x,this.origin_y,this.scale,
		       this.ac_npts,this.ac_fstart,this.ac_fstop,
		       this.ac_source_name,this.tran_npts,this.tran_tstop,
		       this.dc_max_iters]);

	    return json;
	}

	// produce a JSON representation of the diagram
	Schematic.prototype.json_with_analyses = function() {
	    var json = this.json();

	    if (this.dc_results != undefined) json.push(['dc',this.dc_results]);
	    if (this.ac_results != undefined) json.push(['ac',this.ac_results]);
	    if (this.transient_results != undefined) json.push(['transient',this.transient_results]);

	    return json;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Simulation interface
	//
	////////////////////////////////////////////////////////////////////////////////

	Schematic.prototype.extract_circuit = function() {
	    // give all the circuit nodes a name, extract netlist
	    this.label_connection_points();
	    var netlist = this.json();

	    // since we've done the heavy lifting, update input field value
	    // so user can grab diagram if they want
	    this.input.value = JSON.stringify(netlist);

	    // create a circuit from the netlist
	    var ckt = new cktsim.Circuit();
	    if (ckt.load_netlist(netlist))
		return ckt;
	    else
		return null;
	}

	Schematic.prototype.dc_analysis = function() {
	    // remove any previous annotations
	    this.unselect_all(-1);
	    this.redraw_background();

	    var ckt = this.extract_circuit();
	    if (ckt === null) return;

	    // run the analysis
	    this.operating_point = ckt.dc();

	    if (this.operating_point != undefined) {
		// save a copy of the results for submission
		this.dc_results = {};
		for (var i in this.operating_point) this.dc_results[i] = this.operating_point[i];

		// display results on diagram
		this.redraw();
	    }
	}

	// return a list of [color,node_label,offset,type] for each probe in the diagram
	// type == 'voltage' or 'current'
	Schematic.prototype.find_probes = function() {
	    var result = [];
	    var result = [];
	    for (var i = this.components.length - 1; i >= 0; --i) {
		var c = this.components[i];
		var info = c.probe_info();
		if (info != undefined) result.push(c.probe_info());
	    }
	    return result;
	}

	// use a dialog to get AC analysis parameters
	Schematic.prototype.setup_ac_analysis = function() {
	    this.unselect_all(-1);
	    this.redraw_background();

	    var npts_lbl = 'Number of points/decade';
	    var fstart_lbl = 'Starting frequency (Hz)';
	    var fstop_lbl = 'Ending frequency (Hz)';
	    var source_name_lbl = 'Name of V or I source for ac'
    
	    if (this.find_probes().length == 0) {
		alert("AC Analysis: there are no voltage probes in the diagram!");
		return;
	    }

	    var fields = new Array();
	    //fields[npts_lbl] = build_input('text',10,this.ac_npts);
	    fields[fstart_lbl] = build_input('text',10,this.ac_fstart);
	    fields[fstop_lbl] = build_input('text',10,this.ac_fstop);
	    fields[source_name_lbl] = build_input('text',10,this.ac_source_name);

	    var content = build_table(fields);
	    content.fields = fields;
	    content.sch = this;

	    this.dialog('AC Analysis',content,function(content) {
		    var sch = content.sch;

		    // retrieve parameters, remember for next time
		    //sch.ac_npts = content.fields[npts_lbl].value;
		    sch.ac_fstart = content.fields[fstart_lbl].value;
		    sch.ac_fstop = content.fields[fstop_lbl].value;
		    sch.ac_source_name = content.fields[source_name_lbl].value;

		    sch.ac_analysis(cktsim.parse_number(sch.ac_npts),
				    cktsim.parse_number(sch.ac_fstart),
				    cktsim.parse_number(sch.ac_fstop),
				    sch.ac_source_name);
		});
	}

	// perform ac analysis
	Schematic.prototype.ac_analysis = function(npts,fstart,fstop,ac_source_name) {
	    // run the analysis
	    var ckt = this.extract_circuit();
	    if (ckt === null) return;
	    var results = ckt.ac(npts,fstart,fstop,ac_source_name);

	    if (typeof results == 'string') 
		this.message(results);
	    else {
		var x_values = results['_frequencies_'];

		// x axis will be a log scale
		for (var i = x_values.length - 1; i >= 0; --i)
		    x_values[i] = Math.log(x_values[i])/Math.LN10;


		if (this.submit_analyses != undefined) {
		    var submit = this.submit_analyses['ac'];
		    if (submit != undefined) {
			// save a copy of the results for submission
			this.ac_results = {};

			// save requested values for each requested node
			for (var j = 0; j < submit.length; j++) {
			    var flist = submit[j];    // [node_name,f1,f2,...]
			    var node = flist[0];
			    var values = results[node];
			    var fvlist = [];
			    // for each requested freq, interpolate response value
			    for (var k = 1; k < flist.length; k++) {
				var f = flist[k];
				var v = interpolate(f,x_values,values);
				// convert to dB
				fvlist.push([f,v == undefined ? 'undefined' : 20.0 * Math.log(v)/Math.LN10]);
			    }
			    // save results as list of [f,response] paris
			    this.ac_results[node] = fvlist;
			}
		    }
		}

		// set up plot values for each node with a probe
		var y_values = [];  // list of [color, result_array]
		var z_values = [];  // list of [color, result_array]
		var probes = this.find_probes();

		var probe_maxv = [];
		var probe_color = [];

		// Check for probe with near zero transfer function and warn
		for (var i = probes.length - 1; i >= 0; --i) {
		    if (probes[i][3] != 'voltage') continue;
		    probe_color[i] = probes[i][0];
		    var label = probes[i][1];
		    var v = results[label];
		    probe_maxv[i] = array_max(v); // magnitudes always > 0
		}
		var all_max = array_max(probe_maxv);

		if (all_max < 1.0e-16) {
		    alert('Zero ac response, -infinity on DB scale.');
		} else {
		    for (var i = probes.length - 1; i >= 0; --i) {
			if (probes[i][3] != 'voltage') continue;
			if ((probe_maxv[i] / all_max) < 1.0e-10) {
			    alert('Near zero ac response, remove ' + probe_color[i] + ' probe');
			    return;
			}
		    }
		}

		for (var i = probes.length - 1; i >= 0; --i) {
		    if (probes[i][3] != 'voltage') continue;
		    var color = probes[i][0];
		    var label = probes[i][1];
		    var offset = cktsim.parse_number(probes[i][2]);

		    var v = results[label];
		    // convert values into dB relative to source amplitude
		    var v_max = 1;
		    for (var j = v.length - 1; j >= 0; --j)
			// convert each value to dB relative to max
			v[j] = 20.0 * Math.log(v[j]/v_max)/Math.LN10;
		    y_values.push([color,offset,v]);

		    var v = results[label+'_phase'];
		    z_values.push([color,0,v]);
		}

		// graph the result and display in a window
		var graph2 = this.graph(x_values,'log(Frequency in Hz)',z_values,'degrees');
		this.window('AC Analysis - Phase',graph2);
		var graph1 = this.graph(x_values,'log(Frequency in Hz)',y_values,'dB');
		this.window('AC Analysis - Magnitude',graph1,50);
	    }
	}

	Schematic.prototype.transient_analysis = function() {
	    this.unselect_all(-1);
	    this.redraw_background();

	    var npts_lbl = 'Minimum number of timepoints';
	    var tstop_lbl = 'Stop Time (seconds)';
    
	    var probes = this.find_probes();
	    if (probes.length == 0) {
		alert("Transient Analysis: there are no probes in the diagram!");
		return;
	    }

	    var fields = new Array();
	    //fields[npts_lbl] = build_input('text',10,this.tran_npts);
	    fields[tstop_lbl] = build_input('text',10,this.tran_tstop);

	    var content = build_table(fields);
	    content.fields = fields;
	    content.sch = this;

	    this.dialog('Transient Analysis',content,function(content) {
		    var sch = content.sch;
		    var ckt = sch.extract_circuit();
		    if (ckt === null) return;

		    // retrieve parameters, remember for next time
		    //sch.tran_npts = content.fields[npts_lbl].value;
		    sch.tran_tstop = content.fields[tstop_lbl].value;

		    // gather a list of nodes that are being probed.  These
		    // will be added to the list of nodes checked during the
		    // LTE calculations in transient analysis
		    var probe_list = sch.find_probes();
		    var probe_names = new Array(probe_list.length);
		    for (var i = probe_list.length - 1; i >= 0; --i)
			probe_names[i] = probe_list[i][1];

		    // run the analysis
		    var results = ckt.tran(ckt.parse_number(sch.tran_npts), 0,
					   ckt.parse_number(sch.tran_tstop), probe_names, false);

		    if (typeof results == 'string') 
			sch.message(results);
		    else {
			if (sch.submit_analyses != undefined) {
			    var submit = sch.submit_analyses['tran'];
			    if (submit != undefined) {
				// save a copy of the results for submission
				sch.transient_results = {};
				var times = results['_time_'];

				// save requested values for each requested node
				for (var j = 0; j < submit.length; j++) {
				    var tlist = submit[j];    // [node_name,t1,t2,...]
				    var node = tlist[0];
				    var values = results[node];
				    var tvlist = [];
				    // for each requested time, interpolate waveform value
				    for (var k = 1; k < tlist.length; k++) {
					var t = tlist[k];
					var v = interpolate(t,times,values);
					tvlist.push([t,v == undefined ? 'undefined' : v]);
				    }
				    // save results as list of [t,value] pairs
				    sch.transient_results[node] = tvlist;
				}
			    }
			}

			var x_values = results['_time_'];
			var x_legend = 'Time';

			// set up plot values for each node with a probe
			var v_values = [];  // voltage values: list of [color, result_array]
			var i_values = [];  // current values: list of [color, result_array]
			var probes = sch.find_probes();

			for (var i = probes.length - 1; i >= 0; --i) {
			    var color = probes[i][0];
			    var label = probes[i][1];
			    var offset = cktsim.parse_number(probes[i][2]);
			    var v = results[label];
			    if (v == undefined) {
				alert('The ' + color + ' probe is connected to node ' + '"' + label + '"' + ' which is not an actual circuit node');
			    } else if (probes[i][3] == 'voltage') {
				if (color == 'x-axis') {
				    x_values = v;
				    x_legend = 'Voltage';
				} else v_values.push([color,offset,v]);
			    } else {
				if (color == 'x-axis') {
				    x_values = v;
				    x_legend = 'Current';
				} else i_values.push([color,offset,v]);
			    }
			}

			// graph the result and display in a window
			var graph = sch.graph(x_values,x_legend,v_values,'Voltage',i_values,'Current');
			sch.window('Results of Transient Analysis',graph);
		    }
	    })
	}

	// t is the time at which we want a value
	// times is a list of timepoints from the simulation
	function interpolate(t,times,values) {
	    if (values == undefined) return undefined;

	    for (var i = 0; i < times.length; i++)
		if (t < times[i]) {
		    // t falls between times[i-1] and times[i]
		    var t1 = (i == 0) ? times[0] : times[i-1];
		    var t2 = times[i];

		    if (t2 == undefined) return undefined;

		    var v1 = (i == 0) ? values[0] : values[i-1];
		    var v2 = values[i];
		    var v = v1;
		    if (t != t1) v += (t - t1)*(v2 - v1)/(t2 - t1);
		    return v;
		}
	}

	// external interface for setting the property value of a named component
	Schematic.prototype.set_property = function(component_name,property,value) {
	    this.unselect_all(-1);

	    for (var i = this.components.length - 1; i >= 0; --i) {
		var component = this.components[i];
		if (component.properties['name'] == component_name) {
		    component.properties[property] = value.toString();
		    break;
		}
	    }

	    // update diagram
	    this.redraw_background();
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

	    c.lineCap = 'round';

	    // paint background color
	    c.fillStyle = element_style;
	    c.fillRect(0,0,this.width,this.height);

	    if (!this.diagram_only && this.show_grid) {
		// grid
		c.strokeStyle = grid_style;
		var first_x = this.origin_x;
		var last_x = first_x + this.width/this.scale;
		var first_y = this.origin_y;
		var last_y = first_y + this.height/this.scale;

		for (var i = this.grid*Math.ceil(first_x/this.grid); i < last_x; i += this.grid)
		    this.draw_line(c,i,first_y,i,last_y,0.1);

		for (var i = this.grid*Math.ceil(first_y/this.grid); i < last_y; i += this.grid)
		    this.draw_line(c,first_x,i,last_x,i,0.1);
	    }

	    // unselected components
	    var min_x = Infinity;  // compute bounding box for diagram
	    var max_x = -Infinity;
	    var min_y = Infinity;
	    var max_y = -Infinity;
	    for (var i = this.components.length - 1; i >= 0; --i) {
		var component = this.components[i];
		if (!component.selected) {
		    component.draw(c);
		    min_x = Math.min(component.bbox[0],min_x);
		    max_x = Math.max(component.bbox[2],max_x);
		    min_y = Math.min(component.bbox[1],min_y);
		    max_y = Math.max(component.bbox[3],max_y);
		}
	    }
	    this.unsel_bbox = [min_x,min_y,max_x,max_y];

	    this.redraw();   // background changed, redraw on screen
	}

	// redraw what user sees = static image + dynamic parts
	Schematic.prototype.redraw = function() {
	    var c = this.canvas.getContext('2d');

	    // put static image in the background
	    c.drawImage(this.bg_image, 0, 0);

	    // selected components
	    var min_x = this.unsel_bbox[0];   // compute bounding box for diagram
	    var max_x = this.unsel_bbox[2];
	    var min_y = this.unsel_bbox[1];
	    var max_y = this.unsel_bbox[3];
	    var selections = false;
	    for (var i = this.components.length - 1; i >= 0; --i) {
		var component = this.components[i];
		if (component.selected) {
		    component.draw(c);
		    selections = true;
		    min_x = Math.min(component.bbox[0],min_x);
		    max_x = Math.max(component.bbox[2],max_x);
		    min_y = Math.min(component.bbox[1],min_y);
		    max_y = Math.max(component.bbox[3],max_y);
		}
	    }
	    if (min_x == Infinity) this.bbox = [0,0,0,0];
	    else this.bbox = [min_x,min_y,max_x,max_y];
	    this.enable_tool('cut',selections);
	    this.enable_tool('copy',selections);
	    this.enable_tool('paste',sch_clipboard.length > 0);

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
    
	    // display operating point results
	    if (this.operating_point) {
		if (typeof this.operating_point == 'string')
		    this.message(this.operating_point);
		else {
		    // make a copy of the operating_point info so we can mess with it
		    var temp = new Array();
		    for (var i in this.operating_point) temp[i] = this.operating_point[i];

		    // run through connection points displaying (once) the voltage
		    // for each electrical node
		    for (var location in this.connection_points)
			(this.connection_points[location])[0].display_voltage(c,temp);

		    // let components display branch current info if available
		    for (var i = this.components.length - 1; i >= 0; --i)
			this.components[i].display_current(c,temp)
		}
	    }
	    
	    // add scrolling/zooming control
	    if (!this.diagram_only) {
		var r = this.sctl_r;
		var x = this.sctl_x;
		var y = this.sctl_y;

		// circle with border
		c.fillStyle = element_style;
		c.beginPath();
		c.arc(x,y,r,0,2*Math.PI);
		c.fill();

		c.strokeStyle = grid_style;
		c.lineWidth = 0.5;
		c.beginPath();
		c.arc(x,y,r,0,2*Math.PI);
		c.stroke();

		// direction markers for scroll
		c.lineWidth = 3;
		c.beginPath();

		c.moveTo(x + 4,y - r + 8);   // north
		c.lineTo(x,y - r + 4);
		c.lineTo(x - 4,y - r + 8);

		c.moveTo(x + r - 8,y + 4);   // east
		c.lineTo(x + r - 4,y);
		c.lineTo(x + r - 8,y - 4);

		c.moveTo(x + 4,y + r - 8);   // south
		c.lineTo(x,y + r - 4);
		c.lineTo(x - 4,y + r - 8);

		c.moveTo(x - r + 8,y + 4);   // west
		c.lineTo(x - r + 4,y);
		c.lineTo(x - r + 8,y - 4);

		c.stroke();

		// zoom control
		x = this.zctl_left;
		y = this.zctl_top;
		c.lineWidth = 0.5;
		c.fillStyle = element_style;    // background
		c.fillRect(x,y,16,48);
		c.strokeStyle = grid_style;     // border
		c.strokeRect(x,y,16,48);
		c.lineWidth = 1.0;
		c.beginPath();
		// zoom in label
		c.moveTo(x+4,y+8); c.lineTo(x+12,y+8); c.moveTo(x+8,y+4); c.lineTo(x+8,y+12);
		// zoom out label
		c.moveTo(x+4,y+24); c.lineTo(x+12,y+24);
		// surround label
		c.strokeRect(x+4,y+36,8,8);
		c.stroke();
	    }
	}

	// draws a cross cursor
	Schematic.prototype.cross_cursor = function(c,x,y) {
	    this.draw_line(c,x-this.grid,y,x+this.grid,y,1);
	    this.draw_line(c,x,y-this.grid,x,y+this.grid,1);
	}

	Schematic.prototype.moveTo = function(c,x,y) {
	    c.moveTo((x - this.origin_x) * this.scale,(y - this.origin_y) * this.scale);
	}

	Schematic.prototype.lineTo = function(c,x,y) {
	    c.lineTo((x - this.origin_x) * this.scale,(y - this.origin_y) * this.scale);
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
	    var currentElement = this;
	    do {
		totalOffsetX += currentElement.offsetLeft;
		totalOffsetY += currentElement.offsetTop;
	    }
	    while (currentElement = currentElement.offsetParent);

	    // now compute relative position of click within the canvas
	    this.mouse_x = event.pageX - totalOffsetX;
	    this.mouse_y = event.pageY - totalOffsetY;

	    this.page_x = event.pageX;
	    this.page_y = event.pageY;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Event handling
	//
	////////////////////////////////////////////////////////////////////////////////

	// process keystrokes, consuming those that are meaningful to us
	function schematic_key_down(event) {
	    if (!event) event = window.event;
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;
	    var code = event.keyCode;

	    // keep track of modifier key state
	    if (code == 16) sch.shiftKey = true;
	    else if (code == 17) sch.ctrlKey = true;
	    else if (code == 18) sch.altKey = true;
	    else if (code == 91) sch.cmdKey = true;

	    // backspace or delete: delete selected components
	    else if (code == 8 || code == 46) {
		// delete selected components
		for (var i = sch.components.length - 1; i >= 0; --i) {
		    var component = sch.components[i];
		    if (component.selected) component.remove();
		}
		sch.clean_up_wires();
		sch.redraw_background();
		event.preventDefault();
		return false;
	    }

	    // cmd/ctrl x: cut
	    else if ((sch.ctrlKey || sch.cmdKey) && code == 88) {
		sch.cut();
		event.preventDefault();
		return false;
	    }

	    // cmd/ctrl c: copy
	    else if ((sch.ctrlKey || sch.cmdKey) && code == 67) {
		sch.copy();
		event.preventDefault();
		return false;
	    }

	    // cmd/ctrl v: paste
	    else if ((sch.ctrlKey || sch.cmdKey) && code == 86) {
		sch.paste();
		event.preventDefault();
		return false;
	    }

	    // 'r': rotate component
	    else if (!sch.ctrlKey && !sch.altKey && !sch.cmdKey && code == 82) {
		// rotate
		for (var i = sch.components.length - 1; i >= 0; --i) {
		    var component = sch.components[i];
		    if (component.selected) {
			component.rotate(1);
			sch.check_wires(component);
		    }
		}
		sch.clean_up_wires();
		sch.redraw_background();
		event.preventDefault();
		return false;
	    }

	    else return true;

	    // consume keystroke
	    sch.redraw();
	    event.preventDefault();
	    return false;
	}

	function schematic_key_up(event) {
	    if (!event) event = window.event;
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;
	    var code = event.keyCode;

	    if (code == 16) sch.shiftKey = false;
	    else if (code == 17) sch.ctrlKey = false;
	    else if (code == 18) sch.altKey = false;
	    else if (code == 91) sch.cmdKey = false;
	}

	function schematic_mouse_enter(event) {
	    if (!event) event = window.event;
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

	    // see if user has selected a new part
	    if (sch.new_part) {
		// grab incoming part, turn off selection of parts bin
		var part = sch.new_part;
		sch.new_part = undefined;
		part.select(false);

		// unselect everything else in the schematic, add part and select it
		sch.unselect_all(-1);
		sch.redraw_background();  // so we see any components that got unselected

		// make a clone of the component in the parts bin
		part = part.component.clone(sch.cursor_x,sch.cursor_y);
		part.add(sch);  // add it to schematic
		part.set_select(true);

		// and start dragging it
		sch.drag_begin();
	    }

	    sch.drawCursor = true;
	    sch.redraw();
	    sch.canvas.focus();  // capture key strokes
	    return false;
	}

	function schematic_mouse_leave(event) {
	    if (!event) event = window.event;
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;
	    sch.drawCursor = false;
	    sch.redraw();
	    return false;
	}

	function schematic_mouse_down(event) {
	    if (!event) event = window.event;
	    else event.preventDefault();
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

	    // determine where event happened in schematic coordinates
	    sch.canvas.relMouseCoords(event);

	    var mx = sch.canvas.mouse_x;
	    var my = sch.canvas.mouse_y;
	    var sx = mx - sch.sctl_x;
	    var sy = my - sch.sctl_y;
	    var zx = mx - sch.zctl_left;
	    var zy = my - sch.zctl_top;
	    if (sx*sx + sy*sy <= sch.sctl_r*sch.sctl_r) {   // click in scrolling control
		// click on scrolling control, check which quadrant
		if (Math.abs(sy) > Math.abs(sx)) {   // N or S
		    var delta = this.height / 8;
		    if (sy > 0) delta = -delta;
		    var temp = sch.origin_y - delta;
		    if (temp > origin_min*sch.grid && temp < origin_max*sch.grid) sch.origin_y = temp;
		} else {			    // E or W
		    var delta = this.width / 8;
		    if (sx < 0) delta = -delta;
		    var temp = sch.origin_x + delta;
		    if (temp > origin_min*sch.grid && temp < origin_max*sch.grid) sch.origin_x = temp;
		}
	    } else if (zx >= 0 && zx < 16 && zy >= 0 && zy < 48) {   // click in zoom control
		if (zy < 16) sch.zoomin();
		else if (zy < 32) sch.zoomout();
		else sch.zoomall();
	    } else {
		var x = mx/sch.scale + sch.origin_x;
		var y = my/sch.scale + sch.origin_y;
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
	    }

	    sch.redraw_background();
	    return false;
	}

	function schematic_mouse_move(event) {
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
	    //sch.message(sch.canvas.page_x + ',' + sch.canvas.page_y + ';' + sch.canvas.mouse_x + ',' + sch.canvas.mouse_y + ';' + sch.cursor_x + ',' + sch.cursor_y);

	    return false;
	}

	function schematic_mouse_up(event) {
	    if (!event) event = window.event;
	    else event.preventDefault();
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

	    // drawing a new wire
	    if (sch.wire) {
		var r = sch.wire;
		sch.wire = undefined;

		if (r[0]!=r[2] || r[1]!=r[3]) {
		    // insert wire component
		    sch.add_wire(r[0],r[1],r[2],r[3]);
		    sch.clean_up_wires();
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

		sch.select_rect = undefined;
		sch.redraw_background();
	    }
	    return false;
	}

	function schematic_mouse_wheel(event) {
	    if (!event) event = window.event;
	    else event.preventDefault();
	    var sch = (window.event) ? event.srcElement.schematic : event.target.schematic;

	    var delta = 0;
	    if (event.wheelDelta) delta = event.wheelDelta;
	    else if (event.detail) delta = -event.detail;

	    if (delta) {
		var nscale = (delta > 0) ? sch.scale*zoom_factor : sch.scale/zoom_factor;

		if (nscale > zoom_min && nscale < zoom_max) {
		    // zoom around current mouse position
		    sch.canvas.relMouseCoords(event);
		    var s = 1.0/sch.scale - 1.0/nscale;
		    sch.origin_x += sch.canvas.mouse_x*s;
		    sch.origin_y += sch.canvas.mouse_y*s;
		    sch.scale = nscale;
		    sch.redraw_background();
		}
	    }
	}

	function schematic_double_click(event) {
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
		if (sch.components[i].edit_properties(x,y))
		    break;

	    return false;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Status message and dialogs
	//
	////////////////////////////////////////////////////////////////////////////////

	Schematic.prototype.message = function(message) {
	    this.status.nodeValue = message;
	}

	Schematic.prototype.append_message = function(message) {
	    this.status.nodeValue += ' / '+message;
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
	    dialog.callback = callback;

	    // look for property input fields in the content and give
	    // them a keypress listener that interprets ENTER as
	    // clicking OK.
	    var plist = content.getElementsByClassName('property');
	    for (var i = plist.length - 1; i >= 0; --i) {
		var field = plist[i];
		field.dialog = dialog;  // help event handler find us...
		field.addEventListener('keypress',dialog_check_for_ENTER,false);
	    }

	    // div to hold the content
	    var body = document.createElement('div');
	    content.style.marginBotton = '5px';
	    body.appendChild(content);
	    body.style.padding = '5px';
	    dialog.appendChild(body);

	    // OK button
	    var ok_button = document.createElement('span');
	    ok_button.appendChild(document.createTextNode('OK'));
	    ok_button.dialog = dialog;   // for the handler to use
	    ok_button.addEventListener('click',dialog_okay,false);
	    ok_button.style.display = 'inline';
	    ok_button.style.border = '1px solid';
	    ok_button.style.padding = '5px';
	    ok_button.style.margin = '10px';

	    // cancel button
	    var cancel_button = document.createElement('span');
	    cancel_button.appendChild(document.createTextNode('Cancel'));
	    cancel_button.dialog = dialog;   // for the handler to use
	    cancel_button.addEventListener('click',dialog_cancel,false);
	    cancel_button.style.display = 'inline';
	    cancel_button.style.border = '1px solid';
	    cancel_button.style.padding = '5px';
	    cancel_button.style.margin = '10px';

	    // div to hold the two buttons
	    var buttons = document.createElement('div');
	    buttons.style.textAlign = 'center';
	    buttons.appendChild(ok_button);
	    buttons.appendChild(cancel_button);
	    buttons.style.padding = '5px';
	    buttons.style.margin = '10px';
	    dialog.appendChild(buttons);

	    // put into an overlay window
	    this.window(title,dialog);
	}

	// callback when user click "Cancel" in a dialog
	function dialog_cancel(event) {
	    if (!event) event = window.event;
	    var dialog = (window.event) ? event.srcElement.dialog : event.target.dialog;

	    window_close(dialog.win);
	}

	// callback when user click "OK" in a dialog
	function dialog_okay(event) {
	    if (!event) event = window.event;
	    var dialog = (window.event) ? event.srcElement.dialog : event.target.dialog;

	    window_close(dialog.win);

	    // invoke the callback with the dialog contents as the argument
	    if (dialog.callback) dialog.callback(dialog.content);
	}

	// callback for keypress in input fields: if user typed ENTER, act
	// like they clicked OK button.
	function dialog_check_for_ENTER(event) {
	    var key = (window.event) ? window.event.keyCode : event.keyCode;
	    if (key == 13) dialog_okay(event);
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Draggable, resizeable, closeable window
	//
	////////////////////////////////////////////////////////////////////////////////

	// build a 2-column HTML table from an associative array (keys as text in
	// column 1, values in column 2).
	function build_table(a) {
	    var tbl = document.createElement('table');

	    // build a row for each element in associative array
	    for (var i in a) {
		var label = document.createTextNode(i + ': ');
		var col1 = document.createElement('td');
		col1.appendChild(label);
		var col2 = document.createElement('td');
		col2.appendChild(a[i]);
		var row = document.createElement('tr');
		row.appendChild(col1);
		row.appendChild(col2);
		row.style.verticalAlign = 'center';
		tbl.appendChild(row);
	    }

	    return tbl;
	}

	// build an input field
	function build_input(type,size,value) {
	    var input = document.createElement('input');
	    input.type = type;
	    input.size = size;
	    input.className = 'property';  // make this easier to find later
	    if (value == undefined) input.value = '';
	    else input.value = value.toString();
	    return input;
	}

	// build a select widget using the strings found in the options array
	function build_select(options,selected) {
	    var select = document.createElement('select');
	    for (var i = 0; i < options.length; i++) {
		var option = document.createElement('option');
		option.text = options[i];
		select.add(option);
		if (options[i] == selected) select.selectedIndex = i;
	    }
	    return select;
	}

	Schematic.prototype.window = function(title,content,offset) {
	    // create the div for the top level of the window
	    var win = document.createElement('div');
	    win.sch = this;
	    win.content = content;
	    win.drag_x = undefined;
	    win.draw_y = undefined;

	    // div to hold the title
	    var head = document.createElement('div');
	    head.style.backgroundColor = 'black';
	    head.style.color = 'white';
	    head.style.textAlign = 'center';
	    head.style.padding = '5px';
	    head.appendChild(document.createTextNode(title));
	    head.win = win;
	    win.head = head;

	    var close_button = new Image();
	    close_button.src = close_icon;
	    close_button.style.cssFloat = 'right';
	    close_button.addEventListener('click',window_close_button,false);
	    close_button.win = win;
	    head.appendChild(close_button);

	    win.appendChild(head);

	    // capture mouse events in title bar
	    head.addEventListener('mousedown',window_mouse_down,false);

	    // div to hold the content
	    //var body = document.createElement('div');
	    //body.appendChild(content);
	    win.appendChild(content);
	    content.win = win;   // so content can contact us

	    // compute location relative to canvas
	    if (offset == undefined) offset = 0;
	    win.left = this.canvas.mouse_x + offset;
	    win.top = this.canvas.mouse_y + offset;

	    // add to DOM
	    win.style.background = 'white';
	    //win.style.zIndex = '1000';
	    win.style.position = 'absolute';
	    win.style.left = win.left + 'px';
	    win.style.top = win.top + 'px';
	    win.style.border = '2px solid';

	    this.canvas.parentNode.insertBefore(win,this.canvas);
	    bring_to_front(win,true);
	}

	// adjust zIndex of pop-up window so that it is in front
	function bring_to_front(win,insert) {
	    var wlist = win.sch.window_list;
	    var i = wlist.indexOf(win);

	    // remove from current position (if any) in window list
	    if (i != -1) wlist.splice(i,1);

	    // if requested, add to end of window list
	    if (insert) wlist.push(win);

	    // adjust all zIndex values
	    for (i = 0; i < wlist.length; i += 1)
		wlist[i].style.zIndex = 1000 + i;
	}

	// close the window
	function window_close(win) {
	    // remove the window from the top-level div of the schematic
	    win.parentNode.removeChild(win);

	    // remove from list of pop-up windows
	    bring_to_front(win,false);
	}

	function window_close_button(event) {
	    if (!event) event = window.event;
	    var src = (window.event) ? event.srcElement : event.target;
	    window_close(src.win);
	}

	// capture mouse events in title bar of window
	function window_mouse_down(event) {
	    if (!event) event = window.event;
	    var src = (window.event) ? event.srcElement : event.target;
	    var win = src.win;

	    bring_to_front(win,true);

	    // add handlers to document so we capture them no matter what
	    document.addEventListener('mousemove',window_mouse_move,false);
	    document.addEventListener('mouseup',window_mouse_up,false);
	    document.tracking_window = win;
    
	    // remember where mouse is so we can compute dx,dy during drag
	    win.drag_x = event.pageX;
	    win.drag_y = event.pageY;

	    return false;
	}

	function window_mouse_up(event) {
	    var win = document.tracking_window;
    
	    // show's over folks...
	    document.removeEventListener('mousemove',window_mouse_move,false);
	    document.removeEventListener('mouseup',window_mouse_up,false);
	    document.tracking_window = undefined;
	    win.drag_x = undefined;
	    win.drag_y = undefined;
	    return true;  // consume event
	}

	function window_mouse_move(event) {
	    var win = document.tracking_window;
    
	    if (win.drag_x) {
		var dx = event.pageX - win.drag_x;
		var dy = event.pageY - win.drag_y;

		// move the window
		win.left += dx;
		win.top += dy;
		win.style.left = win.left + 'px';
		win.style.top = win.top + 'px';
	
		// update reference point
		win.drag_x += dx;
		win.drag_y += dy;

		return true;  // consume event
	    }
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Toolbar
	//
	////////////////////////////////////////////////////////////////////////////////

	Schematic.prototype.add_tool = function(icon,tip,callback) {
	    var tool;
	    if (icon.search('data:image') != -1) {
		tool = document.createElement('img');
		tool.src = icon;
	    } else {
		tool = document.createElement('span');
		tool.style.font = 'small-caps small sans-serif';
		var label = document.createTextNode(icon);
		tool.appendChild(label);
	    }

	    // decorate tool
	    tool.style.borderWidth = '1px';
	    tool.style.borderStyle = 'solid';
	    tool.style.borderColor = background_style;
	    tool.style.padding = '2px';
	    tool.style.verticalAlign = 'middle';
	    tool.style.cursor = 'default';

	    // set up event processing
	    tool.addEventListener('mouseover',tool_enter,false);
	    tool.addEventListener('mouseout',tool_leave,false);
	    tool.addEventListener('click',tool_click,false);

	    // add to toolbar
	    tool.sch = this;
	    tool.tip = tip;
	    tool.callback = callback;
	    this.toolbar.push(tool);

	    tool.enabled = false;
	    tool.style.opacity = 0.2;

	    return tool;
	}

	Schematic.prototype.enable_tool = function(tname,which) {
	    var tool = this.tools[tname];

	    if (tool != undefined) {
		tool.style.opacity = which ? 1.0 : 0.2;
		tool.enabled = which;

		// if disabling tool, remove border and tip
		if (!which) {
		    tool.style.borderColor = background_style;
		    tool.sch.message('');
		}
	    }
	}

	// highlight tool button by turning on border, changing background
	function tool_enter(event) {
	    if (!event) event = window.event;
	    var tool = (window.event) ? event.srcElement : event.target;

	    if (tool.enabled) {
		tool.style.borderColor = normal_style;
		tool.sch.message(tool.tip);
		tool.opacity = 1.0;
	    }
	}

	// unhighlight tool button by turning off border, reverting to normal background
	function tool_leave(event) {
	    if (!event) event = window.event;
	    var tool = (window.event) ? event.srcElement : event.target;

	    if (tool.enabled) {
		tool.style.borderColor = background_style;
		tool.sch.message('');
	    }
	}

	// handle click on a tool
	function tool_click(event) {
	    if (!event) event = window.event;
	    var tool = (window.event) ? event.srcElement : event.target;

	    if (tool.enabled) {
		tool.sch.canvas.relMouseCoords(event);  // so we can position pop-up window correctly
		tool.callback.call(tool.sch);
	    }
	}

	help_icon = 'data:image/gif;base64,R0lGODlhEAAQAJEAAAAAAP///wAAAAAAACH5BAkAAAIAIf8LSUNDUkdCRzEwMTL/AAAHqGFwcGwCIAAAbW50clJHQiBYWVogB9kAAgAZAAsAGgALYWNzcEFQUEwAAAAAYXBwbAAAAAAAAAAAAAAAAAAAAAAAAPbWAAEAAAAA0y1hcHBsAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALZGVzYwAAAQgAAABvZHNjbQAAAXgAAAVsY3BydAAABuQAAAA4d3RwdAAABxwAAAAUclhZWgAABzAAAAAUZ1hZWgAAB0QAAAAUYlhZWgAAB1gAAAAUclRSQwAAB2wAAAAOY2hhZAAAB3wAAAAsYlRSQwAAB2wAAAAOZ1RS/0MAAAdsAAAADmRlc2MAAAAAAAAAFEdlbmVyaWMgUkdCIFByb2ZpbGUAAAAAAAAAAAAAABRHZW5lcmljIFJHQiBQcm9maWxlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABtbHVjAAAAAAAAAB4AAAAMc2tTSwAAACgAAAF4aHJIUgAAACgAAAGgY2FFUwAAACQAAAHIcHRCUgAAACYAAAHsdWtVQQAAACoAAAISZnJGVQAAACgAAAI8emhUVwAAABYAAAJkaXRJVAAAACgAAAJ6bmJOTwAAACYAAAKia29LUgAAABYAAP8CyGNzQ1oAAAAiAAAC3mhlSUwAAAAeAAADAGRlREUAAAAsAAADHmh1SFUAAAAoAAADSnN2U0UAAAAmAAAConpoQ04AAAAWAAADcmphSlAAAAAaAAADiHJvUk8AAAAkAAADomVsR1IAAAAiAAADxnB0UE8AAAAmAAAD6G5sTkwAAAAoAAAEDmVzRVMAAAAmAAAD6HRoVEgAAAAkAAAENnRyVFIAAAAiAAAEWmZpRkkAAAAoAAAEfHBsUEwAAAAsAAAEpHJ1UlUAAAAiAAAE0GFyRUcAAAAmAAAE8mVuVVMAAAAmAAAFGGRhREsAAAAuAAAFPgBWAWEAZQBvAGIAZQD/YwBuAP0AIABSAEcAQgAgAHAAcgBvAGYAaQBsAEcAZQBuAGUAcgBpAQ0AawBpACAAUgBHAEIAIABwAHIAbwBmAGkAbABQAGUAcgBmAGkAbAAgAFIARwBCACAAZwBlAG4A6AByAGkAYwBQAGUAcgBmAGkAbAAgAFIARwBCACAARwBlAG4A6QByAGkAYwBvBBcEMAQzBDAEOwRMBD0EOAQ5ACAEPwRABD4ERAQwBDkEOwAgAFIARwBCAFAAcgBvAGYAaQBsACAAZwDpAG4A6QByAGkAcQB1AGUAIABSAFYAQpAadSgAIABSAEcAQgAggnJfaWPPj/AAUAByAG8AZgBp/wBsAG8AIABSAEcAQgAgAGcAZQBuAGUAcgBpAGMAbwBHAGUAbgBlAHIAaQBzAGsAIABSAEcAQgAtAHAAcgBvAGYAaQBsx3y8GAAgAFIARwBCACDVBLhc0wzHfABPAGIAZQBjAG4A/QAgAFIARwBCACAAcAByAG8AZgBpAGwF5AXoBdUF5AXZBdwAIABSAEcAQgAgBdsF3AXcBdkAQQBsAGwAZwBlAG0AZQBpAG4AZQBzACAAUgBHAEIALQBQAHIAbwBmAGkAbADBAGwAdABhAGwA4QBuAG8AcwAgAFIARwBCACAAcAByAG8AZgBpAGxmbpAaACAAUgBHAEIAIGPPj//wZYdO9k4AgiwAIABSAEcAQgAgMNcw7TDVMKEwpDDrAFAAcgBvAGYAaQBsACAAUgBHAEIAIABnAGUAbgBlAHIAaQBjA5MDtQO9A7kDugPMACADwAPBA78DxgOvA7sAIABSAEcAQgBQAGUAcgBmAGkAbAAgAFIARwBCACAAZwBlAG4A6QByAGkAYwBvAEEAbABnAGUAbQBlAGUAbgAgAFIARwBCAC0AcAByAG8AZgBpAGUAbA5CDhsOIw5EDh8OJQ5MACAAUgBHAEIAIA4XDjEOSA4nDkQOGwBHAGUAbgBlAGwAIABSAEcAQgAgAFAAcgBvAGYAaQBsAGkAWQBsAGX/AGkAbgBlAG4AIABSAEcAQgAtAHAAcgBvAGYAaQBpAGwAaQBVAG4AaQB3AGUAcgBzAGEAbABuAHkAIABwAHIAbwBmAGkAbAAgAFIARwBCBB4EMQRJBDgEOQAgBD8EQAQ+BEQEOAQ7BEwAIABSAEcAQgZFBkQGQQAgBioGOQYxBkoGQQAgAFIARwBCACAGJwZEBjkGJwZFAEcAZQBuAGUAcgBpAGMAIABSAEcAQgAgAFAAcgBvAGYAaQBsAGUARwBlAG4AZQByAGUAbAAgAFIARwBCAC0AYgBlAHMAawByAGkAdgBlAGwAcwBldGV4dAAAAABDb3B5cmlnaHQgMjAwrzcgQXBwbGUgSW5jLiwgYWxsIHJpZ2h0cyByZXNlcnZlZC4AWFlaIAAAAAAAAPNSAAEAAAABFs9YWVogAAAAAAAAdE0AAD3uAAAD0FhZWiAAAAAAAABadQAArHMAABc0WFlaIAAAAAAAACgaAAAVnwAAuDZjdXJ2AAAAAAAAAAEBzQAAc2YzMgAAAAAAAQxCAAAF3v//8yYAAAeSAAD9kf//+6L///2jAAAD3AAAwGwALAAAAAAQABAAAAIglI+pwK3XInhSLoZc0oa/7lHRB4bXRJZoaqau+o6ujBQAOw==';

	cut_icon = 'data:image/gif;base64,R0lGODlhEAAQALMAAAAAAIAAAACAAICAAAAAgIAAgACAgMDAwICAgP8AAAD/AP//AAAA//8A/wD//////yH5BAEAAAcALAAAAAAQABAAAAQu8MhJqz1g5qs7lxv2gRkQfuWomarXEgDRHjJhf3YtyRav0xcfcFgR0nhB5OwTAQA7';

	copy_icon = 'data:image/gif;base64,R0lGODlhEAAQALMAAAAAAIAAAACAAICAAAAAgIAAgACAgMDAwICAgP8AAAD/AP//AAAA//8A/wD//////yH5BAEAAAcALAAAAAAQABAAAAQ+8MhJ6wE4Wwqef9gmdV8HiKZJrCz3ecS7TikWfzExvk+M9a0a4MbTkXCgTMeoHPJgG5+yF31SLazsTMTtViIAOw==';

	paste_icon = 'data:image/gif;base64,R0lGODlhEAAQALMAAAAAAIAAAACAAICAAAAAgIAAgACAgMDAwICAgP8AAAD/AP//AAAA//8A/wD//////yH5BAEAAAcALAAAAAAQABAAAARL8MhJqwUYWJnxWp3GDcgAgCdQIqLKXmVLhhnyHiqpr7rME8AgocVDEB5IJHD0SyofBFzxGIQGAbvB0ZkcTq1CKK6z5YorwnR0w44AADs=';

	close_icon = 'data:image/gif;base64,R0lGODlhEAAQAMQAAGtra/f3/62tre/v9+bm787O1pycnHNzc6WlpcXFxd7e3tbW1nt7e7W1te/v74SEhMXFzmNjY+bm5v///87OzgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAAAAAAALAAAAAAQABAAAAVt4DRMZGmSwRQQBUS9MAwRIyQ5Uq7neEFSDtxOF4T8cobIQaE4RAQ5yjHHiCCSD510QtFGvoCFdppDfBu7bYzy+D7WP5ggAgA8Y3FKwi5IAhIweW1vbBGEWy5rilsFi2tGAwSJixAFBCkpJ5ojIQA7';

	grid_icon = 'data:image/gif;base64,R0lGODlhEAAQAMQAAAAAAP///zAwYT09bpGRqZ6et5iYsKWlvbi40MzM5cXF3czM5OHh5tTU2fDw84uMom49DbWKcfLy8g0NDcDAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAABQALAAAAAAQABAAAAUtICWOZGmeKDCqIlu68AvMdO2ueHvGuslTN6Bt6MsBd8Zg77hsDW3FpRJFrYpCADs=';

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Graphing
	//
	///////////////////////////////////////////////////////////////////////////////

	// add dashed lines!
	// from http://davidowens.wordpress.com/2010/09/07/html-5-canvas-and-dashed-lines/
	CanvasRenderingContext2D.prototype.dashedLineTo = function(fromX, fromY, toX, toY, pattern) {
	    // Our growth rate for our line can be one of the following:
	    //   (+,+), (+,-), (-,+), (-,-)
	    // Because of this, our algorithm needs to understand if the x-coord and
	    // y-coord should be getting smaller or larger and properly cap the values
	    // based on (x,y).
	    var lt = function (a, b) { return a <= b; };
	    var gt = function (a, b) { return a >= b; };
	    var capmin = function (a, b) { return Math.min(a, b); };
	    var capmax = function (a, b) { return Math.max(a, b); };

	    var checkX = { thereYet: gt, cap: capmin };
	    var checkY = { thereYet: gt, cap: capmin };

	    if (fromY - toY > 0) {
		checkY.thereYet = lt;
		checkY.cap = capmax;
	    }
	    if (fromX - toX > 0) {
		checkX.thereYet = lt;
		checkX.cap = capmax;
	    }

	    this.moveTo(fromX, fromY);
	    var offsetX = fromX;
	    var offsetY = fromY;
	    var idx = 0, dash = true;
	    while (!(checkX.thereYet(offsetX, toX) && checkY.thereYet(offsetY, toY))) {
		var ang = Math.atan2(toY - fromY, toX - fromX);
		var len = pattern[idx];

		offsetX = checkX.cap(toX, offsetX + (Math.cos(ang) * len));
		offsetY = checkY.cap(toY, offsetY + (Math.sin(ang) * len));

		if (dash) this.lineTo(offsetX, offsetY);
		else this.moveTo(offsetX, offsetY);

		idx = (idx + 1) % pattern.length;
		dash = !dash;
	    }
	};

	// given a range of values, return a new range [vmin',vmax'] where the limits
	// have been chosen "nicely".  Taken from matplotlib.ticker.LinearLocator
	function view_limits(vmin,vmax) {
	    // deal with degenerate case...
	    if (vmin == vmax) {
		if (vmin == 0) { vmin = -0.5; vmax = 0.5; }
		else {
		    vmin = vmin > 0 ? 0.9*vmin : 1.1*vmin;
		    vmax = vmax > 0 ? 1.1*vmax : 0.9*vmax;
		}
	    }

	    var log_range = Math.log(vmax - vmin)/Math.LN10;
	    var exponent = Math.floor(log_range);
	    //if (log_range - exponent < 0.5) exponent -= 1;
	    var scale = Math.pow(10,-exponent);
	    vmin = Math.floor(scale*vmin)/scale;
	    vmax = Math.ceil(scale*vmax)/scale;

	    return [vmin,vmax,1.0/scale];
	}

	function engineering_notation(n,nplaces,trim) {
	    if (n == 0) return '0';
	    if (n == undefined) return 'undefined';
	    if (trim == undefined) trim = true;

	    var sign = n < 0 ? -1 : 1;
	    var log10 = Math.log(sign*n)/Math.LN10;
	    var exp = Math.floor(log10/3);   // powers of 1000
	    var mantissa = sign*Math.pow(10,log10 - 3*exp);

	    // keep specified number of places following decimal point
	    var mstring = (mantissa + sign*0.5*Math.pow(10,-nplaces)).toString();
	    var mlen = mstring.length;
	    var endindex = mstring.indexOf('.');
	    if (endindex != -1) {
		if (nplaces > 0) {
		    endindex += nplaces + 1;
		    if (endindex > mlen) endindex = mlen;
		    if (trim) {
			while (mstring.charAt(endindex-1) == '0') endindex -= 1;
			if (mstring.charAt(endindex-1) == '.') endindex -= 1;
		    }
		}
		if (endindex < mlen)
		    mstring = mstring.substring(0,endindex);
	    }

	    switch(exp) {
	    case -5:	return mstring+"f";
	    case -4:	return mstring+"p";
	    case -3:	return mstring+"n";
	    case -2:	return mstring+"u";
	    case -1:	return mstring+"m";
	    case 0:	return mstring;
	    case 1:	return mstring+"K";
	    case 2:	return mstring+"M";
	    case 3:	return mstring+"G";
	    }

	    // don't have a good suffix, so just print the number
	    return n.toString();
	}

	var grid_pattern = [1,2];
	var cursor_pattern = [5,5];

	// x_values is an array of x coordinates for each of the plots
	// y_values is an array of [color, value_array], one entry for each plot on left vertical axis
	// z_values is an array of [color, value_array], one entry for each plot on right vertical axis
	Schematic.prototype.graph = function(x_values,x_legend,y_values,y_legend,z_values,z_legend) {
	    var pwidth = 400;	// dimensions of actual plot
	    var pheight = 300;	// dimensions of actual plot
	    var left_margin = (y_values != undefined && y_values.length > 0) ? 55 : 25;
	    var top_margin = 25;
	    var right_margin = (z_values != undefined && z_values.length > 0) ? 55 : 25;
	    var bottom_margin = 45;
	    var tick_length = 5;

	    var w = pwidth + left_margin + right_margin;
	    var h = pheight + top_margin + bottom_margin;

	    var canvas = document.createElement('canvas');
	    canvas.width = w;
	    canvas.height = h;

	    // the graph itself will be drawn here and this image will be copied
	    // onto canvas, where it can be overlayed with mouse cursors, etc.
	    var bg_image = document.createElement('canvas');
	    bg_image.width = w;
	    bg_image.height = h;
	    canvas.bg_image = bg_image;	// so we can find it during event handling

	    // start by painting an opaque background
	    var c = bg_image.getContext('2d');
	    c.fillStyle = background_style;
	    c.fillRect(0,0,w,h);
	    c.fillStyle = element_style;
	    c.fillRect(left_margin,top_margin,pwidth,pheight);

	    // figure out scaling for plots
	    var x_min = array_min(x_values);
	    var x_max = array_max(x_values);
	    var x_limits = view_limits(x_min,x_max);
	    x_min = x_limits[0];
	    x_max = x_limits[1];
	    var x_scale = pwidth/(x_max - x_min);

	    function plot_x(x) {
		return (x - x_min)*x_scale + left_margin;
	    }

	    // draw x grid
	    c.strokeStyle = grid_style;
	    c.lineWidth = 1;
	    c.fillStyle = normal_style;
	    c.font = '10pt sans-serif';
	    c.textAlign = 'center';
	    c.textBaseline = 'top';
	    var end = top_margin + pheight;
	    for (var x = x_min; x <= x_max; x += x_limits[2]) {
		var temp = plot_x(x) + 0.5;  // keep lines crisp!

		// grid line
		c.beginPath();
		if (x == x_min) {
		    c.moveTo(temp,top_margin);
		    c.lineTo(temp,end);
		} else 
		    c.dashedLineTo(temp,top_margin,temp,end,grid_pattern);
		c.stroke();

		// tick mark
		c.beginPath();
		c.moveTo(temp,end);
		c.lineTo(temp,end + tick_length);
		c.stroke();
		c.fillText(engineering_notation(x,2),temp,end + tick_length);
	    }

	    if (y_values != undefined && y_values.length > 0) {
		var y_min = Infinity;
		var y_max = -Infinity;
		var plot;
		for (plot = y_values.length - 1; plot >= 0; --plot) {
		    var values = y_values[plot][2];
		    if (values == undefined) continue;  // no data points
		    var offset = y_values[plot][1];
		    var temp = array_min(values) + offset;
		    if (temp < y_min) y_min = temp;
		    temp = array_max(values) + offset;
		    if (temp > y_max) y_max = temp;
		}
		var y_limits = view_limits(y_min,y_max);
		y_min = y_limits[0];
		y_max = y_limits[1];
		var y_scale = pheight/(y_max - y_min);

		function plot_y(y) {
		    return (y_max - y)*y_scale + top_margin;
		}

		// draw y grid
		c.textAlign = 'right';
		c.textBaseline = 'middle';
		for (var y = y_min; y <= y_max; y += y_limits[2]) {
		    if (Math.abs(y/y_max) < 0.001) y = 0.0; // Just 3 digits
		    var temp = plot_y(y) + 0.5;  // keep lines crisp!

		    // grid line
		    c.beginPath();
		    if (y == y_min) {
			c.moveTo(left_margin,temp);
			c.lineTo(left_margin + pwidth,temp);
		    } else 
			c.dashedLineTo(left_margin,temp,left_margin + pwidth,temp,grid_pattern);
		    c.stroke();

		    // tick mark
		    c.beginPath();
		    c.moveTo(left_margin - tick_length,temp);
		    c.lineTo(left_margin,temp);
		    c.stroke();
		    c.fillText(engineering_notation(y,2),left_margin - tick_length -2,temp);
		}

		// now draw each plot
		var x,y;
		var nx,ny;
		c.lineWidth = 3;
		c.lineCap = 'round';
		for (plot = y_values.length - 1; plot >= 0; --plot) {
		    var color = probe_colors_rgb[y_values[plot][0]];
		    if (color == undefined) continue;  // no plot color (== x-axis)
		    c.strokeStyle = color;
		    var values = y_values[plot][2];
		    if (values == undefined) continue;  // no data points
		    var offset = y_values[plot][1];

		    x = plot_x(x_values[0]);
		    y = plot_y(values[0] + offset);
		    c.beginPath();
		    c.moveTo(x,y);
		    for (var i = 1; i < x_values.length; i++) {
			nx = plot_x(x_values[i]);
			ny = plot_y(values[i] + offset);
			c.lineTo(nx,ny);
			x = nx;
			y = ny;
			if (i % 100 == 99) {
			    // too many lineTo's cause canvas to break
			    c.stroke();
			    c.beginPath();
			    c.moveTo(x,y);
			}
		    }
		    c.stroke();
		}
	    }

	    if (z_values != undefined && z_values.length > 0) {
		var z_min = Infinity;
		var z_max = -Infinity;
		for (plot = z_values.length - 1; plot >= 0; --plot) {
		    var values = z_values[plot][2];
		    if (values == undefined) continue;  // no data points
		    var offset = z_values[plot][1];
		    var temp = array_min(values) + offset;
		    if (temp < z_min) z_min = temp;
		    temp = array_max(values) + offset;
		    if (temp > z_max) z_max = temp;
		}
		var z_limits = view_limits(z_min,z_max);
		z_min = z_limits[0];
		z_max = z_limits[1];
		var z_scale = pheight/(z_max - z_min);

		function plot_z(z) {
		    return (z_max - z)*z_scale + top_margin;
		}

		// draw z ticks
		c.textAlign = 'left';
		c.textBaseline = 'middle';
		c.lineWidth = 1;
		c.strokeStyle = normal_style;
		var tick_length_half = Math.floor(tick_length/2);
		var tick_delta = tick_length - tick_length_half;
		for (var z = z_min; z <= z_max; z += z_limits[2]) {
		    if (Math.abs(z/z_max) < 0.001) z = 0.0; // Just 3 digits
		    var temp = plot_z(z) + 0.5;  // keep lines crisp!

		    // tick mark
		    c.beginPath();
		    c.moveTo(left_margin + pwidth - tick_length_half,temp);
		    c.lineTo(left_margin + pwidth + tick_delta,temp);
		    c.stroke();
		    c.fillText(engineering_notation(z,2),left_margin + pwidth + tick_length + 2,temp);
		}

		var z;
		var nz;
		c.lineWidth = 3;
		for (plot = z_values.length - 1; plot >= 0; --plot) {
		    var color = probe_colors_rgb[z_values[plot][0]];
		    if (color == undefined) continue;  // no plot color (== x-axis)
		    c.strokeStyle = color;
		    var values = z_values[plot][2];
		    if (values == undefined) continue;  // no data points
		    var offset = z_values[plot][1];
		    
		    x = plot_x(x_values[0]);
		    z = plot_z(values[0] + offset);
		    c.beginPath();
		    c.moveTo(x,z);
		    for (var i = 1; i < x_values.length; i++) {
			nx = plot_x(x_values[i]);
			nz = plot_z(values[i] + offset);
			c.lineTo(nx,nz);
			x = nx;
			z = nz;
			if (i % 100 == 99) {
			    // too many lineTo's cause canvas to break
			    c.stroke();
			    c.beginPath();
			    c.moveTo(x,z);
			}
		    }
		    c.stroke();
		}
	    }

	    // draw legends
	    c.font = '12pt sans-serif';
	    c.textAlign = 'center';
	    c.textBaseline = 'bottom';
	    c.fillText(x_legend,left_margin + pwidth/2,h - 5);

	    if (y_values != undefined && y_values.length > 0) {
		c.textBaseline = 'top';
		c.save();
		c.translate(5 ,top_margin + pheight/2);
		c.rotate(-Math.PI/2);
		c.fillText(y_legend,0,0);
		c.restore();
	    }

	    if (z_values != undefined && z_values.length > 0) {
		c.textBaseline = 'bottom';
		c.save();
		c.translate(w-5 ,top_margin + pheight/2);
		c.rotate(-Math.PI/2);
		c.fillText(z_legend,0,0);
		c.restore();
	    }

	    // save info need for interactions with the graph
	    canvas.x_values = x_values;
	    canvas.y_values = y_values;
	    canvas.z_values = z_values;
	    canvas.x_legend = x_legend;
	    canvas.y_legend = y_legend;
	    canvas.z_legend = y_legend;
	    canvas.x_min = x_min;
	    canvas.x_scale = x_scale;
	    canvas.y_min = y_min;
	    canvas.y_scale = y_scale;
	    canvas.z_min = z_min;
	    canvas.z_scale = z_scale;
	    canvas.left_margin = left_margin;
	    canvas.top_margin = top_margin;
	    canvas.pwidth = pwidth;
	    canvas.pheight = pheight;
	    canvas.tick_length = tick_length;

	    canvas.cursor1_x = undefined;
	    canvas.cursor2_x = undefined;
	    canvas.sch = this;

	    // do something useful when user mouses over graph
	    canvas.addEventListener('mousemove',graph_mouse_move,false);

	    // return our masterpiece
	    redraw_plot(canvas);
	    return canvas;
	}

	function array_max(a) {
	    max = -Infinity;
	    for (var i = a.length - 1; i >= 0; --i)
		if (a[i] > max) max = a[i];
	    return max;
	}

	function array_min(a) {
	    min = Infinity;
	    for (var i = a.length - 1; i >= 0; --i)
		if (a[i] < min) min = a[i];
	    return min;
	}

	function plot_cursor(c,graph,cursor_x,left_margin) {
	    // draw dashed vertical marker that follows mouse
	    var x = graph.left_margin + cursor_x;
	    var end_y = graph.top_margin + graph.pheight + graph.tick_length;
	    c.strokeStyle = grid_style;
	    c.lineWidth = 1;
	    c.beginPath();
	    c.dashedLineTo(x,graph.top_margin,x,end_y,cursor_pattern);
	    c.stroke();

	    // add x label at bottom of marker
	    var graph_x = cursor_x/graph.x_scale + graph.x_min;
	    c.font = '10pt sans-serif';
	    c.textAlign = 'center';
	    c.textBaseline = 'top';
	    c.fillStyle = background_style;
	    c.fillText('\u2588\u2588\u2588\u2588\u2588',x,end_y);
	    c.fillStyle = normal_style;
	    c.fillText(engineering_notation(graph_x,3,false),x,end_y);

	    // compute which points marker is between
	    var x_values = graph.x_values;
	    var len = x_values.length;
	    var index = 0;
	    while (index < len && graph_x >= x_values[index]) index += 1;
	    var x1 = (index == 0) ? x_values[0] : x_values[index-1];
	    var x2 = x_values[index];

	    if (x2 != undefined) {
		// for each plot, interpolate and output value at intersection with marker
		c.textAlign = 'left';
		var tx = graph.left_margin + left_margin;
		var ty = graph.top_margin;
		if (graph.y_values != undefined) {
		    for (var plot = 0; plot < graph.y_values.length; plot++) {
			var values = graph.y_values[plot][2];
			var color = probe_colors_rgb[graph.y_values[plot][0]];
			if (values == undefined || color == undefined) continue;  // no data points or x-axis
		    
			// interpolate signal value at graph_x using values[index-1] and values[index]
			var y1 = (index == 0) ? values[0] : values[index-1];
			var y2 = values[index];
			var y = y1;
			if (graph_x != x1) y += (graph_x - x1)*(y2 - y1)/(x2 - x1);
		    
			// annotate plot with value of signal at marker
			c.fillStyle = element_style;
			c.fillText('\u2588\u2588\u2588\u2588\u2588',tx-3,ty);
			c.fillStyle = color;
			c.fillText(engineering_notation(y,3,false),tx,ty);
			ty += 14;
		    }
		}

		c.textAlign = 'right';
		if (graph.z_values != undefined) {
		    var tx = graph.left_margin + graph.pwidth - left_margin;
		    var ty = graph.top_margin;
		    for (var plot = 0; plot < graph.z_values.length; plot++) {
			var values = graph.z_values[plot][2];
			var color = probe_colors_rgb[graph.z_values[plot][0]];
			if (values == undefined || color == undefined) continue;  // no data points or x-axis
		    
			// interpolate signal value at graph_x using values[index-1] and values[index]
			var z1 = (index == 0) ? values[0]: values[index-1];
			var z2 = values[index];
			var z = z1;
			if (graph_x != x1) z += (graph_x - x1)*(z2 - z1)/(x2 - x1);
		    
			// annotate plot with value of signal at marker
			c.fillStyle = element_style;
			c.fillText('\u2588\u2588\u2588\u2588\u2588',tx+3,ty);
			c.fillStyle = color;
			c.fillText(engineering_notation(z,3,false),tx,ty);
			ty += 14;
		    }
		}
	    }
	}

	function redraw_plot(graph) {
	    var c = graph.getContext('2d');
	    c.drawImage(graph.bg_image,0,0);

	    if (graph.cursor1_x != undefined) plot_cursor(c,graph,graph.cursor1_x,4);
	    if (graph.cursor2_x != undefined) plot_cursor(c,graph,graph.cursor2_x,30);

	    /*
	    if (graph.cursor1_x != undefined) {
		// draw dashed vertical marker that follows mouse
		var x = graph.left_margin + graph.cursor1_x;
		var end_y = graph.top_margin + graph.pheight + graph.tick_length;
		c.strokeStyle = grid_style;
		c.lineWidth = 1;
		c.beginPath();
		c.dashedLineTo(x,graph.top_margin,x,end_y,cursor_pattern);
		c.stroke();

		// add x label at bottom of marker
		var graph_x = graph.cursor1_x/graph.x_scale + graph.x_min;
		c.font = '10pt sans-serif';
		c.textAlign = 'center';
		c.textBaseline = 'top';
		c.fillStyle = background_style;
		c.fillText('\u2588\u2588\u2588\u2588\u2588',x,end_y);
		c.fillStyle = normal_style;
		c.fillText(engineering_notation(graph_x,3,false),x,end_y);

		// compute which points marker is between
		var x_values = graph.x_values;
		var len = x_values.length;
		var index = 0;
		while (index < len && graph_x >= x_values[index]) index += 1;
		var x1 = (index == 0) ? x_values[0] : x_values[index-1];
		var x2 = x_values[index];

		if (x2 != undefined) {
		    // for each plot, interpolate and output value at intersection with marker
		    c.textAlign = 'left';
		    var tx = graph.left_margin + 4;
		    var ty = graph.top_margin;
		    for (var plot = 0; plot < graph.y_values.length; plot++) {
			var values = graph.y_values[plot][1];

			// interpolate signal value at graph_x using values[index-1] and values[index]
			var y1 = (index == 0) ? values[0] : values[index-1];
			var y2 = values[index];
			var y = y1;
			if (graph_x != x1) y += (graph_x - x1)*(y2 - y1)/(x2 - x1);

			// annotate plot with value of signal at marker
			c.fillStyle = element_style;
			c.fillText('\u2588\u2588\u2588\u2588\u2588',tx-3,ty);
			c.fillStyle = probe_colors_rgb[graph.y_values[plot][0]];
			c.fillText(engineering_notation(y,3,false),tx,ty);
			ty += 14;
		    }
		}
	    }
	    */
	}

	function graph_mouse_move(event) {
	    if (!event) event = window.event;
	    var g = (window.event) ? event.srcElement : event.target;

	    g.relMouseCoords(event);
	    // not sure yet where the 3,-3 offset correction comes from (borders? padding?)
	    var gx = g.mouse_x - g.left_margin - 3;
	    var gy = g.pheight - (g.mouse_y - g.top_margin) + 3;
	    if (gx >= 0 && gx <= g.pwidth && gy >=0 && gy <= g.pheight) {
		//g.sch.message('button: '+event.button+', which: '+event.which);
		g.cursor1_x = gx;
	    } else {
		g.cursor1_x = undefined;
		g.cursor2_x = undefined;
	    }

	    redraw_plot(g);
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Parts bin
	//
	////////////////////////////////////////////////////////////////////////////////

	// one instance will be created for each part in the parts bin
	function Part(sch) {
	    this.sch = sch;
	    this.component = undefined;
	    this.selected = false;

	    // set up canvas
	    this.canvas = document.createElement('canvas');
	    this.canvas.style.borderStyle = 'solid';
	    this.canvas.style.borderWidth = '1px';
	    this.canvas.style.borderColor = background_style;
	    //this.canvas.style.position = 'absolute';
	    this.canvas.style.cursor = 'default';
	    this.canvas.height = part_w;
	    this.canvas.width = part_h;
	    this.canvas.part = this;

	    this.canvas.addEventListener('mouseover',part_enter,false);
	    this.canvas.addEventListener('mouseout',part_leave,false);
	    this.canvas.addEventListener('mousedown',part_mouse_down,false);
	    this.canvas.addEventListener('mouseup',part_mouse_up,false);

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

	Part.prototype.set_component = function(component,tip) {
	    component.sch = this;
	    this.component = component;
	    this.tip = tip;

	    // figure out scaling and centering of parts icon
	    var b = component.bounding_box;
	    var dx = b[2] - b[0];
	    var dy = b[3] - b[1];
	    this.scale = 0.8; //Math.min(part_w/(1.2*dx),part_h/(1.2*dy));
	    this.origin_x = b[0] + dx/2.0 - part_w/(2.0*this.scale);
	    this.origin_y = b[1] + dy/2.0 - part_h/(2.0*this.scale);

	    this.redraw();
	}

	Part.prototype.redraw = function(part) {
	    var c = this.canvas.getContext('2d');

	    // paint background color
	    c.fillStyle = this.selected ? selected_style : background_style;
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

	Part.prototype.moveTo = function(c,x,y) {
	    c.moveTo((x - this.origin_x) * this.scale,(y - this.origin_y) * this.scale);
	}

	Part.prototype.lineTo = function(c,x,y) {
	    c.lineTo((x - this.origin_x) * this.scale,(y - this.origin_y) * this.scale);
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

	function part_enter(event) {
	    if (!event) event = window.event;
	    var canvas = (window.event) ? event.srcElement : event.target;
	    var part = canvas.part;

	    // avoid Chrome bug that changes to text cursor whenever
	    // drag starts.  We'll restore the default handler at
	    // the appropriate point so behavior in other parts of
	    // the document are unaffected.
	    //part.sch.saved_onselectstart = document.onselectstart;
	    //document.onselectstart = function () { return false; };

	    canvas.style.borderColor = normal_style;
	    part.sch.message(part.tip+': drag onto diagram to insert');
	    return false;
	}

	function part_leave(event) {
	    if (!event) event = window.event;
	    var canvas = (window.event) ? event.srcElement : event.target;
	    var part = canvas.part;

	    if (typeof part.sch.new_part == 'undefined') {
		// leaving with no part selected?  revert handler
		//document.onselectstart = part.sch.saved_onselectstart;
	    }

	    canvas.style.borderColor = background_style;
	    part.sch.message('');
	    return false;
	}

	function part_mouse_down(event) {
	    if (!event) event = window.event;
	    var part = (window.event) ? event.srcElement.part : event.target.part;

	    part.select(true);
	    part.sch.new_part = part;
	    return false;
	}

	function part_mouse_up(event) {
	    if (!event) event = window.event;
	    var part = (window.event) ? event.srcElement.part : event.target.part;

	    part.select(false);
	    part.sch.new_part = undefined;
	    return false;
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

	function Component(type,x,y,rotation) {
	    this.sch = undefined;
	    this.type = type;
	    this.x = x;
	    this.y = y;
	    this.rotation = rotation;
	    this.selected = false;
	    this.properties = new Array();
	    this.bounding_box = [0,0,0,0];   // in device coords [left,top,right,bottom]
	    this.bbox = this.bounding_box;   // in absolute coords
	    this.connections = [];
	}

	Component.prototype.json = function(index) {
	    this.properties['_json_'] = index; // remember where we are in the JSON list

	    var props = {};
	    for (var p in this.properties) props[p] = this.properties[p];

	    var conns = [];
	    for (var i = 0; i < this.connections.length; i++)
		conns.push(this.connections[i].json());

	    var json = [this.type,[this.x, this.y, this.rotation],props,conns];
	    return json;
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

	Component.prototype.add = function(sch) {
	    this.sch = sch;   // we now belong to a schematic!
	    sch.add_component(this);
	    this.update_coords();
	}

	Component.prototype.remove = function() {
	    // remove connection points from schematic
	    for (var i = this.connections.length - 1; i >= 0; --i) {
		var cp = this.connections[i];
		this.sch.remove_connection_point(cp,cp.location);
	    }

	    // remove component from schematic
	    this.sch.remove_component(this);
	    this.sch = undefined;

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

	Component.prototype.moveTo = function(c,x,y) {
	    var nx = this.transform_x(x,y) + this.x;
	    var ny = this.transform_y(x,y) + this.y;
	    this.sch.moveTo(c,nx,ny);
	}

	Component.prototype.lineTo = function(c,x,y) {
	    var nx = this.transform_x(x,y) + this.x;
	    var ny = this.transform_y(x,y) + this.y;
	    this.sch.lineTo(c,nx,ny);
	}

	Component.prototype.draw_line = function(c,x1,y1,x2,y2) {
	    c.strokeStyle = this.selected ? selected_style :
                            this.type == 'w' ? normal_style : component_style;
	    var nx1 = this.transform_x(x1,y1) + this.x;
	    var ny1 = this.transform_y(x1,y1) + this.y;
	    var nx2 = this.transform_x(x2,y2) + this.x;
	    var ny2 = this.transform_y(x2,y2) + this.y;
	    this.sch.draw_line(c,nx1,ny1,nx2,ny2,1);
	}

	Component.prototype.draw_circle = function(c,x,y,radius,filled) {
	    if (filled) c.fillStyle = this.selected ? selected_style : normal_style;
	    else c.strokeStyle = this.selected ? selected_style :
		     this.type == 'w' ? normal_style : component_style;
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
	    c.strokeStyle = this.selected ? selected_style :
                            this.type == 'w' ? normal_style : component_style;
	    var nx = this.transform_x(x,y) + this.x;
	    var ny = this.transform_y(x,y) + this.y;
	    this.sch.draw_arc(c,nx,ny,radius,
			      start_radians+rot_angle[this.rotation],end_radians+rot_angle[this.rotation],
			      false,1,false);
	}

	Component.prototype.draw = function(c) {
	    /*
	    for (var i = this.connections.length - 1; i >= 0; --i) {
		var cp = this.connections[i];
		cp.draw_x(c);
	    }
	    */
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

	Component.prototype.draw_text = function(c,text,x,y,alignment,size,fill) {
	    var a = aOrient[this.rotation*9 + alignment];
	    c.textAlign = textAlign[a];
	    c.textBaseline = textBaseline[a];
	    if (fill == undefined)
		c.fillStyle = this.selected ? selected_style : normal_style;
	    else
		c.fillStyle = fill;
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
	    if (this.near(x,y)) {
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

	// does mouse click fall on this component?
	Component.prototype.near = function(x,y) {
	    return inside(this.bbox,x,y);
	}

	Component.prototype.edit_properties = function(x,y) {
	    if (this.near(x,y)) {
		// make an <input> widget for each property
		var fields = new Array();
		for (var i in this.properties)
		    // underscore at beginning of property name => system property
		    if (i.charAt(0) != '_')
			fields[i] = build_input('text',10,this.properties[i]);

		var content = build_table(fields);
		content.fields = fields;
		content.component = this;

		this.sch.dialog('Edit Properties',content,function(content) {
			for (var i in content.fields)
			    content.component.properties[i] = content.fields[i].value;
			content.component.sch.redraw_background();
		    });
		return true;
	    } else return false;
	}

	// clear the labels on all connections
	Component.prototype.clear_labels = function() {
	    for (var i = this.connections.length - 1; i >=0; --i) {
		this.connections[i].clear_label();
	    }
	}

	// default action: don't propagate label
	Component.prototype.propagate_label = function(label) {
	}

	// give components a chance to generate default labels for their connection(s)
	// default action: do nothing
	Component.prototype.add_default_labels = function() {
	}

	// component should generate labels for all unlabeled connections
	Component.prototype.label_connections = function() {
	    for (var i = this.connections.length - 1; i >=0; --i) {
		var cp = this.connections[i];
		if (!cp.label)
		    cp.propagate_label(this.sch.get_next_label());
	    }
	}

	// default behavior: no probe info
	Component.prototype.probe_info = function() { return undefined; }

	// default behavior: nothing to display for DC analysis
	Component.prototype.display_current = function(c,vmap) {
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
	    this.label = undefined;
	}

	ConnectionPoint.prototype.toString = function() {
	    return '<ConnectionPoint ('+this.offset_x+','+this.offset_y+') '+this.parent.toString()+'>';
	}

	ConnectionPoint.prototype.json = function() {
	    return this.label;
	}

	ConnectionPoint.prototype.clear_label = function() {
	    this.label = undefined;
	}

	ConnectionPoint.prototype.propagate_label = function(label) {
	    // should we check if existing label is the same?  it should be...

	    if (this.label === undefined) {
		// label this connection point
		this.label = label;

		// propagate label to coincident connection points
		this.parent.sch.propagate_label(label,this.location);

		// possibly label other cp's for this device?
		this.parent.propagate_label(label);
	    } else if (this.label != '0' && label != '0' && this.label != label)
		alert("Node has two conflicting labels: "+this.label+", "+label);
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
	    if (parent.sch) 
		parent.sch.update_connection_point(this,old_location);
	}

	ConnectionPoint.prototype.coincident = function(x,y) {
	    return this.x==x && this.y==y;
	}

	ConnectionPoint.prototype.draw = function(c,n) {
	    if (n != 2)
		this.parent.draw_circle(c,this.offset_x,this.offset_y,connection_point_radius,n > 2);
	}

	ConnectionPoint.prototype.draw_x = function(c) {
	    this.parent.draw_line(c,this.offset_x-2,this.offset_y-2,this.offset_x+2,this.offset_y+2,grid_style);
	    this.parent.draw_line(c,this.offset_x+2,this.offset_y-2,this.offset_x-2,this.offset_y+2,grid_style);
	}

	ConnectionPoint.prototype.display_voltage = function(c,vmap) {
	    var v = vmap[this.label];
	    if (v != undefined) {
		var label = v.toFixed(2) + 'V';
		
		// first draw some solid blocks in the background
		c.globalAlpha = 0.85;
		this.parent.draw_text(c,'\u2588\u2588\u2588',this.offset_x,this.offset_y,
				      4,annotation_size,element_style);
		c.globalAlpha = 1.0;

		// display the node voltage at this connection point
		this.parent.draw_text(c,label,this.offset_x,this.offset_y,
				      4,annotation_size,annotation_style);

		// only display each node voltage once
		delete vmap[this.label];
	    }
	}

	// see if three connection points are collinear
	function collinear(p1,p2,p3) {
	    // from http://mathworld.wolfram.com/Collinear.html
	    var area = p1.x*(p2.y - p3.y) + p2.x*(p3.y - p1.y) + p3.x*(p1.y - p2.y);
	    return area == 0;
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Wire
	//
	////////////////////////////////////////////////////////////////////////////////

	near_distance = 2;   // how close to wire counts as "near by"

	function Wire(x1,y1,x2,y2) {
	    // arbitrarily call x1,y1 the origin
	    Component.call(this,'w',x1,y1,0);
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
    
	// return connection point at other end of wire from specified cp
	Wire.prototype.other_end = function(cp) {
	    if (cp == this.connections[0]) return this.connections[1];
	    else if (cp == this.connections[1]) return this.connections[0];
	    else return undefined;
	}

	Wire.prototype.json = function(index) {
	    var json = ['w',[this.x, this.y, this.x+this.dx, this.y+this.dy]];
	    return json;
	}

	Wire.prototype.draw = function(c) {
	    this.draw_line(c,0,0,this.dx,this.dy);
	}

	Wire.prototype.clone = function(x,y) {
	    return new Wire(x,y,x+this.dx,y+this.dy);
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

	// selection rectangle selects wire only if it includes
	// one of the end points
	Wire.prototype.select_rect = function(s) {
	    this.was_previously_selected = this.selected;
	    if (inside(s,this.x,this.y) || inside(s,this.x+this.dx,this.y+this.dy))
		this.set_select(true);
	}

	// if connection point cp bisects the
	// wire represented by this compononent, return true
	Wire.prototype.bisect_cp = function(cp) {
	    var x = cp.x;
	    var y = cp.y;

	    // crude check: (x,y) within expanded bounding box of wire
	    if (inside(this.bbox,x,y)) {
		// compute distance between x,y and nearst point on line
		// http://www.allegro.cc/forums/thread/589720
		var D = Math.abs((x - this.x)*this.dy - (y - this.y)*this.dx)/this.len;
		// final check: ensure point isn't an end point of the wire
		if (D < 1 && !this.connections[0].coincident(x,y) && !this.connections[1].coincident(x,y))
		    return true;
	    }
	    return false;
	}

	// if some connection point of component c bisects the
	// wire represented by this compononent, return that
	// connection point.  Otherwise return null.
	Wire.prototype.bisect = function(c) {
	    if (c == undefined) return;
	    for (var i = c.connections.length - 1; i >= 0; --i) {
		var cp = c.connections[i];
		if (this.bisect_cp(cp)) return cp;
	    }
	    return null;
	}

	Wire.prototype.move_end = function() {
	    // look for wires bisected by this wire
	    this.sch.check_wires(this);

	    // look for connection points that might bisect us
	    this.sch.check_connection_points(this);
	}

	// wires "conduct" their label to the other end
	Wire.prototype.propagate_label = function(label) {
	    // don't worry about relabeling a cp, it won't recurse!
	    this.connections[0].propagate_label(label);
	    this.connections[1].propagate_label(label);
	}

	// Wires have no properties to edit
	Wire.prototype.edit_properties = function(x,y) {
	    return false;
	}

	// some actual component will start the labeling of electrical nodes,
	// so do nothing here
	Wire.prototype.label_connections = function() {
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Ground
	//
	////////////////////////////////////////////////////////////////////////////////

	function Ground(x,y,rotation) {
	    Component.call(this,'g',x,y,rotation);
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
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,8);
	    this.draw_line(c,-6,8,6,8);
	}

	Ground.prototype.clone = function(x,y) {
	    return new Ground(x,y,this.rotation);
	}

	// Grounds no properties to edit
	Ground.prototype.edit_properties = function(x,y) {
	    return false;
	}

	// give components a chance to generate a label for their connection(s)
	// default action: do nothing
	Ground.prototype.add_default_labels = function() {
	    this.connections[0].propagate_label('0');   // canonical label for GND node
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Label
	//
	////////////////////////////////////////////////////////////////////////////////

	function Label(x,y,rotation,label) {
	    Component.call(this,'L',x,y,rotation);
	    this.properties['label'] = label ? label : '???';
	    this.add_connection(0,0);
	    this.bounding_box = [-2,0,2,8];
	    this.update_coords();
	}
	Label.prototype = new Component();
	Label.prototype.constructor = Label;

	Label.prototype.toString = function() {
	    return '<Label'+' ('+this.x+','+this.y+')>';
	}
    
	Label.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,8);
	    this.draw_text(c,this.properties['label'],0,9,1,property_size);
	}

	Label.prototype.clone = function(x,y) {
	    return new Label(x,y,this.rotation,this.properties['label']);
	}

	// give components a chance to generate a label for their connection(s)
	// default action: do nothing
	Label.prototype.add_default_labels = function() {
	    this.connections[0].propagate_label(this.properties['label']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Voltage Probe
	//
	////////////////////////////////////////////////////////////////////////////////

	probe_colors = ['red','green','blue','cyan','magenta','yellow','black','x-axis'];
	probe_colors_rgb = {
	    'red': 'rgb(255,64,64)',
	    'green': 'rgb(64,255,64)',
	    'blue': 'rgb(64,64,255)',
	    'cyan': 'rgb(64,255,255)',
	    'magenta' : 'rgb(255,64,255)',
	    'yellow': 'rgb(255,255,64)',
	    'black': 'rgb(0,0,0)',
	    'x-axis': undefined,
	};

	function Probe(x,y,rotation,color,offset) {
	    Component.call(this,'s',x,y,rotation);
	    this.add_connection(0,0);
	    this.properties['color'] = color ? color : 'cyan';
	    this.properties['offset'] = (offset==undefined || offset=='') ? '0' : offset;
	    this.bounding_box = [0,0,27,-21];
	    this.update_coords();
	}
	Probe.prototype = new Component();
	Probe.prototype.constructor = Probe;

	Probe.prototype.toString = function() {
	    return '<Probe ('+this.x+','+this.y+')>';
	}
    
	Probe.prototype.draw = function(c) {
	    // draw outline
	    this.draw_line(c,0,0,4,-4);
	    this.draw_line(c,2,-6,6,-2);
	    this.draw_line(c,2,-6,17,-21);
	    this.draw_line(c,6,-2,21,-17);
	    this.draw_line(c,17,-21,21,-17);
	    this.draw_arc(c,19,-11,8,3*Math.PI/2,0);

	    // fill body with plot color
	    var color = probe_colors_rgb[this.properties['color']];
	    if (color != undefined) {
		c.fillStyle = color;
		c.beginPath();
		this.moveTo(c,2,-6);
		this.lineTo(c,6,-2);
		this.lineTo(c,21,-17);
		this.lineTo(c,17,-21);
		this.lineTo(c,2,-6);
		c.fill();
	    } else {
		this.draw_text(c,this.properties['color'],27,-11,1,property_size);
	    }
	}

	Probe.prototype.clone = function(x,y) {
	    return new Probe(x,y,this.rotation,this.properties['color'],this.properties['offset']);
	}

	Probe.prototype.edit_properties = function(x,y) {
	    if (inside(this.bbox,x,y)) {
		var fields = new Array();
		fields['Plot color'] = build_select(probe_colors,this.properties['color']);
		fields['Plot offset'] = build_input('text',10,this.properties['offset']);

		var content = build_table(fields);
		content.fields = fields;
		content.component = this;

		this.sch.dialog('Edit Properties',content,function(content) {
			var color_choice = content.fields['Plot color'];
			content.component.properties['color'] = probe_colors[color_choice.selectedIndex];
			content.component.properties['offset'] = content.fields['Plot offset'].value;
			content.component.sch.redraw_background();
		    });
		return true;
	    } else return false;
	}

	// return [color, node_label, offset, type] for this probe
	Probe.prototype.probe_info = function() {
	    var color = this.properties['color'];
	    var offset = this.properties['offset'];
	    if (offset==undefined || offset=="") offset = '0';
	    return [color,this.connections[0].label,offset,'voltage'];
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Ammeter Probe
	//
	////////////////////////////////////////////////////////////////////////////////

	function Ammeter(x,y,rotation,color,offset) {
	    Component.call(this,'a',x,y,rotation);
	    this.add_connection(0,0);   // pos
	    this.add_connection(16,0);   // neg
	    this.properties['color'] = color ? color : 'magenta';
	    this.properties['offset'] = (offset==undefined || offset=='') ? '0' : offset;
	    this.bounding_box = [-3,0,16,3];
	    this.update_coords();
	}
	Ammeter.prototype = new Component();
	Ammeter.prototype.constructor = Ammeter;

	Ammeter.prototype.toString = function() {
	    return '<Ammeter ('+this.x+','+this.y+')>';
	}
    
	Ammeter.prototype.move_end = function() {
	    Component.prototype.move_end.call(this);   // do the normal processing

	    // special for current probes: see if probe has been placed
	    // in the middle of wire, creating three wire segments one
	    // of which is shorting the two terminals of the probe.  If
	    // so, auto remove the shorting segment.
	    var e1 = this.connections[0].location;
	    var e2 = this.connections[1].location;
	    var cplist = this.sch.find_connections(this.connections[0]);
	    for (var i = cplist.length - 1; i >= 0; --i) {
		var c = cplist[i].parent;  // a component connected to ammeter terminal
		// look for a wire whose end points match those of the ammeter
		if (c.type == 'w') {
		    var c_e1 = c.connections[0].location;
		    var c_e2 = c.connections[1].location;
		    if ((e1 == c_e1 && c2 == c_e2) || (e1 == c_e2 && e2 == c_e1)) {
			c.remove();
			break;
		    }
		}
	    }
	}

	Ammeter.prototype.draw = function(c) {
	    this.draw_line(c,0,0,16,0);

	    // draw chevron in probe color
	    c.strokeStyle = probe_colors_rgb[this.properties['color']];
	    if (c.strokeStyle != undefined) {
		c.beginPath();
		this.moveTo(c,6,-3);
		this.lineTo(c,10,0);
		this.lineTo(c,6,3);
		c.stroke();
	    }
	}

	Ammeter.prototype.clone = function(x,y) {
	    return new Ammeter(x,y,this.rotation,this.properties['color'],this.properties['offset']);
	}

	// share code with voltage probe
	Ammeter.prototype.edit_properties = Probe.prototype.edit_properties;

	Ammeter.prototype.label = function() {
	    var name = this.properties['name'];
	    var label = 'I(' + (name ? name : '_' + this.properties['_json_']) + ')';
	    return label;
	}

	// display current for DC analysis
	Ammeter.prototype.display_current = function(c,vmap) {
	    var label = this.label();
	    var v = vmap[label];
	    if (v != undefined) {
		var i = engineering_notation(v,2) + 'A';
		this.draw_text(c,i,8,-5,7,annotation_size,annotation_style);

		// only display each current once
		delete vmap[label];
	    }
	}

	// return [color, current_label, offset, type] for this probe
	Ammeter.prototype.probe_info = function() {
	    var color = this.properties['color'];
	    var offset = this.properties['offset'];
	    if (offset==undefined || offset=="") offset = '0';
	    return [color,this.label(),offset,'current'];
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Resistor
	//
	////////////////////////////////////////////////////////////////////////////////

	function Resistor(x,y,rotation,name,r) {
	    Component.call(this,'r',x,y,rotation);
	    this.properties['name'] = name;
	    this.properties['r'] = r ? r : '1';
	    this.add_connection(0,0);
	    this.add_connection(0,48);
	    this.bounding_box = [-5,0,5,48];
	    this.update_coords();
	}
	Resistor.prototype = new Component();
	Resistor.prototype.constructor = Resistor;

	Resistor.prototype.toString = function() {
	    return '<Resistor '+this.properties['r']+' ('+this.x+','+this.y+')>';
	}
    
	Resistor.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
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

	Resistor.prototype.clone = function(x,y) {
	    return new Resistor(x,y,this.rotation,this.properties['name'],this.properties['r']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Capacitor
	//
	////////////////////////////////////////////////////////////////////////////////

	function Capacitor(x,y,rotation,name,c) {
	    Component.call(this,'c',x,y,rotation);
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
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,22);
	    this.draw_line(c,-8,22,8,22);
	    this.draw_line(c,-8,26,8,26);
	    this.draw_line(c,0,26,0,48);
	    if (this.properties['c'])
		this.draw_text(c,this.properties['c']+'F',9,24,3,property_size);
	    if (this.properties['name'])
		this.draw_text(c,this.properties['name'],-9,24,5,property_size);
	}

	Capacitor.prototype.clone = function(x,y) {
	    return new Capacitor(x,y,this.rotation,this.properties['name'],this.properties['c']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Inductor
	//
	////////////////////////////////////////////////////////////////////////////////

	function Inductor(x,y,rotation,name,l) {
	    Component.call(this,'l',x,y,rotation);
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
	    Component.prototype.draw.call(this,c);   // give superclass a shot
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

	Inductor.prototype.clone = function(x,y) {
	    return new Inductor(x,y,this.rotation,this.properties['name'],this.properties['l']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Diode
	//
	////////////////////////////////////////////////////////////////////////////////

	diode_types = ['normal','ideal'];

	function Diode(x,y,rotation,name,area,type) {
	    Component.call(this,'d',x,y,rotation);
	    this.properties['name'] = name;
	    this.properties['area'] = area ? area : '1';
	    this.properties['type'] = type ? type : 'normal';
	    this.add_connection(0,0);   // anode
	    this.add_connection(0,48);  // cathode
	    this.bounding_box = (type == 'ideal') ? [-12,0,12,48] : [-8,0,8,48];
	    this.update_coords();
	}
	Diode.prototype = new Component();
	Diode.prototype.constructor = Diode;

	Diode.prototype.toString = function() {
	    return '<Diode '+this.properties['area']+' ('+this.x+','+this.y+')>';
	}
    
	Diode.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,16);
	    this.draw_line(c,-8,16,8,16);
	    this.draw_line(c,-8,16,0,32);
	    this.draw_line(c,8,16,0,32);
	    this.draw_line(c,-8,32,8,32);
	    this.draw_line(c,0,32,0,48);

	    if (this.properties['type'] == 'ideal') {
		// put a box around an ideal diode
		this.draw_line(c,-10,12,10,12);
		this.draw_line(c,-10,12,-10,36);
		this.draw_line(c,10,12,10,36);
		this.draw_line(c,-10,36,10,36);
	    }

	    if (this.properties['area'])
		this.draw_text(c,this.properties['area'],10,24,3,property_size);
	    if (this.properties['name'])
		this.draw_text(c,this.properties['name'],-10,24,5,property_size);
	}

	Diode.prototype.clone = function(x,y) {
	    return new Diode(x,y,this.rotation,this.properties['name'],this.properties['area'],this.properties['type']);
	}

	Diode.prototype.edit_properties = function(x,y) {
	    if (inside(this.bbox,x,y)) {
		var fields = new Array();
		fields['name'] = build_input('text',10,this.properties['name']);
		fields['area'] = build_input('text',10,this.properties['area']);
		fields['type'] = build_select(diode_types,this.properties['type']);

		var content = build_table(fields);
		content.fields = fields;
		content.component = this;

		this.sch.dialog('Edit Properties',content,function(content) {
			content.component.properties['name'] = content.fields['name'].value;
			content.component.properties['area'] = content.fields['area'].value;
			content.component.properties['type'] = diode_types[content.fields['type'].selectedIndex];
			content.component.sch.redraw_background();
		    });
		return true;
	    } else return false;
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  N-channel Mosfet
	//
	////////////////////////////////////////////////////////////////////////////////

	function NFet(x,y,rotation,name,w_over_l) {
	    Component.call(this,'n',x,y,rotation);
	    this.properties['name'] = name;
	    this.properties['W/L'] = w_over_l ? w_over_l : '2';
	    this.add_connection(0,0);   // drain
	    this.add_connection(-24,24);  // gate
	    this.add_connection(0,48);  // source
	    this.bounding_box = [-24,0,8,48];
	    this.update_coords();
	}
	NFet.prototype = new Component();
	NFet.prototype.constructor = NFet;

	NFet.prototype.toString = function() {
	    return '<NFet '+this.properties['W/L']+' ('+this.x+','+this.y+')>';
	}
    
	NFet.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,16);
	    this.draw_line(c,-8,16,0,16);
	    this.draw_line(c,-8,16,-8,32);
	    this.draw_line(c,-8,32,0,32);
	    this.draw_line(c,0,32,0,48);

	    this.draw_line(c,-24,24,-12,24);
	    this.draw_line(c,-12,16,-12,32);

	    var dim = this.properties['W/L'];
	    if (this.properties['name']) {
		this.draw_text(c,this.properties['name'],2,22,6,property_size);
		this.draw_text(c,dim,2,26,0,property_size);
	    } else
		this.draw_text(c,dim,2,24,3,property_size);
	}

	NFet.prototype.clone = function(x,y) {
	    return new NFet(x,y,this.rotation,this.properties['name'],this.properties['W/L']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  P-channel Mosfet
	//
	////////////////////////////////////////////////////////////////////////////////

	function PFet(x,y,rotation,name,w_over_l) {
	    Component.call(this,'p',x,y,rotation);
	    this.properties['name'] = name;
	    this.properties['W/L'] = w_over_l ? w_over_l : '2';
	    this.add_connection(0,0);   // drain
	    this.add_connection(-24,24);  // gate
	    this.add_connection(0,48);  // source
	    this.bounding_box = [-24,0,8,48];
	    this.update_coords();
	}
	PFet.prototype = new Component();
	PFet.prototype.constructor = PFet;

	PFet.prototype.toString = function() {
	    return '<PFet '+this.properties['W/L']+' ('+this.x+','+this.y+')>';
	}
    
	PFet.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,16);
	    this.draw_line(c,-8,16,0,16);
	    this.draw_line(c,-8,16,-8,32);
	    this.draw_line(c,-8,32,0,32);
	    this.draw_line(c,0,32,0,48);

	    this.draw_line(c,-24,24,-16,24);

	    this.draw_circle(c,-14,24,2,false);
	    this.draw_line(c,-12,16,-12,32);

	    var dim = this.properties['W/L'];
	    if (this.properties['name']) {
		this.draw_text(c,this.properties['name'],2,22,6,property_size);
		this.draw_text(c,dim,2,26,0,property_size);
	    } else
		this.draw_text(c,dim,2,24,3,property_size);
	}

	PFet.prototype.clone = function(x,y) {
	    return new PFet(x,y,this.rotation,this.properties['name'],this.properties['W/L']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Op Amp
	//
	////////////////////////////////////////////////////////////////////////////////

	function OpAmp(x,y,rotation,name,A) {
	    Component.call(this,'o',x,y,rotation);
	    this.properties['name'] = name;
	    this.properties['A'] = A ? A : '30000';
	    this.add_connection(0,0);   // +
	    this.add_connection(0,16);  // -
	    this.add_connection(48,8);  // output
	    this.add_connection(24,32);  // ground
	    this.bounding_box = [0,-8,48,32];
	    this.update_coords();
	}
	OpAmp.prototype = new Component();
	OpAmp.prototype.constructor = OpAmp;

	OpAmp.prototype.toString = function() {
	    return '<OpAmp'+this.properties['A']+' ('+this.x+','+this.y+')>';
	}
    
	OpAmp.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    // triangle
	    this.draw_line(c,8,-8,8,24);
	    this.draw_line(c,8,-8,40,8);
	    this.draw_line(c,8,24,40,8);
	    // inputs and output
	    this.draw_line(c,0,0,8,0);
	    this.draw_line(c,0,16,8,16);
	    this.draw_text(c,'gnd',37,18,property_size);
	    this.draw_line(c,40,8,48,8);
	    this.draw_line(c,24,16,24,32);
	    // + and -
	    this.draw_line(c,10,0,16,0);
	    this.draw_line(c,13,-3,13,3);
	    this.draw_line(c,10,16,16,16);

	    if (this.properties['name'])
		this.draw_text(c,this.properties['name'],32,16,0,property_size);
	}

	OpAmp.prototype.clone = function(x,y) {
	    return new OpAmp(x,y,this.rotation,this.properties['name'],this.properties['A']);
	}

	////////////////////////////////////////////////////////////////////////////////
	//
	//  Source
	//
	////////////////////////////////////////////////////////////////////////////////

	
	function Source(x,y,rotation,name,type,value) {
	    Component.call(this,type,x,y,rotation);
	    this.properties['name'] = name;
	    if (value == undefined) value = 'dc(1)';
	    this.properties['value'] = value;
	    this.add_connection(0,0);
	    this.add_connection(0,48);
	    this.bounding_box = [-12,0,12,48];
	    this.update_coords();

	    this.content = document.createElement('div');  // used by edit_properties
	}
	Source.prototype = new Component();
	Source.prototype.constructor = Source;

	Source.prototype.toString = function() {
	    return '<'+this.type+'source '+this.properties['params']+' ('+this.x+','+this.y+')>';
	}
    
	Source.prototype.draw = function(c) {
	    Component.prototype.draw.call(this,c);   // give superclass a shot
	    this.draw_line(c,0,0,0,12);
	    this.draw_circle(c,0,24,12,false);
	    this.draw_line(c,0,36,0,48);

	    if (this.type == 'v') {  // voltage source
		//this.draw_text(c,'+',0,12,1,property_size);
		//this.draw_text(c,'\u2013',0,36,7,property_size);  // minus sign
		// draw + and -
		this.draw_line(c,0,15,0,21);
		this.draw_line(c,-3,18,3,18);
		this.draw_line(c,-3,30,3,30);
		// draw V
		//this.draw_line(c,-3,20,0,28);
		//this.draw_line(c,3,20,0,28);
	    } else if (this.type == 'i') {  // current source
		// draw arrow: pos to neg
		this.draw_line(c,0,15,0,32);
		this.draw_line(c,-3,26,0,32);
		this.draw_line(c,3,26,0,32);
	    }

	    if (this.properties['name'])
		this.draw_text(c,this.properties['name'],-13,24,5,property_size);
	    if (this.properties['value'])
		this.draw_text(c,this.properties['value'],13,24,3,property_size);
	}

	// map source function name to labels for each source parameter
	source_functions = {
	    'dc': ['DC value'],

	    'impulse': ['Height',
			'Width (secs)'],

	    'step': ['Initial value',
		     'Plateau value',
		     'Delay until step (secs)',
		     'Rise time (secs)'],

	    'square': ['Initial value',
		       'Plateau value',
		       'Frequency (Hz)',
		       'Duty cycle (%)'],

	    'triangle': ['Initial value',
			 'Plateau value',
			 'Frequency (Hz)'],

	    'pwl': ['Comma-separated list of alternating times and values'],

	    'pwl_repeating': ['Comma-separated list of alternating times and values'],

	    'pulse': ['Initial value',
		      'Plateau value',
		      'Delay until pulse (secs)',
		      'Time for first transition (secs)',
		      'Time for second transition (secs)',
		      'Pulse width (secs)',
		      'Period (secs)'],

	    'sin': ['Offset value',
		    'Amplitude',
		    'Frequency (Hz)',
		    'Delay until sin starts (secs)',
		    'Phase offset (degrees)'],
	}

	// build property editor div
	Source.prototype.build_content = function(src) {
	    // make an <input> widget for each property
	    var fields = []
	    fields['name'] = build_input('text',10,this.properties['name']);

	    if (src == undefined) {
		fields['value'] = this.properties['value'];
	    } else {
		// fancy version: add select tag for source type
		var src_types = [];
		for (var t in source_functions) src_types.push(t);
		var type_select = build_select(src_types,src.fun);
		type_select.component = this;
		type_select.addEventListener('change',source_type_changed,false)
		fields['type'] = type_select;

		if (src.fun == 'pwl' || src.run == 'pwl_repeating') {
		    var v = '';
		    var first = true;
		    for (var i = 0; i < src.args.length; i++) {
			if (first) first = false;
			else v += ',';
			v += engineering_notation(src.args[i],3);
			if (i % 2 == 0) v += 's';
		    }
		    fields[source_functions[src.fun][0]] = build_input('text',30,v);
		} else {
		    // followed separate input tag for each parameter
		    var labels = source_functions[src.fun];
		    for (var i = 0; i < labels.length; i++) {
			var v = engineering_notation(src.args[i],3);
			fields[labels[i]] = build_input('text',10,v);
		    }
		}
	    }

	    var div = this.content;
	    if (div.hasChildNodes())
		div.removeChild(div.firstChild);  // remove table of input fields
	    div.appendChild(build_table(fields));
	    div.fields = fields;
	    div.component = this;
	    return div;
	}

	function source_type_changed(event) {
	    if (!event) event = window.event;
	    var select = (window.event) ? event.srcElement : event.target;

	    // see where to get source parameters from
	    var type = select.options[select.selectedIndex].value;
	    var src = undefined;
	    if (this.src != undefined && type == this.src.fun)
		src = this.src;
	    else if (typeof cktsim != 'undefined')
		src = cktsim.parse_source(type+'()');

	    select.component.build_content(src);
	}

	Source.prototype.edit_properties = function(x,y) {
	    if (this.near(x,y)) {
		this.src = undefined;
		if (typeof cktsim != 'undefined')
		    this.src = cktsim.parse_source(this.properties['value']);
		var content = this.build_content(this.src);

		this.sch.dialog('Edit Properties',content,function(content) {
			var c = content.component;
			var fields = content.fields;

			var first = true;
			var value = '';
			for (var label in fields) {
			    if (label == 'name') 
				c.properties['name'] = fields['name'].value;
			    else if (label == 'value')  {
				// if unknown source type
				value = fields['value'].value;
				c.sch.redraw_background();
				return;
			    } else if (label == 'type') {
				var select = fields['type'];
				value = select.options[select.selectedIndex].value + '(';
			    } else {
				if (first) first = false;
				else value += ',';
				value += fields[label].value;
			    }
			}
			c.properties['value'] = value + ')';
			c.sch.redraw_background();
		    });
		return true;
	    } else return false;
	}


	function VSource(x,y,rotation,name,value) {
	    Source.call(this,x,y,rotation,name,'v',value);
	    this.type = 'v';
	}
	VSource.prototype = new Component();
	VSource.prototype.constructor = VSource;
	VSource.prototype.toString = Source.prototype.toString;
	VSource.prototype.draw = Source.prototype.draw;
	VSource.prototype.clone = Source.prototype.clone;
	VSource.prototype.build_content = Source.prototype.build_content;
	VSource.prototype.edit_properties = Source.prototype.edit_properties;

	// display current for DC analysis
	VSource.prototype.display_current = function(c,vmap) {
	    var name = this.properties['name'];
	    var label = 'I(' + (name ? name : '_' + this.properties['_json_']) + ')';
	    var v = vmap[label];
	    if (v != undefined) {
		// first draw some solid blocks in the background
		c.globalAlpha = 0.5;
		this.draw_text(c,'\u2588\u2588\u2588',-8,8,4,annotation_size,element_style);
		c.globalAlpha = 1.0;

		// display the element current 
		var i = engineering_notation(v,2) + 'A';
		this.draw_text(c,i,-3,5,5,annotation_size,annotation_style);
		// draw arrow for current
		this.draw_line(c,-3,4,0,8);
		this.draw_line(c,3,4,0,8);
		// only display each current once
		delete vmap[label];
	    }
	}

	VSource.prototype.clone = function(x,y) {
	    return new VSource(x,y,this.rotation,this.properties['name'],this.properties['value']);
	}

	function ISource(x,y,rotation,name,value) {
	    Source.call(this,x,y,rotation,name,'i',value);
	    this.type = 'i';
	}
	ISource.prototype = new Component();
	ISource.prototype.constructor = ISource;
	ISource.prototype.toString = Source.prototype.toString;
	ISource.prototype.draw = Source.prototype.draw;
	ISource.prototype.clone = Source.prototype.clone;
	ISource.prototype.build_content = Source.prototype.build_content;
	ISource.prototype.edit_properties = Source.prototype.edit_properties;

	ISource.prototype.clone = function(x,y) {
	    return new ISource(x,y,this.rotation,this.properties['name'],this.properties['value']);
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  JQuery slider support for setting a component value
	//
	///////////////////////////////////////////////////////////////////////////////

	function component_slider(event,ui) {
	    var sname = $(this).slider("option","schematic");

	    // set value of specified component
	    var cname = $(this).slider("option","component");
	    var pname = $(this).slider("option","property");
	    var suffix = $(this).slider("option","suffix");
	    if (typeof suffix != "string") suffix = "";

	    var v = ui.value;
	    $(this).slider("value",v);  // move slider's indicator

	    var choices = $(this).slider("option","choices");
	    if (choices instanceof Array) v = choices[v];

	    // selector may match several schematics
	    $("." + sname).each(function(index,element) {
		    element.schematic.set_property(cname,pname,v.toString() + suffix);
		})

	    // perform requested analysis
	    var analysis = $(this).slider("option","analysis");
	    if (analysis == "dc")
		$("." + sname).each(function(index,element) {
			element.schematic.dc_analysis();
		    })

	    return false;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Module definition
	//
	///////////////////////////////////////////////////////////////////////////////

	var module = {
	    'Schematic': Schematic,
	    'component_slider': component_slider,
	}
	return module;
    }());
