var Sound = (function() {

	//////////PRIVATE FIELDS AND METHODS//////////
	var TWO_PI = 2.0*Math.PI;
	var PI_DIV_2 = Math.PI/2.0;
	
	function Player()
	{
		this.isChrome = false;
		this.isMoz = false;
		this.audioChrome;
		this.audioMoz;
		this.dir = "/static/courses/6002/sounds/";
		this.inSignal;
		this.outSignals = [];
		this.numberChannels = 1;
		this.soundLength = 1; //In seconds
		this.sampleRate = 44100; //In Hertz
		this.numberSamples = 44100;
		this.isPlaying = false;
		this.chromeTimer;
		this.mozTimer;
		this.audioData ;
		this.playAudio;
		this.outSrc;

		//Test for Web Audio API --> Webkit browsers ie Chrome & Safari	
		//https://dvcs.w3.org/hg/audio/raw-file/tip/webaudio/specification.html
		if (!!window.webkitAudioContext)
		{
			this.audioChrome = new webkitAudioContext();
			this.isChrome = true;
		}
		//Test for Audio Data API --> Firefox 4 and ulterior
		//https://wiki.mozilla.org/Audio_Data_API
		else if (!!new Audio().mozSetup)
		{
			this.audioMoz = new Audio();
			this.isMoz = true;
		}
		else //Sound libraries are not supported, exit.
			throw "Neither Web Audio API nor Audio Data API is supported in this browser.";

		//To be overriden	
		this.soundStarted = function()
		{
		}	
	
		this.soundStopped = function()
		{
		}
	
		this.load = function(url, callback)
		{
			var request;
			var file =  this.dir + url;
			var self = this;
			request = new XMLHttpRequest();
  			request.open('GET', file, true); //Asynchronous
  			request.responseType = 'arraybuffer';
  	
			request.onload = function()
			{
				var arrayBuffer = request.response;
   			if (arrayBuffer)
				{ 
					var audioDataTmp = new Int16Array(arrayBuffer, 44);
					self.audioData = new Float32Array(audioDataTmp);
					//The music has been loaded, continue execution
					callback();
				}
  		}
			request.send();
		}        

		this.getAudioHeader = function(audioHeaderData)
		{
			//44 first bytes of file are the header
			return {					                               // OFFS SIZE NOTES
					chunkId      : bytesToStr(audioHeaderData, 0, 4),  // 0    4    "RIFF" = 0x52494646
    				chunkSize    : bytesToNum(audioHeaderData, 4, 4),  // 4    4    36+SubChunk2Size = 4+(8+SubChunk1Size)+(8+SubChunk2Size)
    				format       : bytesToStr(audioHeaderData, 8, 4),  // 8    4    "WAVE" = 0x57415645
    				subChunk1Id  : bytesToStr(audioHeaderData, 12, 4), // 12   4    "fmt " = 0x666d7420
    				subChunk1Size: bytesToNum(audioHeaderData, 16, 4), // 16   4    16 for PCM
    				audioFormat  : bytesToNum(audioHeaderData, 20, 2), // 20   2    PCM = 1
    				numChannels  : bytesToNum(audioHeaderData, 22, 2), // 22   2    Mono = 1, Stereo = 2, etc.
    				sampleRate   : bytesToNum(audioHeaderData, 24, 4), // 24   4    8000, 44100, etc
    				byteRate     : bytesToNum(audioHeaderData, 28, 4), // 28   4    SampleRate*NumChannels*BitsPerSample/8
    				blockAlign   : bytesToNum(audioHeaderData, 32, 2), // 32   2    NumChannels*BitsPerSample/8
    				bitsPerSample: bytesToNum(audioHeaderData, 34, 2), // 34   2    8 bits = 8, 16 bits = 16, etc...
    				subChunk2Id  : bytesToStr(audioHeaderData, 36, 4), // 36   4    "data" = 0x64617461
    				subChunk2Size: bytesToNum(audioHeaderData, 40, 4)  // 40   4    data size = NumSamples*NumChannels*BitsPerSample/8
			};	
		}

		this.bytesToStr = function(arr, offset, len)
		{
			var result = "";
			var l = 0;
			var i = offset;	
	
			while (l < len)
			{
				result += String.fromCharCode(arr[i]);
				i++;
				l++;
			}

			return result;
		}

		//Bytes are stored as little endians
		this.bytesToNum = function(arr, offset, len)
		{
			var result = 0;
			var l = 0;;
			var i = offset + len - 1;
			var hexstr = "0x";
			var tmpstr;
	 
			while (l < len)
			{
				if (arr[i] >= 0  && arr[i] <= 15) 
					tmpstr = "0" + arr[i].toString(16);
				else
					tmpstr = arr[i].toString(16);
   
				hexstr += tmpstr;
				i--;
				l++;
			}
	
			return parseInt(hexstr, 16);
		}

		this.createBuffers = function(nOut)
		{
			this.numberSamples = this.sampleRate*this.soundLength;
					
			if (this.isChrome)
			{	
				var b, d;
				
				b = this.audioChrome.createBuffer(this.numberChannels, this.numberSamples, this.sampleRate);
				d = b.getChannelData(0); //Float32Array
				this.inSignal = {buffer: b, data: d, listen: true};
				
				for (var i = 0; i < nOut; i++)
				{
					
					b = this.audioChrome.createBuffer(this.numberChannels, this.numberSamples, this.sampleRate);
					d = b.getChannelData(0); //Float32Array
					this.outSignals[i] = {buffer: b, data: d, listen: false};
				}
			}
			else if (this.isMoz)
			{
				this.inSignal = {data: new Float32Array(this.numberSamples), listen: true};
				for (var i = 0; i < nOut; i++)
				{
					this.outSignals[i] = {data: new Float32Array(this.numberSamples), listen: false};
				}
				this.audioMoz.mozSetup(this.numberChannels, this.sampleRate);
			}
		}

		this.generateZero = function()
		{
			for (var i = 0, l = this.inSignal.data.length; i < l; i++)
			{
				this.inSignal.data[i] = 0;
			}
		}

		this.generateUnitImpulse = function()
		{
			this.inSignal.data[0] = 1000;		
			for (var i = 1, l = this.inSignal.data.length; i < l; i++)
			{
				this.inSignal.data[i] = 0.0;
			}
		}

		this.generateUnitStep = function()
		{
			for (var i = 0, l = this.inSignal.data.length; i < l; i++)
			{
				this.inSignal.data[i] = 1.0;
			}
		}

		this.generateSineWave = function(peakToPeak, frequency, vOffset)
		{
			var amp = 0.5*peakToPeak;
			
			if (vOffset != 0)
			{		
				for (var i = 0, l = this.inSignal.data.length; i < l; i++)
				{
					this.inSignal.data[i] = amp * Math.sin(TWO_PI*frequency*i/this.sampleRate) + vOffset;
				}
			}
			else
			{
				for (var i = 0, l = this.inSignal.data.length; i < l; i++)
				{
					this.inSignal.data[i] = amp * Math.sin(TWO_PI*frequency*i/this.sampleRate);
				}
			}		
		}
	
		this.generateSquareWave = function(peakToPeak, frequency, vOffset)
		{
			var amp = 0.5*peakToPeak;		
			var period = 1/frequency;
			var halfPeriod = period/2;
			var itmp, sgn;
		
			
			if (vOffset != 0)
			{
				for (var i = 0, l = this.inSignal.data.length; i < l; i++)
				{
					itmp = (i/this.sampleRate) % period;
					if (itmp < halfPeriod)
						sgn = sgn = 1;
					else
						sgn = -1;
					this.inSignal.data[i] = amp * sgn + vOffset;
				}
			}
			else
			{
				for (var i = 0, l = this.inSignal.data.length; i < l; i++)
				{
					itmp = (i/this.sampleRate) % period;
					if (itmp < halfPeriod)
						sgn = sgn = 1;
					else
						sgn = -1;
					this.inSignal.data[i] = amp * sgn;
				}
			}	
		}

		this.normalizeSound = function(arr)
		{
			var min = Number.POSITIVE_INFINITY;
			var max = Number.NEGATIVE_INFINITY;
			var vInMaxLocal = 10.0;
			var maxVol = 1/vInMaxLocal;
					
			//Find the min and max
			for (var i = 0, l = arr.length; i < l; i++)
			{
				if (arr[i] > max)
					max = arr[i];
				if (arr[i] < min)
					min = arr[i];
			}
	
			var vPeakToPeak = Math.abs(max - min);
			var maxVol = vPeakToPeak / vInMaxLocal;  //If we have a peak to peak voltage of 10 V, we want max sound, normalize to [-1, 1]
			var norm = Math.max(Math.abs(min), Math.abs(max));
	
			if (max != 0.0)		
			{
				for (var i = 0, l = arr.length; i < l; i++)
				{
					arr[i] = maxVol*arr[i] / norm;	
				}
			}
			else  //Fill in with zeros
			{
				for (var i = 0, l = arr.length; i < l; i++)
				{
					arr[i] = 0.0;	
				}
			}
		}

		this.normalizeAllSounds = function()
		{
			//Normalize the sound buffer that will be heard		
			this.normalizeSound(this.inSignal.data);
			for (var i = 0; i < this.outSignals.length; i++)
			{
				this.normalizeSound(this.outSignals[i].data);
			}		
		}

		this.playTone = function()
		{
			this.soundStarted();		
			var self = this;		
			if (this.isChrome)
			{	
				this.outSrc = this.audioChrome.createBufferSource();

				if (this.inSignal.listen)
					this.outSrc.buffer = this.inSignal.buffer;
				else
				{
					for (var i = 0; i < this.outSignals.length; i++)
					{
						if (this.outSignals[i].listen)	
							this.outSrc.buffer = this.outSignals[i].buffer;
					}		
				}				
  				
				this.outSrc.connect(this.audioChrome.destination);
				this.outSrc.noteOn(0);
				this.isPlaying = true;
				this.chromeTimer = setTimeout(function(){
					self.isPlaying = false;
					self.soundStopped();
				}, this.outSrc.buffer.duration * 1000);
		
			}
			else if (this.isMoz)
			{
				var playedAudioData;
				var currentWritePosition = 0;
				var currentPlayPosition = 0;
				var prebufferSize = 22050 / 2; // buffer 500ms
				var tail = null;
								
				if (this.inSignal.listen)
					playedAudioData = this.inSignal.data;
				else
				{
					for (var i = 0; i < this.outSignals.length; i++)
					{
						if (this.outSignals[i].listen)	
							playedAudioData = this.outSignals[i].data;
					}
				}

				this.isPlaying = true;
				
				// The function called with regular interval to populate the audio output buffer.		
				this.playAudio = setInterval(function()
				{
					var written;					
					currentPlayPosition = self.audioMoz.mozCurrentSampleOffset();
					
					// Check if some data was not written in previous attempts.
					if (tail)
					{
						written = self.audioMoz.mozWriteAudio(tail);
						currentWritePosition += written;
						if (written < tail.length)
						{
							// Not all the data was written, saving the tail...
            	tail = tail.subarray(written); 
							return; //... and exit the function.
						}
						tail = null;
					}

					// Check if we need add some data to the audio output
					var available = Math.floor(currentPlayPosition + prebufferSize - currentWritePosition);
					if (available > 0)
					{
						var data = playedAudioData.subarray(currentWritePosition); 
						// Writting the data
						written = self.audioMoz.mozWriteAudio(data);
						// Not all the data was written, saving the tail
						if(written <= data.length)
							tail = data.subarray(written);
						currentWritePosition += written;
					}
				}, 100);
				
				this.mozTimer = setTimeout(function(){
		  		clearInterval(self.playAudio);
					self.isPlaying = false;
					self.soundStopped();
				}, this.soundLength*1000);	
			}
		}

		this.stopTone = function()
		{
			if (this.isPlaying)
			{	
				if (this.isChrome)
				{
					clearTimeout(this.chromeTimer);
					this.outSrc.noteOff(0);
				}	
				else if (this.isMoz)
				{
					clearTimeout(this.mozTimer);
					clearInterval(this.playAudio);
				}
				this.isPlaying = false;
			}
			this.soundStopped();
		}
	}
	
	//////////PUBLIC FIELDS AND METHODS//////////
	return {
		Player: Player
	};
}());
