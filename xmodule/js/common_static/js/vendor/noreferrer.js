/*
 jquery.noreferrer.js, version 0.1.3
 https://github.com/knu/noreferrer

 Copyright (c) 2011 Akinori MUSHA
 Licensed under the 2-clause BSD license.
*/
(function(){(function(){$.browser.webkit||$.event.add(window,"load",function(){$("a[href][rel~=noreferrer], area[href][rel~=noreferrer]").each(function(){var b,e,c,g,d,f,h;b=this;c=b.href;$.browser.opera?(b.href="http://www.google.com/url?q="+encodeURIComponent(c),b.title||(b.title="Go to "+c)):(d=!1,g=function(){b.href="javascript:void(0)"},f=function(){b.href=c},$(b).bind("mouseout mouseover focus blur",f).mousedown(function(a){a.which===2&&(d=!0)}).blur(function(){d=!1}).mouseup(function(a){if(!(a.which===
2&&d))return!0;g();d=!1;setTimeout(function(){alert("Middle clicking on this link is disabled");f()},500);return!1}),e="<html><head><meta http-equiv='Refresh' content='0; URL="+$("<p/>").text(c).html()+"' /></head><body></body></html>",$.browser.msie?$(b).click(function(){var a;switch(a=this.target||"_self"){case "_self":case window.name:a=window;break;default:a=window.open(null,a)}a=a.document;a.clear();a.write(e);a.close();return!1}):(h="data:text/html;charset=utf-8,"+
encodeURIComponent(e),$(b).click(function(){this.href=h;return!0})))})})})()}).call(this);