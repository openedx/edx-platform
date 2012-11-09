/*
 * jQuery i18n plugin
 * @requires jQuery v1.1 or later
 *
 * Examples at: http://recurser.com/articles/2008/02/21/jquery-i18n-translation-plugin/
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 *
 * Based on 'javascript i18n that almost doesn't suck' by markos
 * http://markos.gaivo.net/blog/?p=100
 *
 * Revision: $Id$
 * Version: 1.0.0  Feb-10-2008
 */
 (function($) {
/**
 * i18n provides a mechanism for translating strings using a jscript dictionary.
 *
 */


/*
 * i18n property list
 */
$.i18n = {
	
/**
 * setDictionary()
 * Initialise the dictionary and translate nodes
 *
 * @param property_list i18n_dict : The dictionary to use for translation
 */
	setDictionary: function(i18n_dict) {
		i18n_dict = i18n_dict;
	},
	
/**
 * _()
 * The actual translation function. Looks the given string up in the 
 * dictionary and returns the translation if one exists. If a translation 
 * is not found, returns the original word
 *
 * @param string str : The string to translate 
 * @param property_list params : params for using printf() on the string
 * @return string : Translated word
 *
 */
	_: function (str, params) {
		var transl = str;
		if (i18n_dict&& i18n_dict[str]) {
			transl = i18n_dict[str];
		}
		return this.printf(transl, params);
	},
	
/**
 * toEntity()
 * Change non-ASCII characters to entity representation 
 *
 * @param string str : The string to transform
 * @return string result : Original string with non-ASCII content converted to entities
 *
 */
	toEntity: function (str) {
		var result = '';
		for (var i=0;i<str.length; i++) {
			if (str.charCodeAt(i) > 128)
				result += "&#"+str.charCodeAt(i)+";";
			else
				result += str.charAt(i);
		}
		return result;
	},
	
/**
 * stripStr()
 *
 * @param string str : The string to strip
 * @return string result : Stripped string
 *
 */
 	stripStr: function(str) {
		return str.replace(/^\s*/, "").replace(/\s*$/, "");
	},
	
/**
 * stripStrML()
 *
 * @param string str : The multi-line string to strip
 * @return string result : Stripped string
 *
 */
	stripStrML: function(str) {
		// Split because m flag doesn't exist before JS1.5 and we need to
		// strip newlines anyway
		var parts = str.split('\n');
		for (var i=0; i<parts.length; i++)
			parts[i] = stripStr(parts[i]);
	
		// Don't join with empty strings, because it "concats" words
		// And strip again
		return stripStr(parts.join(" "));
	},

/*
 * printf()
 * C-printf like function, which substitutes %s with parameters
 * given in list. %%s is used to escape %s.
 *
 * Doesn't work in IE5.0 (splice)
 *
 * @param string S : string to perform printf on.
 * @param string L : Array of arguments for printf()
 */
	printf: function(S, L) {
		if (!L) return S;

		var nS = "";
		var tS = S.split("%s");

		for(var i=0; i<L.length; i++) {
			if (tS[i].lastIndexOf('%') == tS[i].length-1 && i != L.length-1)
				tS[i] += "s"+tS.splice(i+1,1)[0];
			nS += tS[i] + L[i];
		}
		return nS + tS[tS.length-1];
	}

};


})(jQuery);
