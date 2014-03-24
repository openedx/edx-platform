/**
 * jQuery Watch Plugin
 *
 * @author Darcy Clarke
 * @version 2.0
 *
 * Copyright (c) 2012 Darcy Clarke
 * Dual licensed under the MIT and GPL licenses.
 *
 * ADDS: 
 *
 * - $.watch()
 *  
 * USES:
 *
 * - DOMAttrModified event
 * 
 * FALLBACKS:
 * 
 * - propertychange event
 * - setTimeout() with delay 
 *
 * EXAMPLE:
 * 
 * $('div').watch('width height', function(){
 *      console.log(this.style.width, this.style.height);
 * });
 *
 * $('div').animate({width:'100px',height:'200px'}, 500);
 *
 */

(function($){
    $.extend($.fn, {         
        /**
         * Watch Method
         * 
         * @param {String} the name of the properties to watch
         * @param {Object} options to overide defaults (only 'throttle' right now)
         * @param {Function} callback function to be executed when attributes change
         *
         * @return {jQuery Object} returns the jQuery object for chainability
         */   
        watch : function(props, options, callback){
            // Dummmy element
            var element = document.createElement('div');

            /**
             * Checks Support for Event
             * 
             * @param {String} the name of the event
             * @param {Element Object} the element to test support against
             *
             * @return {Boolean} returns result of test (true/false)
             */
            var isEventSupported = function(eventName, el) {
                eventName = 'on' + eventName;
                var supported = (eventName in el);
                if(!supported){
                    el.setAttribute(eventName, 'return;');
                    supported = typeof el[eventName] == 'function';
                }
                return supported;
            };
            // Type check options
            if(typeof(options) == 'function'){
                callback = options;
                options = {};
            }
            // Type check callback
            if(typeof(callback) != 'function')
                callback = function(){};
            // Map options over defaults
            options = $.extend({}, { throttle : 10 }, options);
            /**
             * Checks if properties have changed
             * 
             * @param {Element Object} the element to watch
             *
             */
            var check = function(el) {
                var data = el.data(),
                    changed = false,
                    temp;

                // Loop through properties
                var length = typeof data!='undefined' && typeof data.props!='undefined'?data.props.length:0;
                for(var i=0;i < length; i++){
                    temp = el.css(data.props[i]);
                    if(data.vals[i] != temp){
                        data.vals[i] = temp;
                        changed = true;
                        break;
                    }
                }
                // Run callback if property has changed
                if(changed && data.cb)
                    data.cb.call(el, data);
            };
            return this.each(function(){
                var el = $(this),
                    cb = function(){ check.call(this, el) },
                    data = { props:props.split(','), cb:callback, vals: [] };
                $.each(data.props, function(i){ data.vals[i] = el.css(data.props[i]); });
                el.data(data);
                if(isEventSupported('DOMAttrModified', element)){
                    el.on('DOMAttrModified', callback);
                } else if(isEventSupported('propertychange', element)){
                    el.on('propertychange', callback);
                } else {
                    setInterval(cb, options.throttle);
                }
            });
        }
    });
})(jQuery);
