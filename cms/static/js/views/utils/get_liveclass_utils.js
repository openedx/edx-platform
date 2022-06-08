/**
 * Provides utilities for validating liveclass during creation.
 */
 define(['jquery', 'gettext', 'common/js/components/utils/view_utils', 'js/views/utils/create_utils_base'],
 function($, gettext, ViewUtils, CreateUtilsFactory) {
     'use strict';
     return function(selectors, classes) {
         var keyLengthViolationMessage = gettext('The combined length of the organization and library code fields' +
           ' cannot be more than <%- limit %> characters.');
         var keyFieldSelectors = [selectors.org, selectors.number];
         var nonEmptyCheckFieldSelectors = [selectors.name, selectors.org, selectors.number];

         CreateUtilsFactory.call(this, selectors, classes);
       
         this.create = function(liveclassInfo, errorHandler) {
             $.getJSON(
                 '/live_class/details/',
                 liveclassInfo
             ).done(function(response) {
                var elem = document.getElementById("output");
                elem.innerHTML = '';
                var output = document.getElementById('output');
                output.style.display='block';
                var response = JSON.parse(JSON.stringify(response))
                
    
                for(let i=0;i<response.length;i++)
                {
                    if(response[i]["meeting_link"]!=null && response[i]["meeting_link"]!=undefined)
                    {
                        console.log(response[i])
                        //alert(response.results[i]["topic_name"])
                        var parent = document.createElement("div");
                        var ele = document.createElement("div");
                        ele.setAttribute("id","timedrpact"+i);
                        ele.setAttribute("class","inner");
                        ele.innerHTML=response[i]["topic_name"];
                        parent.appendChild(ele);
                        var ele1= document.createElement("a");
                        ele1.setAttribute("id","timedrpact1"+i);
                        ele1.setAttribute("class","button inner-link");
                        ele1.setAttribute("href",response[i]["meeting_link"]);
                        ele1.setAttribute("target",'_black');
                        ele1.innerHTML='Start';
                        parent.appendChild(ele1);
                        
                        output.appendChild(parent);  
                    }
                        
                }
                
             }).fail(function(jqXHR, textStatus, errorThrown) {
                 var reason = errorThrown;
                 if (jqXHR.responseText) {
                     try {
                         var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                         if (detailedReason) {
                             reason = detailedReason;
                         }
                     } catch (e) {}
                 }
                 errorHandler(reason);
             });
         };

         this.getUser = function(liveclassInfo, errorHandler) {
            $.getJSON(
                '/accounts/details',
                liveclassInfo
            ).done(function(response) {
                errorHandler(response)
            //    var elem = document.getElementById("output");
            //    elem.innerHTML = '';
            //    var output = document.getElementById('output');
            //    output.style.display='block';
            //    var response = JSON.parse(JSON.stringify(response))
               
            //    for(let i=0;i<response.results.length;i++)
            //      {
            //        var parent = document.createElement("div");
            //        var ele = document.createElement("div");
            //        ele.setAttribute("id","timedrpact"+i);
            //        ele.setAttribute("class","inner");
            //        ele.innerHTML=response.results[i]["topic_name"];
            //        parent.appendChild(ele);
            //        var ele1= document.createElement("a");
            //        ele1.setAttribute("id","timedrpact1"+i);
            //        ele1.setAttribute("class","button inner-link");
            //        ele1.setAttribute("href",response.results[i]["meeting_link"]);
            //        ele1.setAttribute("target",'_black');
            //        ele1.innerHTML='Start';
            //        parent.appendChild(ele1);
            //        output.appendChild(parent);  
                         
            //      }
               
            }).fail(function(jqXHR, textStatus, errorThrown) {
                var reason = errorThrown;
                if (jqXHR.responseText) {
                    try {
                        var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                        if (detailedReason) {
                            reason = detailedReason;
                        }
                    } catch (e) {}
                }
                errorHandler(reason);
            });
        };


        this.assignUser = function(liveclassInfo, errorHandler) {
            $.postJSON(
                '/live_class/user/enrollment',
                liveclassInfo
            ).done(function(response) {
                errorHandler(response)
               
            }).fail(function(jqXHR, textStatus, errorThrown) {
                var reason = errorThrown;
                if (jqXHR.responseText) {
                    try {
                        var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                        if (detailedReason) {
                            reason = detailedReason;
                        }
                    } catch (e) {}
                }
                errorHandler(reason);
            });
        };
     };
 });
