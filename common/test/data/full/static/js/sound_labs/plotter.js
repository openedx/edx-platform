var Plotter = (function() {

	//////////PRIVATE FIELDS AND METHODS//////////
	var Utils =
	{
		TWO_PI: 2.0*Math.PI,
		PI_DIV_2: Math.PI/2.0,

		getxPix : function(fx, fleft, fwidth, wleft, wwidth)
		{
			return Math.round(wleft + wwidth * (fx - fleft) / fwidth);
		},
		
		getxFromPix : function(wx, wleft, wwidth, fleft, fwidth)
		{
			return fleft + fwidth * (wx - wleft) / wwidth;
		},
	
		getyPix : function(fy, fbottom, fheight, wbottom, wheight)
		{
			return Math.round(wbottom - wheight * (fy - fbottom) / fheight);
		},
		
		getyFromPix : function(wy, wbottom, wheight, fbottom, fheight)
		{
			return fbottom + fheight * (wbottom - wy) / wheight;
		},
		
		log10: function(x)
		{
			return Math.log(x)/Math.LN10;
		}
	};

	var Color =
	{
		//Old palette
		/*background : "rgb(0, 51, 102)", //0.0, 0.2, 0.4
		black : "rgb(0, 0, 0)", //0.0
		lodarkgray : "rgb(26, 26, 26)", //0.1 = 25.5
		darkgray : "rgb(51, 51, 51)", //0.2
		lomidgray : "rgb(102, 102, 102)", //0.4
		midgray : "rgb(128, 128, 128)", //0.5 = 127.5
		himidgray : "rgb(153, 153, 153)", //0.6
		litegray : "rgb(204, 204, 204)", //0.8
		white : "rgb(255, 255, 255)", //1.0

		red : "rgb(255, 0, 0)",
		green : "rgb(0, 255, 0)",
		blue : "rgb(255, 255, 0)",
		yellow : "rgb(255, 255, 0)",
		cyan : "rgb(0, 255, 255)",
		magenta : "rgb(255, 0, 255)",*/
		
		
		//Solarized palette: http://ethanschoonover.com/solarized
		base03 :   "#002b36",
		base02 :   "#073642",
		base015:   "#30535c",
		base01 :   "#586e75",
		base00 :   "#657b83",
		base0  :   "#839496",
		base1  :   "#93a1a1",
		base2  :   "#eee8d5",
		base3  :   "#fdf6e3",
		yellow :   "#b58900",
		orange :   "#cb4b16",
		red    :   "#dc322f",
		magenta:   "#d33682",
		violet :   "#6c71c4",
		blue   :   "#268bd2",
		cyan   :   "#2aa198",
		green  :   "#859900",
		//lightgreen: "#c3cd82
		//lightblue: "#95c6e9",
		lightblue: "#00bfff",
		lightyellow: "#ffcf48",
		lightgreen: "#1df914",
		lightmagenta: "#ff3656"
	};
	
	////////// GENERAL DRAWING ROUTINES //////////
	
	function drawLine(c, x1, y1, x2, y2)
	{
		c.beginPath();
		c.moveTo(x1 + 0.5, y1 + 0.5);
		c.lineTo(x2 + 0.5, y2 + 0.5);
		c.stroke();
	}

	//Draws a rectangle, top left corner x1, y1 and bottom right corner x2, y2
	function drawRect(c, x1, y1, x2, y2)
	{
		c.strokeRect(x1 + 0.5, y1 + 0.5, x2 - x1 + 1.0, y2 - y1 + 1.0);
	}

	function fillRect(c, x1, y1, x2, y2)
	{
		c.fillRect(x1, y1, x2 - x1 + 1.0, y2 - y1 + 1.0);
	}

	function clearRect(c, x1, y1, x2, y2)
	{
		c.clearRect(x1 + 0.5, y1 + 0.5, x2 - x1 + 1.0, y2 - y1 + 1.0);
	}

	function drawPixel(c, x, y)
	{
		c.fillRect(x, y, 1.0, 1.0);
	}

	function drawPoint(c, x, y, radius)
	{
		c.beginPath();
		c.arc(x + 0.5, y + 0.5, radius, 0, Utils.TWO_PI, true); //Last param is anticlockwise
		c.fill();
	}

	function drawHollowPoint(c, x, y, radius)
	{
		c.beginPath();
		c.arc(x + 0.5, y + 0.5, radius, 0, Utils.TWO_PI, true); //Last param is anticlockwise
		c.stroke();
	}

	function drawTriangle(c, x1, y1, x2, y2, x3, y3)
	{
		c.beginPath();
		c.moveTo(x1 + 0.5, y1 + 0.5);
		c.lineTo(x2 + 0.5, y2 + 0.5);
		c.lineTo(x3 + 0.5, y3 + 0.5);
		c.closePath();
		c.stroke();
	}

	function fillTriangle(c, x1, y1, x2, y2, x3, y3)
	{
		c.beginPath();
		c.moveTo(x1 + 0.5, y1 + 0.5);
		c.lineTo(x2 + 0.5, y2 + 0.5);
		c.lineTo(x3 + 0.5, y3 + 0.5);
		c.closePath();
		c.fill();
	}

	function drawHalfCircle(c, x, y, radius, concaveDown) //For inductance only
	{
		c.beginPath();
		if (concaveDown)
			c.arc(x + 0.5, y + 0.5, radius, 0, Math.PI, true); //Last param is anticlockwise
		else
			c.arc(x + 0.5, y + 0.5, radius, Math.PI, 0, true); //Last param is anticlockwise
		c.stroke();
	}

	function drawDiamond(c, x, y, h)
	{
		var xc = x + 0.5;
		var yc = y + 0.5;

		c.beginPath();
		c.moveTo(xc-h, yc);
		c.lineTo(xc, yc-h);
		c.lineTo(xc+h, yc);
		c.lineTo(xc, yc+h);
		c.closePath();

		c.fill();
	}

	function drawX(c, x, y, h)
	{
		var xc = x + 0.5;
		var yc = y + 0.5;

		c.beginPath();
		c.moveTo(xc+h, yc-h);
		c.lineTo(xc-h, yc+h);
		c.moveTo(xc-h, yc-h);
		c.lineTo(xc+h, yc+h);
		c.stroke();
	}
	
	function drawArrow(c, x1, y1, x2, y2, base, height)
	{
		var xs1 = x1 + 0.5;
		var ys1 = y1 + 0.5;
		var xs2 = x2 + 0.5;
		var ys2 = y2 + 0.5;
		var xv = x2 - x1;
		var yv = y2 - y1;
		var ang = Math.atan2(-yv, xv);

		c.beginPath();
		//Arrow line
		c.moveTo(xs1, ys1);
		c.lineTo(xs2, ys2);
		c.stroke();
		//Arrow head, first draw a triangle with top on origin then translate/rotate to orient and fit on line
		c.save();
		c.beginPath();
		c.translate(xs2, ys2);
		c.rotate(Utils.PI_DIV_2-ang);

		c.moveTo(0, 0);
		c.lineTo(-base, height);
		c.lineTo(base, height);
		c.closePath();
		c.fill();
		//c.stroke();
		c.restore();
	}
	
	function DrawingZone(left, top, width, height)
	{
		this.left = left;
		this.top = top;
		this.width = width;
		this.height = height;
		this.right = left + width - 1;
		this.bottom = top + height - 1;
	}
	
	function Graph(x, y, width, height, canvas, buffer)
	{
		this.canvas = canvas;
		this.buffer = buffer;
		this.canvas_ctx = canvas.getContext("2d");
		this.buffer_ctx = buffer.getContext("2d");
		this.canvasColor = Color.base02; //Color.background : "rgb(0, 51, 102)"
		
		//Use the screen canvas
		this.ctx = this.canvas_ctx;
		
		this.drawingZone = new DrawingZone(x, y, width, height);
		this.drawingZoneColor = Color.base03; //Color.black;
		this.drawingZoneBorderColor = Color.base01; //Color.lomidgray;

		this.xGridColor = Color.base015; //Color.darkGray;
		this.xAxisColor = Color.base00;  //Color.himidgray;
		this.xLabelColor = Color.base1;  //Color.himidgray;
		this.xTextColor = Color.base2;   //Color.litegray;

		this.yGridColor = Color.base015; //Color.darkGray;
		this.yAxisColor = Color.base00;  //Color.himidgray;
		this.yLabelColor = Color.base1;  //Color.himidgray;
		this.yTextColor = Color.base2;   //Color.litegray;
		
		this.xText = "x";
		this.yText = "y";

		this.xmin = -1.0;
		this.xmax = 1.0;
		this.xspan = 2.0;
		this.ymin = -10.0;
		this.ymax = 10.0;
		this.yspan = 20.0;

		this.x0 = 0.0;
		this.y0 = 0.0;
		this.wx0 = 0;
		this.wy0 = 0;
		this.xShortTickStep = 0.1;
		this.xShortTickMin = this.xmin;
		this.xShortTickMax = this.xmax;

		this.xLongTickStep = 0.2;
		this.xLongTickMin = this.xmin;
		this.xLongTickMax = this.xmax;

		this.xLabelStep = 0.2;
		this.xLabelMin = this.xmin;
		this.xLabelMax = this.xmax;

		this.xGridStep = 0.2;
		this.xGridMin = this.xmin;
		this.xGridMax = this.xmax;

		this.formatxzero = true;
		this.formatyzero = true;

		this.yShortTickStep = 1;
		this.yShortTickMin = this.ymin;
		this.yShortTickMax = this.ymax;

		this.yLongTickStep = 2;
		this.yLongTickMin = this.ymin;
		this.yLongTickMax = this.ymax;

		this.yLabelStep = 2;
		this.yLabelMin = this.ymin;
		this.yLabelMax = this.ymax;

		this.yGridStep = 2;
		this.yGridMin = this.ymin;
		this.yGridMax = this.ymax;

		this.automaticxLabels = true;
		this.xLabelyOffset = 7;
		this.automaticyLabels = true;
		this.yLabelxOffset = -7;

		this.xTextxOffset = 9;
		this.yTextyOffset = -9;
		
		this.hasxLog = false;
		this.hasyLog = false;
		this.xPowerMin = 1;
		this.xPowerMax = 5;
		this.yPowerMin = 1;
		this.yPowerMax = 5;
		this.xLabelDecimalDigits = 1;
		this.yLabelDecimalDigits = 1;

		this.showxGrid = true;
		this.showyGrid = true;
		this.showBorder = true;
		this.showxShortTicks = true;
		this.showxLongTicks = true;
		this.showxLabels = true;
		this.showyShortTicks = true;
		this.showyLongTicks = true;
		this.showyLabels = true;
		this.showxAxis = true;
		this.showxText = true;
		this.showyAxis = true;
		this.showyText = true;

		this.paintOn = function(where) //On what context the drawing commands will operate
		{
			if (where == "buffer")
				this.ctx = this.buffer_ctx;
			else if (where == "canvas")
				this.ctx = this.canvas_ctx;  //Default behavior
		};
		
		this.paintBuffer = function() //Paints buffer on screen canvas
		{
			this.canvas_ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
			this.canvas_ctx.drawImage(buffer, 0, 0);
		};
		
		this.paintCanvas = function() //Paints screen canvas on buffer
		{
			this.buffer_ctx.clearRect(0, 0, this.buffer.width, this.buffer.height);
			this.buffer_ctx.drawImage(canvas, 0, 0);
		};		
		
		this.drawBorder = function()
		{
			this.ctx.strokeStyle = this.drawingZoneBorderColor;
			drawRect(this.ctx, this.drawingZone.left, this.drawingZone.top, this.drawingZone.right - 1, this.drawingZone.bottom - 1);
		};

		this.drawxAxis = function()
		{
			this.wy0 = this.getyPix(this.y0);
			this.ctx.strokeStyle = this.xAxisColor;
			drawLine(this.ctx, this.drawingZone.left, this.wy0, this.drawingZone.right + 6, this.wy0);
			drawLine(this.ctx, this.drawingZone.right + 3, this.wy0 - 3, this.drawingZone.right + 3, this.wy0 + 3);
			drawLine(this.ctx, this.drawingZone.right + 4, this.wy0 - 2, this.drawingZone.right + 4, this.wy0 + 2);
			drawLine(this.ctx, this.drawingZone.right + 5, this.wy0 - 1, this.drawingZone.right + 5, this.wy0 + 1);
		};
		
		/*
		if (this.hasxLog)
						wx = this.getxPix(Utils.log10(x));
		if (this.hasyLog)
						wy = this.getyPix(Utils.log10(y));
		*/
						
		/*
		this.ctx.textAlign = "left";
		this.ctx.textAlign = "center";
		this.ctx.textAlign = "right";
		this.ctx.textBaseline = "top";
		this.ctx.textBaseline = "middle";
		this.ctx.textBaseline = "bottom";
		this.ctx.textBaseline = "alphabetic";
		*/
						
		this.drawxLog = function()
		{
			var power;
			var x;
			var wx;
			var wy = this.drawingZone.bottom + 12;
			var str;
			
			//Don't draw grid line when on border of graph
			for(var p = this.xPowerMin; p <= this.xPowerMax; p++)
			{
				wx = this.getxPix(p);
				if(wx > this.drawingZone.right)
						wx = this.drawingZone.right;
				//Labeled grid line
				if (p != this.xPowerMin && p != this.xPowerMax) //Don't draw line on left or right border of graph
				{ 
					this.ctx.strokeStyle = this.xGridColor;
					drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.top);
				}	
				//Long ticks
				this.ctx.strokeStyle = this.xLabelColor;
				drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.bottom + 4);
				//Now the labels
				this.ctx.fillStyle = this.xLabelColor;
				this.ctx.strokeStyle = this.xLabelColor;
				str = "10^{" + p.toFixed(0) + "}";
				this.drawSubSuperScript(this.ctx, str, wx, wy, "center", "top");
								
				if (p != this.xPowerMax)
				{
					for(var i = 2; i < 10; i++)
					{
						x = p + Utils.log10(i);
						wx = this.getxPix(x);
						//Grid
						this.ctx.strokeStyle = this.xGridColor;
						drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.top);
						//Short ticks
						this.ctx.strokeStyle = this.xLabelColor;
						drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.bottom + 2);
					}
				}
			}
		}
		
		this.drawyLog = function()
		{
			var power;
			var y;
			var wy;
			var wx = this.drawingZone.left - 7;
			var str;
			
			//Don't draw grid line when on border of graph
			for(var p = this.yPowerMin; p <= this.yPowerMax; p++)
			{
				wy = this.getyPix(p);	
				if(wy < this.drawingZone.top)
					wy = this.drawingZone.top;
				//Labeled grid line
				if (p != this.yPowerMin && p != this.yPowerMax) //Don't draw line on left or right border of graph
				{ 
					this.ctx.strokeStyle = this.yGridColor;
					drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.right, wy);
				}	
				//Long ticks
				this.ctx.strokeStyle = this.yLabelColor;
				drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.left - 4, wy);
				//Now the labels
				this.ctx.fillStyle = this.yLabelColor;
				this.ctx.strokeStyle = this.yLabelColor;
				str = "10^{" + p.toFixed(0) + "}";
				this.drawSubSuperScript(this.ctx, str, wx, wy, "right", "middle");
				
				if (p != this.xPowerMax)
				{
					for(var i = 2; i < 10; i++)
					{
						y = p + Utils.log10(i);
						wy = this.getyPix(y);
						//Grid
						this.ctx.strokeStyle = this.yGridColor;
						drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.right, wy);
						//Short ticks
						this.ctx.strokeStyle = this.xLabelColor;
						drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.left - 2, wy);
					}
				}
			}
		}

		this.drawxGrid = function()
		{
			var x;
			var wx;

			this.ctx.strokeStyle = this.xGridColor;

			if(this.xGridStep > 0)
			{
				for(x = this.xGridMin; x <= this.xGridMax; x += this.xGridStep)
				{
					wx = this.getxPix(x);
					if(wx > this.drawingZone.right)
						wx = this.drawingZone.right;
					drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.top);
				}
			}
		};

		this.drawxLongTicks = function()
		{
			var x;
			var wx;

			this.ctx.strokeStyle = this.xLabelColor;

			if(this.xLongTickStep > 0)
			{
				for(x = this.xLongTickMin; x <= this.xLongTickMax; x += this.xLongTickStep)
				{
					wx = this.getxPix(x);
					if(wx > this.drawingZone.right)
						wx = this.drawingZone.right;
					drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.bottom + 4);
				}
			}
		};

		this.drawxShortTicks = function()
		{
			var x;
			var wx;

			this.ctx.strokeStyle = this.xLabelColor;

			if(this.xShortTickStep > 0)
			{
				for(x = this.xShortTickMin; x <= this.xShortTickMax; x += this.xShortTickStep)
				{
					wx = this.getxPix(x);
					if(wx > this.drawingZone.right)
						wx = this.drawingZone.right;
					drawLine(this.ctx, wx, this.drawingZone.bottom, wx, this.drawingZone.bottom + 2);
				}
			}
		};
		
		this.drawyAxis = function()
		{
			this.wx0 = this.getxPix(this.x0);

			this.ctx.strokeStyle = this.yAxisColor;
			drawLine(this.ctx, this.wx0, this.drawingZone.bottom, this.wx0, this.drawingZone.top - 6);
			drawLine(this.ctx, this.wx0 - 3, this.drawingZone.top - 3, this.wx0 + 3, this.drawingZone.top - 3);
			drawLine(this.ctx, this.wx0 - 2, this.drawingZone.top - 4, this.wx0 + 2, this.drawingZone.top - 4);
			drawLine(this.ctx, this.wx0 - 1, this.drawingZone.top - 5, this.wx0 + 1, this.drawingZone.top - 5);
		};

		this.drawyLongTicks = function()
		{
			var y;
			var wy;

			this.ctx.strokeStyle = this.yLabelColor;

			if(this.yLongTickStep > 0)
			{
				for(y = this.yLongTickMin; y <= this.yLongTickMax; y += this.yLongTickStep)
				{
					wy = this.getyPix(y);	
					if(wy < this.drawingZone.top)
						wy = this.drawingZone.top;
					drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.left - 4, wy);
				}
			}
		};

		this.drawyShortTicks = function()
		{
			var y;
			var wy;

			this.ctx.strokeStyle = this.yLabelColor;

			if(this.yShortTickStep > 0)
			{
				for(y = this.yShortTickMin; y <= this.yShortTickMax; y += this.yShortTickStep)
				{
					wy = this.getyPix(y);
					if(wy < this.drawingZone.top)
						wy = this.drawingZone.top;
					drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.left - 2, wy);
				}
			}
		};

		this.drawyGrid = function()
		{
			var y;
			var wy;

			this.ctx.strokeStyle = this.yGridColor;

			if(this.yGridStep > 0)
			{
				for(y = this.yGridMin; y <= this.yGridMax; y += this.yGridStep)
				{
					wy = this.getyPix(y);
					if(wy < this.drawingZone.top)
						wy = this.drawingZone.top;
					drawLine(this.ctx, this.drawingZone.left, wy, this.drawingZone.right, wy);
				}
			}
		};

		this.drawxLabels = function()
		{
			var x;
			var wx = 0;
			var wy = this.drawingZone.bottom + this.xLabelyOffset;
			//y coordinate of all labels
			var str;

			this.ctx.font = "8pt Verdana bold";
			this.ctx.fillStyle = this.xLabelColor;
			this.ctx.strokeStyle = this.xLabelColor;
			this.ctx.textAlign = "center";
			this.ctx.textBaseline = "top";
			
			if(this.automaticxLabels)
			{
				for( x = this.xLabelMin; x <= this.xLabelMax; x += this.xLabelStep)
				{
					wx = this.getxPix(x);

					if(Math.abs(x) < 0.00001 && this.formatxzero)
						str = "0";
					else
						str = x.toFixed(this.xLabelDecimalDigits);

					//this.ctx.fillText(this.text, xmid, ymid);
					this.ctx.strokeText(str, wx, wy);
					this.ctx.fillText(str, wx, wy);
				}
			}
		}
		
		this.drawxText = function()
		{
			var x;
			var wx = this.drawingZone.right + this.xTextxOffset;
			var wy = this.getyPix(this.y0);

			this.ctx.fillStyle = this.xTextColor;
			this.ctx.strokeStyle = this.xTextColor;
			this.drawSubSuperScript(this.ctx, this.xText, wx, wy, "left", "middle", "10pt Verdana bold", "8pt Verdana bold");
		};

		this.drawyLabels = function()
		{
			var y;
			var wy = 0;
			var wx = this.drawingZone.left + this.yLabelxOffset;
			var str;

			this.ctx.font = "8pt Verdana bold";
			this.ctx.fillStyle = this.yLabelColor;
			this.ctx.strokeStyle = this.yLabelColor;
			this.ctx.textAlign = "right";
			this.ctx.textBaseline = "middle";
			
			if(this.automaticyLabels)
			{
				for( y = this.yLabelMin; y <= this.yLabelMax; y += this.yLabelStep)
				{
					wy = this.getyPix(y);

					if(Math.abs(y) < 0.00001 && this.formatyzero)
						str = "0";
					else
						str = y.toFixed(this.yLabelDecimalDigits);

					this.ctx.strokeText(str, wx, wy);
					this.ctx.fillText(str, wx, wy);
				}
			}
		};

		this.drawyText = function()
		{
			var x;
			var wx = this.getxPix(this.x0);
			var wy = this.drawingZone.top + this.yTextyOffset;

			this.ctx.fillStyle = this.yTextColor;
			this.ctx.strokeStyle = this.yTextColor;
			this.drawSubSuperScript(this.ctx, this.yText, wx, wy, "left", "bottom", "10pt Verdana bold", "8pt Verdana bold");
		};
		
		this.parseSubSuperScriptText = function(str)
		{
			/*var regExpSub = /_\{(.*?)\}/g;
			var regExpSup = /\^\{(.*?)\}/g;
			var subs = [];
			var sups = [];
			var text = [];
			var finalText = [];
			var isSub = false;
			var isSup = false;

			subs = str.match(regExpSub);
			for (var i = 0; i < subs.length; i++)
			{
				subs[i] = subs[i].substring(2, subs[i].length - 1); //Discard _{ and }
			}

			sups = str.match(regExpSup);
			for (var i = 0; i < sups.length; i++)
			{
				sups[i] = sups[i].substring(2, sups[i].length - 1); //Discard ^{ and }
			}*/
	   	
    	var len = str.length;
   		var i = 0;
   		var start;
   		var end;
   		found = false;
   		var text = [];
   		var type;
   		var ntext = "";
	   	
   		while (i < len)
   		{
   			if (str[i] == "_") //Encountered a potential subscript _
   				type = "sub";
   			else if (str[i] == "^")  //Encountered a potential superscript ^
   				type = "sup";
   			
   			if (type == "sub" || type == "sup")
   			{
   				if (str[i+1] == "{")
   				{
   					i += 2; //Discard _{ or ^{
   					start = i;
   					found = false;
   					while (i < len) //Look for }
   					{
   						if (str[i] == "}")
   						{
   							found = true;
   							end = i;
   							break;
   						}
   						i++;
   					}
   					if (found && end > start) //Discard empty subscript ie _{}
   					{
   						//Store previous normal text if not empty and tag it as so
   						if (ntext.length != 0)
   						{
   							text.push({s: ntext, type: "normal"});
   							ntext = "";
   						}	
   						//Store subscript or superscript and tag it as so
   						if (type == "sub")
   							text.push({s: str.substring(start, end), type: "sub"});
   						else if (type == "sup")
   							text.push({s: str.substring(start, end), type: "sup"});
   						i = end + 1;
   					}
   					else
   						i = start - 2; //Nothing was found, backtrack to _ or ^
   				}
   			}
   			ntext += str[i];
   			if (i == len - 1 && ntext.length != 0) //We've reached the end, store normal text if not empty and tag it as so 
   				text.push({s: ntext, type: "normal"});
   			i++;
   		}
   	
			return text;
		}
  
		this.subSuperScriptLength = function(c, text, fNormal, fSubSup)
		{
			var fontNormal = fNormal;
			var fontSubSup = fSubSup;
				    	    
   		var xpos = 0;
   	
   		for (var i = 0; i < text.length; i++)
   		{		
				if (text[i].type == "normal")
					c.font = fontNormal;
				else if (text[i].type == "sub")
					c.font = fontSubSup;
				else
					c.font = fontSubSup;
				xpos += c.measureText(text[i].s).width;	
			}
   	
			return xpos;
		}	
  	
		this.drawSubSuperScript = function(c, str, x, y, xway, yway, fNormal, fSubSup)
		{
			var fontNormal = (typeof fNormal == 'undefined') ? "8pt Verdana bold" : fNormal;
			var fontSubSup = (typeof fSubSup == 'undefined') ? "7pt Verdana bold" : fSubSup;
			
			this.ctx.textAlign = "left"; 
			this.ctx.textBaseline = yway;
	    	    	    
   		var text = this.parseSubSuperScriptText(str);
   		var len = this.subSuperScriptLength(c, text, fontNormal, fontSubSup);
   		var xposIni = x;
   		var yposIni = y;
   		var xpos, ypos;
   	
   		if (xway == "left")
   			xpos = xposIni;
   		else if (xway == "right")
   			xpos = xposIni - len;
   		else if (xway == "center")
   			xpos = xposIni - len/2;	
   	
   		//Draw the text
   		for (var i = 0; i < text.length; i++)
   		{		
				if (text[i].type == "normal")
				{
					c.font = fontNormal;
					ypos = yposIni;
				}	
				else if (text[i].type == "sub")
				{
					c.font = fontSubSup;
					ypos = yposIni + 3;
				}
				else
				{
					c.font = fontSubSup;
					ypos = yposIni - 5;
				}
				c.strokeText(text[i].s, xpos, ypos);
				c.fillText(text[i].s, xpos, ypos);
				//Advance x position
				xpos += c.measureText(text[i].s).width + 2;	
			}   		
		}

		this.paint = function()
		{
			//Clears the canvas entirely with background color
			this.ctx.fillStyle = this.canvasColor;
			this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
			
			//Clear drawing zone
			this.ctx.fillStyle = this.drawingZoneColor;
			fillRect(this.ctx, this.drawingZone.left, this.drawingZone.top, this.drawingZone.right, this.drawingZone.bottom);

			if (!this.hasxLog)
			{
				if(this.showxGrid)
					this.drawxGrid();
			}
			
			if (!this.hasyLog)
			{	
				if(this.showyGrid)
					this.drawyGrid();
			}		

			if(this.showBorder)
				this.drawBorder();

			if (!this.hasxLog)
			{
				if(this.showxShortTicks)
					this.drawxShortTicks();
				if(this.showxLongTicks)
					this.drawxLongTicks();
				if(this.showxLabels)
					this.drawxLabels();
			}		

			if (!this.hasyLog)
			{
				if(this.showyShortTicks)
					this.drawyShortTicks();
				if(this.showyLongTicks)
					this.drawyLongTicks();
				if(this.showyLabels)
					this.drawyLabels();
			}		

			if (this.hasxLog)
				this.drawxLog();
				
			if (this.hasyLog)
				this.drawyLog();
			
			if(this.showxAxis)
				this.drawxAxis();
			if(this.showxText)
				this.drawxText();
			
			if(this.showyAxis)
				this.drawyAxis();
			if(this.showyText)
				this.drawyText();
						
			
		};

		this.drawCurve = function(f, color)
		{
			var wx, wy;
			var x, y;

			this.ctx.strokeStyle = color;
			wx = this.drawingZone.left;
			x = this.getxFromPix(wx);
			y = f(x);
			wy = this.getyPix(y);

			this.ctx.beginPath();
			this.ctx.moveTo(wx + 0.5, wy + 0.5);

			while(wx < this.drawingZone.right)
			{
				wx++;
				x = this.getxFromPix(wx);
				y = f(x);
				wy = this.getyPix(y);
				this.ctx.lineTo(wx + 0.5, wy + 0.5);
			}
			//this.ctx.closePath();

			this.ctx.stroke();
		};

		this.drawArray = function(tt, ff, color)
		{
			var wx, wy;
			var x, y;
			var l = tt.length;
			this.ctx.save();
			this.ctx.beginPath();
			this.ctx.rect(this.drawingZone.left, this.drawingZone.top, this.drawingZone.width, this.drawingZone.height);
			this.ctx.clip();
			this.ctx.strokeStyle = color;//"rgb(256, 0, 0)";// Color.orange; //yellow, orange, red, magenta, violet, blue, cyan, green

			wx = this.getxPix(tt[0]);
			wy = this.getyPix(ff[0]);
			this.ctx.beginPath();
			this.ctx.moveTo(wx + 0.5, wy + 0.5);

			for (var i = 0; i < l; i++)
			{
				wx = this.getxPix(tt[i]);
				wy = this.getyPix(ff[i]);
				//this.ctx.lineTo(wx + 0.5, wy + 0.5);
				this.ctx.lineTo(wx, wy);
			}

			//this.ctx.closePath();

			this.ctx.stroke();
			this.ctx.restore();
		};

		this.drawPoint = function(x, y, color)
		{
			this.ctx.fillStyle = color;
			drawPoint(this.ctx, this.getxPix(x), this.getyPix(y), 4);
		};

		this.drawHollowPoint = function(x, y, color)
		{
			this.ctx.strokeStyle = color;
			drawHollowPoint(this.ctx, this.getxPix(x), this.getyPix(y), 4);
		};

		this.drawDiamond = function(x, y, color)
		{
			this.ctx.fillStyle = color;
			drawDiamond(this.ctx, this.getxPix(x), this.getyPix(y), 4);
		};

		this.drawX = function(x, y, color)
		{
			this.ctx.strokeStyle = color;
			drawX(this.ctx, this.getxPix(x), this.getyPix(y), 4);
		};

		this.drawLine = function(x1, y1, x2, y2, color)
		{
			this.ctx.strokeStyle = color;
			drawLine(this.ctx, this.getxPix(x1), this.getyPix(y1), this.getxPix(x2), this.getyPix(y2));
		};

		this.drawArrow = function(x1, y1, x2, y2, color)
		{
			this.ctx.strokeStyle = color;
			this.ctx.fillStyle = color;
			drawArrow(this.ctx, this.getxPix(x1), this.getyPix(y1), this.getxPix(x2), this.getyPix(y2), 5, 10);
		};

		this.getxPix = function(x)
		{
			return Math.round(this.drawingZone.left + this.drawingZone.width * (x - this.xmin) / this.xspan);
		};

		this.getyPix = function(y)
		{
			return Math.round(this.drawingZone.bottom - this.drawingZone.height * (y - this.ymin) / this.yspan);
		};

		this.getxFromPix = function(wx)
		{
			return (this.xmin + this.xspan * (wx - this.drawingZone.left) / this.drawingZone.width);
		};

		this.getyFromPix = function(wy)
		{
			return (this.ymin + this.yspan * (this.drawingZone.bottom - wy) / this.drawingZone.height);
		};

		this.isInside = function(x, y)
		{
			if((this.drawingZone.left <= x) && (x <= this.drawingZone.right) && (this.drawingZone.top <= y) && (y <= this.drawingZone.bottom))
				return true;
			else
				return false;
		};

		this.inBounds = function(x, y)
		{
			if((this.xmin <= x) && (x <= this.xmax) && (this.ymin <= y) && (y <= this.ymax))
				return true;
			else
				return false;
		};
	}

	//////////PUBLIC FIELDS AND METHODS//////////
	return {

		Utils: Utils,
		Color: Color,
		DrawingZone: DrawingZone,
		Graph: Graph,
	};
}());
