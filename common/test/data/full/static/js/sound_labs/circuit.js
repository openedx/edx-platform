var Circuit = (function() {

	var Color =
	{
		background : "rgb(0, 51, 102)", //0.0, 0.2, 0.4
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
		blue : "rgb(0, 0, 255)",
		yellow : "rgb(255, 255, 0)",
		cyan : "rgb(0, 255, 255)",
		magenta : "rgb(255, 0, 255)"
	};
	
	var Utils =
	{
		TWO_PI: 2.0*Math.PI,
		PI_DIV_2: Math.PI/2.0
	};
	
	function distance(x1, y1, x2, y2)
	{
		var dx = x2 - x1;
		var dy = y2 - y1;

		return Math.sqrt(dx * dx + dy * dy);
	}
	
	function transform(x, y, xt, yt, rot)
	{
		//First translate
		x -= xt;
		y -= yt;
		//Then rotate
		return {x: x * Math.cos(rot) - y * Math.sin(rot), y: x * Math.sin(rot) + y * Math.cos(rot)};
	}

	function closestGridPoint(gridStep, x)
	{
		return gridStep * Math.round(x / gridStep);
	}
	
	function getMousePosition(diagram, event)
	{
		var mouseX = event.pageX - (parseInt(diagram.element.offset().left) + parseInt(diagram.element.css('paddingLeft')) + parseInt(diagram.element.css('borderLeftWidth')));
		var mouseY = event.pageY - (parseInt(diagram.element.offset().top) + parseInt(diagram.element.css('paddingTop')) + parseInt(diagram.element.css('borderTopWidth')));
		return {x : mouseX,	y : mouseY};
	}
	
	function diagramMouseDown(event)
	{
		if (!event) event = window.event;
	  else event.preventDefault();
	  var canvas = (window.event) ? event.srcElement : event.target;
	  var diagram = canvas.diagram;
		var mpos = getMousePosition(diagram, event);

		for(var i = 0, len = diagram.components.length; i < len; i++)
		{
			if(diagram.components[i].isInside(mpos.x, mpos.y))
			{
				diagram.components[i].selected = true;
				diagram.startx = closestGridPoint(diagram.gridStep, mpos.x);
				diagram.starty = closestGridPoint(diagram.gridStep, mpos.y);
			}
		}
		
		return false;
	}

	function diagramMouseMove(event)
	{
		if (!event) event = window.event;
	  else event.preventDefault();
	  var canvas = (window.event) ? event.srcElement : event.target;
	  var diagram = canvas.diagram;
	  var mpos = getMousePosition(diagram, event);
		var componentSelected = false;

		//First check if any component if selected
		for(var i = 0, len = diagram.components.length; i < len; i++)
		{
			if(diagram.components[i].selected)
			{
				diagram.endx = closestGridPoint(diagram.gridStep, mpos.x);
				diagram.components[i].x += (diagram.endx - diagram.startx);
				diagram.startx = diagram.endx;
				diagram.endy = closestGridPoint(diagram.gridStep, mpos.y);
				diagram.components[i].y += (diagram.endy - diagram.starty);
				diagram.starty = diagram.endy;
				diagram.paint();
				componentSelected = true;
			}
		}

		if(!componentSelected)
		{
			for(var i = 0, len = diagram.components.length; i < len; i++)
			{
				if(diagram.components[i].isInside(mpos.x, mpos.y))
					diagram.components[i].selectable = true;
				else
					diagram.components[i].selectable = false;
				//Repaint only once, on a mouse enter or mouse leave
				if(diagram.components[i].previousSelectable != diagram.components[i].selectable)
				{
					diagram.components[i].previousSelectable = diagram.components[i].selectable;
					diagram.paint();
				}
			}
		}

		return false;
	}
	
	function diagramMouseUp(event)
	{
		if (!event) event = window.event;
	  else event.preventDefault();
	  var canvas = (window.event) ? event.srcElement : event.target;
	  var diagram = canvas.diagram;	
		var mpos = getMousePosition(diagram, event);

		for(var i = 0, len = diagram.components.length; i < len; i++)
		{
			//Unselect all
			diagram.components[i].selected = false;
		}
		diagram.startx = 0;
		diagram.endx = diagram.startx;
		diagram.starty = 0;
		diagram.endx = diagram.starty;

		return false;
	}
	
	function diagramDoubleClick(event)
	{
		if (!event) event = window.event;
	  else event.preventDefault();
	  var canvas = (window.event) ? event.srcElement : event.target;
	  var diagram = canvas.diagram;	
		
		alert(diagram.toString());
		
		return false;
	}
	
	function copyPrototype(descendant, parent)
	{
		var sConstructor = parent.toString();
		var aMatch = sConstructor.match(/\s*function (.*)\(/);
		if(aMatch != null)
		{
			descendant.prototype[aMatch[1]] = parent;
		}
		for(var m in parent.prototype)
		{
			descendant.prototype[m] = parent.prototype[m];
		}
	}
	
	function Diagram(element, frozen)
	{
		this.element = element;
		this.frozen = frozen;
		this.canvas = element[0];
		this.canvas.diagram = this;
		this.width = this.canvas.width;
		this.height = this.canvas.height;
		this.ctx = this.canvas.getContext("2d");
		this.background = Color.black;
		if (!this.frozen)
		{
			this.canvas.addEventListener('mousedown', diagramMouseDown, false);
			this.canvas.addEventListener('mousemove', diagramMouseMove, false);
			this.canvas.addEventListener('mouseup', diagramMouseUp, false);
			this.canvas.addEventListener('dblclick', diagramDoubleClick, false);
		}	
		//To disable text selection outside the canvas
		this.canvas.onselectstart = function(){return false;};
		this.components = [];
		this.gridStep = 5;
		this.startx = 0;
		this.endx = 0;
		this.starty = 0;
		this.endy = 0;
		this.showGrid = false;
		this.xGridMin = 10;
		this.xGridMax = 500;
		this.yGridMin = 10;
		this.yGridMax = 500;
		this.xOrigin = 0;
		this.yOrigin = 0;
		this.scale = 2; //Scaling is the same in x and y directions
		this.fontSize = 6;
		this.fontType = 'sans-serif'; 
	}
	
	Diagram.prototype.toString = function()
	{
		var result = "";
		for(var i = 0, len = this.components.length; i < len; i++)
		{
			result += this.components[i].toString();
		}
		
		return result;
	}
	
	Diagram.prototype.addNode = function(x, y)
	{
		var n = new Node(x, y);
		n.ctx = this.ctx;
		n.diagram = this;
		n.updateBoundingBox();
		this.components.push(n);
		return n;
	}
	
	Diagram.prototype.addWire = function(x1, y1, x2, y2)
	{
		var w = new Wire(x1, y1, x2, y2)
		w.ctx = this.ctx;
		w.diagram = this;
		w.updateBoundingBox();
		this.components.push(w);
		return w;
	}
	
	Diagram.prototype.addLabel = function(x, y, value, textAlign)
	{
		var l = new Label(x, y, value, textAlign)
		l.ctx = this.ctx;
		l.diagram = this;
		l.updateBoundingBox();
		this.components.push(l);
		return l;
	}
	
	Diagram.prototype.addResistor = function(x, y, value)
	{
		var r = new Resistor(x, y, value)
		r.ctx = this.ctx;
		r.diagram = this;
		r.updateBoundingBox();
		this.components.push(r);
		return r;
	}
	
	Diagram.prototype.addInductor = function(x, y, value)
	{
		var l = new Inductor(x, y, value)
		l.ctx = this.ctx;
		l.diagram = this;
		l.updateBoundingBox();
		this.components.push(l);
		return l;
	}
	
	Diagram.prototype.addCapacitor = function(x, y, value)
	{
		var c = new Capacitor(x, y, value)
		c.ctx = this.ctx;
		c.diagram = this;
		c.updateBoundingBox();
		this.components.push(c);
		return c;
	}
	
	Diagram.prototype.addMosfet = function(x, y, value, type)
	{
		var m = new Mosfet(x, y, value, type)
		m.ctx = this.ctx;
		m.diagram = this;
		m.updateBoundingBox();
		this.components.push(m);
		return m;
	}
	
	Diagram.prototype.addGround = function(x, y)
	{
		var g = new Ground(x, y)
		g.ctx = this.ctx;
		g.diagram = this;
		g.updateBoundingBox();
		this.components.push(g);
		return g;
	}
	
	Diagram.prototype.addDiode = function(x, y, value)
	{
		var d = new Diode(x, y, value)
		d.ctx = this.ctx;
		d.diagram = this;
		d.updateBoundingBox();
		this.components.push(d);
		return d;
	}
	
	Diagram.prototype.addSource = function(x, y, value, type)
	{
		var v = new Source(x, y, value, type)
		v.ctx = this.ctx;
		v.diagram = this;
		v.updateBoundingBox();
		this.components.push(v);
		return v;
	}
	
	Diagram.prototype.paint = function()
	{
		this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
		if (this.showGrid)
			this.drawGrid();
		
		for(var i = 0, len = this.components.length; i < len; i++)
		{
			this.components[i].paint();
		}	
	}
	
	Diagram.prototype.drawGrid = function()
	{
		this.ctx.fillStyle = Color.black;
		for(x = this.xGridMin; x <= this.xGridMax; x += this.gridStep)
		{
			for( y = this.yGridMin; y <= this.yGridMax; y += this.gridStep)
			{
				this.drawPixel(this.ctx, x, y);
			}
		}
	}
	//Drawing routines from schematic
	Diagram.prototype.drawLine = function(c, x1, y1, x2, y2)
	{
		c.beginPath();
		c.moveTo((x1 - this.xOrigin) * this.scale, (y1 - this.yOrigin) * this.scale);
		c.lineTo((x2 - this.xOrigin) * this.scale, (y2 - this.yOrigin) * this.scale);
		c.stroke();
	}
	
	Diagram.prototype.drawArc = function(c, x, y, radius,startRadians, endRadians, anticlockwise, width, filled)
	{
		c.lineWidth = width;
		c.beginPath();
		c.arc((x - this.xOrigin)*this.scale, (y - this.yOrigin)*this.scale, radius*this.scale, startRadians, endRadians, anticlockwise);
		if (filled) c.fill();
		else c.stroke();
	}
	
	Diagram.prototype.drawCircle = function(c, x, y, radius, filled)
	{
		this.drawArc(c, x, y, radius, 0, 2*Math.PI, false, 1, filled);
	}
	
	Diagram.prototype.drawText = function(c, str, x, y)
	{
		c.font = this.scale*this.fontSize + "pt " + this.fontType;
		c.fillText(str, (x - this.xOrigin) * this.scale, (y - this.yOrigin) * this.scale);
	}
	//End drawing routines
	
	Diagram.prototype.parseSubSuperScriptText = function(str)
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
  
  Diagram.prototype.subSuperScriptLength = function(c, text)
	{
		var fontNormal = this.scale*this.fontSize + "pt " + this.fontType;
    var fontSubSup = this.scale*(this.fontSize-2) + "pt " + this.fontType;
	    	    	    
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
  	
	Diagram.prototype.drawSubSuperScript = function(c, str, x, y, way)
	{
		var fontNormal = this.scale*this.fontSize + "pt " + this.fontType;
    var fontSubSup = this.scale*(this.fontSize-2) + "pt " + this.fontType;
	    	    	    
   	var text = this.parseSubSuperScriptText(str);
   	var len = this.subSuperScriptLength(c, text);
   	var xposIni = (x - this.xOrigin) * this.scale;
   	var yposIni = (y - this.yOrigin) * this.scale;
   	var xpos, ypos;
   	
   	if (way == "left")
   		xpos = xposIni;
   	else if (way == "right")
   		xpos = xposIni - len;
   	else if (way == "center")
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
			c.fillText(text[i].s, xpos, ypos);
			//Advance x position
			xpos += c.measureText(text[i].s).width;	
		}   		
	}

	//Draws a rectangle, top left corner x1, y1 and bottom right corner x2, y2
	Diagram.prototype.drawCrispLine = function(c, x1, y1, x2, y2)
	{
		c.beginPath();
		c.moveTo(x1 + 0.5, y1 + 0.5);
		c.lineTo(x2 + 0.5, y2 + 0.5);
		c.stroke();
	}
	
	Diagram.prototype.drawRect = function(c, x1, y1, x2, y2)
	{
		c.strokeRect(x1 + 0.5, y1 + 0.5, x2 - x1 + 1.0, y2 - y1 + 1.0);
	}

	Diagram.prototype.fillRect = function(c, x1, y1, x2, y2)
	{
		c.fillRect(x1, y1, x2 - x1 + 1.0, y2 - y1 + 1.0);
	}

	Diagram.prototype.clearRect = function(c, x1, y1, x2, y2)
	{
		c.clearRect(x1 + 0.5, y1 + 0.5, x2 - x1 + 1.0, y2 - y1 + 1.0);
	}

	Diagram.prototype.drawPixel = function(c, x, y)
	{
		c.fillRect(x, y, 1.0, 1.0);	
	}

	Diagram.prototype.drawPoint = function(c, x, y, radius)
	{
		c.beginPath();
		c.arc(x + 0.5, y + 0.5, radius, 0, Utils.TWO_PI, true); //Last param is anticlockwise  
		c.fill();
	}

	Diagram.prototype.drawHollowPoint = function(c, x, y, radius)
	{
		c.beginPath();
		c.arc(x + 0.5, y + 0.5, radius, 0, Utils.TWO_PI, true); //Last param is anticlockwise  
		c.stroke();  
	}

	Diagram.prototype.drawTriangle = function(c, x1, y1, x2, y2, x3, y3)
	{
		c.beginPath();
		c.moveTo(x1 + 0.5, y1 + 0.5);
		c.lineTo(x2 + 0.5, y2 + 0.5);
		c.lineTo(x3 + 0.5, y3 + 0.5);
		c.closePath();
		c.stroke();
	}

	Diagram.prototype.fillTriangle = function(c, x1, y1, x2, y2, x3, y3)
	{
		c.beginPath();
		c.moveTo(x1 + 0.5, y1 + 0.5);
		c.lineTo(x2 + 0.5, y2 + 0.5);
		c.lineTo(x3 + 0.5, y3 + 0.5);
		c.closePath();
		c.fill();
	}

	Diagram.prototype.drawHalfCircle = function(c, x, y, radius, concaveDown) //For inductance only
	{
		c.beginPath();
		if (concaveDown)
			c.arc(x + 0.5, y + 0.5, radius, 0, Math.PI, true); //Last param is anticlockwise
		else
			c.arc(x + 0.5, y + 0.5, radius, Math.PI, 0, true); //Last param is anticlockwise  
    c.stroke(); 
	}

	Diagram.prototype.drawDiamond = function(c, x, y, h)
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

	Diagram.prototype.drawX = function(c, x, y, h)
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

	Diagram.prototype.drawArrow = function(c, x1, y1, x2, y2, base, height)
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
			
	//***** COMPONENT *****//
	function Component(x, y, width, height)
	{
		this.x = x;
		this.y = y;
		
		this.boundingBox = [0, 0, 0, 0];
		this.transBoundingBox = [0, 0, 0, 0];
		this.xMiddle = 0;
		this.yMiddle = 0;

		this.previousSelectable = false;
		this.selectable = false;
		this.selected = false;
		this.ctx;
		this.diagram;
		this.color = Color.white;
		this.selectedColor = Color.red;
		this.eventListeners = {};
		//Label to the left
		this.label = {str: "", x: 0, y: 0, position: "left", show: true, color: Color.white}; //color: Color.lodarkgray
		//String representing value to the right
		this.valueString = {x: 0, y: 0, position: "right", show: true, suffix: "", decimal: -1, color: Color.white}; //color: Color.lodarkgray
				
		this.lineWidth = 1;
		this.rotation = 0;
		this.value = 0;
	}
	
	Component.prototype.addEventListener = function(type, eventListener)
	{
		if(!(type in this.eventListeners))
			this.eventListeners[type] = eventListener;
	}

	Component.prototype.removeEventListener = function(type, eventListener)
	{
		for(var i in this.eventListeners)
		{
			if(this.eventListeners[i] === eventListener)
				delete this.eventListeners[i].eventListener;
		}
	}

	Component.prototype.fireEvent = function(event)
	{
		if( typeof event == "string")
			(this.eventListeners[event])();
		else
			throw new Error("Event object missing 'type' property.");
	}
	
	Component.prototype.updateBoundingBox = function()
	{
		//Apply global transform
		this.transBoundingBox[0] = (this.boundingBox[0] - this.diagram.xOrigin) * this.diagram.scale;
		this.transBoundingBox[1] = (this.boundingBox[1] - this.diagram.yOrigin) * this.diagram.scale;
		this.transBoundingBox[2] = (this.boundingBox[2] - this.diagram.xOrigin) * this.diagram.scale;
		this.transBoundingBox[3] = (this.boundingBox[3] - this.diagram.yOrigin) * this.diagram.scale;
		//this.getMiddle();
		this.label.x = this.transBoundingBox[0]- 5;
		this.label.y = (this.transBoundingBox[3] - this.transBoundingBox[1]) / 2;
		this.valueString.x = this.transBoundingBox[2] + 5;
		this.valueString.y = (this.transBoundingBox[3] - this.transBoundingBox[1]) / 2;
	}
	
	Component.prototype.initPaint = function()
	{
		if(this.selectable)
		{
			this.ctx.strokeStyle = this.selectedColor;		
			this.ctx.fillStyle = this.selectedColor;
		}
		else
		{	
			this.ctx.strokeStyle = this.color;		
			this.ctx.fillStyle = this.color;
		}
	}
	
	Component.prototype.transform = function()
	{
		this.ctx.translate(this.x, this.y);
		if(this.rotation != 0)
			this.ctx.rotate(-this.rotation);
	}
	
	Component.prototype.getMiddle = function()
	{
		this.xMiddle = (this.boundingBox[2] - this.boundingBox[0]) / 2;
		this.yMiddle = (this.boundingBox[3] - this.boundingBox[1]) / 2;
	}	
	
	Component.prototype.drawLabel = function()
	{
		if (this.label.show)
		{
			var textAlign;
			this.ctx.save();
			this.ctx.fillStyle = this.label.color;
			this.ctx.textAlign = "left";
			if (this.rotation == 0) //Component is vertical
			{
				if (this.label.position == "left") //Label is on left
				{
					this.ctx.textBaseline = "middle";
					textAlign = "right";
				}
				else if (this.label.position == "right") //Label is on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "left";
				}
			}
			else if (this.rotation == Math.PI/2) //Component is horizontal
			{
				if (this.label.position == "left") //Label now on bottom
				{
					this.ctx.textBaseline = "top";
					textAlign = "center";
				}
				else if (this.label.position == "right") //Label on top
				{
					this.ctx.textBaseline = "bottom";
					textAlign = "center";
				}
			}
			else if (this.rotation == Math.PI) //Component is horizontal
			{
				if (this.label.position == "left") //Label now on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "left";
				}
				else if (this.label.position == "right") //Label now on left
				{
					this.ctx.textBaseline = "middle";
					textAlign = "right";
				}
			}	
			else if (this.rotation == 2*Math.PI/3) //Component is vertical
			{
				if (this.label.position == "left") //Label is on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "left";
				}
				else if (this.label.position == "right") //Label is on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "right";
				}
			}			
			this.ctx.translate(this.label.x, this.label.y);
			this.ctx.rotate(this.rotation);
			this.diagram.drawSubSuperScript(this.ctx, this.label.str, 0, 0, textAlign);
			this.ctx.restore();
		}	
	}
	
	Component.prototype.drawValueString = function()
	{
		if (this.valueString.show)
		{
			var textAlign;
			this.ctx.save();
			this.ctx.fillStyle = this.valueString.color;
			this.ctx.textAlign = "left";
			if (this.rotation == 0) //Component is vertical
			{
				if (this.valueString.position == "left") //Label is on left
				{
					this.ctx.textBaseline = "middle";
					textAlign = "right";
				}
				else if (this.valueString.position == "right") //Label is on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "left";
				}
			}
			else if (this.rotation == Math.PI/2) //Component is horizontal
			{
				if (this.valueString.position == "left") //Label now on bottom
				{
					this.ctx.textBaseline = "top";
					textAlign = "center";
				}
				else if (this.valueString.position == "right") //Label on top
				{
					this.ctx.textBaseline = "bottom";
					textAlign = "center";
				}
			}
			else if (this.rotation == Math.PI) //Component is horizontal
			{
				if (this.valueString.position == "left") //Label now on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "left";
				}
				else if (this.valueString.position == "right") //Label now on left
				{
					this.ctx.textBaseline = "middle";
					textAlign = "right";
				}
			}	
			else if (this.rotation == 2*Math.PI/3) //Component is vertical
			{
				if (this.valueString.position == "left") //Label is on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "left";
				}
				else if (this.valueString.position == "right") //Label is on right
				{
					this.ctx.textBaseline = "middle";
					textAlign = "right";
				}
			}
			this.ctx.translate(this.valueString.x, this.valueString.y);
			this.ctx.rotate(this.rotation);
			var str;
			if (this.valueString.decimal < 0)
				str = this.value + " " + this.valueString.suffix;
			else //Force a certain number of digits
				str = (this.value).toFixed(this.valueString.decimal) + " " + this.valueString.suffix;
			
			this.diagram.drawSubSuperScript(this.ctx, str, 0, 0, textAlign);
			this.ctx.restore();
		}	
	}
	
	Component.prototype.isInside = function(x, y)
	{
		var pt = transform(x, y, this.x, this.y, this.rotation);
		if((this.transBoundingBox[0] <= pt.x) && (pt.x <= this.transBoundingBox[2]) && (this.transBoundingBox[1] <= pt.y) && (pt.y <= this.transBoundingBox[3]))
			return true;
		else
			return false;
	}
	
	//***** NODE COMPONENT *****//
	function Node(x, y)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-2, -2, 2, 2];
		this.nodeRadius = 2;
	}

	copyPrototype(Node, Component);
	Node.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawCircle(this.ctx, 0, 0, this.nodeRadius, true);
		this.drawLabel();
		this.ctx.restore();
	}
	
	Node.prototype.toString = function()
	{
	    return "<Node (" + this.x + "," + this.y + ")>";
	}

	//***** WIRE COMPONENT *****//
	function Wire(x1, y1, x2, y2)
	{
		//Call super class
		this.Component(x1, y1);
		this.dx = x2 - x1;
		this.dy = y2 - y1;
		this.boundingBox = [-5, -5, this.dx + 5, this.dy + 5];
	}

	copyPrototype(Wire, Component);
	Wire.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, this.dx, this.dy);
		this.ctx.restore();
	}
	
	Wire.prototype.toString = function()
	{
	    return "<Wire (" + this.x + "," + this.y + "," + (this.x + this.dx) + "," + (this.y + this.dy) + ")>";
	}

	//***** LABEL *****//
	function Label(x, y, value, textAlign)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-10, -10, 10, 10];
		this.value = value;
		this.textAlign = textAlign;
	}

	copyPrototype(Label, Component);
	Label.prototype.paint = function()
	{
		this.ctx.save();
		this.ctx.textAlign = "left";
		this.ctx.translate(this.x, this.y);
		this.ctx.rotate(this.rotation);
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawSubSuperScript(this.ctx, this.value, 0, 0, this.textAlign);
		this.ctx.restore();
	}
	
	Label.prototype.toString = function()
	{
	    return "<Label (" + this.x + "," + this.y + ")>";
	}
	
	//***** CAPACITOR COMPONENT *****//
	function Capacitor(x, y, value)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-8, 0, 8, 48];
		this.value = value;
	}

	copyPrototype(Capacitor, Component);
	Capacitor.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 22);
		this.diagram.drawLine(this.ctx, -8, 22, 8, 22);
		this.diagram.drawLine(this.ctx, -8, 26, 8, 26);
		this.diagram.drawLine(this.ctx, 0, 26, 0, 48);
		this.drawLabel();
		this.drawValueString();
		this.ctx.restore();
	}
	
	Capacitor.prototype.toString = function()
	{
	    return "<Capacitor (" + this.x + "," + this.y + ")>";
	}

	//***** RESISTOR COMPONENT *****//
	function Resistor(x, y, value)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-5, 0, 5, 48];
		this.value = value;
	}

	copyPrototype(Resistor, Component);
	Resistor.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 12);
		this.diagram.drawLine(this.ctx, 0, 12, 4, 14);
		this.diagram.drawLine(this.ctx, 4, 14, -4, 18);
		this.diagram.drawLine(this.ctx, -4, 18, 4, 22);
		this.diagram.drawLine(this.ctx, 4, 22, -4, 26);
		this.diagram.drawLine(this.ctx, -4, 26, 4, 30);
		this.diagram.drawLine(this.ctx, 4, 30, -4, 34);
		this.diagram.drawLine(this.ctx, -4, 34, 0, 36);
		this.diagram.drawLine(this.ctx, 0, 36, 0, 48);
		this.drawLabel();
		this.drawValueString();
		this.ctx.restore();
	}
	
	Resistor.prototype.toString = function()
	{
	    return "<Resistor (" + this.x + "," + this.y + ")>";
	}

	//***** INDUCTOR COMPONENT *****//
	function Inductor(x, y, value)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-4, 0, 5, 48];
		this.value = value;
	}

	copyPrototype(Inductor, Component);
	Inductor.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 14);
		this.diagram.drawArc(this.ctx, 0, 18, 4, 6*Math.PI/4, 3*Math.PI/4);
		this.diagram.drawArc(this.ctx, 0, 24, 4, 5*Math.PI/4, 3*Math.PI/4);
		this.diagram.drawArc(this.ctx, 0, 30, 4, 5*Math.PI/4, 2*Math.PI/4);
		this.diagram.drawLine(this.ctx, 0, 34, 0, 48);
		this.drawLabel();
		this.drawValueString();
		this.ctx.restore();
	}
	
	Inductor.prototype.toString = function()
	{
	    return "<Inductor (" + this.x + "," + this.y + ")>";
	}

	//***** N-CHANNEL AND P-CHANNEL MOSFET COMPONENT *****//
	function Mosfet(x, y, value, type)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-24, 0, 8, 48];
		this.value = value;
		this.type = type;
	}

	copyPrototype(Mosfet, Component);
	Mosfet.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 16);
		this.diagram.drawLine(this.ctx, -8, 16, 0, 16);
		this.diagram.drawLine(this.ctx, -8, 16, -8, 32);
		this.diagram.drawLine(this.ctx, -8, 32, 0, 32);
		this.diagram.drawLine(this.ctx, 0, 32, 0, 48);
		if (this.type == "n")
		{
			this.diagram.drawLine(this.ctx,-24,24,-12,24);
			this.diagram.drawLine(this.ctx,-12,16,-12,32);
		}
		else if (this.type == "p")
		{
			this.diagram.drawLine(this.ctx, -24, 24, -16, 24);
			this.diagram.drawCircle(this.ctx, -14, 24, 2, false);
			this.diagram.drawLine(this.ctx, -12, 16, -12, 32);
		}
		this.drawLabel();
		this.drawValueString();			
		this.ctx.restore();
	}
	
	Mosfet.prototype.toString = function()
	{
	    if (this.type = "n")
	    	return "<Mosfet N Channel (" + this.x + "," + this.y + ")>";
	    else if (this.type = "p")
	    	return "<Mosfet P Channel (" + this.x + "," + this.y + ")>";
	}

	//***** VOLTAGE AND CURRENT SOURCE COMPONENT *****//
	function Source(x, y, value, type)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-12, 0, 12, 48];
		this.value = value;
		this.type = type;
	}

	copyPrototype(Source, Component);
	Source.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 12);
		this.diagram.drawCircle(this.ctx, 0, 24, 12, false);
		this.diagram.drawLine(this.ctx, 0, 36, 0, 48);
		if (this.type == "v")
		{
			//Plus sign, vertical bar
			this.ctx.save();
			this.ctx.translate(0, this.diagram.scale*18);
			this.ctx.rotate(this.rotation);
			this.diagram.drawLine(this.ctx, 0, -3, 0, 3); //this.diagram.drawLine(this.ctx, 0, 15, 0, 21);
			this.ctx.restore();
			
			//Plus sign, horizontal bar
			this.ctx.save();
			this.ctx.translate(0, this.diagram.scale*18);
			this.ctx.rotate(this.rotation);
			this.diagram.drawLine(this.ctx, -3, 0, 3, 0); //this.diagram.drawLine(this.ctx, -3, 18, 3, 18);
			this.ctx.restore();
			//Minus sign
			this.ctx.save();
			this.ctx.translate(0, this.diagram.scale*30);
			this.ctx.rotate(this.rotation);
			this.diagram.drawLine(this.ctx, -3, 0, 3, 0);	//this.diagram.drawLine(this.ctx, -3, 30, 3, 30);
			this.ctx.restore();
		}
		else if (this.type == "i")
		{
			this.diagram.drawLine(this.ctx, 0, 15, 0, 32);
			this.diagram.drawLine(this.ctx,-3, 26, 0, 32);
			this.diagram.drawLine(this.ctx,3, 26, 0, 32);		
		}
		this.drawLabel();
		this.drawValueString();
		this.ctx.restore();
	}
	
	Source.prototype.toString = function()
	{
			if (this.type = "v")
				return "<Voltage Source (" + this.x + "," + this.y + ")>";
	    else if (this.type = "i")
				return "<Current Source (" + this.x + "," + this.y + ")>";
	}

	//***** GROUND COMPONENT *****//
	function Ground(x, y)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-6, 0, 6, 8];
	}

	copyPrototype(Ground, Component);
	Ground.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 8);
	  this.diagram.drawLine(this.ctx, -6, 8, 6, 8);
	  this.ctx.restore();
	}
	
	Ground.prototype.toString = function()
	{
	    return "<Ground (" + this.x + "," + this.y + ")>";
	}

	//***** DIODE COMPONENT *****//
	function Diode(x, y, value)
	{
		//Call super class
		this.Component(x, y);
		this.boundingBox = [-8, 0, 8, 48];
		this.value = value;
	}

	copyPrototype(Diode, Component);
	Diode.prototype.paint = function()
	{
		this.initPaint();
		this.ctx.save();
		this.transform();
		this.drawLabel();
		this.ctx.strokeStyle = this.color;		
		this.ctx.fillStyle = this.color;
		this.diagram.drawLine(this.ctx, 0, 0, 0, 16);
		this.diagram.drawLine(this.ctx, -8, 16, 8, 16);
		this.diagram.drawLine(this.ctx, -8, 16, 0, 32);
		this.diagram.drawLine(this.ctx, 8, 16, 0, 32);
		this.diagram.drawLine(this.ctx, -8, 32, 8, 32);
		this.diagram.drawLine(this.ctx,0 , 32, 0, 48);
		this.ctx.restore();
	}
	
	Diode.prototype.toString = function()
	{
	    return "<Diode (" + this.x + "," + this.y + ")>";
	}
	
//////////PUBLIC FIELDS AND METHODS//////////
	return {

		Utils: Utils,
		Color: Color,
		Diagram: Diagram,
	};
}());
