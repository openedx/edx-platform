/*
    http://www.JSON.org/json2.js
    2010-08-25

    Public Domain.

    NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.

    See http://www.JSON.org/js.html


    This code should be minified before deployment.
    See http://javascript.crockford.com/jsmin.html

    USE YOUR OWN COPY. IT IS EXTREMELY UNWISE TO LOAD CODE FROM SERVERS YOU DO
    NOT CONTROL.


    This file creates a global JSON object containing two methods: stringify
    and parse.

        JSON.stringify(value, replacer, space)
            value       any JavaScript value, usually an object or array.

            replacer    an optional parameter that determines how object
                        values are stringified for objects. It can be a
                        function or an array of strings.

            space       an optional parameter that specifies the indentation
                        of nested structures. If it is omitted, the text will
                        be packed without extra whitespace. If it is a number,
                        it will specify the number of spaces to indent at each
                        level. If it is a string (such as '\t' or '&nbsp;'),
                        it contains the characters used to indent at each level.

            This method produces a JSON text from a JavaScript value.

            When an object value is found, if the object contains a toJSON
            method, its toJSON method will be called and the result will be
            stringified. A toJSON method does not serialize: it returns the
            value represented by the name/value pair that should be serialized,
            or undefined if nothing should be serialized. The toJSON method
            will be passed the key associated with the value, and this will be
            bound to the value

            For example, this would serialize Dates as ISO strings.

                Date.prototype.toJSON = function (key) {
                    function f(n) {
                        // Format integers to have at least two digits.
                        return n < 10 ? '0' + n : n;
                    }

                    return this.getUTCFullYear()   + '-' +
                         f(this.getUTCMonth() + 1) + '-' +
                         f(this.getUTCDate())      + 'T' +
                         f(this.getUTCHours())     + ':' +
                         f(this.getUTCMinutes())   + ':' +
                         f(this.getUTCSeconds())   + 'Z';
                };

            You can provide an optional replacer method. It will be passed the
            key and value of each member, with this bound to the containing
            object. The value that is returned from your method will be
            serialized. If your method returns undefined, then the member will
            be excluded from the serialization.

            If the replacer parameter is an array of strings, then it will be
            used to select the members to be serialized. It filters the results
            such that only members with keys listed in the replacer array are
            stringified.

            Values that do not have JSON representations, such as undefined or
            functions, will not be serialized. Such values in objects will be
            dropped; in arrays they will be replaced with null. You can use
            a replacer function to replace those with JSON values.
            JSON.stringify(undefined) returns undefined.

            The optional space parameter produces a stringification of the
            value that is filled with line breaks and indentation to make it
            easier to read.

            If the space parameter is a non-empty string, then that string will
            be used for indentation. If the space parameter is a number, then
            the indentation will be that many spaces.

            Example:

            text = JSON.stringify(['e', {pluribus: 'unum'}]);
            // text is '["e",{"pluribus":"unum"}]'


            text = JSON.stringify(['e', {pluribus: 'unum'}], null, '\t');
            // text is '[\n\t"e",\n\t{\n\t\t"pluribus": "unum"\n\t}\n]'

            text = JSON.stringify([new Date()], function (key, value) {
                return this[key] instanceof Date ?
                    'Date(' + this[key] + ')' : value;
            });
            // text is '["Date(---current time---)"]'


        JSON.parse(text, reviver)
            This method parses a JSON text to produce an object or array.
            It can throw a SyntaxError exception.

            The optional reviver parameter is a function that can filter and
            transform the results. It receives each of the keys and values,
            and its return value is used instead of the original value.
            If it returns what it received, then the structure is not modified.
            If it returns undefined then the member is deleted.

            Example:

            // Parse the text. Values that look like ISO date strings will
            // be converted to Date objects.

            myData = JSON.parse(text, function (key, value) {
                var a;
                if (typeof value === 'string') {
                    a =
/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)Z$/.exec(value);
                    if (a) {
                        return new Date(Date.UTC(+a[1], +a[2] - 1, +a[3], +a[4],
                            +a[5], +a[6]));
                    }
                }
                return value;
            });

            myData = JSON.parse('["Date(09/09/2001)"]', function (key, value) {
                var d;
                if (typeof value === 'string' &&
                        value.slice(0, 5) === 'Date(' &&
                        value.slice(-1) === ')') {
                    d = new Date(value.slice(5, -1));
                    if (d) {
                        return d;
                    }
                }
                return value;
            });


    This is a reference implementation. You are free to copy, modify, or
    redistribute.
*/

/*jslint evil: true, strict: false */

/*members "", "\b", "\t", "\n", "\f", "\r", "\"", JSON, "\\", apply,
    call, charCodeAt, getUTCDate, getUTCFullYear, getUTCHours,
    getUTCMinutes, getUTCMonth, getUTCSeconds, hasOwnProperty, join,
    lastIndex, length, parse, prototype, push, replace, slice, stringify,
    test, toJSON, toString, valueOf
*/


// Create a JSON object only if one does not already exist. We create the
// methods in a closure to avoid creating global variables.

if (!this.JSON) {
    this.JSON = {};
}

(function () {

    function f(n) {
        // Format integers to have at least two digits.
        return n < 10 ? '0' + n : n;
    }

    if (typeof Date.prototype.toJSON !== 'function') {

        Date.prototype.toJSON = function (key) {

            return isFinite(this.valueOf()) ?
                   this.getUTCFullYear()   + '-' +
                 f(this.getUTCMonth() + 1) + '-' +
                 f(this.getUTCDate())      + 'T' +
                 f(this.getUTCHours())     + ':' +
                 f(this.getUTCMinutes())   + ':' +
                 f(this.getUTCSeconds())   + 'Z' : null;
        };

        String.prototype.toJSON =
        Number.prototype.toJSON =
        Boolean.prototype.toJSON = function (key) {
            return this.valueOf();
        };
    }

    var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        escapable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        gap,
        indent,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        rep;


    function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

        escapable.lastIndex = 0;
        return escapable.test(string) ?
            '"' + string.replace(escapable, function (a) {
                var c = meta[a];
                return typeof c === 'string' ? c :
                    '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
            }) + '"' :
            '"' + string + '"';
    }


    function str(key, holder) {

// Produce a string from holder[key].

        var i,          // The loop counter.
            k,          // The member key.
            v,          // The member value.
            length,
            mind = gap,
            partial,
            value = holder[key];

// If the value has a toJSON method, call it to obtain a replacement value.

        if (value && typeof value === 'object' &&
                typeof value.toJSON === 'function') {
            value = value.toJSON(key);
        }

// If we were called with a replacer function, then call the replacer to
// obtain a replacement value.

        if (typeof rep === 'function') {
            value = rep.call(holder, key, value);
        }

// What happens next depends on the value's type.

        switch (typeof value) {
        case 'string':
            return quote(value);

        case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

            return isFinite(value) ? String(value) : 'null';

        case 'boolean':
        case 'null':

// If the value is a boolean or null, convert it to a string. Note:
// typeof null does not produce 'null'. The case is included here in
// the remote chance that this gets fixed someday.

            return String(value);

// If the type is 'object', we might be dealing with an object or an array or
// null.

        case 'object':

// Due to a specification blunder in ECMAScript, typeof null is 'object',
// so watch out for that case.

            if (!value) {
                return 'null';
            }

// Make an array to hold the partial results of stringifying this object value.

            gap += indent;
            partial = [];

// Is the value an array?

            if (Object.prototype.toString.apply(value) === '[object Array]') {

// The value is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

                length = value.length;
                for (i = 0; i < length; i += 1) {
                    partial[i] = str(i, value) || 'null';
                }

// Join all of the elements together, separated with commas, and wrap them in
// brackets.

                v = partial.length === 0 ? '[]' :
                    gap ? '[\n' + gap +
                            partial.join(',\n' + gap) + '\n' +
                                mind + ']' :
                          '[' + partial.join(',') + ']';
                gap = mind;
                return v;
            }

// If the replacer is an array, use it to select the members to be stringified.

            if (rep && typeof rep === 'object') {
                length = rep.length;
                for (i = 0; i < length; i += 1) {
                    k = rep[i];
                    if (typeof k === 'string') {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            } else {

// Otherwise, iterate through all of the keys in the object.

                for (k in value) {
                    if (Object.hasOwnProperty.call(value, k)) {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            }

// Join all of the member texts together, separated with commas,
// and wrap them in braces.

            v = partial.length === 0 ? '{}' :
                gap ? '{\n' + gap + partial.join(',\n' + gap) + '\n' +
                        mind + '}' : '{' + partial.join(',') + '}';
            gap = mind;
            return v;
        }
    }

// If the JSON object does not yet have a stringify method, give it one.

    if (typeof JSON.stringify !== 'function') {
        JSON.stringify = function (value, replacer, space) {

// The stringify method takes a value and an optional replacer, and an optional
// space parameter, and returns a JSON text. The replacer can be a function
// that can replace values, or an array of strings that will select the keys.
// A default replacer method can be provided. Use of the space parameter can
// produce text that is more easily readable.

            var i;
            gap = '';
            indent = '';

// If the space parameter is a number, make an indent string containing that
// many spaces.

            if (typeof space === 'number') {
                for (i = 0; i < space; i += 1) {
                    indent += ' ';
                }

// If the space parameter is a string, it will be used as the indent string.

            } else if (typeof space === 'string') {
                indent = space;
            }

// If there is a replacer, it must be a function or an array.
// Otherwise, throw an error.

            rep = replacer;
            if (replacer && typeof replacer !== 'function' &&
                    (typeof replacer !== 'object' ||
                     typeof replacer.length !== 'number')) {
                throw new Error('JSON.stringify');
            }

// Make a fake root object containing our value under the key of ''.
// Return the result of stringifying the value.

            return str('', {'': value});
        };
    }


// If the JSON object does not yet have a parse method, give it one.

    if (typeof JSON.parse !== 'function') {
        JSON.parse = function (text, reviver) {

// The parse method takes a text and an optional reviver function, and returns
// a JavaScript value if the text is a valid JSON text.

            var j;

            function walk(holder, key) {

// The walk method is used to recursively walk the resulting structure so
// that modifications can be made.

                var k, v, value = holder[key];
                if (value && typeof value === 'object') {
                    for (k in value) {
                        if (Object.hasOwnProperty.call(value, k)) {
                            v = walk(value, k);
                            if (v !== undefined) {
                                value[k] = v;
                            } else {
                                delete value[k];
                            }
                        }
                    }
                }
                return reviver.call(holder, key, value);
            }


// Parsing happens in four stages. In the first stage, we replace certain
// Unicode characters with escape sequences. JavaScript handles many characters
// incorrectly, either silently deleting them, or treating them as line endings.

            text = String(text);
            cx.lastIndex = 0;
            if (cx.test(text)) {
                text = text.replace(cx, function (a) {
                    return '\\u' +
                        ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
                });
            }

// In the second stage, we run the text against regular expressions that look
// for non-JSON patterns. We are especially concerned with '()' and 'new'
// because they can cause invocation, and '=' because it can cause mutation.
// But just to be safe, we want to reject all unexpected forms.

// We split the second stage into 4 regexp operations in order to work around
// crippling inefficiencies in IE's and Safari's regexp engines. First we
// replace the JSON backslash pairs with '@' (a non-JSON character). Second, we
// replace all simple value tokens with ']' characters. Third, we delete all
// open brackets that follow a colon or comma or that begin the text. Finally,
// we look to see that the remaining characters are only whitespace or ']' or
// ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

            if (/^[\],:{}\s]*$/
.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
.replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
.replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

// In the third stage we use the eval function to compile the text into a
// JavaScript structure. The '{' operator is subject to a syntactic ambiguity
// in JavaScript: it can begin a block or an object literal. We wrap the text
// in parens to eliminate the ambiguity.

                j = eval('(' + text + ')');

// In the optional fourth stage, we recursively walk the new structure, passing
// each name/value pair to a reviver function for possible transformation.

                return typeof reviver === 'function' ?
                    walk({'': j}, '') : j;
            }

// If the text is not JSON parseable, then a SyntaxError is thrown.

            throw new SyntaxError('JSON.parse');
        };
    }
}());
if (!Object.keys) Object.keys = function(o) {
    if (o !== Object(o))
        throw new TypeError('Object.keys called on a non-object');
    var k=[] , p;
    for (p in o) if (Object.prototype.hasOwnProperty.call(o,p)) k.push(p);
    return k;
}
/*
Copyright (c) 2005-2010 Yusuke Kawasaki. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in
   the documentation and/or other materials provided with the
   distribution.
3. Neither the name of the author nor the names of its contributors
   may be used to endorse or promote products derived from this 
   software without specific, prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
*/
// ================================================================
//  jkl-parsexml.js ---- JavaScript Kantan Library for Parsing XML
//  http://www.kawa.net/works/js/jkl/parsexml.html
// ================================================================
//  v0.01  2005/05/18  first release
//  v0.02  2005/05/20  Opera 8.0beta may be abailable but somtimes crashed
//  v0.03  2005/05/20  overrideMimeType( "text/xml" );
//  v0.04  2005/05/21  class variables: REQUEST_TYPE, RESPONSE_TYPE
//  v0.05  2005/05/22  use Msxml2.DOMDocument.5.0 for GET method on IE6
//  v0.06  2005/05/22  CDATA_SECTION_NODE
//  v0.07  2005/05/23  use Microsoft.XMLDOM for GET method on IE6
//  v0.10  2005/10/11  new function: ParseXMLToObject.ParseXML.HTTP.responseText()
//  v0.11  2005/10/13  new sub class: ParseXMLToObject.ParseXML.Text, JSON and DOM.
//  v0.12  2005/10/14  new sub class: ParseXMLToObject.ParseXML.CSV and CSVmap.
//  v0.13  2005/10/28  bug fixed: TEXT_NODE regexp for white spaces
//  v0.14  2005/11/06  bug fixed: TEXT_NODE regexp at Safari
//  v0.15  2005/11/08  bug fixed: ParseXMLToObject.ParseXML.CSV.async() method
//  v0.16  2005/11/15  new sub class: LoadVars, and UTF-8 text on Safari
//  v0.18  2005/11/16  improve: UTF-8 text file on Safari
//  v0.19  2006/02/03  use XMLHTTPRequest instead of ActiveX on IE7,iCab
//  v0.20  2006/03/22  (skipped)
//  v0.21  2006/11/30  use ActiveX again on IE7
//  v0.22  2007/01/04  ParseXMLToObject.ParseXML.JSON.parseResponse() updated
//  v0.22c 2010/01/07  New BSD License declaration added. no code changed

//  v3.3.0 2017/05/12  (gav) Added additional ways to parse strings directly.
// ================================================================

//Note:
/*
This file has been modified from its original format in the folloing ways
JKL has been changed to ParseXMLToObject for compatability with existing applications
*/
if ( typeof(ParseXMLToObject) == 'undefined' ) ParseXMLToObject = function() {};

// ================================================================
//  class: ParseXMLToObject.ParseXML 

/** @constructor */
ParseXMLToObject.ParseXML = function ( url, query, method ) {
    //console.log( "new ParseXMLToObject.ParseXML( '"+url+"', '"+query+"', '"+method+"' );" );
    this.http = new ParseXMLToObject.ParseXML.HTTP( url, query, method, false );
    return this;
};

// ================================================================
//  class variables

ParseXMLToObject.ParseXML.VERSION = "0.22";
ParseXMLToObject.ParseXML.MIME_TYPE_XML  = "text/xml";
ParseXMLToObject.ParseXML.MAP_NODETYPE = [
    "",
    "ELEMENT_NODE",                 // 1
    "ATTRIBUTE_NODE",               // 2
    "TEXT_NODE",                    // 3
    "CDATA_SECTION_NODE",           // 4
    "ENTITY_REFERENCE_NODE",        // 5
    "ENTITY_NODE",                  // 6
    "PROCESSING_INSTRUCTION_NODE",  // 7
    "COMMENT_NODE",                 // 8
    "DOCUMENT_NODE",                // 9
    "DOCUMENT_TYPE_NODE",           // 10
    "DOCUMENT_FRAGMENT_NODE",       // 11
    "NOTATION_NODE"                 // 12
];

// ================================================================
//  define callback function (ajax)

ParseXMLToObject.ParseXML.prototype.async = function ( func, args ) {
    this.callback_func = func;      // callback function
    this.callback_arg  = args;      // first argument
};

ParseXMLToObject.ParseXML.prototype.onerror = function ( func, args ) {
    this.onerror_func = func;       // callback function
};

// ================================================================
//  method: parse()
//  return: parsed object
//  Download a file from remote server and parse it.

ParseXMLToObject.ParseXML.prototype.parse = function () {
    if ( ! this.http ) return;

    // set onerror call back 
    if ( this.onerror_func ) {
        this.http.onerror( this.onerror_func );
    }

    if ( this.callback_func ) {                             // async mode
        var copy = this;
        var proc = function() {
            if ( ! copy.http ) return;
            var data = copy.parseResponse();
            copy.callback_func( data, copy.callback_arg );  // call back
        };
        this.http.async( proc );
    }

    this.http.load();

    if ( ! this.callback_func ) {                           // sync mode
        var data = this.parseResponse();
        return data;
    }
};

ParseXMLToObject.ParseXML.prototype.parseString = function (data) {
    var xml, tmp;
    if ( !data || typeof data !== "string" ) {
        return undefined;
    }
    try {
        if ( window.DOMParser ) { // Standard
            tmp = new window.DOMParser();
            xml = tmp.parseFromString( data, "text/xml" );
        } else { // IE
            xml = new window.ActiveXObject( "Microsoft.XMLDOM" );
            xml.async = "false";
            xml.loadXML( data );
        }
    } catch ( e ) {
        xml = undefined;
        return undefined;
    }
    if ( !xml || !xml.documentElement || xml.getElementsByTagName( "parsererror" ).length ) {
        alert( "Invalid XML: " + data );
        return undefined;
    }

    var out = this.parseDocument(xml.documentElement);
    return out;
}


// ================================================================
//  every child/children into array
ParseXMLToObject.ParseXML.prototype.setOutputArrayAll = function () {
    this.setOutputArray( true );
}
//  a child into scalar, children into array
ParseXMLToObject.ParseXML.prototype.setOutputArrayAuto = function () {
    this.setOutputArray( null );
}
//  every child/children into scalar (first sibiling only)
ParseXMLToObject.ParseXML.prototype.setOutputArrayNever = function () {
    this.setOutputArray( false );
}
//  specified child/children into array, other child/children into scalar
ParseXMLToObject.ParseXML.prototype.setOutputArrayElements = function ( list ) {
    this.setOutputArray( list );
}
//  specify how to treate child/children into scalar/array
ParseXMLToObject.ParseXML.prototype.setOutputArray = function ( mode ) {
    if ( typeof(mode) == "string" ) {
        mode = [ mode ];                // string into array
    }
    if ( mode && typeof(mode) == "object" ) {
        if ( mode.length < 0 ) {
            mode = false;               // false when array == [] 
        } else {
            var hash = {};
            for( var i=0; i<mode.length; i++ ) {
                hash[mode[i]] = true;
            }
            mode = hash;                // array into hashed array
            if ( mode["*"] ) {
                mode = true;            // true when includes "*"
            }
        } 
    } 
    this.usearray = mode;
}

// ================================================================
//  method: parseResponse()

ParseXMLToObject.ParseXML.prototype.parseResponse = function () {
    var root = this.http.documentElement();//he root object
    var data = this.parseDocument( root );
    return data;
}

// ================================================================
//  convert from DOM root node to JavaScript Object 
//  method: parseElement( rootElement )

ParseXMLToObject.ParseXML.prototype.parseDocument = function ( root ) {
//root: object
    //console.log( "parseDocument: "+root );
    if ( ! root ) return;

    var ret = this.parseElement( root );            // parse root node
    //console.log( "parsed: "+ret );

    if ( this.usearray == true ) {                  // always into array
        ret = [ ret ];
    } else if ( this.usearray == false ) {          // always into scalar
        //
    } else if ( this.usearray == null ) {           // automatic
        //
    } else if ( this.usearray[root.nodeName] ) {    // specified tag
        ret = [ ret ];
    }

    var json = {};
    json[root.nodeName] = ret;                      // root nodeName
    return json;
};

// ================================================================
//  convert from DOM Element to JavaScript Object 
//  method: parseElement( element )

ParseXMLToObject.ParseXML.prototype.parseElement = function ( elem ) {
    //console.log( "nodeType: "+ParseXMLToObject.ParseXML.MAP_NODETYPE[elem.nodeType]+" <"+elem.nodeName+">" );

    //  COMMENT_NODE

    if ( elem.nodeType == 7 ) {
        return;
    }

    //  TEXT_NODE CDATA_SECTION_NODE

    if ( elem.nodeType == 3 || elem.nodeType == 4 ) {
        // var bool = elem.nodeValue.match( /[^\u0000-\u0020]/ );
        var bool = elem.nodeValue.match( /[^\x00-\x20]/ ); // for Safari
        if ( bool == null ) return;     // ignore white spaces
        //console.log( "TEXT_NODE: "+elem.nodeValue.length+ " "+bool );
        return elem.nodeValue;
    }

    var retval;
    var cnt = {};

    //  parse attributes

    if ( elem.attributes && elem.attributes.length ) {
        retval = {};
        for ( var i=0; i<elem.attributes.length; i++ ) {
            var key = elem.attributes[i].nodeName;
            if ( typeof(key) != "string" ) continue;
            var val = elem.attributes[i].nodeValue;
            if ( ! val ) continue;
            if ( typeof(cnt[key]) == "undefined" ) cnt[key] = 0;
            cnt[key] ++;
            this.addNode( retval, key, cnt[key], val );
        }
    }

    //  parse child nodes (recursive)

    if ( elem.childNodes && elem.childNodes.length ) {
        var textonly = true;
        if ( retval ) textonly = false;        // some attributes exists
        for ( var i=0; i<elem.childNodes.length && textonly; i++ ) {
            var ntype = elem.childNodes[i].nodeType;
            if ( ntype == 3 || ntype == 4 ) continue;
            textonly = false;
        }
        if ( textonly ) {
            if ( ! retval ) retval = "";
            for ( var i=0; i<elem.childNodes.length; i++ ) {
                retval += elem.childNodes[i].nodeValue;
            }
        } else {
            if ( ! retval ) retval = {};
            for ( var i=0; i<elem.childNodes.length; i++ ) {
                var key = elem.childNodes[i].nodeName;
                if ( typeof(key) != "string" ) continue;
                var val = this.parseElement( elem.childNodes[i] );
                if ( ! val ) continue;
                if ( typeof(cnt[key]) == "undefined" ) cnt[key] = 0;
                cnt[key] ++;
                this.addNode( retval, key, cnt[key], val );
            }
        }
    }
    return retval;
};

// ================================================================
//  method: addNode( hash, key, count, value )

ParseXMLToObject.ParseXML.prototype.addNode = function ( hash, key, cnts, val ) {
    if ( this.usearray == true ) {              // into array
        if ( cnts == 1 ) hash[key] = [];
        hash[key][hash[key].length] = val;      // push
    } else if ( this.usearray == false ) {      // into scalar
        if ( cnts == 1 ) hash[key] = val;       // only 1st sibling
    } else if ( this.usearray == null ) {
        if ( cnts == 1 ) {                      // 1st sibling
            hash[key] = val;
        } else if ( cnts == 2 ) {               // 2nd sibling
            hash[key] = [ hash[key], val ];
        } else {                                // 3rd sibling and more
            hash[key][hash[key].length] = val;
        }
    } else if ( this.usearray[key] ) {
        if ( cnts == 1 ) hash[key] = [];
        hash[key][hash[key].length] = val;      // push
    } else {
        if ( cnts == 1 ) hash[key] = val;       // only 1st sibling
    }
};

// ================================================================
//  class: ParseXMLToObject.ParseXML.HTTP
//  constructer: new ParseXMLToObject.ParseXML.HTTP()

/** @constructor */
ParseXMLToObject.ParseXML.HTTP = function( url, query, method, textmode ) {
    //console.log( "new ParseXMLToObject.ParseXML.HTTP( '"+url+"', '"+query+"', '"+method+"', '"+textmode+"' );" );
    this.url = url;
    if ( typeof(query) == "string" ) {
        this.query = query;
    } else {
        this.query = "";
    }
    if ( method ) {
        this.method = method;
    } else if ( typeof(query) == "string" ) {
        this.method = "POST";
    } else {
        this.method = "GET";
    }
    this.textmode = textmode ? true : false;
    this.req = null;
    this.xmldom_flag = false;
    this.onerror_func  = null;
    this.callback_func = null;
    this.already_done = null;
    return this;
};

// ================================================================
//  class variables

ParseXMLToObject.ParseXML.HTTP.REQUEST_TYPE  = "application/x-www-form-urlencoded";
ParseXMLToObject.ParseXML.HTTP.ACTIVEX_XMLDOM  = "Microsoft.XMLDOM";  // Msxml2.DOMDocument.5.0
ParseXMLToObject.ParseXML.HTTP.ACTIVEX_XMLHTTP = "Microsoft.XMLHTTP"; // Msxml2.XMLHTTP.3.0
ParseXMLToObject.ParseXML.HTTP.EPOCH_TIMESTAMP = "Thu, 01 Jun 1970 00:00:00 GMT"

// ================================================================

ParseXMLToObject.ParseXML.HTTP.prototype.onerror = ParseXMLToObject.ParseXML.prototype.onerror;
ParseXMLToObject.ParseXML.HTTP.prototype.async = function( func ) {
    this.async_func = func;
}

// ================================================================
//  [IE+IXMLDOMElement]
//      XML     text/xml            OK
//      XML     application/rdf+xml OK
//      TEXT    text/plain          NG
//      TEXT    others              NG
//  [IE+IXMLHttpRequest]
//      XML     text/xml            OK
//      XML     application/rdf+xml NG
//      TEXT    text/plain          OK
//      TEXT    others              OK
//  [Firefox+XMLHttpRequest]
//      XML     text/xml            OK
//      XML     application/rdf+xml OK (overrideMimeType)
//      TEXT    text/plain          OK
//      TEXT    others              OK (overrideMimeType)
//  [Opera+XMLHttpRequest]
//      XML     text/xml            OK
//      XML     application/rdf+xml OK
//      TEXT    text/plain          OK
//      TEXT    others              OK
// ================================================================

ParseXMLToObject.ParseXML.HTTP.prototype.load = function() {
    // create XMLHttpRequest object
    if ( window.ActiveXObject ) {                           // IE5.5,6,7
        var activex = ParseXMLToObject.ParseXML.HTTP.ACTIVEX_XMLHTTP;    // IXMLHttpRequest
        if ( this.method == "GET" && ! this.textmode ) {
            // use IXMLDOMElement to accept any mime types
            // because overrideMimeType() is not available on IE6
            activex = ParseXMLToObject.ParseXML.HTTP.ACTIVEX_XMLDOM;     // IXMLDOMElement
        }
        //console.log( "new ActiveXObject( '"+activex+"' )" );
        this.req = new ActiveXObject( activex );
    } else if ( window.XMLHttpRequest ) {                   // Firefox, Opera, iCab
        //console.log( "new XMLHttpRequest()" );
        this.req = new XMLHttpRequest();
    }

    // async mode when call back function is specified
    var async_flag = this.async_func ? true : false;
    //console.log( "async: "+ async_flag );

    // open for XMLHTTPRequest (not for IXMLDOMElement)
    if ( typeof(this.req.send) != "undefined" ) {
        //console.log( "open( '"+this.method+"', '"+this.url+"', "+async_flag+" );" );
        this.req.open( this.method, this.url, async_flag );
    }

//  // If-Modified-Since: Thu, 01 Jun 1970 00:00:00 GMT
//  if ( typeof(this.req.setRequestHeader) != "undefined" ) {
//      //console.log( "If-Modified-Since"+ParseXMLToObject.ParseXML.HTTP.EPOCH_TIMESTAMP );
//      this.req.setRequestHeader( "If-Modified-Since", ParseXMLToObject.ParseXML.HTTP.EPOCH_TIMESTAMP );
//  }

    // Content-Type: application/x-www-form-urlencoded (request header)
    // Some server does not accept without request content-type.
    if ( typeof(this.req.setRequestHeader) != "undefined" ) {
        //console.log( "Content-Type: "+ParseXMLToObject.ParseXML.HTTP.REQUEST_TYPE+" (request)" );
        this.req.setRequestHeader( "Content-Type", ParseXMLToObject.ParseXML.HTTP.REQUEST_TYPE );
    }

    // Content-Type: text/xml (response header)
    // FireFox does not accept other mime types like application/rdf+xml etc.
    if ( typeof(this.req.overrideMimeType) != "undefined" && ! this.textmode ) {
        //console.log( "Content-Type: "+ParseXMLToObject.ParseXML.MIME_TYPE_XML+" (response)" );
        this.req.overrideMimeType( ParseXMLToObject.ParseXML.MIME_TYPE_XML );
    }

    // set call back handler when async mode
    if ( async_flag ) {
        var copy = this;
        copy.already_done = false;                  // not parsed yet
        var check_func = function () {
            if ( copy.req.readyState != 4 ) return;
            //console.log( "readyState(async): "+copy.req.readyState );
            var succeed = copy.checkResponse();
            //console.log( "checkResponse(async): "+succeed );
            if ( ! succeed ) return;                // failed
            if ( copy.already_done ) return;        // parse only once
            copy.already_done = true;               // already parsed
            copy.async_func();                      // call back async
        };
        this.req.onreadystatechange = check_func;
        // for document.implementation.createDocument
        // this.req.onload = check_func;
    }

    // send the request and query string
    if ( typeof(this.req.send) != "undefined" ) {
        //console.log( "XMLHTTPRequest: send( '"+this.query+"' );" );
		this.req.send( this.query );                        // XMLHTTPRequest
	} else if ( typeof(this.req.load) != "undefined" ) {
        //console.log( "IXMLDOMElement: load( '"+this.url+"' );" );
        this.req.async = async_flag;
        this.req.load( this.url );                          // IXMLDOMElement
    }

    // just return when async mode
    if ( async_flag ) return;

    var succeed = this.checkResponse();
    //console.log( "checkResponse(sync): "+succeed );
}

// ================================================================
//  method: checkResponse()

ParseXMLToObject.ParseXML.HTTP.prototype.checkResponse = function() {
    // parseError on IXMLDOMElement
    if ( this.req.parseError && this.req.parseError.errorCode != 0 ) {
        //console.log( "parseError: "+this.req.parseError.reason );
        if ( this.onerror_func ) this.onerror_func( this.req.parseError.reason );
        return false;                       // failed
    }

    // HTTP response code
    if ( this.req.status-0 > 0 &&
         this.req.status != 200 &&          // OK
         this.req.status != 206 &&          // Partial Content
         this.req.status != 304 ) {         // Not Modified
        //console.log( "status: "+this.req.status );
        if ( this.onerror_func ) this.onerror_func( this.req.status );
        return false;                       // failed
    }

    return true;                            // succeed
}

// ================================================================
//  method: documentElement()
//  return: XML DOM in response body

ParseXMLToObject.ParseXML.HTTP.prototype.documentElement = function() {
    //console.log( "documentElement: "+this.req );
    if ( ! this.req ) return;
    if ( this.req.responseXML ) {
        return this.req.responseXML.documentElement;    // XMLHTTPRequest
    } else {
        return this.req.documentElement;                // IXMLDOMDocument
    }
}

// ================================================================
//  method: responseText()
//  return: text string in response body

ParseXMLToObject.ParseXML.HTTP.prototype.responseText = function() {
    //console.log( "responseText: "+this.req );
    if ( ! this.req ) return;

    //  Safari and Konqueror cannot understand the encoding of text files.
    if ( navigator.appVersion.match( "KHTML" ) ) {
        var esc = escape( this.req.responseText );
//        debug.print( "escape: "+esc );
        if ( ! esc.match("%u") && esc.match("%") ) {
            return decodeURIComponent(esc);
        }
    }

    return this.req.responseText;
}

// ================================================================
//  http://msdn.microsoft.com/library/en-us/xmlsdk/html/d051f7c5-e882-42e8-a5b6-d1ce67af275c.asp
// ================================================================
/*!
  * Reqwest! A general purpose XHR connection manager
  * license MIT (c) Dustin Diaz 2015
  * https://github.com/ded/reqwest
  */
!function(e,t,n){typeof module!="undefined"&&module.exports?module.exports=n():typeof define=="function"&&define.amd?define(n):t[e]=n()}("reqwest",this,function(){function succeed(e){var t=protocolRe.exec(e.url);return t=t&&t[1]||context.location.protocol,httpsRe.test(t)?twoHundo.test(e.request.status):!!e.request.response}function handleReadyState(e,t,n){return function(){if(e._aborted)return n(e.request);if(e._timedOut)return n(e.request,"Request is aborted: timeout");e.request&&e.request[readyState]==4&&(e.request.onreadystatechange=noop,succeed(e)?t(e.request):n(e.request))}}function setHeaders(e,t){var n=t.headers||{},r;n.Accept=n.Accept||defaultHeaders.accept[t.type]||defaultHeaders.accept["*"];var i=typeof FormData!="undefined"&&t.data instanceof FormData;!t.crossOrigin&&!n[requestedWith]&&(n[requestedWith]=defaultHeaders.requestedWith),!n[contentType]&&!i&&(n[contentType]=t.contentType||defaultHeaders.contentType);for(r in n)n.hasOwnProperty(r)&&"setRequestHeader"in e&&e.setRequestHeader(r,n[r])}function setCredentials(e,t){typeof t.withCredentials!="undefined"&&typeof e.withCredentials!="undefined"&&(e.withCredentials=!!t.withCredentials)}function generalCallback(e){lastValue=e}function urlappend(e,t){return e+(/\?/.test(e)?"&":"?")+t}function handleJsonp(e,t,n,r){var i=uniqid++,s=e.jsonpCallback||"callback",o=e.jsonpCallbackName||reqwest.getcallbackPrefix(i),u=new RegExp("((^|\\?|&)"+s+")=([^&]+)"),a=r.match(u),f=doc.createElement("script"),l=0,c=navigator.userAgent.indexOf("MSIE 10.0")!==-1;return a?a[3]==="?"?r=r.replace(u,"$1="+o):o=a[3]:r=urlappend(r,s+"="+o),context[o]=generalCallback,f.type="text/javascript",f.src=r,f.async=!0,typeof f.onreadystatechange!="undefined"&&!c&&(f.htmlFor=f.id="_reqwest_"+i),f.onload=f.onreadystatechange=function(){if(f[readyState]&&f[readyState]!=="complete"&&f[readyState]!=="loaded"||l)return!1;f.onload=f.onreadystatechange=null,f.onclick&&f.onclick(),t(lastValue),lastValue=undefined,head.removeChild(f),l=1},head.appendChild(f),{abort:function(){f.onload=f.onreadystatechange=null,n({},"Request is aborted: timeout",{}),lastValue=undefined,head.removeChild(f),l=1}}}function getRequest(e,t){var n=this.o,r=(n.method||"GET").toUpperCase(),i=typeof n=="string"?n:n.url,s=n.processData!==!1&&n.data&&typeof n.data!="string"?reqwest.toQueryString(n.data):n.data||null,o,u=!1;return(n["type"]=="jsonp"||r=="GET")&&s&&(i=urlappend(i,s),s=null),n["type"]=="jsonp"?handleJsonp(n,e,t,i):(o=n.xhr&&n.xhr(n)||xhr(n),o.open(r,i,n.async===!1?!1:!0),setHeaders(o,n),setCredentials(o,n),context[xDomainRequest]&&o instanceof context[xDomainRequest]?(o.onload=e,o.onerror=t,o.onprogress=function(){},u=!0):o.onreadystatechange=handleReadyState(this,e,t),n.before&&n.before(o),u?setTimeout(function(){o.send(s)},200):o.send(s),o)}function Reqwest(e,t){this.o=e,this.fn=t,init.apply(this,arguments)}function setType(e){if(e===null)return undefined;if(e.match("json"))return"json";if(e.match("javascript"))return"js";if(e.match("text"))return"html";if(e.match("xml"))return"xml"}function init(o,fn){function complete(e){o.timeout&&clearTimeout(self.timeout),self.timeout=null;while(self._completeHandlers.length>0)self._completeHandlers.shift()(e)}function success(resp){var type=o.type||resp&&setType(resp.getResponseHeader("Content-Type"));resp=type!=="jsonp"?self.request:resp;var filteredResponse=globalSetupOptions.dataFilter(resp.responseText,type),r=filteredResponse;try{resp.responseText=r}catch(e){}if(r)switch(type){case"json":try{resp=context.JSON?context.JSON.parse(r):eval("("+r+")")}catch(err){return error(resp,"Could not parse JSON in response",err)}break;case"js":resp=eval(r);break;case"html":resp=r;break;case"xml":resp=resp.responseXML&&resp.responseXML.parseError&&resp.responseXML.parseError.errorCode&&resp.responseXML.parseError.reason?null:resp.responseXML}self._responseArgs.resp=resp,self._fulfilled=!0,fn(resp),self._successHandler(resp);while(self._fulfillmentHandlers.length>0)resp=self._fulfillmentHandlers.shift()(resp);complete(resp)}function timedOut(){self._timedOut=!0,self.request.abort()}function error(e,t,n){e=self.request,self._responseArgs.resp=e,self._responseArgs.msg=t,self._responseArgs.t=n,self._erred=!0;while(self._errorHandlers.length>0)self._errorHandlers.shift()(e,t,n);complete(e)}this.url=typeof o=="string"?o:o.url,this.timeout=null,this._fulfilled=!1,this._successHandler=function(){},this._fulfillmentHandlers=[],this._errorHandlers=[],this._completeHandlers=[],this._erred=!1,this._responseArgs={};var self=this;fn=fn||function(){},o.timeout&&(this.timeout=setTimeout(function(){timedOut()},o.timeout)),o.success&&(this._successHandler=function(){o.success.apply(o,arguments)}),o.error&&this._errorHandlers.push(function(){o.error.apply(o,arguments)}),o.complete&&this._completeHandlers.push(function(){o.complete.apply(o,arguments)}),this.request=getRequest.call(this,success,error)}function reqwest(e,t){return new Reqwest(e,t)}function normalize(e){return e?e.replace(/\r?\n/g,"\r\n"):""}function serial(e,t){var n=e.name,r=e.tagName.toLowerCase(),i=function(e){e&&!e.disabled&&t(n,normalize(e.attributes.value&&e.attributes.value.specified?e.value:e.text))},s,o,u,a;if(e.disabled||!n)return;switch(r){case"input":/reset|button|image|file/i.test(e.type)||(s=/checkbox/i.test(e.type),o=/radio/i.test(e.type),u=e.value,(!s&&!o||e.checked)&&t(n,normalize(s&&u===""?"on":u)));break;case"textarea":t(n,normalize(e.value));break;case"select":if(e.type.toLowerCase()==="select-one")i(e.selectedIndex>=0?e.options[e.selectedIndex]:null);else for(a=0;e.length&&a<e.length;a++)e.options[a].selected&&i(e.options[a])}}function eachFormElement(){var e=this,t,n,r=function(t,n){var r,i,s;for(r=0;r<n.length;r++){s=t[byTag](n[r]);for(i=0;i<s.length;i++)serial(s[i],e)}};for(n=0;n<arguments.length;n++)t=arguments[n],/input|select|textarea/i.test(t.tagName)&&serial(t,e),r(t,["input","select","textarea"])}function serializeQueryString(){return reqwest.toQueryString(reqwest.serializeArray.apply(null,arguments))}function serializeHash(){var e={};return eachFormElement.apply(function(t,n){t in e?(e[t]&&!isArray(e[t])&&(e[t]=[e[t]]),e[t].push(n)):e[t]=n},arguments),e}function buildParams(e,t,n,r){var i,s,o,u=/\[\]$/;if(isArray(t))for(s=0;t&&s<t.length;s++)o=t[s],n||u.test(e)?r(e,o):buildParams(e+"["+(typeof o=="object"?s:"")+"]",o,n,r);else if(t&&t.toString()==="[object Object]")for(i in t)buildParams(e+"["+i+"]",t[i],n,r);else r(e,t)}var context=this;if("window"in context)var doc=document,byTag="getElementsByTagName",head=doc[byTag]("head")[0];else{var XHR2;try{XHR2=require("xhr2")}catch(ex){throw new Error("Peer dependency `xhr2` required! Please npm install xhr2")}}var httpsRe=/^http/,protocolRe=/(^\w+):\/\//,twoHundo=/^(20\d|1223)$/,readyState="readyState",contentType="Content-Type",requestedWith="X-Requested-With",uniqid=0,callbackPrefix="reqwest_"+ +(new Date),lastValue,xmlHttpRequest="XMLHttpRequest",xDomainRequest="XDomainRequest",noop=function(){},isArray=typeof Array.isArray=="function"?Array.isArray:function(e){return e instanceof Array},defaultHeaders={contentType:"application/x-www-form-urlencoded",requestedWith:xmlHttpRequest,accept:{"*":"text/javascript, text/html, application/xml, text/xml, */*",xml:"application/xml, text/xml",html:"text/html",text:"text/plain",json:"application/json, text/javascript",js:"application/javascript, text/javascript"}},xhr=function(e){if(e.crossOrigin===!0){var t=context[xmlHttpRequest]?new XMLHttpRequest:null;if(t&&"withCredentials"in t)return t;if(context[xDomainRequest])return new XDomainRequest;throw new Error("Browser does not support cross-origin requests")}return context[xmlHttpRequest]?new XMLHttpRequest:XHR2?new XHR2:new ActiveXObject("Microsoft.XMLHTTP")},globalSetupOptions={dataFilter:function(e){return e}};return Reqwest.prototype={abort:function(){this._aborted=!0,this.request.abort()},retry:function(){init.call(this,this.o,this.fn)},then:function(e,t){return e=e||function(){},t=t||function(){},this._fulfilled?this._responseArgs.resp=e(this._responseArgs.resp):this._erred?t(this._responseArgs.resp,this._responseArgs.msg,this._responseArgs.t):(this._fulfillmentHandlers.push(e),this._errorHandlers.push(t)),this},always:function(e){return this._fulfilled||this._erred?e(this._responseArgs.resp):this._completeHandlers.push(e),this},fail:function(e){return this._erred?e(this._responseArgs.resp,this._responseArgs.msg,this._responseArgs.t):this._errorHandlers.push(e),this},"catch":function(e){return this.fail(e)}},reqwest.serializeArray=function(){var e=[];return eachFormElement.apply(function(t,n){e.push({name:t,value:n})},arguments),e},reqwest.serialize=function(){if(arguments.length===0)return"";var e,t,n=Array.prototype.slice.call(arguments,0);return e=n.pop(),e&&e.nodeType&&n.push(e)&&(e=null),e&&(e=e.type),e=="map"?t=serializeHash:e=="array"?t=reqwest.serializeArray:t=serializeQueryString,t.apply(null,n)},reqwest.toQueryString=function(e,t){var n,r,i=t||!1,s=[],o=encodeURIComponent,u=function(e,t){t="function"==typeof t?t():t==null?"":t,s[s.length]=o(e)+"="+o(t)};if(isArray(e))for(r=0;e&&r<e.length;r++)u(e[r].name,e[r].value);else for(n in e)e.hasOwnProperty(n)&&buildParams(n,e[n],i,u);return s.join("&").replace(/%20/g,"+")},reqwest.getcallbackPrefix=function(){return callbackPrefix},reqwest.compat=function(e,t){return e&&(e.type&&(e.method=e.type)&&delete e.type,e.dataType&&(e.type=e.dataType),e.jsonpCallback&&(e.jsonpCallbackName=e.jsonpCallback)&&delete e.jsonpCallback,e.jsonp&&(e.jsonpCallback=e.jsonp)),new Reqwest(e,t)},reqwest.ajaxSetup=function(e){e=e||{};for(var t in e)globalSetupOptions[t]=e[t]},reqwest})
;
/*

 JS Signals <http://millermedeiros.github.com/js-signals/>
 Released under the MIT license
 Author: Miller Medeiros
 Version: 1.0.0 - Build: 268 (2012/11/29 05:48 PM)
*/
(function(i){function h(a,b,c,d,e){this._listener=b;this._isOnce=c;this.context=d;this._signal=a;this._priority=e||0}function g(a,b){if(typeof a!=="function")throw Error("listener is a required param of {fn}() and should be a Function.".replace("{fn}",b));}function e(){this._bindings=[];this._prevParams=null;var a=this;this.dispatch=function(){e.prototype.dispatch.apply(a,arguments)}}h.prototype={active:!0,params:null,execute:function(a){var b;this.active&&this._listener&&(a=this.params?this.params.concat(a):
a,b=this._listener.apply(this.context,a),this._isOnce&&this.detach());return b},detach:function(){return this.isBound()?this._signal.remove(this._listener,this.context):null},isBound:function(){return!!this._signal&&!!this._listener},isOnce:function(){return this._isOnce},getListener:function(){return this._listener},getSignal:function(){return this._signal},_destroy:function(){delete this._signal;delete this._listener;delete this.context},toString:function(){return"[SignalBinding isOnce:"+this._isOnce+
", isBound:"+this.isBound()+", active:"+this.active+"]"}};e.prototype={VERSION:"1.0.0",memorize:!1,_shouldPropagate:!0,active:!0,_registerListener:function(a,b,c,d){var e=this._indexOfListener(a,c);if(e!==-1){if(a=this._bindings[e],a.isOnce()!==b)throw Error("You cannot add"+(b?"":"Once")+"() then add"+(!b?"":"Once")+"() the same listener without removing the relationship first.");}else a=new h(this,a,b,c,d),this._addBinding(a);this.memorize&&this._prevParams&&a.execute(this._prevParams);return a},
_addBinding:function(a){var b=this._bindings.length;do--b;while(this._bindings[b]&&a._priority<=this._bindings[b]._priority);this._bindings.splice(b+1,0,a)},_indexOfListener:function(a,b){for(var c=this._bindings.length,d;c--;)if(d=this._bindings[c],d._listener===a&&d.context===b)return c;return-1},has:function(a,b){return this._indexOfListener(a,b)!==-1},add:function(a,b,c){g(a,"add");return this._registerListener(a,!1,b,c)},addOnce:function(a,b,c){g(a,"addOnce");return this._registerListener(a,
!0,b,c)},remove:function(a,b){g(a,"remove");var c=this._indexOfListener(a,b);c!==-1&&(this._bindings[c]._destroy(),this._bindings.splice(c,1));return a},removeAll:function(){for(var a=this._bindings.length;a--;)this._bindings[a]._destroy();this._bindings.length=0},getNumListeners:function(){return this._bindings.length},halt:function(){this._shouldPropagate=!1},dispatch:function(a){if(this.active){var b=Array.prototype.slice.call(arguments),c=this._bindings.length,d;if(this.memorize)this._prevParams=
b;if(c){d=this._bindings.slice();this._shouldPropagate=!0;do c--;while(d[c]&&this._shouldPropagate&&d[c].execute(b)!==!1)}}},forget:function(){this._prevParams=null},dispose:function(){this.removeAll();delete this._bindings;delete this._prevParams},toString:function(){return"[Signal active:"+this.active+" numListeners:"+this.getNumListeners()+"]"}};var f=e;f.Signal=e;typeof define==="function"&&define.amd?define(function(){return f}):typeof module!=="undefined"&&module.exports?module.exports=f:i.signals=
f})(this);(function(window) {
    var re = {
        not_string: /[^sS]/,
        number: /[def]/,
        text: /^[^\x25]+/,
        modulo: /^\x25{2}/,
        placeholder: /^\x25(?:([1-9]\d*)\$|\(([^\)]+)\))?(\+)?(0|'[^$])?(-)?(\d+)?(?:\.(\d+))?([b-fosSuxX])/,
        key: /^([a-z_][a-z_\d]*)/i,
        key_access: /^\.([a-z_][a-z_\d]*)/i,
        index_access: /^\[(\d+)\]/,
        sign: /^[\+\-]/
    }

    function sprintf() {
        var key = arguments[0], cache = sprintf.cache
        if (!(cache[key] && cache.hasOwnProperty(key))) {
            cache[key] = sprintf.parse(key)
        }
        return sprintf.format.call(null, cache[key], arguments)
    }

    sprintf.format = function(parse_tree, argv) {
        var cursor = 1, tree_length = parse_tree.length, node_type = "", arg, output = [], i, k, match, pad, pad_character, pad_length, is_positive = true, sign = ""
        for (i = 0; i < tree_length; i++) {
            node_type = get_type(parse_tree[i])
            if (node_type === "string") {
                output[output.length] = parse_tree[i]
            }
            else if (node_type === "array") {
                match = parse_tree[i] // convenience purposes only
                if (match[2]) { // keyword argument
                    arg = argv[cursor]
                    for (k = 0; k < match[2].length; k++) {
                        if (!arg.hasOwnProperty(match[2][k])) {
                            throw new Error(sprintf("[sprintf] property '%s' does not exist", match[2][k]))
                        }
                        arg = arg[match[2][k]]
                    }
                }
                else if (match[1]) { // positional argument (explicit)
                    arg = argv[match[1]]
                }
                else { // positional argument (implicit)
                    arg = argv[cursor++]
                }

                if (get_type(arg) == "function") {
                    arg = arg()
                }

                if (re.not_string.test(match[8]) && (get_type(arg) != "number" && isNaN(arg))) {
                    throw new TypeError(sprintf("[sprintf] expecting number but found %s", get_type(arg)))
                }

                if (re.number.test(match[8])) {
                    is_positive = arg >= 0
                }

                switch (match[8]) {
                    case "b":
                        arg = arg.toString(2)
                        break
                    case "c":
                        arg = String.fromCharCode(arg)
                        break
                    case "d":
                        arg = parseInt(arg, 10)
                        break
                    case "e":
                        arg = match[7] ? arg.toExponential(match[7]) : arg.toExponential()
                        break
                    case "f":
                        arg = match[7] ? parseFloat(arg).toFixed(match[7]) : parseFloat(arg)
                        break
                    case "o":
                        arg = arg.toString(8)
                        break
                    case "s":
                        arg = ((arg = String(arg)) && match[7] ? arg.substring(0, match[7]) : arg)
                        break
                    case "S":
                        arg = "'" + ((arg = String(arg)) && match[7] ? arg.substring(0, match[7]) : arg) + "'"
                        break
                    case "u":
                        arg = arg >>> 0
                        break
                    case "x":
                        arg = arg.toString(16)
                        break
                    case "X":
                        arg = arg.toString(16).toUpperCase()
                        break
                }
                if (!is_positive || (re.number.test(match[8]) && match[3])) {
                    sign = is_positive ? "+" : "-"
                    arg = arg.toString().replace(re.sign, "")
                }
                pad_character = match[4] ? match[4] == "0" ? "0" : match[4].charAt(1) : " "
                pad_length = match[6] - (sign + arg).length
                pad = match[6] ? str_repeat(pad_character, pad_length) : ""
                output[output.length] = match[5] ? sign + arg + pad : (pad_character == 0 ? sign + pad + arg : pad + sign + arg)
            }
        }
        return output.join("")
    }

    sprintf.cache = {}

    sprintf.parse = function(fmt) {
        var _fmt = fmt, match = [], parse_tree = [], arg_names = 0
        while (_fmt) {
            if ((match = re.text.exec(_fmt)) !== null) {
                parse_tree[parse_tree.length] = match[0]
            }
            else if ((match = re.modulo.exec(_fmt)) !== null) {
                parse_tree[parse_tree.length] = "%"
            }
            else if ((match = re.placeholder.exec(_fmt)) !== null) {
                if (match[2]) {
                    arg_names |= 1
                    var field_list = [], replacement_field = match[2], field_match = []
                    if ((field_match = re.key.exec(replacement_field)) !== null) {
                        field_list[field_list.length] = field_match[1]
                        while ((replacement_field = replacement_field.substring(field_match[0].length)) !== "") {
                            if ((field_match = re.key_access.exec(replacement_field)) !== null) {
                                field_list[field_list.length] = field_match[1]
                            }
                            else if ((field_match = re.index_access.exec(replacement_field)) !== null) {
                                field_list[field_list.length] = field_match[1]
                            }
                            else {
                                throw new SyntaxError("[sprintf] failed to parse named argument key")
                            }
                        }
                    }
                    else {
                        throw new SyntaxError("[sprintf] failed to parse named argument key")
                    }
                    match[2] = field_list
                }
                else {
                    arg_names |= 2
                }
                if (arg_names === 3) {
                    throw new Error("[sprintf] mixing positional and named placeholders is not (yet) supported")
                }
                parse_tree[parse_tree.length] = match
            }
            else {
                throw new SyntaxError("[sprintf] unexpected placeholder")
            }
            _fmt = _fmt.substring(match[0].length)
        }
        return parse_tree
    }

    var vsprintf = function(fmt, argv, _argv) {
        _argv = (argv || []).slice(0)
        _argv.splice(0, 0, fmt)
        return sprintf.apply(null, _argv)
    }

    /**
     * helpers
     */
    function get_type(variable) {
        return Object.prototype.toString.call(variable).slice(8, -1).toLowerCase()
    }

    function str_repeat(input, multiplier) {
        return Array(multiplier + 1).join(input)
    }

    /**
     * export to either browser or node.js
     */
    if (typeof exports !== "undefined") {
        exports.sprintf = sprintf
        exports.vsprintf = vsprintf
    }
    else {
        window.sprintf = sprintf
        window.vsprintf = vsprintf

        if (typeof define === "function" && define.amd) {
            define(function() {
                return {
                    sprintf: sprintf,
                    vsprintf: vsprintf
                }
            })
        }
    }
})(typeof window === "undefined" ? this : window);
