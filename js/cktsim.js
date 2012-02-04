//////////////////////////////////////////////////////////////////////////////
//
//  Circuit simulator
//
//////////////////////////////////////////////////////////////////////////////

// Copyright (C) 2011 Massachusetts Institute of Technology


// create a circuit for simulation using "new cktsim.Circuit()"

// for modified nodal analysis (MNA) stamps see
// http://www.analog-electronics.eu/analog-electronics/modified-nodal-analysis/modified-nodal-analysis.xhtml

cktsim = (function() {
    
	///////////////////////////////////////////////////////////////////////////////
	//
	//  Circuit
	//
	//////////////////////////////////////////////////////////////////////////////

	// types of "nodes" in the linear system
	T_VOLTAGE = 0;
	T_CURRENT = 1;

        v_newt_lim = 0.3;   // Voltage limited Newton great for Mos/diodes
	v_abstol = 1e-6;	// criterion for absolute convergence (voltage)
	i_abstol = 1e-12;	// criterion for absolute convergence (current)
	min_time_step = 1e-18;	// smallest possible time step
	max_dc_iters = 200;	// max iterations before giving pu
	max_tran_iters = 10;	// max iterations before giving up
	increase_limit = 4;	// if we converge in this many iterations, increase time step
	time_step_increase_factor = 2.0;  // How much can lte let timestep grow.
	lte_step_decrease_factor = 8;    // How much will lte shrink timestep in one iter.
	nr_step_decrease_factor = 4;     // How much Newton will shink timeste in one iter.
	reltol = 0.0001;		// convergence criterion relative to max observed value
        lterel = 4;             // The ratio between lte error and Newton error.

	function Circuit() {
	    this.node_map = new Array();
	    this.ntypes = [];
	    this.initial_conditions = [];  // ic's for each element

	    this.devices = [];  // list of devices
	    this.device_map = new Array();  // map name -> device
	    this.voltage_sources = [];  // list of voltage sources

	    this.finalized = false;
	    this.diddc = false;
	    this.node_index = -1;
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
		this.matrix = this.make_mat(this.N, this.N+1);
		this.Gl = this.make_mat(this.N, this.N);  // Matrix for linear conductances
		this.G = this.make_mat(this.N, this.N);  // Complete conductance matrix
		this.C = this.make_mat(this.N, this.N);  // Matrix for linear L's and C's

		this.soln_max = new Array(this.N);   // max abs value seen for each unknown
		this.abstol = new Array(this.N);
		this.solution = new Array(this.N);
		this.rhs = new Array(this.N);
		for (var i = this.N - 1; i >= 0; --i) {	    
		    this.soln_max[i] = 0.0;
		    this.abstol[i] = this.ntypes[i] == T_VOLTAGE ? v_abstol : i_abstol;
		    this.solution[i] = 0.0;
		    this.rhs[i] = 0.0;
		}
	    }
	}

	// load circuit from JSON netlist (see schematic.js)
	Circuit.prototype.load_netlist = function(netlist) {
	    // set up mapping for ground node always called '0' in JSON netlist
	    var gnd_label = '0';
	    this.node_map[gnd_label] = this.gnd_node();

	    // process each component in the JSON netlist (see schematic.js for format)
	    var found_ground = false;
	    for (var i = netlist.length - 1; i >= 0; --i) {
		var component = netlist[i];
		var type = component[0];

		// ignore wires, ground connections, scope probes and view info
		if (type == 'view' || type == 'w' || type == 'g' || type == 's' || type == 'L') {
		    continue;
		}

		var properties = component[2];
		var name = properties['name'];
		if (name==undefined || name=='')
		    name = '_' + properties['_json_'].toString();

		// convert node names to circuit indicies
		var connections = component[3];
		for (var j = connections.length - 1; j >= 0; --j) {
		    var node = connections[j];
		    if(node == gnd_label) found_ground = true;
		    var index = this.node_map[node];
		    if (index == undefined) index = this.node(node,T_VOLTAGE);
		    connections[j] = index;
		}

		// process the component
		if (type == 'r')	// resistor
		    this.r(connections[0],connections[1],properties['r'],name);
		else if (type == 'd')	// diode
		    this.d(connections[0],connections[1],properties['area'],name);
		else if (type == 'c')   // capacitor
		    this.c(connections[0],connections[1],properties['c'],name);
		else if (type == 'l')	// inductor
		    this.l(connections[0],connections[1],properties['l'],name);
		else if (type == 'v') 	// voltage source
		    this.v(connections[0],connections[1],properties['value'],name);
		else if (type == 'i') 	// current source
		    this.i(connections[0],connections[1],properties['value'],name);
		else if (type == 'o') 	// op amp
		    this.opamp(connections[0],connections[1],connections[2],connections[3],properties['A'],name);
		else if (type == 'n') 	// n fet
		    this.n(connections[0],connections[1],connections[2],properties['W/L'],name);
		else if (type == 'p') 	// p fet
		    this.p(connections[0],connections[1],connections[2],properties['W/L'],name);
	    }
	    if(found_ground == false) { // No ground on schematic
		alert('Please make at least one connection to ground  (inverted T symbol)');
		return false;
	    }
	    return true;
	    
	}

	// if converges: updates this.solution, this.soln_max, returns iter count
	// otherwise: return undefined and set this.problem_node
	// Load should compute -f and df/dx (note the sign pattern!)
        Circuit.prototype.find_solution = function(load,maxiters) {
	    var soln = this.solution;
	    var rhs = this.rhs;
	    var d_sol,converged;

	    // iteratively solve until values convere or iteration limit exceeded
	    for (var iter = 0; iter < maxiters; iter++) {
		// set up equations
		load(this,soln,rhs);

		// Compute the Newton delta
		d_sol = solve_linear_system(this.matrix,rhs);

		// Update solution and check convergence.
		converged = true;
		for (var i = this.N - 1; i >= 0; --i) {
		    // Simple voltage step limiting to encourage Newton convergence
		    if (this.ntypes[i] == T_VOLTAGE) {
			d_sol[i] = (d_sol[i] > v_newt_lim) ? v_newt_lim : d_sol[i];
			d_sol[i] = (d_sol[i] < -v_newt_lim) ? -v_newt_lim : d_sol[i];
		    }
		    soln[i] += d_sol[i];
		    if (Math.abs(soln[i]) > this.soln_max[i])
			this.soln_max[i] = Math.abs(soln[i]);
		    thresh = this.abstol[i] + reltol*this.soln_max[i];
		    if (Math.abs(d_sol[i]) > thresh) {
			converged = false;
			this.problem_node = i;
		    }
		}
		//alert(numeric.prettyPrint(this.solution);)
                if (converged == true) return iter+1;
	    }
	    // too many iterations
	    return undefined;
	}

	// DC analysis
	Circuit.prototype.dc = function() {

	    // Allocation matrices for linear part, etc.
	    this.finalize();

	    // Load up the linear part.
	    for (var i = this.devices.length - 1; i >= 0; --i) {
		this.devices[i].load_linear(this)
	    }

	    // Define -f and df/dx for Newton solver
	    function load_dc(ckt,soln,rhs) {
		// rhs is initialized to -Gl * soln
		ckt.matv_mult(ckt.Gl, soln, rhs, -1.0);
		// G matrix is initialized with linear Gl
		ckt.copy_mat(ckt.Gl,ckt.G);
		// Now load up the nonlinear parts of rhs and G
		for (var i = ckt.devices.length - 1; i >= 0; --i)
			ckt.devices[i].load_dc(ckt,soln,rhs);
		// G matrix is copied in to the system matrix
		ckt.copy_mat(ckt.G,ckt.matrix);
	    }

	    // find the operating point
	    var iterations = this.find_solution(load_dc,max_dc_iters);

	    if (typeof iterations == 'undefined') {
		return 'Node '+this.node_map[this.problem_node]+' unconverged';
	    } else {
		// Note that a dc solution was computed
		this.diddc = true;
		// create solution dictionary
		var result = new Array();
		// capture node voltages
		for (var name in this.node_map) {
		    var index = this.node_map[name];
		    result[name] = (index == -1) ? 0 : this.solution[index];
		}
		// capture branch currents from voltage sources
		for (var i = this.voltage_sources.length - 1; i >= 0; --i) {
		    var v = this.voltage_sources[i];
		    result['I('+v.name+')'] = this.solution[v.branch];
		}
		return result;
	    }
	}

	// Transient analysis (needs work!)
        Circuit.prototype.tran = function(ntpts, tstart, tstop, probenames, no_dc) {

	    // Define -f and df/dx for Newton solver
	    function load_tran(ckt,soln,rhs) {
		// Crnt is initialized to -Gl * soln
		ckt.matv_mult(ckt.Gl, soln, ckt.c,-1.0);
		// G matrix is initialized with linear Gl
		ckt.copy_mat(ckt.Gl,ckt.G);
		// Now load up the nonlinear parts of crnt and G
		for (var i = ckt.devices.length - 1; i >= 0; --i)
		    ckt.devices[i].load_tran(ckt,soln,ckt.c,ckt.time);
		// Exploit the fact that storage elements are linear
		ckt.matv_mult(ckt.C, soln, ckt.q, 1.0);
		// -rhs = c - dqdt
		for (var i = ckt.N-1; i >= 0; --i) {
		    var dqdt = ckt.alpha0*ckt.q[i] + ckt.alpha1*ckt.oldq[i] + 
			ckt.alpha2*ckt.old2q[i];
		    //alert(numeric.prettyPrint(dqdt));
		    rhs[i] = ckt.beta0[i]*ckt.c[i] + ckt.beta1[i]*ckt.oldc[i] - dqdt;
		}
		// matrix = beta0*G + alpha0*C.
		ckt.mat_scale_add(ckt.G,ckt.C,ckt.beta0,ckt.alpha0,ckt.matrix);
	    }

	    var p = new Array(3);
	    function interp_coeffs(t, t0, t1, t2) {
		// Poly coefficients
		var dtt0 = (t - t0);
		var dtt1 = (t - t1);
		var dtt2 = (t - t2);
		var dt0dt1 = (t0 - t1);
		var dt0dt2 = (t0 - t2);
		var dt1dt2 = (t1 - t2);
		p[0] = (dtt1*dtt2)/(dt0dt1 * dt0dt2);
		p[1] = (dtt0*dtt2)/(-dt0dt1 * dt1dt2);
		p[2] = (dtt0*dtt1)/(dt0dt2 * dt1dt2);
		return p;
	    }

	    function pick_step(ckt, step_index) {
		var min_shrink_factor = 1.0/lte_step_decrease_factor;
	        var max_growth_factor = time_step_increase_factor;
		var N = ckt.N;
		var p = interp_coeffs(ckt.time, ckt.oldt, ckt.old2t, ckt.old3t);
		var trapcoeff = 0.5*(ckt.time - ckt.oldt)/(ckt.time - ckt.old3t);
		var maxlteratio = 0.0;
		for (var i = ckt.N-1; i >= 0; --i) {
		    if (ckt.ltecheck[i]) { // Check lte on variable
			var pred = p[0]*ckt.oldsol[i] + p[1]*ckt.old2sol[i] + p[2]*ckt.old3sol[i];
			var lte = Math.abs((ckt.solution[i] - pred))*trapcoeff;
			var lteratio = lte/(lterel*(ckt.abstol[i] + reltol*ckt.soln_max[i]));
			maxlteratio = Math.max(maxlteratio, lteratio);
		    }
		}
		var new_step;
		var lte_step_ratio = 1.0/Math.pow(maxlteratio,1/3); // Cube root because trap
		if (lte_step_ratio < 1.0) { // Shrink the timestep to make lte
		    lte_step_ratio = Math.max(lte_step_ratio,min_shrink_factor);
		    new_step = (ckt.time - ckt.oldt)*0.75*lte_step_ratio;
		    new_step = Math.max(new_step, ckt.min_step);
		} else {
		    lte_step_ratio = Math.min(lte_step_ratio, max_growth_factor);
		    if (lte_step_ratio > 1.2)  /* Increase timestep due to lte. */
			new_step = (ckt.time - ckt.oldt) * lte_step_ratio / 1.2;
		    else 
			new_step = (ckt.time - ckt.oldt);
		    new_step = Math.min(new_step, ckt.max_step);
		}
		return new_step;
	    }
	    
	    // Standard to do a dc analysis before transient
	    // Otherwise, do the setup also done in dc.
	    //no_dc = true;
	    if ((this.diddc == false) && (no_dc == false)) this.dc();
	    else {
		// Allocate matrices and vectors.
		this.finalize();

		// Load up the linear elements once and for all
		for (var i = this.devices.length - 1; i >= 0; --i) 
		    this.devices[i].load_linear(this)
	    }

	    // Tired of typing this, and using "with" generates hate mail.
	    var N = this.N;

	    // build array to hold list of results for each variable
	    // last entry is for timepoints.
	    var response = new Array(N + 1);
	    for (var i = N; i >= 0; --i) response[i] = new Array();

	    // Allocate back vectors for up to a second order method
	    this.old3sol = new Array(this.N);
	    this.old3q = new Array(this.N);
	    this.old2sol = new Array(this.N);
	    this.old2q = new Array(this.N);
	    this.oldsol = new Array(this.N);
	    this.oldq = new Array(this.N);
	    this.q = new Array(this.N);
	    this.oldc = new Array(this.N);
	    this.c = new Array(this.N);
	    this.alpha0 = 1.0;
	    this.alpha1 = 0.0;
	    this.alpha2 = 0.0;
	    this.beta0 = new Array(this.N);
	    this.beta1 = new Array(this.N);

	    // Mark the algebraic rows (useful for trap)
	    this.ar = this.zero_row(this.C);

	    // Non-algebraic variables and probe variables get lte
	    this.ltecheck = new Array(this.N);
	    for (var i = N; i >= 0; --i) 
		this.ltecheck[i] = (this.ar[i] == 0);

	    for (var name in this.node_map) {
		var index = this.node_map[name];
		for (var i = probenames.length; i >= 0; --i) {
		    if (name == probenames[i]) {
			this.ltecheck[index] = true;
			break;
		    }
		}
	    }
	
	    this.time = tstart;
	    this.max_step = (tstop - tstart)/ntpts;
	    this.min_step = this.max_step/1e8;
	    var new_step = this.max_step/1e6;
	    this.oldt = this.time - new_step;

	    // Initialize old crnts, charges, and solutions.
	    load_tran(this,this.solution,this.rhs)
	    for (var i = N-1; i >= 0; --i) {
		this.old3sol[i] = this.solution[i];
		this.old2sol[i] = this.solution[i];
		this.oldsol[i] = this.solution[i];
		this.old3q[i] = this.q[i]; 
		this.old2q[i] = this.q[i]; 
		this.oldq[i] = this.q[i]; 
		this.oldc[i] = this.c[i]; 
	    }

	    var step_index = -2;  // Start with two pseudo-Euler steps
	    var beta0,beta1;
	    while (this.time <= tstop) {
		// Save the just computed solution, and move back q and c.
		for (var i = this.N - 1; i >= 0; --i) {
		    if (step_index >= 0)
			response[i].push(this.solution[i]);
		    this.oldc[i] = this.c[i];
		    this.old3sol[i] = this.old2sol[i];
		    this.old2sol[i] = this.oldsol[i];
		    this.oldsol[i] = this.solution[i];
		    this.old3q[i] = this.oldq[i];
		    this.old2q[i] = this.oldq[i];
		    this.oldq[i] = this.q[i];

		}

		if (step_index < 0) {  // Take a prestep using BE
		    this.old3t = this.old2t - (this.oldt-this.old2t)
		    this.old2t = this.oldt - (tstart-this.oldt)
		    this.oldt = tstart - (this.time - this.oldt);
		    this.time = tstart;
		    beta0 = 1.0;  
		    beta1 = 0.0;		
		} else {  // Take a regular step
		    // Save the time, and rotate time wheel
		    response[this.N].push(this.time);
		    this.old3t = this.old2t;
		    this.old2t = this.oldt;
		    this.oldt = this.time;
		    // Make sure we come smoothly in to the interval end.
		    if (this.time >= tstop) break;  // We're done.
		    else if(this.time + new_step > tstop)
			this.time = tstop;
		    else if(this.time + 1.5*new_step > tstop)
			this.time += (2/3)*(tstop - this.time);
		    else
			this.time += new_step;
		    // Trapezoidal rule betas
		    beta0 = 0.5;
		    beta1 = 0.5;		
		}

		// Keep track of step index.
		step_index += 1;

		// For trap rule, turn off current avging for algebraic eqns
		for (var i = this.N - 1; i >= 0; --i) {
		    this.beta0[i] = beta0 + this.ar[i]*beta1;
		    this.beta1[i] = (1.0 - this.ar[i])*beta1;
		}
		
		// Loop to find NR converging timestep with okay LTE
		while (true) {
		    // Set the timestep coefficients (alpha2 is for bdf2).
		    this.alpha0 = 1.0/(this.time - this.oldt);
		    this.alpha1 = -this.alpha0;
		    this.alpha2 = 0;

		    // Use Newton to compute the solution.
		    var iterations = this.find_solution(load_tran,max_tran_iters);

		    // If NR succeeds and stepsize is at min, accept and newstep=maxgrowth*minstep.
		    // Else if Newton Fails, shrink step by a factor and try again
		    // Else LTE picks new step, if bigger accept current step and go on.
		    if ((iterations != undefined) && 
			(step_index <= 0 || (this.time-this.oldt) < (1+reltol)*this.min_step)) {
			if (step_index > 0) new_step = time_step_increase_factor*this.min_step;
			break;
		    } else if (iterations == undefined) {  // NR nonconvergence, shrink by factor
			//alert('timestep nonconvergence');
			this.time = this.oldt + 
			    (this.time - this.oldt)/nr_step_decrease_factor;
		    } else {  // Check the LTE and shrink step if needed.
			new_step = pick_step(this, step_index);
			if (new_step < (1.0 - reltol)*(this.time - this.oldt)) {
			   this.time = this.oldt + new_step;  // Try again
			}
			else
			    break;  // LTE okay, new_step for next step
		    }
		}
	    }

	    // create solution dictionary
	    var result = new Array();
	    for (var name in this.node_map) {
		var index = this.node_map[name];
		result[name] = (index == -1) ? 0 : response[index];
	    }
	    // capture branch currents from voltage sources
	    for (var i = this.voltage_sources.length - 1; i >= 0; --i) {
		var v = this.voltage_sources[i];
		result['I('+v.name+')'] = response[v.branch];
	    }

	    result['time'] = response[this.N];
	    return result;
	}

	// AC analysis: npts/decade for freqs in range [fstart,fstop]
	// result['frequencies'] = vector of log10(sample freqs)
	// result['xxx'] = vector of dB(response for node xxx)
        // NOTE: Normalization removed in schematic.js, jkw.
        Circuit.prototype.ac = function(npts,fstart,fstop,source_name) {
	    if (this.diddc == false) this.dc();

	    var N = this.N;
	    var G = this.G;
	    var C = this.C;

	    // Complex numbers, we're going to need a bigger boat
	    var matrixac = this.make_mat(2*N, (2*N)+1);

            // Get the source used for ac
	    if (this.device_map[source_name] === undefined) {
		alert('AC analysis refers to unknown source ' + source_name);
		return 'AC analysis failed, unknown source';
	    }
	    this.device_map[source_name].load_ac(this,this.rhs);

	    // build array to hold list of results for each node
	    // last entry is for frequency values
	    var response = new Array(N + 1);
	    for (var i = N; i >= 0; --i) response[i] = new Array();

	    // multiplicative frequency increase between freq points
	    var delta_f = Math.exp(Math.LN10/npts);

	    var f = fstart;
	    fstop *= 1.0001;  // capture that last time point!
	    while (f <= fstop) {
		var omega = 2 * Math.PI * f;
		response[this.N].push(f);

		// Find complex x+jy that sats Gx-omega*Cy=rhs; omega*Cx+Gy=0
		// Note: solac[0:N-1]=x, solac[N:2N-1]=y
		for (var i = N-1; i >= 0; --i) {
		    // First the rhs, replicated for real and imaginary
		    matrixac[i][2*N] = this.rhs[i];
		    matrixac[i+N][2*N] = 0;

		    for (var j = N-1; j >= 0; --j) {
			matrixac[i][j] = G[i][j];
			matrixac[i+N][j+N] = G[i][j];
			matrixac[i][j+N] = -omega*C[i][j];
			matrixac[i+N][j] = omega*C[i][j];
		    }
		}

		// Compute the small signal response
		var solac = solve_linear_system(matrixac);

		// Save just the magnitude for now
		for (var i = this.N - 1; i >= 0; --i) {
		    var mag = Math.sqrt(solac[i]*solac[i] + solac[i+N]*solac[i+N]);
		    response[i].push(mag);
		}
		f *= delta_f;    // increment frequency
	    }

	    // create solution dictionary
	    var result = new Array();
	    for (var name in this.node_map) {
		var index = this.node_map[name];
		result[name] = (index == -1) ? 0 : response[index];
	    }
	    result['frequencies'] = response[this.N];
	    return result;
	}


        // Helper for adding devices to a circuit, warns on duplicate device names.
        Circuit.prototype.add_device = function(d,name) {
	    // Add device to list of devices and to device map
	    this.devices.push(d);
	    d.name = name;
	    if (name) {
		if (this.device_map[name] === undefined) 
		    this.device_map[name] = d;
		else {
		    alert('Warning: two circuit elements share the same name ' + name);
		    this.device_map[name] = d;
		}
	    }
	    return d;
	}

	Circuit.prototype.r = function(n1,n2,v,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof v) == 'string') {
		v = parse_number(v,undefined);
		if (v === undefined) return undefined;
	    }

	    if (v != 0) {
		var d = new Resistor(n1,n2,v);
		return this.add_device(d, name);
	    } else return this.v(n1,n2,0,name);   // zero resistance == 0V voltage source
	}

	Circuit.prototype.d = function(n1,n2,area,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof area) == 'string') {
		area = parse_number(area,undefined);
		if (area === undefined) return undefined;
	    }

	    if (area != 0) {
		var d = new Diode(n1,n2,area);
		return this.add_device(d, name);
	    } // zero area diodes discarded.
	}


	Circuit.prototype.c = function(n1,n2,v,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof v) == 'string') {
		v = parse_number(v,undefined);
		if (v === undefined) return undefined;
	    }
	    var d = new Capacitor(n1,n2,v);
	    return this.add_device(d, name);
	}

	Circuit.prototype.l = function(n1,n2,v,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof v) == 'string') {
		v = parse_number(v,undefined);
		if (v === undefined) return undefined;
	    }
	    var branch = this.node(undefined,T_CURRENT);
	    var d = new Inductor(n1,n2,branch,v);
	    return this.add_device(d, name);
	}

        Circuit.prototype.v = function(n1,n2,v,name) {
	    var branch = this.node(undefined,T_CURRENT);
	    var d = new VSource(n1,n2,branch,v);
	    this.voltage_sources.push(d);
	    return this.add_device(d, name);
	}

	Circuit.prototype.i = function(n1,n2,v,name) {
	    var d = new ISource(n1,n2,v);
	    return this.add_device(d, name);
	}

        Circuit.prototype.opamp = function(np,nn,no,ng,A,name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof A) == 'string') {
		ratio = parse_number(A,undefined);
		if (A === undefined) return undefined;
	    }
	    var branch = this.node(undefined,T_CURRENT);
	    var d = new Opamp(np,nn,no,ng,branch,A,name);
	    return this.add_device(d, name);
	}

        Circuit.prototype.n = function(d,g,s, ratio, name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof ratio) == 'string') {
		ratio = parse_number(ratio,undefined);
		if (ratio === undefined) return undefined;
	    }
	    var d = new Fet(d,g,s,ratio,name,'n');
	    return this.add_device(d, name);
	}

        Circuit.prototype.p = function(d,g,s, ratio, name) {
	    // try to convert string value into numeric value, barf if we can't
	    if ((typeof ratio) == 'string') {
		ratio = parse_number(ratio,undefined);
		if (ratio === undefined) return undefined;
	    }
	    var d = new Fet(d,g,s,ratio,name,'p');
	    return this.add_device(d, name);
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

        // Allocate an NxM matrix
        Circuit.prototype.make_mat = function(N,M) {
	    var mat = new Array(N);	
	    for (var i = N - 1; i >= 0; --i) {	    
		mat[i] = new Array(M);
		for (var j = M - 1; j >= 0; --j) {	    
		    mat[i][j] = 0.0;
		}
	    }
	    return mat;
	}

        // Form b = scale*Mx
        Circuit.prototype.matv_mult = function(M,x,b,scale) {
	    var n = M.length;
	    var m = M[0].length;
	    
	    if (n != b.length || m != x.length)
		throw 'Rows of M mismatched to b or cols mismatch to x.';

	    for (var i = 0; i < n; i++) {
		var temp = 0;
		for (var j = 0; j < m; j++) temp += M[i][j]*x[j];
		b[i] = scale*temp;  // Recall the neg in the name
	    }
	}

        // C = scalea*A + scaleb*B, scalea, scaleb eithers numbers or arrays (row scaling)
        Circuit.prototype.mat_scale_add = function(A, B, scalea, scaleb, C) {
	    var n = A.length;
	    var m = A[0].length;
	    
	    if (n > B.length || m > B[0].length)
		throw 'Row or columns of A to large for B';
	    if (n > C.length || m > C[0].length)
		throw 'Row or columns of A to large for C';
	    if ((typeof scalea == 'number') && (typeof scaleb == 'number'))
		for (var i = 0; i < n; i++)
		    for (var j = 0; j < m; j++)
			C[i][j] = scalea*A[i][j] + scaleb*B[i][j];
	    else if ((typeof scaleb == 'number') && (scalea instanceof Array))
		for (var i = 0; i < n; i++)
		    for (var j = 0; j < m; j++)
			C[i][j] = scalea[i]*A[i][j] + scaleb*B[i][j];
	    else if ((typeof scaleb instanceof Array) && (scalea instanceof Array))
		for (var i = 0; i < n; i++)
		    for (var j = 0; j < m; j++)
			C[i][j] = scalea[i]*A[i][j] + scaleb[i]*B[i][j];
	    else
		throw 'scalea and scaleb must be scalars or Arrays';
	}

        // Returns a vector of ones and zeros, ones denote zero rows in M
        Circuit.prototype.zero_row = function(M) {
	    var N = M.length
	    var one_if_zero = new Array(N);
	    for (var i = N-1; i >= 0; i--)
		if ((Math.max.apply(Math, M[i]) == 0)
		    && (Math.min.apply(Math, M[i]) == 0))
		    one_if_zero[i] = 1.0;
		else one_if_zero[i] = 0.0;
	    return one_if_zero;
	}
	    
        // Copy A -> using the bounds of A
	Circuit.prototype.copy_mat = function(src,dest) {
	    var n = src.length;
	    var m = src[0].length;
	    if (n > dest.length || m >  dest[0].length)
		throw 'Rows or cols > rows or cols of dest';

	    for (var i = 0; i < n; i++)
		for (var j = 0; j < m; j++)
		    dest[i][j] = src[i][j];
	}

	// add val component between two nodes to matrix M
	// Index of -1 refers to ground node
        Circuit.prototype.add_two_terminal = function(i,j,g,M) {
	    if (i >= 0) {
		M[i][i] += g;
		if (j >= 0) {
		    M[i][j] -= g;
		    M[j][i] -= g;
		    M[j][j] += g;
		}
	    } else if (j >= 0)
		M[j][j] += g;
	}

	// add val component between two nodes to matrix M
	// Index of -1 refers to ground node
        Circuit.prototype.get_two_terminal = function(i,j,x) {
	    var xi_minus_xj = 0;
	    if (i >= 0) xi_minus_xj = x[i];
	    if (j >= 0) xi_minus_xj -= x[j];
	    return xi_minus_xj
	}

        Circuit.prototype.add_conductance_l = function(i,j,g) {
            this.add_two_terminal(i,j,g, this.Gl)
	}

        Circuit.prototype.add_conductance = function(i,j,g) {
            this.add_two_terminal(i,j,g, this.G)
	}

        Circuit.prototype.add_capacitance = function(i,j,c) {
            this.add_two_terminal(i,j,c,this.C)
	}

	// add individual conductance to Gl matrix
	Circuit.prototype.add_to_Gl = function(i,j,g) {
	    if (i >=0 && j >= 0)
		this.Gl[i][j] += g;
	}

	// add individual conductance to Gl matrix
	Circuit.prototype.add_to_G = function(i,j,g) {
	    if (i >=0 && j >= 0)
		this.G[i][j] += g;
	}

	// add individual capacitance to C matrix
	Circuit.prototype.add_to_C = function(i,j,c) {
	    if (i >=0 && j >= 0)
		this.C[i][j] += c;
	}

	// add source info to rhs
        Circuit.prototype.add_to_rhs = function(i,v,rhs) {
	    if (i >= 0)	rhs[i] += v;
	}

	// solve Ax=b and return vector x given augmented matrix M = [A | b]
	// Uses Gaussian elimination with partial pivoting
        function solve_linear_system(M,rhs) {
	    var N = M.length;      // augmented matrix M has N rows, N+1 columns
	    var temp,i,j;

	    // Copy the rhs in to the last column of M if one is given.
	    if (rhs != null) {
		for (var row = 0; row < N ; row++)
		    M[row][N] = rhs[row];
	    }

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

        // Load the linear elements in to Gl and C
        Device.prototype.load_linear = function(ckt) {
	}

	// load linear system equations for dc analysis
	// (inductors shorted and capacitors opened)
        Device.prototype.load_dc = function(ckt,soln,rhs) {
	}

	// load linear system equations for tran analysis
	Device.prototype.load_tran = function(ckt,soln) {
	}

	// load linear system equations for ac analysis:
	// current sources open, voltage sources shorted
	// linear models at operating point for everyone else
	Device.prototype.load_ac = function(ckt,rhs) {
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
		if (s.charAt(index) == 'x' || s.charAt(index) == 'X') { // hex
		    while (true) {
			index += 1;
			if (index >= slen) break;
			if (s.charAt(index) >= '0' && s.charAt(index) <= '9')
			    result = result*16 + ord(s.charAt(index)) - ord('0');
			else if (s.charAt(index) >= 'A' && s.charAt(index) <= 'F')
			    result = result*16 + ord(s.charAt(index)) - ord('A') + 10;
			else if (s.charAt(index) >= 'a' && s.charAt(index) <= 'f')
			    result = result*16 + ord(s.charAt(index)) - ord('a') + 10;
			else break;
		    }
		    return result*multiplier;
		} else if (s.charAt(index) == 'b' || s.charAt(index) == 'B') {  // binary
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
		if (scale == 'e' || scale == 'E') {
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
		} else if (scale == 't' || scale == 'T') result *= 1e12;
		else if (scale == 'g' || scale == 'G') result *= 1e9;
		else if (scale == 'M') result *= 1e6;
		else if (scale == 'k' || scale == 'K') result *= 1e3;
		else if (scale == 'm') result *= 1e-3;
		else if (scale == 'u' || scale == 'U') result *= 1e-6;
		else if (scale == 'n' || scale == 'N') result *= 1e-9;
		else if (scale == 'p' || scale == 'P') result *= 1e-12;
		else if (scale == 'f' || scale == 'F') result *= 1e-15;
	    }
	    // ignore any remaining chars, eg, 1kohms returns 1000
	    return result;
	}

	Circuit.prototype.parse_number = parse_number;  // make it easy to call from outside

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Sources
	//
	///////////////////////////////////////////////////////////////////////////////

	// argument is a string describing the source's value (see comments for details)
	// source types: dc,step,square,triangle,sin,pulse,pwl,pwl_repeating

	// returns an object with the following attributes:
	//   fun -- name of source function
	//   args -- list of argument values
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
	    // dc(v)
	    if (src.fun == 'dc') {
		var v = arg_value(src.args,0,0);
		src.args = [v];
		src.value = function(t) { return v; }  // closure
	    }

	    // post-processing for impulse sources
	    // impulse(height,width)
	    else if (src.fun == 'impulse') {
		var h = arg_value(src.args,0,1);  // default height: 1
		var w = Math.abs(arg_value(src.args,2,1e-9));  // default width: 1ns
		src.args = [h,w];  // remember any defaulted values
		pwl_source(src,[0,0,w/2,h,w,0],false);
	    }

	    // post-processing for step sources
	    // step(v_init,v_plateau,t_delay,t_rise)
	    else if (src.fun == 'step') {
		var v1 = arg_value(src.args,0,0);  // default init value: 0V
		var v2 = arg_value(src.args,1,1);  // default plateau value: 1V
		var td = Math.max(0,arg_value(src.args,2,0));  // time step starts
		var tr = Math.abs(arg_value(src.args,3,1e-9));  // default rise time: 1ns
		src.args = [v1,v2,td,tr];  // remember any defaulted values
		pwl_source(src,[td,v1,td+tr,v2],false);
	    }

	    // post-processing for square wave
	    // square(v_init,v_plateau,freq)
	    else if (src.fun == 'square') {
		var v1 = arg_value(src.args,0,0);  // default init value: 0V
		var v2 = arg_value(src.args,1,1);  // default plateau value: 1V
		var freq = Math.abs(arg_value(src.args,2,1));  // default frequency: 1Hz
		src.args = [v1,v2,freq];  // remember any defaulted values

		var per = freq == 0 ? Infinity : 1/freq;
		var t_change = 0.01 * per;   // rise and fall time
		var t_pw = 0.49 * per;  // half the cycle minus rise and fall time
		pwl_source(src,[0,v1,t_change,v2,t_change+t_pw,
				v2,t_change+t_pw+t_change,v1,per,v1],true);
	    }

	    // post-processing for triangle
	    // triangle(v_init,v_plateua,t_period)
	    else if (src.fun == 'triangle') {
		var v1 = arg_value(src.args,0,0);  // default init value: 0V
		var v2 = arg_value(src.args,1,1);  // default plateau value: 1V
		var freq = Math.abs(arg_value(src.args,2,1));  // default frequency: 1s
		src.args = [v1,v2,freq];  // remember any defaulted values

		var per = freq == 0 ? Infinity : 1/freq;
		pwl_source(src,[0,v1,per/2,v2,per,v1],true);
	    }

	    // post-processing for pwl and pwlr sources
	    // pwl[r](t1,v1,t2,v2,...)
	    else if (src.fun == 'pwl' || src.fun == 'pwl_repeating') {
		pwl_source(src,src.args,src.fun == 'pwl_repeating');
	    }

	    // post-processing for pulsed sources
	    // pulse(v_init,v_plateau,t_delay,t_rise,t_fall,t_width,t_period)
	    else if (src.fun == 'pulse') {
		var v1 = arg_value(src.args,0,0);  // default init value: 0V
		var v2 = arg_value(src.args,1,1);  // default plateau value: 1V
		var td = Math.max(0,arg_value(src.args,2,0));  // time pulse starts
		var tr = Math.abs(arg_value(src.args,3,1e-9));  // default rise time: 1ns
		var tf = Math.abs(arg_value(src.args,4,1e-9));  // default rise time: 1ns
		var pw = Math.abs(arg_value(src.args,5,1e9));  // default pulse width: "infinite"
		var per = Math.abs(arg_value(src.args,6,1e9));  // default period: "infinite"
		src.args = [v1,v2,td,tr,tf,pw,per];

		var t1 = td;       // time when v1 -> v2 transition starts
		var t2 = t1 + tr;  // time when v1 -> v2 transition ends
		var t3 = t2 + pw;  // time when v2 -> v1 transition starts
		var t4 = t3 + tf;  // time when v2 -> v1 transition ends

		pwl_source(src,[t1,v1, t2,v2, t3,v2, t4,v1, per,v1],true);
	    }

	    // post-processing for sinusoidal sources
	    // sin(v_offset,v_amplitude,freq_hz,t_delay,phase_offset_degrees)
	    else if (src.fun == 'sin') {
		var voffset = arg_value(src.args,0,0);  // default offset voltage: 0V
		var va = arg_value(src.args,1,1);  // default amplitude: -1V to 1V
		var freq = Math.abs(arg_value(src.args,2,1));  // default frequency: 1Hz
		var td = Math.max(0,arg_value(src.args,3,0));  // default time delay: 0sec
		var phase = arg_value(src.args,4,0);  // default phase offset: 0 degrees
		src.args = [voffset,va,freq,td,phase];

		phase /= 360.0;

		// return value of source at time t
		src.value = function(t) {  // closure
		    if (t < td) return voffset + va*Math.sin(2*Math.PI*phase);
		    else return voffset + va*Math.sin(2*Math.PI*(freq*(t - td) + phase));
		}

		// return time of next inflection point after time t
		src.inflection_point = function(t) {	// closure
		    if (t < td) return td;
		    else return undefined;
		}
	    }
	
	    // object has all the necessary info to compute the source value and inflection points
	    src.dc = src.value(0);   // DC value is value at time 0
	    return src;
	}

	function pwl_source(src,tv_pairs,repeat) {
	    var nvals = tv_pairs.length;
	    if (nvals % 2 == 1) npts -= 1;  // make sure it's even!

	    if (nvals <= 2) {
		// handle degenerate case
		src.value = function(t) { return nvals == 2 ? tv_pairs[1] : 0; }
		src.inflection_point = function(t) { return undefined; }
	    } else {
		src.value = function(t) { // closure
		    if (repeat)
			// make time periodic if values are to be repeated
			t = Math.fmod(t,tv_pairs[nvals-2]);
		    var last_t = tv_pairs[0];
		    var last_v = tv_pairs[1];
		    if (t > last_t) {
			var next_t,next_v;
			for (var i = 2; i < nvals; i += 2) {
			    next_t = tv_pairs[i];
			    next_v = tv_pairs[i+1];
			    if (next_t > last_t)  // defend against bogus tv pairs
				if (t < next_t)
				    return last_v + (next_v - last_v)*(t - last_t)/(next_t - last_t);
			    last_t = next_t;
			    last_v = next_v;
			}
		    }
		    return last_v;
		}
		src.inflection_point = function(t) {  // closure
		    if (repeat)
			// make time periodic if values are to be repeated
			t = Math.fmod(t,tv_pairs[nvals-2]);
		    for (var i = 0; i < nvals; i += 2) {
			var next_t = tv_pairs[i];
			if (t < next_t) return next_t;
		    }
		    return undefined;
		}
	    }
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
	VSource.prototype.constructor = VSource;

	// load linear part for source evaluation
        VSource.prototype.load_linear = function(ckt) {
	    // MNA stamp for independent voltage source
	    ckt.add_to_Gl(this.branch,this.npos,1.0);
	    ckt.add_to_Gl(this.branch,this.nneg,-1.0);
	    ckt.add_to_Gl(this.npos,this.branch,-1.0);
	    ckt.add_to_Gl(this.nneg,this.branch,1.0);
	}

	// Source voltage added to b.
        VSource.prototype.load_dc = function(ckt,soln,rhs) {
	    ckt.add_to_rhs(this.branch,this.src.dc,rhs);  
	}

	// Load time-dependent value for voltage source for tran
        VSource.prototype.load_tran = function(ckt,soln,rhs,time) {
	    ckt.add_to_rhs(this.branch,this.src.value(time),rhs);  
	}

	// return time of next breakpoint for the device
	VSource.prototype.breakpoint = function(time) {
	    return this.src.inflection_point(time);
	}

	// small signal model ac value
        VSource.prototype.load_ac = function(ckt,rhs) {
	    ckt.add_to_rhs(this.branch,1.0,rhs);
	}

	function ISource(npos,nneg,v) {
	    Device.call(this);

	    this.src = parse_source(v);
	    this.npos = npos;
	    this.nneg = nneg;
	}
	ISource.prototype = new Device();
	ISource.prototype.constructor = ISource;

	// load linear system equations for dc analysis
	ISource.prototype.load_dc = function(ckt,soln,rhs) {
	    var is = this.src.dc;

	    // MNA stamp for independent current source
	    ckt.add_to_rhs(this.npos,-is,rhs);  // current flow into npos
	    ckt.add_to_rhs(this.nneg,is,rhs);   // and out of nneg
	}

	// load linear system equations for tran analysis (just like DC)
        ISource.prototype.load_tran = function(ckt,soln,rhs,time) {
	    var is = this.src.value(time);

	    // MNA stamp for independent current source
	    ckt.add_to_rhs(this.npos,-is,rhs);  // current flow into npos
	    ckt.add_to_rhs(this.nneg,is,rhs);   // and out of nneg
	}

	// return time of next breakpoint for the device
	ISource.prototype.breakpoint = function(time) {
	    return this.src.inflection_point(time);
	}

	// small signal model: open circuit
	ISource.prototype.load_ac = function(ckt) {
	    // MNA stamp for independent current source
	    ckt.add_to_rhs(this.npos,-1.0,rhs);  // current flow into npos
	    ckt.add_to_rhs(this.nneg,1.0,rhs);   // and out of nneg
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
	Resistor.prototype.constructor = Resistor;

        Resistor.prototype.load_linear = function(ckt) {
	    // MNA stamp for admittance g
	    ckt.add_conductance_l(this.n1,this.n2,this.g);
	}

	Resistor.prototype.load_dc = function(ckt) {
	    // Nothing to see here, move along.
	}

	Resistor.prototype.load_tran = function(ckt,soln) {
	}

	Resistor.prototype.load_ac = function(ckt) {
	}

	///////////////////////////////////////////////////////////////////////////////
	//
	//  Diode
	//
	///////////////////////////////////////////////////////////////////////////////

	function Diode(n1,n2,v) {
	    Device.call(this);
	    this.anode = n1;
	    this.cathode = n2;
	    this.area = v;
	    this.is = 1.0e-14;
	    this.ais = this.area * this.is;
	    this.vt = 2.58e-2;  // 26 millivolts
	}
	Diode.prototype = new Device();
        Diode.prototype.constructor = Diode;

        Diode.prototype.load_linear = function(ckt) {
	    // Diode is not linear, has no linear piece.
	}

        Diode.prototype.load_dc = function(ckt,soln,rhs) {
	    var vd = ckt.get_two_terminal(this.anode, this.cathode, soln);
	    var temp1 = this.ais * Math.exp(vd / this.vt);
	    var id = temp1 - this.ais;
	    var gd = temp1 / this.vt

	    // MNA stamp for independent current source
	    ckt.add_to_rhs(this.anode,-id,rhs);  // current flows into anode
	    ckt.add_to_rhs(this.cathode,id,rhs);   // and out of cathode
	    ckt.add_conductance(this.anode,this.cathode,gd);
	}

        Diode.prototype.load_tran = function(ckt,soln,rhs,time) {
	    this.load_dc(ckt,soln,rhs);
	}

	Diode.prototype.load_ac = function(ckt) {
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
	Capacitor.prototype.constructor = Capacitor;

        Capacitor.prototype.load_linear = function(ckt) {
	    // MNA stamp for capacitance matrix 
	    ckt.add_capacitance(this.n1,this.n2,this.value);
	}

	Capacitor.prototype.load_dc = function(ckt,soln,rhs) {
	}

	Capacitor.prototype.load_ac = function(ckt) {
	}

	Capacitor.prototype.load_tran = function(ckt) {
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
	Inductor.prototype.constructor = Inductor;

        Inductor.prototype.load_linear = function(ckt) {
	    // MNA stamp for inductor linear part
	    // L on diag of C because L di/dt = v(n1) - v(n2)
	    ckt.add_to_Gl(this.n1,this.branch,1);
	    ckt.add_to_Gl(this.branch,this.n1,-1);
	    ckt.add_to_Gl(this.n2,this.branch,-1);
	    ckt.add_to_Gl(this.branch,this.n2,1);
	    ckt.add_to_C(this.branch,this.branch,this.value)
	}

	Inductor.prototype.load_dc = function(ckt,soln,rhs) {
	    // Inductor is a short at dc, so is linear.
	}

	Inductor.prototype.load_ac = function(ckt) {
	}

	Inductor.prototype.load_tran = function(ckt) {
	}



	///////////////////////////////////////////////////////////////////////////////
	//
	//  Simple Voltage-Controlled Voltage Source Op Amp model 
	//
	///////////////////////////////////////////////////////////////////////////////

        function Opamp(np,nn,no,ng,branch,A,name) {
	    Device.call(this);
	    this.np = np;
	    this.nn = nn;
	    this.no = no;
	    this.ng = ng;
	    this.branch = branch;
	    this.gain = A;
	    this.name = name;
	}

	Opamp.prototype = new Device();
        Opamp.prototype.constructor = Opamp;
        
        Opamp.prototype.load_linear = function(ckt) {
            // MNA stamp for VCVS: 1/A(v(no) - v(ng)) - (v(np)-v(nn))) = 0.
	    var invA = 1.0/this.gain;
	    ckt.add_to_Gl(this.no,this.branch,1);
	    ckt.add_to_Gl(this.ng,this.branch,-1);
	    ckt.add_to_Gl(this.branch,this.no,-invA);
	    ckt.add_to_Gl(this.branch,this.ng,invA);
	    ckt.add_to_Gl(this.branch,this.np,1);
	    ckt.add_to_Gl(this.branch,this.nn,-1);
	}

	Opamp.prototype.load_dc = function(ckt,soln,rhs) {
	    // Op-amp is linear.
	}

	Opamp.prototype.load_ac = function(ckt) {
	}

	Opamp.prototype.load_tran = function(ckt) {
	}



	///////////////////////////////////////////////////////////////////////////////
	//
	//  Simplified MOS FET with no bulk connection and no body effect.
	//
	///////////////////////////////////////////////////////////////////////////////


        function Fet(d,g,s,ratio,name,type) {
	    Device.call(this);
	    this.d = d;
	    this.g = g;
	    this.s = s;
	    this.name = name;
	    this.ratio = ratio;
	    if (type != 'n' && type != 'p')
	    { throw 'fet type is not n or p';
	    }
	    this.type_sign = (type == 'n') ? 1 : -1;
	    this.vt = 0.5;
	    this.kp = 20e-6;
            this.beta = this.kp * this.ratio;
	    this.lambda = 0.05;
	}
	Fet.prototype = new Device();
        Fet.prototype.constructor = Fet;

        Fet.prototype.load_linear = function(ckt) {
	    // FET's are nonlinear, just like javascript progammers
	}

        Fet.prototype.load_dc = function(ckt,soln,rhs) {
	    var vds = this.type_sign * ckt.get_two_terminal(this.d, this.s, soln);
	    if (vds < 0) { // Drain and source have swapped roles
		var temp = this.d;
		this.d = this.s;
		this.s = temp;
		vds = this.type_sign * ckt.get_two_terminal(this.d, this.s, soln);
	    }
	    var vgs = this.type_sign * ckt.get_two_terminal(this.g, this.s, soln);
	    var vgst = vgs - this.vt;
	    with (this) {
		var gmgs,ids,gds;
		if (vgst > 0.0 ) { // vgst < 0, transistor off, no subthreshold here.
		    if (vgst < vds) { /* Saturation. */
			gmgs =  beta * (1 + (lambda * vds)) * vgst;
			ids = type_sign * 0.5 * gmgs * vgst;
			gds = 0.5 * beta * vgst * vgst * lambda;
		    } else {  /* Linear region */
			gmgs =  beta * (1 + lambda * vds);
			ids = type_sign * gmgs * vds * (vgst - 0.50 * vds);
			gds = gmgs * (vgst - vds) + beta * lambda * vds * (vgst - 0.5 * vds);
			gmgs *= vds;
		    }
		    ckt.add_to_rhs(d,-ids,rhs);  // current flows into the drain
		    ckt.add_to_rhs(s, ids,rhs);   // and out the source		    
		    ckt.add_conductance(d,s,gds);
		    ckt.add_to_G(s,s, gmgs);
		    ckt.add_to_G(d,s,-gmgs);
		    ckt.add_to_G(d,g, gmgs);
		    ckt.add_to_G(s,g,-gmgs);
		}
	    }
	}

	Fet.prototype.load_tran = function(ckt,soln,rhs) {
	    this.load_dc(ckt,soln,rhs);
	}

	Fet.prototype.load_ac = function(ckt) {
	}


	///////////////////////////////////////////////////////////////////////////////
	//
	//  Module definition
	//
	///////////////////////////////////////////////////////////////////////////////
	var module = {
	    'Circuit': Circuit,
	    'parse_number': parse_number,
	    'parse_source': parse_source,
	}
	return module;
    }());
