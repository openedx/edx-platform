/* 
	jQuery TextAreaResizer plugin
	Created on 17th January 2008 by Ryan O'Dell 
	Version 1.0.4
*/(function($){var textarea,staticOffset;var iLastMousePos=0;var iMin=32;var grip;$.fn.TextAreaResizer=function(){return this.each(function(){textarea=$(this).addClass('processed'),staticOffset=null;$(this).wrap('<div class="resizable-textarea"><span></span></div>').parent().append($('<div class="grippie"></div>').bind("mousedown",{el:this},startDrag));var grippie=$('div.grippie',$(this).parent())[0];grippie.style.marginRight=(grippie.offsetWidth-$(this)[0].offsetWidth)+'px'})};function startDrag(e){textarea=$(e.data.el);textarea.blur();iLastMousePos=mousePosition(e).y;staticOffset=textarea.height()-iLastMousePos;textarea.css('opacity',0.25);$(document).mousemove(performDrag).mouseup(endDrag);return false}function performDrag(e){var iThisMousePos=mousePosition(e).y;var iMousePos=staticOffset+iThisMousePos;if(iLastMousePos>=(iThisMousePos)){iMousePos-=5}iLastMousePos=iThisMousePos;iMousePos=Math.max(iMin,iMousePos);textarea.height(iMousePos+'px');if(iMousePos<iMin){endDrag(e)}return false}function endDrag(e){$(document).unbind('mousemove',performDrag).unbind('mouseup',endDrag);textarea.css('opacity',1);textarea.focus();textarea=null;staticOffset=null;iLastMousePos=0}function mousePosition(e){return{x:e.clientX+document.documentElement.scrollLeft,y:e.clientY+document.documentElement.scrollTop}}})(jQuery);
/*
 *	TypeWatch 2.0 - Original by Denny Ferrassoli / Refactored by Charles Christolini
 *  Copyright(c) 2007 Denny Ferrassoli - DennyDotNet.com
 *  Coprright(c) 2008 Charles Christolini - BinaryPie.com
 *  Dual licensed under the MIT and GPL licenses:
 *  http://www.opensource.org/licenses/mit-license.php
 *  http://www.gnu.org/licenses/gpl.html
*/(function(jQuery){jQuery.fn.typeWatch=function(o){var options=jQuery.extend({wait:750,callback:function(){},highlight:true,captureLength:2},o);function checkElement(timer,override){var elTxt=jQuery(timer.el).val();if((elTxt.length>options.captureLength&&elTxt.toUpperCase()!=timer.text)||(override&&elTxt.length>options.captureLength)){timer.text=elTxt.toUpperCase();timer.cb(elTxt)}};function watchElement(elem){if(elem.type.toUpperCase()=="TEXT"||elem.nodeName.toUpperCase()=="TEXTAREA"){var timer={timer:null,text:jQuery(elem).val().toUpperCase(),cb:options.callback,el:elem,wait:options.wait};if(options.highlight){jQuery(elem).focus(function(){this.select()})}var startWatch=function(evt){var timerWait=timer.wait;var overrideBool=false;if(evt.keyCode==13&&this.type.toUpperCase()=="TEXT"){timerWait=1;overrideBool=true}var timerCallbackFx=function(){checkElement(timer,overrideBool)};clearTimeout(timer.timer);timer.timer=setTimeout(timerCallbackFx,timerWait)};jQuery(elem).keydown(startWatch)}};return this.each(function(index){watchElement(this)})}})(jQuery);
/*
Ajax upload
*/jQuery.extend({createUploadIframe:function(d,b){var a="jUploadFrame"+d;if(window.ActiveXObject){var c=document.createElement('<iframe id="'+a+'" name="'+a+'" />');if(typeof b=="boolean"){c.src="javascript:false"}else{if(typeof b=="string"){c.src=b}}}else{var c=document.createElement("iframe");c.id=a;c.name=a}c.style.position="absolute";c.style.top="-1000px";c.style.left="-1000px";document.body.appendChild(c);return c},createUploadForm:function(g,b){var e="jUploadForm"+g;var a="jUploadFile"+g;var d=$('<form  action="" method="POST" name="'+e+'" id="'+e+'" enctype="multipart/form-data"></form>');var c=$("#"+b);var f=$(c).clone();$(c).attr("id",a);$(c).before(f);$(c).appendTo(d);$(d).css("position","absolute");$(d).css("top","-1200px");$(d).css("left","-1200px");$(d).appendTo("body");return d},ajaxFileUpload:function(k){k=jQuery.extend({},jQuery.ajaxSettings,k);var a=new Date().getTime();var b=jQuery.createUploadForm(a,k.fileElementId);var i=jQuery.createUploadIframe(a,k.secureuri);var h="jUploadFrame"+a;var j="jUploadForm"+a;if(k.global&&!jQuery.active++){jQuery.event.trigger("ajaxStart")}var c=false;var f={};if(k.global){jQuery.event.trigger("ajaxSend",[f,k])}var d=function(l){var p=document.getElementById(h);try{if(p.contentWindow){f.responseText=p.contentWindow.document.body?p.contentWindow.document.body.innerText:null;f.responseXML=p.contentWindow.document.XMLDocument?p.contentWindow.document.XMLDocument:p.contentWindow.document}else{if(p.contentDocument){f.responseText=p.contentDocument.document.body?p.contentDocument.document.body.textContent||document.body.innerText:null;f.responseXML=p.contentDocument.document.XMLDocument?p.contentDocument.document.XMLDocument:p.contentDocument.document}}}catch(o){jQuery.handleError(k,f,null,o)}if(f||l=="timeout"){c=true;var m;try{m=l!="timeout"?"success":"error";if(m!="error"){var n=jQuery.uploadHttpData(f,k.dataType);if(k.success){k.success(n,m)}if(k.global){jQuery.event.trigger("ajaxSuccess",[f,k])}}else{jQuery.handleError(k,f,m)}}catch(o){m="error";jQuery.handleError(k,f,m,o)}if(k.global){jQuery.event.trigger("ajaxComplete",[f,k])}if(k.global&&!--jQuery.active){jQuery.event.trigger("ajaxStop")}if(k.complete){k.complete(f,m)}jQuery(p).unbind();setTimeout(function(){try{$(p).remove();$(b).remove()}catch(q){jQuery.handleError(k,f,null,q)}},100);f=null}};if(k.timeout>0){setTimeout(function(){if(!c){d("timeout")}},k.timeout)}try{var b=$("#"+j);$(b).attr("action",k.url);$(b).attr("method","POST");$(b).attr("target",h);if(b.encoding){b.encoding="multipart/form-data"}else{b.enctype="multipart/form-data"}$(b).submit()}catch(g){jQuery.handleError(k,f,null,g)}if(window.attachEvent){document.getElementById(h).attachEvent("onload",d)}else{document.getElementById(h).addEventListener("load",d,false)}return{abort:function(){}}},uploadHttpData:function(r,type){var data=!type;data=type=="xml"||data?r.responseXML:r.responseText;if(type=="script"){jQuery.globalEval(data)}if(type=="json"){eval("data = "+data)}if(type=="html"){jQuery("<div>").html(data).evalScripts()}return data}});
/**
 * Upload call. Used only once in the wmd file upload
 * this is "tightly coupled" with the wmd file uploader
 * @param {Object} jquery object imageUrl - where the
 *        uploaded url must be inserted on successful upload
 * @param {Function} handler that is run upon change
 * of the file upload field
 */
function ajaxFileUpload(imageUrl, startUploadHandler)
{
  $("#loading").ajaxStart(function(){
      $(this).show();
  }).ajaxComplete(function(){
      $(this).hide();
  });

  $("#upload").ajaxStart(function(){
          $(this).hide();
      }).ajaxComplete(function(){
          $(this).show();
      });

      $.ajaxFileUpload
      (
        {
            url: askbot['urls']['upload'],
              secureuri:false,
              fileElementId:'file-upload',
              dataType: 'xml',
              success: function (data, status)
              {
                  var fileURL = $(data).find('file_url').text();
                  var error = $(data).find('error').text();
                  if(error != ''){
                      alert(error);
                      if (startUploadHandler){
                        /* re-install this as the upload extension
                         * will remove the handler to prevent double uploading */
                        $('#file-upload').change(startUploadHandler);
                      }
                  }else{
                    imageUrl.attr('value', fileURL);
                  }

              },
              error: function (data, status, e)
              {
                  alert(e);
                  if (startUploadHandler){
                    /* re-install this as the upload extension
                     * will remove the handler to prevent double uploading */
                    $('#file-upload').change(startUploadHandler);
                  }
              }
          }
      )

    return false;
};
