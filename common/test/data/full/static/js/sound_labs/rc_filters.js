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

var diagram, VIn, R, C;

function initDiagram()
{
	//Test if canvas is supported. If not, exit.
	var testCanvas = document.createElement("canvas")
	if (!testCanvas.getContext)
		throw "Canvas element is not supported in this browser."
	
	var element = $('#diag2');
	diagram = new Circuit.Diagram(element, true);

	//Lines
	var wirev1 = diagram.addWire(100, 295, 100, 325);
	var wirev2 = diagram.addWire(100, 140, 100, 170);
	var wirev3 = diagram.addWire(380, 295, 380, 325);
	var wirev4 = diagram.addWire(380, 140, 380, 170);
	var wireh1 = diagram.addWire(100, 140, 145, 140);
	var wireh2 = diagram.addWire(285, 140, 333, 140);
	var wireh3 = diagram.addWire(100, 355, 240, 355);
		
	var rLabel = diagram.addLabel(205, 75, "\u002B  v_{R}  \u2212", "left"); 
	var cLabelPlus = diagram.addLabel(305, 225, "\u002B", "left");
	var cLabel = diagram.addLabel(305, 250, "v_{C}", "left");
	var cLabelMinus = diagram.addLabel(305, 270, "\u2212", "left");
	rLabel.color = Plotter.Color.lightgreen;
	cLabelPlus.color = Plotter.Color.lightyellow;
	cLabel.color = Plotter.Color.lightyellow;
	cLabelMinus.color = Plotter.Color.lightyellow;
	
	//Ground
	var ground = diagram.addGround(240, 355);
		
	//Resistor
	R = diagram.addResistor(190, 140, 1);
	R.rotation = Math.PI/2;
	R.label.str = "R";
	R.valueString.suffix = "k\u03A9";
	
	//Capacitor
	C = diagram.addCapacitor(380, 200, 110);
	C.label.str = "C";
	C.valueString.suffix = "nF";
	
	//Voltage source
	VIn = diagram.addSource(100, 200, 3, "v");
	VIn.label.str = "v_{IN}";
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
	magGraph.yText = "Magnitude (dB)";	
	magGraph.xmin = -1;
	magGraph.xmax = 5;
	magGraph.xspan = 6;
	magGraph.xPowerMin = -1;
	magGraph.xPowerMax = 5;
		
	//y axis
	magGraph.ymin = -100;
	magGraph.ymax = 10;
	magGraph.yspan = 110;
	magGraph.yShortTickMin = -100;
	magGraph.yShortTickMax = 10;
	magGraph.yShortTickStep = 5;
	magGraph.yLongTickMin = -100;
	magGraph.yLongTickMax = 10;
	magGraph.yLongTickStep = 10;
	magGraph.yLabelMin = -100;
	magGraph.yLabelMax = 10;
	magGraph.yLabelStep = 10;
	magGraph.yGridMin = -100;
	magGraph.yGridMax = 10;
	magGraph.yGridStep = 10;
	magGraph.x0 = magGraph.xPowerMin;
	magGraph.y0 = magGraph.ymin;	
	magGraph.hasxLog = true;
	magGraph.hasxPowers = true;
	magGraph.hasyLog = false;
	magGraph.hasyPowers = false;
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
	phaseGraph.ymin = -100;
	phaseGraph.ymax = 100;
	phaseGraph.yspan = 200;
	phaseGraph.yShortTickMin = -100;
	phaseGraph.yShortTickMax = 100;
	phaseGraph.yShortTickStep = 5;
	phaseGraph.yLongTickMin = -100;
	phaseGraph.yLongTickMax = 100;
	phaseGraph.yLongTickStep = 10;
	phaseGraph.yLabelMin = -100;
	phaseGraph.yLabelMax = 100;
	phaseGraph.yLabelStep = 10;
	phaseGraph.yGridMin = -100;
	phaseGraph.yGridMax = 100;
	phaseGraph.yGridStep = 10;
	phaseGraph.x0 = phaseGraph.xPowerMin;
	phaseGraph.y0 = phaseGraph.ymin;	
	phaseGraph.hasxLog = true;
	phaseGraph.hasxPowers = true;
	phaseGraph.hasyLog = false;
	phaseGraph.hasyPowers = false;
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
	if (vcChecked)
		timeGraph.drawArray(time, csig, Plotter.Color.lightyellow);
	if (vrChecked)
		timeGraph.drawArray(time, rsig, Plotter.Color.lightgreen);
		
	magGraph.paintBuffer();
	magGraph.paintOn("canvas");
	if (vcChecked)
		magGraph.drawArray(frequencies, cmag, Plotter.Color.lightyellow);
	if (vrChecked)
		magGraph.drawArray(frequencies, rmag, Plotter.Color.lightgreen);
	
	phaseGraph.paintBuffer();
	phaseGraph.paintOn("canvas");
	if (vcChecked)
		phaseGraph.drawArray(frequencies, cphase, Plotter.Color.lightyellow);
	if (vrChecked)
		phaseGraph.drawArray(frequencies, rphase, Plotter.Color.lightgreen);	
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
		fc = getfCutoff(r, c);
		$("#fc").html("f<sub>C</sub> = " + fc.toFixed(0) + " Hz");
	}	
}		

$(function()
{
	fc = getfCutoff(r, c);
	$("#fc").html("f<sub>C</sub> = " + fc.toFixed(0) + " Hz");
	$("#vinSlider").slider({value: vIn, min: 0, max: 5, step: 0.01,
					slide: function(event, ui)
					{
						$("#vin").html("v<sub>IN</sub> = " + ui.value + " V");
						vIn = ui.value;
						VIn.value = vIn;
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

	$("#rSlider").slider({value: 1, min: 0.1, max: 10, step: 0.01,
					slide: function(event, ui)
					{
						//Values of slider are in Kilo Ohms
						var val = getResistance(ui.value);
						$(this).slider("value", val);
						if (val >= 1.0) //kOhms
						{
							$("#r").html("R = " +  val + " k&Omega;");
							R.value = val;
							R.valueString.suffix = "k\u03A9";
						}	
						else
						{
							$("#r").html("R = " +  kiloToUnit(val) + " &Omega;");
							R.value = kiloToUnit(val);
							R.valueString.suffix = "\u03A9";  
						}	
						
						r = kiloToUnit(val);
						communSlide();
						//return false; //Blocks keystrokes if enabled
					}
				});
	$("#r").html("R = " + $("#rSlider").slider("value") + " k&Omega;");
	
	$("#vc0Slider").slider({value: vC0, min: 0, max: 5, step: 0.01,
					slide: function(event, ui)
					{
						$("#vc0").html("v<sub>C</sub>(0) = " + ui.value + " V");
						vC0 = ui.value;
						communSlide();
					}
				});
	$("#vc0").html("v<sub>C</sub>(0) = " + $("#vc0Slider").slider("value") + " V");

	$("#cSlider").slider({value: 110, min: 0, max: 1000, step: 1,
					slide: function(event, ui)
					{
						//Values of slider are in nano Farad
						var val = getCapacitance(ui.value);
						$(this).slider("value", val);
						if (val >= 1000)
						{
							$("#c").html("C = " +  nanoToMicro(val) + " &mu;F");
							C.value = nanoToMicro(val);
							C.valueString.suffix = "\u03BCF";
						}	
						else
						{
							$("#c").html("C = " +  val + " nF");  
							C.value = val;
							C.valueString.suffix = "nF";
						}	
						
						c = nanoToUnit(val);
						communSlide();
						//return false; //Blocks keystrokes if enabled
					}
				});
	$("#c").html("C = " + $("#cSlider").slider("value") + " nF");
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
	if($('#vcCheckbox').prop('checked')) 
		vcChecked = true;
	else
		vcChecked = false;
	if($('#vrCheckbox').prop('checked')) 
		vrChecked = true;
	else
		vrChecked = false;
}

function getRadioButtonsState()
{
	if($('#vinRadioButton').prop('checked')) 
		sp.inSignal.listen = true;
	else
		sp.inSignal.listen = false;
	if($('#vcRadioButton').prop('checked')) 
		sp.outSignals[0].listen = true;
	else
		sp.outSignals[0].listen = false;
	if($('#vrRadioButton').prop('checked')) 
		sp.outSignals[1].listen = true;
	else
		sp.outSignals[1].listen = false;
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
var timeGraph, magGraph, phaseGraph;
var maxTime = 10; //In ms
var xLab = "t (ms)";
var maxVolt = 2;
var time;
var insig, csig, rsig, frequencies, cmag, rmag, cphase, rphase;
//Sound Player
var sp;

//Drop variable down for Type of Input
var musicType = 3;
//Checkboxes variables for Graph
var vinChecked = true;
var vcChecked = true;
var vrChecked = false;
//Slider variables
var vIn = 3.0;
var vInMax = 5.0;
var freq = 1000;
var vBias = 0.0;
var r = kiloToUnit(1);
var vC0 = 0.0;
var c = nanoToUnit(110);
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

	sp.createBuffers(2); //We have two outputs, first one is the voltage across capacitor C, the second across resistor R
	getRadioButtonsState(); //Set what we are listening to, input, or one of the above
	
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
		for (var i = 0, l = sp.inSignal.data.length; i < l; i++)
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
				for (var i = 0, l = sp.inSignal.data.length; i < l; i++)
				{
					sp.inSignal.data[i] = vBias + vIn*sp.audioData[i] / max;	
				}
			}
			else //Fill in with vBias
			{
				for (var i = 0, l = sp.inSignal.data.length; i < l; i++)
				{
					sp.inSignal.data[i] = vBias;	
				}
			}
		}
		else
		{
			if (max != 0.0)
			{	
				for (var i = 0, l = sp.inSignal.data.length; i < l; i++)
				{
					sp.inSignal.data[i] = vIn*sp.audioData[i] / max;	
				}
			}
			else //Fill in with zeros
			{
				for (var i = 0, l = sp.inSignal.data.length; i < l; i++)
				{
					sp.inSignal.data[i] = 0.0;	
				}
			}
		}		
	}
	getVRVC(sp.inSignal.data, sp.outSignals[0].data, sp.outSignals[1].data, r, c, vC0, sp.sampleRate);
      
	time = [];
	insig = [];
	csig = [];
	rsig = [];
	frequencies = [];
	cmag = [];
	rmag = [];
	cphase = [];
	rphase = [];
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
		csig[i] = sp.outSignals[0].data[ii];
		rsig[i] = sp.outSignals[1].data[ii];
		x += xinc;
		i++;	
	}

	sp.normalizeAllSounds();
	
	//Bode plots
	fc = getfCutoff(r, c);
	var df = magGraph.xspan / 500; //magGraph is 500 pix large
	var fp = magGraph.xmin;
	var f;
		
	//Scale of magGraph is 500 px
	for (var i = 0; i <= 500; i++)
	{
		frequencies[i] = fp;
		f = Math.pow(10, fp);
		cmag[i] = getGainC_DB(f, fc);
		rmag[i] = getGainR_DB(f, fc);
		cphase[i] = getPhaseC(f, fc);
		rphase[i] = getPhaseR(f, fc);
		fp += df;
	}
}

//Constants
var TWO_PI = 2.0*Math.PI;
var PI_DIV_2 = Math.PI/2.0;
//var tau = R*C; //tau: Time constant

var resistance = [0.1, 0.11, 0.12, 0.13, 0.15, 0.16, 0.18, 0.2, 0.22, 0.24, 0.27, 0.3, 0.33, 0.36, 0.39, 0.43, 0.47, 0.51, 0.56, 0.62, 0.68, 0.75, 0.82, 0.91, 1, 1.1, 1.2, 1.3, 1.50, 1.6, 1.8, 2, 2.2, 2.4, 2.7, 3, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1, 10];

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

function unitToKilo(u)
{
	return u/1000;
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

//vIN - vOut = RC dvOUT/dt
//xi = vIN
//yi = vOUT

//yi = alpha*x[i] + (1 - alpha)y[i-1] with alpha = dt/(RC + dt). dt is the sampling period. 0 <= alpha <= 1 is the smoothing factor. Exponentially-weighted moving average

function getVRVC(inData, outData, rData, R, C, VC0, sampleRate)
{
	var dt = 1.0 / sampleRate;
	var alpha = dt/(R*C + dt);
	
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

	for (var i = 1, l = outData.length; i < l; i++)
	{
		outData[i] = outData[i-1] + alpha * (inData[i] - outData[i-1]);
		rData[i] = inData[i] - outData[i]; 
	}
}

function getfCutoff(R, C)
{
	return 1.0/(TWO_PI*R*C);
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

//LOW PASS FILTER: vC
//Complex Gain is 1/(1+j(f/fc)) 
function getGainC(f, fc)
{
	var frac = f/fc;
	return 1.0/Math.sqrt(1.0 + frac*frac);
}

function getGainC_DB(f, fc)
{
	var frac = f/fc;
	return -20.0*Plotter.Utils.log10(Math.sqrt(1.0 + frac*frac));
}

function getPhaseC(f, fc)
{
	return radToDeg(-Math.atan2(f/fc, 1.0));
}

//HIGH PASS FILTER: vR
//Complex Gain is j(f/fc)/(1+j(f/fc))
function getGainR(f, fc)
{
	var frac = f/fc;
	return frac/Math.sqrt(1.0 + frac*frac);
}

function getGainR_DB(f, fc)
{
	var frac = f/fc;
	return 20.0*(Plotter.Utils.log10(frac) - Plotter.Utils.log10(Math.sqrt(1.0 + frac*frac)));
}

function getPhaseR(f, fc)
{
	return radToDeg(PI_DIV_2 - Math.atan2(f/fc, 1.0));
}
