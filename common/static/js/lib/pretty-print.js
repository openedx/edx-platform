/**
* pretty-data - nodejs plugin to pretty-print or minify data in XML, JSON and CSS formats.
*
* Version - 0.40.0
* Copyright (c) 2012 Vadim Kiryukhin
* vkiryukhin @ gmail.com
* http://www.eslinstructor.net/pretty-data/
*
*
* Code extracted for xml formatting only
*/

/* eslint-disable */

(function (root, factory){
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define([], function (){
            return (root.PrettyPrint = factory());
        });
    } else {
        // Browser globals
        root.PrettyPrint = factory();
    }
}(this, function () {
    function PrettyPrint(){
        var maxdeep = 100, // nesting level
            ix = 0;

        this.shift = ['\n']; // array of shifts
        this.step = '  '; // 2 spaces

        // initialize array with shifts //
        for (ix = 0; ix < maxdeep; ix++) {
            this.shift.push(this.shift[ix] + this.step);
        }
    }

    PrettyPrint.prototype.xml = function (text) {
        var ar = text.replace(/>\s{0,}</g, "><")
                .replace(/</g, "~::~<")
                .replace(/xmlns\:/g, "~::~xmlns:")
                .replace(/xmlns\=/g, "~::~xmlns=")
                .split('~::~'),
            len = ar.length,
            inComment = false,
            deep = 0,
            str = '',
            ix = 0;

        for (ix = 0; ix < len; ix++) {
            // start comment or <![CDATA[...]]> or <!DOCTYPE //
            if (ar[ix].search(/<!/) > -1) {
                str += this.shift[deep] + ar[ix];
                inComment = true;
                // end comment  or <![CDATA[...]]> //
                if (ar[ix].search(/-->/) > -1 || ar[ix].search(/\]>/) > -1 || ar[ix].search(/!DOCTYPE/) > -1) {
                    inComment = false;
                }
            } else
            // end comment  or <![CDATA[...]]> //
            if (ar[ix].search(/-->/) > -1 || ar[ix].search(/\]>/) > -1) {
                str += ar[ix];
                inComment = false;
            } else
            // <elm></elm> //
            if (/^<\w/.exec(ar[ix - 1]) && /^<\/\w/.exec(ar[ix]) &&
                /^<[\w:\-\.\,]+/.exec(ar[ix - 1]) == /^<\/[\w:\-\.\,]+/.exec(ar[ix])[0].replace('/', '')) {
                str += ar[ix];
                if (!inComment) deep--;
            } else
            // <elm> //
            if (ar[ix].search(/<\w/) > -1 && ar[ix].search(/<\//) == -1 && ar[ix].search(/\/>/) == -1) {
                str = !inComment ? str += this.shift[deep++] + ar[ix] : str += ar[ix];
            } else
            // <elm>...</elm> //
            if (ar[ix].search(/<\w/) > -1 && ar[ix].search(/<\//) > -1) {
                str = !inComment ? str += this.shift[deep] + ar[ix] : str += ar[ix];
            } else
            // </elm> //
            if (ar[ix].search(/<\//) > -1) {
                str = !inComment ? str += this.shift[--deep] + ar[ix] : str += ar[ix];
            } else
            // <elm/> //
            if (ar[ix].search(/\/>/) > -1) {
                str = !inComment ? str += this.shift[deep] + ar[ix] : str += ar[ix];
            } else
            // <? xml ... ?> //
            if (ar[ix].search(/<\?/) > -1) {
                str += this.shift[deep] + ar[ix];
            } else
            // xmlns //
            if (ar[ix].search(/xmlns\:/) > -1 || ar[ix].search(/xmlns\=/) > -1) {
                str += this.shift[deep] + ar[ix];
            }

            else {
                str += ar[ix];
            }
        }

        return (str[0] == '\n') ? str.slice(1) : str;
    };

    return new PrettyPrint();
}));
