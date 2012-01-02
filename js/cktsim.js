//////////////////////////////////////////////////////////////////////////////
//
//  Circuit simulator
//
//////////////////////////////////////////////////////////////////////////////

// Chris Terman, Dec. 2011

// create a circuit for simulation using "new cktsim.Circuit()"

// for modified nodal analysis (MNA) stamps see
// http://books.google.com/books?id=qhHsSlazGrQC&pg=PA44&lpg=PA44&dq=MNA+stamp+inductor&source=bl&ots=ThMq-FmhLo&sig=cTP1ld_fhIJbGPSBXPDbh3Xappk&hl=en&sa=X&ei=6wb-ToecFMHj0QH61-Fs&ved=0CFcQ6AEwAw#v=onepage&q=MNA%20stamp%20inductor&f=false

cktsim = (function() {

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Circuit
	//
	//////////////////////////////////////////////////////////////////////////////

	// types of "nodes" in the linear system
	T_VOLTAGE = 0;
	T_CURRENT = 1;

	function Circuit() {
	    this.node_map = new Array();
	    this.ntypes = [];
	    this.initial_conditions = [];  // ic's for each element

	    this.devices = [];  // list of devices
	    this.device_map = new Array();  // map name -> device
	    this.end_of_timestep = [];   // list of devices to be called at end of each timestep

	    this.finalized = false;
	    this.node_index = -1;

	    // for backward Euler: coeff0 = 1/timestep, coeff1 = 0
	    // for trapezoidal: coeff0 = 2/timestep, coeff1 = 1
	    this.coeff0 = undefined;
	    this.coeff1 = undefined;
	}

	// index of ground node
	Circuit.prototype.gnd_node = function() {
	    return -1;
	}

	// allocate a new node index
	Circuit.prototype.node = function(name,ntype,ic) {
	    this.node_index += 1;
	    if (name) this.node_map[name] = this.node_index;
	    this.ntypes.push(ntype);
	    this.initial_conditions.push(ic);
	    return this.node_index;
	}

	// call to finalize the circuit in preparation for simulation
	Circuit.prototype.finalize = function() {
	    if (!this.finalized) {
		this.finalized = true;
		this.N = this.node_index + 1;  // number of nodes

		// give each device a chance to finalize itself
		for (var i = this.devices.length - 1; i >= 0; --i)
		    this.devices[i].finalize(this);

		// set up augmented matrix and various temp vectors
		this.matrix = new Array(this.N);
		for (var i = this.N - 1; i >= 0; --i)
		    this.matrix[i] = new Array(this.N + 1);
		this.swap = new Array(this.N);  // keep track of row swaps during pivoting
		this.soln = new Array(this.N);  // hold swapped solution
	    }
	}

	// load circuit from JSON netlist (see schematic.js)
	Circuit.prototype.load_netlist = function(netlist) {
	    // set up mapping for ground node always called '0' in JSON netlist
	    this.node_map['0'] = this.gnd_node();

	    // process each component in the JSON netlist (see schematic.js for format)
	    for (var i = netlist.length - 1; i >= 0; --i) {
		var component = netlist[i];
		var type = component[0];

		// ignore wires, ground connections and view info
		if (type == 'view' || type == 'w' || type == 'g') continue;

		var properties = component[2];
		var name = properties['name'];

		// convert node names to circuit indicies
		var connections = component[3];
		for (var j = connections.length - 1; j >= 0; --j) {
		    var node = connections[j];
		    var index = this.node_map[node];
		    if (index == undefined) index = this.node(node,T_VOLTAGE);
		    connections[j] = index;
		}

		// process the component
		if (type == 'r')	// resistor
		    this.r(connections[0],connections[1],properties['r'],name);
		else if (type == 'c')   // capacitor
		    this.c(connections[0],connections[1],properties['c'],name);
		else if (type == 'l')	// inductor
		    this.l(connections[0],connections[1],properties['l'],name);
		else if (type == 'v') 	// voltage source
		    this.v(connections[0],connections[1],properties['value'],name);
		else if (type == 'i') 	// current source
		    this.i(connections[0],connections[1],properties['value'],name);
		else if (type == 'o') 	// op amp
		    this.opamp(connections[0],connections[1],connections[2],properties['A'],name);
		else if (type == 'n') 	// n fet
		    this.fet('n',connections[0],connections[1],connections[2],
			     properties['sw'],properties['sl'],name);
		else if (type == 'p') 	// p fet
		    this.fet('p',connections[0],connections[1],connections[2],
			     properties['sw'],properties['sl'],name);
	    }
	}

	// DC analysis
	Circuit.prototype.dc = function() {
	    this.finalize();

	    // set up equations
	    this.initialize_linear_system();
	    for (var i = this.devices.length - 1; i >= 0; --i)
		this.devices[i].load_dc(this);

	    // solve for operating point
	    var x = solve_linear_system(this.matrix);

	    // create solution dictionary
	    var result = new Array();
	    for (var name in this.node_map) {
		var index = this.node_map[name];
		result[name] = (index == -1) ? 0 : x[index];
	    }
	    return result;
	}

	Circuit.prototype.r = function(n1,n2,v,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof v) == 'string') {
		v = parse_number(v,undefined);
		if (v === undefined) return undefined;
	    }

	    var d;
	    if (v != 0) {
		d = new Resistor(n1,n2,v);
		this.devices.push(d);
		if (name) this.device_map[name] = d;
	    } else return this.v(n1,n2,0,name);   // zero resistance == 0V voltage source
	}

	Circuit.prototype.c = function(n1,n2,v,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof v) == 'string') {
		v = parse_number(v,undefined);
		if (v === undefined) return undefined;
	    }
	    var d = new Capacitor(n1,n2,v);
	    this.devices.push(d);
	    if (name) this.device_map[name] = d;
	    return d;
	}

	Circuit.prototype.l = function(n1,n2,v,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof v) == 'string') {
		v = parse_number(v,undefined);
		if (v === undefined) return undefined;
	    }
	    var branch = this.node(undefined,T_CURRENT);
	    var d = new Inductor(n1,n2,branch,v);
	    this.devices.push(d);
	    if (name) this.device_map[name] = d;
	    return d;
	}

	Circuit.prototype.v = function(n1,n2,v,name) {
	    var branch = this.node(undefined,T_CURRENT);
	    var d = new VSource(n1,n2,branch,v);
	    this.devices.push(d);
	    if (name) this.device_map[name] = d;
	    return d;
	}

	Circuit.prototype.i = function(n1,n2,v,name) {
	    var d = new ISource(n1,n2,v);
	    this.devices.push(d);
	    if (name) this.device_map[name] = d;
	    return d;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Support for creating and solving a system of linear equations
	//
	////////////////////////////////////////////////////////////////////////////////

	// model circuit using a linear system of the form Ax = b where
	//  A is an nxn matrix of conductances and branch voltages
	//  b is an n-element vector of sources
	//  x is an n-element vector of unknowns (node voltages, branch currents)

	// Knowns (A and b) are stored in an augmented matrix M = [A | b]
	// Matrix is stored as an array of arrays: M[row][col].

	// set augmented matrix to zero
	Circuit.prototype.initialize_linear_system = function() {
	    for (var i = this.N - 1; i >= 0; --i) {
		var row = this.matrix[i];
		for (var j = this.N; j >= 0; --j)   // N+1 entries
		    row[j] = 0;
	    }
	}

	// add conductance between two nodes to matrix A.
	// Index of -1 refers to ground node
	Circuit.prototype.add_conductance = function(i,j,g) {
	    if (i >= 0) {
		this.matrix[i][i] += g;
		if (j >= 0) {
		    this.matrix[i][j] -= g;
		    this.matrix[j][i] -= g;
		    this.matrix[j][j] += g;
		}
	    } else if (j >= 0)
		this.matrix[j][j] += g;
	}

	// add individual conductance to A
	Circuit.prototype.add_to_A = function(i,j,v) {
	    if (i >=0 && j >= 0)
		this.matrix[i][j] += v;
	}

	// add source info to vector b
	Circuit.prototype.add_to_b = function(i,v) {
	    if (i >= 0)	this.matrix[i][this.N] += v;
	}

	// solve Ax=b and return vector x given augmented matrix [A | b]
	// Uses Gaussian elimination with partial pivoting
	function solve_linear_system(M) {
	    var N = M.length;      // augmented matrix M has N rows, N+1 columns
	    var temp,i,j;

	    // gaussian elimination
	    for (var col = 0; col < N ; col++) {
		// find pivot: largest abs(v) in this column of remaining rows
		var max_v = Math.abs(M[col][col]);
		var max_col = col;
		for (i = col + 1; i < N; i++) {
		    temp = Math.abs(M[i][col]);
		    if (temp > max_v) { max_v = temp; max_col = i; }
		}

		// if no value found, generate a small conductance to gnd
		// otherwise swap current row with pivot row
		if (max_v == 0) M[col][col] = 1e-10;
		else {
		    temp = M[col];
		    M[col] = M[max_col];
		    M[max_col] = temp;
		}

		// now eliminate this column for all subsequent rows
		for (i = col + 1; i < N; i++) {
		    temp = M[i][col]/M[col][col];   // multiplier we'll use for current row
		    if (temp != 0)
			// subtract current row from row we're working on
			// remember to process b too!
			for (j = col; j <= N; j++) M[i][j] -= M[col][j]*temp;
		}
	    }

	    // matrix is now upper triangular, so solve for elements of x starting
	    // with the last row
	    var x = new Array(N);
	    for (i = N-1; i >= 0; --i) {
		temp = M[i][N];   // grab b[i] from augmented matrix as RHS
		// subtract LHS term from RHS using known x values
		for (j = N-1; j > i; --j) temp -= M[i][j]*x[j];
		// now compute new x value
		x[i] = temp/M[i][i];
	    }

	    // return solution
	    return x;
	}

	// test solution code, expect x = [2,3,-1]
	//M = [[2,1,-1,8],[-3,-1,2,-11],[-2,1,2,-3]];
	//x = solve_linear_system(M);
	//y = 1;  // so we have place to set a breakpoint :)

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Device base class
	//
	////////////////////////////////////////////////////////////////////////////////

	function Device() {
	}

	// complete initial set up of device
	Device.prototype.finalize = function() {
	}

	// reset internal state of the device to initial value
	Device.prototype.reset = function() {
	}

	// load linear system equations for dc analysis
	// (inductors shorted and capacitors opened)
	Device.prototype.load_dc = function(ckt) {
	}

	// load linear system equations for tran analysis
	Device.prototype.load_tran = function(ckt,soln) {
	}

	// load linear system equations for ac analysis:
	// current sources open, voltage sources shorted
	// linear models at operating point for everyone else
	Device.prototype.load_ac = function(ckt) {
	}

	// called with there's an accepted time step
	Device.prototype.end_of_timestep = function(ckt) {
	}

	// return time of next breakpoint for the device
	Device.prototype.breakpoint = function(time) {
	    return undefined;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Parse numbers in engineering notation
	//
	///////////////////////////////////////////////////////////////////////////////

	// convert first character of argument into an integer
	function ord(ch) {
	    return ch.charCodeAt(0);
	}

	// convert string argument to a number, accepting usual notations
	// (hex, octal, binary, decimal, floating point) plus engineering
	// scale factors (eg, 1k = 1000.0 = 1e3).
	// return default if argument couldn't be interpreted as a number
	function parse_number(s,default_v) {
	    s = s.toLowerCase();  // make life simple for ourselves
	    var slen = s.length;
	    var multiplier = 1;
	    var result = 0;
	    var index = 0;

	    // skip leading whitespace
	    while (index < slen && s.charAt(index) <= ' ') index += 1;
	    if (index == slen) return default_v;

	    // check for leading sign
	    if (s.charAt(index) == '-') {
		multiplier = -1;
		index += 1;
	    } else if (s.charAt(index) == '+')
		index += 1;
	    var start = index;   // remember where digits start

	    // if leading digit is 0, check for hex, octal or binary notation
	    if (index >= slen) return default_v;
	    else if (s.charAt(index) == '0') {
		index += 1;
		if (index >= slen) return 0;
		if (s.charAt(index) == 'x') { // hex
		    while (true) {
			index += 1;
			if (index >= slen) break;
			if (s.charAt(index) >= '0' && s.charAt(index) <= '9')
			    result = result*16 + ord(s.charAt(index)) - ord('0');
			else if (s.charAt(index) >= 'a' && s.charAt(index) <= 'f')
			    result = result*16 + ord(s.charAt(index)) - ord('a') + 10;
			else break;
		    }
		    return result*multiplier;
		} else if (s.charAt(index) == 'b') {  // binary
		    while (true) {
			index += 1;
			if (index >= slen) break;
			if (s.charAt(index) >= '0' && s.charAt(index) <= '1')
			    result = result*2 + ord(s.charAt(index)) - ord('0');
			else break;
		    }
		    return result*multiplier;
		} else if (s.charAt(index) != '.') { // octal
		    while (true) {
			if (s.charAt(index) >= '0' && s.charAt(index) <= '7')
			    result = result*8 + ord(s.charAt(index)) - ord('0');
			else break;
			index += 1;
			if (index >= slen) break;
		    }
		    return result*multiplier;
		}
	    }
    
	    // read decimal integer or floating-point number
	    while (true) {
		if (s.charAt(index) >= '0' && s.charAt(index) <= '9')
		    result = result*10 + ord(s.charAt(index)) - ord('0');
		else break;
		index += 1;
		if (index >= slen) break;
	    }

	    // fractional part?
	    if (index < slen && s.charAt(index) == '.') {
		while (true) {
		    index += 1;
		    if (index >= slen) break;
		    if (s.charAt(index) >= '0' && s.charAt(index) <= '9') {
			result = result*10 + ord(s.charAt(index)) - ord('0');
			multiplier *= 0.1;
		    } else break;
		}
	    }

	    // if we haven't seen any digits yet, don't check
	    // for exponents or scale factors
	    if (index == start) return default_v;

	    // type of multiplier determines type of result:
	    // multiplier is a float if we've seen digits past
	    // a decimal point, otherwise it's an int or long.
	    // Up to this point result is an int or long.
	    result *= multiplier;

	    // now check for exponent or engineering scale factor.  If there
	    // is one, result will be a float.
	    if (index < slen) {
		var scale = s.charAt(index);
		index += 1;
		if (scale == 'e') {
		    var exponent = 0;
		    multiplier = 10.0;
		    if (index < slen) {
			if (s.charAt(index) == '+') index += 1;
			else if (s.charAt(index) == '-') {
			    index += 1;
			    multiplier = 0.1;
			}
		    }
		    while (index < slen) {
			if (s.charAt(index) >= '0' && s.charAt(index) <= '9') {
			    exponent = exponent*10 + ord(s.charAt(index)) - ord('0');
			    index += 1;
			} else break;
		    }
		    while (exponent > 0) {
			exponent -= 1;
			result *= multiplier;
		    }
		} else if (scale == 't') result *= 1e12;
		else if (scale == 'g') result *= 1e9;
		else if (scale == 'k') result *= 1e3;
		else if (scale == 'u') result *= 1e-6;
		else if (scale == 'n') result *= 1e-9;
		else if (scale == 'p') result *= 1e-12;
		else if (scale == 'f') result *= 1e-15;
		else if (scale == 'm') {
		    if (index+1 < slen) {
			if (s.charAt(index) == 'e' && s.charAt(index+1) == 'g')
			    result *= 1e6;
			else if (s.charAt(index) == 'i' && s.charAt(index+1) == 'l')
			    result *= 25.4e-6;
		    } else result *= 1e-3;
		} else return default_v;
	    }
	    // ignore any remaining chars, eg, 1kohms returns 1000
	    return result;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Sources
	//
	///////////////////////////////////////////////////////////////////////////////

	// argument is a string describing the source's value:
	//  <value> or dc(<value>)  -- constant value
	//  pulse(<vinit>,<vpulse>,<tdelay>,<trise>,<tfall>,<t_width>,<t_period>)
	//  sin(<voffset>,<vamplitude>,<hz>,<tdelay>,<phase_offset_degrees>)
	//  pwl(<time>,<value>,...)  -- piecewise linear: time,value pairs

	// returns an object with the following attributes:
	//   value(t) -- compute source value at time t
	//   inflection_point(t) -- compute time after t when a time point is needed
	//   dc -- value at time 0

	function parse_source(v) {
	    // generic parser: parse v as either <value> or <fun>(<value>,...)
	    var src = new Object();
	    src.value = function(t) { return 0; }  // overridden below
	    src.inflection_point = function(t) { return undefined; };  // may be overridden below

	    // see if there's a "(" in the description
	    var index = v.indexOf('(');
	    var ch;
	    if (index >= 0) {
		src.fun = v.slice(0,index);   // function name is before the "("
		src.args = [];	// we'll push argument values onto this list
		var end = v.indexOf(')',index);
		if (end == -1) end = v.length;

		index += 1;     // start parsing right after "("
		while (index < end) {
		    // figure out where next argument value starts
		    ch = v.charAt(index);
		    if (ch <= ' ') { index++; continue; }
		    // and where it ends
		    var arg_end = v.indexOf(',',index);
		    if (arg_end == -1) arg_end = end;
		    // parse and save result in our list of arg values
		    src.args.push(parse_number(v.slice(index,arg_end),undefined));
		    index = arg_end + 1;
		}
	    } else {
		src.fun = 'dc';
		src.args = [parse_number(v,0)];
	    }

	    // post-processing for constant sources
	    if (src.fun == 'dc') {
		var value = src.args[0];
		if (value === undefined) value = 0;
		src.value = function(t) { return value; }  // closure
	    }

	    // post-processing for pulsed sources
	    else if (src.fun == 'pulse') {
		var v1 = arg_value(src.args,0,0);  // default init value: 0V
		var v2 = arg_value(src.args,1,1);  // default plateau value: 1V
		var td = Math.min(0,arg_value(src.args,2,0));  // time pulse starts

		var tr = Math.abs(arg_value(src.args,3,1e-9));  // default rise time: 1ns
		var tf = Math.abs(arg_value(src.args,4,1e-9));  // default rise time: 1ns
		var pw = Math.abs(arg_value(src.args,5,1e9));  // default pulse width: "infinite"
		var per = Math.abs(arg_value(src.args,6,1e9));  // default period: "infinite"

		var t1 = td;       // time when v1 -> v2 transition starts
		var t2 = t1 + tr;  // time when v1 -> v2 transition ends
		var t3 = t2 + pw;  // time when v2 -> v1 transition starts
		var t4 = t3 + tf;  // time when v2 -> v1 transition ends

		// return value of source at time t
		src.value = function(t) {	// closure
		    var tmod = Math.fmod(t,per);
		    if (tmod < t1) return v1;
		    else if (tmod < t2) return v1 + (v2-v1)*(tmod-t1)/(t2-t1);
		    else if (tmod < t3) return v2;
		    else if (tmod < t4) return v2 + (v1-v2)*(tmod-t3)/(t4-t3);
		    else return v1;
		}

		// return time of next inflection point after time t
		src.inflection_point = function(t) {	// closure
		    var tstart = per * Math.floor(t/per);
		    var tmod = t - tstart;
		    if (tmod < t1) return tstart + t1;
		    else if (t < t2) return tstart + t2;
		    else if (t < t3) return tstart + t3;
		    else if (t < t4) return tstart + t4;
		    else return tstart + per + t1;
		}
	    }

	    // post-processing for sinusoidal sources
	    else if (src.fun == 'sin') {
		var degrees_to_radians = 2*Math.PI/360.0;
		var voffset = arg_value(src.args,0,0);  // default offset voltage: 0V
		var va = arg_value(src.args,1,1);  // default amplitude: -1V to 1V
		var freq = arg_value(src.args,2,1);  // default frequency: 1Hz
		var td = Math.min(0,arg_value(src.args,3,0));  // default time delay: 0sec
		var phase = arg_value(src.args,4,0);  // default phase offset: 0 degrees

		phase /= 360.0;

		// return value of source at time t
		src.value = function(t) {  // closure
		    if (t < td) return voffset + Math.sin(2*Math.PI*phase);
		    else {
			t -= td;
			return voffset + Math.sin(2*Math.PI*(freq*(t - td) + phase));
		    }
		}

		// return time of next inflection point after time t
		src.inflection_point = function(t) {	// closure
		    if (t < td) return td;
		    else return undefined;
		}
	    }
	
	    // to do:
	    // post-processing for piece-wise linear sources

	    // object has all the necessary info to compute the source value and inflection points
	    src.dc = src.value(0);   // DC value is value at time 0
	    return src;
	}

	// helper function: return args[index] if present, else default_v
	function arg_value(args,index,default_v) {
	    if (index < args.length) {
		var result = args[index];
		if (result === undefined) result = default_v;
		return result;
	    } else return default_v;
	}

	// we need fmod in the Math library!
	Math.fmod = function(numerator,denominator) {
	    var quotient = Math.floor(numerator/denominator);
	    return numerator - quotient*denominator;
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Sources
	//
	///////////////////////////////////////////////////////////////////////////////

	function VSource(npos,nneg,branch,v) {
	    Device.call(this);

	    this.src = parse_source(v);
	    this.npos = npos;
	    this.nneg = nneg;
	    this.branch = branch;
	}
	VSource.prototype = new Device();
	VSource.prototype.construction = VSource;

	// load linear system equations for dc analysis
	VSource.prototype.load_dc = function(ckt,soln) {
	    // MNA stamp for independent voltage source
	    ckt.add_to_A(this.branch,this.npos,1.0);
	    ckt.add_to_A(this.branch,this.nneg,-1.0);
	    ckt.add_to_A(this.npos,this.branch,1.0);
	    ckt.add_to_A(this.nneg,this.branch,-1.0);
	    ckt.add_to_b(this.branch,this.src.value(ckt.time));

	}

	// load linear system equations for tran analysis (just like DC)
	VSource.prototype.load_tran = function(ckt,soln) {
	    this.load_dc(ckt);
	}

	// return time of next breakpoint for the device
	VSource.prototype.breakpoint = function(time) {
	    return this.src.inflection_point(time);
	}

	// small signal model: short circuit
	VSource.prototype.load_ac = function() {
	    // use branch row in matrix to set following constraint on system:
	    // v_pos - v_neg = 0V
	    ckt.add_to_A(this.branch,this.npos,1.0);
	    ckt.add_to_A(this.branch,this.nneg,-1.0);
	    // ckt.add_to_b(this.branch,0);   // adding 0 isn't necessary!
	}

	function ISource(npos,nneg,v) {
	    Device.call(this);

	    this.src = parse_source(v);
	    this.npos = npos;
	    this.nneg = nneg;
	}
	ISource.prototype = new Device();
	ISource.prototype.construction = ISource;

	// load linear system equations for dc analysis
	ISource.prototype.load_dc = function(ckt) {
	    var i = this.src.value(ckt.time);

	    // MNA stamp for independent current source
	    ckt.add_to_b(this.npos,-i);  // current flow into npos
	    ckt.add_to_b(this.nneg,i);   // and out of nneg
	}

	// load linear system equations for tran analysis (just like DC)
	ISource.prototype.load_tran = function(ckt,soln) {
	    this.load_dc(ckt);
	}

	// return time of next breakpoint for the device
	ISource.prototype.breakpoint = function(time) {
	    return this.src.inflection_point(time);
	}

	// small signal model: open circuit
	ISource.prototype.load_ac = function() {
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Resistor
	//
	///////////////////////////////////////////////////////////////////////////////

	function Resistor(n1,n2,v) {
	    Device.call(this);
	    this.n1 = n1;
	    this.n2 = n2;
	    this.g = 1.0/v;
	}
	Resistor.prototype = new Device();
	Resistor.prototype.construction = Resistor;

	Resistor.prototype.load_dc = function(ckt) {
	    // MNA stamp for admittance g
	    ckt.add_conductance(this.n1,this.n2,this.g);
	}

	Resistor.prototype.load_tran = function(ckt,soln) {
	    this.load_dc(ckt);
	}

	Resistor.prototype.load_ac = function(ckt) {
	    this.load_dc(ckt);
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Capacitor
	//
	///////////////////////////////////////////////////////////////////////////////

	function Capacitor(n1,n2,v) {
	    Device.call(this);
	    this.n1 = n1;
	    this.n2 = n2;
	    this.value = v;
	}
	Capacitor.prototype = new Device();
	Capacitor.prototype.construction = Capacitor;

	// capacitor is modeled as a current source (ieq) in parallel with a conductance (geq)

	Capacitor.prototype.reset = function() {
	    this.q = 0;		// state variable (charge)
	    this.i = 0;		// dstate/dt (current)
	    this.prev_q = 0;	// last iteration
	    this.prev_i = 0;
	}

	Capacitor.prototype.finalize = function(ckt) {
	    // call us at the end of each timestep
	    ckt.end_of_timestep.push(this);
	}

	Capacitor.prototype.end_of_timestep = function(ckt) {
	    // update state when timestep is accepted
	    this.prev_q = this.q;
	    this.prev_i = this.i;
	}

	Capacitor.prototype.load_dc = function(ckt) {
	    // open circuit
	}

	Capacitor.prototype.load_tran = function(ckt,soln) {
	    var vcap = ((this.n1 >= 0) ? soln[this.n1] : 0) - ((this.n2 >= 0) ? soln[this.n2] : 0);
	    this.q = this.value * vcap;   // set charge

	    // integrate
	    // for backward Euler: coeff0 = 1/timestep, coeff1 = 0
	    // for trapezoidal: coeff0 = 2/timestep, coeff1 = 1
	    this.i = ckt.coeff0*(this.q - this.prev_q) - ckt.coeff1*this.prev_i;
	    var ieq = this.i - ckt.coeff0*this.q;
	    var geq = ckt.coeff0 * this.value;

	    // MNA stamp for admittance geq
	    ckt.add_conductance(this.n1,this.n2,geq);

	    // MNA stamp for current source ieq
	    ckt.add_to_b(this.n1,-ieq);
	    ckt.add_to_b(this.n2,ieq);
	}

	Capacitor.prototype.load_ac = function(ckt) {
	    ckt.add_conductance(this.n1,this.n2,ckt.omega * this.value);
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Inductor
	//
	///////////////////////////////////////////////////////////////////////////////

	function Inductor(n1,n2,branch,v) {
	    Device.call(this);
	    this.n1 = n1;
	    this.n2 = n2;
	    this.branch = branch;
	    this.value = v;
	}
	Inductor.prototype = new Device();
	Inductor.prototype.construction = Inductor;

	// inductor is modeled as a voltage source (veq) with impedance (geq)

	Inductor.prototype.reset = function() {
	    this.flux = 0;	// state variable (flux)
	    this.v = 0;		// dstate/dt (voltage)
	    this.prev_flux = 0;	// last iteration
	    this.prev_v = 0;
	}

	Inductor.prototype.finalize = function(ckt) {
	    // call us at the end of each timestep
	    ckt.end_of_timestep.push(this);
	}

	Inductor.prototype.end_of_timestep = function(ckt) {
	    // update state when timestep is accepted
	    this.prev_flux = this.flux;
	    this.prev_v = this.v;
	}

	Inductor.prototype.load_dc = function(ckt) {
	    // short circuit: veq = 0, req = 0
	    ckt.add_to_A(this.n1,this.branch,1);
	    ckt.add_to_A(this.branch,this.n1,1);
	    ckt.add_to_A(this.n2,this.branch,-1);
	    ckt.add_to_A(this.branch,this.n2,-1);
	}

	Inductor.prototype.load_tran = function(ckt,soln) {
	    this.flux = this.value * soln[this.branch];   // set flux

	    // integrate
	    // for backward Euler: coeff0 = 1/timestep, coeff1 = 0
	    // for trapezoidal: coeff0 = 2/timestep, coeff1 = 1
	    this.v = ckt.coeff0*(this.flux - this.prev_flux) - ckt.coeff1*this.prev_v;
	    var veq = this.v - ckt.coeff0*this.flux;
	    var req = ckt.coeff0 * this.value;

	    // MNA stamp for voltage source with impedance
	    ckt.add_to_b(this.branch,veq);
	    ckt.add_to_A(this.branch,this.branch,-req);
	    ckt.add_to_A(this.n1,this.branch,1);
	    ckt.add_to_A(this.branch,this.n1,1);
	    ckt.add_to_A(this.n2,this.branch,-1);
	    ckt.add_to_A(this.branch,this.n2,-1);
	}

	Inductor.prototype.load_ac = function(ckt) {
	    ckt.add_to_A(this.branch,this.branch,-ckt.omega * this.value);
	    ckt.add_to_A(this.n1,this.branch,1);
	    ckt.add_to_A(this.branch,this.n1,1);
	    ckt.add_to_A(this.n2,this.branch,-1);
	    ckt.add_to_A(this.branch,this.n2,-1);
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Module definition
	//
	///////////////////////////////////////////////////////////////////////////////
	var module = {
	    'Circuit': Circuit,
	}
	return module;
    }());
