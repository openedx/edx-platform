/**
 * Student dashboard credit messaging.
 */

 var edx = edx || {};

 (function($, analytics) {
     'use strict';
 
     $(document).ready(function() {
         live_class()
         function live_class()
         {
            
            $.ajax({
                type: 'GET',
                url: '/api/enrollment/v1/enrollment/live_class/enroll',
                data: $(this).serializeArray(),
                success: function(response) {
                    //alert(JSON.stringify(response))
                    // setTimeout(
                    //   function(){
                        var output = document.getElementById('output');
                        output.style.display='block';
                        var response = JSON.parse(JSON.stringify(response))
                        
                        for(let i=0;i<response.length;i++)
                          {
                              if(response[i]['live_class']!=undefined && response[i]['live_class']!=null )
                              {
                                var parent = document.createElement("div");
                                parent.classList.add('d-flex', 'justify-content-between', 'align-items-center',)
                                parent.setAttribute("style", "background: #fff; box-shadow: 0 2px 7px 0 rgb(0, 0, 0,.8%); overflow: hidden; border-radius: 8px; margin-bottom: 24px");
                                var image = document.createElement("img");
                                image.setAttribute('src', 'http://via.placeholder.com/220x120')
                                var ele = document.createElement("div");
                                ele.setAttribute(
                                  "style", "font-size: 1.2em; font-weight: 900; color:#000;");
                                ele.setAttribute("id","timedrpact"+i);
                                ele.setAttribute("class","inner");
                                ele.appendChild(image);
                                const span = document.createElement("span");
                                span.innerText = response[i]['live_class']["topic_name"];
                                span.style.marginLeft = '40px';
                                ele.appendChild(span);
                                parent.appendChild(ele);
                                var ele1= document.createElement("a");
                                ele1.setAttribute("id","timedrpact1"+i);
                                ele1.setAttribute("class","button inner-link");
                                ele1.setAttribute("href",response[i]['live_class']["meeting_link"]);
                                ele1.setAttribute("target",'_black');
                                ele1.setAttribute(
                                  "style", "font-size: 18px; margin-right: 20px; box-shadow: 0px 5px 0px #ee6100; border: none; color:#fff; background: #ff7f27; border-radius: 12px; padding: 12px 20px; background-image: none; text-shadow: 0 0");
                                ele1.innerHTML='Join Class';
                                parent.appendChild(ele1);
                                output.appendChild(parent);  
                              }
                           
                                  
                          }
            
                    //  }, 500); // adding timeout to make spinner animation longer
                }
            });
        }
 
        //alert('d')
         var $errorContainer = $('.credit-error-msg'),
             creditStatusError = $errorContainer.data('credit-error');
 
         if (creditStatusError === 'True') {
             $errorContainer.toggleClass('is-hidden');
         }
 
         // Fire analytics events when the "purchase credit" button is clicked
         $('.purchase-credit-btn').on('click', function(event) {
             var courseKey = $(event.target).data('course-key');
             analytics.track(
                 'edx.bi.credit.clicked_purchase_credit',
                 {
                     category: 'credit',
                     label: courseKey
                 }
             );
         });
 
 
         // This event invokes credit request endpoint. It will initiate
         // a credit request for the credit course for the provided user.
         $('.pending-credit-btn').on('click', function(event) {
             var $target = $(event.target),
                 courseKey = $target.data('course-key'),
                 username = $target.data('user'),
                 providerId = $target.data('provider');
 
             event.preventDefault();
 
             edx.commerce.credit.createCreditRequest(providerId, courseKey, username).fail(function() {
                 $('.credit-action').hide();
                 $errorContainer.toggleClass('is-hidden');
             });
         });
     });
 }(jQuery, window.analytics));
 
 