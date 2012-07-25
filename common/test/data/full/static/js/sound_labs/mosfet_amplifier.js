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
		initGraph();
		setGraph();
		generateBuffer();
		calculateSignals();
		draw();
		labEnabled = true;
	}
	catch(err)
	{
		labEnabled = false;
		alert(err + " The tool is disabled.");
	}	
});

function initGraph()
{
	//Test if canvas is supported. If not, exit.
	var testCanvas = document.createElement("canvas")
	if (!testCanvas.getContext)
		throw "Canvas element is not supported in this browser."
	//Get canvas
	var canvas = $('#graph')[0];
	//To disable text selection outside the canvas
	canvas.onselectstart = function(){return false;};
	//Create an offscreen buffer
	var buffer = document.createElement('canvas');
	buffer.width = canvas.width;
	buffer.height = canvas.height;
	graph = new Plotter.Graph(50, 50, 400, 400, canvas, buffer);
}

var diagram, VS, VIn, VBias, R;

function initDiagram()
{
	//Test if canvas is supported. If not, exit.
	var testCanvas = document.createElement("canvas")
	if (!testCanvas.getContext)
		throw "Canvas element is not supported in this browser."
	
	var element = $('#diag1');
	diagram = new Circuit.Diagram(element, true);

	//Lines
	var wirev1 = diagram.addWire(100, 289, 100, 361);
	var wirev2 = diagram.addWire(100, 78, 100, 135.5);
	var wirev3 = diagram.addWire(380, 78.5, 380, 89.5);
	var wirev4 = diagram.addWire(380, 290, 380, 361.5);
	
	var wireh1 = diagram.addWire(100, 78, 240, 78);
	var wireh2 = diagram.addWire(240, 243, 286, 243);
	var wireh3 = diagram.addWire(100, 433, 240, 433);
		
	var vOutPlus = diagram.addLabel(396, 219, "\u002B", "left");
	var vOutLabel = diagram.addLabel(396, 244, "v_{OUT}", "left");
	var vOutMinus = diagram.addLabel(396, 274, "\u2212", "left");
	vOutPlus.color = Plotter.Color.lightyellow;
	vOutLabel.color = Plotter.Color.lightyellow;
	vOutMinus.color = Plotter.Color.lightyellow;
	
	var vRPlus = diagram.addLabel(310, 127, "\u002B", "left");
	var vRLabel = diagram.addLabel(310, 152, "v_{R}", "left");
	var vRMinus = diagram.addLabel(310, 182, "\u2212", "left");
	vRPlus.color = Plotter.Color.lightgreen;
	vRLabel.color = Plotter.Color.lightgreen;
	vRMinus.color = Plotter.Color.lightgreen;
	
	//vin
	//Plotter.Color.lightblue);
	//vout
	//Plotter.Color.lightyellow);
	//vr
	//Plotter.Color.lightgreen);
	
	//Ground
	var ground = diagram.addGround(240, 433);
		
	//Resistor
	R = diagram.addResistor(380, 99.5, 10);
	R.label.str = "R";
	R.valueString.suffix = "k\u03A9";
	
	//Voltage sources
	VS = diagram.addSource(100, 193, 1.6, "v");
	VS.label.str = "V_{S}";
	VS.valueString.suffix = "V";
	VIn = diagram.addSource(240, 243, 3, "v");
	VIn.label.str = "v_{IN}";
	VIn.label.color = Plotter.Color.lightblue;
	VIn.valueString.suffix = "V";
	VIn.valueString.color = Plotter.Color.lightblue;
	VBias = diagram.addSource(240, 338, 2.5, "v");
	VBias.label.str = "v_{BIAS}";
	VBias.valueString.suffix = "V";
	
	//Mosfet
	var nMosfet = diagram.addMosfet(380, 195, "", "n"); 
	
	//diagram.showGrid = true;
	//diagram.gridStep = 1;
	diagram.paint();
}

function setGraph()
{
	var lticks = 1;
	var sticks = 0.5;
	//x axis
	graph.xText = xLab;
	graph.yText = "V_{MAX} (Volts)";	
	graph.xmin = 0;
	graph.xmax = maxTime;
	graph.xspan = maxTime;
	graph.xShortTickMin = 0;
	graph.xShortTickMax = maxTime;
	graph.xShortTickStep = maxTime/20;
	graph.xLongTickMin = 0;
	graph.xLongTickMax = maxTime;
	graph.xLongTickStep = maxTime/10;
	graph.xLabelMin = 0;
	graph.xLabelMax = maxTime;
	graph.xLabelStep = maxTime/10;
	graph.xGridMin = 0;
	graph.xGridMax = maxTime;
	graph.xGridStep = maxTime/10;
	//y axis
	graph.ymin = -maxVolt;
	graph.ymax = maxVolt;
	graph.yspan = 2*maxVolt;
	graph.yShortTickMin = -maxVolt + (maxVolt % sticks);
	graph.yShortTickMax = maxVolt - (maxVolt % sticks);
	graph.yShortTickStep = sticks;
	graph.yLongTickMin = -maxVolt + (maxVolt % lticks);
	graph.yLongTickMax = maxVolt - (maxVolt % lticks);
	graph.yLongTickStep = lticks;
	graph.yLabelMin = -maxVolt + (maxVolt % lticks);
	graph.yLabelMax = maxVolt - (maxVolt % lticks);
	graph.yLabelStep = lticks;
	graph.yGridMin = -maxVolt + (maxVolt % lticks);
	graph.yGridMax = maxVolt - (maxVolt % lticks);
	graph.yGridStep = lticks;
}	
	
function generateBuffer()
{
	//Draw on offscreen image buffer
	graph.paintOn("buffer"); 
	graph.paint();
}

function draw()
{	
	//Paint buffer on canvas
	graph.paintBuffer();
	
	//Draw on canvas
	graph.paintOn("canvas"); //Draw on screen image
	
	if (vinChecked)	
		graph.drawArray(time, insig, Plotter.Color.lightblue);
	if (voutChecked)
		graph.drawArray(time, outsig, Plotter.Color.lightyellow);
	if (vrChecked)
		graph.drawArray(time, rsig, Plotter.Color.lightgreen);
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
	}	
}		

$(function()
{
	$("#vsSlider" ).slider({value: vS, min: 0, max: 10, step: 0.01,
					slide: function(event, ui)
					{
						$("#vs").html("V<sub>S</sub> = " + ui.value + " V");
						vS = ui.value;
						VS.value = vS;
						communSlide();
					}
				});
	$("#vs").html("V<sub>S</sub> = "+ $("#vsSlider").slider("value") + " V");

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

	$("#freqSlider").slider({value: freq, min: 0, max: 5000, step: 100,
					slide: function(event, ui)
					{
						$("#freq").html("Frequency = " + ui.value + " Hz");
						freq = ui.value;
						communSlide();
					}
				});
	$("#freq").html("Frequency = " + $("#freqSlider").slider("value") + " Hz");

	$("#vbiasSlider").slider({value: vBias, min: 0, max: 10, step: 0.01,
					slide: function(event, ui)
					{
						$("#vbias").html("V<sub>BIAS</sub> = " + ui.value + " V");
						vBias = ui.value;
						VBias.value = vBias;
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

	$("#kSlider").slider({value: k*1000, min: 0, max: 10, step: 0.01,
					slide: function(event, ui)
					{
						$("#k").html("k = " + ui.value + " mA/V<sup>2</sup>");
						k = ui.value / 1000; //Values are in mA
						communSlide();
					}
				});
	$("#k").html("k = " + $("#kSlider").slider("value") + " mA/V<sup>2</sup>");

        $("#vtSlider").slider({value: vt, min: 0, max: 10, step: 0.01,
					slide: function(event, ui)
					{
						$("#vt").html("V<sub>T</sub> = " + ui.value + " V");
						vt = ui.value;
						communSlide();
					} 
				});
	$("#vt").html("V<sub>T</sub> = " + $("#vtSlider").slider("value") + " V");

	$("#vmaxSlider" ).slider({value: vMax, min: 1, max: 20, step: 0.1,
					slide: function(event, ui)
					{
						$("#vmax").html("V<sub>MAX</sub> = " + ui.value + " V");
						maxVolt = ui.value;
						if (labEnabled)
						{
							if (sp.isPlaying)
								sp.stopTone();
							setGraph();
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
	if($('#voutCheckbox').prop('checked')) 
		voutChecked = true;
	else
		voutChecked = false;
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
	if($('#voutRadioButton').prop('checked')) 
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

function musicLoaded()
{
	setGraph();
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
var insig;
var outsig;
//Sound Player
var sp;

//Drop variable down for Type of Input
var musicType = 3;
//Checkboxes variables for Graph
var vinChecked = true;
var voutChecked = true;
var vrChecked = false;
//Slider variables
var vS = 1.6;
var vIn = 3.0;
var vInMax = 5.0;
var freq = 1000;
var vBias = 2.5;
var r = 10000;
var k = 0.001;
var vt = 1;
var vMax = 2;

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

	sp.createBuffers(2); //We have two outputs, first one is the voltage across Drain, Source, the second across resistor R
	getRadioButtonsState(); //Set what we are listening to, input, or one of the above
	
	if (musicType == 0) //Zero Input
		sp.generateZero();
	else if (musicType == 1) //Unit Impulse
		sp.generateUnitImpulse();
	else if (musicType == 2) //Unit Step
		sp.generateUnitStep();
	else if (musicType == 3) //Sine Wave
		sp.generateSineWave(vIn, freq, 0);	
	else if (musicType == 4) //Square Wave
		sp.generateSquareWave(vIn, freq, 0);
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
	
	getVDS(sp.inSignal.data, sp.outSignals[0].data, vBias, vS, r, k, vt);
	getVr(sp.outSignals[0].data, sp.outSignals[1].data);
        
	time = [];
	insig = [];
	outsig = [];
	rsig = [];
	var i = 0;
	var ii;
	var imult;
	var imax;
	var x = 0;
	var xinc;
	
	
	//Scale of graph is 500 px
	//All generated sound (sine wave etc.) except square wave have sampling rate of 50000 Hz, length 1s. We will plot the first 10 ms. That's 500 		samples for 10 ms and 500 px
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
		outsig[i] = sp.outSignals[0].data[ii];
		rsig[i] = sp.outSignals[1].data[ii];
		x += xinc;
		i++;	
	}

	sp.normalizeAllSounds();
}

var resistance = [0.1, 0.11, 0.12, 0.13, 0.15, 0.16, 0.18, 0.2, 0.22, 0.24, 0.27, 0.3, 0.33, 0.36, 0.39, 0.43, 0.47, 0.51, 0.56, 0.62, 0.68, 0.75, 0.82, 0.91, 1, 1.1, 1.2, 1.3, 1.50, 1.6, 1.8, 2, 2.2, 2.4, 2.7, 3, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1, 10];

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

function kiloToUnit(k)
{
	return k*1000;
}

function getVDS(inData, outData, VBIAS, VS, R, K, VT)
{
	// Given vector of inputs (VGS), compute vector of outputs (VDS)
	// VGS: input source in vector
	// VDS: voltage across MOSFET
	// VS: Supply Voltage
	// R: load resistor
	// VC: gate-to-source below above which MOSFET is in saturation
	// K, VT: mosfet parameters
	
	var b;
	var VC = getVC(VS, R, K, VT);
	var indata;
 	
	for (var i = 0, l = inData.length; i < l; i++)
	{
		indata = inData[i] + VBIAS;
		
		if (indata < VT)
			outData[i] = VS;
		else if (indata < VC)
			outData[i] = VS - R*(K/2)*Math.pow(indata - VT, 2);
        	else
		{
                	b = -R*K*(indata - VT) - 1;
			outData[i] = (-b - Math.sqrt(b*b - 2*R*K*VS))/(R*K);
		}
	}
};

// Solve for VC, where VC is the VGS below which the MOSFET is in saturation
function getVC(VS, R, K, VT)
{
	return VT + (-1 + Math.sqrt(1 + 2*VS*R*K))/(R*K);
}

function getVr(inData, outData)
{
	for (var i = 0, l = outData.length; i < l; i++)
	{
		outData[i] = vS - inData[i];
	}	
}
