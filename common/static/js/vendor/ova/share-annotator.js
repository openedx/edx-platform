/* 
Share Annotation Plugin v1.0 (https://github.com/danielcebrian/share-annotator)
Copyright (C) 2014 Daniel Cebrian Robles
License: https://github.com/danielcebrian/share-annotator/blob/master/License.rst

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/
var _ref,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

Annotator.Plugin.Share = (function(_super) {
	__extends(Share, _super);
	
	//Default Share configuration
	Share.prototype.options = {
		shareIn:['facebook','twitter','email','google'],
		getUrl:{
			'facebook':function(title,link,noteText){
				return 'https://www.facebook.com/sharer/sharer.php?s=100&p[url]='+link+'&p[title]='+encodeURIComponent('Open Video Annotation')+'&p[summary]='+noteText;
			},
			'twitter':function(title,link,noteText){
				return 'https://twitter.com/intent/tweet?original_referer='+link+'&source=tweetbutton&url='+link+ "&via=OpenVideoAnnotation&text=" +encodeURIComponent('I want to share the next Open Video Annotation: ');
			},
			'google':function(title,link,noteText){
				return 'https://plus.google.com/share?url='+link;
			},
			'email': function(title,link,noteText){
				return 'mailto:?subject='+title+'&body='+link;
			}
		},
		baseUrl:'', //baseUrl = the base url for all the shared annotations
	};

	function Share(element,options) {
		if (typeof options!='undefined')
			this.options.shareIn = typeof options.shareIn!='undefined'?options.shareIn:this.options.shareIn;
		this.buildHTMLShareButton = __bind(this.buildHTMLShareButton, this);
		this.runningAPI = __bind(this.runningAPI, this);
		this.updateViewer = __bind(this.updateViewer, this);
		_ref = Share.__super__.constructor.apply(this, arguments);
		return _ref;
	}

	Share.prototype.field = null;

	Share.prototype.input = null;

	Share.prototype.pluginInit = function() {
		console.log("Share-pluginInit");
		//Check that annotator is working
		if (!Annotator.supported()) {
			return;
		}
		
		//-- Editor
		this.field = this.annotator.editor.addField({
			type: 'input', //options (textarea,input,select,checkbox)
		});

		//Modify the element created with annotator to be an invisible span
		var newfield = Annotator.$('<li class="annotator-item">'+this.buildHTMLShareButton('Share without saving:')+'</li>');
		Annotator.$(this.field).replaceWith(newfield);
		this.field=newfield[0];
		
		//Create the actions for the buttons
		this.buttonsActions(this.field,2,this.options.baseUrl); //2 is the method of the API that will be for share without saving
		
		//Init the API plugin
		var APIoptions = this.initAPI();
		
		this.runAPI(APIoptions);
		
		//-- Viewer
		var newview = this.annotator.viewer.addField({
			load: this.updateViewer,
		});

		return this.input = $(this.field).find(':input');
	};
	
	//Share button HTML
	Share.prototype.buildHTMLShareButton = function(title,id) {
		var title = title || '',
			id = typeof id!='undefined'?'annotationId="'+id+'"':'',
			titleText = title!=''?'<div class="share-text-annotator">'+title+'</div>':'',
			shareButton = '<div class="share-button-annotator share-button" '+id+'></div>',
			popup = '<div class="share-popup-overlay-bg" style="z-index:30000000000"><div class="share-popup"><div class="share-popup-items"></div><div class="close-btn">Close</div></div></div>';
		return '<div class="share-container-annotator">'+titleText+shareButton+popup+'</div>';
	}
	
	//template for the design of the Share Plugin
	Share.prototype.buildHTMLPopup = function(title) {
		var buttons = '';
		if (typeof this.options.shareIn!='undefined'){
			this.options.shareIn.forEach(function(item) { 
				buttons += '<div class="share-'+item+'-annotator share-button">'+item.charAt(0).toUpperCase() + item.slice(1)+'</div>';
			});
		}
		this.uri = typeof this.uri!='undefined'?this.uri:'';
		var title = '<div class="share-popup-title">'+title.replace(":","")+'</div>',
			copy = '<div class="share-popup-copy">Copy and Share:</div>',
			uri = '<input type="text" class="share-popup-uri" onclick="javascript:this.select();" readonly="true" value="'+this.uri+'">',
			popup = title + buttons + copy + uri;
		return popup;
	}
	
	//Create the actions for the buttons
	Share.prototype.buttonsActions = function(field,method,url) {
		var share = this;
		
		// hide popup when user clicks on close button
		$(field).find('.close-btn').click(function() {
			$('.share-popup-overlay-bg').hide();
		});
		// hides the popup if user clicks anywhere outside the container
		$(field).find('.share-popup-overlay-bg').click(function() {
			$('.share-popup-overlay-bg').hide();
		});
		// prevents the overlay from closing if user clicks inside the popup overlay
		$(field).find('.share-popup').click(function() {
			return false;
		});
		// Share button
		$(field).find('.share-button-annotator.share-button').click(function() {
		    event.preventDefault(); // disable normal link function so that it doesn't refresh the page
		    var _field = this,
		    	ovaId = $(this).attr('annotationId'),
		    	title = method == 1?'Share':'Share without saving';
		    
		    // share.uri will be useful for buildHTMLPopup functions
		    share.uri = share.createAPIURL(method,ovaId,url); 
		    
		    //display your popup
		    $(this).parent().find('.share-popup-overlay-bg').show(); 
		    
		    //build buttons
		    $(this).parent().find('.share-popup-items').html(share.buildHTMLPopup(title)); 
		    
		    //buttons actions
			if (typeof share.options.shareIn!='undefined'){
				share.options.shareIn.forEach(function(item) {
					$(_field).parent().find('.share-'+item+'-annotator.share-button').click(function() {
						var url = share.createAPIURL(method,ovaId,url),
							title = "Sharing a annotation with Open Video Annotation";
							link = encodeURIComponent(url),
							noteText = share.getSource('ovaText'),
							finalUrl = '';
						if (method==1){
							var viewer = share.annotator.viewer,
								textarea = $(viewer.element).find('div:first').html();
							noteText = encodeURIComponent(textarea);
						}
						finalUrl = typeof share.options.getUrl[item]!='undefined'?share.options.getUrl[item](title,link,noteText):'';
						if(typeof share.options.getUrl[item]!='undefined')
							window.open(finalUrl);
					}); 
				});
			}
		});
	};
	
	
	Share.prototype.createAPIURL = function(method,ovaId,url) {
		var annotator = this.annotator,
			editor = annotator.editor,
			method = method || 1,
			//url = location.protocol + '//' + location.host + location.pathname,
			url = url || window.location.href;
		
		url += (url.indexOf('?') >= 0)?'&':'?';
			
		if (method === 1){
			var ovaId = typeof ovaId!='undefined'?ovaId:'';
			url += 'ovaId=' + ovaId;
		}else if (method === 2){
			var ovaText = this.getSource('ovaText') || " ";
			url += 'ovaText='+ ovaText;
			if(typeof editor.VideoJS!='undefined' && editor.VideoJS !== -1){//Video Annotation
				var	ovaStart = this.getSource('ovaStart') || " ",
					ovaEnd = this.getSource('ovaEnd') || " ",
					ovaContainer = this.getSource('ovaContainer') || " ",
					ovaSrc = this.getSource('ovaSrc') || " ";
				url +=  '&ovaStart='+ ovaStart
					+'&ovaEnd='+ ovaEnd 
					+'&ovaContainer='+ovaContainer
					+'&ovaSrc='+ ovaSrc;
			}else if(typeof editor.OpenSeaDragon!='undefined' && editor.OpenSeaDragon !== -1){//Image Annotation
				var	ovaLeft = this.getSource('ovaLeft') || " ",
					ovaTop = this.getSource('ovaTop') || " ",
					ovaWidth = this.getSource('ovaWidth') || " ",
					ovaHeight = this.getSource('ovaHeight') || " ",
					ovaLeftZoom = this.getSource('ovaLeftZoom') || " ",
					ovaTopZoom = this.getSource('ovaTopZoom') || " ",
					ovaWidthZoom = this.getSource('ovaWidthZoom') || " ",
					ovaHeightZoom = this.getSource('ovaHeightZoom') || " ",
					ovaContainer = this.getSource('ovaContainer') || " ",
					ovaSrc = this.getSource('ovaSrc') || " ";
				url +=  '&ovaLeft='+ ovaLeft
					+'&ovaTop='+ ovaTop
					+'&ovaWidth='+ ovaWidth
					+'&ovaHeight='+ ovaHeight
					+'&ovaLeftZoom='+ ovaLeftZoom
					+'&ovaTopZoom='+ ovaTopZoom
					+'&ovaWidthZoom='+ ovaWidthZoom
					+'&ovaHeightZoom='+ ovaHeightZoom 
					+'&ovaContainer='+ovaContainer
					+'&ovaSrc='+ ovaSrc;
			}else{//Text Annotation
				var	ovaStart = this.getSource('ovaStart') || " ",
					ovaEnd = this.getSource('ovaEnd') || " ",
					ovastartOffset = this.getSource('ovastartOffset') || " ",
					ovaendOffset = this.getSource('ovaendOffset') || " ";
				url +=  '&ovaStart='+ ovaStart
					+'&ovaEnd='+ ovaEnd
					+'&ovastartOffset='+ovastartOffset
					+'&ovaendOffset='+ ovaendOffset;
			}
		}
		return url;
	};
	
	Share.prototype.getSource = function(source) {
		var	source = source || '';
		if (source == 'ovaId') {//method 1
			source=this.annotation.id;
		}else{//method 2
			var annotator = this.annotator,
				editor = annotator.editor,
				textarea = $(editor.element).find('textarea')[0];
			if(source == 'ovaText')
				source = textarea.value;
			if (typeof editor.VideoJS!='undefined' && editor.VideoJS !== -1){//Video Annotation
				if(source == 'ovaContainer')
					source = editor.VideoJS;
				else if(source == 'ovaSrc')
					source = annotator.mplayer[editor.VideoJS].tech.options_.source.src;
				else if(source == 'ovaStart')
					source = annotator.mplayer[editor.VideoJS].rangeslider.getValues().start;
				else if(source == 'ovaEnd')
					source = annotator.mplayer[editor.VideoJS].rangeslider.getValues().end;
			}else if (typeof editor.OpenSeaDragon!='undefined' && editor.OpenSeaDragon !== -1){//Image Annotation
				var annotation = editor.annotation;
				if(source == 'ovaLeft')
					source = annotator.osda.rectPosition.left;
				else if(source == 'ovaTop')
					source = annotator.osda.rectPosition.top;
				else if(source == 'ovaWidth')
					source = annotator.osda.rectPosition.width;
				else if(source == 'ovaHeight')
					source = annotator.osda.rectPosition.height;
				else if(source == 'ovaLeftZoom')
					source = annotator.osda.viewer.drawer.viewport.getBounds().x;
				else if(source == 'ovaTopZoom')
					source = annotator.osda.viewer.drawer.viewport.getBounds().y;
				else if(source == 'ovaWidthZoom')
					source = annotator.osda.viewer.drawer.viewport.getBounds().width;
				else if(source == 'ovaHeightZoom')
					source = annotator.osda.viewer.drawer.viewport.getBounds().height;
				else if(source == 'ovaContainer')
					source = annotator.osda.viewer.id;
				else if(source == 'ovaSrc'){
					var source = annotator.osda.viewer.source,
						tilesUrl = typeof source.tilesUrl!='undefined'?source.tilesUrl:'',
						functionUrl = typeof source.getTileUrl!='undefined'?source.getTileUrl:'';
					source = tilesUrl!=''?tilesUrl:(''+functionUrl).replace(/\s+/g, ' '); // - target.src (media source)
				}
			}else{//Text Annotation
				var annotation = editor.annotation;
				if(source == 'ovastartOffset')
					source = annotation.ranges[0].startOffset;
				else if(source == 'ovaendOffset')
					source = annotation.ranges[0].endOffset;
				else if(source == 'ovaStart')
					source = annotation.ranges[0].start;
				else if(source == 'ovaEnd')
					source = annotation.ranges[0].end;
			}
		}
		return encodeURIComponent(source);
	};
	
	Share.prototype.initAPI = function() {
		console.log("initAPI");
		// -- Detect API in the URL -- //
		/*
		The first option is to give a known id of an annotation
		Example http://url.com/#id=rTcpOjIMT2aF1apDtboC-Q
		*/
		var API = {},
			ovaId = this.getParameterByName('ovaId'), //Method 1 (Obligatory)
			start = this.getParameterByName('ovaStart'), //Method 2 (Obligatory)
			end = this.getParameterByName('ovaEnd'), //Method 2 (Obligatory)
			container = this.getParameterByName('ovaContainer'), //Method 2 (Obligatory)
			src = this.getParameterByName('ovaSrc'),//Method 2 (Obligatory)
			text = this.getParameterByName('ovaText'),//Method 2 
			user = this.getParameterByName('ovaUser'),//Method 2 
			Left = this.getParameterByName('ovaLeft'),//Method 2 
			Top = this.getParameterByName('ovaTop'),//Method 2 
			Width = this.getParameterByName('ovaWidth'),//Method 2 
			Height = this.getParameterByName('ovaHeight'),//Method 2 
			leftZoom = this.getParameterByName('ovaLeftZoom'),//Method 2 
			topZoom = this.getParameterByName('ovaTopZoom'),//Method 2 
			widthZoom = this.getParameterByName('ovaWidthZoom'),//Method 2 
			heightZoom = this.getParameterByName('ovaHeightZoom'),//Method 2  
			startOffset = this.getParameterByName('ovastartOffset'),//Method 2 
			endOffset = this.getParameterByName('ovaendOffset');//Method 2 
		
		//remove the variables from the url browser
		var stripped_url = top.location.href;
		if (ovaId != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaId');
		if (start != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaStart');
		if (end != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaEnd');
		if (container != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaContainer');
		if (src != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaSrc');
		if (text != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaText');
		if (user != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaUser');
		if (Left != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaLeft');
		if (Top != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaTop');
		if (Width != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaWidth');
		if (Height != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaHeight');
		if (leftZoom != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaLeftZoom');
		if (topZoom != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaTopZoom');
		if (widthZoom != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaWidthZoom');
		if (heightZoom != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaHeightZoom');
		if (startOffset != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovastartOffset');
		if (endOffset != '') stripped_url = this.removeVariableFromURL(stripped_url, 'ovaendOffset');
  		window.history.pushState("object or string", "Title", stripped_url);
  		
		
		// Method 1 API with the Id of the annotation
		//Example: http://danielcebrian.com/annotations/demo.html?&ovaId=wtva_SjnQb2HtqppDihKug
		if(ovaId != ''){
			$.extend(API,{method:1,ovaId:ovaId});
		}
		//Method 2 API with all the parameter to load the annotation
		//Example with video: http://danielcebrian.com/annotations/demo.html?ovaContainer=vid1&ovaSrc=http%3A%2F%2Fvideo-js.zencoder.com%2Foceans-clip.mp4&ovaStart=2&ovaEnd=10&ovaText=This%20is%20test&ovaUser=Test%20User
		//Example with text: http://danielcebrian.com/annotations/demo.html?ovaStart=%2Fp%5B1%5D&ovaEnd=%2Fp%5B1%5D&ovastartOffset=542&ovaendOffset=572&ovaText=API
	
		if(start!='' && end!='' && container!='' && src!=''){//video api
			$.extend(API,{method:2,start:start,end:end,container:container,src:src,text:text,user:user});
		}else if(Left!='' && Top!='' && Width!='' && Height!='' && leftZoom!='' && topZoom!='' && widthZoom!='' && heightZoom!=''){//image api
			$.extend(API,{method:2,Left:Left,Top:Top,Width:Width,Height:Height,leftZoom:leftZoom,topZoom:topZoom,widthZoom:widthZoom,heightZoom:heightZoom,container:container,src:src,text:text,user:user});
		}else if(start!='' && end!='' && startOffset!='' && endOffset!=''){//text api
			$.extend(API,{method:2,start:start,end:end,startOffset:startOffset,endOffset:endOffset,text:text,user:user});
		}
		return API;
	}
	Share.prototype.runningAPI =  function (annotations,API){
		var wrapper = $('.annotator-wrapper').parent()[0],
			mplayer,
			osda,
			self=this;
			
		//Set Annotator in wrapper to fix quick DOM
		$.data(wrapper, 'annotator', self.annotator);//Set the object in the span
		annotator = window.annotator = $.data(wrapper, 'annotator');
		mplayer = typeof annotator.mplayer!='undefined'?annotator.mplayer:[];
		osda = typeof annotator.osda!='undefined'?annotator.osda:[];
		
		//Detect if the URL has an API element
		if (typeof API!='undefined' && typeof API.method!='undefined' && (API.method=='1'||API.method=='2')) {
			if(API.method=='1'){
				var allannotations = annotator.plugins['Store'].annotations,
					ovaId = decodeURIComponent(API.ovaId);
				
				for (var item in allannotations) {
					var an = allannotations[item],
						olditem;
					if (typeof an.id!='undefined' && an.id == ovaId){//this is the annotation
						if(self._isVideo(an)){//It is a video
							if (typeof mplayer[an.target.container]!='undefined'){
								var player = mplayer[an.target.container];
								if (player.id_ == an.target.container){
									var anFound = an;
									videojs(player.id_).ready(function(){
										if (player.techName != 'Youtube'){
											player.preload('auto');
										}
										player.autoPlayAPI = anFound;
										player.play();
									});
								}
							}
						}else if(an.media=="image"){//It is a OpenSeaDragon Annotation
							if ( $("div#"+an.target.container).length){
							    var isOpenViewer = typeof annotator.osda !="undefined" && typeof annotator.osda.viewer!="undefined"; 
							    function waitingOsda(){
								isOpenViewer = typeof annotator.osda !="undefined" && typeof annotator.osda.viewer!="undefined";
								if(typeof olditem == "undefined"){olditem = item;}
								if(!isOpenViewer){
								    setTimeout(waitingOsda,200);
								}else{
								    an = allannotations[olditem];
								    $(an.highlights).parent().find('.annotator-hl').removeClass('api'); 
								    //change the color
								    $(an.highlights).addClass('api');
								    //change zoom
								    if (typeof annotator!='undefined' && typeof annotator.osda!='undefined'){
								    	var currentBounds = annotator.osda.viewer.drawer.viewport.getBounds(),
					    					bounds = typeof an.bounds!='undefined'?an.bounds:{};
									if (typeof bounds.x!='undefined') currentBounds.x = bounds.x;
									if (typeof bounds.y!='undefined') currentBounds.y = bounds.y;
									if (typeof bounds.width!='undefined') currentBounds.width = bounds.width;
									if (typeof bounds.height!='undefined') currentBounds.height = bounds.height;
								    	annotator.osda.viewer.drawer.viewport.fitBounds(currentBounds); 
								    }
								    //animate to the annotation
								    $('html,body').animate({
									scrollTop: $(annotator.osda.viewer.element).offset().top},
									'slow');
								}
    							    }
							    waitingOsda();
							}
						}else{//It is a text
							var hasRanges = typeof an.ranges!='undefined' && typeof an.ranges[0] !='undefined',
								startOffset = hasRanges?an.ranges[0].startOffset:'',
								endOffset = hasRanges?an.ranges[0].endOffset:'';
				
							if(typeof startOffset!='undefined' && typeof endOffset!='undefined'){ 
								//change the color
								$(an.highlights).addClass('api'); 
								//animate to the annotation
								$('html,body').animate({
									scrollTop: $(an.highlights[0]).offset().top},
									'slow');
							}
						}
					}
				}
			}else if (API.method=='2'){
				if (typeof mplayer!='undefined'){
					//variable for Video
					var	container = decodeURIComponent(API.container),
						player = mplayer[container],
						isVideo = (typeof player!='undefined' && container==player.id_),
						isNumber = (!isNaN(parseFloat(API.start)) && isFinite(API.start) && !isNaN(parseFloat(API.end)) && isFinite(API.end)),
						isSource = false;
						
					if(isVideo){
						//Compare without extension
						var src = decodeURIComponent(API.src),
							targetSrc = src.substring(0,src.lastIndexOf(".")),
							playerSrc = player.tech.options_.source.src==''?player.tag.currentSrc:player.tech.options_.source.src;
						playerSrc = playerSrc.substring(0,playerSrc.lastIndexOf("."))
						isSource = (targetSrc == playerSrc);
					}
		
					//Open Video Annotation
					if(isVideo && isNumber && isSource){ 
						var annotation = {
								rangeTime: {
									start:API.start,
									end:API.end
								},
								created: new Date().toISOString(),
								updated: new Date().toISOString(),
								target:{
									container: container,
									src: src
								},
								media: 'video',
								text:decodeURIComponent(API.text),
								user:decodeURIComponent(API.user)
							};
						videojs(player.id_).ready(function(){
							if (player.techName != 'Youtube'){
								player.preload('auto');
							}
							player.autoPlayAPI = annotation;
							player.play();
						});
					}
				}
				//variable for text
				var startOffset = API.startOffset,
					endOffset = API.endOffset;
				
				//Text Annotation
				if(!isVideo && typeof startOffset!='undefined' && typeof endOffset!='undefined'){ 
					var annotation = {
						ranges: [{
							start:decodeURIComponent(API.start),
							end:decodeURIComponent(API.end),
							startOffset:decodeURIComponent(API.startOffset),
							endOffset:decodeURIComponent(API.endOffset),
						}],
						created: new Date().toISOString(),
						updated: new Date().toISOString(),
						media: 'text',
						text:decodeURIComponent(API.text),
						user:decodeURIComponent(API.user)
					};
					//show the annotation
					annotator.setupAnnotation(annotation);
					//to change the color
					$(annotation.highlights).addClass('api'); 
					//animate to the annotation
					$('html,body').animate({
						scrollTop: $(annotation.highlights[0]).offset().top},
						'slow');
				}
				
			}
		}
		//Let know to others API that this plugin is loaded
		annotator.isShareLoaded = true;
		annotator.publish('shareloaded');
	}
	Share.prototype.runAPI = function(API) {
		var self = this;
		var func = function (annotations){
			self.runningAPI(annotations,API);
			self.annotator.unsubscribe("annotationsLoaded",func);	
		};
		this.annotator
			//-- Finished the Annotator DOM
			.subscribe("annotationsLoaded",func);
	}
	
	Share.prototype._isVideo = function(an){
		//Detect if the annotation is a Open Video Annotation
		var an = an || {}
			rt = an.rangeTime,
			isVideo = (typeof an.media!='undefined' && an.media=='video'),
			hasContainer = (typeof an.target!='undefined' && typeof an.target.container!='undefined' ),
			isNumber = (typeof rt!='undefined' && !isNaN(parseFloat(rt.start)) && isFinite(rt.start) && !isNaN(parseFloat(rt.end)) && isFinite(rt.end));
		return (isVideo && hasContainer && isNumber);
	}
	
	Share.prototype._isImage = function(an){
		var wrapper = $('.annotator-wrapper').parent()[0],
			annotator = window.annotator = $.data(wrapper, 'annotator'),
			rp = an.rangePosition,
			isOpenSeaDragon = (typeof annotator.osda != 'undefined'),
			isContainer = (typeof an.target!='undefined' && typeof an.target.container!='undefined' ),
			isImage = (typeof an.media!='undefined' && an.media=='image'),
			isRP = (typeof rp!='undefined');
		return (isOpenSeaDragon && isContainer && isImage && isRP);
	}

	Share.prototype.getParameterByName = function(name) {
		name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
		var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
			//results = regex.exec(location.search),
        	results = regex.exec('?'+window.location.href.split('?')[1]);
		return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
	};
	
	Share.prototype.removeVariableFromURL = function(url_string, variable_name) {
		var URL = String(url_string);
		var regex = new RegExp( "\\?" + variable_name + "=[^&]*&?", "gi");
		URL = URL.replace(regex,'?');
		regex = new RegExp( "\\&" + variable_name + "=[^&]*&?", "gi");
		URL = URL.replace(regex,'&');
		URL = URL.replace(/(\?|&)$/,'');
		regex = null;
		return URL;
	}

	Share.prototype.updateViewer = function(field, annotation) {
		this.annotation = annotation;
		
		var self = this,
			field = $(field),
			ret = field.addClass('share-viewer-annotator').html(function() {
				var string;
				return self.buildHTMLShareButton('Share:',self.getSource('ovaId'));
			});
			
			
		//Create the actions for the buttons
		this.buttonsActions(field[0],1,this.options.baseUrl); //1 is the method of the API that will be for share some annotation in the database
		return ret;
	};

	return Share;

})(Annotator.Plugin);

