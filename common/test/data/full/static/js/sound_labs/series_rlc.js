$(document).ready(function()
{
	//The try catch block checks if canvas and audio libraries are present. If not, we exit and alert the user.
	try
	{
		//Add corresponding listener to various UI elements		
		$('#musicTypeSelect').change(onSelectChange);		
		$('input:checkbox').click(checkboxClicked);
		$('input:radio').click(radioButtonClicked);
		$('#playButton').click(playButtonClicked);
		initSound();
		initDiagram();
		initGraphs();
		setTimeGraph();
		setMagGraph();
		setPhaseGraph();
		generateBuffer();
		calculateSignals();
		draw();
		labEnabled = true;
		$("#graphTabs").tabs();
		$("#graphTabs").bind("tabsselect", tabSelected);
	}
	catch(err)
	{
		labEnabled = false;
		alert(err + " The tool is disabled.");
	}	
});

function initGraphs()
{
	//Test if canvas is supported. If not, exit.
	var testCanvas = document.createElement("canvas")
	if (!testCanvas.getContext)
		throw "Canvas element is not supported in this browser."
	
	//Time graph
	//Get canvas
	var timeCanvas = $('#time')[0];
	//To disable text selection outside the canvas
	timeCanvas.onselectstart = function(){return false;};
	//Create an offscreen buffer
	var timeBuffer = document.createElement('canvas');
	timeBuffer.width = timeCanvas.width;
	timeBuffer.height = timeCanvas.height;
	timeGraph = new Plotter.Graph(50, 50, 400, 400, timeCanvas, timeBuffer);
	
	//Magnitude graph
	//Get canvas
	var magCanvas = $('#magnitude')[0];
	//To disable text selection outside the canvas
	magCanvas.onselectstart = function(){return false;};
	//Create an offscreen buffer
	var magBuffer = document.createElement('canvas');
	magBuffer.width = magCanvas.width;
	magBuffer.height = magCanvas.height;
	magGraph = new Plotter.Graph(50, 50, 400, 400, magCanvas, magBuffer);
	
	//Phase graph
	//Get canvas
	var phaseCanvas = $('#phase')[0];
	//To disable text selection outside the canvas
	phaseCanvas.onselectstart = function(){return false;};
	//Create an offscreen buffer
	var phaseBuffer = document.createElement('canvas');
	phaseBuffer.width = phaseCanvas.width;
	phaseBuffer.height = phaseCanvas.height;
	phaseGraph = new Plotter.Graph(50, 50, 400, 400, phaseCanvas, phaseBuffer);
}

var diagram, VIn, R, L, C;

function initDiagram()
{
	//Test if canvas is supported. If not, exit.
	var testCanvas = document.createElement("canvas")
	if (!testCanvas.getContext)
		throw "Canvas element is not supported in this browser."
	
	var element = $('#diag3');
	diagram = new Circuit.Diagram(element, true);

	//Lines
	var wirev1 = diagram.addWire(100, 295, 100, 325);
	var wirev2 = diagram.addWire(100, 140, 100, 170);
	var wirev3 = diagram.addWire(380, 295, 380, 325);
	var wirev4 = diagram.addWire(380, 140, 380, 170);
	var wireh1 = diagram.addWire(100, 140, 115, 140);
	var wireh2 = diagram.addWire(225, 140, 240, 140);
	var wireh3 = diagram.addWire(350, 140, 365, 140);
	var wireh4 = diagram.addWire(100, 355, 240, 355);
		
	var rLabel = diagram.addLabel(145, 75, "\u002B  v_{R}  \u2212", "left"); 
	var lLabel = diagram.addLabel(275, 75, "\u002B  v_{L}  \u2212", "left"); 
	var cLabelPlus = diagram.addLabel(305, 225, "\u002B", "left");
	var cLabel = diagram.addLabel(305, 250, "v_{C}", "left");
	var cLabelMinus = diagram.addLabel(305, 270, "\u2212", "left");
	rLabel.color = Plotter.Color.lightgreen;
	lLabel.color = Plotter.Color.lightmagenta;
	cLabelPlus.color = Plotter.Color.lightyellow;
	cLabel.color = Plotter.Color.lightyellow;
	cLabelMinus.color = Plotter.Color.lightyellow;
	
	//Ground
	var ground = diagram.addGround(240, 355);
		
	//Resistor
	R = diagram.addResistor(130, 140, 1);
	R.rotation = Math.PI/2;
	R.label.str = "R";
	R.valueString.suffix = "k\u03A9";
	
	//Inductor
	L = diagram.addInductor(255, 140, 10);
	L.rotation =  Math.PI/2;
	L.label.str = "L";
	L.valueString.suffix = "mH"
			
	//Capacitor
	C = diagram.addCapacitor(380, 200, 110);
	C.label.str = "C";
	C.valueString.suffix = "nF";
	
	//Voltage source
	VIn = diagram.addSource(100, 200, 3.0, "v");
	VIn.label.str = "v_{IN}";
	VIn.valueString.decimal = 2;
	VIn.valueString.suffix = "V";
	VIn.label.color = Plotter.Color.lightblue;
	VIn.valueString.color = Plotter.Color.lightblue;
	
	//diagram.showGrid = true;
	diagram.paint();
}

function setTimeGraph()
{
	var lticks = 1;
	var sticks = 0.5;
	//x axis
	timeGraph.xText = xLab;
	timeGraph.yText = "V_{MAX} (Volts)";	
	timeGraph.xmin = 0;
	timeGraph.xmax = maxTime;
	timeGraph.xspan = maxTime;
	timeGraph.xShortTickMin = 0;
	timeGraph.xShortTickMax = maxTime;
	timeGraph.xShortTickStep = maxTime/20;
	timeGraph.xLongTickMin = 0;
	timeGraph.xLongTickMax = maxTime;
	timeGraph.xLongTickStep = maxTime/10;
	timeGraph.xLabelMin = 0;
	timeGraph.xLabelMax = maxTime;
	timeGraph.xLabelStep = maxTime/10;
	timeGraph.xGridMin = 0;
	timeGraph.xGridMax = maxTime;
	timeGraph.xGridStep = maxTime/10;
	//y axis
	timeGraph.ymin = -maxVolt;
	timeGraph.ymax = maxVolt;
	timeGraph.yspan = 2*maxVolt;
	timeGraph.yShortTickMin = -maxVolt + (maxVolt % sticks);
	timeGraph.yShortTickMax = maxVolt - (maxVolt % sticks);
	timeGraph.yShortTickStep = sticks;
	timeGraph.yLongTickMin = -maxVolt + (maxVolt % lticks);
	timeGraph.yLongTickMax = maxVolt - (maxVolt % lticks);
	timeGraph.yLongTickStep = lticks;
	timeGraph.yLabelMin = -maxVolt + (maxVolt % lticks);
	timeGraph.yLabelMax = maxVolt - (maxVolt % lticks);
	timeGraph.yLabelStep = lticks;
	timeGraph.yGridMin = -maxVolt + (maxVolt % lticks);
	timeGraph.yGridMax = maxVolt - (maxVolt % lticks);
	timeGraph.yGridStep = lticks;
}

function setMagGraph()
{
	var lticks = 1;
	var sticks = 0.5;
	//x axis
	magGraph.xText = "f (Hz)";
	magGraph.xPowerMin = -1;
	magGraph.xPowerMax = 9;
	magGraph.xspan = 10;
		
	//y axis
	magGraph.yText = "Magnitude (dB)";
	magGraph.ymin = -300;
	magGraph.ymax = 40;
	magGraph.yspan = 340;
	magGraph.yShortTickMin = -300;
	magGraph.yShortTickMax = 40;
	magGraph.yShortTickStep = 10;
	magGraph.yLongTickMin = -300;
	magGraph.yLongTickMax = 40;
	magGraph.yLongTickStep = 20;
	magGraph.yLabelMin = -300;
	magGraph.yLabelMax = 40;
	magGraph.yLabelStep = 20;
	magGraph.yGridMin = -300;
	magGraph.yGridMax = 40;
	magGraph.yGridStep = 20;
	magGraph.x0 = magGraph.xPowerMin;
	magGraph.y0 = magGraph.ymin;	
	magGraph.hasxLog = true;
	magGraph.hasxPowers = true;
	magGraph.hasyLog = false;
	magGraph.hasyPowers = false;
	magGraph.yLabelDecimalDigits = 0;
}

function setPhaseGraph()
{
	var lticks = 1;
	var sticks = 0.5;
	//x axis
	phaseGraph.xText = "f (Hz)";
	phaseGraph.yText = "Phase (degrees)";	
	phaseGraph.xmin = -1;
	phaseGraph.xmax = 5;
	phaseGraph.xspan = 6;
	phaseGraph.xPowerMin = -1;
	phaseGraph.xPowerMax = 5;
	
	//y axis
	phaseGraph.ymin = -200;
	phaseGraph.ymax = 200;
	phaseGraph.yspan = 400;
	phaseGraph.yShortTickMin = -180;
	phaseGraph.yShortTickMax = 180;
	phaseGraph.yShortTickStep = 10;
	phaseGraph.yLongTickMin = -180;
	phaseGraph.yLongTickMax = 180;
	phaseGraph.yLongTickStep = 45;
	phaseGraph.yLabelMin = -180;
	phaseGraph.yLabelMax = 180;
	phaseGraph.yLabelStep = 45;
	phaseGraph.yGridMin = -180;
	phaseGraph.yGridMax = 180;
	phaseGraph.yGridStep = 10;
	phaseGraph.x0 = phaseGraph.xPowerMin;
	phaseGraph.y0 = phaseGraph.ymin;	
	phaseGraph.hasxLog = true;
	phaseGraph.hasxPowers = true;
	phaseGraph.hasyLog = false;
	phaseGraph.hasyPowers = false;
	phaseGraph.yLabelDecimalDigits = 0;
}	
	
function generateBuffer()
{
	timeGraph.paintOn("buffer"); 
	timeGraph.paint();
	magGraph.paintOn("buffer"); 
	magGraph.paint();
	phaseGraph.paintOn("buffer"); 
	phaseGraph.paint();
}

function draw()
{	
	//Paint buffer on canvas
	timeGraph.paintBuffer();
	
	//Draw on canvas
	timeGraph.paintOn("canvas"); //Draw on screen image
	
	if (vinChecked)	
		timeGraph.drawArray(time, insig, Plotter.Color.lightblue);
	if (vrChecked)
		timeGraph.drawArray(time, rsig, Plotter.Color.lightgreen);
	if (vlChecked)
		timeGraph.drawArray(time, lsig, Plotter.Color.lightmagenta);
	if (vcChecked)
		timeGraph.drawArray(time, csig, Plotter.Color.lightyellow);
		
			
	magGraph.paintBuffer();
	magGraph.paintOn("canvas");
	if (vrChecked)
		magGraph.drawArray(frequencies, rmag, Plotter.Color.lightgreen);
	if (vlChecked)
		magGraph.drawArray(frequencies, lmag, Plotter.Color.lightmagenta);
	if (vcChecked)
		magGraph.drawArray(frequencies, cmag, Plotter.Color.lightyellow);
		
	phaseGraph.paintBuffer();
	phaseGraph.paintOn("canvas");
	if (vrChecked)
		phaseGraph.drawArray(frequencies, rphase, Plotter.Color.lightgreen);
	if (vlChecked)
		phaseGraph.drawArray(frequencies, lphase, Plotter.Color.lightmagenta);
	if (vcChecked)
		phaseGraph.drawArray(frequencies, cphase, Plotter.Color.lightyellow);
}

function initSound()
{
	sp = new Sound.Player();
	sp.soundStarted = function()
	{
		$('#playButton').prop('value', "Stop");
	}	
	
	sp.soundStopped = function()
	{
		$('#playButton').prop('value', "Play");
	}
}		
	
function communSlide()
{
	if (labEnabled)
	{
		if (sp.isPlaying)
			sp.stopTone();
		calculateSignals();
		draw();
		diagram.paint();
		//fc = getfCutoff(r, c);
		//$("#fc").html("f<sub>C</sub> = " + fc.toFixed(0) + " Hz");
	}	
}		

$(function()
{
	//fc = getfCutoff(r, c);
	//$("#fc").html("f<sub>C</sub> = " + fc.toFixed(0) + " Hz");
	$("#vinSlider").slider({value: vIn, min: 0, max: 5, step: 0.01,
					slide: function(event, ui)
					{
						$("#vin").html("v<sub>IN</sub> = " + ui.value + " V");
						vIn = ui.value;
						VIn.value = vIn;
						VIn.valueString.decimal = -1; //Bug?????
						communSlide();
					}
				});
	$("#vin").html("v<sub>IN</sub> = " + $("#vinSlider").slider("value") + " V");

	$("#freqSlider").slider({value: freq, min: 100, max: 5000, step: 100,
					slide: function(event, ui)
					{
						$("#freq").html("Frequency = " + ui.value + " Hz");
						freq = ui.value;
						communSlide();
					}
				});
	$("#freq").html("Frequency = " + $("#freqSlider").slider("value") + " Hz");

	$("#vbiasSlider").slider({value: vBias, min: -5, max: 5, step: 0.01,
					slide: function(event, ui)
					{
						$("#vbias").html("V<sub>BIAS</sub> = " + ui.value + " V");
						vBias = ui.value;
						communSlide();
					}
				});
	$("#vbias").html("V<sub>BIAS</sub> = " + $("#vbiasSlider").slider("value") + " V");

	$("#rSlider").slider({value: 10, min: 10, max: 1000, step: 1,
					slide: function(event, ui)
					{
						//Values of slider are in Ohms
						var val = getResistance(ui.value);
						$(this).slider("value", val);
						if (val >= 1000.0) //kOhms
						{
							$("#r").html("R = " +  unitToKilo(val) + " k&Omega;");
							R.value = unitToKilo(val);
							R.valueString.suffix = "k\u03A9";
						}	
						else
						{
							$("#r").html("R = " +  val + " &Omega;");
							R.value = val;
							R.valueString.suffix = "\u03A9";
						}	
						
						r = val;
						communSlide();
						//return false; //Blocks keystrokes
					}
				});
	$("#r").html("R = " + $("#rSlider").slider("value") + " &Omega;");
	
	$("#lSlider").slider({value: 10, min: 0, max: 1000, step: 1,
					slide: function(event, ui)
					{
						//Values of slider are in milli Henry
						var val = getInductance(ui.value);
						$(this).slider("value", val);
						if (val >= 1000.0) //H
						{
							$("#l").html("L = " +  milliToUnit(val) + " H"); 
							L.value = milliToUnit(val);
							L.valueString.suffix = "H";
						}	
						else
						{
							$("#l").html("L = " +  val + " mH");  
							L.value = val;
							L.valueString.suffix = "mH";
						}	
						
						l = milliToUnit(val);
						communSlide();
					}
				});
	$("#l").html("L = " + $("#lSlider").slider("value") + " mH");
	
	$("#cSlider").slider({value: 10, min: 10, max: 1000, step: 1,
					slide: function(event, ui)
					{
						//Values of slider are in micro Farad
						var val = getCapacitance(ui.value);
						$(this).slider("value", val);
						if (val >= 1000)
						{
							$("#c").html("C = " +  val + " F");
							C.value = microToUnit(val);
							C.valueString.suffix = "F";
						}	
						else
						{
							$("#c").html("C = " +  val + " &mu;F");  
							C.value = val;
							C.valueString.suffix = "\u03BCF";
						}	
						
						c = microToUnit(val);
						communSlide();
					}
				});
	$("#c").html("C = " + $("#cSlider").slider("value") + "  &mu;F");
  $("#vc0Slider").slider({value: vC0, min: 0, max: 5, step: 0.01,
					slide: function(event, ui)
					{
						$("#vc0").html("v<sub>C</sub>(0) = " + ui.value + " V");
						vC0 = ui.value;
						communSlide();
					}
				});
	$("#vc0").html("v<sub>C</sub>(0) = " + $("#vc0Slider").slider("value") + " V");
	$("#i0Slider").slider({value: i0, min: 0, max: 1, step: 0.01,
					slide: function(event, ui)
					{
						$("#i0").html("i(0) = " + ui.value + " A");
						i0 = ui.value;
						communSlide();
					}
				});
	$("#i0").html("i(0) = " + $("#i0Slider").slider("value") + " A");
	$("#vmaxSlider" ).slider({value: vMax, min: 1, max: 20, step: 0.1,
					slide: function(event, ui)
					{
						$("#vmax").html("V<sub>MAX</sub> = " + ui.value + " V");
						maxVolt = ui.value;
						if (labEnabled)
						{
							if (sp.isPlaying)
								sp.stopTone();
							setTimeGraph();
							generateBuffer();
							calculateSignals();
							draw();	
						}	
					}
				});
	$("#vmax").html("V<sub>MAX</sub> = " + $("#vmaxSlider").slider("value") + " V");
});

function getCheckboxesState()
{
	if($('#vinCheckbox').prop('checked')) 
		vinChecked = true;
	else
		vinChecked = false;
	if($('#vrCheckbox').prop('checked')) 
		vrChecked = true;
	else
		vrChecked = false;
	if($('#vlCheckbox').prop('checked')) 
		vlChecked = true;
	else
		vlChecked = false;
	if($('#vcCheckbox').prop('checked')) 
		vcChecked = true;
	else
		vcChecked = false;
}

function getRadioButtonsState()
{
	if($('#vinRadioButton').prop('checked')) 
		sp.inSignal.listen = true;
	else
		sp.inSignal.listen = false;
	if($('#vrRadioButton').prop('checked')) 
		sp.outSignals[1].listen = true;
	else
		sp.outSignals[1].listen = false;
	if($('#vlRadioButton').prop('checked')) 
		sp.outSignals[2].listen = true;
	else
		sp.outSignals[2].listen = false;
	if($('#vcRadioButton').prop('checked')) 
		sp.outSignals[3].listen = true;
	else
		sp.outSignals[3].listen = false;	
}

function onSelectChange()
{
	if (labEnabled)
	{
		musicType = $("#musicTypeSelect").val();
		sp.stopTone();
		if (musicType == 0) //Zero Input
		{
			$("#vinSlider").slider( "option", "disabled", true);
			$("#freqSlider").slider( "option", "disabled", true);
			maxTime = 10; //ms
			xLab = "t (ms)";
			musicLoaded();
		}
		else if (musicType == 1) //Unit Impulse
		{
			$("#vinSlider").slider( "option", "disabled", true);
			$("#freqSlider").slider( "option", "disabled", true);	
			maxTime = 10; //ms
			xLab = "t (ms)";
			musicLoaded();
		}
		else if (musicType == 2) //Unit Step
		{
			$("#vinSlider").slider( "option", "disabled", true);
			$("#freqSlider").slider( "option", "disabled", true);	
			maxTime = 10; //ms
			xLab = "t (ms)";
			musicLoaded();
		}	
		if (musicType == 3) //Sine Wave
		{
			$("#vinSlider").slider( "option", "disabled", false);
			$("#freqSlider").slider( "option", "disabled", false);		
			maxTime = 10; //ms
			xLab = "t (ms)";
			musicLoaded();
		}
		else if (musicType == 4) //Square Wave
		{
			$("#vinSlider").slider( "option", "disabled", false);
			$("#freqSlider").slider( "option", "disabled", false);		
			maxTime = 10; //ms
			xLab = "t (ms)";
			musicLoaded();
		}		
		else if (musicType == 5 || musicType == 6 || musicType == 7 || musicType == 8) //Music
		{		
			$("#vinSlider").slider( "option", "disabled", false);
			$("#freqSlider").slider( "option", "disabled", true);		
			maxTime = 20; //s
			xLab = "t (s)";
			
			if (musicType == 5)
				sp.load("classical.wav", musicLoaded);
			else if (musicType == 6)
				sp.load("folk.wav", musicLoaded);
			else if (musicType == 7)
				sp.load("jazz.wav", musicLoaded);
			else
				sp.load("reggae.wav", musicLoaded);
		}	
	}	
}

function tabSelected(event, ui)
{
	if (ui.index == 0)
	{
		 //Time, renable all sliders
		$("#vinSlider").slider("option", "disabled", false);
		$("#freqSlider").slider("option", "disabled", false);
		$("#vbiasSlider").slider("option", "disabled", false);
		$("#vc0Slider").slider("option", "disabled", false);
		$("#i0Slider").slider("option", "disabled", false);
		$("#vmaxSlider" ).slider("option", "disabled", false);
		//And vinCheckbox
		$('#vinCheckbox').attr("disabled", false);

	}
	else if (ui.index == 1 || ui.index == 2)
	{
		 //Magnitude or phase, disable elements that have no effect on graphs
		$("#vinSlider").slider("option", "disabled", true);
		$("#freqSlider").slider("option", "disabled", true);
		$("#vbiasSlider").slider("option", "disabled", true);
		$("#vc0Slider").slider("option", "disabled", true);
		$("#i0Slider").slider("option", "disabled", true);
		$("#vmaxSlider" ).slider("option", "disabled", true);
		$('#vinCheckbox').attr("disabled", true);
	}
}

function musicLoaded()
{
	setTimeGraph();
	generateBuffer();
	calculateSignals();
	draw();
}	

function checkboxClicked()
{
	if (labEnabled)
	{
		getCheckboxesState();
		draw();
	}	
}

function radioButtonClicked()
{
	if (labEnabled)
	{
		if (sp.isPlaying)
			sp.stopTone();
		getRadioButtonsState();
	}	
}

function playButtonClicked()
{
	if (labEnabled)
	{
		if (sp.isPlaying)
			sp.stopTone();
		else
			sp.playTone();
	}	
}

//TO DO: PUT ALL THE FOLLOWING GLOBAL VARIABLES IN A NAMESPACE
var labEnabled = true;
//Graph
var graph;
var maxTime = 10; //In ms
var xLab = "t (ms)";
var maxVolt = 2;
var time;
var insig, rsig, lsig, csig, frequencies, rmag, lmag, cmag, rphase, lphase, cphase;

//Sound Player
var sp;

//Drop variable down for Type of Input
var musicType = 3;
//Checkboxes variables for Graph
var vinChecked = true, vrChecked = false, vlChecked = false, vcChecked = true;
//Slider variables
var vIn = 3.0;
var vInMax = 5.0;
var freq = 1000;
var vBias = 0.0;
var r = 10;
var l = milliToUnit(10);
var c = microToUnit(10);
var vC0 = 0.0;
var i0 = 0.0;
var vMax = 2;
var fc;

function calculateSignals()
{
	if (musicType == 0 || musicType == 1 || musicType == 2 || musicType == 3) 
	{	
		sp.soundLength = 1;		
		sp.sampleRate = 50000;
	}
	else if (musicType == 4)
	{
		sp.soundLength = 1;		
		sp.sampleRate = 88200;
	}
	else if (musicType == 5 || musicType == 6 || musicType == 7 || musicType == 8) //Classical, Folk, Jazz, Reggae
	{
		sp.soundLength = 20;
		sp.sampleRate = 22050;
	} 

	 //We have 4 outputs, 1: current, 2: vR, 3: vL, 4: vC
	sp.createBuffers(4);
	
	if (musicType == 0) //Zero Input
		sp.generateZero();
	else if (musicType == 1) //Unit Impulse
		sp.generateUnitImpulse();
	else if (musicType == 2) //Unit Step
		sp.generateUnitStep();
	else if (musicType == 3) //Sine Wave
		sp.generateSineWave(vIn, freq, vBias);	
	else if (musicType == 4) //Square Wave
		sp.generateSquareWave(vIn, freq, vBias);
	else if (musicType == 5 || musicType == 6 || musicType == 7 || musicType == 8) //Classical, Folk, Jazz, Reggae
	{
		//TO DO: MOVE OUT		
		var max = Number.NEGATIVE_INFINITY;
		var amp = 0.0;
			
		//Find the max and normalize
		for (var i = 0, len = sp.inSignal.data.length; i < len; i++)
		{
			amp = Math.abs(sp.audioData[i]);
			if (amp > max)
				max = amp;
		}
		max /= 0.5;
		if (vBias != 0.0)
		{
			if (max != 0.0)
			{	
				for (var i = 0, len = sp.inSignal.data.length; i < len; i++)
				{
					sp.inSignal.data[i] = vBias + vIn*sp.audioData[i] / max;	
				}
			}
			else //Fill in with vBias
			{
				for (var i = 0, len = sp.inSignal.data.length; i < len; i++)
				{
					sp.inSignal.data[i] = vBias;	
				}
			}
		}
		else
		{
			if (max != 0.0)
			{	
				for (var i = 0, len = sp.inSignal.data.length; i < len; i++)
				{
					sp.inSignal.data[i] = vIn*sp.audioData[i] / max;	
				}
			}
			else //Fill in with zeros
			{
				for (var i = 0, len = sp.inSignal.data.length; i < len; i++)
				{
					sp.inSignal.data[i] = 0.0;	
				}
			}
		}		
	}
	
	getSeriesRLC(sp.inSignal.data, sp.outSignals[0].data, sp.outSignals[1].data, sp.outSignals[2].data, sp.outSignals[3].data, r, l, c, vC0, i0, sp.sampleRate);
	
	time = [];
	insig = [];
	rsig = [];
	lsig = [];
	csig = [];
	frequencies = [];
	rmag = [];
	lmag = [];
	cmag = [];
	rphase = [];
	lphase = [];
	cphase = [];
	
	var i = 0;
	var ii;
	var imult;
	var imax;
	var x = 0;
	var xinc;
	
	
	//Scale of graph is 500 px
	//All generated sound (sine wave etc.) except square wave have sampling rate of 50000 Hz, length 1s. We will plot the first 10 ms. That's 500 samples for 10 ms and 500 px
	if (musicType == 0 || musicType == 1 || musicType == 2 || musicType == 3)
	{
		xinc = 10/500;
		imax = 500;
		imult = 1;
	}
	else if (musicType == 4) //At 50000 Hz, square wave plays very poorly, we use 88200 Hz
	{
		xinc = 10/882;
		imax = 882;
		imult = 1;
	}
	else if (musicType == 5 || musicType == 6 || musicType == 7 || musicType == 8) //All music files have a sampling rate 22050 Hz, length 20s. 20s/500px --> get value every 0.04 s ie every 882 samples.
	{
		xinc = 20/500;
		imax = 500;		
		imult = 882;	
	}

	while (i <= imax)
	{
		ii = imult*i;		
		time[i] = x;
		insig[i] = sp.inSignal.data[ii];
		//MISSING I PLOT
		rsig[i] = sp.outSignals[1].data[ii];
		lsig[i] = sp.outSignals[2].data[ii];
		csig[i] = sp.outSignals[3].data[ii];
		
		x += xinc;
		i++;	
	}

	sp.normalizeAllSounds();
	
	//Bode plots
	var df = magGraph.xspan / 500; //magGraph is 500 pix large
	var fp = magGraph.xmin;
	var f;
	var w;
		
	//Scale of magGraph is 500 px
	for (var i = 0; i <= 500; i++)
	{
		frequencies[i] = fp;
		f = Math.pow(10, fp);
		w = Plotter.Utils.TWO_PI*f;
		rmag[i] = getGainR(w, r, l, c);
		lmag[i] = getGainL(w, r, l, c);
		cmag[i] = getGainC(w, r, l, c);
		rphase[i] = getPhaseR(w, r, l, c);
		lphase[i] = getPhaseL(w, r, l, c);
		cphase[i] = getPhaseC(w, r, l, c);
		fp += df;
	}
}

var resistance = [10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91, 100, 110, 120, 130, 150, 160, 180, 200, 220, 240, 270, 300, 330, 360, 390, 430, 470, 510, 560, 620, 680, 750, 820, 910, 1000];

var inductance = [10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 87, 91, 100, 110, 120, 130, 150, 160, 180, 200, 220, 240, 270, 300, 330, 360, 390, 430, 470, 510, 560, 620, 680, 750, 820, 870, 910, 1000];  //Note: 87 and 870?

var capacitance = [10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91, 100, 110, 120, 130, 150, 160, 180, 200, 220, 240, 270, 300, 330, 360, 390, 430, 470, 510, 560, 620, 680, 750, 820, 910, 1000];

function getResistance(value)
{
	var distance;
	var minDistance = Number.POSITIVE_INFINITY;
	var minIndex;
   	
  for (var i = 0, l = resistance.length; i < l; i++)
  {
		distance = Math.abs(value - resistance[i]);
		if (distance < minDistance)
		{
			minDistance = distance;
			minIndex = i;
		}
  }
	return resistance[minIndex];	
}

function getInductance(value)
{
	var distance;
	var minDistance = Number.POSITIVE_INFINITY;
	var minIndex;
   	
  for (var i = 0, l = inductance.length; i < l; i++)
  {
		distance = Math.abs(value - inductance[i]);
		if (distance < minDistance)
		{
			minDistance = distance;
			minIndex = i;
		}
  }
	return inductance[minIndex];	
}

function getCapacitance(value)
{
	var distance;
	var minDistance = Number.POSITIVE_INFINITY;
	var minIndex;
   	
  for (var i = 0, l = capacitance.length; i < l; i++)
  {
		distance = Math.abs(value - capacitance[i]);
		if (distance < minDistance)
		{
			minDistance = distance;
			minIndex = i;
		}
  }
	return capacitance[minIndex];	
}

function radToDeg(angle)
{
	return angle*180.0/Math.PI;
}

function degToRad(angle)
{
	return angle*Math.PI/180.0;
}

function unitToKilo(u)
{
	return u/1000;
}

function unitToMilli(u)
{
	return u*1000;
}

function unitToMicro(u)
{
	return u*1000000;
}

function unitToNano(u)
{
	return u*1000000000;
}

function unitToPico(u)
{
	return u*1000000000000;
}

function kiloToUnit(k)
{
	return k*1000;
}

function milliToUnit(m)
{
	return m/1000;
}

function microToUnit(m)
{
	return m/1000000;
}

function nanoToUnit(n)
{
	return n/1000000000;
}

function picoToUnit(p)
{
	return p/1000000000000;
}

function nanoToMicro(p)
{
	return p/1000;
}

/*
	Vin = RI + LdI/dt + Vout
	I = CdVout/dt
	
	LCd^2Vout/dt^2 + RCdVout/dt + Vout = Vin
	
	leads to, for x[i] array of input, y[i] array out outputs:
	
	(dy/dt)[i] = (y[i+1] - y[i])/deltaT
	(d^2y/dt^2)[i] = (y[i+2]-2y[i+1]+y[i])/(deltaT^2)
	
	LC(yi+2 - 2yi+1 + yi)/dt^2 + RC(yi+1 - yi)/dt + yi = xi
	
	yi+2 = (2.0*yi+1 - yi) - (R/L)(y[i+1]-y[i])dt + (1/LC)(x[i] - y[i])dt^2;
	
	xi = Vin(0)
	yi = Vc(0)
	yi+1 = yi + dtI(0)/C
	
	beta = [dt*dt - RCdt + LC]/C(Rdt-2L)
*/

/*NECESSARY?
if (musicType != 1)
	{
		outData[0] = VC0;
		rData[0] = inData[0] - outData[0]; 
	}	
	else //Unit Impulse
	{
		outData[0] =  inData[0];
		rData[0] = -inData[0];
	}
*/
/*
function getVR(x, y)
{
	for (var i = 0, l = y.length; i < l; i++)
	{
		y[i] = x[i];
	}
}

function getVL(x, y)
{
	for (var i = 0, l = y.length; i < l; i++)
	{
		y[i] = x[i];
	}
}

function getVC(x, y, R, L, C, VC0, I0, sampleRate)
{
	var dt = 1.0 / sampleRate;
	var A1 = dt*R/L;
	var A2 = dt*dt/(L*C);
		
	y[0] = VC0;
	y[1] = y[0] + dt*I0/C;
	
	for (var i = 2, l = y.length; i < l; i++)
	{
		y[i+2] = (2.0*y[i+1] - y[i]) - A1*(y[i+1]-y[i]) + A2*(x[i] - y[i]);
	}
}
*/
//###########################################################################
/*
vR + vL + vC = vIn
Ldi/dt + Ri + q/C = vIn

System of ODE, use improved Euler method.
i = q'
i' = (1/L)(vIn - Ri - q/C)

Initial conditions given by vC(0) and i0

Then 
q0 = C vC(0)
i0
i'0 = (1/L)(vIn - Ri0 - q0/C)

qnew = qold + q'old dt = qold + i'olddt
inew = iold + i'old dt
i'new = (1/L)(vIn(n) - Rinew - qnew/C)

qnew = qold + (q'old + q'new)dt/2 = qold + (iold + inew)dt/2
inew = iold + (i'old + i'new)dt/2
i'new = (1/L)(vIn(n) - Rinew - qnew/C) 
*/

function getSeriesRLC(x, yi, yr, yl, yc, R, L, C, VC0, I0, sampleRate) //x input, yi, yr, yl, yc outputs
{
	var dt = 1.0/sampleRate;
	var dtdiv2 = dt/2.0;
	var cte = 1.0/L;
	var qold = C*VC0;
	var qnew;
	var iold = I0;
	var inew;
	var diold = cte*(x[0] - R*iold - qold/C);
	var dinew;
	//Fill out our initial conditions on all 4 outputs
	yc[0] = qold/C;
	yi[0] = iold;
	yr[0] = R*iold;
	yl[0] = L*diold;
	 
	for (var k = 1, l = x.length; k < l; k++)
	{
		qnew = qold + iold*dt;
	  inew = iold + diold*dt;
	  dinew = cte*(x[k] - R*inew - qnew/C);
	  //Improved Euler method follows
	  qnew = qold + (iold + inew)*dtdiv2;
		inew = iold + (diold + dinew)*dtdiv2;
		dinew = cte*(x[k] - R*inew - qnew/C); 
	  //Got all we need, fill up our 4 outputs
	  yc[k] = qnew/C;
		yi[k] = inew;
		yr[k] = R*inew;
		yl[k] = L*dinew;
		
		qold = qnew;
		iold = inew;
		diold = dinew;
	}
}	
	
function radToDeg(angle)
{
	return angle*180.0/Math.PI;
}

function degToRad(angle)
{
	return angle*Math.PI/180.0;
}

//db for voltages: 20*log(|gain|)

//Gain and phase for vR
//Complex Gain is R/(R +j(Lw - 1/(Cw)))
function getGainR(w, R, L, C)
{
	var re = R;
	var im = L*w - 1.0/(C*w);
	return 20.0*(Plotter.Utils.log10(R) - Plotter.Utils.log10(Math.sqrt(re*re + im*im)));
}

function getPhaseR(w, R, L, C)
{
	var re = R;
	var im = L*w - 1.0/(C*w);
	return radToDeg(-Math.atan2(im, re));
}

//Gain and phase for vL
//Complex Gain is jLw/(R +j(Lw - 1/(Cw)))
function getGainL(w, R, L, C)
{
	var re = R;
	var im = L*w - 1.0/(C*w);
	return 20.0*(Plotter.Utils.log10(L*w) - Plotter.Utils.log10(Math.sqrt(re*re + im*im)));
}

function getPhaseL(w, R, L, C)
{
	var re = R;
	var im = L*w - 1.0/(C*w);
	return radToDeg(Plotter.Utils.PI_DIV_2 - Math.atan2(im, re));
}

//Gain and phase for vC
//Complex Gain is (-j/Cw)/(R +j(Lw - 1/(Cw)))
function getGainC(w, R, L, C)
{
	var re = R;
	var im = L*w - 1.0/(C*w);
	return 20.0*(-Plotter.Utils.log10(C*w) - Plotter.Utils.log10(Math.sqrt(re*re + im*im)));
}

function getPhaseC(w, R, L, C)
{
	var re = R;
	var im = L*w - 1.0/(C*w);
	return radToDeg(-Plotter.Utils.PI_DIV_2 - Math.atan2(im, re));
}	
