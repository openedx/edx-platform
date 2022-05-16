(function(e, a) { for(var i in a) e[i] = a[i]; }(window, /******/ (function(modules) { // webpackBootstrap
/******/ 	// install a JSONP callback for chunk loading
/******/ 	var parentJsonpFunction = window["webpackJsonp"];
/******/ 	window["webpackJsonp"] = function webpackJsonpCallback(chunkIds, moreModules, executeModules) {
/******/ 		// add "moreModules" to the modules object,
/******/ 		// then flag all "chunkIds" as loaded and fire callback
/******/ 		var moduleId, chunkId, i = 0, resolves = [], result;
/******/ 		for(;i < chunkIds.length; i++) {
/******/ 			chunkId = chunkIds[i];
/******/ 			if(installedChunks[chunkId]) {
/******/ 				resolves.push(installedChunks[chunkId][0]);
/******/ 			}
/******/ 			installedChunks[chunkId] = 0;
/******/ 		}
/******/ 		for(moduleId in moreModules) {
/******/ 			if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
/******/ 				modules[moduleId] = moreModules[moduleId];
/******/ 			}
/******/ 		}
/******/ 		if(parentJsonpFunction) parentJsonpFunction(chunkIds, moreModules, executeModules);
/******/ 		while(resolves.length) {
/******/ 			resolves.shift()();
/******/ 		}
/******/ 		if(executeModules) {
/******/ 			for(i=0; i < executeModules.length; i++) {
/******/ 				result = __webpack_require__(__webpack_require__.s = executeModules[i]);
/******/ 			}
/******/ 		}
/******/ 		return result;
/******/ 	};
/******/
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// objects to store loaded and loading chunks
/******/ 	var installedChunks = {
/******/ 		72: 0
/******/ 	};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/ 	// This file contains only the entry chunk.
/******/ 	// The chunk loading function for additional chunks
/******/ 	__webpack_require__.e = function requireEnsure(chunkId) {
/******/ 		var installedChunkData = installedChunks[chunkId];
/******/ 		if(installedChunkData === 0) {
/******/ 			return new Promise(function(resolve) { resolve(); });
/******/ 		}
/******/
/******/ 		// a Promise means "currently loading".
/******/ 		if(installedChunkData) {
/******/ 			return installedChunkData[2];
/******/ 		}
/******/
/******/ 		// setup Promise in chunk cache
/******/ 		var promise = new Promise(function(resolve, reject) {
/******/ 			installedChunkData = installedChunks[chunkId] = [resolve, reject];
/******/ 		});
/******/ 		installedChunkData[2] = promise;
/******/
/******/ 		// start chunk loading
/******/ 		var head = document.getElementsByTagName('head')[0];
/******/ 		var script = document.createElement('script');
/******/ 		script.type = 'text/javascript';
/******/ 		script.charset = 'utf-8';
/******/ 		script.async = true;
/******/ 		script.timeout = 120000;
/******/
/******/ 		if (__webpack_require__.nc) {
/******/ 			script.setAttribute("nonce", __webpack_require__.nc);
/******/ 		}
/******/ 		script.src = __webpack_require__.p + "" + chunkId + ".js";
/******/ 		var timeout = setTimeout(onScriptComplete, 120000);
/******/ 		script.onerror = script.onload = onScriptComplete;
/******/ 		function onScriptComplete() {
/******/ 			// avoid mem leaks in IE.
/******/ 			script.onerror = script.onload = null;
/******/ 			clearTimeout(timeout);
/******/ 			var chunk = installedChunks[chunkId];
/******/ 			if(chunk !== 0) {
/******/ 				if(chunk) {
/******/ 					chunk[1](new Error('Loading chunk ' + chunkId + ' failed.'));
/******/ 				}
/******/ 				installedChunks[chunkId] = undefined;
/******/ 			}
/******/ 		};
/******/ 		head.appendChild(script);
/******/
/******/ 		return promise;
/******/ 	};
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// identity function for calling harmony imports with the correct context
/******/ 	__webpack_require__.i = function(value) { return value; };
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, {
/******/ 				configurable: false,
/******/ 				enumerable: true,
/******/ 				get: getter
/******/ 			});
/******/ 		}
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// on error function for async loading
/******/ 	__webpack_require__.oe = function(err) { console.error(err); throw err; };
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = "./node_modules/babel-polyfill/lib/index.js");
/******/ })
/************************************************************************/
/******/ ({

/***/ "./common/static/js/vendor/codemirror-compressed.js":
/***/ (function(module, exports) {

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

window.CodeMirror = function () {
  "use strict";
  var userAgent = navigator.userAgent;var platform = navigator.platform;var gecko = /gecko\/\d/i.test(userAgent);var ie_upto10 = /MSIE \d/.test(userAgent);var ie_11up = /Trident\/(?:[7-9]|\d{2,})\..*rv:(\d+)/.exec(userAgent);var edge = /Edge\/(\d+)/.exec(userAgent);var ie = ie_upto10 || ie_11up || edge;var ie_version = ie && (ie_upto10 ? document.documentMode || 6 : +(edge || ie_11up)[1]);var webkit = !edge && /WebKit\//.test(userAgent);var qtwebkit = webkit && /Qt\/\d+\.\d+/.test(userAgent);var chrome = !edge && /Chrome\//.test(userAgent);var presto = /Opera\//.test(userAgent);var safari = /Apple Computer/.test(navigator.vendor);var mac_geMountainLion = /Mac OS X 1\d\D([8-9]|\d\d)\D/.test(userAgent);var phantom = /PhantomJS/.test(userAgent);var ios = !edge && /AppleWebKit/.test(userAgent) && /Mobile\/\w+/.test(userAgent);var android = /Android/.test(userAgent);var mobile = ios || android || /webOS|BlackBerry|Opera Mini|Opera Mobi|IEMobile/i.test(userAgent);var mac = ios || /Mac/.test(platform);var chromeOS = /\bCrOS\b/.test(userAgent);var windows = /win/i.test(platform);var presto_version = presto && userAgent.match(/Version\/(\d*\.\d*)/);if (presto_version) {
    presto_version = Number(presto_version[1]);
  }if (presto_version && presto_version >= 15) {
    presto = false;webkit = true;
  }var flipCtrlCmd = mac && (qtwebkit || presto && (presto_version == null || presto_version < 12.11));var captureRightClick = gecko || ie && ie_version >= 9;function classTest(cls) {
    return new RegExp("(^|\\s)" + cls + "(?:$|\\s)\\s*");
  }var rmClass = function rmClass(node, cls) {
    var current = node.className;var match = classTest(cls).exec(current);if (match) {
      var after = current.slice(match.index + match[0].length);node.className = current.slice(0, match.index) + (after ? match[1] + after : "");
    }
  };function removeChildren(e) {
    for (var count = e.childNodes.length; count > 0; --count) {
      e.removeChild(e.firstChild);
    }return e;
  }function removeChildrenAndAdd(parent, e) {
    return removeChildren(parent).appendChild(e);
  }function elt(tag, content, className, style) {
    var e = document.createElement(tag);if (className) {
      e.className = className;
    }if (style) {
      e.style.cssText = style;
    }if (typeof content == "string") {
      e.appendChild(document.createTextNode(content));
    } else if (content) {
      for (var i = 0; i < content.length; ++i) {
        e.appendChild(content[i]);
      }
    }return e;
  }function eltP(tag, content, className, style) {
    var e = elt(tag, content, className, style);e.setAttribute("role", "presentation");return e;
  }var range;if (document.createRange) {
    range = function range(node, start, end, endNode) {
      var r = document.createRange();r.setEnd(endNode || node, end);r.setStart(node, start);return r;
    };
  } else {
    range = function range(node, start, end) {
      var r = document.body.createTextRange();try {
        r.moveToElementText(node.parentNode);
      } catch (e) {
        return r;
      }r.collapse(true);r.moveEnd("character", end);r.moveStart("character", start);return r;
    };
  }function contains(parent, child) {
    if (child.nodeType == 3) {
      child = child.parentNode;
    }if (parent.contains) {
      return parent.contains(child);
    }do {
      if (child.nodeType == 11) {
        child = child.host;
      }if (child == parent) {
        return true;
      }
    } while (child = child.parentNode);
  }function activeElt() {
    var activeElement;try {
      activeElement = document.activeElement;
    } catch (e) {
      activeElement = document.body || null;
    }while (activeElement && activeElement.shadowRoot && activeElement.shadowRoot.activeElement) {
      activeElement = activeElement.shadowRoot.activeElement;
    }return activeElement;
  }function addClass(node, cls) {
    var current = node.className;if (!classTest(cls).test(current)) {
      node.className += (current ? " " : "") + cls;
    }
  }function joinClasses(a, b) {
    var as = a.split(" ");for (var i = 0; i < as.length; i++) {
      if (as[i] && !classTest(as[i]).test(b)) {
        b += " " + as[i];
      }
    }return b;
  }var selectInput = function selectInput(node) {
    node.select();
  };if (ios) {
    selectInput = function selectInput(node) {
      node.selectionStart = 0;node.selectionEnd = node.value.length;
    };
  } else if (ie) {
    selectInput = function selectInput(node) {
      try {
        node.select();
      } catch (_e) {}
    };
  }function bind(f) {
    var args = Array.prototype.slice.call(arguments, 1);return function () {
      return f.apply(null, args);
    };
  }function copyObj(obj, target, overwrite) {
    if (!target) {
      target = {};
    }for (var prop in obj) {
      if (obj.hasOwnProperty(prop) && (overwrite !== false || !target.hasOwnProperty(prop))) {
        target[prop] = obj[prop];
      }
    }return target;
  }function countColumn(string, end, tabSize, startIndex, startValue) {
    if (end == null) {
      end = string.search(/[^\s\u00a0]/);if (end == -1) {
        end = string.length;
      }
    }for (var i = startIndex || 0, n = startValue || 0;;) {
      var nextTab = string.indexOf("\t", i);if (nextTab < 0 || nextTab >= end) {
        return n + (end - i);
      }n += nextTab - i;n += tabSize - n % tabSize;i = nextTab + 1;
    }
  }var Delayed = function Delayed() {
    this.id = null;this.f = null;this.time = 0;this.handler = bind(this.onTimeout, this);
  };Delayed.prototype.onTimeout = function (self) {
    self.id = 0;if (self.time <= +new Date()) {
      self.f();
    } else {
      setTimeout(self.handler, self.time - +new Date());
    }
  };Delayed.prototype.set = function (ms, f) {
    this.f = f;var time = +new Date() + ms;if (!this.id || time < this.time) {
      clearTimeout(this.id);this.id = setTimeout(this.handler, ms);this.time = time;
    }
  };function indexOf(array, elt) {
    for (var i = 0; i < array.length; ++i) {
      if (array[i] == elt) {
        return i;
      }
    }return -1;
  }var scrollerGap = 30;var Pass = { toString: function toString() {
      return "CodeMirror.Pass";
    } };var sel_dontScroll = { scroll: false },
      sel_mouse = { origin: "*mouse" },
      sel_move = { origin: "+move" };function findColumn(string, goal, tabSize) {
    for (var pos = 0, col = 0;;) {
      var nextTab = string.indexOf("\t", pos);if (nextTab == -1) {
        nextTab = string.length;
      }var skipped = nextTab - pos;if (nextTab == string.length || col + skipped >= goal) {
        return pos + Math.min(skipped, goal - col);
      }col += nextTab - pos;col += tabSize - col % tabSize;pos = nextTab + 1;if (col >= goal) {
        return pos;
      }
    }
  }var spaceStrs = [""];function spaceStr(n) {
    while (spaceStrs.length <= n) {
      spaceStrs.push(lst(spaceStrs) + " ");
    }return spaceStrs[n];
  }function lst(arr) {
    return arr[arr.length - 1];
  }function map(array, f) {
    var out = [];for (var i = 0; i < array.length; i++) {
      out[i] = f(array[i], i);
    }return out;
  }function insertSorted(array, value, score) {
    var pos = 0,
        priority = score(value);while (pos < array.length && score(array[pos]) <= priority) {
      pos++;
    }array.splice(pos, 0, value);
  }function nothing() {}function createObj(base, props) {
    var inst;if (Object.create) {
      inst = Object.create(base);
    } else {
      nothing.prototype = base;inst = new nothing();
    }if (props) {
      copyObj(props, inst);
    }return inst;
  }var nonASCIISingleCaseWordChar = /[\u00df\u0587\u0590-\u05f4\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\u3400-\u4db5\u4e00-\u9fcc\uac00-\ud7af]/;function isWordCharBasic(ch) {
    return (/\w/.test(ch) || ch > "" && (ch.toUpperCase() != ch.toLowerCase() || nonASCIISingleCaseWordChar.test(ch))
    );
  }function isWordChar(ch, helper) {
    if (!helper) {
      return isWordCharBasic(ch);
    }if (helper.source.indexOf("\\w") > -1 && isWordCharBasic(ch)) {
      return true;
    }return helper.test(ch);
  }function isEmpty(obj) {
    for (var n in obj) {
      if (obj.hasOwnProperty(n) && obj[n]) {
        return false;
      }
    }return true;
  }var extendingChars = /[\u0300-\u036f\u0483-\u0489\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u0610-\u061a\u064b-\u065e\u0670\u06d6-\u06dc\u06de-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0711\u0730-\u074a\u07a6-\u07b0\u07eb-\u07f3\u0816-\u0819\u081b-\u0823\u0825-\u0827\u0829-\u082d\u0900-\u0902\u093c\u0941-\u0948\u094d\u0951-\u0955\u0962\u0963\u0981\u09bc\u09be\u09c1-\u09c4\u09cd\u09d7\u09e2\u09e3\u0a01\u0a02\u0a3c\u0a41\u0a42\u0a47\u0a48\u0a4b-\u0a4d\u0a51\u0a70\u0a71\u0a75\u0a81\u0a82\u0abc\u0ac1-\u0ac5\u0ac7\u0ac8\u0acd\u0ae2\u0ae3\u0b01\u0b3c\u0b3e\u0b3f\u0b41-\u0b44\u0b4d\u0b56\u0b57\u0b62\u0b63\u0b82\u0bbe\u0bc0\u0bcd\u0bd7\u0c3e-\u0c40\u0c46-\u0c48\u0c4a-\u0c4d\u0c55\u0c56\u0c62\u0c63\u0cbc\u0cbf\u0cc2\u0cc6\u0ccc\u0ccd\u0cd5\u0cd6\u0ce2\u0ce3\u0d3e\u0d41-\u0d44\u0d4d\u0d57\u0d62\u0d63\u0dca\u0dcf\u0dd2-\u0dd4\u0dd6\u0ddf\u0e31\u0e34-\u0e3a\u0e47-\u0e4e\u0eb1\u0eb4-\u0eb9\u0ebb\u0ebc\u0ec8-\u0ecd\u0f18\u0f19\u0f35\u0f37\u0f39\u0f71-\u0f7e\u0f80-\u0f84\u0f86\u0f87\u0f90-\u0f97\u0f99-\u0fbc\u0fc6\u102d-\u1030\u1032-\u1037\u1039\u103a\u103d\u103e\u1058\u1059\u105e-\u1060\u1071-\u1074\u1082\u1085\u1086\u108d\u109d\u135f\u1712-\u1714\u1732-\u1734\u1752\u1753\u1772\u1773\u17b7-\u17bd\u17c6\u17c9-\u17d3\u17dd\u180b-\u180d\u18a9\u1920-\u1922\u1927\u1928\u1932\u1939-\u193b\u1a17\u1a18\u1a56\u1a58-\u1a5e\u1a60\u1a62\u1a65-\u1a6c\u1a73-\u1a7c\u1a7f\u1b00-\u1b03\u1b34\u1b36-\u1b3a\u1b3c\u1b42\u1b6b-\u1b73\u1b80\u1b81\u1ba2-\u1ba5\u1ba8\u1ba9\u1c2c-\u1c33\u1c36\u1c37\u1cd0-\u1cd2\u1cd4-\u1ce0\u1ce2-\u1ce8\u1ced\u1dc0-\u1de6\u1dfd-\u1dff\u200c\u200d\u20d0-\u20f0\u2cef-\u2cf1\u2de0-\u2dff\u302a-\u302f\u3099\u309a\ua66f-\ua672\ua67c\ua67d\ua6f0\ua6f1\ua802\ua806\ua80b\ua825\ua826\ua8c4\ua8e0-\ua8f1\ua926-\ua92d\ua947-\ua951\ua980-\ua982\ua9b3\ua9b6-\ua9b9\ua9bc\uaa29-\uaa2e\uaa31\uaa32\uaa35\uaa36\uaa43\uaa4c\uaab0\uaab2-\uaab4\uaab7\uaab8\uaabe\uaabf\uaac1\uabe5\uabe8\uabed\udc00-\udfff\ufb1e\ufe00-\ufe0f\ufe20-\ufe26\uff9e\uff9f]/;function isExtendingChar(ch) {
    return ch.charCodeAt(0) >= 768 && extendingChars.test(ch);
  }function skipExtendingChars(str, pos, dir) {
    while ((dir < 0 ? pos > 0 : pos < str.length) && isExtendingChar(str.charAt(pos))) {
      pos += dir;
    }return pos;
  }function findFirst(pred, from, to) {
    var dir = from > to ? -1 : 1;for (;;) {
      if (from == to) {
        return from;
      }var midF = (from + to) / 2,
          mid = dir < 0 ? Math.ceil(midF) : Math.floor(midF);if (mid == from) {
        return pred(mid) ? from : to;
      }if (pred(mid)) {
        to = mid;
      } else {
        from = mid + dir;
      }
    }
  }function iterateBidiSections(order, from, to, f) {
    if (!order) {
      return f(from, to, "ltr", 0);
    }var found = false;for (var i = 0; i < order.length; ++i) {
      var part = order[i];if (part.from < to && part.to > from || from == to && part.to == from) {
        f(Math.max(part.from, from), Math.min(part.to, to), part.level == 1 ? "rtl" : "ltr", i);found = true;
      }
    }if (!found) {
      f(from, to, "ltr");
    }
  }var bidiOther = null;function getBidiPartAt(order, ch, sticky) {
    var found;bidiOther = null;for (var i = 0; i < order.length; ++i) {
      var cur = order[i];if (cur.from < ch && cur.to > ch) {
        return i;
      }if (cur.to == ch) {
        if (cur.from != cur.to && sticky == "before") {
          found = i;
        } else {
          bidiOther = i;
        }
      }if (cur.from == ch) {
        if (cur.from != cur.to && sticky != "before") {
          found = i;
        } else {
          bidiOther = i;
        }
      }
    }return found != null ? found : bidiOther;
  }var bidiOrdering = function () {
    var lowTypes = "bbbbbbbbbtstwsbbbbbbbbbbbbbbssstwNN%%%NNNNNN,N,N1111111111NNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNbbbbbbsbbbbbbbbbbbbbbbbbbbbbbbbbb,N%%%%NNNNLNNNNN%%11NLNNN1LNNNNNLLLLLLLLLLLLLLLLLLLLLLLNLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLN";var arabicTypes = "nnnnnnNNr%%r,rNNmmmmmmmmmmmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmmmmmmmmmmmmmmmnnnnnnnnnn%nnrrrmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmnNmmmmmmrrmmNmmmmrr1111111111";function charType(code) {
      if (code <= 247) {
        return lowTypes.charAt(code);
      } else if (1424 <= code && code <= 1524) {
        return "R";
      } else if (1536 <= code && code <= 1785) {
        return arabicTypes.charAt(code - 1536);
      } else if (1774 <= code && code <= 2220) {
        return "r";
      } else if (8192 <= code && code <= 8203) {
        return "w";
      } else if (code == 8204) {
        return "b";
      } else {
        return "L";
      }
    }var bidiRE = /[\u0590-\u05f4\u0600-\u06ff\u0700-\u08ac]/;var isNeutral = /[stwN]/,
        isStrong = /[LRr]/,
        countsAsLeft = /[Lb1n]/,
        countsAsNum = /[1n]/;function BidiSpan(level, from, to) {
      this.level = level;this.from = from;this.to = to;
    }return function (str, direction) {
      var outerType = direction == "ltr" ? "L" : "R";if (str.length == 0 || direction == "ltr" && !bidiRE.test(str)) {
        return false;
      }var len = str.length,
          types = [];for (var i = 0; i < len; ++i) {
        types.push(charType(str.charCodeAt(i)));
      }for (var i$1 = 0, prev = outerType; i$1 < len; ++i$1) {
        var type = types[i$1];if (type == "m") {
          types[i$1] = prev;
        } else {
          prev = type;
        }
      }for (var i$2 = 0, cur = outerType; i$2 < len; ++i$2) {
        var type$1 = types[i$2];if (type$1 == "1" && cur == "r") {
          types[i$2] = "n";
        } else if (isStrong.test(type$1)) {
          cur = type$1;if (type$1 == "r") {
            types[i$2] = "R";
          }
        }
      }for (var i$3 = 1, prev$1 = types[0]; i$3 < len - 1; ++i$3) {
        var type$2 = types[i$3];if (type$2 == "+" && prev$1 == "1" && types[i$3 + 1] == "1") {
          types[i$3] = "1";
        } else if (type$2 == "," && prev$1 == types[i$3 + 1] && (prev$1 == "1" || prev$1 == "n")) {
          types[i$3] = prev$1;
        }prev$1 = type$2;
      }for (var i$4 = 0; i$4 < len; ++i$4) {
        var type$3 = types[i$4];if (type$3 == ",") {
          types[i$4] = "N";
        } else if (type$3 == "%") {
          var end = void 0;for (end = i$4 + 1; end < len && types[end] == "%"; ++end) {}var replace = i$4 && types[i$4 - 1] == "!" || end < len && types[end] == "1" ? "1" : "N";for (var j = i$4; j < end; ++j) {
            types[j] = replace;
          }i$4 = end - 1;
        }
      }for (var i$5 = 0, cur$1 = outerType; i$5 < len; ++i$5) {
        var type$4 = types[i$5];if (cur$1 == "L" && type$4 == "1") {
          types[i$5] = "L";
        } else if (isStrong.test(type$4)) {
          cur$1 = type$4;
        }
      }for (var i$6 = 0; i$6 < len; ++i$6) {
        if (isNeutral.test(types[i$6])) {
          var end$1 = void 0;for (end$1 = i$6 + 1; end$1 < len && isNeutral.test(types[end$1]); ++end$1) {}var before = (i$6 ? types[i$6 - 1] : outerType) == "L";var after = (end$1 < len ? types[end$1] : outerType) == "L";var replace$1 = before == after ? before ? "L" : "R" : outerType;for (var j$1 = i$6; j$1 < end$1; ++j$1) {
            types[j$1] = replace$1;
          }i$6 = end$1 - 1;
        }
      }var order = [],
          m;for (var i$7 = 0; i$7 < len;) {
        if (countsAsLeft.test(types[i$7])) {
          var start = i$7;for (++i$7; i$7 < len && countsAsLeft.test(types[i$7]); ++i$7) {}order.push(new BidiSpan(0, start, i$7));
        } else {
          var pos = i$7,
              at = order.length;for (++i$7; i$7 < len && types[i$7] != "L"; ++i$7) {}for (var j$2 = pos; j$2 < i$7;) {
            if (countsAsNum.test(types[j$2])) {
              if (pos < j$2) {
                order.splice(at, 0, new BidiSpan(1, pos, j$2));
              }var nstart = j$2;for (++j$2; j$2 < i$7 && countsAsNum.test(types[j$2]); ++j$2) {}order.splice(at, 0, new BidiSpan(2, nstart, j$2));pos = j$2;
            } else {
              ++j$2;
            }
          }if (pos < i$7) {
            order.splice(at, 0, new BidiSpan(1, pos, i$7));
          }
        }
      }if (direction == "ltr") {
        if (order[0].level == 1 && (m = str.match(/^\s+/))) {
          order[0].from = m[0].length;order.unshift(new BidiSpan(0, 0, m[0].length));
        }if (lst(order).level == 1 && (m = str.match(/\s+$/))) {
          lst(order).to -= m[0].length;order.push(new BidiSpan(0, len - m[0].length, len));
        }
      }return direction == "rtl" ? order.reverse() : order;
    };
  }();function getOrder(line, direction) {
    var order = line.order;if (order == null) {
      order = line.order = bidiOrdering(line.text, direction);
    }return order;
  }var noHandlers = [];var on = function on(emitter, type, f) {
    if (emitter.addEventListener) {
      emitter.addEventListener(type, f, false);
    } else if (emitter.attachEvent) {
      emitter.attachEvent("on" + type, f);
    } else {
      var map$$1 = emitter._handlers || (emitter._handlers = {});map$$1[type] = (map$$1[type] || noHandlers).concat(f);
    }
  };function getHandlers(emitter, type) {
    return emitter._handlers && emitter._handlers[type] || noHandlers;
  }function off(emitter, type, f) {
    if (emitter.removeEventListener) {
      emitter.removeEventListener(type, f, false);
    } else if (emitter.detachEvent) {
      emitter.detachEvent("on" + type, f);
    } else {
      var map$$1 = emitter._handlers,
          arr = map$$1 && map$$1[type];if (arr) {
        var index = indexOf(arr, f);if (index > -1) {
          map$$1[type] = arr.slice(0, index).concat(arr.slice(index + 1));
        }
      }
    }
  }function signal(emitter, type) {
    var handlers = getHandlers(emitter, type);if (!handlers.length) {
      return;
    }var args = Array.prototype.slice.call(arguments, 2);for (var i = 0; i < handlers.length; ++i) {
      handlers[i].apply(null, args);
    }
  }function signalDOMEvent(cm, e, override) {
    if (typeof e == "string") {
      e = { type: e, preventDefault: function preventDefault() {
          this.defaultPrevented = true;
        } };
    }signal(cm, override || e.type, cm, e);return e_defaultPrevented(e) || e.codemirrorIgnore;
  }function signalCursorActivity(cm) {
    var arr = cm._handlers && cm._handlers.cursorActivity;if (!arr) {
      return;
    }var set = cm.curOp.cursorActivityHandlers || (cm.curOp.cursorActivityHandlers = []);for (var i = 0; i < arr.length; ++i) {
      if (indexOf(set, arr[i]) == -1) {
        set.push(arr[i]);
      }
    }
  }function hasHandler(emitter, type) {
    return getHandlers(emitter, type).length > 0;
  }function eventMixin(ctor) {
    ctor.prototype.on = function (type, f) {
      on(this, type, f);
    };ctor.prototype.off = function (type, f) {
      off(this, type, f);
    };
  }function e_preventDefault(e) {
    if (e.preventDefault) {
      e.preventDefault();
    } else {
      e.returnValue = false;
    }
  }function e_stopPropagation(e) {
    if (e.stopPropagation) {
      e.stopPropagation();
    } else {
      e.cancelBubble = true;
    }
  }function e_defaultPrevented(e) {
    return e.defaultPrevented != null ? e.defaultPrevented : e.returnValue == false;
  }function e_stop(e) {
    e_preventDefault(e);e_stopPropagation(e);
  }function e_target(e) {
    return e.target || e.srcElement;
  }function e_button(e) {
    var b = e.which;if (b == null) {
      if (e.button & 1) {
        b = 1;
      } else if (e.button & 2) {
        b = 3;
      } else if (e.button & 4) {
        b = 2;
      }
    }if (mac && e.ctrlKey && b == 1) {
      b = 3;
    }return b;
  }var dragAndDrop = function () {
    if (ie && ie_version < 9) {
      return false;
    }var div = elt("div");return "draggable" in div || "dragDrop" in div;
  }();var zwspSupported;function zeroWidthElement(measure) {
    if (zwspSupported == null) {
      var test = elt("span", "​");removeChildrenAndAdd(measure, elt("span", [test, document.createTextNode("x")]));if (measure.firstChild.offsetHeight != 0) {
        zwspSupported = test.offsetWidth <= 1 && test.offsetHeight > 2 && !(ie && ie_version < 8);
      }
    }var node = zwspSupported ? elt("span", "​") : elt("span", " ", null, "display: inline-block; width: 1px; margin-right: -1px");node.setAttribute("cm-text", "");return node;
  }var badBidiRects;function hasBadBidiRects(measure) {
    if (badBidiRects != null) {
      return badBidiRects;
    }var txt = removeChildrenAndAdd(measure, document.createTextNode("AخA"));var r0 = range(txt, 0, 1).getBoundingClientRect();var r1 = range(txt, 1, 2).getBoundingClientRect();removeChildren(measure);if (!r0 || r0.left == r0.right) {
      return false;
    }return badBidiRects = r1.right - r0.right < 3;
  }var splitLinesAuto = "\n\nb".split(/\n/).length != 3 ? function (string) {
    var pos = 0,
        result = [],
        l = string.length;while (pos <= l) {
      var nl = string.indexOf("\n", pos);if (nl == -1) {
        nl = string.length;
      }var line = string.slice(pos, string.charAt(nl - 1) == "\r" ? nl - 1 : nl);var rt = line.indexOf("\r");if (rt != -1) {
        result.push(line.slice(0, rt));pos += rt + 1;
      } else {
        result.push(line);pos = nl + 1;
      }
    }return result;
  } : function (string) {
    return string.split(/\r\n?|\n/);
  };var hasSelection = window.getSelection ? function (te) {
    try {
      return te.selectionStart != te.selectionEnd;
    } catch (e) {
      return false;
    }
  } : function (te) {
    var range$$1;try {
      range$$1 = te.ownerDocument.selection.createRange();
    } catch (e) {}if (!range$$1 || range$$1.parentElement() != te) {
      return false;
    }return range$$1.compareEndPoints("StartToEnd", range$$1) != 0;
  };var hasCopyEvent = function () {
    var e = elt("div");if ("oncopy" in e) {
      return true;
    }e.setAttribute("oncopy", "return;");return typeof e.oncopy == "function";
  }();var badZoomedRects = null;function hasBadZoomedRects(measure) {
    if (badZoomedRects != null) {
      return badZoomedRects;
    }var node = removeChildrenAndAdd(measure, elt("span", "x"));var normal = node.getBoundingClientRect();var fromRange = range(node, 0, 1).getBoundingClientRect();return badZoomedRects = Math.abs(normal.left - fromRange.left) > 1;
  }var modes = {},
      mimeModes = {};function defineMode(name, mode) {
    if (arguments.length > 2) {
      mode.dependencies = Array.prototype.slice.call(arguments, 2);
    }modes[name] = mode;
  }function defineMIME(mime, spec) {
    mimeModes[mime] = spec;
  }function resolveMode(spec) {
    if (typeof spec == "string" && mimeModes.hasOwnProperty(spec)) {
      spec = mimeModes[spec];
    } else if (spec && typeof spec.name == "string" && mimeModes.hasOwnProperty(spec.name)) {
      var found = mimeModes[spec.name];if (typeof found == "string") {
        found = { name: found };
      }spec = createObj(found, spec);spec.name = found.name;
    } else if (typeof spec == "string" && /^[\w\-]+\/[\w\-]+\+xml$/.test(spec)) {
      return resolveMode("application/xml");
    } else if (typeof spec == "string" && /^[\w\-]+\/[\w\-]+\+json$/.test(spec)) {
      return resolveMode("application/json");
    }if (typeof spec == "string") {
      return { name: spec };
    } else {
      return spec || { name: "null" };
    }
  }function getMode(options, spec) {
    spec = resolveMode(spec);var mfactory = modes[spec.name];if (!mfactory) {
      return getMode(options, "text/plain");
    }var modeObj = mfactory(options, spec);if (modeExtensions.hasOwnProperty(spec.name)) {
      var exts = modeExtensions[spec.name];for (var prop in exts) {
        if (!exts.hasOwnProperty(prop)) {
          continue;
        }if (modeObj.hasOwnProperty(prop)) {
          modeObj["_" + prop] = modeObj[prop];
        }modeObj[prop] = exts[prop];
      }
    }modeObj.name = spec.name;if (spec.helperType) {
      modeObj.helperType = spec.helperType;
    }if (spec.modeProps) {
      for (var prop$1 in spec.modeProps) {
        modeObj[prop$1] = spec.modeProps[prop$1];
      }
    }return modeObj;
  }var modeExtensions = {};function extendMode(mode, properties) {
    var exts = modeExtensions.hasOwnProperty(mode) ? modeExtensions[mode] : modeExtensions[mode] = {};copyObj(properties, exts);
  }function copyState(mode, state) {
    if (state === true) {
      return state;
    }if (mode.copyState) {
      return mode.copyState(state);
    }var nstate = {};for (var n in state) {
      var val = state[n];if (val instanceof Array) {
        val = val.concat([]);
      }nstate[n] = val;
    }return nstate;
  }function innerMode(mode, state) {
    var info;while (mode.innerMode) {
      info = mode.innerMode(state);if (!info || info.mode == mode) {
        break;
      }state = info.state;mode = info.mode;
    }return info || { mode: mode, state: state };
  }function startState(mode, a1, a2) {
    return mode.startState ? mode.startState(a1, a2) : true;
  }var StringStream = function StringStream(string, tabSize, lineOracle) {
    this.pos = this.start = 0;this.string = string;this.tabSize = tabSize || 8;this.lastColumnPos = this.lastColumnValue = 0;this.lineStart = 0;this.lineOracle = lineOracle;
  };StringStream.prototype.eol = function () {
    return this.pos >= this.string.length;
  };StringStream.prototype.sol = function () {
    return this.pos == this.lineStart;
  };StringStream.prototype.peek = function () {
    return this.string.charAt(this.pos) || undefined;
  };StringStream.prototype.next = function () {
    if (this.pos < this.string.length) {
      return this.string.charAt(this.pos++);
    }
  };StringStream.prototype.eat = function (match) {
    var ch = this.string.charAt(this.pos);var ok;if (typeof match == "string") {
      ok = ch == match;
    } else {
      ok = ch && (match.test ? match.test(ch) : match(ch));
    }if (ok) {
      ++this.pos;return ch;
    }
  };StringStream.prototype.eatWhile = function (match) {
    var start = this.pos;while (this.eat(match)) {}return this.pos > start;
  };StringStream.prototype.eatSpace = function () {
    var start = this.pos;while (/[\s\u00a0]/.test(this.string.charAt(this.pos))) {
      ++this.pos;
    }return this.pos > start;
  };StringStream.prototype.skipToEnd = function () {
    this.pos = this.string.length;
  };StringStream.prototype.skipTo = function (ch) {
    var found = this.string.indexOf(ch, this.pos);if (found > -1) {
      this.pos = found;return true;
    }
  };StringStream.prototype.backUp = function (n) {
    this.pos -= n;
  };StringStream.prototype.column = function () {
    if (this.lastColumnPos < this.start) {
      this.lastColumnValue = countColumn(this.string, this.start, this.tabSize, this.lastColumnPos, this.lastColumnValue);this.lastColumnPos = this.start;
    }return this.lastColumnValue - (this.lineStart ? countColumn(this.string, this.lineStart, this.tabSize) : 0);
  };StringStream.prototype.indentation = function () {
    return countColumn(this.string, null, this.tabSize) - (this.lineStart ? countColumn(this.string, this.lineStart, this.tabSize) : 0);
  };StringStream.prototype.match = function (pattern, consume, caseInsensitive) {
    if (typeof pattern == "string") {
      var cased = function cased(str) {
        return caseInsensitive ? str.toLowerCase() : str;
      };var substr = this.string.substr(this.pos, pattern.length);if (cased(substr) == cased(pattern)) {
        if (consume !== false) {
          this.pos += pattern.length;
        }return true;
      }
    } else {
      var match = this.string.slice(this.pos).match(pattern);if (match && match.index > 0) {
        return null;
      }if (match && consume !== false) {
        this.pos += match[0].length;
      }return match;
    }
  };StringStream.prototype.current = function () {
    return this.string.slice(this.start, this.pos);
  };StringStream.prototype.hideFirstChars = function (n, inner) {
    this.lineStart += n;try {
      return inner();
    } finally {
      this.lineStart -= n;
    }
  };StringStream.prototype.lookAhead = function (n) {
    var oracle = this.lineOracle;return oracle && oracle.lookAhead(n);
  };StringStream.prototype.baseToken = function () {
    var oracle = this.lineOracle;return oracle && oracle.baseToken(this.pos);
  };function getLine(doc, n) {
    n -= doc.first;if (n < 0 || n >= doc.size) {
      throw new Error("There is no line " + (n + doc.first) + " in the document.");
    }var chunk = doc;while (!chunk.lines) {
      for (var i = 0;; ++i) {
        var child = chunk.children[i],
            sz = child.chunkSize();if (n < sz) {
          chunk = child;break;
        }n -= sz;
      }
    }return chunk.lines[n];
  }function getBetween(doc, start, end) {
    var out = [],
        n = start.line;doc.iter(start.line, end.line + 1, function (line) {
      var text = line.text;if (n == end.line) {
        text = text.slice(0, end.ch);
      }if (n == start.line) {
        text = text.slice(start.ch);
      }out.push(text);++n;
    });return out;
  }function getLines(doc, from, to) {
    var out = [];doc.iter(from, to, function (line) {
      out.push(line.text);
    });return out;
  }function updateLineHeight(line, height) {
    var diff = height - line.height;if (diff) {
      for (var n = line; n; n = n.parent) {
        n.height += diff;
      }
    }
  }function lineNo(line) {
    if (line.parent == null) {
      return null;
    }var cur = line.parent,
        no = indexOf(cur.lines, line);for (var chunk = cur.parent; chunk; cur = chunk, chunk = chunk.parent) {
      for (var i = 0;; ++i) {
        if (chunk.children[i] == cur) {
          break;
        }no += chunk.children[i].chunkSize();
      }
    }return no + cur.first;
  }function _lineAtHeight(chunk, h) {
    var n = chunk.first;outer: do {
      for (var i$1 = 0; i$1 < chunk.children.length; ++i$1) {
        var child = chunk.children[i$1],
            ch = child.height;if (h < ch) {
          chunk = child;continue outer;
        }h -= ch;n += child.chunkSize();
      }return n;
    } while (!chunk.lines);var i = 0;for (; i < chunk.lines.length; ++i) {
      var line = chunk.lines[i],
          lh = line.height;if (h < lh) {
        break;
      }h -= lh;
    }return n + i;
  }function isLine(doc, l) {
    return l >= doc.first && l < doc.first + doc.size;
  }function lineNumberFor(options, i) {
    return String(options.lineNumberFormatter(i + options.firstLineNumber));
  }function Pos(line, ch, sticky) {
    if (sticky === void 0) sticky = null;if (!(this instanceof Pos)) {
      return new Pos(line, ch, sticky);
    }this.line = line;this.ch = ch;this.sticky = sticky;
  }function cmp(a, b) {
    return a.line - b.line || a.ch - b.ch;
  }function equalCursorPos(a, b) {
    return a.sticky == b.sticky && cmp(a, b) == 0;
  }function copyPos(x) {
    return Pos(x.line, x.ch);
  }function maxPos(a, b) {
    return cmp(a, b) < 0 ? b : a;
  }function minPos(a, b) {
    return cmp(a, b) < 0 ? a : b;
  }function clipLine(doc, n) {
    return Math.max(doc.first, Math.min(n, doc.first + doc.size - 1));
  }function _clipPos(doc, pos) {
    if (pos.line < doc.first) {
      return Pos(doc.first, 0);
    }var last = doc.first + doc.size - 1;if (pos.line > last) {
      return Pos(last, getLine(doc, last).text.length);
    }return clipToLen(pos, getLine(doc, pos.line).text.length);
  }function clipToLen(pos, linelen) {
    var ch = pos.ch;if (ch == null || ch > linelen) {
      return Pos(pos.line, linelen);
    } else if (ch < 0) {
      return Pos(pos.line, 0);
    } else {
      return pos;
    }
  }function clipPosArray(doc, array) {
    var out = [];for (var i = 0; i < array.length; i++) {
      out[i] = _clipPos(doc, array[i]);
    }return out;
  }var SavedContext = function SavedContext(state, lookAhead) {
    this.state = state;this.lookAhead = lookAhead;
  };var Context = function Context(doc, state, line, lookAhead) {
    this.state = state;this.doc = doc;this.line = line;this.maxLookAhead = lookAhead || 0;this.baseTokens = null;this.baseTokenPos = 1;
  };Context.prototype.lookAhead = function (n) {
    var line = this.doc.getLine(this.line + n);if (line != null && n > this.maxLookAhead) {
      this.maxLookAhead = n;
    }return line;
  };Context.prototype.baseToken = function (n) {
    if (!this.baseTokens) {
      return null;
    }while (this.baseTokens[this.baseTokenPos] <= n) {
      this.baseTokenPos += 2;
    }var type = this.baseTokens[this.baseTokenPos + 1];return { type: type && type.replace(/( |^)overlay .*/, ""), size: this.baseTokens[this.baseTokenPos] - n };
  };Context.prototype.nextLine = function () {
    this.line++;if (this.maxLookAhead > 0) {
      this.maxLookAhead--;
    }
  };Context.fromSaved = function (doc, saved, line) {
    if (saved instanceof SavedContext) {
      return new Context(doc, copyState(doc.mode, saved.state), line, saved.lookAhead);
    } else {
      return new Context(doc, copyState(doc.mode, saved), line);
    }
  };Context.prototype.save = function (copy) {
    var state = copy !== false ? copyState(this.doc.mode, this.state) : this.state;return this.maxLookAhead > 0 ? new SavedContext(state, this.maxLookAhead) : state;
  };function highlightLine(cm, line, context, forceToEnd) {
    var st = [cm.state.modeGen],
        lineClasses = {};runMode(cm, line.text, cm.doc.mode, context, function (end, style) {
      return st.push(end, style);
    }, lineClasses, forceToEnd);var state = context.state;var loop = function loop(o) {
      context.baseTokens = st;var overlay = cm.state.overlays[o],
          i = 1,
          at = 0;context.state = true;runMode(cm, line.text, overlay.mode, context, function (end, style) {
        var start = i;while (at < end) {
          var i_end = st[i];if (i_end > end) {
            st.splice(i, 1, end, st[i + 1], i_end);
          }i += 2;at = Math.min(end, i_end);
        }if (!style) {
          return;
        }if (overlay.opaque) {
          st.splice(start, i - start, end, "overlay " + style);i = start + 2;
        } else {
          for (; start < i; start += 2) {
            var cur = st[start + 1];st[start + 1] = (cur ? cur + " " : "") + "overlay " + style;
          }
        }
      }, lineClasses);context.state = state;context.baseTokens = null;context.baseTokenPos = 1;
    };for (var o = 0; o < cm.state.overlays.length; ++o) {
      loop(o);
    }return { styles: st, classes: lineClasses.bgClass || lineClasses.textClass ? lineClasses : null };
  }function getLineStyles(cm, line, updateFrontier) {
    if (!line.styles || line.styles[0] != cm.state.modeGen) {
      var context = getContextBefore(cm, lineNo(line));var resetState = line.text.length > cm.options.maxHighlightLength && copyState(cm.doc.mode, context.state);var result = highlightLine(cm, line, context);if (resetState) {
        context.state = resetState;
      }line.stateAfter = context.save(!resetState);line.styles = result.styles;if (result.classes) {
        line.styleClasses = result.classes;
      } else if (line.styleClasses) {
        line.styleClasses = null;
      }if (updateFrontier === cm.doc.highlightFrontier) {
        cm.doc.modeFrontier = Math.max(cm.doc.modeFrontier, ++cm.doc.highlightFrontier);
      }
    }return line.styles;
  }function getContextBefore(cm, n, precise) {
    var doc = cm.doc,
        display = cm.display;if (!doc.mode.startState) {
      return new Context(doc, true, n);
    }var start = findStartLine(cm, n, precise);var saved = start > doc.first && getLine(doc, start - 1).stateAfter;var context = saved ? Context.fromSaved(doc, saved, start) : new Context(doc, startState(doc.mode), start);doc.iter(start, n, function (line) {
      processLine(cm, line.text, context);var pos = context.line;line.stateAfter = pos == n - 1 || pos % 5 == 0 || pos >= display.viewFrom && pos < display.viewTo ? context.save() : null;context.nextLine();
    });if (precise) {
      doc.modeFrontier = context.line;
    }return context;
  }function processLine(cm, text, context, startAt) {
    var mode = cm.doc.mode;var stream = new StringStream(text, cm.options.tabSize, context);stream.start = stream.pos = startAt || 0;if (text == "") {
      callBlankLine(mode, context.state);
    }while (!stream.eol()) {
      readToken(mode, stream, context.state);stream.start = stream.pos;
    }
  }function callBlankLine(mode, state) {
    if (mode.blankLine) {
      return mode.blankLine(state);
    }if (!mode.innerMode) {
      return;
    }var inner = innerMode(mode, state);if (inner.mode.blankLine) {
      return inner.mode.blankLine(inner.state);
    }
  }function readToken(mode, stream, state, inner) {
    for (var i = 0; i < 10; i++) {
      if (inner) {
        inner[0] = innerMode(mode, state).mode;
      }var style = mode.token(stream, state);if (stream.pos > stream.start) {
        return style;
      }
    }throw new Error("Mode " + mode.name + " failed to advance stream.");
  }var Token = function Token(stream, type, state) {
    this.start = stream.start;this.end = stream.pos;this.string = stream.current();this.type = type || null;this.state = state;
  };function takeToken(cm, pos, precise, asArray) {
    var doc = cm.doc,
        mode = doc.mode,
        style;pos = _clipPos(doc, pos);var line = getLine(doc, pos.line),
        context = getContextBefore(cm, pos.line, precise);var stream = new StringStream(line.text, cm.options.tabSize, context),
        tokens;if (asArray) {
      tokens = [];
    }while ((asArray || stream.pos < pos.ch) && !stream.eol()) {
      stream.start = stream.pos;style = readToken(mode, stream, context.state);if (asArray) {
        tokens.push(new Token(stream, style, copyState(doc.mode, context.state)));
      }
    }return asArray ? tokens : new Token(stream, style, context.state);
  }function extractLineClasses(type, output) {
    if (type) {
      for (;;) {
        var lineClass = type.match(/(?:^|\s+)line-(background-)?(\S+)/);if (!lineClass) {
          break;
        }type = type.slice(0, lineClass.index) + type.slice(lineClass.index + lineClass[0].length);var prop = lineClass[1] ? "bgClass" : "textClass";if (output[prop] == null) {
          output[prop] = lineClass[2];
        } else if (!new RegExp("(?:^|s)" + lineClass[2] + "(?:$|s)").test(output[prop])) {
          output[prop] += " " + lineClass[2];
        }
      }
    }return type;
  }function runMode(cm, text, mode, context, f, lineClasses, forceToEnd) {
    var flattenSpans = mode.flattenSpans;if (flattenSpans == null) {
      flattenSpans = cm.options.flattenSpans;
    }var curStart = 0,
        curStyle = null;var stream = new StringStream(text, cm.options.tabSize, context),
        style;var inner = cm.options.addModeClass && [null];if (text == "") {
      extractLineClasses(callBlankLine(mode, context.state), lineClasses);
    }while (!stream.eol()) {
      if (stream.pos > cm.options.maxHighlightLength) {
        flattenSpans = false;if (forceToEnd) {
          processLine(cm, text, context, stream.pos);
        }stream.pos = text.length;style = null;
      } else {
        style = extractLineClasses(readToken(mode, stream, context.state, inner), lineClasses);
      }if (inner) {
        var mName = inner[0].name;if (mName) {
          style = "m-" + (style ? mName + " " + style : mName);
        }
      }if (!flattenSpans || curStyle != style) {
        while (curStart < stream.start) {
          curStart = Math.min(stream.start, curStart + 5e3);f(curStart, curStyle);
        }curStyle = style;
      }stream.start = stream.pos;
    }while (curStart < stream.pos) {
      var pos = Math.min(stream.pos, curStart + 5e3);f(pos, curStyle);curStart = pos;
    }
  }function findStartLine(cm, n, precise) {
    var minindent,
        minline,
        doc = cm.doc;var lim = precise ? -1 : n - (cm.doc.mode.innerMode ? 1e3 : 100);for (var search = n; search > lim; --search) {
      if (search <= doc.first) {
        return doc.first;
      }var line = getLine(doc, search - 1),
          after = line.stateAfter;if (after && (!precise || search + (after instanceof SavedContext ? after.lookAhead : 0) <= doc.modeFrontier)) {
        return search;
      }var indented = countColumn(line.text, null, cm.options.tabSize);if (minline == null || minindent > indented) {
        minline = search - 1;minindent = indented;
      }
    }return minline;
  }function retreatFrontier(doc, n) {
    doc.modeFrontier = Math.min(doc.modeFrontier, n);if (doc.highlightFrontier < n - 10) {
      return;
    }var start = doc.first;for (var line = n - 1; line > start; line--) {
      var saved = getLine(doc, line).stateAfter;if (saved && (!(saved instanceof SavedContext) || line + saved.lookAhead < n)) {
        start = line + 1;break;
      }
    }doc.highlightFrontier = Math.min(doc.highlightFrontier, start);
  }var sawReadOnlySpans = false,
      sawCollapsedSpans = false;function seeReadOnlySpans() {
    sawReadOnlySpans = true;
  }function seeCollapsedSpans() {
    sawCollapsedSpans = true;
  }
  function MarkedSpan(marker, from, to) {
    this.marker = marker;this.from = from;this.to = to;
  }function getMarkedSpanFor(spans, marker) {
    if (spans) {
      for (var i = 0; i < spans.length; ++i) {
        var span = spans[i];if (span.marker == marker) {
          return span;
        }
      }
    }
  }function removeMarkedSpan(spans, span) {
    var r;for (var i = 0; i < spans.length; ++i) {
      if (spans[i] != span) {
        (r || (r = [])).push(spans[i]);
      }
    }return r;
  }function addMarkedSpan(line, span) {
    line.markedSpans = line.markedSpans ? line.markedSpans.concat([span]) : [span];span.marker.attachLine(line);
  }function markedSpansBefore(old, startCh, isInsert) {
    var nw;if (old) {
      for (var i = 0; i < old.length; ++i) {
        var span = old[i],
            marker = span.marker;var startsBefore = span.from == null || (marker.inclusiveLeft ? span.from <= startCh : span.from < startCh);if (startsBefore || span.from == startCh && marker.type == "bookmark" && (!isInsert || !span.marker.insertLeft)) {
          var endsAfter = span.to == null || (marker.inclusiveRight ? span.to >= startCh : span.to > startCh);(nw || (nw = [])).push(new MarkedSpan(marker, span.from, endsAfter ? null : span.to));
        }
      }
    }return nw;
  }function markedSpansAfter(old, endCh, isInsert) {
    var nw;if (old) {
      for (var i = 0; i < old.length; ++i) {
        var span = old[i],
            marker = span.marker;var endsAfter = span.to == null || (marker.inclusiveRight ? span.to >= endCh : span.to > endCh);if (endsAfter || span.from == endCh && marker.type == "bookmark" && (!isInsert || span.marker.insertLeft)) {
          var startsBefore = span.from == null || (marker.inclusiveLeft ? span.from <= endCh : span.from < endCh);(nw || (nw = [])).push(new MarkedSpan(marker, startsBefore ? null : span.from - endCh, span.to == null ? null : span.to - endCh));
        }
      }
    }return nw;
  }function stretchSpansOverChange(doc, change) {
    if (change.full) {
      return null;
    }var oldFirst = isLine(doc, change.from.line) && getLine(doc, change.from.line).markedSpans;var oldLast = isLine(doc, change.to.line) && getLine(doc, change.to.line).markedSpans;if (!oldFirst && !oldLast) {
      return null;
    }var startCh = change.from.ch,
        endCh = change.to.ch,
        isInsert = cmp(change.from, change.to) == 0;var first = markedSpansBefore(oldFirst, startCh, isInsert);var last = markedSpansAfter(oldLast, endCh, isInsert);var sameLine = change.text.length == 1,
        offset = lst(change.text).length + (sameLine ? startCh : 0);if (first) {
      for (var i = 0; i < first.length; ++i) {
        var span = first[i];if (span.to == null) {
          var found = getMarkedSpanFor(last, span.marker);if (!found) {
            span.to = startCh;
          } else if (sameLine) {
            span.to = found.to == null ? null : found.to + offset;
          }
        }
      }
    }if (last) {
      for (var i$1 = 0; i$1 < last.length; ++i$1) {
        var span$1 = last[i$1];if (span$1.to != null) {
          span$1.to += offset;
        }if (span$1.from == null) {
          var found$1 = getMarkedSpanFor(first, span$1.marker);if (!found$1) {
            span$1.from = offset;if (sameLine) {
              (first || (first = [])).push(span$1);
            }
          }
        } else {
          span$1.from += offset;if (sameLine) {
            (first || (first = [])).push(span$1);
          }
        }
      }
    }if (first) {
      first = clearEmptySpans(first);
    }if (last && last != first) {
      last = clearEmptySpans(last);
    }var newMarkers = [first];if (!sameLine) {
      var gap = change.text.length - 2,
          gapMarkers;if (gap > 0 && first) {
        for (var i$2 = 0; i$2 < first.length; ++i$2) {
          if (first[i$2].to == null) {
            (gapMarkers || (gapMarkers = [])).push(new MarkedSpan(first[i$2].marker, null, null));
          }
        }
      }for (var i$3 = 0; i$3 < gap; ++i$3) {
        newMarkers.push(gapMarkers);
      }newMarkers.push(last);
    }return newMarkers;
  }function clearEmptySpans(spans) {
    for (var i = 0; i < spans.length; ++i) {
      var span = spans[i];if (span.from != null && span.from == span.to && span.marker.clearWhenEmpty !== false) {
        spans.splice(i--, 1);
      }
    }if (!spans.length) {
      return null;
    }return spans;
  }function removeReadOnlyRanges(doc, from, to) {
    var markers = null;doc.iter(from.line, to.line + 1, function (line) {
      if (line.markedSpans) {
        for (var i = 0; i < line.markedSpans.length; ++i) {
          var mark = line.markedSpans[i].marker;if (mark.readOnly && (!markers || indexOf(markers, mark) == -1)) {
            (markers || (markers = [])).push(mark);
          }
        }
      }
    });if (!markers) {
      return null;
    }var parts = [{ from: from, to: to }];for (var i = 0; i < markers.length; ++i) {
      var mk = markers[i],
          m = mk.find(0);for (var j = 0; j < parts.length; ++j) {
        var p = parts[j];if (cmp(p.to, m.from) < 0 || cmp(p.from, m.to) > 0) {
          continue;
        }var newParts = [j, 1],
            dfrom = cmp(p.from, m.from),
            dto = cmp(p.to, m.to);if (dfrom < 0 || !mk.inclusiveLeft && !dfrom) {
          newParts.push({ from: p.from, to: m.from });
        }if (dto > 0 || !mk.inclusiveRight && !dto) {
          newParts.push({ from: m.to, to: p.to });
        }parts.splice.apply(parts, newParts);j += newParts.length - 3;
      }
    }return parts;
  }function detachMarkedSpans(line) {
    var spans = line.markedSpans;if (!spans) {
      return;
    }for (var i = 0; i < spans.length; ++i) {
      spans[i].marker.detachLine(line);
    }line.markedSpans = null;
  }function attachMarkedSpans(line, spans) {
    if (!spans) {
      return;
    }for (var i = 0; i < spans.length; ++i) {
      spans[i].marker.attachLine(line);
    }line.markedSpans = spans;
  }function extraLeft(marker) {
    return marker.inclusiveLeft ? -1 : 0;
  }function extraRight(marker) {
    return marker.inclusiveRight ? 1 : 0;
  }function compareCollapsedMarkers(a, b) {
    var lenDiff = a.lines.length - b.lines.length;if (lenDiff != 0) {
      return lenDiff;
    }var aPos = a.find(),
        bPos = b.find();var fromCmp = cmp(aPos.from, bPos.from) || extraLeft(a) - extraLeft(b);if (fromCmp) {
      return -fromCmp;
    }var toCmp = cmp(aPos.to, bPos.to) || extraRight(a) - extraRight(b);if (toCmp) {
      return toCmp;
    }return b.id - a.id;
  }function collapsedSpanAtSide(line, start) {
    var sps = sawCollapsedSpans && line.markedSpans,
        found;if (sps) {
      for (var sp = void 0, i = 0; i < sps.length; ++i) {
        sp = sps[i];if (sp.marker.collapsed && (start ? sp.from : sp.to) == null && (!found || compareCollapsedMarkers(found, sp.marker) < 0)) {
          found = sp.marker;
        }
      }
    }return found;
  }function collapsedSpanAtStart(line) {
    return collapsedSpanAtSide(line, true);
  }function collapsedSpanAtEnd(line) {
    return collapsedSpanAtSide(line, false);
  }function collapsedSpanAround(line, ch) {
    var sps = sawCollapsedSpans && line.markedSpans,
        found;if (sps) {
      for (var i = 0; i < sps.length; ++i) {
        var sp = sps[i];if (sp.marker.collapsed && (sp.from == null || sp.from < ch) && (sp.to == null || sp.to > ch) && (!found || compareCollapsedMarkers(found, sp.marker) < 0)) {
          found = sp.marker;
        }
      }
    }return found;
  }function conflictingCollapsedRange(doc, lineNo$$1, from, to, marker) {
    var line = getLine(doc, lineNo$$1);var sps = sawCollapsedSpans && line.markedSpans;if (sps) {
      for (var i = 0; i < sps.length; ++i) {
        var sp = sps[i];if (!sp.marker.collapsed) {
          continue;
        }var found = sp.marker.find(0);var fromCmp = cmp(found.from, from) || extraLeft(sp.marker) - extraLeft(marker);var toCmp = cmp(found.to, to) || extraRight(sp.marker) - extraRight(marker);if (fromCmp >= 0 && toCmp <= 0 || fromCmp <= 0 && toCmp >= 0) {
          continue;
        }if (fromCmp <= 0 && (sp.marker.inclusiveRight && marker.inclusiveLeft ? cmp(found.to, from) >= 0 : cmp(found.to, from) > 0) || fromCmp >= 0 && (sp.marker.inclusiveRight && marker.inclusiveLeft ? cmp(found.from, to) <= 0 : cmp(found.from, to) < 0)) {
          return true;
        }
      }
    }
  }function visualLine(line) {
    var merged;while (merged = collapsedSpanAtStart(line)) {
      line = merged.find(-1, true).line;
    }return line;
  }function visualLineEnd(line) {
    var merged;while (merged = collapsedSpanAtEnd(line)) {
      line = merged.find(1, true).line;
    }return line;
  }function visualLineContinued(line) {
    var merged, lines;while (merged = collapsedSpanAtEnd(line)) {
      line = merged.find(1, true).line;(lines || (lines = [])).push(line);
    }return lines;
  }function visualLineNo(doc, lineN) {
    var line = getLine(doc, lineN),
        vis = visualLine(line);if (line == vis) {
      return lineN;
    }return lineNo(vis);
  }function visualLineEndNo(doc, lineN) {
    if (lineN > doc.lastLine()) {
      return lineN;
    }var line = getLine(doc, lineN),
        merged;if (!lineIsHidden(doc, line)) {
      return lineN;
    }while (merged = collapsedSpanAtEnd(line)) {
      line = merged.find(1, true).line;
    }return lineNo(line) + 1;
  }function lineIsHidden(doc, line) {
    var sps = sawCollapsedSpans && line.markedSpans;if (sps) {
      for (var sp = void 0, i = 0; i < sps.length; ++i) {
        sp = sps[i];if (!sp.marker.collapsed) {
          continue;
        }if (sp.from == null) {
          return true;
        }if (sp.marker.widgetNode) {
          continue;
        }if (sp.from == 0 && sp.marker.inclusiveLeft && lineIsHiddenInner(doc, line, sp)) {
          return true;
        }
      }
    }
  }function lineIsHiddenInner(doc, line, span) {
    if (span.to == null) {
      var end = span.marker.find(1, true);return lineIsHiddenInner(doc, end.line, getMarkedSpanFor(end.line.markedSpans, span.marker));
    }if (span.marker.inclusiveRight && span.to == line.text.length) {
      return true;
    }for (var sp = void 0, i = 0; i < line.markedSpans.length; ++i) {
      sp = line.markedSpans[i];if (sp.marker.collapsed && !sp.marker.widgetNode && sp.from == span.to && (sp.to == null || sp.to != span.from) && (sp.marker.inclusiveLeft || span.marker.inclusiveRight) && lineIsHiddenInner(doc, line, sp)) {
        return true;
      }
    }
  }function _heightAtLine(lineObj) {
    lineObj = visualLine(lineObj);var h = 0,
        chunk = lineObj.parent;for (var i = 0; i < chunk.lines.length; ++i) {
      var line = chunk.lines[i];if (line == lineObj) {
        break;
      } else {
        h += line.height;
      }
    }for (var p = chunk.parent; p; chunk = p, p = chunk.parent) {
      for (var i$1 = 0; i$1 < p.children.length; ++i$1) {
        var cur = p.children[i$1];if (cur == chunk) {
          break;
        } else {
          h += cur.height;
        }
      }
    }return h;
  }function lineLength(line) {
    if (line.height == 0) {
      return 0;
    }var len = line.text.length,
        merged,
        cur = line;while (merged = collapsedSpanAtStart(cur)) {
      var found = merged.find(0, true);cur = found.from.line;len += found.from.ch - found.to.ch;
    }cur = line;while (merged = collapsedSpanAtEnd(cur)) {
      var found$1 = merged.find(0, true);len -= cur.text.length - found$1.from.ch;cur = found$1.to.line;len += cur.text.length - found$1.to.ch;
    }return len;
  }function findMaxLine(cm) {
    var d = cm.display,
        doc = cm.doc;d.maxLine = getLine(doc, doc.first);d.maxLineLength = lineLength(d.maxLine);d.maxLineChanged = true;doc.iter(function (line) {
      var len = lineLength(line);if (len > d.maxLineLength) {
        d.maxLineLength = len;d.maxLine = line;
      }
    });
  }var Line = function Line(text, markedSpans, estimateHeight) {
    this.text = text;attachMarkedSpans(this, markedSpans);this.height = estimateHeight ? estimateHeight(this) : 1;
  };Line.prototype.lineNo = function () {
    return lineNo(this);
  };eventMixin(Line);function updateLine(line, text, markedSpans, estimateHeight) {
    line.text = text;if (line.stateAfter) {
      line.stateAfter = null;
    }if (line.styles) {
      line.styles = null;
    }if (line.order != null) {
      line.order = null;
    }detachMarkedSpans(line);attachMarkedSpans(line, markedSpans);var estHeight = estimateHeight ? estimateHeight(line) : 1;if (estHeight != line.height) {
      updateLineHeight(line, estHeight);
    }
  }function cleanUpLine(line) {
    line.parent = null;detachMarkedSpans(line);
  }var styleToClassCache = {},
      styleToClassCacheWithMode = {};function interpretTokenStyle(style, options) {
    if (!style || /^\s*$/.test(style)) {
      return null;
    }var cache = options.addModeClass ? styleToClassCacheWithMode : styleToClassCache;return cache[style] || (cache[style] = style.replace(/\S+/g, "cm-$&"));
  }function buildLineContent(cm, lineView) {
    var content = eltP("span", null, null, webkit ? "padding-right: .1px" : null);var builder = { pre: eltP("pre", [content], "CodeMirror-line"), content: content, col: 0, pos: 0, cm: cm, trailingSpace: false, splitSpaces: cm.getOption("lineWrapping") };lineView.measure = {};for (var i = 0; i <= (lineView.rest ? lineView.rest.length : 0); i++) {
      var line = i ? lineView.rest[i - 1] : lineView.line,
          order = void 0;builder.pos = 0;builder.addToken = buildToken;if (hasBadBidiRects(cm.display.measure) && (order = getOrder(line, cm.doc.direction))) {
        builder.addToken = buildTokenBadBidi(builder.addToken, order);
      }builder.map = [];var allowFrontierUpdate = lineView != cm.display.externalMeasured && lineNo(line);insertLineContent(line, builder, getLineStyles(cm, line, allowFrontierUpdate));if (line.styleClasses) {
        if (line.styleClasses.bgClass) {
          builder.bgClass = joinClasses(line.styleClasses.bgClass, builder.bgClass || "");
        }if (line.styleClasses.textClass) {
          builder.textClass = joinClasses(line.styleClasses.textClass, builder.textClass || "");
        }
      }if (builder.map.length == 0) {
        builder.map.push(0, 0, builder.content.appendChild(zeroWidthElement(cm.display.measure)));
      }if (i == 0) {
        lineView.measure.map = builder.map;lineView.measure.cache = {};
      } else {
        (lineView.measure.maps || (lineView.measure.maps = [])).push(builder.map);(lineView.measure.caches || (lineView.measure.caches = [])).push({});
      }
    }if (webkit) {
      var last = builder.content.lastChild;if (/\bcm-tab\b/.test(last.className) || last.querySelector && last.querySelector(".cm-tab")) {
        builder.content.className = "cm-tab-wrap-hack";
      }
    }signal(cm, "renderLine", cm, lineView.line, builder.pre);if (builder.pre.className) {
      builder.textClass = joinClasses(builder.pre.className, builder.textClass || "");
    }return builder;
  }function defaultSpecialCharPlaceholder(ch) {
    var token = elt("span", "•", "cm-invalidchar");token.title = "\\u" + ch.charCodeAt(0).toString(16);token.setAttribute("aria-label", token.title);return token;
  }function buildToken(builder, text, style, startStyle, endStyle, css, attributes) {
    if (!text) {
      return;
    }var displayText = builder.splitSpaces ? splitSpaces(text, builder.trailingSpace) : text;var special = builder.cm.state.specialChars,
        mustWrap = false;var content;if (!special.test(text)) {
      builder.col += text.length;content = document.createTextNode(displayText);builder.map.push(builder.pos, builder.pos + text.length, content);if (ie && ie_version < 9) {
        mustWrap = true;
      }builder.pos += text.length;
    } else {
      content = document.createDocumentFragment();var pos = 0;while (true) {
        special.lastIndex = pos;var m = special.exec(text);var skipped = m ? m.index - pos : text.length - pos;if (skipped) {
          var txt = document.createTextNode(displayText.slice(pos, pos + skipped));if (ie && ie_version < 9) {
            content.appendChild(elt("span", [txt]));
          } else {
            content.appendChild(txt);
          }builder.map.push(builder.pos, builder.pos + skipped, txt);builder.col += skipped;builder.pos += skipped;
        }if (!m) {
          break;
        }pos += skipped + 1;var txt$1 = void 0;if (m[0] == "\t") {
          var tabSize = builder.cm.options.tabSize,
              tabWidth = tabSize - builder.col % tabSize;txt$1 = content.appendChild(elt("span", spaceStr(tabWidth), "cm-tab"));txt$1.setAttribute("role", "presentation");txt$1.setAttribute("cm-text", "\t");builder.col += tabWidth;
        } else if (m[0] == "\r" || m[0] == "\n") {
          txt$1 = content.appendChild(elt("span", m[0] == "\r" ? "␍" : "␤", "cm-invalidchar"));txt$1.setAttribute("cm-text", m[0]);builder.col += 1;
        } else {
          txt$1 = builder.cm.options.specialCharPlaceholder(m[0]);txt$1.setAttribute("cm-text", m[0]);if (ie && ie_version < 9) {
            content.appendChild(elt("span", [txt$1]));
          } else {
            content.appendChild(txt$1);
          }builder.col += 1;
        }builder.map.push(builder.pos, builder.pos + 1, txt$1);builder.pos++;
      }
    }builder.trailingSpace = displayText.charCodeAt(text.length - 1) == 32;if (style || startStyle || endStyle || mustWrap || css) {
      var fullStyle = style || "";if (startStyle) {
        fullStyle += startStyle;
      }if (endStyle) {
        fullStyle += endStyle;
      }var token = elt("span", [content], fullStyle, css);if (attributes) {
        for (var attr in attributes) {
          if (attributes.hasOwnProperty(attr) && attr != "style" && attr != "class") {
            token.setAttribute(attr, attributes[attr]);
          }
        }
      }return builder.content.appendChild(token);
    }builder.content.appendChild(content);
  }function splitSpaces(text, trailingBefore) {
    if (text.length > 1 && !/  /.test(text)) {
      return text;
    }var spaceBefore = trailingBefore,
        result = "";for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);if (ch == " " && spaceBefore && (i == text.length - 1 || text.charCodeAt(i + 1) == 32)) {
        ch = " ";
      }result += ch;spaceBefore = ch == " ";
    }return result;
  }function buildTokenBadBidi(inner, order) {
    return function (builder, text, style, startStyle, endStyle, css, attributes) {
      style = style ? style + " cm-force-border" : "cm-force-border";var start = builder.pos,
          end = start + text.length;for (;;) {
        var part = void 0;for (var i = 0; i < order.length; i++) {
          part = order[i];if (part.to > start && part.from <= start) {
            break;
          }
        }if (part.to >= end) {
          return inner(builder, text, style, startStyle, endStyle, css, attributes);
        }inner(builder, text.slice(0, part.to - start), style, startStyle, null, css, attributes);startStyle = null;text = text.slice(part.to - start);start = part.to;
      }
    };
  }function buildCollapsedSpan(builder, size, marker, ignoreWidget) {
    var widget = !ignoreWidget && marker.widgetNode;if (widget) {
      builder.map.push(builder.pos, builder.pos + size, widget);
    }if (!ignoreWidget && builder.cm.display.input.needsContentAttribute) {
      if (!widget) {
        widget = builder.content.appendChild(document.createElement("span"));
      }widget.setAttribute("cm-marker", marker.id);
    }if (widget) {
      builder.cm.display.input.setUneditable(widget);builder.content.appendChild(widget);
    }builder.pos += size;builder.trailingSpace = false;
  }function insertLineContent(line, builder, styles) {
    var spans = line.markedSpans,
        allText = line.text,
        at = 0;if (!spans) {
      for (var i$1 = 1; i$1 < styles.length; i$1 += 2) {
        builder.addToken(builder, allText.slice(at, at = styles[i$1]), interpretTokenStyle(styles[i$1 + 1], builder.cm.options));
      }return;
    }var len = allText.length,
        pos = 0,
        i = 1,
        text = "",
        style,
        css;var nextChange = 0,
        spanStyle,
        spanEndStyle,
        spanStartStyle,
        collapsed,
        attributes;for (;;) {
      if (nextChange == pos) {
        spanStyle = spanEndStyle = spanStartStyle = css = "";attributes = null;collapsed = null;nextChange = Infinity;var foundBookmarks = [],
            endStyles = void 0;for (var j = 0; j < spans.length; ++j) {
          var sp = spans[j],
              m = sp.marker;if (m.type == "bookmark" && sp.from == pos && m.widgetNode) {
            foundBookmarks.push(m);
          } else if (sp.from <= pos && (sp.to == null || sp.to > pos || m.collapsed && sp.to == pos && sp.from == pos)) {
            if (sp.to != null && sp.to != pos && nextChange > sp.to) {
              nextChange = sp.to;spanEndStyle = "";
            }if (m.className) {
              spanStyle += " " + m.className;
            }if (m.css) {
              css = (css ? css + ";" : "") + m.css;
            }if (m.startStyle && sp.from == pos) {
              spanStartStyle += " " + m.startStyle;
            }if (m.endStyle && sp.to == nextChange) {
              (endStyles || (endStyles = [])).push(m.endStyle, sp.to);
            }if (m.title) {
              (attributes || (attributes = {})).title = m.title;
            }if (m.attributes) {
              for (var attr in m.attributes) {
                (attributes || (attributes = {}))[attr] = m.attributes[attr];
              }
            }if (m.collapsed && (!collapsed || compareCollapsedMarkers(collapsed.marker, m) < 0)) {
              collapsed = sp;
            }
          } else if (sp.from > pos && nextChange > sp.from) {
            nextChange = sp.from;
          }
        }if (endStyles) {
          for (var j$1 = 0; j$1 < endStyles.length; j$1 += 2) {
            if (endStyles[j$1 + 1] == nextChange) {
              spanEndStyle += " " + endStyles[j$1];
            }
          }
        }if (!collapsed || collapsed.from == pos) {
          for (var j$2 = 0; j$2 < foundBookmarks.length; ++j$2) {
            buildCollapsedSpan(builder, 0, foundBookmarks[j$2]);
          }
        }if (collapsed && (collapsed.from || 0) == pos) {
          buildCollapsedSpan(builder, (collapsed.to == null ? len + 1 : collapsed.to) - pos, collapsed.marker, collapsed.from == null);if (collapsed.to == null) {
            return;
          }if (collapsed.to == pos) {
            collapsed = false;
          }
        }
      }if (pos >= len) {
        break;
      }var upto = Math.min(len, nextChange);while (true) {
        if (text) {
          var end = pos + text.length;if (!collapsed) {
            var tokenText = end > upto ? text.slice(0, upto - pos) : text;builder.addToken(builder, tokenText, style ? style + spanStyle : spanStyle, spanStartStyle, pos + tokenText.length == nextChange ? spanEndStyle : "", css, attributes);
          }if (end >= upto) {
            text = text.slice(upto - pos);pos = upto;break;
          }pos = end;spanStartStyle = "";
        }text = allText.slice(at, at = styles[i++]);style = interpretTokenStyle(styles[i++], builder.cm.options);
      }
    }
  }function LineView(doc, line, lineN) {
    this.line = line;this.rest = visualLineContinued(line);this.size = this.rest ? lineNo(lst(this.rest)) - lineN + 1 : 1;this.node = this.text = null;this.hidden = lineIsHidden(doc, line);
  }function buildViewArray(cm, from, to) {
    var array = [],
        nextPos;for (var pos = from; pos < to; pos = nextPos) {
      var view = new LineView(cm.doc, getLine(cm.doc, pos), pos);nextPos = pos + view.size;array.push(view);
    }return array;
  }var operationGroup = null;function pushOperation(op) {
    if (operationGroup) {
      operationGroup.ops.push(op);
    } else {
      op.ownsGroup = operationGroup = { ops: [op], delayedCallbacks: [] };
    }
  }function fireCallbacksForOps(group) {
    var callbacks = group.delayedCallbacks,
        i = 0;do {
      for (; i < callbacks.length; i++) {
        callbacks[i].call(null);
      }for (var j = 0; j < group.ops.length; j++) {
        var op = group.ops[j];if (op.cursorActivityHandlers) {
          while (op.cursorActivityCalled < op.cursorActivityHandlers.length) {
            op.cursorActivityHandlers[op.cursorActivityCalled++].call(null, op.cm);
          }
        }
      }
    } while (i < callbacks.length);
  }function finishOperation(op, endCb) {
    var group = op.ownsGroup;if (!group) {
      return;
    }try {
      fireCallbacksForOps(group);
    } finally {
      operationGroup = null;endCb(group);
    }
  }var orphanDelayedCallbacks = null;function signalLater(emitter, type) {
    var arr = getHandlers(emitter, type);if (!arr.length) {
      return;
    }var args = Array.prototype.slice.call(arguments, 2),
        list;if (operationGroup) {
      list = operationGroup.delayedCallbacks;
    } else if (orphanDelayedCallbacks) {
      list = orphanDelayedCallbacks;
    } else {
      list = orphanDelayedCallbacks = [];setTimeout(fireOrphanDelayed, 0);
    }var loop = function loop(i) {
      list.push(function () {
        return arr[i].apply(null, args);
      });
    };for (var i = 0; i < arr.length; ++i) {
      loop(i);
    }
  }function fireOrphanDelayed() {
    var delayed = orphanDelayedCallbacks;orphanDelayedCallbacks = null;for (var i = 0; i < delayed.length; ++i) {
      delayed[i]();
    }
  }function updateLineForChanges(cm, lineView, lineN, dims) {
    for (var j = 0; j < lineView.changes.length; j++) {
      var type = lineView.changes[j];if (type == "text") {
        updateLineText(cm, lineView);
      } else if (type == "gutter") {
        updateLineGutter(cm, lineView, lineN, dims);
      } else if (type == "class") {
        updateLineClasses(cm, lineView);
      } else if (type == "widget") {
        updateLineWidgets(cm, lineView, dims);
      }
    }lineView.changes = null;
  }function ensureLineWrapped(lineView) {
    if (lineView.node == lineView.text) {
      lineView.node = elt("div", null, null, "position: relative");if (lineView.text.parentNode) {
        lineView.text.parentNode.replaceChild(lineView.node, lineView.text);
      }lineView.node.appendChild(lineView.text);if (ie && ie_version < 8) {
        lineView.node.style.zIndex = 2;
      }
    }return lineView.node;
  }function updateLineBackground(cm, lineView) {
    var cls = lineView.bgClass ? lineView.bgClass + " " + (lineView.line.bgClass || "") : lineView.line.bgClass;if (cls) {
      cls += " CodeMirror-linebackground";
    }if (lineView.background) {
      if (cls) {
        lineView.background.className = cls;
      } else {
        lineView.background.parentNode.removeChild(lineView.background);lineView.background = null;
      }
    } else if (cls) {
      var wrap = ensureLineWrapped(lineView);lineView.background = wrap.insertBefore(elt("div", null, cls), wrap.firstChild);cm.display.input.setUneditable(lineView.background);
    }
  }function getLineContent(cm, lineView) {
    var ext = cm.display.externalMeasured;if (ext && ext.line == lineView.line) {
      cm.display.externalMeasured = null;lineView.measure = ext.measure;return ext.built;
    }return buildLineContent(cm, lineView);
  }function updateLineText(cm, lineView) {
    var cls = lineView.text.className;var built = getLineContent(cm, lineView);if (lineView.text == lineView.node) {
      lineView.node = built.pre;
    }lineView.text.parentNode.replaceChild(built.pre, lineView.text);lineView.text = built.pre;if (built.bgClass != lineView.bgClass || built.textClass != lineView.textClass) {
      lineView.bgClass = built.bgClass;lineView.textClass = built.textClass;updateLineClasses(cm, lineView);
    } else if (cls) {
      lineView.text.className = cls;
    }
  }function updateLineClasses(cm, lineView) {
    updateLineBackground(cm, lineView);if (lineView.line.wrapClass) {
      ensureLineWrapped(lineView).className = lineView.line.wrapClass;
    } else if (lineView.node != lineView.text) {
      lineView.node.className = "";
    }var textClass = lineView.textClass ? lineView.textClass + " " + (lineView.line.textClass || "") : lineView.line.textClass;lineView.text.className = textClass || "";
  }function updateLineGutter(cm, lineView, lineN, dims) {
    if (lineView.gutter) {
      lineView.node.removeChild(lineView.gutter);lineView.gutter = null;
    }if (lineView.gutterBackground) {
      lineView.node.removeChild(lineView.gutterBackground);lineView.gutterBackground = null;
    }if (lineView.line.gutterClass) {
      var wrap = ensureLineWrapped(lineView);lineView.gutterBackground = elt("div", null, "CodeMirror-gutter-background " + lineView.line.gutterClass, "left: " + (cm.options.fixedGutter ? dims.fixedPos : -dims.gutterTotalWidth) + "px; width: " + dims.gutterTotalWidth + "px");cm.display.input.setUneditable(lineView.gutterBackground);wrap.insertBefore(lineView.gutterBackground, lineView.text);
    }var markers = lineView.line.gutterMarkers;if (cm.options.lineNumbers || markers) {
      var wrap$1 = ensureLineWrapped(lineView);var gutterWrap = lineView.gutter = elt("div", null, "CodeMirror-gutter-wrapper", "left: " + (cm.options.fixedGutter ? dims.fixedPos : -dims.gutterTotalWidth) + "px");cm.display.input.setUneditable(gutterWrap);wrap$1.insertBefore(gutterWrap, lineView.text);if (lineView.line.gutterClass) {
        gutterWrap.className += " " + lineView.line.gutterClass;
      }if (cm.options.lineNumbers && (!markers || !markers["CodeMirror-linenumbers"])) {
        lineView.lineNumber = gutterWrap.appendChild(elt("div", lineNumberFor(cm.options, lineN), "CodeMirror-linenumber CodeMirror-gutter-elt", "left: " + dims.gutterLeft["CodeMirror-linenumbers"] + "px; width: " + cm.display.lineNumInnerWidth + "px"));
      }if (markers) {
        for (var k = 0; k < cm.display.gutterSpecs.length; ++k) {
          var id = cm.display.gutterSpecs[k].className,
              found = markers.hasOwnProperty(id) && markers[id];if (found) {
            gutterWrap.appendChild(elt("div", [found], "CodeMirror-gutter-elt", "left: " + dims.gutterLeft[id] + "px; width: " + dims.gutterWidth[id] + "px"));
          }
        }
      }
    }
  }function updateLineWidgets(cm, lineView, dims) {
    if (lineView.alignable) {
      lineView.alignable = null;
    }for (var node = lineView.node.firstChild, next = void 0; node; node = next) {
      next = node.nextSibling;if (node.className == "CodeMirror-linewidget") {
        lineView.node.removeChild(node);
      }
    }insertLineWidgets(cm, lineView, dims);
  }function buildLineElement(cm, lineView, lineN, dims) {
    var built = getLineContent(cm, lineView);lineView.text = lineView.node = built.pre;if (built.bgClass) {
      lineView.bgClass = built.bgClass;
    }if (built.textClass) {
      lineView.textClass = built.textClass;
    }updateLineClasses(cm, lineView);updateLineGutter(cm, lineView, lineN, dims);insertLineWidgets(cm, lineView, dims);return lineView.node;
  }function insertLineWidgets(cm, lineView, dims) {
    insertLineWidgetsFor(cm, lineView.line, lineView, dims, true);if (lineView.rest) {
      for (var i = 0; i < lineView.rest.length; i++) {
        insertLineWidgetsFor(cm, lineView.rest[i], lineView, dims, false);
      }
    }
  }function insertLineWidgetsFor(cm, line, lineView, dims, allowAbove) {
    if (!line.widgets) {
      return;
    }var wrap = ensureLineWrapped(lineView);for (var i = 0, ws = line.widgets; i < ws.length; ++i) {
      var widget = ws[i],
          node = elt("div", [widget.node], "CodeMirror-linewidget");if (!widget.handleMouseEvents) {
        node.setAttribute("cm-ignore-events", "true");
      }positionLineWidget(widget, node, lineView, dims);cm.display.input.setUneditable(node);if (allowAbove && widget.above) {
        wrap.insertBefore(node, lineView.gutter || lineView.text);
      } else {
        wrap.appendChild(node);
      }signalLater(widget, "redraw");
    }
  }function positionLineWidget(widget, node, lineView, dims) {
    if (widget.noHScroll) {
      (lineView.alignable || (lineView.alignable = [])).push(node);var width = dims.wrapperWidth;node.style.left = dims.fixedPos + "px";if (!widget.coverGutter) {
        width -= dims.gutterTotalWidth;node.style.paddingLeft = dims.gutterTotalWidth + "px";
      }node.style.width = width + "px";
    }if (widget.coverGutter) {
      node.style.zIndex = 5;node.style.position = "relative";if (!widget.noHScroll) {
        node.style.marginLeft = -dims.gutterTotalWidth + "px";
      }
    }
  }function widgetHeight(widget) {
    if (widget.height != null) {
      return widget.height;
    }var cm = widget.doc.cm;if (!cm) {
      return 0;
    }if (!contains(document.body, widget.node)) {
      var parentStyle = "position: relative;";if (widget.coverGutter) {
        parentStyle += "margin-left: -" + cm.display.gutters.offsetWidth + "px;";
      }if (widget.noHScroll) {
        parentStyle += "width: " + cm.display.wrapper.clientWidth + "px;";
      }removeChildrenAndAdd(cm.display.measure, elt("div", [widget.node], null, parentStyle));
    }return widget.height = widget.node.parentNode.offsetHeight;
  }function eventInWidget(display, e) {
    for (var n = e_target(e); n != display.wrapper; n = n.parentNode) {
      if (!n || n.nodeType == 1 && n.getAttribute("cm-ignore-events") == "true" || n.parentNode == display.sizer && n != display.mover) {
        return true;
      }
    }
  }function paddingTop(display) {
    return display.lineSpace.offsetTop;
  }function paddingVert(display) {
    return display.mover.offsetHeight - display.lineSpace.offsetHeight;
  }function paddingH(display) {
    if (display.cachedPaddingH) {
      return display.cachedPaddingH;
    }var e = removeChildrenAndAdd(display.measure, elt("pre", "x", "CodeMirror-line-like"));var style = window.getComputedStyle ? window.getComputedStyle(e) : e.currentStyle;var data = { left: parseInt(style.paddingLeft), right: parseInt(style.paddingRight) };if (!isNaN(data.left) && !isNaN(data.right)) {
      display.cachedPaddingH = data;
    }return data;
  }function scrollGap(cm) {
    return scrollerGap - cm.display.nativeBarWidth;
  }function displayWidth(cm) {
    return cm.display.scroller.clientWidth - scrollGap(cm) - cm.display.barWidth;
  }function displayHeight(cm) {
    return cm.display.scroller.clientHeight - scrollGap(cm) - cm.display.barHeight;
  }function ensureLineHeights(cm, lineView, rect) {
    var wrapping = cm.options.lineWrapping;var curWidth = wrapping && displayWidth(cm);if (!lineView.measure.heights || wrapping && lineView.measure.width != curWidth) {
      var heights = lineView.measure.heights = [];if (wrapping) {
        lineView.measure.width = curWidth;var rects = lineView.text.firstChild.getClientRects();for (var i = 0; i < rects.length - 1; i++) {
          var cur = rects[i],
              next = rects[i + 1];if (Math.abs(cur.bottom - next.bottom) > 2) {
            heights.push((cur.bottom + next.top) / 2 - rect.top);
          }
        }
      }heights.push(rect.bottom - rect.top);
    }
  }function mapFromLineView(lineView, line, lineN) {
    if (lineView.line == line) {
      return { map: lineView.measure.map, cache: lineView.measure.cache };
    }for (var i = 0; i < lineView.rest.length; i++) {
      if (lineView.rest[i] == line) {
        return { map: lineView.measure.maps[i], cache: lineView.measure.caches[i] };
      }
    }for (var i$1 = 0; i$1 < lineView.rest.length; i$1++) {
      if (lineNo(lineView.rest[i$1]) > lineN) {
        return { map: lineView.measure.maps[i$1], cache: lineView.measure.caches[i$1], before: true };
      }
    }
  }function updateExternalMeasurement(cm, line) {
    line = visualLine(line);var lineN = lineNo(line);var view = cm.display.externalMeasured = new LineView(cm.doc, line, lineN);view.lineN = lineN;var built = view.built = buildLineContent(cm, view);view.text = built.pre;removeChildrenAndAdd(cm.display.lineMeasure, built.pre);return view;
  }function measureChar(cm, line, ch, bias) {
    return measureCharPrepared(cm, prepareMeasureForLine(cm, line), ch, bias);
  }function findViewForLine(cm, lineN) {
    if (lineN >= cm.display.viewFrom && lineN < cm.display.viewTo) {
      return cm.display.view[findViewIndex(cm, lineN)];
    }var ext = cm.display.externalMeasured;if (ext && lineN >= ext.lineN && lineN < ext.lineN + ext.size) {
      return ext;
    }
  }function prepareMeasureForLine(cm, line) {
    var lineN = lineNo(line);var view = findViewForLine(cm, lineN);if (view && !view.text) {
      view = null;
    } else if (view && view.changes) {
      updateLineForChanges(cm, view, lineN, getDimensions(cm));cm.curOp.forceUpdate = true;
    }if (!view) {
      view = updateExternalMeasurement(cm, line);
    }var info = mapFromLineView(view, line, lineN);return { line: line, view: view, rect: null, map: info.map, cache: info.cache, before: info.before, hasHeights: false };
  }function measureCharPrepared(cm, prepared, ch, bias, varHeight) {
    if (prepared.before) {
      ch = -1;
    }var key = ch + (bias || ""),
        found;if (prepared.cache.hasOwnProperty(key)) {
      found = prepared.cache[key];
    } else {
      if (!prepared.rect) {
        prepared.rect = prepared.view.text.getBoundingClientRect();
      }if (!prepared.hasHeights) {
        ensureLineHeights(cm, prepared.view, prepared.rect);prepared.hasHeights = true;
      }found = measureCharInner(cm, prepared, ch, bias);if (!found.bogus) {
        prepared.cache[key] = found;
      }
    }return { left: found.left, right: found.right, top: varHeight ? found.rtop : found.top, bottom: varHeight ? found.rbottom : found.bottom };
  }var nullRect = { left: 0, right: 0, top: 0, bottom: 0 };function nodeAndOffsetInLineMap(map$$1, ch, bias) {
    var node, start, end, collapse, mStart, mEnd;for (var i = 0; i < map$$1.length; i += 3) {
      mStart = map$$1[i];mEnd = map$$1[i + 1];if (ch < mStart) {
        start = 0;end = 1;collapse = "left";
      } else if (ch < mEnd) {
        start = ch - mStart;end = start + 1;
      } else if (i == map$$1.length - 3 || ch == mEnd && map$$1[i + 3] > ch) {
        end = mEnd - mStart;start = end - 1;if (ch >= mEnd) {
          collapse = "right";
        }
      }if (start != null) {
        node = map$$1[i + 2];if (mStart == mEnd && bias == (node.insertLeft ? "left" : "right")) {
          collapse = bias;
        }if (bias == "left" && start == 0) {
          while (i && map$$1[i - 2] == map$$1[i - 3] && map$$1[i - 1].insertLeft) {
            node = map$$1[(i -= 3) + 2];collapse = "left";
          }
        }if (bias == "right" && start == mEnd - mStart) {
          while (i < map$$1.length - 3 && map$$1[i + 3] == map$$1[i + 4] && !map$$1[i + 5].insertLeft) {
            node = map$$1[(i += 3) + 2];collapse = "right";
          }
        }break;
      }
    }return { node: node, start: start, end: end, collapse: collapse, coverStart: mStart, coverEnd: mEnd };
  }function getUsefulRect(rects, bias) {
    var rect = nullRect;if (bias == "left") {
      for (var i = 0; i < rects.length; i++) {
        if ((rect = rects[i]).left != rect.right) {
          break;
        }
      }
    } else {
      for (var i$1 = rects.length - 1; i$1 >= 0; i$1--) {
        if ((rect = rects[i$1]).left != rect.right) {
          break;
        }
      }
    }return rect;
  }function measureCharInner(cm, prepared, ch, bias) {
    var place = nodeAndOffsetInLineMap(prepared.map, ch, bias);var node = place.node,
        start = place.start,
        end = place.end,
        collapse = place.collapse;var rect;if (node.nodeType == 3) {
      for (var i$1 = 0; i$1 < 4; i$1++) {
        while (start && isExtendingChar(prepared.line.text.charAt(place.coverStart + start))) {
          --start;
        }while (place.coverStart + end < place.coverEnd && isExtendingChar(prepared.line.text.charAt(place.coverStart + end))) {
          ++end;
        }if (ie && ie_version < 9 && start == 0 && end == place.coverEnd - place.coverStart) {
          rect = node.parentNode.getBoundingClientRect();
        } else {
          rect = getUsefulRect(range(node, start, end).getClientRects(), bias);
        }if (rect.left || rect.right || start == 0) {
          break;
        }end = start;start = start - 1;collapse = "right";
      }if (ie && ie_version < 11) {
        rect = maybeUpdateRectForZooming(cm.display.measure, rect);
      }
    } else {
      if (start > 0) {
        collapse = bias = "right";
      }var rects;if (cm.options.lineWrapping && (rects = node.getClientRects()).length > 1) {
        rect = rects[bias == "right" ? rects.length - 1 : 0];
      } else {
        rect = node.getBoundingClientRect();
      }
    }if (ie && ie_version < 9 && !start && (!rect || !rect.left && !rect.right)) {
      var rSpan = node.parentNode.getClientRects()[0];if (rSpan) {
        rect = { left: rSpan.left, right: rSpan.left + charWidth(cm.display), top: rSpan.top, bottom: rSpan.bottom };
      } else {
        rect = nullRect;
      }
    }var rtop = rect.top - prepared.rect.top,
        rbot = rect.bottom - prepared.rect.top;var mid = (rtop + rbot) / 2;var heights = prepared.view.measure.heights;var i = 0;for (; i < heights.length - 1; i++) {
      if (mid < heights[i]) {
        break;
      }
    }var top = i ? heights[i - 1] : 0,
        bot = heights[i];var result = { left: (collapse == "right" ? rect.right : rect.left) - prepared.rect.left, right: (collapse == "left" ? rect.left : rect.right) - prepared.rect.left, top: top, bottom: bot };if (!rect.left && !rect.right) {
      result.bogus = true;
    }if (!cm.options.singleCursorHeightPerLine) {
      result.rtop = rtop;result.rbottom = rbot;
    }return result;
  }function maybeUpdateRectForZooming(measure, rect) {
    if (!window.screen || screen.logicalXDPI == null || screen.logicalXDPI == screen.deviceXDPI || !hasBadZoomedRects(measure)) {
      return rect;
    }var scaleX = screen.logicalXDPI / screen.deviceXDPI;var scaleY = screen.logicalYDPI / screen.deviceYDPI;return { left: rect.left * scaleX, right: rect.right * scaleX, top: rect.top * scaleY, bottom: rect.bottom * scaleY };
  }function clearLineMeasurementCacheFor(lineView) {
    if (lineView.measure) {
      lineView.measure.cache = {};lineView.measure.heights = null;if (lineView.rest) {
        for (var i = 0; i < lineView.rest.length; i++) {
          lineView.measure.caches[i] = {};
        }
      }
    }
  }function clearLineMeasurementCache(cm) {
    cm.display.externalMeasure = null;removeChildren(cm.display.lineMeasure);for (var i = 0; i < cm.display.view.length; i++) {
      clearLineMeasurementCacheFor(cm.display.view[i]);
    }
  }function clearCaches(cm) {
    clearLineMeasurementCache(cm);cm.display.cachedCharWidth = cm.display.cachedTextHeight = cm.display.cachedPaddingH = null;if (!cm.options.lineWrapping) {
      cm.display.maxLineChanged = true;
    }cm.display.lineNumChars = null;
  }function pageScrollX() {
    if (chrome && android) {
      return -(document.body.getBoundingClientRect().left - parseInt(getComputedStyle(document.body).marginLeft));
    }return window.pageXOffset || (document.documentElement || document.body).scrollLeft;
  }function pageScrollY() {
    if (chrome && android) {
      return -(document.body.getBoundingClientRect().top - parseInt(getComputedStyle(document.body).marginTop));
    }return window.pageYOffset || (document.documentElement || document.body).scrollTop;
  }function widgetTopHeight(lineObj) {
    var height = 0;if (lineObj.widgets) {
      for (var i = 0; i < lineObj.widgets.length; ++i) {
        if (lineObj.widgets[i].above) {
          height += widgetHeight(lineObj.widgets[i]);
        }
      }
    }return height;
  }function intoCoordSystem(cm, lineObj, rect, context, includeWidgets) {
    if (!includeWidgets) {
      var height = widgetTopHeight(lineObj);rect.top += height;rect.bottom += height;
    }if (context == "line") {
      return rect;
    }if (!context) {
      context = "local";
    }var yOff = _heightAtLine(lineObj);if (context == "local") {
      yOff += paddingTop(cm.display);
    } else {
      yOff -= cm.display.viewOffset;
    }if (context == "page" || context == "window") {
      var lOff = cm.display.lineSpace.getBoundingClientRect();yOff += lOff.top + (context == "window" ? 0 : pageScrollY());var xOff = lOff.left + (context == "window" ? 0 : pageScrollX());rect.left += xOff;rect.right += xOff;
    }rect.top += yOff;rect.bottom += yOff;return rect;
  }function fromCoordSystem(cm, coords, context) {
    if (context == "div") {
      return coords;
    }var left = coords.left,
        top = coords.top;if (context == "page") {
      left -= pageScrollX();top -= pageScrollY();
    } else if (context == "local" || !context) {
      var localBox = cm.display.sizer.getBoundingClientRect();left += localBox.left;top += localBox.top;
    }var lineSpaceBox = cm.display.lineSpace.getBoundingClientRect();return { left: left - lineSpaceBox.left, top: top - lineSpaceBox.top };
  }function _charCoords(cm, pos, context, lineObj, bias) {
    if (!lineObj) {
      lineObj = getLine(cm.doc, pos.line);
    }return intoCoordSystem(cm, lineObj, measureChar(cm, lineObj, pos.ch, bias), context);
  }function _cursorCoords(cm, pos, context, lineObj, preparedMeasure, varHeight) {
    lineObj = lineObj || getLine(cm.doc, pos.line);if (!preparedMeasure) {
      preparedMeasure = prepareMeasureForLine(cm, lineObj);
    }function get(ch, right) {
      var m = measureCharPrepared(cm, preparedMeasure, ch, right ? "right" : "left", varHeight);if (right) {
        m.left = m.right;
      } else {
        m.right = m.left;
      }return intoCoordSystem(cm, lineObj, m, context);
    }var order = getOrder(lineObj, cm.doc.direction),
        ch = pos.ch,
        sticky = pos.sticky;if (ch >= lineObj.text.length) {
      ch = lineObj.text.length;sticky = "before";
    } else if (ch <= 0) {
      ch = 0;sticky = "after";
    }if (!order) {
      return get(sticky == "before" ? ch - 1 : ch, sticky == "before");
    }function getBidi(ch, partPos, invert) {
      var part = order[partPos],
          right = part.level == 1;return get(invert ? ch - 1 : ch, right != invert);
    }var partPos = getBidiPartAt(order, ch, sticky);var other = bidiOther;var val = getBidi(ch, partPos, sticky == "before");if (other != null) {
      val.other = getBidi(ch, other, sticky != "before");
    }return val;
  }function estimateCoords(cm, pos) {
    var left = 0;pos = _clipPos(cm.doc, pos);if (!cm.options.lineWrapping) {
      left = charWidth(cm.display) * pos.ch;
    }var lineObj = getLine(cm.doc, pos.line);var top = _heightAtLine(lineObj) + paddingTop(cm.display);return { left: left, right: left, top: top, bottom: top + lineObj.height };
  }function PosWithInfo(line, ch, sticky, outside, xRel) {
    var pos = Pos(line, ch, sticky);pos.xRel = xRel;if (outside) {
      pos.outside = outside;
    }return pos;
  }function _coordsChar(cm, x, y) {
    var doc = cm.doc;y += cm.display.viewOffset;if (y < 0) {
      return PosWithInfo(doc.first, 0, null, -1, -1);
    }var lineN = _lineAtHeight(doc, y),
        last = doc.first + doc.size - 1;if (lineN > last) {
      return PosWithInfo(doc.first + doc.size - 1, getLine(doc, last).text.length, null, 1, 1);
    }if (x < 0) {
      x = 0;
    }var lineObj = getLine(doc, lineN);for (;;) {
      var found = coordsCharInner(cm, lineObj, lineN, x, y);var collapsed = collapsedSpanAround(lineObj, found.ch + (found.xRel > 0 || found.outside > 0 ? 1 : 0));if (!collapsed) {
        return found;
      }var rangeEnd = collapsed.find(1);if (rangeEnd.line == lineN) {
        return rangeEnd;
      }lineObj = getLine(doc, lineN = rangeEnd.line);
    }
  }function wrappedLineExtent(cm, lineObj, preparedMeasure, y) {
    y -= widgetTopHeight(lineObj);var end = lineObj.text.length;var begin = findFirst(function (ch) {
      return measureCharPrepared(cm, preparedMeasure, ch - 1).bottom <= y;
    }, end, 0);end = findFirst(function (ch) {
      return measureCharPrepared(cm, preparedMeasure, ch).top > y;
    }, begin, end);return { begin: begin, end: end };
  }function wrappedLineExtentChar(cm, lineObj, preparedMeasure, target) {
    if (!preparedMeasure) {
      preparedMeasure = prepareMeasureForLine(cm, lineObj);
    }var targetTop = intoCoordSystem(cm, lineObj, measureCharPrepared(cm, preparedMeasure, target), "line").top;return wrappedLineExtent(cm, lineObj, preparedMeasure, targetTop);
  }function boxIsAfter(box, x, y, left) {
    return box.bottom <= y ? false : box.top > y ? true : (left ? box.left : box.right) > x;
  }function coordsCharInner(cm, lineObj, lineNo$$1, x, y) {
    y -= _heightAtLine(lineObj);var preparedMeasure = prepareMeasureForLine(cm, lineObj);var widgetHeight$$1 = widgetTopHeight(lineObj);var begin = 0,
        end = lineObj.text.length,
        ltr = true;var order = getOrder(lineObj, cm.doc.direction);if (order) {
      var part = (cm.options.lineWrapping ? coordsBidiPartWrapped : coordsBidiPart)(cm, lineObj, lineNo$$1, preparedMeasure, order, x, y);ltr = part.level != 1;begin = ltr ? part.from : part.to - 1;end = ltr ? part.to : part.from - 1;
    }var chAround = null,
        boxAround = null;var ch = findFirst(function (ch) {
      var box = measureCharPrepared(cm, preparedMeasure, ch);box.top += widgetHeight$$1;box.bottom += widgetHeight$$1;if (!boxIsAfter(box, x, y, false)) {
        return false;
      }if (box.top <= y && box.left <= x) {
        chAround = ch;boxAround = box;
      }return true;
    }, begin, end);var baseX,
        sticky,
        outside = false;if (boxAround) {
      var atLeft = x - boxAround.left < boxAround.right - x,
          atStart = atLeft == ltr;ch = chAround + (atStart ? 0 : 1);sticky = atStart ? "after" : "before";baseX = atLeft ? boxAround.left : boxAround.right;
    } else {
      if (!ltr && (ch == end || ch == begin)) {
        ch++;
      }sticky = ch == 0 ? "after" : ch == lineObj.text.length ? "before" : measureCharPrepared(cm, preparedMeasure, ch - (ltr ? 1 : 0)).bottom + widgetHeight$$1 <= y == ltr ? "after" : "before";var coords = _cursorCoords(cm, Pos(lineNo$$1, ch, sticky), "line", lineObj, preparedMeasure);baseX = coords.left;outside = y < coords.top ? -1 : y >= coords.bottom ? 1 : 0;
    }ch = skipExtendingChars(lineObj.text, ch, 1);return PosWithInfo(lineNo$$1, ch, sticky, outside, x - baseX);
  }function coordsBidiPart(cm, lineObj, lineNo$$1, preparedMeasure, order, x, y) {
    var index = findFirst(function (i) {
      var part = order[i],
          ltr = part.level != 1;return boxIsAfter(_cursorCoords(cm, Pos(lineNo$$1, ltr ? part.to : part.from, ltr ? "before" : "after"), "line", lineObj, preparedMeasure), x, y, true);
    }, 0, order.length - 1);var part = order[index];if (index > 0) {
      var ltr = part.level != 1;var start = _cursorCoords(cm, Pos(lineNo$$1, ltr ? part.from : part.to, ltr ? "after" : "before"), "line", lineObj, preparedMeasure);if (boxIsAfter(start, x, y, true) && start.top > y) {
        part = order[index - 1];
      }
    }return part;
  }function coordsBidiPartWrapped(cm, lineObj, _lineNo, preparedMeasure, order, x, y) {
    var ref = wrappedLineExtent(cm, lineObj, preparedMeasure, y);var begin = ref.begin;var end = ref.end;if (/\s/.test(lineObj.text.charAt(end - 1))) {
      end--;
    }var part = null,
        closestDist = null;for (var i = 0; i < order.length; i++) {
      var p = order[i];if (p.from >= end || p.to <= begin) {
        continue;
      }var ltr = p.level != 1;var endX = measureCharPrepared(cm, preparedMeasure, ltr ? Math.min(end, p.to) - 1 : Math.max(begin, p.from)).right;var dist = endX < x ? x - endX + 1e9 : endX - x;if (!part || closestDist > dist) {
        part = p;closestDist = dist;
      }
    }if (!part) {
      part = order[order.length - 1];
    }if (part.from < begin) {
      part = { from: begin, to: part.to, level: part.level };
    }if (part.to > end) {
      part = { from: part.from, to: end, level: part.level };
    }return part;
  }var measureText;function textHeight(display) {
    if (display.cachedTextHeight != null) {
      return display.cachedTextHeight;
    }if (measureText == null) {
      measureText = elt("pre", null, "CodeMirror-line-like");for (var i = 0; i < 49; ++i) {
        measureText.appendChild(document.createTextNode("x"));measureText.appendChild(elt("br"));
      }measureText.appendChild(document.createTextNode("x"));
    }removeChildrenAndAdd(display.measure, measureText);var height = measureText.offsetHeight / 50;if (height > 3) {
      display.cachedTextHeight = height;
    }removeChildren(display.measure);return height || 1;
  }function charWidth(display) {
    if (display.cachedCharWidth != null) {
      return display.cachedCharWidth;
    }var anchor = elt("span", "xxxxxxxxxx");var pre = elt("pre", [anchor], "CodeMirror-line-like");removeChildrenAndAdd(display.measure, pre);var rect = anchor.getBoundingClientRect(),
        width = (rect.right - rect.left) / 10;if (width > 2) {
      display.cachedCharWidth = width;
    }return width || 10;
  }function getDimensions(cm) {
    var d = cm.display,
        left = {},
        width = {};var gutterLeft = d.gutters.clientLeft;for (var n = d.gutters.firstChild, i = 0; n; n = n.nextSibling, ++i) {
      var id = cm.display.gutterSpecs[i].className;left[id] = n.offsetLeft + n.clientLeft + gutterLeft;width[id] = n.clientWidth;
    }return { fixedPos: compensateForHScroll(d), gutterTotalWidth: d.gutters.offsetWidth, gutterLeft: left, gutterWidth: width, wrapperWidth: d.wrapper.clientWidth };
  }function compensateForHScroll(display) {
    return display.scroller.getBoundingClientRect().left - display.sizer.getBoundingClientRect().left;
  }function estimateHeight(cm) {
    var th = textHeight(cm.display),
        wrapping = cm.options.lineWrapping;var perLine = wrapping && Math.max(5, cm.display.scroller.clientWidth / charWidth(cm.display) - 3);return function (line) {
      if (lineIsHidden(cm.doc, line)) {
        return 0;
      }var widgetsHeight = 0;if (line.widgets) {
        for (var i = 0; i < line.widgets.length; i++) {
          if (line.widgets[i].height) {
            widgetsHeight += line.widgets[i].height;
          }
        }
      }if (wrapping) {
        return widgetsHeight + (Math.ceil(line.text.length / perLine) || 1) * th;
      } else {
        return widgetsHeight + th;
      }
    };
  }function estimateLineHeights(cm) {
    var doc = cm.doc,
        est = estimateHeight(cm);doc.iter(function (line) {
      var estHeight = est(line);if (estHeight != line.height) {
        updateLineHeight(line, estHeight);
      }
    });
  }function posFromMouse(cm, e, liberal, forRect) {
    var display = cm.display;if (!liberal && e_target(e).getAttribute("cm-not-content") == "true") {
      return null;
    }var x,
        y,
        space = display.lineSpace.getBoundingClientRect();try {
      x = e.clientX - space.left;y = e.clientY - space.top;
    } catch (e) {
      return null;
    }var coords = _coordsChar(cm, x, y),
        line;if (forRect && coords.xRel == 1 && (line = getLine(cm.doc, coords.line).text).length == coords.ch) {
      var colDiff = countColumn(line, line.length, cm.options.tabSize) - line.length;coords = Pos(coords.line, Math.max(0, Math.round((x - paddingH(cm.display).left) / charWidth(cm.display)) - colDiff));
    }return coords;
  }function findViewIndex(cm, n) {
    if (n >= cm.display.viewTo) {
      return null;
    }n -= cm.display.viewFrom;if (n < 0) {
      return null;
    }var view = cm.display.view;for (var i = 0; i < view.length; i++) {
      n -= view[i].size;if (n < 0) {
        return i;
      }
    }
  }function regChange(cm, from, to, lendiff) {
    if (from == null) {
      from = cm.doc.first;
    }if (to == null) {
      to = cm.doc.first + cm.doc.size;
    }if (!lendiff) {
      lendiff = 0;
    }var display = cm.display;if (lendiff && to < display.viewTo && (display.updateLineNumbers == null || display.updateLineNumbers > from)) {
      display.updateLineNumbers = from;
    }cm.curOp.viewChanged = true;if (from >= display.viewTo) {
      if (sawCollapsedSpans && visualLineNo(cm.doc, from) < display.viewTo) {
        resetView(cm);
      }
    } else if (to <= display.viewFrom) {
      if (sawCollapsedSpans && visualLineEndNo(cm.doc, to + lendiff) > display.viewFrom) {
        resetView(cm);
      } else {
        display.viewFrom += lendiff;display.viewTo += lendiff;
      }
    } else if (from <= display.viewFrom && to >= display.viewTo) {
      resetView(cm);
    } else if (from <= display.viewFrom) {
      var cut = viewCuttingPoint(cm, to, to + lendiff, 1);if (cut) {
        display.view = display.view.slice(cut.index);display.viewFrom = cut.lineN;display.viewTo += lendiff;
      } else {
        resetView(cm);
      }
    } else if (to >= display.viewTo) {
      var cut$1 = viewCuttingPoint(cm, from, from, -1);if (cut$1) {
        display.view = display.view.slice(0, cut$1.index);display.viewTo = cut$1.lineN;
      } else {
        resetView(cm);
      }
    } else {
      var cutTop = viewCuttingPoint(cm, from, from, -1);var cutBot = viewCuttingPoint(cm, to, to + lendiff, 1);if (cutTop && cutBot) {
        display.view = display.view.slice(0, cutTop.index).concat(buildViewArray(cm, cutTop.lineN, cutBot.lineN)).concat(display.view.slice(cutBot.index));display.viewTo += lendiff;
      } else {
        resetView(cm);
      }
    }var ext = display.externalMeasured;if (ext) {
      if (to < ext.lineN) {
        ext.lineN += lendiff;
      } else if (from < ext.lineN + ext.size) {
        display.externalMeasured = null;
      }
    }
  }function regLineChange(cm, line, type) {
    cm.curOp.viewChanged = true;var display = cm.display,
        ext = cm.display.externalMeasured;if (ext && line >= ext.lineN && line < ext.lineN + ext.size) {
      display.externalMeasured = null;
    }if (line < display.viewFrom || line >= display.viewTo) {
      return;
    }var lineView = display.view[findViewIndex(cm, line)];if (lineView.node == null) {
      return;
    }var arr = lineView.changes || (lineView.changes = []);if (indexOf(arr, type) == -1) {
      arr.push(type);
    }
  }function resetView(cm) {
    cm.display.viewFrom = cm.display.viewTo = cm.doc.first;cm.display.view = [];cm.display.viewOffset = 0;
  }function viewCuttingPoint(cm, oldN, newN, dir) {
    var index = findViewIndex(cm, oldN),
        diff,
        view = cm.display.view;if (!sawCollapsedSpans || newN == cm.doc.first + cm.doc.size) {
      return { index: index, lineN: newN };
    }var n = cm.display.viewFrom;for (var i = 0; i < index; i++) {
      n += view[i].size;
    }if (n != oldN) {
      if (dir > 0) {
        if (index == view.length - 1) {
          return null;
        }diff = n + view[index].size - oldN;index++;
      } else {
        diff = n - oldN;
      }oldN += diff;newN += diff;
    }while (visualLineNo(cm.doc, newN) != newN) {
      if (index == (dir < 0 ? 0 : view.length - 1)) {
        return null;
      }newN += dir * view[index - (dir < 0 ? 1 : 0)].size;index += dir;
    }return { index: index, lineN: newN };
  }function adjustView(cm, from, to) {
    var display = cm.display,
        view = display.view;if (view.length == 0 || from >= display.viewTo || to <= display.viewFrom) {
      display.view = buildViewArray(cm, from, to);display.viewFrom = from;
    } else {
      if (display.viewFrom > from) {
        display.view = buildViewArray(cm, from, display.viewFrom).concat(display.view);
      } else if (display.viewFrom < from) {
        display.view = display.view.slice(findViewIndex(cm, from));
      }display.viewFrom = from;if (display.viewTo < to) {
        display.view = display.view.concat(buildViewArray(cm, display.viewTo, to));
      } else if (display.viewTo > to) {
        display.view = display.view.slice(0, findViewIndex(cm, to));
      }
    }display.viewTo = to;
  }function countDirtyView(cm) {
    var view = cm.display.view,
        dirty = 0;for (var i = 0; i < view.length; i++) {
      var lineView = view[i];if (!lineView.hidden && (!lineView.node || lineView.changes)) {
        ++dirty;
      }
    }return dirty;
  }function updateSelection(cm) {
    cm.display.input.showSelection(cm.display.input.prepareSelection());
  }function prepareSelection(cm, primary) {
    if (primary === void 0) primary = true;var doc = cm.doc,
        result = {};var curFragment = result.cursors = document.createDocumentFragment();var selFragment = result.selection = document.createDocumentFragment();for (var i = 0; i < doc.sel.ranges.length; i++) {
      if (!primary && i == doc.sel.primIndex) {
        continue;
      }var range$$1 = doc.sel.ranges[i];if (range$$1.from().line >= cm.display.viewTo || range$$1.to().line < cm.display.viewFrom) {
        continue;
      }var collapsed = range$$1.empty();if (collapsed || cm.options.showCursorWhenSelecting) {
        drawSelectionCursor(cm, range$$1.head, curFragment);
      }if (!collapsed) {
        drawSelectionRange(cm, range$$1, selFragment);
      }
    }return result;
  }function drawSelectionCursor(cm, head, output) {
    var pos = _cursorCoords(cm, head, "div", null, null, !cm.options.singleCursorHeightPerLine);var cursor = output.appendChild(elt("div", " ", "CodeMirror-cursor"));cursor.style.left = pos.left + "px";cursor.style.top = pos.top + "px";cursor.style.height = Math.max(0, pos.bottom - pos.top) * cm.options.cursorHeight + "px";if (pos.other) {
      var otherCursor = output.appendChild(elt("div", " ", "CodeMirror-cursor CodeMirror-secondarycursor"));otherCursor.style.display = "";otherCursor.style.left = pos.other.left + "px";otherCursor.style.top = pos.other.top + "px";otherCursor.style.height = (pos.other.bottom - pos.other.top) * .85 + "px";
    }
  }function cmpCoords(a, b) {
    return a.top - b.top || a.left - b.left;
  }function drawSelectionRange(cm, range$$1, output) {
    var display = cm.display,
        doc = cm.doc;var fragment = document.createDocumentFragment();var padding = paddingH(cm.display),
        leftSide = padding.left;var rightSide = Math.max(display.sizerWidth, displayWidth(cm) - display.sizer.offsetLeft) - padding.right;var docLTR = doc.direction == "ltr";function add(left, top, width, bottom) {
      if (top < 0) {
        top = 0;
      }top = Math.round(top);bottom = Math.round(bottom);fragment.appendChild(elt("div", null, "CodeMirror-selected", "position: absolute; left: " + left + "px;\n                             top: " + top + "px; width: " + (width == null ? rightSide - left : width) + "px;\n                             height: " + (bottom - top) + "px"));
    }function drawForLine(line, fromArg, toArg) {
      var lineObj = getLine(doc, line);var lineLen = lineObj.text.length;var start, end;function coords(ch, bias) {
        return _charCoords(cm, Pos(line, ch), "div", lineObj, bias);
      }function wrapX(pos, dir, side) {
        var extent = wrappedLineExtentChar(cm, lineObj, null, pos);var prop = dir == "ltr" == (side == "after") ? "left" : "right";var ch = side == "after" ? extent.begin : extent.end - (/\s/.test(lineObj.text.charAt(extent.end - 1)) ? 2 : 1);return coords(ch, prop)[prop];
      }var order = getOrder(lineObj, doc.direction);iterateBidiSections(order, fromArg || 0, toArg == null ? lineLen : toArg, function (from, to, dir, i) {
        var ltr = dir == "ltr";var fromPos = coords(from, ltr ? "left" : "right");var toPos = coords(to - 1, ltr ? "right" : "left");var openStart = fromArg == null && from == 0,
            openEnd = toArg == null && to == lineLen;var first = i == 0,
            last = !order || i == order.length - 1;if (toPos.top - fromPos.top <= 3) {
          var openLeft = (docLTR ? openStart : openEnd) && first;var openRight = (docLTR ? openEnd : openStart) && last;var left = openLeft ? leftSide : (ltr ? fromPos : toPos).left;var right = openRight ? rightSide : (ltr ? toPos : fromPos).right;add(left, fromPos.top, right - left, fromPos.bottom);
        } else {
          var topLeft, topRight, botLeft, botRight;if (ltr) {
            topLeft = docLTR && openStart && first ? leftSide : fromPos.left;topRight = docLTR ? rightSide : wrapX(from, dir, "before");botLeft = docLTR ? leftSide : wrapX(to, dir, "after");botRight = docLTR && openEnd && last ? rightSide : toPos.right;
          } else {
            topLeft = !docLTR ? leftSide : wrapX(from, dir, "before");topRight = !docLTR && openStart && first ? rightSide : fromPos.right;botLeft = !docLTR && openEnd && last ? leftSide : toPos.left;botRight = !docLTR ? rightSide : wrapX(to, dir, "after");
          }add(topLeft, fromPos.top, topRight - topLeft, fromPos.bottom);if (fromPos.bottom < toPos.top) {
            add(leftSide, fromPos.bottom, null, toPos.top);
          }add(botLeft, toPos.top, botRight - botLeft, toPos.bottom);
        }if (!start || cmpCoords(fromPos, start) < 0) {
          start = fromPos;
        }if (cmpCoords(toPos, start) < 0) {
          start = toPos;
        }if (!end || cmpCoords(fromPos, end) < 0) {
          end = fromPos;
        }if (cmpCoords(toPos, end) < 0) {
          end = toPos;
        }
      });return { start: start, end: end };
    }var sFrom = range$$1.from(),
        sTo = range$$1.to();if (sFrom.line == sTo.line) {
      drawForLine(sFrom.line, sFrom.ch, sTo.ch);
    } else {
      var fromLine = getLine(doc, sFrom.line),
          toLine = getLine(doc, sTo.line);var singleVLine = visualLine(fromLine) == visualLine(toLine);var leftEnd = drawForLine(sFrom.line, sFrom.ch, singleVLine ? fromLine.text.length + 1 : null).end;var rightStart = drawForLine(sTo.line, singleVLine ? 0 : null, sTo.ch).start;if (singleVLine) {
        if (leftEnd.top < rightStart.top - 2) {
          add(leftEnd.right, leftEnd.top, null, leftEnd.bottom);add(leftSide, rightStart.top, rightStart.left, rightStart.bottom);
        } else {
          add(leftEnd.right, leftEnd.top, rightStart.left - leftEnd.right, leftEnd.bottom);
        }
      }if (leftEnd.bottom < rightStart.top) {
        add(leftSide, leftEnd.bottom, null, rightStart.top);
      }
    }output.appendChild(fragment);
  }function restartBlink(cm) {
    if (!cm.state.focused) {
      return;
    }var display = cm.display;clearInterval(display.blinker);var on = true;display.cursorDiv.style.visibility = "";if (cm.options.cursorBlinkRate > 0) {
      display.blinker = setInterval(function () {
        return display.cursorDiv.style.visibility = (on = !on) ? "" : "hidden";
      }, cm.options.cursorBlinkRate);
    } else if (cm.options.cursorBlinkRate < 0) {
      display.cursorDiv.style.visibility = "hidden";
    }
  }function ensureFocus(cm) {
    if (!cm.state.focused) {
      cm.display.input.focus();onFocus(cm);
    }
  }function delayBlurEvent(cm) {
    cm.state.delayingBlurEvent = true;setTimeout(function () {
      if (cm.state.delayingBlurEvent) {
        cm.state.delayingBlurEvent = false;onBlur(cm);
      }
    }, 100);
  }function onFocus(cm, e) {
    if (cm.state.delayingBlurEvent) {
      cm.state.delayingBlurEvent = false;
    }if (cm.options.readOnly == "nocursor") {
      return;
    }if (!cm.state.focused) {
      signal(cm, "focus", cm, e);cm.state.focused = true;addClass(cm.display.wrapper, "CodeMirror-focused");if (!cm.curOp && cm.display.selForContextMenu != cm.doc.sel) {
        cm.display.input.reset();if (webkit) {
          setTimeout(function () {
            return cm.display.input.reset(true);
          }, 20);
        }
      }cm.display.input.receivedFocus();
    }restartBlink(cm);
  }function onBlur(cm, e) {
    if (cm.state.delayingBlurEvent) {
      return;
    }if (cm.state.focused) {
      signal(cm, "blur", cm, e);cm.state.focused = false;rmClass(cm.display.wrapper, "CodeMirror-focused");
    }clearInterval(cm.display.blinker);setTimeout(function () {
      if (!cm.state.focused) {
        cm.display.shift = false;
      }
    }, 150);
  }function updateHeightsInViewport(cm) {
    var display = cm.display;var prevBottom = display.lineDiv.offsetTop;for (var i = 0; i < display.view.length; i++) {
      var cur = display.view[i],
          wrapping = cm.options.lineWrapping;var height = void 0,
          width = 0;if (cur.hidden) {
        continue;
      }if (ie && ie_version < 8) {
        var bot = cur.node.offsetTop + cur.node.offsetHeight;height = bot - prevBottom;prevBottom = bot;
      } else {
        var box = cur.node.getBoundingClientRect();height = box.bottom - box.top;if (!wrapping && cur.text.firstChild) {
          width = cur.text.firstChild.getBoundingClientRect().right - box.left - 1;
        }
      }var diff = cur.line.height - height;if (diff > .005 || diff < -.005) {
        updateLineHeight(cur.line, height);updateWidgetHeight(cur.line);if (cur.rest) {
          for (var j = 0; j < cur.rest.length; j++) {
            updateWidgetHeight(cur.rest[j]);
          }
        }
      }if (width > cm.display.sizerWidth) {
        var chWidth = Math.ceil(width / charWidth(cm.display));if (chWidth > cm.display.maxLineLength) {
          cm.display.maxLineLength = chWidth;cm.display.maxLine = cur.line;cm.display.maxLineChanged = true;
        }
      }
    }
  }function updateWidgetHeight(line) {
    if (line.widgets) {
      for (var i = 0; i < line.widgets.length; ++i) {
        var w = line.widgets[i],
            parent = w.node.parentNode;if (parent) {
          w.height = parent.offsetHeight;
        }
      }
    }
  }function visibleLines(display, doc, viewport) {
    var top = viewport && viewport.top != null ? Math.max(0, viewport.top) : display.scroller.scrollTop;top = Math.floor(top - paddingTop(display));var bottom = viewport && viewport.bottom != null ? viewport.bottom : top + display.wrapper.clientHeight;var from = _lineAtHeight(doc, top),
        to = _lineAtHeight(doc, bottom);if (viewport && viewport.ensure) {
      var ensureFrom = viewport.ensure.from.line,
          ensureTo = viewport.ensure.to.line;if (ensureFrom < from) {
        from = ensureFrom;to = _lineAtHeight(doc, _heightAtLine(getLine(doc, ensureFrom)) + display.wrapper.clientHeight);
      } else if (Math.min(ensureTo, doc.lastLine()) >= to) {
        from = _lineAtHeight(doc, _heightAtLine(getLine(doc, ensureTo)) - display.wrapper.clientHeight);to = ensureTo;
      }
    }return { from: from, to: Math.max(to, from + 1) };
  }function maybeScrollWindow(cm, rect) {
    if (signalDOMEvent(cm, "scrollCursorIntoView")) {
      return;
    }var display = cm.display,
        box = display.sizer.getBoundingClientRect(),
        doScroll = null;if (rect.top + box.top < 0) {
      doScroll = true;
    } else if (rect.bottom + box.top > (window.innerHeight || document.documentElement.clientHeight)) {
      doScroll = false;
    }if (doScroll != null && !phantom) {
      var scrollNode = elt("div", "​", null, "position: absolute;\n                         top: " + (rect.top - display.viewOffset - paddingTop(cm.display)) + "px;\n                         height: " + (rect.bottom - rect.top + scrollGap(cm) + display.barHeight) + "px;\n                         left: " + rect.left + "px; width: " + Math.max(2, rect.right - rect.left) + "px;");cm.display.lineSpace.appendChild(scrollNode);scrollNode.scrollIntoView(doScroll);cm.display.lineSpace.removeChild(scrollNode);
    }
  }function scrollPosIntoView(cm, pos, end, margin) {
    if (margin == null) {
      margin = 0;
    }var rect;if (!cm.options.lineWrapping && pos == end) {
      pos = pos.ch ? Pos(pos.line, pos.sticky == "before" ? pos.ch - 1 : pos.ch, "after") : pos;end = pos.sticky == "before" ? Pos(pos.line, pos.ch + 1, "before") : pos;
    }for (var limit = 0; limit < 5; limit++) {
      var changed = false;var coords = _cursorCoords(cm, pos);var endCoords = !end || end == pos ? coords : _cursorCoords(cm, end);rect = { left: Math.min(coords.left, endCoords.left), top: Math.min(coords.top, endCoords.top) - margin, right: Math.max(coords.left, endCoords.left), bottom: Math.max(coords.bottom, endCoords.bottom) + margin };var scrollPos = calculateScrollPos(cm, rect);var startTop = cm.doc.scrollTop,
          startLeft = cm.doc.scrollLeft;if (scrollPos.scrollTop != null) {
        updateScrollTop(cm, scrollPos.scrollTop);if (Math.abs(cm.doc.scrollTop - startTop) > 1) {
          changed = true;
        }
      }if (scrollPos.scrollLeft != null) {
        setScrollLeft(cm, scrollPos.scrollLeft);if (Math.abs(cm.doc.scrollLeft - startLeft) > 1) {
          changed = true;
        }
      }if (!changed) {
        break;
      }
    }return rect;
  }function scrollIntoView(cm, rect) {
    var scrollPos = calculateScrollPos(cm, rect);if (scrollPos.scrollTop != null) {
      updateScrollTop(cm, scrollPos.scrollTop);
    }if (scrollPos.scrollLeft != null) {
      setScrollLeft(cm, scrollPos.scrollLeft);
    }
  }function calculateScrollPos(cm, rect) {
    var display = cm.display,
        snapMargin = textHeight(cm.display);if (rect.top < 0) {
      rect.top = 0;
    }var screentop = cm.curOp && cm.curOp.scrollTop != null ? cm.curOp.scrollTop : display.scroller.scrollTop;var screen = displayHeight(cm),
        result = {};if (rect.bottom - rect.top > screen) {
      rect.bottom = rect.top + screen;
    }var docBottom = cm.doc.height + paddingVert(display);var atTop = rect.top < snapMargin,
        atBottom = rect.bottom > docBottom - snapMargin;if (rect.top < screentop) {
      result.scrollTop = atTop ? 0 : rect.top;
    } else if (rect.bottom > screentop + screen) {
      var newTop = Math.min(rect.top, (atBottom ? docBottom : rect.bottom) - screen);if (newTop != screentop) {
        result.scrollTop = newTop;
      }
    }var screenleft = cm.curOp && cm.curOp.scrollLeft != null ? cm.curOp.scrollLeft : display.scroller.scrollLeft;var screenw = displayWidth(cm) - (cm.options.fixedGutter ? display.gutters.offsetWidth : 0);var tooWide = rect.right - rect.left > screenw;if (tooWide) {
      rect.right = rect.left + screenw;
    }if (rect.left < 10) {
      result.scrollLeft = 0;
    } else if (rect.left < screenleft) {
      result.scrollLeft = Math.max(0, rect.left - (tooWide ? 0 : 10));
    } else if (rect.right > screenw + screenleft - 3) {
      result.scrollLeft = rect.right + (tooWide ? 0 : 10) - screenw;
    }return result;
  }function addToScrollTop(cm, top) {
    if (top == null) {
      return;
    }resolveScrollToPos(cm);cm.curOp.scrollTop = (cm.curOp.scrollTop == null ? cm.doc.scrollTop : cm.curOp.scrollTop) + top;
  }function ensureCursorVisible(cm) {
    resolveScrollToPos(cm);var cur = cm.getCursor();cm.curOp.scrollToPos = { from: cur, to: cur, margin: cm.options.cursorScrollMargin };
  }function scrollToCoords(cm, x, y) {
    if (x != null || y != null) {
      resolveScrollToPos(cm);
    }if (x != null) {
      cm.curOp.scrollLeft = x;
    }if (y != null) {
      cm.curOp.scrollTop = y;
    }
  }function scrollToRange(cm, range$$1) {
    resolveScrollToPos(cm);cm.curOp.scrollToPos = range$$1;
  }function resolveScrollToPos(cm) {
    var range$$1 = cm.curOp.scrollToPos;if (range$$1) {
      cm.curOp.scrollToPos = null;var from = estimateCoords(cm, range$$1.from),
          to = estimateCoords(cm, range$$1.to);scrollToCoordsRange(cm, from, to, range$$1.margin);
    }
  }function scrollToCoordsRange(cm, from, to, margin) {
    var sPos = calculateScrollPos(cm, { left: Math.min(from.left, to.left), top: Math.min(from.top, to.top) - margin, right: Math.max(from.right, to.right), bottom: Math.max(from.bottom, to.bottom) + margin });scrollToCoords(cm, sPos.scrollLeft, sPos.scrollTop);
  }function updateScrollTop(cm, val) {
    if (Math.abs(cm.doc.scrollTop - val) < 2) {
      return;
    }if (!gecko) {
      updateDisplaySimple(cm, { top: val });
    }setScrollTop(cm, val, true);if (gecko) {
      updateDisplaySimple(cm);
    }startWorker(cm, 100);
  }function setScrollTop(cm, val, forceScroll) {
    val = Math.min(cm.display.scroller.scrollHeight - cm.display.scroller.clientHeight, val);if (cm.display.scroller.scrollTop == val && !forceScroll) {
      return;
    }cm.doc.scrollTop = val;cm.display.scrollbars.setScrollTop(val);if (cm.display.scroller.scrollTop != val) {
      cm.display.scroller.scrollTop = val;
    }
  }function setScrollLeft(cm, val, isScroller, forceScroll) {
    val = Math.min(val, cm.display.scroller.scrollWidth - cm.display.scroller.clientWidth);if ((isScroller ? val == cm.doc.scrollLeft : Math.abs(cm.doc.scrollLeft - val) < 2) && !forceScroll) {
      return;
    }cm.doc.scrollLeft = val;alignHorizontally(cm);if (cm.display.scroller.scrollLeft != val) {
      cm.display.scroller.scrollLeft = val;
    }cm.display.scrollbars.setScrollLeft(val);
  }function measureForScrollbars(cm) {
    var d = cm.display,
        gutterW = d.gutters.offsetWidth;var docH = Math.round(cm.doc.height + paddingVert(cm.display));return { clientHeight: d.scroller.clientHeight, viewHeight: d.wrapper.clientHeight, scrollWidth: d.scroller.scrollWidth, clientWidth: d.scroller.clientWidth, viewWidth: d.wrapper.clientWidth, barLeft: cm.options.fixedGutter ? gutterW : 0, docHeight: docH, scrollHeight: docH + scrollGap(cm) + d.barHeight, nativeBarWidth: d.nativeBarWidth, gutterWidth: gutterW };
  }var NativeScrollbars = function NativeScrollbars(place, scroll, cm) {
    this.cm = cm;var vert = this.vert = elt("div", [elt("div", null, null, "min-width: 1px")], "CodeMirror-vscrollbar");var horiz = this.horiz = elt("div", [elt("div", null, null, "height: 100%; min-height: 1px")], "CodeMirror-hscrollbar");vert.tabIndex = horiz.tabIndex = -1;place(vert);place(horiz);on(vert, "scroll", function () {
      if (vert.clientHeight) {
        scroll(vert.scrollTop, "vertical");
      }
    });on(horiz, "scroll", function () {
      if (horiz.clientWidth) {
        scroll(horiz.scrollLeft, "horizontal");
      }
    });this.checkedZeroWidth = false;if (ie && ie_version < 8) {
      this.horiz.style.minHeight = this.vert.style.minWidth = "18px";
    }
  };NativeScrollbars.prototype.update = function (measure) {
    var needsH = measure.scrollWidth > measure.clientWidth + 1;var needsV = measure.scrollHeight > measure.clientHeight + 1;var sWidth = measure.nativeBarWidth;if (needsV) {
      this.vert.style.display = "block";this.vert.style.bottom = needsH ? sWidth + "px" : "0";var totalHeight = measure.viewHeight - (needsH ? sWidth : 0);this.vert.firstChild.style.height = Math.max(0, measure.scrollHeight - measure.clientHeight + totalHeight) + "px";
    } else {
      this.vert.style.display = "";this.vert.firstChild.style.height = "0";
    }if (needsH) {
      this.horiz.style.display = "block";this.horiz.style.right = needsV ? sWidth + "px" : "0";this.horiz.style.left = measure.barLeft + "px";var totalWidth = measure.viewWidth - measure.barLeft - (needsV ? sWidth : 0);this.horiz.firstChild.style.width = Math.max(0, measure.scrollWidth - measure.clientWidth + totalWidth) + "px";
    } else {
      this.horiz.style.display = "";this.horiz.firstChild.style.width = "0";
    }if (!this.checkedZeroWidth && measure.clientHeight > 0) {
      if (sWidth == 0) {
        this.zeroWidthHack();
      }this.checkedZeroWidth = true;
    }return { right: needsV ? sWidth : 0, bottom: needsH ? sWidth : 0 };
  };NativeScrollbars.prototype.setScrollLeft = function (pos) {
    if (this.horiz.scrollLeft != pos) {
      this.horiz.scrollLeft = pos;
    }if (this.disableHoriz) {
      this.enableZeroWidthBar(this.horiz, this.disableHoriz, "horiz");
    }
  };NativeScrollbars.prototype.setScrollTop = function (pos) {
    if (this.vert.scrollTop != pos) {
      this.vert.scrollTop = pos;
    }if (this.disableVert) {
      this.enableZeroWidthBar(this.vert, this.disableVert, "vert");
    }
  };NativeScrollbars.prototype.zeroWidthHack = function () {
    var w = mac && !mac_geMountainLion ? "12px" : "18px";this.horiz.style.height = this.vert.style.width = w;this.horiz.style.pointerEvents = this.vert.style.pointerEvents = "none";this.disableHoriz = new Delayed();this.disableVert = new Delayed();
  };NativeScrollbars.prototype.enableZeroWidthBar = function (bar, delay, type) {
    bar.style.pointerEvents = "auto";function maybeDisable() {
      var box = bar.getBoundingClientRect();var elt$$1 = type == "vert" ? document.elementFromPoint(box.right - 1, (box.top + box.bottom) / 2) : document.elementFromPoint((box.right + box.left) / 2, box.bottom - 1);if (elt$$1 != bar) {
        bar.style.pointerEvents = "none";
      } else {
        delay.set(1e3, maybeDisable);
      }
    }delay.set(1e3, maybeDisable);
  };NativeScrollbars.prototype.clear = function () {
    var parent = this.horiz.parentNode;parent.removeChild(this.horiz);parent.removeChild(this.vert);
  };var NullScrollbars = function NullScrollbars() {};NullScrollbars.prototype.update = function () {
    return { bottom: 0, right: 0 };
  };NullScrollbars.prototype.setScrollLeft = function () {};NullScrollbars.prototype.setScrollTop = function () {};NullScrollbars.prototype.clear = function () {};function updateScrollbars(cm, measure) {
    if (!measure) {
      measure = measureForScrollbars(cm);
    }var startWidth = cm.display.barWidth,
        startHeight = cm.display.barHeight;updateScrollbarsInner(cm, measure);for (var i = 0; i < 4 && startWidth != cm.display.barWidth || startHeight != cm.display.barHeight; i++) {
      if (startWidth != cm.display.barWidth && cm.options.lineWrapping) {
        updateHeightsInViewport(cm);
      }updateScrollbarsInner(cm, measureForScrollbars(cm));startWidth = cm.display.barWidth;startHeight = cm.display.barHeight;
    }
  }function updateScrollbarsInner(cm, measure) {
    var d = cm.display;var sizes = d.scrollbars.update(measure);d.sizer.style.paddingRight = (d.barWidth = sizes.right) + "px";
    d.sizer.style.paddingBottom = (d.barHeight = sizes.bottom) + "px";d.heightForcer.style.borderBottom = sizes.bottom + "px solid transparent";if (sizes.right && sizes.bottom) {
      d.scrollbarFiller.style.display = "block";d.scrollbarFiller.style.height = sizes.bottom + "px";d.scrollbarFiller.style.width = sizes.right + "px";
    } else {
      d.scrollbarFiller.style.display = "";
    }if (sizes.bottom && cm.options.coverGutterNextToScrollbar && cm.options.fixedGutter) {
      d.gutterFiller.style.display = "block";d.gutterFiller.style.height = sizes.bottom + "px";d.gutterFiller.style.width = measure.gutterWidth + "px";
    } else {
      d.gutterFiller.style.display = "";
    }
  }var scrollbarModel = { native: NativeScrollbars, null: NullScrollbars };function initScrollbars(cm) {
    if (cm.display.scrollbars) {
      cm.display.scrollbars.clear();if (cm.display.scrollbars.addClass) {
        rmClass(cm.display.wrapper, cm.display.scrollbars.addClass);
      }
    }cm.display.scrollbars = new scrollbarModel[cm.options.scrollbarStyle](function (node) {
      cm.display.wrapper.insertBefore(node, cm.display.scrollbarFiller);on(node, "mousedown", function () {
        if (cm.state.focused) {
          setTimeout(function () {
            return cm.display.input.focus();
          }, 0);
        }
      });node.setAttribute("cm-not-content", "true");
    }, function (pos, axis) {
      if (axis == "horizontal") {
        setScrollLeft(cm, pos);
      } else {
        updateScrollTop(cm, pos);
      }
    }, cm);if (cm.display.scrollbars.addClass) {
      addClass(cm.display.wrapper, cm.display.scrollbars.addClass);
    }
  }var nextOpId = 0;function _startOperation(cm) {
    cm.curOp = { cm: cm, viewChanged: false, startHeight: cm.doc.height, forceUpdate: false, updateInput: 0, typing: false, changeObjs: null, cursorActivityHandlers: null, cursorActivityCalled: 0, selectionChanged: false, updateMaxLine: false, scrollLeft: null, scrollTop: null, scrollToPos: null, focus: false, id: ++nextOpId };pushOperation(cm.curOp);
  }function _endOperation(cm) {
    var op = cm.curOp;if (op) {
      finishOperation(op, function (group) {
        for (var i = 0; i < group.ops.length; i++) {
          group.ops[i].cm.curOp = null;
        }endOperations(group);
      });
    }
  }function endOperations(group) {
    var ops = group.ops;for (var i = 0; i < ops.length; i++) {
      endOperation_R1(ops[i]);
    }for (var i$1 = 0; i$1 < ops.length; i$1++) {
      endOperation_W1(ops[i$1]);
    }for (var i$2 = 0; i$2 < ops.length; i$2++) {
      endOperation_R2(ops[i$2]);
    }for (var i$3 = 0; i$3 < ops.length; i$3++) {
      endOperation_W2(ops[i$3]);
    }for (var i$4 = 0; i$4 < ops.length; i$4++) {
      endOperation_finish(ops[i$4]);
    }
  }function endOperation_R1(op) {
    var cm = op.cm,
        display = cm.display;maybeClipScrollbars(cm);if (op.updateMaxLine) {
      findMaxLine(cm);
    }op.mustUpdate = op.viewChanged || op.forceUpdate || op.scrollTop != null || op.scrollToPos && (op.scrollToPos.from.line < display.viewFrom || op.scrollToPos.to.line >= display.viewTo) || display.maxLineChanged && cm.options.lineWrapping;op.update = op.mustUpdate && new DisplayUpdate(cm, op.mustUpdate && { top: op.scrollTop, ensure: op.scrollToPos }, op.forceUpdate);
  }function endOperation_W1(op) {
    op.updatedDisplay = op.mustUpdate && updateDisplayIfNeeded(op.cm, op.update);
  }function endOperation_R2(op) {
    var cm = op.cm,
        display = cm.display;if (op.updatedDisplay) {
      updateHeightsInViewport(cm);
    }op.barMeasure = measureForScrollbars(cm);if (display.maxLineChanged && !cm.options.lineWrapping) {
      op.adjustWidthTo = measureChar(cm, display.maxLine, display.maxLine.text.length).left + 3;cm.display.sizerWidth = op.adjustWidthTo;op.barMeasure.scrollWidth = Math.max(display.scroller.clientWidth, display.sizer.offsetLeft + op.adjustWidthTo + scrollGap(cm) + cm.display.barWidth);op.maxScrollLeft = Math.max(0, display.sizer.offsetLeft + op.adjustWidthTo - displayWidth(cm));
    }if (op.updatedDisplay || op.selectionChanged) {
      op.preparedSelection = display.input.prepareSelection();
    }
  }function endOperation_W2(op) {
    var cm = op.cm;if (op.adjustWidthTo != null) {
      cm.display.sizer.style.minWidth = op.adjustWidthTo + "px";if (op.maxScrollLeft < cm.doc.scrollLeft) {
        setScrollLeft(cm, Math.min(cm.display.scroller.scrollLeft, op.maxScrollLeft), true);
      }cm.display.maxLineChanged = false;
    }var takeFocus = op.focus && op.focus == activeElt();if (op.preparedSelection) {
      cm.display.input.showSelection(op.preparedSelection, takeFocus);
    }if (op.updatedDisplay || op.startHeight != cm.doc.height) {
      updateScrollbars(cm, op.barMeasure);
    }if (op.updatedDisplay) {
      setDocumentHeight(cm, op.barMeasure);
    }if (op.selectionChanged) {
      restartBlink(cm);
    }if (cm.state.focused && op.updateInput) {
      cm.display.input.reset(op.typing);
    }if (takeFocus) {
      ensureFocus(op.cm);
    }
  }function endOperation_finish(op) {
    var cm = op.cm,
        display = cm.display,
        doc = cm.doc;if (op.updatedDisplay) {
      postUpdateDisplay(cm, op.update);
    }if (display.wheelStartX != null && (op.scrollTop != null || op.scrollLeft != null || op.scrollToPos)) {
      display.wheelStartX = display.wheelStartY = null;
    }if (op.scrollTop != null) {
      setScrollTop(cm, op.scrollTop, op.forceScroll);
    }if (op.scrollLeft != null) {
      setScrollLeft(cm, op.scrollLeft, true, true);
    }if (op.scrollToPos) {
      var rect = scrollPosIntoView(cm, _clipPos(doc, op.scrollToPos.from), _clipPos(doc, op.scrollToPos.to), op.scrollToPos.margin);maybeScrollWindow(cm, rect);
    }var hidden = op.maybeHiddenMarkers,
        unhidden = op.maybeUnhiddenMarkers;if (hidden) {
      for (var i = 0; i < hidden.length; ++i) {
        if (!hidden[i].lines.length) {
          signal(hidden[i], "hide");
        }
      }
    }if (unhidden) {
      for (var i$1 = 0; i$1 < unhidden.length; ++i$1) {
        if (unhidden[i$1].lines.length) {
          signal(unhidden[i$1], "unhide");
        }
      }
    }if (display.wrapper.offsetHeight) {
      doc.scrollTop = cm.display.scroller.scrollTop;
    }if (op.changeObjs) {
      signal(cm, "changes", cm, op.changeObjs);
    }if (op.update) {
      op.update.finish();
    }
  }function runInOp(cm, f) {
    if (cm.curOp) {
      return f();
    }_startOperation(cm);try {
      return f();
    } finally {
      _endOperation(cm);
    }
  }function operation(cm, f) {
    return function () {
      if (cm.curOp) {
        return f.apply(cm, arguments);
      }_startOperation(cm);try {
        return f.apply(cm, arguments);
      } finally {
        _endOperation(cm);
      }
    };
  }function methodOp(f) {
    return function () {
      if (this.curOp) {
        return f.apply(this, arguments);
      }_startOperation(this);try {
        return f.apply(this, arguments);
      } finally {
        _endOperation(this);
      }
    };
  }function docMethodOp(f) {
    return function () {
      var cm = this.cm;if (!cm || cm.curOp) {
        return f.apply(this, arguments);
      }_startOperation(cm);try {
        return f.apply(this, arguments);
      } finally {
        _endOperation(cm);
      }
    };
  }function startWorker(cm, time) {
    if (cm.doc.highlightFrontier < cm.display.viewTo) {
      cm.state.highlight.set(time, bind(highlightWorker, cm));
    }
  }function highlightWorker(cm) {
    var doc = cm.doc;if (doc.highlightFrontier >= cm.display.viewTo) {
      return;
    }var end = +new Date() + cm.options.workTime;var context = getContextBefore(cm, doc.highlightFrontier);var changedLines = [];doc.iter(context.line, Math.min(doc.first + doc.size, cm.display.viewTo + 500), function (line) {
      if (context.line >= cm.display.viewFrom) {
        var oldStyles = line.styles;var resetState = line.text.length > cm.options.maxHighlightLength ? copyState(doc.mode, context.state) : null;var highlighted = highlightLine(cm, line, context, true);if (resetState) {
          context.state = resetState;
        }line.styles = highlighted.styles;var oldCls = line.styleClasses,
            newCls = highlighted.classes;if (newCls) {
          line.styleClasses = newCls;
        } else if (oldCls) {
          line.styleClasses = null;
        }var ischange = !oldStyles || oldStyles.length != line.styles.length || oldCls != newCls && (!oldCls || !newCls || oldCls.bgClass != newCls.bgClass || oldCls.textClass != newCls.textClass);for (var i = 0; !ischange && i < oldStyles.length; ++i) {
          ischange = oldStyles[i] != line.styles[i];
        }if (ischange) {
          changedLines.push(context.line);
        }line.stateAfter = context.save();context.nextLine();
      } else {
        if (line.text.length <= cm.options.maxHighlightLength) {
          processLine(cm, line.text, context);
        }line.stateAfter = context.line % 5 == 0 ? context.save() : null;context.nextLine();
      }if (+new Date() > end) {
        startWorker(cm, cm.options.workDelay);return true;
      }
    });doc.highlightFrontier = context.line;doc.modeFrontier = Math.max(doc.modeFrontier, context.line);if (changedLines.length) {
      runInOp(cm, function () {
        for (var i = 0; i < changedLines.length; i++) {
          regLineChange(cm, changedLines[i], "text");
        }
      });
    }
  }var DisplayUpdate = function DisplayUpdate(cm, viewport, force) {
    var display = cm.display;this.viewport = viewport;this.visible = visibleLines(display, cm.doc, viewport);this.editorIsHidden = !display.wrapper.offsetWidth;this.wrapperHeight = display.wrapper.clientHeight;this.wrapperWidth = display.wrapper.clientWidth;this.oldDisplayWidth = displayWidth(cm);this.force = force;this.dims = getDimensions(cm);this.events = [];
  };DisplayUpdate.prototype.signal = function (emitter, type) {
    if (hasHandler(emitter, type)) {
      this.events.push(arguments);
    }
  };DisplayUpdate.prototype.finish = function () {
    for (var i = 0; i < this.events.length; i++) {
      signal.apply(null, this.events[i]);
    }
  };function maybeClipScrollbars(cm) {
    var display = cm.display;if (!display.scrollbarsClipped && display.scroller.offsetWidth) {
      display.nativeBarWidth = display.scroller.offsetWidth - display.scroller.clientWidth;display.heightForcer.style.height = scrollGap(cm) + "px";display.sizer.style.marginBottom = -display.nativeBarWidth + "px";display.sizer.style.borderRightWidth = scrollGap(cm) + "px";display.scrollbarsClipped = true;
    }
  }function selectionSnapshot(cm) {
    if (cm.hasFocus()) {
      return null;
    }var active = activeElt();if (!active || !contains(cm.display.lineDiv, active)) {
      return null;
    }var result = { activeElt: active };if (window.getSelection) {
      var sel = window.getSelection();if (sel.anchorNode && sel.extend && contains(cm.display.lineDiv, sel.anchorNode)) {
        result.anchorNode = sel.anchorNode;result.anchorOffset = sel.anchorOffset;result.focusNode = sel.focusNode;result.focusOffset = sel.focusOffset;
      }
    }return result;
  }function restoreSelection(snapshot) {
    if (!snapshot || !snapshot.activeElt || snapshot.activeElt == activeElt()) {
      return;
    }snapshot.activeElt.focus();if (snapshot.anchorNode && contains(document.body, snapshot.anchorNode) && contains(document.body, snapshot.focusNode)) {
      var sel = window.getSelection(),
          range$$1 = document.createRange();range$$1.setEnd(snapshot.anchorNode, snapshot.anchorOffset);range$$1.collapse(false);sel.removeAllRanges();sel.addRange(range$$1);sel.extend(snapshot.focusNode, snapshot.focusOffset);
    }
  }function updateDisplayIfNeeded(cm, update) {
    var display = cm.display,
        doc = cm.doc;if (update.editorIsHidden) {
      resetView(cm);return false;
    }if (!update.force && update.visible.from >= display.viewFrom && update.visible.to <= display.viewTo && (display.updateLineNumbers == null || display.updateLineNumbers >= display.viewTo) && display.renderedView == display.view && countDirtyView(cm) == 0) {
      return false;
    }if (maybeUpdateLineNumberWidth(cm)) {
      resetView(cm);update.dims = getDimensions(cm);
    }var end = doc.first + doc.size;var from = Math.max(update.visible.from - cm.options.viewportMargin, doc.first);var to = Math.min(end, update.visible.to + cm.options.viewportMargin);if (display.viewFrom < from && from - display.viewFrom < 20) {
      from = Math.max(doc.first, display.viewFrom);
    }if (display.viewTo > to && display.viewTo - to < 20) {
      to = Math.min(end, display.viewTo);
    }if (sawCollapsedSpans) {
      from = visualLineNo(cm.doc, from);to = visualLineEndNo(cm.doc, to);
    }var different = from != display.viewFrom || to != display.viewTo || display.lastWrapHeight != update.wrapperHeight || display.lastWrapWidth != update.wrapperWidth;adjustView(cm, from, to);display.viewOffset = _heightAtLine(getLine(cm.doc, display.viewFrom));cm.display.mover.style.top = display.viewOffset + "px";var toUpdate = countDirtyView(cm);if (!different && toUpdate == 0 && !update.force && display.renderedView == display.view && (display.updateLineNumbers == null || display.updateLineNumbers >= display.viewTo)) {
      return false;
    }var selSnapshot = selectionSnapshot(cm);if (toUpdate > 4) {
      display.lineDiv.style.display = "none";
    }patchDisplay(cm, display.updateLineNumbers, update.dims);if (toUpdate > 4) {
      display.lineDiv.style.display = "";
    }display.renderedView = display.view;restoreSelection(selSnapshot);removeChildren(display.cursorDiv);removeChildren(display.selectionDiv);display.gutters.style.height = display.sizer.style.minHeight = 0;if (different) {
      display.lastWrapHeight = update.wrapperHeight;display.lastWrapWidth = update.wrapperWidth;startWorker(cm, 400);
    }display.updateLineNumbers = null;return true;
  }function postUpdateDisplay(cm, update) {
    var viewport = update.viewport;for (var first = true;; first = false) {
      if (!first || !cm.options.lineWrapping || update.oldDisplayWidth == displayWidth(cm)) {
        if (viewport && viewport.top != null) {
          viewport = { top: Math.min(cm.doc.height + paddingVert(cm.display) - displayHeight(cm), viewport.top) };
        }update.visible = visibleLines(cm.display, cm.doc, viewport);if (update.visible.from >= cm.display.viewFrom && update.visible.to <= cm.display.viewTo) {
          break;
        }
      }if (!updateDisplayIfNeeded(cm, update)) {
        break;
      }updateHeightsInViewport(cm);var barMeasure = measureForScrollbars(cm);updateSelection(cm);updateScrollbars(cm, barMeasure);setDocumentHeight(cm, barMeasure);update.force = false;
    }update.signal(cm, "update", cm);if (cm.display.viewFrom != cm.display.reportedViewFrom || cm.display.viewTo != cm.display.reportedViewTo) {
      update.signal(cm, "viewportChange", cm, cm.display.viewFrom, cm.display.viewTo);cm.display.reportedViewFrom = cm.display.viewFrom;cm.display.reportedViewTo = cm.display.viewTo;
    }
  }function updateDisplaySimple(cm, viewport) {
    var update = new DisplayUpdate(cm, viewport);if (updateDisplayIfNeeded(cm, update)) {
      updateHeightsInViewport(cm);postUpdateDisplay(cm, update);var barMeasure = measureForScrollbars(cm);updateSelection(cm);updateScrollbars(cm, barMeasure);setDocumentHeight(cm, barMeasure);update.finish();
    }
  }function patchDisplay(cm, updateNumbersFrom, dims) {
    var display = cm.display,
        lineNumbers = cm.options.lineNumbers;var container = display.lineDiv,
        cur = container.firstChild;function rm(node) {
      var next = node.nextSibling;if (webkit && mac && cm.display.currentWheelTarget == node) {
        node.style.display = "none";
      } else {
        node.parentNode.removeChild(node);
      }return next;
    }var view = display.view,
        lineN = display.viewFrom;for (var i = 0; i < view.length; i++) {
      var lineView = view[i];if (lineView.hidden) ;else if (!lineView.node || lineView.node.parentNode != container) {
        var node = buildLineElement(cm, lineView, lineN, dims);container.insertBefore(node, cur);
      } else {
        while (cur != lineView.node) {
          cur = rm(cur);
        }var updateNumber = lineNumbers && updateNumbersFrom != null && updateNumbersFrom <= lineN && lineView.lineNumber;if (lineView.changes) {
          if (indexOf(lineView.changes, "gutter") > -1) {
            updateNumber = false;
          }updateLineForChanges(cm, lineView, lineN, dims);
        }if (updateNumber) {
          removeChildren(lineView.lineNumber);lineView.lineNumber.appendChild(document.createTextNode(lineNumberFor(cm.options, lineN)));
        }cur = lineView.node.nextSibling;
      }lineN += lineView.size;
    }while (cur) {
      cur = rm(cur);
    }
  }function updateGutterSpace(display) {
    var width = display.gutters.offsetWidth;display.sizer.style.marginLeft = width + "px";
  }function setDocumentHeight(cm, measure) {
    cm.display.sizer.style.minHeight = measure.docHeight + "px";cm.display.heightForcer.style.top = measure.docHeight + "px";cm.display.gutters.style.height = measure.docHeight + cm.display.barHeight + scrollGap(cm) + "px";
  }function alignHorizontally(cm) {
    var display = cm.display,
        view = display.view;if (!display.alignWidgets && (!display.gutters.firstChild || !cm.options.fixedGutter)) {
      return;
    }var comp = compensateForHScroll(display) - display.scroller.scrollLeft + cm.doc.scrollLeft;var gutterW = display.gutters.offsetWidth,
        left = comp + "px";for (var i = 0; i < view.length; i++) {
      if (!view[i].hidden) {
        if (cm.options.fixedGutter) {
          if (view[i].gutter) {
            view[i].gutter.style.left = left;
          }if (view[i].gutterBackground) {
            view[i].gutterBackground.style.left = left;
          }
        }var align = view[i].alignable;if (align) {
          for (var j = 0; j < align.length; j++) {
            align[j].style.left = left;
          }
        }
      }
    }if (cm.options.fixedGutter) {
      display.gutters.style.left = comp + gutterW + "px";
    }
  }function maybeUpdateLineNumberWidth(cm) {
    if (!cm.options.lineNumbers) {
      return false;
    }var doc = cm.doc,
        last = lineNumberFor(cm.options, doc.first + doc.size - 1),
        display = cm.display;if (last.length != display.lineNumChars) {
      var test = display.measure.appendChild(elt("div", [elt("div", last)], "CodeMirror-linenumber CodeMirror-gutter-elt"));var innerW = test.firstChild.offsetWidth,
          padding = test.offsetWidth - innerW;display.lineGutter.style.width = "";display.lineNumInnerWidth = Math.max(innerW, display.lineGutter.offsetWidth - padding) + 1;display.lineNumWidth = display.lineNumInnerWidth + padding;display.lineNumChars = display.lineNumInnerWidth ? last.length : -1;display.lineGutter.style.width = display.lineNumWidth + "px";updateGutterSpace(cm.display);return true;
    }return false;
  }function getGutters(gutters, lineNumbers) {
    var result = [],
        sawLineNumbers = false;for (var i = 0; i < gutters.length; i++) {
      var name = gutters[i],
          style = null;if (typeof name != "string") {
        style = name.style;name = name.className;
      }if (name == "CodeMirror-linenumbers") {
        if (!lineNumbers) {
          continue;
        } else {
          sawLineNumbers = true;
        }
      }result.push({ className: name, style: style });
    }if (lineNumbers && !sawLineNumbers) {
      result.push({ className: "CodeMirror-linenumbers", style: null });
    }return result;
  }function renderGutters(display) {
    var gutters = display.gutters,
        specs = display.gutterSpecs;removeChildren(gutters);display.lineGutter = null;for (var i = 0; i < specs.length; ++i) {
      var ref = specs[i];var className = ref.className;var style = ref.style;var gElt = gutters.appendChild(elt("div", null, "CodeMirror-gutter " + className));if (style) {
        gElt.style.cssText = style;
      }if (className == "CodeMirror-linenumbers") {
        display.lineGutter = gElt;gElt.style.width = (display.lineNumWidth || 1) + "px";
      }
    }gutters.style.display = specs.length ? "" : "none";updateGutterSpace(display);
  }function updateGutters(cm) {
    renderGutters(cm.display);regChange(cm);alignHorizontally(cm);
  }function Display(place, doc, input, options) {
    var d = this;this.input = input;d.scrollbarFiller = elt("div", null, "CodeMirror-scrollbar-filler");d.scrollbarFiller.setAttribute("cm-not-content", "true");d.gutterFiller = elt("div", null, "CodeMirror-gutter-filler");d.gutterFiller.setAttribute("cm-not-content", "true");d.lineDiv = eltP("div", null, "CodeMirror-code");d.selectionDiv = elt("div", null, null, "position: relative; z-index: 1");d.cursorDiv = elt("div", null, "CodeMirror-cursors");d.measure = elt("div", null, "CodeMirror-measure");d.lineMeasure = elt("div", null, "CodeMirror-measure");d.lineSpace = eltP("div", [d.measure, d.lineMeasure, d.selectionDiv, d.cursorDiv, d.lineDiv], null, "position: relative; outline: none");var lines = eltP("div", [d.lineSpace], "CodeMirror-lines");d.mover = elt("div", [lines], null, "position: relative");d.sizer = elt("div", [d.mover], "CodeMirror-sizer");d.sizerWidth = null;d.heightForcer = elt("div", null, null, "position: absolute; height: " + scrollerGap + "px; width: 1px;");d.gutters = elt("div", null, "CodeMirror-gutters");d.lineGutter = null;d.scroller = elt("div", [d.sizer, d.heightForcer, d.gutters], "CodeMirror-scroll");d.scroller.setAttribute("tabIndex", "-1");d.wrapper = elt("div", [d.scrollbarFiller, d.gutterFiller, d.scroller], "CodeMirror");if (ie && ie_version < 8) {
      d.gutters.style.zIndex = -1;d.scroller.style.paddingRight = 0;
    }if (!webkit && !(gecko && mobile)) {
      d.scroller.draggable = true;
    }if (place) {
      if (place.appendChild) {
        place.appendChild(d.wrapper);
      } else {
        place(d.wrapper);
      }
    }d.viewFrom = d.viewTo = doc.first;d.reportedViewFrom = d.reportedViewTo = doc.first;d.view = [];d.renderedView = null;d.externalMeasured = null;d.viewOffset = 0;d.lastWrapHeight = d.lastWrapWidth = 0;d.updateLineNumbers = null;d.nativeBarWidth = d.barHeight = d.barWidth = 0;d.scrollbarsClipped = false;d.lineNumWidth = d.lineNumInnerWidth = d.lineNumChars = null;d.alignWidgets = false;d.cachedCharWidth = d.cachedTextHeight = d.cachedPaddingH = null;d.maxLine = null;d.maxLineLength = 0;d.maxLineChanged = false;d.wheelDX = d.wheelDY = d.wheelStartX = d.wheelStartY = null;d.shift = false;d.selForContextMenu = null;d.activeTouch = null;d.gutterSpecs = getGutters(options.gutters, options.lineNumbers);renderGutters(d);input.init(d);
  }var wheelSamples = 0,
      wheelPixelsPerUnit = null;if (ie) {
    wheelPixelsPerUnit = -.53;
  } else if (gecko) {
    wheelPixelsPerUnit = 15;
  } else if (chrome) {
    wheelPixelsPerUnit = -.7;
  } else if (safari) {
    wheelPixelsPerUnit = -1 / 3;
  }function wheelEventDelta(e) {
    var dx = e.wheelDeltaX,
        dy = e.wheelDeltaY;if (dx == null && e.detail && e.axis == e.HORIZONTAL_AXIS) {
      dx = e.detail;
    }if (dy == null && e.detail && e.axis == e.VERTICAL_AXIS) {
      dy = e.detail;
    } else if (dy == null) {
      dy = e.wheelDelta;
    }return { x: dx, y: dy };
  }function wheelEventPixels(e) {
    var delta = wheelEventDelta(e);delta.x *= wheelPixelsPerUnit;delta.y *= wheelPixelsPerUnit;return delta;
  }function onScrollWheel(cm, e) {
    var delta = wheelEventDelta(e),
        dx = delta.x,
        dy = delta.y;var display = cm.display,
        scroll = display.scroller;var canScrollX = scroll.scrollWidth > scroll.clientWidth;var canScrollY = scroll.scrollHeight > scroll.clientHeight;if (!(dx && canScrollX || dy && canScrollY)) {
      return;
    }if (dy && mac && webkit) {
      outer: for (var cur = e.target, view = display.view; cur != scroll; cur = cur.parentNode) {
        for (var i = 0; i < view.length; i++) {
          if (view[i].node == cur) {
            cm.display.currentWheelTarget = cur;break outer;
          }
        }
      }
    }if (dx && !gecko && !presto && wheelPixelsPerUnit != null) {
      if (dy && canScrollY) {
        updateScrollTop(cm, Math.max(0, scroll.scrollTop + dy * wheelPixelsPerUnit));
      }setScrollLeft(cm, Math.max(0, scroll.scrollLeft + dx * wheelPixelsPerUnit));if (!dy || dy && canScrollY) {
        e_preventDefault(e);
      }display.wheelStartX = null;return;
    }if (dy && wheelPixelsPerUnit != null) {
      var pixels = dy * wheelPixelsPerUnit;var top = cm.doc.scrollTop,
          bot = top + display.wrapper.clientHeight;if (pixels < 0) {
        top = Math.max(0, top + pixels - 50);
      } else {
        bot = Math.min(cm.doc.height, bot + pixels + 50);
      }updateDisplaySimple(cm, { top: top, bottom: bot });
    }if (wheelSamples < 20) {
      if (display.wheelStartX == null) {
        display.wheelStartX = scroll.scrollLeft;display.wheelStartY = scroll.scrollTop;display.wheelDX = dx;display.wheelDY = dy;setTimeout(function () {
          if (display.wheelStartX == null) {
            return;
          }var movedX = scroll.scrollLeft - display.wheelStartX;var movedY = scroll.scrollTop - display.wheelStartY;var sample = movedY && display.wheelDY && movedY / display.wheelDY || movedX && display.wheelDX && movedX / display.wheelDX;display.wheelStartX = display.wheelStartY = null;if (!sample) {
            return;
          }wheelPixelsPerUnit = (wheelPixelsPerUnit * wheelSamples + sample) / (wheelSamples + 1);++wheelSamples;
        }, 200);
      } else {
        display.wheelDX += dx;display.wheelDY += dy;
      }
    }
  }var Selection = function Selection(ranges, primIndex) {
    this.ranges = ranges;this.primIndex = primIndex;
  };Selection.prototype.primary = function () {
    return this.ranges[this.primIndex];
  };Selection.prototype.equals = function (other) {
    if (other == this) {
      return true;
    }if (other.primIndex != this.primIndex || other.ranges.length != this.ranges.length) {
      return false;
    }for (var i = 0; i < this.ranges.length; i++) {
      var here = this.ranges[i],
          there = other.ranges[i];if (!equalCursorPos(here.anchor, there.anchor) || !equalCursorPos(here.head, there.head)) {
        return false;
      }
    }return true;
  };Selection.prototype.deepCopy = function () {
    var out = [];for (var i = 0; i < this.ranges.length; i++) {
      out[i] = new Range(copyPos(this.ranges[i].anchor), copyPos(this.ranges[i].head));
    }return new Selection(out, this.primIndex);
  };Selection.prototype.somethingSelected = function () {
    for (var i = 0; i < this.ranges.length; i++) {
      if (!this.ranges[i].empty()) {
        return true;
      }
    }return false;
  };Selection.prototype.contains = function (pos, end) {
    if (!end) {
      end = pos;
    }for (var i = 0; i < this.ranges.length; i++) {
      var range = this.ranges[i];if (cmp(end, range.from()) >= 0 && cmp(pos, range.to()) <= 0) {
        return i;
      }
    }return -1;
  };var Range = function Range(anchor, head) {
    this.anchor = anchor;this.head = head;
  };Range.prototype.from = function () {
    return minPos(this.anchor, this.head);
  };Range.prototype.to = function () {
    return maxPos(this.anchor, this.head);
  };Range.prototype.empty = function () {
    return this.head.line == this.anchor.line && this.head.ch == this.anchor.ch;
  };function normalizeSelection(cm, ranges, primIndex) {
    var mayTouch = cm && cm.options.selectionsMayTouch;var prim = ranges[primIndex];ranges.sort(function (a, b) {
      return cmp(a.from(), b.from());
    });primIndex = indexOf(ranges, prim);for (var i = 1; i < ranges.length; i++) {
      var cur = ranges[i],
          prev = ranges[i - 1];var diff = cmp(prev.to(), cur.from());if (mayTouch && !cur.empty() ? diff > 0 : diff >= 0) {
        var from = minPos(prev.from(), cur.from()),
            to = maxPos(prev.to(), cur.to());var inv = prev.empty() ? cur.from() == cur.head : prev.from() == prev.head;if (i <= primIndex) {
          --primIndex;
        }ranges.splice(--i, 2, new Range(inv ? to : from, inv ? from : to));
      }
    }return new Selection(ranges, primIndex);
  }function simpleSelection(anchor, head) {
    return new Selection([new Range(anchor, head || anchor)], 0);
  }function changeEnd(change) {
    if (!change.text) {
      return change.to;
    }return Pos(change.from.line + change.text.length - 1, lst(change.text).length + (change.text.length == 1 ? change.from.ch : 0));
  }function adjustForChange(pos, change) {
    if (cmp(pos, change.from) < 0) {
      return pos;
    }if (cmp(pos, change.to) <= 0) {
      return changeEnd(change);
    }var line = pos.line + change.text.length - (change.to.line - change.from.line) - 1,
        ch = pos.ch;if (pos.line == change.to.line) {
      ch += changeEnd(change).ch - change.to.ch;
    }return Pos(line, ch);
  }function computeSelAfterChange(doc, change) {
    var out = [];for (var i = 0; i < doc.sel.ranges.length; i++) {
      var range = doc.sel.ranges[i];out.push(new Range(adjustForChange(range.anchor, change), adjustForChange(range.head, change)));
    }return normalizeSelection(doc.cm, out, doc.sel.primIndex);
  }function offsetPos(pos, old, nw) {
    if (pos.line == old.line) {
      return Pos(nw.line, pos.ch - old.ch + nw.ch);
    } else {
      return Pos(nw.line + (pos.line - old.line), pos.ch);
    }
  }function computeReplacedSel(doc, changes, hint) {
    var out = [];var oldPrev = Pos(doc.first, 0),
        newPrev = oldPrev;for (var i = 0; i < changes.length; i++) {
      var change = changes[i];var from = offsetPos(change.from, oldPrev, newPrev);var to = offsetPos(changeEnd(change), oldPrev, newPrev);oldPrev = change.to;newPrev = to;if (hint == "around") {
        var range = doc.sel.ranges[i],
            inv = cmp(range.head, range.anchor) < 0;out[i] = new Range(inv ? to : from, inv ? from : to);
      } else {
        out[i] = new Range(from, from);
      }
    }return new Selection(out, doc.sel.primIndex);
  }function loadMode(cm) {
    cm.doc.mode = getMode(cm.options, cm.doc.modeOption);resetModeState(cm);
  }function resetModeState(cm) {
    cm.doc.iter(function (line) {
      if (line.stateAfter) {
        line.stateAfter = null;
      }if (line.styles) {
        line.styles = null;
      }
    });cm.doc.modeFrontier = cm.doc.highlightFrontier = cm.doc.first;startWorker(cm, 100);cm.state.modeGen++;if (cm.curOp) {
      regChange(cm);
    }
  }function isWholeLineUpdate(doc, change) {
    return change.from.ch == 0 && change.to.ch == 0 && lst(change.text) == "" && (!doc.cm || doc.cm.options.wholeLineUpdateBefore);
  }function updateDoc(doc, change, markedSpans, estimateHeight$$1) {
    function spansFor(n) {
      return markedSpans ? markedSpans[n] : null;
    }function update(line, text, spans) {
      updateLine(line, text, spans, estimateHeight$$1);signalLater(line, "change", line, change);
    }function linesFor(start, end) {
      var result = [];for (var i = start; i < end; ++i) {
        result.push(new Line(text[i], spansFor(i), estimateHeight$$1));
      }return result;
    }var from = change.from,
        to = change.to,
        text = change.text;var firstLine = getLine(doc, from.line),
        lastLine = getLine(doc, to.line);var lastText = lst(text),
        lastSpans = spansFor(text.length - 1),
        nlines = to.line - from.line;if (change.full) {
      doc.insert(0, linesFor(0, text.length));doc.remove(text.length, doc.size - text.length);
    } else if (isWholeLineUpdate(doc, change)) {
      var added = linesFor(0, text.length - 1);update(lastLine, lastLine.text, lastSpans);if (nlines) {
        doc.remove(from.line, nlines);
      }if (added.length) {
        doc.insert(from.line, added);
      }
    } else if (firstLine == lastLine) {
      if (text.length == 1) {
        update(firstLine, firstLine.text.slice(0, from.ch) + lastText + firstLine.text.slice(to.ch), lastSpans);
      } else {
        var added$1 = linesFor(1, text.length - 1);added$1.push(new Line(lastText + firstLine.text.slice(to.ch), lastSpans, estimateHeight$$1));update(firstLine, firstLine.text.slice(0, from.ch) + text[0], spansFor(0));doc.insert(from.line + 1, added$1);
      }
    } else if (text.length == 1) {
      update(firstLine, firstLine.text.slice(0, from.ch) + text[0] + lastLine.text.slice(to.ch), spansFor(0));doc.remove(from.line + 1, nlines);
    } else {
      update(firstLine, firstLine.text.slice(0, from.ch) + text[0], spansFor(0));update(lastLine, lastText + lastLine.text.slice(to.ch), lastSpans);var added$2 = linesFor(1, text.length - 1);if (nlines > 1) {
        doc.remove(from.line + 1, nlines - 1);
      }doc.insert(from.line + 1, added$2);
    }signalLater(doc, "change", doc, change);
  }function linkedDocs(doc, f, sharedHistOnly) {
    function propagate(doc, skip, sharedHist) {
      if (doc.linked) {
        for (var i = 0; i < doc.linked.length; ++i) {
          var rel = doc.linked[i];if (rel.doc == skip) {
            continue;
          }var shared = sharedHist && rel.sharedHist;if (sharedHistOnly && !shared) {
            continue;
          }f(rel.doc, shared);propagate(rel.doc, doc, shared);
        }
      }
    }propagate(doc, null, true);
  }function attachDoc(cm, doc) {
    if (doc.cm) {
      throw new Error("This document is already in use.");
    }cm.doc = doc;doc.cm = cm;estimateLineHeights(cm);loadMode(cm);setDirectionClass(cm);if (!cm.options.lineWrapping) {
      findMaxLine(cm);
    }cm.options.mode = doc.modeOption;regChange(cm);
  }function setDirectionClass(cm) {
    (cm.doc.direction == "rtl" ? addClass : rmClass)(cm.display.lineDiv, "CodeMirror-rtl");
  }function directionChanged(cm) {
    runInOp(cm, function () {
      setDirectionClass(cm);regChange(cm);
    });
  }function History(startGen) {
    this.done = [];this.undone = [];this.undoDepth = Infinity;this.lastModTime = this.lastSelTime = 0;this.lastOp = this.lastSelOp = null;this.lastOrigin = this.lastSelOrigin = null;this.generation = this.maxGeneration = startGen || 1;
  }function historyChangeFromChange(doc, change) {
    var histChange = { from: copyPos(change.from), to: changeEnd(change), text: getBetween(doc, change.from, change.to) };attachLocalSpans(doc, histChange, change.from.line, change.to.line + 1);linkedDocs(doc, function (doc) {
      return attachLocalSpans(doc, histChange, change.from.line, change.to.line + 1);
    }, true);return histChange;
  }function clearSelectionEvents(array) {
    while (array.length) {
      var last = lst(array);if (last.ranges) {
        array.pop();
      } else {
        break;
      }
    }
  }function lastChangeEvent(hist, force) {
    if (force) {
      clearSelectionEvents(hist.done);return lst(hist.done);
    } else if (hist.done.length && !lst(hist.done).ranges) {
      return lst(hist.done);
    } else if (hist.done.length > 1 && !hist.done[hist.done.length - 2].ranges) {
      hist.done.pop();return lst(hist.done);
    }
  }function addChangeToHistory(doc, change, selAfter, opId) {
    var hist = doc.history;hist.undone.length = 0;var time = +new Date(),
        cur;var last;if ((hist.lastOp == opId || hist.lastOrigin == change.origin && change.origin && (change.origin.charAt(0) == "+" && hist.lastModTime > time - (doc.cm ? doc.cm.options.historyEventDelay : 500) || change.origin.charAt(0) == "*")) && (cur = lastChangeEvent(hist, hist.lastOp == opId))) {
      last = lst(cur.changes);if (cmp(change.from, change.to) == 0 && cmp(change.from, last.to) == 0) {
        last.to = changeEnd(change);
      } else {
        cur.changes.push(historyChangeFromChange(doc, change));
      }
    } else {
      var before = lst(hist.done);if (!before || !before.ranges) {
        pushSelectionToHistory(doc.sel, hist.done);
      }cur = { changes: [historyChangeFromChange(doc, change)], generation: hist.generation };hist.done.push(cur);while (hist.done.length > hist.undoDepth) {
        hist.done.shift();if (!hist.done[0].ranges) {
          hist.done.shift();
        }
      }
    }hist.done.push(selAfter);hist.generation = ++hist.maxGeneration;hist.lastModTime = hist.lastSelTime = time;hist.lastOp = hist.lastSelOp = opId;hist.lastOrigin = hist.lastSelOrigin = change.origin;if (!last) {
      signal(doc, "historyAdded");
    }
  }function selectionEventCanBeMerged(doc, origin, prev, sel) {
    var ch = origin.charAt(0);return ch == "*" || ch == "+" && prev.ranges.length == sel.ranges.length && prev.somethingSelected() == sel.somethingSelected() && new Date() - doc.history.lastSelTime <= (doc.cm ? doc.cm.options.historyEventDelay : 500);
  }function addSelectionToHistory(doc, sel, opId, options) {
    var hist = doc.history,
        origin = options && options.origin;if (opId == hist.lastSelOp || origin && hist.lastSelOrigin == origin && (hist.lastModTime == hist.lastSelTime && hist.lastOrigin == origin || selectionEventCanBeMerged(doc, origin, lst(hist.done), sel))) {
      hist.done[hist.done.length - 1] = sel;
    } else {
      pushSelectionToHistory(sel, hist.done);
    }hist.lastSelTime = +new Date();hist.lastSelOrigin = origin;hist.lastSelOp = opId;if (options && options.clearRedo !== false) {
      clearSelectionEvents(hist.undone);
    }
  }function pushSelectionToHistory(sel, dest) {
    var top = lst(dest);if (!(top && top.ranges && top.equals(sel))) {
      dest.push(sel);
    }
  }function attachLocalSpans(doc, change, from, to) {
    var existing = change["spans_" + doc.id],
        n = 0;doc.iter(Math.max(doc.first, from), Math.min(doc.first + doc.size, to), function (line) {
      if (line.markedSpans) {
        (existing || (existing = change["spans_" + doc.id] = {}))[n] = line.markedSpans;
      }++n;
    });
  }function removeClearedSpans(spans) {
    if (!spans) {
      return null;
    }var out;for (var i = 0; i < spans.length; ++i) {
      if (spans[i].marker.explicitlyCleared) {
        if (!out) {
          out = spans.slice(0, i);
        }
      } else if (out) {
        out.push(spans[i]);
      }
    }return !out ? spans : out.length ? out : null;
  }function getOldSpans(doc, change) {
    var found = change["spans_" + doc.id];if (!found) {
      return null;
    }var nw = [];for (var i = 0; i < change.text.length; ++i) {
      nw.push(removeClearedSpans(found[i]));
    }return nw;
  }function mergeOldSpans(doc, change) {
    var old = getOldSpans(doc, change);var stretched = stretchSpansOverChange(doc, change);if (!old) {
      return stretched;
    }if (!stretched) {
      return old;
    }for (var i = 0; i < old.length; ++i) {
      var oldCur = old[i],
          stretchCur = stretched[i];if (oldCur && stretchCur) {
        spans: for (var j = 0; j < stretchCur.length; ++j) {
          var span = stretchCur[j];for (var k = 0; k < oldCur.length; ++k) {
            if (oldCur[k].marker == span.marker) {
              continue spans;
            }
          }oldCur.push(span);
        }
      } else if (stretchCur) {
        old[i] = stretchCur;
      }
    }return old;
  }function copyHistoryArray(events, newGroup, instantiateSel) {
    var copy = [];for (var i = 0; i < events.length; ++i) {
      var event = events[i];if (event.ranges) {
        copy.push(instantiateSel ? Selection.prototype.deepCopy.call(event) : event);continue;
      }var changes = event.changes,
          newChanges = [];copy.push({ changes: newChanges });for (var j = 0; j < changes.length; ++j) {
        var change = changes[j],
            m = void 0;newChanges.push({ from: change.from, to: change.to, text: change.text });if (newGroup) {
          for (var prop in change) {
            if (m = prop.match(/^spans_(\d+)$/)) {
              if (indexOf(newGroup, Number(m[1])) > -1) {
                lst(newChanges)[prop] = change[prop];delete change[prop];
              }
            }
          }
        }
      }
    }return copy;
  }function extendRange(range, head, other, extend) {
    if (extend) {
      var anchor = range.anchor;if (other) {
        var posBefore = cmp(head, anchor) < 0;if (posBefore != cmp(other, anchor) < 0) {
          anchor = head;head = other;
        } else if (posBefore != cmp(head, other) < 0) {
          head = other;
        }
      }return new Range(anchor, head);
    } else {
      return new Range(other || head, head);
    }
  }function extendSelection(doc, head, other, options, extend) {
    if (extend == null) {
      extend = doc.cm && (doc.cm.display.shift || doc.extend);
    }setSelection(doc, new Selection([extendRange(doc.sel.primary(), head, other, extend)], 0), options);
  }function extendSelections(doc, heads, options) {
    var out = [];var extend = doc.cm && (doc.cm.display.shift || doc.extend);for (var i = 0; i < doc.sel.ranges.length; i++) {
      out[i] = extendRange(doc.sel.ranges[i], heads[i], null, extend);
    }var newSel = normalizeSelection(doc.cm, out, doc.sel.primIndex);setSelection(doc, newSel, options);
  }function replaceOneSelection(doc, i, range, options) {
    var ranges = doc.sel.ranges.slice(0);ranges[i] = range;setSelection(doc, normalizeSelection(doc.cm, ranges, doc.sel.primIndex), options);
  }function setSimpleSelection(doc, anchor, head, options) {
    setSelection(doc, simpleSelection(anchor, head), options);
  }function filterSelectionChange(doc, sel, options) {
    var obj = { ranges: sel.ranges, update: function update(ranges) {
        this.ranges = [];for (var i = 0; i < ranges.length; i++) {
          this.ranges[i] = new Range(_clipPos(doc, ranges[i].anchor), _clipPos(doc, ranges[i].head));
        }
      }, origin: options && options.origin };signal(doc, "beforeSelectionChange", doc, obj);if (doc.cm) {
      signal(doc.cm, "beforeSelectionChange", doc.cm, obj);
    }if (obj.ranges != sel.ranges) {
      return normalizeSelection(doc.cm, obj.ranges, obj.ranges.length - 1);
    } else {
      return sel;
    }
  }function setSelectionReplaceHistory(doc, sel, options) {
    var done = doc.history.done,
        last = lst(done);if (last && last.ranges) {
      done[done.length - 1] = sel;setSelectionNoUndo(doc, sel, options);
    } else {
      setSelection(doc, sel, options);
    }
  }function setSelection(doc, sel, options) {
    setSelectionNoUndo(doc, sel, options);addSelectionToHistory(doc, doc.sel, doc.cm ? doc.cm.curOp.id : NaN, options);
  }function setSelectionNoUndo(doc, sel, options) {
    if (hasHandler(doc, "beforeSelectionChange") || doc.cm && hasHandler(doc.cm, "beforeSelectionChange")) {
      sel = filterSelectionChange(doc, sel, options);
    }var bias = options && options.bias || (cmp(sel.primary().head, doc.sel.primary().head) < 0 ? -1 : 1);setSelectionInner(doc, skipAtomicInSelection(doc, sel, bias, true));if (!(options && options.scroll === false) && doc.cm) {
      ensureCursorVisible(doc.cm);
    }
  }function setSelectionInner(doc, sel) {
    if (sel.equals(doc.sel)) {
      return;
    }doc.sel = sel;if (doc.cm) {
      doc.cm.curOp.updateInput = 1;doc.cm.curOp.selectionChanged = true;signalCursorActivity(doc.cm);
    }signalLater(doc, "cursorActivity", doc);
  }function reCheckSelection(doc) {
    setSelectionInner(doc, skipAtomicInSelection(doc, doc.sel, null, false));
  }function skipAtomicInSelection(doc, sel, bias, mayClear) {
    var out;for (var i = 0; i < sel.ranges.length; i++) {
      var range = sel.ranges[i];var old = sel.ranges.length == doc.sel.ranges.length && doc.sel.ranges[i];var newAnchor = skipAtomic(doc, range.anchor, old && old.anchor, bias, mayClear);var newHead = skipAtomic(doc, range.head, old && old.head, bias, mayClear);if (out || newAnchor != range.anchor || newHead != range.head) {
        if (!out) {
          out = sel.ranges.slice(0, i);
        }out[i] = new Range(newAnchor, newHead);
      }
    }return out ? normalizeSelection(doc.cm, out, sel.primIndex) : sel;
  }function skipAtomicInner(doc, pos, oldPos, dir, mayClear) {
    var line = getLine(doc, pos.line);if (line.markedSpans) {
      for (var i = 0; i < line.markedSpans.length; ++i) {
        var sp = line.markedSpans[i],
            m = sp.marker;var preventCursorLeft = "selectLeft" in m ? !m.selectLeft : m.inclusiveLeft;var preventCursorRight = "selectRight" in m ? !m.selectRight : m.inclusiveRight;if ((sp.from == null || (preventCursorLeft ? sp.from <= pos.ch : sp.from < pos.ch)) && (sp.to == null || (preventCursorRight ? sp.to >= pos.ch : sp.to > pos.ch))) {
          if (mayClear) {
            signal(m, "beforeCursorEnter");if (m.explicitlyCleared) {
              if (!line.markedSpans) {
                break;
              } else {
                --i;continue;
              }
            }
          }if (!m.atomic) {
            continue;
          }if (oldPos) {
            var near = m.find(dir < 0 ? 1 : -1),
                diff = void 0;if (dir < 0 ? preventCursorRight : preventCursorLeft) {
              near = movePos(doc, near, -dir, near && near.line == pos.line ? line : null);
            }if (near && near.line == pos.line && (diff = cmp(near, oldPos)) && (dir < 0 ? diff < 0 : diff > 0)) {
              return skipAtomicInner(doc, near, pos, dir, mayClear);
            }
          }var far = m.find(dir < 0 ? -1 : 1);if (dir < 0 ? preventCursorLeft : preventCursorRight) {
            far = movePos(doc, far, dir, far.line == pos.line ? line : null);
          }return far ? skipAtomicInner(doc, far, pos, dir, mayClear) : null;
        }
      }
    }return pos;
  }function skipAtomic(doc, pos, oldPos, bias, mayClear) {
    var dir = bias || 1;var found = skipAtomicInner(doc, pos, oldPos, dir, mayClear) || !mayClear && skipAtomicInner(doc, pos, oldPos, dir, true) || skipAtomicInner(doc, pos, oldPos, -dir, mayClear) || !mayClear && skipAtomicInner(doc, pos, oldPos, -dir, true);if (!found) {
      doc.cantEdit = true;return Pos(doc.first, 0);
    }return found;
  }function movePos(doc, pos, dir, line) {
    if (dir < 0 && pos.ch == 0) {
      if (pos.line > doc.first) {
        return _clipPos(doc, Pos(pos.line - 1));
      } else {
        return null;
      }
    } else if (dir > 0 && pos.ch == (line || getLine(doc, pos.line)).text.length) {
      if (pos.line < doc.first + doc.size - 1) {
        return Pos(pos.line + 1, 0);
      } else {
        return null;
      }
    } else {
      return new Pos(pos.line, pos.ch + dir);
    }
  }function selectAll(cm) {
    cm.setSelection(Pos(cm.firstLine(), 0), Pos(cm.lastLine()), sel_dontScroll);
  }function filterChange(doc, change, update) {
    var obj = { canceled: false, from: change.from, to: change.to, text: change.text, origin: change.origin, cancel: function cancel() {
        return obj.canceled = true;
      } };if (update) {
      obj.update = function (from, to, text, origin) {
        if (from) {
          obj.from = _clipPos(doc, from);
        }if (to) {
          obj.to = _clipPos(doc, to);
        }if (text) {
          obj.text = text;
        }if (origin !== undefined) {
          obj.origin = origin;
        }
      };
    }signal(doc, "beforeChange", doc, obj);if (doc.cm) {
      signal(doc.cm, "beforeChange", doc.cm, obj);
    }if (obj.canceled) {
      if (doc.cm) {
        doc.cm.curOp.updateInput = 2;
      }return null;
    }return { from: obj.from, to: obj.to, text: obj.text, origin: obj.origin };
  }function makeChange(doc, change, ignoreReadOnly) {
    if (doc.cm) {
      if (!doc.cm.curOp) {
        return operation(doc.cm, makeChange)(doc, change, ignoreReadOnly);
      }if (doc.cm.state.suppressEdits) {
        return;
      }
    }if (hasHandler(doc, "beforeChange") || doc.cm && hasHandler(doc.cm, "beforeChange")) {
      change = filterChange(doc, change, true);if (!change) {
        return;
      }
    }var split = sawReadOnlySpans && !ignoreReadOnly && removeReadOnlyRanges(doc, change.from, change.to);if (split) {
      for (var i = split.length - 1; i >= 0; --i) {
        makeChangeInner(doc, { from: split[i].from, to: split[i].to, text: i ? [""] : change.text, origin: change.origin });
      }
    } else {
      makeChangeInner(doc, change);
    }
  }function makeChangeInner(doc, change) {
    if (change.text.length == 1 && change.text[0] == "" && cmp(change.from, change.to) == 0) {
      return;
    }var selAfter = computeSelAfterChange(doc, change);addChangeToHistory(doc, change, selAfter, doc.cm ? doc.cm.curOp.id : NaN);makeChangeSingleDoc(doc, change, selAfter, stretchSpansOverChange(doc, change));var rebased = [];linkedDocs(doc, function (doc, sharedHist) {
      if (!sharedHist && indexOf(rebased, doc.history) == -1) {
        rebaseHist(doc.history, change);rebased.push(doc.history);
      }makeChangeSingleDoc(doc, change, null, stretchSpansOverChange(doc, change));
    });
  }function makeChangeFromHistory(doc, type, allowSelectionOnly) {
    var suppress = doc.cm && doc.cm.state.suppressEdits;if (suppress && !allowSelectionOnly) {
      return;
    }var hist = doc.history,
        event,
        selAfter = doc.sel;var source = type == "undo" ? hist.done : hist.undone,
        dest = type == "undo" ? hist.undone : hist.done;var i = 0;for (; i < source.length; i++) {
      event = source[i];if (allowSelectionOnly ? event.ranges && !event.equals(doc.sel) : !event.ranges) {
        break;
      }
    }if (i == source.length) {
      return;
    }hist.lastOrigin = hist.lastSelOrigin = null;for (;;) {
      event = source.pop();if (event.ranges) {
        pushSelectionToHistory(event, dest);if (allowSelectionOnly && !event.equals(doc.sel)) {
          setSelection(doc, event, { clearRedo: false });return;
        }selAfter = event;
      } else if (suppress) {
        source.push(event);return;
      } else {
        break;
      }
    }var antiChanges = [];pushSelectionToHistory(selAfter, dest);dest.push({ changes: antiChanges, generation: hist.generation });hist.generation = event.generation || ++hist.maxGeneration;var filter = hasHandler(doc, "beforeChange") || doc.cm && hasHandler(doc.cm, "beforeChange");var loop = function loop(i) {
      var change = event.changes[i];change.origin = type;if (filter && !filterChange(doc, change, false)) {
        source.length = 0;return {};
      }antiChanges.push(historyChangeFromChange(doc, change));var after = i ? computeSelAfterChange(doc, change) : lst(source);makeChangeSingleDoc(doc, change, after, mergeOldSpans(doc, change));if (!i && doc.cm) {
        doc.cm.scrollIntoView({ from: change.from, to: changeEnd(change) });
      }var rebased = [];linkedDocs(doc, function (doc, sharedHist) {
        if (!sharedHist && indexOf(rebased, doc.history) == -1) {
          rebaseHist(doc.history, change);rebased.push(doc.history);
        }makeChangeSingleDoc(doc, change, null, mergeOldSpans(doc, change));
      });
    };for (var i$1 = event.changes.length - 1; i$1 >= 0; --i$1) {
      var returned = loop(i$1);if (returned) return returned.v;
    }
  }function shiftDoc(doc, distance) {
    if (distance == 0) {
      return;
    }doc.first += distance;doc.sel = new Selection(map(doc.sel.ranges, function (range) {
      return new Range(Pos(range.anchor.line + distance, range.anchor.ch), Pos(range.head.line + distance, range.head.ch));
    }), doc.sel.primIndex);if (doc.cm) {
      regChange(doc.cm, doc.first, doc.first - distance, distance);for (var d = doc.cm.display, l = d.viewFrom; l < d.viewTo; l++) {
        regLineChange(doc.cm, l, "gutter");
      }
    }
  }function makeChangeSingleDoc(doc, change, selAfter, spans) {
    if (doc.cm && !doc.cm.curOp) {
      return operation(doc.cm, makeChangeSingleDoc)(doc, change, selAfter, spans);
    }if (change.to.line < doc.first) {
      shiftDoc(doc, change.text.length - 1 - (change.to.line - change.from.line));return;
    }if (change.from.line > doc.lastLine()) {
      return;
    }if (change.from.line < doc.first) {
      var shift = change.text.length - 1 - (doc.first - change.from.line);shiftDoc(doc, shift);change = { from: Pos(doc.first, 0), to: Pos(change.to.line + shift, change.to.ch), text: [lst(change.text)], origin: change.origin };
    }var last = doc.lastLine();if (change.to.line > last) {
      change = { from: change.from, to: Pos(last, getLine(doc, last).text.length), text: [change.text[0]], origin: change.origin };
    }change.removed = getBetween(doc, change.from, change.to);if (!selAfter) {
      selAfter = computeSelAfterChange(doc, change);
    }if (doc.cm) {
      makeChangeSingleDocInEditor(doc.cm, change, spans);
    } else {
      updateDoc(doc, change, spans);
    }setSelectionNoUndo(doc, selAfter, sel_dontScroll);if (doc.cantEdit && skipAtomic(doc, Pos(doc.firstLine(), 0))) {
      doc.cantEdit = false;
    }
  }function makeChangeSingleDocInEditor(cm, change, spans) {
    var doc = cm.doc,
        display = cm.display,
        from = change.from,
        to = change.to;var recomputeMaxLength = false,
        checkWidthStart = from.line;if (!cm.options.lineWrapping) {
      checkWidthStart = lineNo(visualLine(getLine(doc, from.line)));doc.iter(checkWidthStart, to.line + 1, function (line) {
        if (line == display.maxLine) {
          recomputeMaxLength = true;return true;
        }
      });
    }if (doc.sel.contains(change.from, change.to) > -1) {
      signalCursorActivity(cm);
    }updateDoc(doc, change, spans, estimateHeight(cm));if (!cm.options.lineWrapping) {
      doc.iter(checkWidthStart, from.line + change.text.length, function (line) {
        var len = lineLength(line);if (len > display.maxLineLength) {
          display.maxLine = line;display.maxLineLength = len;display.maxLineChanged = true;recomputeMaxLength = false;
        }
      });if (recomputeMaxLength) {
        cm.curOp.updateMaxLine = true;
      }
    }retreatFrontier(doc, from.line);startWorker(cm, 400);var lendiff = change.text.length - (to.line - from.line) - 1;if (change.full) {
      regChange(cm);
    } else if (from.line == to.line && change.text.length == 1 && !isWholeLineUpdate(cm.doc, change)) {
      regLineChange(cm, from.line, "text");
    } else {
      regChange(cm, from.line, to.line + 1, lendiff);
    }var changesHandler = hasHandler(cm, "changes"),
        changeHandler = hasHandler(cm, "change");if (changeHandler || changesHandler) {
      var obj = { from: from, to: to, text: change.text, removed: change.removed, origin: change.origin };if (changeHandler) {
        signalLater(cm, "change", cm, obj);
      }if (changesHandler) {
        (cm.curOp.changeObjs || (cm.curOp.changeObjs = [])).push(obj);
      }
    }cm.display.selForContextMenu = null;
  }function _replaceRange(doc, code, from, to, origin) {
    var assign;if (!to) {
      to = from;
    }if (cmp(to, from) < 0) {
      assign = [to, from], from = assign[0], to = assign[1];
    }if (typeof code == "string") {
      code = doc.splitLines(code);
    }makeChange(doc, { from: from, to: to, text: code, origin: origin });
  }function rebaseHistSelSingle(pos, from, to, diff) {
    if (to < pos.line) {
      pos.line += diff;
    } else if (from < pos.line) {
      pos.line = from;pos.ch = 0;
    }
  }function rebaseHistArray(array, from, to, diff) {
    for (var i = 0; i < array.length; ++i) {
      var sub = array[i],
          ok = true;if (sub.ranges) {
        if (!sub.copied) {
          sub = array[i] = sub.deepCopy();sub.copied = true;
        }for (var j = 0; j < sub.ranges.length; j++) {
          rebaseHistSelSingle(sub.ranges[j].anchor, from, to, diff);rebaseHistSelSingle(sub.ranges[j].head, from, to, diff);
        }continue;
      }for (var j$1 = 0; j$1 < sub.changes.length; ++j$1) {
        var cur = sub.changes[j$1];if (to < cur.from.line) {
          cur.from = Pos(cur.from.line + diff, cur.from.ch);cur.to = Pos(cur.to.line + diff, cur.to.ch);
        } else if (from <= cur.to.line) {
          ok = false;break;
        }
      }if (!ok) {
        array.splice(0, i + 1);i = 0;
      }
    }
  }function rebaseHist(hist, change) {
    var from = change.from.line,
        to = change.to.line,
        diff = change.text.length - (to - from) - 1;rebaseHistArray(hist.done, from, to, diff);rebaseHistArray(hist.undone, from, to, diff);
  }function changeLine(doc, handle, changeType, op) {
    var no = handle,
        line = handle;if (typeof handle == "number") {
      line = getLine(doc, clipLine(doc, handle));
    } else {
      no = lineNo(handle);
    }if (no == null) {
      return null;
    }if (op(line, no) && doc.cm) {
      regLineChange(doc.cm, no, changeType);
    }return line;
  }function LeafChunk(lines) {
    this.lines = lines;this.parent = null;var height = 0;for (var i = 0; i < lines.length; ++i) {
      lines[i].parent = this;height += lines[i].height;
    }this.height = height;
  }LeafChunk.prototype = { chunkSize: function chunkSize() {
      return this.lines.length;
    }, removeInner: function removeInner(at, n) {
      for (var i = at, e = at + n; i < e; ++i) {
        var line = this.lines[i];this.height -= line.height;cleanUpLine(line);signalLater(line, "delete");
      }this.lines.splice(at, n);
    }, collapse: function collapse(lines) {
      lines.push.apply(lines, this.lines);
    }, insertInner: function insertInner(at, lines, height) {
      this.height += height;this.lines = this.lines.slice(0, at).concat(lines).concat(this.lines.slice(at));for (var i = 0; i < lines.length; ++i) {
        lines[i].parent = this;
      }
    }, iterN: function iterN(at, n, op) {
      for (var e = at + n; at < e; ++at) {
        if (op(this.lines[at])) {
          return true;
        }
      }
    } };function BranchChunk(children) {
    this.children = children;var size = 0,
        height = 0;for (var i = 0; i < children.length; ++i) {
      var ch = children[i];size += ch.chunkSize();height += ch.height;ch.parent = this;
    }this.size = size;this.height = height;this.parent = null;
  }BranchChunk.prototype = { chunkSize: function chunkSize() {
      return this.size;
    }, removeInner: function removeInner(at, n) {
      this.size -= n;for (var i = 0; i < this.children.length; ++i) {
        var child = this.children[i],
            sz = child.chunkSize();if (at < sz) {
          var rm = Math.min(n, sz - at),
              oldHeight = child.height;child.removeInner(at, rm);this.height -= oldHeight - child.height;if (sz == rm) {
            this.children.splice(i--, 1);child.parent = null;
          }if ((n -= rm) == 0) {
            break;
          }at = 0;
        } else {
          at -= sz;
        }
      }if (this.size - n < 25 && (this.children.length > 1 || !(this.children[0] instanceof LeafChunk))) {
        var lines = [];this.collapse(lines);this.children = [new LeafChunk(lines)];this.children[0].parent = this;
      }
    }, collapse: function collapse(lines) {
      for (var i = 0; i < this.children.length; ++i) {
        this.children[i].collapse(lines);
      }
    }, insertInner: function insertInner(at, lines, height) {
      this.size += lines.length;this.height += height;for (var i = 0; i < this.children.length; ++i) {
        var child = this.children[i],
            sz = child.chunkSize();if (at <= sz) {
          child.insertInner(at, lines, height);if (child.lines && child.lines.length > 50) {
            var remaining = child.lines.length % 25 + 25;for (var pos = remaining; pos < child.lines.length;) {
              var leaf = new LeafChunk(child.lines.slice(pos, pos += 25));child.height -= leaf.height;this.children.splice(++i, 0, leaf);leaf.parent = this;
            }child.lines = child.lines.slice(0, remaining);this.maybeSpill();
          }break;
        }at -= sz;
      }
    }, maybeSpill: function maybeSpill() {
      if (this.children.length <= 10) {
        return;
      }var me = this;do {
        var spilled = me.children.splice(me.children.length - 5, 5);var sibling = new BranchChunk(spilled);if (!me.parent) {
          var copy = new BranchChunk(me.children);copy.parent = me;me.children = [copy, sibling];me = copy;
        } else {
          me.size -= sibling.size;me.height -= sibling.height;var myIndex = indexOf(me.parent.children, me);me.parent.children.splice(myIndex + 1, 0, sibling);
        }sibling.parent = me.parent;
      } while (me.children.length > 10);me.parent.maybeSpill();
    }, iterN: function iterN(at, n, op) {
      for (var i = 0; i < this.children.length; ++i) {
        var child = this.children[i],
            sz = child.chunkSize();if (at < sz) {
          var used = Math.min(n, sz - at);if (child.iterN(at, used, op)) {
            return true;
          }if ((n -= used) == 0) {
            break;
          }at = 0;
        } else {
          at -= sz;
        }
      }
    } };var LineWidget = function LineWidget(doc, node, options) {
    if (options) {
      for (var opt in options) {
        if (options.hasOwnProperty(opt)) {
          this[opt] = options[opt];
        }
      }
    }this.doc = doc;this.node = node;
  };LineWidget.prototype.clear = function () {
    var cm = this.doc.cm,
        ws = this.line.widgets,
        line = this.line,
        no = lineNo(line);if (no == null || !ws) {
      return;
    }for (var i = 0; i < ws.length; ++i) {
      if (ws[i] == this) {
        ws.splice(i--, 1);
      }
    }if (!ws.length) {
      line.widgets = null;
    }var height = widgetHeight(this);updateLineHeight(line, Math.max(0, line.height - height));if (cm) {
      runInOp(cm, function () {
        adjustScrollWhenAboveVisible(cm, line, -height);regLineChange(cm, no, "widget");
      });signalLater(cm, "lineWidgetCleared", cm, this, no);
    }
  };LineWidget.prototype.changed = function () {
    var this$1 = this;var oldH = this.height,
        cm = this.doc.cm,
        line = this.line;this.height = null;var diff = widgetHeight(this) - oldH;if (!diff) {
      return;
    }if (!lineIsHidden(this.doc, line)) {
      updateLineHeight(line, line.height + diff);
    }if (cm) {
      runInOp(cm, function () {
        cm.curOp.forceUpdate = true;adjustScrollWhenAboveVisible(cm, line, diff);signalLater(cm, "lineWidgetChanged", cm, this$1, lineNo(line));
      });
    }
  };eventMixin(LineWidget);function adjustScrollWhenAboveVisible(cm, line, diff) {
    if (_heightAtLine(line) < (cm.curOp && cm.curOp.scrollTop || cm.doc.scrollTop)) {
      addToScrollTop(cm, diff);
    }
  }function addLineWidget(doc, handle, node, options) {
    var widget = new LineWidget(doc, node, options);var cm = doc.cm;if (cm && widget.noHScroll) {
      cm.display.alignWidgets = true;
    }changeLine(doc, handle, "widget", function (line) {
      var widgets = line.widgets || (line.widgets = []);if (widget.insertAt == null) {
        widgets.push(widget);
      } else {
        widgets.splice(Math.min(widgets.length - 1, Math.max(0, widget.insertAt)), 0, widget);
      }widget.line = line;if (cm && !lineIsHidden(doc, line)) {
        var aboveVisible = _heightAtLine(line) < doc.scrollTop;updateLineHeight(line, line.height + widgetHeight(widget));if (aboveVisible) {
          addToScrollTop(cm, widget.height);
        }cm.curOp.forceUpdate = true;
      }return true;
    });if (cm) {
      signalLater(cm, "lineWidgetAdded", cm, widget, typeof handle == "number" ? handle : lineNo(handle));
    }return widget;
  }var nextMarkerId = 0;var TextMarker = function TextMarker(doc, type) {
    this.lines = [];this.type = type;this.doc = doc;this.id = ++nextMarkerId;
  };TextMarker.prototype.clear = function () {
    if (this.explicitlyCleared) {
      return;
    }var cm = this.doc.cm,
        withOp = cm && !cm.curOp;if (withOp) {
      _startOperation(cm);
    }if (hasHandler(this, "clear")) {
      var found = this.find();if (found) {
        signalLater(this, "clear", found.from, found.to);
      }
    }var min = null,
        max = null;for (var i = 0; i < this.lines.length; ++i) {
      var line = this.lines[i];var span = getMarkedSpanFor(line.markedSpans, this);if (cm && !this.collapsed) {
        regLineChange(cm, lineNo(line), "text");
      } else if (cm) {
        if (span.to != null) {
          max = lineNo(line);
        }if (span.from != null) {
          min = lineNo(line);
        }
      }line.markedSpans = removeMarkedSpan(line.markedSpans, span);if (span.from == null && this.collapsed && !lineIsHidden(this.doc, line) && cm) {
        updateLineHeight(line, textHeight(cm.display));
      }
    }if (cm && this.collapsed && !cm.options.lineWrapping) {
      for (var i$1 = 0; i$1 < this.lines.length; ++i$1) {
        var visual = visualLine(this.lines[i$1]),
            len = lineLength(visual);if (len > cm.display.maxLineLength) {
          cm.display.maxLine = visual;cm.display.maxLineLength = len;cm.display.maxLineChanged = true;
        }
      }
    }if (min != null && cm && this.collapsed) {
      regChange(cm, min, max + 1);
    }this.lines.length = 0;this.explicitlyCleared = true;if (this.atomic && this.doc.cantEdit) {
      this.doc.cantEdit = false;if (cm) {
        reCheckSelection(cm.doc);
      }
    }if (cm) {
      signalLater(cm, "markerCleared", cm, this, min, max);
    }if (withOp) {
      _endOperation(cm);
    }if (this.parent) {
      this.parent.clear();
    }
  };TextMarker.prototype.find = function (side, lineObj) {
    if (side == null && this.type == "bookmark") {
      side = 1;
    }var from, to;for (var i = 0; i < this.lines.length; ++i) {
      var line = this.lines[i];var span = getMarkedSpanFor(line.markedSpans, this);if (span.from != null) {
        from = Pos(lineObj ? line : lineNo(line), span.from);if (side == -1) {
          return from;
        }
      }if (span.to != null) {
        to = Pos(lineObj ? line : lineNo(line), span.to);if (side == 1) {
          return to;
        }
      }
    }return from && { from: from, to: to };
  };TextMarker.prototype.changed = function () {
    var this$1 = this;var pos = this.find(-1, true),
        widget = this,
        cm = this.doc.cm;if (!pos || !cm) {
      return;
    }runInOp(cm, function () {
      var line = pos.line,
          lineN = lineNo(pos.line);var view = findViewForLine(cm, lineN);if (view) {
        clearLineMeasurementCacheFor(view);cm.curOp.selectionChanged = cm.curOp.forceUpdate = true;
      }cm.curOp.updateMaxLine = true;if (!lineIsHidden(widget.doc, line) && widget.height != null) {
        var oldHeight = widget.height;widget.height = null;var dHeight = widgetHeight(widget) - oldHeight;if (dHeight) {
          updateLineHeight(line, line.height + dHeight);
        }
      }signalLater(cm, "markerChanged", cm, this$1);
    });
  };TextMarker.prototype.attachLine = function (line) {
    if (!this.lines.length && this.doc.cm) {
      var op = this.doc.cm.curOp;if (!op.maybeHiddenMarkers || indexOf(op.maybeHiddenMarkers, this) == -1) {
        (op.maybeUnhiddenMarkers || (op.maybeUnhiddenMarkers = [])).push(this);
      }
    }this.lines.push(line);
  };TextMarker.prototype.detachLine = function (line) {
    this.lines.splice(indexOf(this.lines, line), 1);if (!this.lines.length && this.doc.cm) {
      var op = this.doc.cm.curOp;(op.maybeHiddenMarkers || (op.maybeHiddenMarkers = [])).push(this);
    }
  };eventMixin(TextMarker);function _markText(doc, from, to, options, type) {
    if (options && options.shared) {
      return markTextShared(doc, from, to, options, type);
    }if (doc.cm && !doc.cm.curOp) {
      return operation(doc.cm, _markText)(doc, from, to, options, type);
    }var marker = new TextMarker(doc, type),
        diff = cmp(from, to);if (options) {
      copyObj(options, marker, false);
    }if (diff > 0 || diff == 0 && marker.clearWhenEmpty !== false) {
      return marker;
    }if (marker.replacedWith) {
      marker.collapsed = true;marker.widgetNode = eltP("span", [marker.replacedWith], "CodeMirror-widget");if (!options.handleMouseEvents) {
        marker.widgetNode.setAttribute("cm-ignore-events", "true");
      }if (options.insertLeft) {
        marker.widgetNode.insertLeft = true;
      }
    }if (marker.collapsed) {
      if (conflictingCollapsedRange(doc, from.line, from, to, marker) || from.line != to.line && conflictingCollapsedRange(doc, to.line, from, to, marker)) {
        throw new Error("Inserting collapsed marker partially overlapping an existing one");
      }seeCollapsedSpans();
    }if (marker.addToHistory) {
      addChangeToHistory(doc, { from: from, to: to, origin: "markText" }, doc.sel, NaN);
    }var curLine = from.line,
        cm = doc.cm,
        updateMaxLine;doc.iter(curLine, to.line + 1, function (line) {
      if (cm && marker.collapsed && !cm.options.lineWrapping && visualLine(line) == cm.display.maxLine) {
        updateMaxLine = true;
      }if (marker.collapsed && curLine != from.line) {
        updateLineHeight(line, 0);
      }addMarkedSpan(line, new MarkedSpan(marker, curLine == from.line ? from.ch : null, curLine == to.line ? to.ch : null));++curLine;
    });if (marker.collapsed) {
      doc.iter(from.line, to.line + 1, function (line) {
        if (lineIsHidden(doc, line)) {
          updateLineHeight(line, 0);
        }
      });
    }if (marker.clearOnEnter) {
      on(marker, "beforeCursorEnter", function () {
        return marker.clear();
      });
    }if (marker.readOnly) {
      seeReadOnlySpans();if (doc.history.done.length || doc.history.undone.length) {
        doc.clearHistory();
      }
    }if (marker.collapsed) {
      marker.id = ++nextMarkerId;marker.atomic = true;
    }if (cm) {
      if (updateMaxLine) {
        cm.curOp.updateMaxLine = true;
      }if (marker.collapsed) {
        regChange(cm, from.line, to.line + 1);
      } else if (marker.className || marker.startStyle || marker.endStyle || marker.css || marker.attributes || marker.title) {
        for (var i = from.line; i <= to.line; i++) {
          regLineChange(cm, i, "text");
        }
      }if (marker.atomic) {
        reCheckSelection(cm.doc);
      }signalLater(cm, "markerAdded", cm, marker);
    }return marker;
  }var SharedTextMarker = function SharedTextMarker(markers, primary) {
    this.markers = markers;this.primary = primary;for (var i = 0; i < markers.length; ++i) {
      markers[i].parent = this;
    }
  };SharedTextMarker.prototype.clear = function () {
    if (this.explicitlyCleared) {
      return;
    }this.explicitlyCleared = true;for (var i = 0; i < this.markers.length; ++i) {
      this.markers[i].clear();
    }signalLater(this, "clear");
  };SharedTextMarker.prototype.find = function (side, lineObj) {
    return this.primary.find(side, lineObj);
  };eventMixin(SharedTextMarker);function markTextShared(doc, from, to, options, type) {
    options = copyObj(options);options.shared = false;var markers = [_markText(doc, from, to, options, type)],
        primary = markers[0];var widget = options.widgetNode;linkedDocs(doc, function (doc) {
      if (widget) {
        options.widgetNode = widget.cloneNode(true);
      }markers.push(_markText(doc, _clipPos(doc, from), _clipPos(doc, to), options, type));for (var i = 0; i < doc.linked.length; ++i) {
        if (doc.linked[i].isParent) {
          return;
        }
      }primary = lst(markers);
    });return new SharedTextMarker(markers, primary);
  }function findSharedMarkers(doc) {
    return doc.findMarks(Pos(doc.first, 0), doc.clipPos(Pos(doc.lastLine())), function (m) {
      return m.parent;
    });
  }function copySharedMarkers(doc, markers) {
    for (var i = 0; i < markers.length; i++) {
      var marker = markers[i],
          pos = marker.find();var mFrom = doc.clipPos(pos.from),
          mTo = doc.clipPos(pos.to);if (cmp(mFrom, mTo)) {
        var subMark = _markText(doc, mFrom, mTo, marker.primary, marker.primary.type);marker.markers.push(subMark);subMark.parent = marker;
      }
    }
  }function detachSharedMarkers(markers) {
    var loop = function loop(i) {
      var marker = markers[i],
          linked = [marker.primary.doc];linkedDocs(marker.primary.doc, function (d) {
        return linked.push(d);
      });for (var j = 0; j < marker.markers.length; j++) {
        var subMarker = marker.markers[j];if (indexOf(linked, subMarker.doc) == -1) {
          subMarker.parent = null;marker.markers.splice(j--, 1);
        }
      }
    };for (var i = 0; i < markers.length; i++) {
      loop(i);
    }
  }var nextDocId = 0;var Doc = function Doc(text, mode, firstLine, lineSep, direction) {
    if (!(this instanceof Doc)) {
      return new Doc(text, mode, firstLine, lineSep, direction);
    }if (firstLine == null) {
      firstLine = 0;
    }BranchChunk.call(this, [new LeafChunk([new Line("", null)])]);this.first = firstLine;this.scrollTop = this.scrollLeft = 0;this.cantEdit = false;this.cleanGeneration = 1;this.modeFrontier = this.highlightFrontier = firstLine;var start = Pos(firstLine, 0);this.sel = simpleSelection(start);this.history = new History(null);this.id = ++nextDocId;this.modeOption = mode;this.lineSep = lineSep;this.direction = direction == "rtl" ? "rtl" : "ltr";this.extend = false;if (typeof text == "string") {
      text = this.splitLines(text);
    }updateDoc(this, { from: start, to: start, text: text });setSelection(this, simpleSelection(start), sel_dontScroll);
  };Doc.prototype = createObj(BranchChunk.prototype, { constructor: Doc, iter: function iter(from, to, op) {
      if (op) {
        this.iterN(from - this.first, to - from, op);
      } else {
        this.iterN(this.first, this.first + this.size, from);
      }
    }, insert: function insert(at, lines) {
      var height = 0;for (var i = 0; i < lines.length; ++i) {
        height += lines[i].height;
      }this.insertInner(at - this.first, lines, height);
    }, remove: function remove(at, n) {
      this.removeInner(at - this.first, n);
    }, getValue: function getValue(lineSep) {
      var lines = getLines(this, this.first, this.first + this.size);if (lineSep === false) {
        return lines;
      }return lines.join(lineSep || this.lineSeparator());
    }, setValue: docMethodOp(function (code) {
      var top = Pos(this.first, 0),
          last = this.first + this.size - 1;makeChange(this, { from: top, to: Pos(last, getLine(this, last).text.length), text: this.splitLines(code), origin: "setValue", full: true }, true);if (this.cm) {
        scrollToCoords(this.cm, 0, 0);
      }setSelection(this, simpleSelection(top), sel_dontScroll);
    }), replaceRange: function replaceRange(code, from, to, origin) {
      from = _clipPos(this, from);to = to ? _clipPos(this, to) : from;_replaceRange(this, code, from, to, origin);
    }, getRange: function getRange(from, to, lineSep) {
      var lines = getBetween(this, _clipPos(this, from), _clipPos(this, to));if (lineSep === false) {
        return lines;
      }return lines.join(lineSep || this.lineSeparator());
    }, getLine: function getLine(line) {
      var l = this.getLineHandle(line);return l && l.text;
    }, setLine: function setLine(line, text) {
      if (isLine(this, line)) _replaceRange(this, text, Pos(line, 0), _clipPos(this, Pos(line)));
    }, getLineHandle: function getLineHandle(line) {
      if (isLine(this, line)) {
        return getLine(this, line);
      }
    }, getLineNumber: function getLineNumber(line) {
      return lineNo(line);
    }, getLineHandleVisualStart: function getLineHandleVisualStart(line) {
      if (typeof line == "number") {
        line = getLine(this, line);
      }return visualLine(line);
    }, lineCount: function lineCount() {
      return this.size;
    }, firstLine: function firstLine() {
      return this.first;
    }, lastLine: function lastLine() {
      return this.first + this.size - 1;
    }, clipPos: function clipPos(pos) {
      return _clipPos(this, pos);
    }, getCursor: function getCursor(start) {
      var range$$1 = this.sel.primary(),
          pos;if (start == null || start == "head") {
        pos = range$$1.head;
      } else if (start == "anchor") {
        pos = range$$1.anchor;
      } else if (start == "end" || start == "to" || start === false) {
        pos = range$$1.to();
      } else {
        pos = range$$1.from();
      }return pos;
    }, listSelections: function listSelections() {
      return this.sel.ranges;
    }, somethingSelected: function somethingSelected() {
      return this.sel.somethingSelected();
    }, setCursor: docMethodOp(function (line, ch, options) {
      setSimpleSelection(this, _clipPos(this, typeof line == "number" ? Pos(line, ch || 0) : line), null, options);
    }), setSelection: docMethodOp(function (anchor, head, options) {
      setSimpleSelection(this, _clipPos(this, anchor), _clipPos(this, head || anchor), options);
    }), extendSelection: docMethodOp(function (head, other, options) {
      extendSelection(this, _clipPos(this, head), other && _clipPos(this, other), options);
    }), extendSelections: docMethodOp(function (heads, options) {
      extendSelections(this, clipPosArray(this, heads), options);
    }), extendSelectionsBy: docMethodOp(function (f, options) {
      var heads = map(this.sel.ranges, f);extendSelections(this, clipPosArray(this, heads), options);
    }), setSelections: docMethodOp(function (ranges, primary, options) {
      if (!ranges.length) {
        return;
      }var out = [];for (var i = 0; i < ranges.length; i++) {
        out[i] = new Range(_clipPos(this, ranges[i].anchor), _clipPos(this, ranges[i].head));
      }if (primary == null) {
        primary = Math.min(ranges.length - 1, this.sel.primIndex);
      }setSelection(this, normalizeSelection(this.cm, out, primary), options);
    }), addSelection: docMethodOp(function (anchor, head, options) {
      var ranges = this.sel.ranges.slice(0);ranges.push(new Range(_clipPos(this, anchor), _clipPos(this, head || anchor)));setSelection(this, normalizeSelection(this.cm, ranges, ranges.length - 1), options);
    }), getSelection: function getSelection(lineSep) {
      var ranges = this.sel.ranges,
          lines;for (var i = 0; i < ranges.length; i++) {
        var sel = getBetween(this, ranges[i].from(), ranges[i].to());lines = lines ? lines.concat(sel) : sel;
      }if (lineSep === false) {
        return lines;
      } else {
        return lines.join(lineSep || this.lineSeparator());
      }
    }, getSelections: function getSelections(lineSep) {
      var parts = [],
          ranges = this.sel.ranges;for (var i = 0; i < ranges.length; i++) {
        var sel = getBetween(this, ranges[i].from(), ranges[i].to());if (lineSep !== false) {
          sel = sel.join(lineSep || this.lineSeparator());
        }parts[i] = sel;
      }return parts;
    }, replaceSelection: function replaceSelection(code, collapse, origin) {
      var dup = [];for (var i = 0; i < this.sel.ranges.length; i++) {
        dup[i] = code;
      }this.replaceSelections(dup, collapse, origin || "+input");
    }, replaceSelections: docMethodOp(function (code, collapse, origin) {
      var changes = [],
          sel = this.sel;for (var i = 0; i < sel.ranges.length; i++) {
        var range$$1 = sel.ranges[i];changes[i] = { from: range$$1.from(), to: range$$1.to(), text: this.splitLines(code[i]), origin: origin };
      }var newSel = collapse && collapse != "end" && computeReplacedSel(this, changes, collapse);for (var i$1 = changes.length - 1; i$1 >= 0; i$1--) {
        makeChange(this, changes[i$1]);
      }if (newSel) {
        setSelectionReplaceHistory(this, newSel);
      } else if (this.cm) {
        ensureCursorVisible(this.cm);
      }
    }), undo: docMethodOp(function () {
      makeChangeFromHistory(this, "undo");
    }), redo: docMethodOp(function () {
      makeChangeFromHistory(this, "redo");
    }), undoSelection: docMethodOp(function () {
      makeChangeFromHistory(this, "undo", true);
    }), redoSelection: docMethodOp(function () {
      makeChangeFromHistory(this, "redo", true);
    }), setExtending: function setExtending(val) {
      this.extend = val;
    }, getExtending: function getExtending() {
      return this.extend;
    }, historySize: function historySize() {
      var hist = this.history,
          done = 0,
          undone = 0;for (var i = 0; i < hist.done.length; i++) {
        if (!hist.done[i].ranges) {
          ++done;
        }
      }for (var i$1 = 0; i$1 < hist.undone.length; i$1++) {
        if (!hist.undone[i$1].ranges) {
          ++undone;
        }
      }return { undo: done, redo: undone };
    }, clearHistory: function clearHistory() {
      this.history = new History(this.history.maxGeneration);
    }, markClean: function markClean() {
      this.cleanGeneration = this.changeGeneration(true);
    }, changeGeneration: function changeGeneration(forceSplit) {
      if (forceSplit) {
        this.history.lastOp = this.history.lastSelOp = this.history.lastOrigin = null;
      }return this.history.generation;
    }, isClean: function isClean(gen) {
      return this.history.generation == (gen || this.cleanGeneration);
    }, getHistory: function getHistory() {
      return { done: copyHistoryArray(this.history.done), undone: copyHistoryArray(this.history.undone) };
    }, setHistory: function setHistory(histData) {
      var hist = this.history = new History(this.history.maxGeneration);hist.done = copyHistoryArray(histData.done.slice(0), null, true);hist.undone = copyHistoryArray(histData.undone.slice(0), null, true);
    }, setGutterMarker: docMethodOp(function (line, gutterID, value) {
      return changeLine(this, line, "gutter", function (line) {
        var markers = line.gutterMarkers || (line.gutterMarkers = {});markers[gutterID] = value;if (!value && isEmpty(markers)) {
          line.gutterMarkers = null;
        }return true;
      });
    }), clearGutter: docMethodOp(function (gutterID) {
      var this$1 = this;this.iter(function (line) {
        if (line.gutterMarkers && line.gutterMarkers[gutterID]) {
          changeLine(this$1, line, "gutter", function () {
            line.gutterMarkers[gutterID] = null;if (isEmpty(line.gutterMarkers)) {
              line.gutterMarkers = null;
            }return true;
          });
        }
      });
    }), lineInfo: function lineInfo(line) {
      var n;if (typeof line == "number") {
        if (!isLine(this, line)) {
          return null;
        }n = line;line = getLine(this, line);if (!line) {
          return null;
        }
      } else {
        n = lineNo(line);
        if (n == null) {
          return null;
        }
      }return { line: n, handle: line, text: line.text, gutterMarkers: line.gutterMarkers, textClass: line.textClass, bgClass: line.bgClass, wrapClass: line.wrapClass, widgets: line.widgets };
    }, addLineClass: docMethodOp(function (handle, where, cls) {
      return changeLine(this, handle, where == "gutter" ? "gutter" : "class", function (line) {
        var prop = where == "text" ? "textClass" : where == "background" ? "bgClass" : where == "gutter" ? "gutterClass" : "wrapClass";if (!line[prop]) {
          line[prop] = cls;
        } else if (classTest(cls).test(line[prop])) {
          return false;
        } else {
          line[prop] += " " + cls;
        }return true;
      });
    }), removeLineClass: docMethodOp(function (handle, where, cls) {
      return changeLine(this, handle, where == "gutter" ? "gutter" : "class", function (line) {
        var prop = where == "text" ? "textClass" : where == "background" ? "bgClass" : where == "gutter" ? "gutterClass" : "wrapClass";var cur = line[prop];if (!cur) {
          return false;
        } else if (cls == null) {
          line[prop] = null;
        } else {
          var found = cur.match(classTest(cls));if (!found) {
            return false;
          }var end = found.index + found[0].length;line[prop] = cur.slice(0, found.index) + (!found.index || end == cur.length ? "" : " ") + cur.slice(end) || null;
        }return true;
      });
    }), addLineWidget: docMethodOp(function (handle, node, options) {
      return addLineWidget(this, handle, node, options);
    }), removeLineWidget: function removeLineWidget(widget) {
      widget.clear();
    }, markText: function markText(from, to, options) {
      return _markText(this, _clipPos(this, from), _clipPos(this, to), options, options && options.type || "range");
    }, setBookmark: function setBookmark(pos, options) {
      var realOpts = { replacedWith: options && (options.nodeType == null ? options.widget : options), insertLeft: options && options.insertLeft, clearWhenEmpty: false, shared: options && options.shared, handleMouseEvents: options && options.handleMouseEvents };pos = _clipPos(this, pos);return _markText(this, pos, pos, realOpts, "bookmark");
    }, findMarksAt: function findMarksAt(pos) {
      pos = _clipPos(this, pos);var markers = [],
          spans = getLine(this, pos.line).markedSpans;if (spans) {
        for (var i = 0; i < spans.length; ++i) {
          var span = spans[i];if ((span.from == null || span.from <= pos.ch) && (span.to == null || span.to >= pos.ch)) {
            markers.push(span.marker.parent || span.marker);
          }
        }
      }return markers;
    }, findMarks: function findMarks(from, to, filter) {
      from = _clipPos(this, from);to = _clipPos(this, to);var found = [],
          lineNo$$1 = from.line;this.iter(from.line, to.line + 1, function (line) {
        var spans = line.markedSpans;if (spans) {
          for (var i = 0; i < spans.length; i++) {
            var span = spans[i];if (!(span.to != null && lineNo$$1 == from.line && from.ch >= span.to || span.from == null && lineNo$$1 != from.line || span.from != null && lineNo$$1 == to.line && span.from >= to.ch) && (!filter || filter(span.marker))) {
              found.push(span.marker.parent || span.marker);
            }
          }
        }++lineNo$$1;
      });return found;
    }, getAllMarks: function getAllMarks() {
      var markers = [];this.iter(function (line) {
        var sps = line.markedSpans;if (sps) {
          for (var i = 0; i < sps.length; ++i) {
            if (sps[i].from != null) {
              markers.push(sps[i].marker);
            }
          }
        }
      });return markers;
    }, posFromIndex: function posFromIndex(off) {
      var ch,
          lineNo$$1 = this.first,
          sepSize = this.lineSeparator().length;this.iter(function (line) {
        var sz = line.text.length + sepSize;if (sz > off) {
          ch = off;return true;
        }off -= sz;++lineNo$$1;
      });return _clipPos(this, Pos(lineNo$$1, ch));
    }, indexFromPos: function indexFromPos(coords) {
      coords = _clipPos(this, coords);var index = coords.ch;if (coords.line < this.first || coords.ch < 0) {
        return 0;
      }var sepSize = this.lineSeparator().length;this.iter(this.first, coords.line, function (line) {
        index += line.text.length + sepSize;
      });return index;
    }, copy: function copy(copyHistory) {
      var doc = new Doc(getLines(this, this.first, this.first + this.size), this.modeOption, this.first, this.lineSep, this.direction);doc.scrollTop = this.scrollTop;doc.scrollLeft = this.scrollLeft;doc.sel = this.sel;doc.extend = false;if (copyHistory) {
        doc.history.undoDepth = this.history.undoDepth;doc.setHistory(this.getHistory());
      }return doc;
    }, linkedDoc: function linkedDoc(options) {
      if (!options) {
        options = {};
      }var from = this.first,
          to = this.first + this.size;if (options.from != null && options.from > from) {
        from = options.from;
      }if (options.to != null && options.to < to) {
        to = options.to;
      }var copy = new Doc(getLines(this, from, to), options.mode || this.modeOption, from, this.lineSep, this.direction);if (options.sharedHist) {
        copy.history = this.history;
      }(this.linked || (this.linked = [])).push({ doc: copy, sharedHist: options.sharedHist });copy.linked = [{ doc: this, isParent: true, sharedHist: options.sharedHist }];copySharedMarkers(copy, findSharedMarkers(this));return copy;
    }, unlinkDoc: function unlinkDoc(other) {
      if (other instanceof CodeMirror) {
        other = other.doc;
      }if (this.linked) {
        for (var i = 0; i < this.linked.length; ++i) {
          var link = this.linked[i];if (link.doc != other) {
            continue;
          }this.linked.splice(i, 1);other.unlinkDoc(this);detachSharedMarkers(findSharedMarkers(this));break;
        }
      }if (other.history == this.history) {
        var splitIds = [other.id];linkedDocs(other, function (doc) {
          return splitIds.push(doc.id);
        }, true);other.history = new History(null);other.history.done = copyHistoryArray(this.history.done, splitIds);other.history.undone = copyHistoryArray(this.history.undone, splitIds);
      }
    }, iterLinkedDocs: function iterLinkedDocs(f) {
      linkedDocs(this, f);
    }, getMode: function getMode() {
      return this.mode;
    }, getEditor: function getEditor() {
      return this.cm;
    }, splitLines: function splitLines(str) {
      if (this.lineSep) {
        return str.split(this.lineSep);
      }return splitLinesAuto(str);
    }, lineSeparator: function lineSeparator() {
      return this.lineSep || "\n";
    }, setDirection: docMethodOp(function (dir) {
      if (dir != "rtl") {
        dir = "ltr";
      }if (dir == this.direction) {
        return;
      }this.direction = dir;this.iter(function (line) {
        return line.order = null;
      });if (this.cm) {
        directionChanged(this.cm);
      }
    }) });Doc.prototype.eachLine = Doc.prototype.iter;var lastDrop = 0;function onDrop(e) {
    var cm = this;clearDragCursor(cm);if (signalDOMEvent(cm, e) || eventInWidget(cm.display, e)) {
      return;
    }e_preventDefault(e);if (ie) {
      lastDrop = +new Date();
    }var pos = posFromMouse(cm, e, true),
        files = e.dataTransfer.files;if (!pos || cm.isReadOnly()) {
      return;
    }if (files && files.length && window.FileReader && window.File) {
      var n = files.length,
          text = Array(n),
          read = 0;var loadFile = function loadFile(file, i) {
        if (cm.options.allowDropFileTypes && indexOf(cm.options.allowDropFileTypes, file.type) == -1) {
          return;
        }var reader = new FileReader();reader.onload = operation(cm, function () {
          var content = reader.result;if (/[\x00-\x08\x0e-\x1f]{2}/.test(content)) {
            content = "";
          }text[i] = content;if (++read == n) {
            pos = _clipPos(cm.doc, pos);var change = { from: pos, to: pos, text: cm.doc.splitLines(text.join(cm.doc.lineSeparator())), origin: "paste" };makeChange(cm.doc, change);setSelectionReplaceHistory(cm.doc, simpleSelection(pos, changeEnd(change)));
          }
        });reader.readAsText(file);
      };for (var i = 0; i < n; ++i) {
        loadFile(files[i], i);
      }
    } else {
      if (cm.state.draggingText && cm.doc.sel.contains(pos) > -1) {
        cm.state.draggingText(e);setTimeout(function () {
          return cm.display.input.focus();
        }, 20);return;
      }try {
        var text$1 = e.dataTransfer.getData("Text");if (text$1) {
          var selected;if (cm.state.draggingText && !cm.state.draggingText.copy) {
            selected = cm.listSelections();
          }setSelectionNoUndo(cm.doc, simpleSelection(pos, pos));if (selected) {
            for (var i$1 = 0; i$1 < selected.length; ++i$1) {
              _replaceRange(cm.doc, "", selected[i$1].anchor, selected[i$1].head, "drag");
            }
          }cm.replaceSelection(text$1, "around", "paste");cm.display.input.focus();
        }
      } catch (e) {}
    }
  }function onDragStart(cm, e) {
    if (ie && (!cm.state.draggingText || +new Date() - lastDrop < 100)) {
      e_stop(e);return;
    }if (signalDOMEvent(cm, e) || eventInWidget(cm.display, e)) {
      return;
    }e.dataTransfer.setData("Text", cm.getSelection());e.dataTransfer.effectAllowed = "copyMove";if (e.dataTransfer.setDragImage && !safari) {
      var img = elt("img", null, null, "position: fixed; left: 0; top: 0;");img.src = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==";if (presto) {
        img.width = img.height = 1;cm.display.wrapper.appendChild(img);img._top = img.offsetTop;
      }e.dataTransfer.setDragImage(img, 0, 0);if (presto) {
        img.parentNode.removeChild(img);
      }
    }
  }function onDragOver(cm, e) {
    var pos = posFromMouse(cm, e);if (!pos) {
      return;
    }var frag = document.createDocumentFragment();drawSelectionCursor(cm, pos, frag);if (!cm.display.dragCursor) {
      cm.display.dragCursor = elt("div", null, "CodeMirror-cursors CodeMirror-dragcursors");cm.display.lineSpace.insertBefore(cm.display.dragCursor, cm.display.cursorDiv);
    }removeChildrenAndAdd(cm.display.dragCursor, frag);
  }function clearDragCursor(cm) {
    if (cm.display.dragCursor) {
      cm.display.lineSpace.removeChild(cm.display.dragCursor);cm.display.dragCursor = null;
    }
  }function forEachCodeMirror(f) {
    if (!document.getElementsByClassName) {
      return;
    }var byClass = document.getElementsByClassName("CodeMirror"),
        editors = [];for (var i = 0; i < byClass.length; i++) {
      var cm = byClass[i].CodeMirror;if (cm) {
        editors.push(cm);
      }
    }if (editors.length) {
      editors[0].operation(function () {
        for (var i = 0; i < editors.length; i++) {
          f(editors[i]);
        }
      });
    }
  }var globalsRegistered = false;function ensureGlobalHandlers() {
    if (globalsRegistered) {
      return;
    }registerGlobalHandlers();globalsRegistered = true;
  }function registerGlobalHandlers() {
    var resizeTimer;on(window, "resize", function () {
      if (resizeTimer == null) {
        resizeTimer = setTimeout(function () {
          resizeTimer = null;forEachCodeMirror(onResize);
        }, 100);
      }
    });on(window, "blur", function () {
      return forEachCodeMirror(onBlur);
    });
  }function onResize(cm) {
    var d = cm.display;d.cachedCharWidth = d.cachedTextHeight = d.cachedPaddingH = null;d.scrollbarsClipped = false;cm.setSize();
  }var keyNames = { 3: "Pause", 8: "Backspace", 9: "Tab", 13: "Enter", 16: "Shift", 17: "Ctrl", 18: "Alt", 19: "Pause", 20: "CapsLock", 27: "Esc", 32: "Space", 33: "PageUp", 34: "PageDown", 35: "End", 36: "Home", 37: "Left", 38: "Up", 39: "Right", 40: "Down", 44: "PrintScrn", 45: "Insert", 46: "Delete", 59: ";", 61: "=", 91: "Mod", 92: "Mod", 93: "Mod", 106: "*", 107: "=", 109: "-", 110: ".", 111: "/", 145: "ScrollLock", 173: "-", 186: ";", 187: "=", 188: ",", 189: "-", 190: ".", 191: "/", 192: "`", 219: "[", 220: "\\", 221: "]", 222: "'", 63232: "Up", 63233: "Down", 63234: "Left", 63235: "Right", 63272: "Delete", 63273: "Home", 63275: "End", 63276: "PageUp", 63277: "PageDown", 63302: "Insert" };for (var i = 0; i < 10; i++) {
    keyNames[i + 48] = keyNames[i + 96] = String(i);
  }for (var i$1 = 65; i$1 <= 90; i$1++) {
    keyNames[i$1] = String.fromCharCode(i$1);
  }for (var i$2 = 1; i$2 <= 12; i$2++) {
    keyNames[i$2 + 111] = keyNames[i$2 + 63235] = "F" + i$2;
  }var keyMap = {};keyMap.basic = { Left: "goCharLeft", Right: "goCharRight", Up: "goLineUp", Down: "goLineDown", End: "goLineEnd", Home: "goLineStartSmart", PageUp: "goPageUp", PageDown: "goPageDown", Delete: "delCharAfter", Backspace: "delCharBefore", "Shift-Backspace": "delCharBefore", Tab: "defaultTab", "Shift-Tab": "indentAuto", Enter: "newlineAndIndent", Insert: "toggleOverwrite", Esc: "singleSelection" };keyMap.pcDefault = { "Ctrl-A": "selectAll", "Ctrl-D": "deleteLine", "Ctrl-Z": "undo", "Shift-Ctrl-Z": "redo", "Ctrl-Y": "redo", "Ctrl-Home": "goDocStart", "Ctrl-End": "goDocEnd", "Ctrl-Up": "goLineUp", "Ctrl-Down": "goLineDown", "Ctrl-Left": "goGroupLeft", "Ctrl-Right": "goGroupRight", "Alt-Left": "goLineStart", "Alt-Right": "goLineEnd", "Ctrl-Backspace": "delGroupBefore", "Ctrl-Delete": "delGroupAfter", "Ctrl-S": "save", "Ctrl-F": "find", "Ctrl-G": "findNext", "Shift-Ctrl-G": "findPrev", "Shift-Ctrl-F": "replace", "Shift-Ctrl-R": "replaceAll", "Ctrl-[": "indentLess", "Ctrl-]": "indentMore", "Ctrl-U": "undoSelection", "Shift-Ctrl-U": "redoSelection", "Alt-U": "redoSelection", fallthrough: "basic" };keyMap.emacsy = { "Ctrl-F": "goCharRight", "Ctrl-B": "goCharLeft", "Ctrl-P": "goLineUp", "Ctrl-N": "goLineDown", "Alt-F": "goWordRight", "Alt-B": "goWordLeft", "Ctrl-A": "goLineStart", "Ctrl-E": "goLineEnd", "Ctrl-V": "goPageDown", "Shift-Ctrl-V": "goPageUp", "Ctrl-D": "delCharAfter", "Ctrl-H": "delCharBefore", "Alt-D": "delWordAfter", "Alt-Backspace": "delWordBefore", "Ctrl-K": "killLine", "Ctrl-T": "transposeChars", "Ctrl-O": "openLine" };keyMap.macDefault = { "Cmd-A": "selectAll", "Cmd-D": "deleteLine", "Cmd-Z": "undo", "Shift-Cmd-Z": "redo", "Cmd-Y": "redo", "Cmd-Home": "goDocStart", "Cmd-Up": "goDocStart", "Cmd-End": "goDocEnd", "Cmd-Down": "goDocEnd", "Alt-Left": "goGroupLeft", "Alt-Right": "goGroupRight", "Cmd-Left": "goLineLeft", "Cmd-Right": "goLineRight", "Alt-Backspace": "delGroupBefore", "Ctrl-Alt-Backspace": "delGroupAfter", "Alt-Delete": "delGroupAfter", "Cmd-S": "save", "Cmd-F": "find", "Cmd-G": "findNext", "Shift-Cmd-G": "findPrev", "Cmd-Alt-F": "replace", "Shift-Cmd-Alt-F": "replaceAll", "Cmd-[": "indentLess", "Cmd-]": "indentMore", "Cmd-Backspace": "delWrappedLineLeft", "Cmd-Delete": "delWrappedLineRight", "Cmd-U": "undoSelection", "Shift-Cmd-U": "redoSelection", "Ctrl-Up": "goDocStart", "Ctrl-Down": "goDocEnd", fallthrough: ["basic", "emacsy"] };keyMap["default"] = mac ? keyMap.macDefault : keyMap.pcDefault;function normalizeKeyName(name) {
    var parts = name.split(/-(?!$)/);name = parts[parts.length - 1];var alt, ctrl, shift, cmd;for (var i = 0; i < parts.length - 1; i++) {
      var mod = parts[i];if (/^(cmd|meta|m)$/i.test(mod)) {
        cmd = true;
      } else if (/^a(lt)?$/i.test(mod)) {
        alt = true;
      } else if (/^(c|ctrl|control)$/i.test(mod)) {
        ctrl = true;
      } else if (/^s(hift)?$/i.test(mod)) {
        shift = true;
      } else {
        throw new Error("Unrecognized modifier name: " + mod);
      }
    }if (alt) {
      name = "Alt-" + name;
    }if (ctrl) {
      name = "Ctrl-" + name;
    }if (cmd) {
      name = "Cmd-" + name;
    }if (shift) {
      name = "Shift-" + name;
    }return name;
  }function normalizeKeyMap(keymap) {
    var copy = {};for (var keyname in keymap) {
      if (keymap.hasOwnProperty(keyname)) {
        var value = keymap[keyname];if (/^(name|fallthrough|(de|at)tach)$/.test(keyname)) {
          continue;
        }if (value == "...") {
          delete keymap[keyname];continue;
        }var keys = map(keyname.split(" "), normalizeKeyName);for (var i = 0; i < keys.length; i++) {
          var val = void 0,
              name = void 0;if (i == keys.length - 1) {
            name = keys.join(" ");val = value;
          } else {
            name = keys.slice(0, i + 1).join(" ");val = "...";
          }var prev = copy[name];if (!prev) {
            copy[name] = val;
          } else if (prev != val) {
            throw new Error("Inconsistent bindings for " + name);
          }
        }delete keymap[keyname];
      }
    }for (var prop in copy) {
      keymap[prop] = copy[prop];
    }return keymap;
  }function lookupKey(key, map$$1, handle, context) {
    map$$1 = getKeyMap(map$$1);var found = map$$1.call ? map$$1.call(key, context) : map$$1[key];if (found === false) {
      return "nothing";
    }if (found === "...") {
      return "multi";
    }if (found != null && handle(found)) {
      return "handled";
    }if (map$$1.fallthrough) {
      if (Object.prototype.toString.call(map$$1.fallthrough) != "[object Array]") {
        return lookupKey(key, map$$1.fallthrough, handle, context);
      }for (var i = 0; i < map$$1.fallthrough.length; i++) {
        var result = lookupKey(key, map$$1.fallthrough[i], handle, context);if (result) {
          return result;
        }
      }
    }
  }function isModifierKey(value) {
    var name = typeof value == "string" ? value : keyNames[value.keyCode];return name == "Ctrl" || name == "Alt" || name == "Shift" || name == "Mod";
  }function addModifierNames(name, event, noShift) {
    var base = name;if (event.altKey && base != "Alt") {
      name = "Alt-" + name;
    }if ((flipCtrlCmd ? event.metaKey : event.ctrlKey) && base != "Ctrl") {
      name = "Ctrl-" + name;
    }if ((flipCtrlCmd ? event.ctrlKey : event.metaKey) && base != "Cmd") {
      name = "Cmd-" + name;
    }if (!noShift && event.shiftKey && base != "Shift") {
      name = "Shift-" + name;
    }return name;
  }function keyName(event, noShift) {
    if (presto && event.keyCode == 34 && event["char"]) {
      return false;
    }var name = keyNames[event.keyCode];if (name == null || event.altGraphKey) {
      return false;
    }if (event.keyCode == 3 && event.code) {
      name = event.code;
    }return addModifierNames(name, event, noShift);
  }function getKeyMap(val) {
    return typeof val == "string" ? keyMap[val] : val;
  }function deleteNearSelection(cm, compute) {
    var ranges = cm.doc.sel.ranges,
        kill = [];for (var i = 0; i < ranges.length; i++) {
      var toKill = compute(ranges[i]);while (kill.length && cmp(toKill.from, lst(kill).to) <= 0) {
        var replaced = kill.pop();if (cmp(replaced.from, toKill.from) < 0) {
          toKill.from = replaced.from;break;
        }
      }kill.push(toKill);
    }runInOp(cm, function () {
      for (var i = kill.length - 1; i >= 0; i--) {
        _replaceRange(cm.doc, "", kill[i].from, kill[i].to, "+delete");
      }ensureCursorVisible(cm);
    });
  }function moveCharLogically(line, ch, dir) {
    var target = skipExtendingChars(line.text, ch + dir, dir);return target < 0 || target > line.text.length ? null : target;
  }function moveLogically(line, start, dir) {
    var ch = moveCharLogically(line, start.ch, dir);return ch == null ? null : new Pos(start.line, ch, dir < 0 ? "after" : "before");
  }function endOfLine(visually, cm, lineObj, lineNo, dir) {
    if (visually) {
      var order = getOrder(lineObj, cm.doc.direction);if (order) {
        var part = dir < 0 ? lst(order) : order[0];var moveInStorageOrder = dir < 0 == (part.level == 1);var sticky = moveInStorageOrder ? "after" : "before";var ch;if (part.level > 0 || cm.doc.direction == "rtl") {
          var prep = prepareMeasureForLine(cm, lineObj);ch = dir < 0 ? lineObj.text.length - 1 : 0;var targetTop = measureCharPrepared(cm, prep, ch).top;ch = findFirst(function (ch) {
            return measureCharPrepared(cm, prep, ch).top == targetTop;
          }, dir < 0 == (part.level == 1) ? part.from : part.to - 1, ch);if (sticky == "before") {
            ch = moveCharLogically(lineObj, ch, 1);
          }
        } else {
          ch = dir < 0 ? part.to : part.from;
        }return new Pos(lineNo, ch, sticky);
      }
    }return new Pos(lineNo, dir < 0 ? lineObj.text.length : 0, dir < 0 ? "before" : "after");
  }function moveVisually(cm, line, start, dir) {
    var bidi = getOrder(line, cm.doc.direction);if (!bidi) {
      return moveLogically(line, start, dir);
    }if (start.ch >= line.text.length) {
      start.ch = line.text.length;start.sticky = "before";
    } else if (start.ch <= 0) {
      start.ch = 0;start.sticky = "after";
    }var partPos = getBidiPartAt(bidi, start.ch, start.sticky),
        part = bidi[partPos];if (cm.doc.direction == "ltr" && part.level % 2 == 0 && (dir > 0 ? part.to > start.ch : part.from < start.ch)) {
      return moveLogically(line, start, dir);
    }var mv = function mv(pos, dir) {
      return moveCharLogically(line, pos instanceof Pos ? pos.ch : pos, dir);
    };var prep;var getWrappedLineExtent = function getWrappedLineExtent(ch) {
      if (!cm.options.lineWrapping) {
        return { begin: 0, end: line.text.length };
      }prep = prep || prepareMeasureForLine(cm, line);return wrappedLineExtentChar(cm, line, prep, ch);
    };var wrappedLineExtent = getWrappedLineExtent(start.sticky == "before" ? mv(start, -1) : start.ch);if (cm.doc.direction == "rtl" || part.level == 1) {
      var moveInStorageOrder = part.level == 1 == dir < 0;var ch = mv(start, moveInStorageOrder ? 1 : -1);if (ch != null && (!moveInStorageOrder ? ch >= part.from && ch >= wrappedLineExtent.begin : ch <= part.to && ch <= wrappedLineExtent.end)) {
        var sticky = moveInStorageOrder ? "before" : "after";return new Pos(start.line, ch, sticky);
      }
    }var searchInVisualLine = function searchInVisualLine(partPos, dir, wrappedLineExtent) {
      var getRes = function getRes(ch, moveInStorageOrder) {
        return moveInStorageOrder ? new Pos(start.line, mv(ch, 1), "before") : new Pos(start.line, ch, "after");
      };for (; partPos >= 0 && partPos < bidi.length; partPos += dir) {
        var part = bidi[partPos];var moveInStorageOrder = dir > 0 == (part.level != 1);var ch = moveInStorageOrder ? wrappedLineExtent.begin : mv(wrappedLineExtent.end, -1);if (part.from <= ch && ch < part.to) {
          return getRes(ch, moveInStorageOrder);
        }ch = moveInStorageOrder ? part.from : mv(part.to, -1);if (wrappedLineExtent.begin <= ch && ch < wrappedLineExtent.end) {
          return getRes(ch, moveInStorageOrder);
        }
      }
    };var res = searchInVisualLine(partPos + dir, dir, wrappedLineExtent);if (res) {
      return res;
    }var nextCh = dir > 0 ? wrappedLineExtent.end : mv(wrappedLineExtent.begin, -1);if (nextCh != null && !(dir > 0 && nextCh == line.text.length)) {
      res = searchInVisualLine(dir > 0 ? 0 : bidi.length - 1, dir, getWrappedLineExtent(nextCh));if (res) {
        return res;
      }
    }return null;
  }var commands = { selectAll: selectAll, singleSelection: function singleSelection(cm) {
      return cm.setSelection(cm.getCursor("anchor"), cm.getCursor("head"), sel_dontScroll);
    }, killLine: function killLine(cm) {
      return deleteNearSelection(cm, function (range) {
        if (range.empty()) {
          var len = getLine(cm.doc, range.head.line).text.length;if (range.head.ch == len && range.head.line < cm.lastLine()) {
            return { from: range.head, to: Pos(range.head.line + 1, 0) };
          } else {
            return { from: range.head, to: Pos(range.head.line, len) };
          }
        } else {
          return { from: range.from(), to: range.to() };
        }
      });
    }, deleteLine: function deleteLine(cm) {
      return deleteNearSelection(cm, function (range) {
        return { from: Pos(range.from().line, 0), to: _clipPos(cm.doc, Pos(range.to().line + 1, 0)) };
      });
    }, delLineLeft: function delLineLeft(cm) {
      return deleteNearSelection(cm, function (range) {
        return { from: Pos(range.from().line, 0), to: range.from() };
      });
    }, delWrappedLineLeft: function delWrappedLineLeft(cm) {
      return deleteNearSelection(cm, function (range) {
        var top = cm.charCoords(range.head, "div").top + 5;var leftPos = cm.coordsChar({ left: 0, top: top }, "div");return { from: leftPos, to: range.from() };
      });
    }, delWrappedLineRight: function delWrappedLineRight(cm) {
      return deleteNearSelection(cm, function (range) {
        var top = cm.charCoords(range.head, "div").top + 5;var rightPos = cm.coordsChar({ left: cm.display.lineDiv.offsetWidth + 100, top: top }, "div");return { from: range.from(), to: rightPos };
      });
    }, undo: function undo(cm) {
      return cm.undo();
    }, redo: function redo(cm) {
      return cm.redo();
    }, undoSelection: function undoSelection(cm) {
      return cm.undoSelection();
    }, redoSelection: function redoSelection(cm) {
      return cm.redoSelection();
    }, goDocStart: function goDocStart(cm) {
      return cm.extendSelection(Pos(cm.firstLine(), 0));
    }, goDocEnd: function goDocEnd(cm) {
      return cm.extendSelection(Pos(cm.lastLine()));
    }, goLineStart: function goLineStart(cm) {
      return cm.extendSelectionsBy(function (range) {
        return lineStart(cm, range.head.line);
      }, { origin: "+move", bias: 1 });
    }, goLineStartSmart: function goLineStartSmart(cm) {
      return cm.extendSelectionsBy(function (range) {
        return lineStartSmart(cm, range.head);
      }, { origin: "+move", bias: 1 });
    }, goLineEnd: function goLineEnd(cm) {
      return cm.extendSelectionsBy(function (range) {
        return lineEnd(cm, range.head.line);
      }, { origin: "+move", bias: -1 });
    }, goLineRight: function goLineRight(cm) {
      return cm.extendSelectionsBy(function (range) {
        var top = cm.cursorCoords(range.head, "div").top + 5;return cm.coordsChar({ left: cm.display.lineDiv.offsetWidth + 100, top: top }, "div");
      }, sel_move);
    }, goLineLeft: function goLineLeft(cm) {
      return cm.extendSelectionsBy(function (range) {
        var top = cm.cursorCoords(range.head, "div").top + 5;return cm.coordsChar({ left: 0, top: top }, "div");
      }, sel_move);
    }, goLineLeftSmart: function goLineLeftSmart(cm) {
      return cm.extendSelectionsBy(function (range) {
        var top = cm.cursorCoords(range.head, "div").top + 5;var pos = cm.coordsChar({ left: 0, top: top }, "div");if (pos.ch < cm.getLine(pos.line).search(/\S/)) {
          return lineStartSmart(cm, range.head);
        }return pos;
      }, sel_move);
    }, goLineUp: function goLineUp(cm) {
      return cm.moveV(-1, "line");
    }, goLineDown: function goLineDown(cm) {
      return cm.moveV(1, "line");
    }, goPageUp: function goPageUp(cm) {
      return cm.moveV(-1, "page");
    }, goPageDown: function goPageDown(cm) {
      return cm.moveV(1, "page");
    }, goCharLeft: function goCharLeft(cm) {
      return cm.moveH(-1, "char");
    }, goCharRight: function goCharRight(cm) {
      return cm.moveH(1, "char");
    }, goColumnLeft: function goColumnLeft(cm) {
      return cm.moveH(-1, "column");
    }, goColumnRight: function goColumnRight(cm) {
      return cm.moveH(1, "column");
    }, goWordLeft: function goWordLeft(cm) {
      return cm.moveH(-1, "word");
    }, goGroupRight: function goGroupRight(cm) {
      return cm.moveH(1, "group");
    }, goGroupLeft: function goGroupLeft(cm) {
      return cm.moveH(-1, "group");
    }, goWordRight: function goWordRight(cm) {
      return cm.moveH(1, "word");
    }, delCharBefore: function delCharBefore(cm) {
      return cm.deleteH(-1, "char");
    }, delCharAfter: function delCharAfter(cm) {
      return cm.deleteH(1, "char");
    }, delWordBefore: function delWordBefore(cm) {
      return cm.deleteH(-1, "word");
    }, delWordAfter: function delWordAfter(cm) {
      return cm.deleteH(1, "word");
    }, delGroupBefore: function delGroupBefore(cm) {
      return cm.deleteH(-1, "group");
    }, delGroupAfter: function delGroupAfter(cm) {
      return cm.deleteH(1, "group");
    }, indentAuto: function indentAuto(cm) {
      return cm.indentSelection("smart");
    }, indentMore: function indentMore(cm) {
      return cm.indentSelection("add");
    }, indentLess: function indentLess(cm) {
      return cm.indentSelection("subtract");
    }, insertTab: function insertTab(cm) {
      return cm.replaceSelection("\t");
    }, insertSoftTab: function insertSoftTab(cm) {
      var spaces = [],
          ranges = cm.listSelections(),
          tabSize = cm.options.tabSize;for (var i = 0; i < ranges.length; i++) {
        var pos = ranges[i].from();var col = countColumn(cm.getLine(pos.line), pos.ch, tabSize);spaces.push(spaceStr(tabSize - col % tabSize));
      }cm.replaceSelections(spaces);
    }, defaultTab: function defaultTab(cm) {
      if (cm.somethingSelected()) {
        cm.indentSelection("add");
      } else {
        cm.execCommand("insertTab");
      }
    }, transposeChars: function transposeChars(cm) {
      return runInOp(cm, function () {
        var ranges = cm.listSelections(),
            newSel = [];for (var i = 0; i < ranges.length; i++) {
          if (!ranges[i].empty()) {
            continue;
          }var cur = ranges[i].head,
              line = getLine(cm.doc, cur.line).text;if (line) {
            if (cur.ch == line.length) {
              cur = new Pos(cur.line, cur.ch - 1);
            }if (cur.ch > 0) {
              cur = new Pos(cur.line, cur.ch + 1);cm.replaceRange(line.charAt(cur.ch - 1) + line.charAt(cur.ch - 2), Pos(cur.line, cur.ch - 2), cur, "+transpose");
            } else if (cur.line > cm.doc.first) {
              var prev = getLine(cm.doc, cur.line - 1).text;if (prev) {
                cur = new Pos(cur.line, 1);cm.replaceRange(line.charAt(0) + cm.doc.lineSeparator() + prev.charAt(prev.length - 1), Pos(cur.line - 1, prev.length - 1), cur, "+transpose");
              }
            }
          }newSel.push(new Range(cur, cur));
        }cm.setSelections(newSel);
      });
    }, newlineAndIndent: function newlineAndIndent(cm) {
      return runInOp(cm, function () {
        var sels = cm.listSelections();for (var i = sels.length - 1; i >= 0; i--) {
          cm.replaceRange(cm.doc.lineSeparator(), sels[i].anchor, sels[i].head, "+input");
        }sels = cm.listSelections();for (var i$1 = 0; i$1 < sels.length; i$1++) {
          cm.indentLine(sels[i$1].from().line, null, true);
        }ensureCursorVisible(cm);
      });
    }, openLine: function openLine(cm) {
      return cm.replaceSelection("\n", "start");
    }, toggleOverwrite: function toggleOverwrite(cm) {
      return cm.toggleOverwrite();
    } };function lineStart(cm, lineN) {
    var line = getLine(cm.doc, lineN);var visual = visualLine(line);if (visual != line) {
      lineN = lineNo(visual);
    }return endOfLine(true, cm, visual, lineN, 1);
  }function lineEnd(cm, lineN) {
    var line = getLine(cm.doc, lineN);var visual = visualLineEnd(line);if (visual != line) {
      lineN = lineNo(visual);
    }return endOfLine(true, cm, line, lineN, -1);
  }function lineStartSmart(cm, pos) {
    var start = lineStart(cm, pos.line);var line = getLine(cm.doc, start.line);var order = getOrder(line, cm.doc.direction);if (!order || order[0].level == 0) {
      var firstNonWS = Math.max(0, line.text.search(/\S/));var inWS = pos.line == start.line && pos.ch <= firstNonWS && pos.ch;return Pos(start.line, inWS ? 0 : firstNonWS, start.sticky);
    }return start;
  }function doHandleBinding(cm, bound, dropShift) {
    if (typeof bound == "string") {
      bound = commands[bound];if (!bound) {
        return false;
      }
    }cm.display.input.ensurePolled();var prevShift = cm.display.shift,
        done = false;try {
      if (cm.isReadOnly()) {
        cm.state.suppressEdits = true;
      }if (dropShift) {
        cm.display.shift = false;
      }done = bound(cm) != Pass;
    } finally {
      cm.display.shift = prevShift;cm.state.suppressEdits = false;
    }return done;
  }function lookupKeyForEditor(cm, name, handle) {
    for (var i = 0; i < cm.state.keyMaps.length; i++) {
      var result = lookupKey(name, cm.state.keyMaps[i], handle, cm);if (result) {
        return result;
      }
    }return cm.options.extraKeys && lookupKey(name, cm.options.extraKeys, handle, cm) || lookupKey(name, cm.options.keyMap, handle, cm);
  }var stopSeq = new Delayed();function dispatchKey(cm, name, e, handle) {
    var seq = cm.state.keySeq;if (seq) {
      if (isModifierKey(name)) {
        return "handled";
      }if (/\'$/.test(name)) {
        cm.state.keySeq = null;
      } else {
        stopSeq.set(50, function () {
          if (cm.state.keySeq == seq) {
            cm.state.keySeq = null;cm.display.input.reset();
          }
        });
      }if (dispatchKeyInner(cm, seq + " " + name, e, handle)) {
        return true;
      }
    }return dispatchKeyInner(cm, name, e, handle);
  }function dispatchKeyInner(cm, name, e, handle) {
    var result = lookupKeyForEditor(cm, name, handle);if (result == "multi") {
      cm.state.keySeq = name;
    }if (result == "handled") {
      signalLater(cm, "keyHandled", cm, name, e);
    }if (result == "handled" || result == "multi") {
      e_preventDefault(e);restartBlink(cm);
    }return !!result;
  }function handleKeyBinding(cm, e) {
    var name = keyName(e, true);if (!name) {
      return false;
    }if (e.shiftKey && !cm.state.keySeq) {
      return dispatchKey(cm, "Shift-" + name, e, function (b) {
        return doHandleBinding(cm, b, true);
      }) || dispatchKey(cm, name, e, function (b) {
        if (typeof b == "string" ? /^go[A-Z]/.test(b) : b.motion) {
          return doHandleBinding(cm, b);
        }
      });
    } else {
      return dispatchKey(cm, name, e, function (b) {
        return doHandleBinding(cm, b);
      });
    }
  }function handleCharBinding(cm, e, ch) {
    return dispatchKey(cm, "'" + ch + "'", e, function (b) {
      return doHandleBinding(cm, b, true);
    });
  }var lastStoppedKey = null;function onKeyDown(e) {
    var cm = this;cm.curOp.focus = activeElt();if (signalDOMEvent(cm, e)) {
      return;
    }if (ie && ie_version < 11 && e.keyCode == 27) {
      e.returnValue = false;
    }var code = e.keyCode;cm.display.shift = code == 16 || e.shiftKey;var handled = handleKeyBinding(cm, e);if (presto) {
      lastStoppedKey = handled ? code : null;if (!handled && code == 88 && !hasCopyEvent && (mac ? e.metaKey : e.ctrlKey)) {
        cm.replaceSelection("", null, "cut");
      }
    }if (code == 18 && !/\bCodeMirror-crosshair\b/.test(cm.display.lineDiv.className)) {
      showCrossHair(cm);
    }
  }function showCrossHair(cm) {
    var lineDiv = cm.display.lineDiv;addClass(lineDiv, "CodeMirror-crosshair");function up(e) {
      if (e.keyCode == 18 || !e.altKey) {
        rmClass(lineDiv, "CodeMirror-crosshair");off(document, "keyup", up);off(document, "mouseover", up);
      }
    }on(document, "keyup", up);on(document, "mouseover", up);
  }function onKeyUp(e) {
    if (e.keyCode == 16) {
      this.doc.sel.shift = false;
    }signalDOMEvent(this, e);
  }function onKeyPress(e) {
    var cm = this;if (eventInWidget(cm.display, e) || signalDOMEvent(cm, e) || e.ctrlKey && !e.altKey || mac && e.metaKey) {
      return;
    }var keyCode = e.keyCode,
        charCode = e.charCode;if (presto && keyCode == lastStoppedKey) {
      lastStoppedKey = null;e_preventDefault(e);return;
    }if (presto && (!e.which || e.which < 10) && handleKeyBinding(cm, e)) {
      return;
    }var ch = String.fromCharCode(charCode == null ? keyCode : charCode);if (ch == "\b") {
      return;
    }if (handleCharBinding(cm, e, ch)) {
      return;
    }cm.display.input.onKeyPress(e);
  }var DOUBLECLICK_DELAY = 400;var PastClick = function PastClick(time, pos, button) {
    this.time = time;this.pos = pos;this.button = button;
  };PastClick.prototype.compare = function (time, pos, button) {
    return this.time + DOUBLECLICK_DELAY > time && cmp(pos, this.pos) == 0 && button == this.button;
  };var lastClick, lastDoubleClick;function clickRepeat(pos, button) {
    var now = +new Date();if (lastDoubleClick && lastDoubleClick.compare(now, pos, button)) {
      lastClick = lastDoubleClick = null;return "triple";
    } else if (lastClick && lastClick.compare(now, pos, button)) {
      lastDoubleClick = new PastClick(now, pos, button);lastClick = null;return "double";
    } else {
      lastClick = new PastClick(now, pos, button);lastDoubleClick = null;return "single";
    }
  }function onMouseDown(e) {
    var cm = this,
        display = cm.display;if (signalDOMEvent(cm, e) || display.activeTouch && display.input.supportsTouch()) {
      return;
    }display.input.ensurePolled();display.shift = e.shiftKey;if (eventInWidget(display, e)) {
      if (!webkit) {
        display.scroller.draggable = false;setTimeout(function () {
          return display.scroller.draggable = true;
        }, 100);
      }return;
    }if (clickInGutter(cm, e)) {
      return;
    }var pos = posFromMouse(cm, e),
        button = e_button(e),
        repeat = pos ? clickRepeat(pos, button) : "single";window.focus();if (button == 1 && cm.state.selectingText) {
      cm.state.selectingText(e);
    }if (pos && handleMappedButton(cm, button, pos, repeat, e)) {
      return;
    }if (button == 1) {
      if (pos) {
        leftButtonDown(cm, pos, repeat, e);
      } else if (e_target(e) == display.scroller) {
        e_preventDefault(e);
      }
    } else if (button == 2) {
      if (pos) {
        extendSelection(cm.doc, pos);
      }setTimeout(function () {
        return display.input.focus();
      }, 20);
    } else if (button == 3) {
      if (captureRightClick) {
        cm.display.input.onContextMenu(e);
      } else {
        delayBlurEvent(cm);
      }
    }
  }function handleMappedButton(cm, button, pos, repeat, event) {
    var name = "Click";if (repeat == "double") {
      name = "Double" + name;
    } else if (repeat == "triple") {
      name = "Triple" + name;
    }name = (button == 1 ? "Left" : button == 2 ? "Middle" : "Right") + name;return dispatchKey(cm, addModifierNames(name, event), event, function (bound) {
      if (typeof bound == "string") {
        bound = commands[bound];
      }if (!bound) {
        return false;
      }var done = false;try {
        if (cm.isReadOnly()) {
          cm.state.suppressEdits = true;
        }done = bound(cm, pos) != Pass;
      } finally {
        cm.state.suppressEdits = false;
      }return done;
    });
  }function configureMouse(cm, repeat, event) {
    var option = cm.getOption("configureMouse");var value = option ? option(cm, repeat, event) : {};if (value.unit == null) {
      var rect = chromeOS ? event.shiftKey && event.metaKey : event.altKey;value.unit = rect ? "rectangle" : repeat == "single" ? "char" : repeat == "double" ? "word" : "line";
    }if (value.extend == null || cm.doc.extend) {
      value.extend = cm.doc.extend || event.shiftKey;
    }if (value.addNew == null) {
      value.addNew = mac ? event.metaKey : event.ctrlKey;
    }if (value.moveOnDrag == null) {
      value.moveOnDrag = !(mac ? event.altKey : event.ctrlKey);
    }return value;
  }function leftButtonDown(cm, pos, repeat, event) {
    if (ie) {
      setTimeout(bind(ensureFocus, cm), 0);
    } else {
      cm.curOp.focus = activeElt();
    }var behavior = configureMouse(cm, repeat, event);var sel = cm.doc.sel,
        contained;if (cm.options.dragDrop && dragAndDrop && !cm.isReadOnly() && repeat == "single" && (contained = sel.contains(pos)) > -1 && (cmp((contained = sel.ranges[contained]).from(), pos) < 0 || pos.xRel > 0) && (cmp(contained.to(), pos) > 0 || pos.xRel < 0)) {
      leftButtonStartDrag(cm, event, pos, behavior);
    } else {
      leftButtonSelect(cm, event, pos, behavior);
    }
  }function leftButtonStartDrag(cm, event, pos, behavior) {
    var display = cm.display,
        moved = false;var dragEnd = operation(cm, function (e) {
      if (webkit) {
        display.scroller.draggable = false;
      }cm.state.draggingText = false;off(display.wrapper.ownerDocument, "mouseup", dragEnd);off(display.wrapper.ownerDocument, "mousemove", mouseMove);off(display.scroller, "dragstart", dragStart);off(display.scroller, "drop", dragEnd);if (!moved) {
        e_preventDefault(e);if (!behavior.addNew) {
          extendSelection(cm.doc, pos, null, null, behavior.extend);
        }if (webkit || ie && ie_version == 9) {
          setTimeout(function () {
            display.wrapper.ownerDocument.body.focus();display.input.focus();
          }, 20);
        } else {
          display.input.focus();
        }
      }
    });var mouseMove = function mouseMove(e2) {
      moved = moved || Math.abs(event.clientX - e2.clientX) + Math.abs(event.clientY - e2.clientY) >= 10;
    };var dragStart = function dragStart() {
      return moved = true;
    };if (webkit) {
      display.scroller.draggable = true;
    }cm.state.draggingText = dragEnd;dragEnd.copy = !behavior.moveOnDrag;if (display.scroller.dragDrop) {
      display.scroller.dragDrop();
    }on(display.wrapper.ownerDocument, "mouseup", dragEnd);on(display.wrapper.ownerDocument, "mousemove", mouseMove);on(display.scroller, "dragstart", dragStart);on(display.scroller, "drop", dragEnd);delayBlurEvent(cm);setTimeout(function () {
      return display.input.focus();
    }, 20);
  }function rangeForUnit(cm, pos, unit) {
    if (unit == "char") {
      return new Range(pos, pos);
    }if (unit == "word") {
      return cm.findWordAt(pos);
    }if (unit == "line") {
      return new Range(Pos(pos.line, 0), _clipPos(cm.doc, Pos(pos.line + 1, 0)));
    }var result = unit(cm, pos);return new Range(result.from, result.to);
  }function leftButtonSelect(cm, event, start, behavior) {
    var display = cm.display,
        doc = cm.doc;e_preventDefault(event);var ourRange,
        ourIndex,
        startSel = doc.sel,
        ranges = startSel.ranges;if (behavior.addNew && !behavior.extend) {
      ourIndex = doc.sel.contains(start);if (ourIndex > -1) {
        ourRange = ranges[ourIndex];
      } else {
        ourRange = new Range(start, start);
      }
    } else {
      ourRange = doc.sel.primary();ourIndex = doc.sel.primIndex;
    }if (behavior.unit == "rectangle") {
      if (!behavior.addNew) {
        ourRange = new Range(start, start);
      }start = posFromMouse(cm, event, true, true);ourIndex = -1;
    } else {
      var range$$1 = rangeForUnit(cm, start, behavior.unit);if (behavior.extend) {
        ourRange = extendRange(ourRange, range$$1.anchor, range$$1.head, behavior.extend);
      } else {
        ourRange = range$$1;
      }
    }if (!behavior.addNew) {
      ourIndex = 0;setSelection(doc, new Selection([ourRange], 0), sel_mouse);startSel = doc.sel;
    } else if (ourIndex == -1) {
      ourIndex = ranges.length;setSelection(doc, normalizeSelection(cm, ranges.concat([ourRange]), ourIndex), { scroll: false, origin: "*mouse" });
    } else if (ranges.length > 1 && ranges[ourIndex].empty() && behavior.unit == "char" && !behavior.extend) {
      setSelection(doc, normalizeSelection(cm, ranges.slice(0, ourIndex).concat(ranges.slice(ourIndex + 1)), 0), { scroll: false, origin: "*mouse" });startSel = doc.sel;
    } else {
      replaceOneSelection(doc, ourIndex, ourRange, sel_mouse);
    }var lastPos = start;function extendTo(pos) {
      if (cmp(lastPos, pos) == 0) {
        return;
      }lastPos = pos;if (behavior.unit == "rectangle") {
        var ranges = [],
            tabSize = cm.options.tabSize;var startCol = countColumn(getLine(doc, start.line).text, start.ch, tabSize);var posCol = countColumn(getLine(doc, pos.line).text, pos.ch, tabSize);var left = Math.min(startCol, posCol),
            right = Math.max(startCol, posCol);for (var line = Math.min(start.line, pos.line), end = Math.min(cm.lastLine(), Math.max(start.line, pos.line)); line <= end; line++) {
          var text = getLine(doc, line).text,
              leftPos = findColumn(text, left, tabSize);if (left == right) {
            ranges.push(new Range(Pos(line, leftPos), Pos(line, leftPos)));
          } else if (text.length > leftPos) {
            ranges.push(new Range(Pos(line, leftPos), Pos(line, findColumn(text, right, tabSize))));
          }
        }if (!ranges.length) {
          ranges.push(new Range(start, start));
        }setSelection(doc, normalizeSelection(cm, startSel.ranges.slice(0, ourIndex).concat(ranges), ourIndex), { origin: "*mouse", scroll: false });cm.scrollIntoView(pos);
      } else {
        var oldRange = ourRange;var range$$1 = rangeForUnit(cm, pos, behavior.unit);var anchor = oldRange.anchor,
            head;if (cmp(range$$1.anchor, anchor) > 0) {
          head = range$$1.head;anchor = minPos(oldRange.from(), range$$1.anchor);
        } else {
          head = range$$1.anchor;anchor = maxPos(oldRange.to(), range$$1.head);
        }var ranges$1 = startSel.ranges.slice(0);ranges$1[ourIndex] = bidiSimplify(cm, new Range(_clipPos(doc, anchor), head));setSelection(doc, normalizeSelection(cm, ranges$1, ourIndex), sel_mouse);
      }
    }var editorSize = display.wrapper.getBoundingClientRect();var counter = 0;function extend(e) {
      var curCount = ++counter;var cur = posFromMouse(cm, e, true, behavior.unit == "rectangle");if (!cur) {
        return;
      }if (cmp(cur, lastPos) != 0) {
        cm.curOp.focus = activeElt();extendTo(cur);var visible = visibleLines(display, doc);if (cur.line >= visible.to || cur.line < visible.from) {
          setTimeout(operation(cm, function () {
            if (counter == curCount) {
              extend(e);
            }
          }), 150);
        }
      } else {
        var outside = e.clientY < editorSize.top ? -20 : e.clientY > editorSize.bottom ? 20 : 0;if (outside) {
          setTimeout(operation(cm, function () {
            if (counter != curCount) {
              return;
            }display.scroller.scrollTop += outside;extend(e);
          }), 50);
        }
      }
    }function done(e) {
      cm.state.selectingText = false;counter = Infinity;if (e) {
        e_preventDefault(e);display.input.focus();
      }off(display.wrapper.ownerDocument, "mousemove", move);off(display.wrapper.ownerDocument, "mouseup", up);doc.history.lastSelOrigin = null;
    }var move = operation(cm, function (e) {
      if (e.buttons === 0 || !e_button(e)) {
        done(e);
      } else {
        extend(e);
      }
    });var up = operation(cm, done);cm.state.selectingText = up;on(display.wrapper.ownerDocument, "mousemove", move);on(display.wrapper.ownerDocument, "mouseup", up);
  }function bidiSimplify(cm, range$$1) {
    var anchor = range$$1.anchor;var head = range$$1.head;var anchorLine = getLine(cm.doc, anchor.line);if (cmp(anchor, head) == 0 && anchor.sticky == head.sticky) {
      return range$$1;
    }var order = getOrder(anchorLine);if (!order) {
      return range$$1;
    }var index = getBidiPartAt(order, anchor.ch, anchor.sticky),
        part = order[index];if (part.from != anchor.ch && part.to != anchor.ch) {
      return range$$1;
    }var boundary = index + (part.from == anchor.ch == (part.level != 1) ? 0 : 1);if (boundary == 0 || boundary == order.length) {
      return range$$1;
    }var leftSide;if (head.line != anchor.line) {
      leftSide = (head.line - anchor.line) * (cm.doc.direction == "ltr" ? 1 : -1) > 0;
    } else {
      var headIndex = getBidiPartAt(order, head.ch, head.sticky);var dir = headIndex - index || (head.ch - anchor.ch) * (part.level == 1 ? -1 : 1);if (headIndex == boundary - 1 || headIndex == boundary) {
        leftSide = dir < 0;
      } else {
        leftSide = dir > 0;
      }
    }var usePart = order[boundary + (leftSide ? -1 : 0)];var from = leftSide == (usePart.level == 1);var ch = from ? usePart.from : usePart.to,
        sticky = from ? "after" : "before";return anchor.ch == ch && anchor.sticky == sticky ? range$$1 : new Range(new Pos(anchor.line, ch, sticky), head);
  }function gutterEvent(cm, e, type, prevent) {
    var mX, mY;if (e.touches) {
      mX = e.touches[0].clientX;mY = e.touches[0].clientY;
    } else {
      try {
        mX = e.clientX;mY = e.clientY;
      } catch (e) {
        return false;
      }
    }if (mX >= Math.floor(cm.display.gutters.getBoundingClientRect().right)) {
      return false;
    }if (prevent) {
      e_preventDefault(e);
    }var display = cm.display;var lineBox = display.lineDiv.getBoundingClientRect();if (mY > lineBox.bottom || !hasHandler(cm, type)) {
      return e_defaultPrevented(e);
    }mY -= lineBox.top - display.viewOffset;for (var i = 0; i < cm.display.gutterSpecs.length; ++i) {
      var g = display.gutters.childNodes[i];if (g && g.getBoundingClientRect().right >= mX) {
        var line = _lineAtHeight(cm.doc, mY);var gutter = cm.display.gutterSpecs[i];signal(cm, type, cm, line, gutter.className, e);return e_defaultPrevented(e);
      }
    }
  }function clickInGutter(cm, e) {
    return gutterEvent(cm, e, "gutterClick", true);
  }function onContextMenu(cm, e) {
    if (eventInWidget(cm.display, e) || contextMenuInGutter(cm, e)) {
      return;
    }if (signalDOMEvent(cm, e, "contextmenu")) {
      return;
    }if (!captureRightClick) {
      cm.display.input.onContextMenu(e);
    }
  }function contextMenuInGutter(cm, e) {
    if (!hasHandler(cm, "gutterContextMenu")) {
      return false;
    }return gutterEvent(cm, e, "gutterContextMenu", false);
  }function themeChanged(cm) {
    cm.display.wrapper.className = cm.display.wrapper.className.replace(/\s*cm-s-\S+/g, "") + cm.options.theme.replace(/(^|\s)\s*/g, " cm-s-");clearCaches(cm);
  }var Init = { toString: function toString() {
      return "CodeMirror.Init";
    } };var defaults = {};var optionHandlers = {};function defineOptions(CodeMirror) {
    var optionHandlers = CodeMirror.optionHandlers;function option(name, deflt, handle, notOnInit) {
      CodeMirror.defaults[name] = deflt;if (handle) {
        optionHandlers[name] = notOnInit ? function (cm, val, old) {
          if (old != Init) {
            handle(cm, val, old);
          }
        } : handle;
      }
    }CodeMirror.defineOption = option;CodeMirror.Init = Init;option("value", "", function (cm, val) {
      return cm.setValue(val);
    }, true);option("mode", null, function (cm, val) {
      cm.doc.modeOption = val;loadMode(cm);
    }, true);option("indentUnit", 2, loadMode, true);option("indentWithTabs", false);option("smartIndent", true);option("tabSize", 4, function (cm) {
      resetModeState(cm);clearCaches(cm);regChange(cm);
    }, true);option("lineSeparator", null, function (cm, val) {
      cm.doc.lineSep = val;if (!val) {
        return;
      }var newBreaks = [],
          lineNo = cm.doc.first;cm.doc.iter(function (line) {
        for (var pos = 0;;) {
          var found = line.text.indexOf(val, pos);if (found == -1) {
            break;
          }pos = found + val.length;newBreaks.push(Pos(lineNo, found));
        }lineNo++;
      });for (var i = newBreaks.length - 1; i >= 0; i--) {
        _replaceRange(cm.doc, val, newBreaks[i], Pos(newBreaks[i].line, newBreaks[i].ch + val.length));
      }
    });option("specialChars", /[\u0000-\u001f\u007f-\u009f\u00ad\u061c\u200b-\u200f\u2028\u2029\ufeff\ufff9-\ufffc]/g, function (cm, val, old) {
      cm.state.specialChars = new RegExp(val.source + (val.test("\t") ? "" : "|\t"), "g");if (old != Init) {
        cm.refresh();
      }
    });option("specialCharPlaceholder", defaultSpecialCharPlaceholder, function (cm) {
      return cm.refresh();
    }, true);option("electricChars", true);option("inputStyle", mobile ? "contenteditable" : "textarea", function () {
      throw new Error("inputStyle can not (yet) be changed in a running editor");
    }, true);option("spellcheck", false, function (cm, val) {
      return cm.getInputField().spellcheck = val;
    }, true);option("autocorrect", false, function (cm, val) {
      return cm.getInputField().autocorrect = val;
    }, true);option("autocapitalize", false, function (cm, val) {
      return cm.getInputField().autocapitalize = val;
    }, true);option("rtlMoveVisually", !windows);option("wholeLineUpdateBefore", true);option("theme", "default", function (cm) {
      themeChanged(cm);updateGutters(cm);
    }, true);option("keyMap", "default", function (cm, val, old) {
      var next = getKeyMap(val);var prev = old != Init && getKeyMap(old);if (prev && prev.detach) {
        prev.detach(cm, next);
      }if (next.attach) {
        next.attach(cm, prev || null);
      }
    });option("extraKeys", null);option("configureMouse", null);option("lineWrapping", false, wrappingChanged, true);option("gutters", [], function (cm, val) {
      cm.display.gutterSpecs = getGutters(val, cm.options.lineNumbers);updateGutters(cm);
    }, true);option("fixedGutter", true, function (cm, val) {
      cm.display.gutters.style.left = val ? compensateForHScroll(cm.display) + "px" : "0";cm.refresh();
    }, true);option("coverGutterNextToScrollbar", false, function (cm) {
      return updateScrollbars(cm);
    }, true);option("scrollbarStyle", "native", function (cm) {
      initScrollbars(cm);updateScrollbars(cm);cm.display.scrollbars.setScrollTop(cm.doc.scrollTop);cm.display.scrollbars.setScrollLeft(cm.doc.scrollLeft);
    }, true);option("lineNumbers", false, function (cm, val) {
      cm.display.gutterSpecs = getGutters(cm.options.gutters, val);updateGutters(cm);
    }, true);option("firstLineNumber", 1, updateGutters, true);option("lineNumberFormatter", function (integer) {
      return integer;
    }, updateGutters, true);option("showCursorWhenSelecting", false, updateSelection, true);option("resetSelectionOnContextMenu", true);option("lineWiseCopyCut", true);option("pasteLinesPerSelection", true);option("selectionsMayTouch", false);option("readOnly", false, function (cm, val) {
      if (val == "nocursor") {
        onBlur(cm);cm.display.input.blur();
      }cm.display.input.readOnlyChanged(val);
    });option("disableInput", false, function (cm, val) {
      if (!val) {
        cm.display.input.reset();
      }
    }, true);option("dragDrop", true, dragDropChanged);option("allowDropFileTypes", null);option("cursorBlinkRate", 530);option("cursorScrollMargin", 0);option("cursorHeight", 1, updateSelection, true);option("singleCursorHeightPerLine", true, updateSelection, true);option("workTime", 100);option("workDelay", 100);option("flattenSpans", true, resetModeState, true);option("addModeClass", false, resetModeState, true);option("pollInterval", 100);option("undoDepth", 200, function (cm, val) {
      return cm.doc.history.undoDepth = val;
    });option("historyEventDelay", 1250);option("viewportMargin", 10, function (cm) {
      return cm.refresh();
    }, true);option("maxHighlightLength", 1e4, resetModeState, true);option("moveInputWithCursor", true, function (cm, val) {
      if (!val) {
        cm.display.input.resetPosition();
      }
    });option("tabindex", null, function (cm, val) {
      return cm.display.input.getField().tabIndex = val || "";
    });option("autofocus", null);option("direction", "ltr", function (cm, val) {
      return cm.doc.setDirection(val);
    }, true);option("phrases", null);
  }function dragDropChanged(cm, value, old) {
    var wasOn = old && old != Init;if (!value != !wasOn) {
      var funcs = cm.display.dragFunctions;var toggle = value ? on : off;toggle(cm.display.scroller, "dragstart", funcs.start);toggle(cm.display.scroller, "dragenter", funcs.enter);toggle(cm.display.scroller, "dragover", funcs.over);toggle(cm.display.scroller, "dragleave", funcs.leave);toggle(cm.display.scroller, "drop", funcs.drop);
    }
  }function wrappingChanged(cm) {
    if (cm.options.lineWrapping) {
      addClass(cm.display.wrapper, "CodeMirror-wrap");cm.display.sizer.style.minWidth = "";cm.display.sizerWidth = null;
    } else {
      rmClass(cm.display.wrapper, "CodeMirror-wrap");findMaxLine(cm);
    }estimateLineHeights(cm);regChange(cm);clearCaches(cm);setTimeout(function () {
      return updateScrollbars(cm);
    }, 100);
  }function CodeMirror(place, options) {
    var this$1 = this;if (!(this instanceof CodeMirror)) {
      return new CodeMirror(place, options);
    }this.options = options = options ? copyObj(options) : {};copyObj(defaults, options, false);var doc = options.value;if (typeof doc == "string") {
      doc = new Doc(doc, options.mode, null, options.lineSeparator, options.direction);
    } else if (options.mode) {
      doc.modeOption = options.mode;
    }this.doc = doc;var input = new CodeMirror.inputStyles[options.inputStyle](this);var display = this.display = new Display(place, doc, input, options);display.wrapper.CodeMirror = this;themeChanged(this);if (options.lineWrapping) {
      this.display.wrapper.className += " CodeMirror-wrap";
    }initScrollbars(this);this.state = { keyMaps: [], overlays: [], modeGen: 0, overwrite: false, delayingBlurEvent: false, focused: false, suppressEdits: false, pasteIncoming: -1, cutIncoming: -1, selectingText: false, draggingText: false, highlight: new Delayed(), keySeq: null, specialChars: null };if (options.autofocus && !mobile) {
      display.input.focus();
    }if (ie && ie_version < 11) {
      setTimeout(function () {
        return this$1.display.input.reset(true);
      }, 20);
    }registerEventHandlers(this);ensureGlobalHandlers();_startOperation(this);this.curOp.forceUpdate = true;attachDoc(this, doc);if (options.autofocus && !mobile || this.hasFocus()) {
      setTimeout(bind(onFocus, this), 20);
    } else {
      onBlur(this);
    }for (var opt in optionHandlers) {
      if (optionHandlers.hasOwnProperty(opt)) {
        optionHandlers[opt](this, options[opt], Init);
      }
    }maybeUpdateLineNumberWidth(this);if (options.finishInit) {
      options.finishInit(this);
    }for (var i = 0; i < initHooks.length; ++i) {
      initHooks[i](this);
    }_endOperation(this);if (webkit && options.lineWrapping && getComputedStyle(display.lineDiv).textRendering == "optimizelegibility") {
      display.lineDiv.style.textRendering = "auto";
    }
  }CodeMirror.defaults = defaults;CodeMirror.optionHandlers = optionHandlers;function registerEventHandlers(cm) {
    var d = cm.display;on(d.scroller, "mousedown", operation(cm, onMouseDown));if (ie && ie_version < 11) {
      on(d.scroller, "dblclick", operation(cm, function (e) {
        if (signalDOMEvent(cm, e)) {
          return;
        }var pos = posFromMouse(cm, e);if (!pos || clickInGutter(cm, e) || eventInWidget(cm.display, e)) {
          return;
        }e_preventDefault(e);var word = cm.findWordAt(pos);extendSelection(cm.doc, word.anchor, word.head);
      }));
    } else {
      on(d.scroller, "dblclick", function (e) {
        return signalDOMEvent(cm, e) || e_preventDefault(e);
      });
    }on(d.scroller, "contextmenu", function (e) {
      return onContextMenu(cm, e);
    });var touchFinished,
        prevTouch = { end: 0 };function finishTouch() {
      if (d.activeTouch) {
        touchFinished = setTimeout(function () {
          return d.activeTouch = null;
        }, 1e3);prevTouch = d.activeTouch;prevTouch.end = +new Date();
      }
    }function isMouseLikeTouchEvent(e) {
      if (e.touches.length != 1) {
        return false;
      }var touch = e.touches[0];return touch.radiusX <= 1 && touch.radiusY <= 1;
    }function farAway(touch, other) {
      if (other.left == null) {
        return true;
      }var dx = other.left - touch.left,
          dy = other.top - touch.top;return dx * dx + dy * dy > 20 * 20;
    }on(d.scroller, "touchstart", function (e) {
      if (!signalDOMEvent(cm, e) && !isMouseLikeTouchEvent(e) && !clickInGutter(cm, e)) {
        d.input.ensurePolled();clearTimeout(touchFinished);var now = +new Date();d.activeTouch = { start: now, moved: false, prev: now - prevTouch.end <= 300 ? prevTouch : null };if (e.touches.length == 1) {
          d.activeTouch.left = e.touches[0].pageX;d.activeTouch.top = e.touches[0].pageY;
        }
      }
    });on(d.scroller, "touchmove", function () {
      if (d.activeTouch) {
        d.activeTouch.moved = true;
      }
    });on(d.scroller, "touchend", function (e) {
      var touch = d.activeTouch;if (touch && !eventInWidget(d, e) && touch.left != null && !touch.moved && new Date() - touch.start < 300) {
        var pos = cm.coordsChar(d.activeTouch, "page"),
            range;if (!touch.prev || farAway(touch, touch.prev)) {
          range = new Range(pos, pos);
        } else if (!touch.prev.prev || farAway(touch, touch.prev.prev)) {
          range = cm.findWordAt(pos);
        } else {
          range = new Range(Pos(pos.line, 0), _clipPos(cm.doc, Pos(pos.line + 1, 0)));
        }cm.setSelection(range.anchor, range.head);cm.focus();e_preventDefault(e);
      }finishTouch();
    });on(d.scroller, "touchcancel", finishTouch);on(d.scroller, "scroll", function () {
      if (d.scroller.clientHeight) {
        updateScrollTop(cm, d.scroller.scrollTop);setScrollLeft(cm, d.scroller.scrollLeft, true);signal(cm, "scroll", cm);
      }
    });on(d.scroller, "mousewheel", function (e) {
      return onScrollWheel(cm, e);
    });on(d.scroller, "DOMMouseScroll", function (e) {
      return onScrollWheel(cm, e);
    });on(d.wrapper, "scroll", function () {
      return d.wrapper.scrollTop = d.wrapper.scrollLeft = 0;
    });d.dragFunctions = { enter: function enter(e) {
        if (!signalDOMEvent(cm, e)) {
          e_stop(e);
        }
      }, over: function over(e) {
        if (!signalDOMEvent(cm, e)) {
          onDragOver(cm, e);e_stop(e);
        }
      }, start: function start(e) {
        return onDragStart(cm, e);
      }, drop: operation(cm, onDrop), leave: function leave(e) {
        if (!signalDOMEvent(cm, e)) {
          clearDragCursor(cm);
        }
      } };var inp = d.input.getField();on(inp, "keyup", function (e) {
      return onKeyUp.call(cm, e);
    });on(inp, "keydown", operation(cm, onKeyDown));on(inp, "keypress", operation(cm, onKeyPress));on(inp, "focus", function (e) {
      return onFocus(cm, e);
    });on(inp, "blur", function (e) {
      return onBlur(cm, e);
    });
  }var initHooks = [];CodeMirror.defineInitHook = function (f) {
    return initHooks.push(f);
  };function indentLine(cm, n, how, aggressive) {
    var doc = cm.doc,
        state;if (how == null) {
      how = "add";
    }if (how == "smart") {
      if (!doc.mode.indent) {
        how = "prev";
      } else {
        state = getContextBefore(cm, n).state;
      }
    }var tabSize = cm.options.tabSize;var line = getLine(doc, n),
        curSpace = countColumn(line.text, null, tabSize);if (line.stateAfter) {
      line.stateAfter = null;
    }var curSpaceString = line.text.match(/^\s*/)[0],
        indentation;if (!aggressive && !/\S/.test(line.text)) {
      indentation = 0;how = "not";
    } else if (how == "smart") {
      indentation = doc.mode.indent(state, line.text.slice(curSpaceString.length), line.text);if (indentation == Pass || indentation > 150) {
        if (!aggressive) {
          return;
        }how = "prev";
      }
    }if (how == "prev") {
      if (n > doc.first) {
        indentation = countColumn(getLine(doc, n - 1).text, null, tabSize);
      } else {
        indentation = 0;
      }
    } else if (how == "add") {
      indentation = curSpace + cm.options.indentUnit;
    } else if (how == "subtract") {
      indentation = curSpace - cm.options.indentUnit;
    } else if (typeof how == "number") {
      indentation = curSpace + how;
    }indentation = Math.max(0, indentation);var indentString = "",
        pos = 0;if (cm.options.indentWithTabs) {
      for (var i = Math.floor(indentation / tabSize); i; --i) {
        pos += tabSize;indentString += "\t";
      }
    }if (pos < indentation) {
      indentString += spaceStr(indentation - pos);
    }if (indentString != curSpaceString) {
      _replaceRange(doc, indentString, Pos(n, 0), Pos(n, curSpaceString.length), "+input");line.stateAfter = null;return true;
    } else {
      for (var i$1 = 0; i$1 < doc.sel.ranges.length; i$1++) {
        var range = doc.sel.ranges[i$1];if (range.head.line == n && range.head.ch < curSpaceString.length) {
          var pos$1 = Pos(n, curSpaceString.length);replaceOneSelection(doc, i$1, new Range(pos$1, pos$1));break;
        }
      }
    }
  }var lastCopied = null;function setLastCopied(newLastCopied) {
    lastCopied = newLastCopied;
  }function applyTextInput(cm, inserted, deleted, sel, origin) {
    var doc = cm.doc;cm.display.shift = false;if (!sel) {
      sel = doc.sel;
    }var recent = +new Date() - 200;var paste = origin == "paste" || cm.state.pasteIncoming > recent;var textLines = splitLinesAuto(inserted),
        multiPaste = null;if (paste && sel.ranges.length > 1) {
      if (lastCopied && lastCopied.text.join("\n") == inserted) {
        if (sel.ranges.length % lastCopied.text.length == 0) {
          multiPaste = [];for (var i = 0; i < lastCopied.text.length; i++) {
            multiPaste.push(doc.splitLines(lastCopied.text[i]));
          }
        }
      } else if (textLines.length == sel.ranges.length && cm.options.pasteLinesPerSelection) {
        multiPaste = map(textLines, function (l) {
          return [l];
        });
      }
    }var updateInput = cm.curOp.updateInput;for (var i$1 = sel.ranges.length - 1; i$1 >= 0; i$1--) {
      var range$$1 = sel.ranges[i$1];var from = range$$1.from(),
          to = range$$1.to();if (range$$1.empty()) {
        if (deleted && deleted > 0) {
          from = Pos(from.line, from.ch - deleted);
        } else if (cm.state.overwrite && !paste) {
          to = Pos(to.line, Math.min(getLine(doc, to.line).text.length, to.ch + lst(textLines).length));
        } else if (paste && lastCopied && lastCopied.lineWise && lastCopied.text.join("\n") == inserted) {
          from = to = Pos(from.line, 0);
        }
      }var changeEvent = { from: from, to: to, text: multiPaste ? multiPaste[i$1 % multiPaste.length] : textLines, origin: origin || (paste ? "paste" : cm.state.cutIncoming > recent ? "cut" : "+input") };makeChange(cm.doc, changeEvent);signalLater(cm, "inputRead", cm, changeEvent);
    }if (inserted && !paste) {
      triggerElectric(cm, inserted);
    }ensureCursorVisible(cm);if (cm.curOp.updateInput < 2) {
      cm.curOp.updateInput = updateInput;
    }cm.curOp.typing = true;cm.state.pasteIncoming = cm.state.cutIncoming = -1;
  }function handlePaste(e, cm) {
    var pasted = e.clipboardData && e.clipboardData.getData("Text");if (pasted) {
      e.preventDefault();if (!cm.isReadOnly() && !cm.options.disableInput) {
        runInOp(cm, function () {
          return applyTextInput(cm, pasted, 0, null, "paste");
        });
      }return true;
    }
  }function triggerElectric(cm, inserted) {
    if (!cm.options.electricChars || !cm.options.smartIndent) {
      return;
    }var sel = cm.doc.sel;for (var i = sel.ranges.length - 1; i >= 0; i--) {
      var range$$1 = sel.ranges[i];if (range$$1.head.ch > 100 || i && sel.ranges[i - 1].head.line == range$$1.head.line) {
        continue;
      }var mode = cm.getModeAt(range$$1.head);var indented = false;if (mode.electricChars) {
        for (var j = 0; j < mode.electricChars.length; j++) {
          if (inserted.indexOf(mode.electricChars.charAt(j)) > -1) {
            indented = indentLine(cm, range$$1.head.line, "smart");break;
          }
        }
      } else if (mode.electricInput) {
        if (mode.electricInput.test(getLine(cm.doc, range$$1.head.line).text.slice(0, range$$1.head.ch))) {
          indented = indentLine(cm, range$$1.head.line, "smart");
        }
      }if (indented) {
        signalLater(cm, "electricInput", cm, range$$1.head.line);
      }
    }
  }function copyableRanges(cm) {
    var text = [],
        ranges = [];for (var i = 0; i < cm.doc.sel.ranges.length; i++) {
      var line = cm.doc.sel.ranges[i].head.line;var lineRange = { anchor: Pos(line, 0), head: Pos(line + 1, 0) };ranges.push(lineRange);text.push(cm.getRange(lineRange.anchor, lineRange.head));
    }return { text: text, ranges: ranges };
  }function disableBrowserMagic(field, spellcheck, autocorrect, autocapitalize) {
    field.setAttribute("autocorrect", autocorrect ? "" : "off");field.setAttribute("autocapitalize", autocapitalize ? "" : "off");field.setAttribute("spellcheck", !!spellcheck);
  }function hiddenTextarea() {
    var te = elt("textarea", null, null, "position: absolute; bottom: -1em; padding: 0; width: 1px; height: 1em; outline: none");var div = elt("div", [te], null, "overflow: hidden; position: relative; width: 3px; height: 0px;");if (webkit) {
      te.style.width = "1000px";
    } else {
      te.setAttribute("wrap", "off");
    }if (ios) {
      te.style.border = "1px solid black";
    }disableBrowserMagic(te);return div;
  }function addEditorMethods(CodeMirror) {
    var optionHandlers = CodeMirror.optionHandlers;var helpers = CodeMirror.helpers = {};CodeMirror.prototype = { constructor: CodeMirror, focus: function focus() {
        window.focus();this.display.input.focus();
      }, setOption: function setOption(option, value) {
        var options = this.options,
            old = options[option];if (options[option] == value && option != "mode") {
          return;
        }options[option] = value;if (optionHandlers.hasOwnProperty(option)) {
          operation(this, optionHandlers[option])(this, value, old);
        }signal(this, "optionChange", this, option);
      }, getOption: function getOption(option) {
        return this.options[option];
      }, getDoc: function getDoc() {
        return this.doc;
      }, addKeyMap: function addKeyMap(map$$1, bottom) {
        this.state.keyMaps[bottom ? "push" : "unshift"](getKeyMap(map$$1));
      }, removeKeyMap: function removeKeyMap(map$$1) {
        var maps = this.state.keyMaps;for (var i = 0; i < maps.length; ++i) {
          if (maps[i] == map$$1 || maps[i].name == map$$1) {
            maps.splice(i, 1);return true;
          }
        }
      }, addOverlay: methodOp(function (spec, options) {
        var mode = spec.token ? spec : CodeMirror.getMode(this.options, spec);if (mode.startState) {
          throw new Error("Overlays may not be stateful.");
        }insertSorted(this.state.overlays, { mode: mode, modeSpec: spec, opaque: options && options.opaque, priority: options && options.priority || 0 }, function (overlay) {
          return overlay.priority;
        });this.state.modeGen++;regChange(this);
      }), removeOverlay: methodOp(function (spec) {
        var overlays = this.state.overlays;for (var i = 0; i < overlays.length; ++i) {
          var cur = overlays[i].modeSpec;if (cur == spec || typeof spec == "string" && cur.name == spec) {
            overlays.splice(i, 1);this.state.modeGen++;regChange(this);return;
          }
        }
      }), indentLine: methodOp(function (n, dir, aggressive) {
        if (typeof dir != "string" && typeof dir != "number") {
          if (dir == null) {
            dir = this.options.smartIndent ? "smart" : "prev";
          } else {
            dir = dir ? "add" : "subtract";
          }
        }if (isLine(this.doc, n)) {
          indentLine(this, n, dir, aggressive);
        }
      }), indentSelection: methodOp(function (how) {
        var ranges = this.doc.sel.ranges,
            end = -1;for (var i = 0; i < ranges.length; i++) {
          var range$$1 = ranges[i];if (!range$$1.empty()) {
            var from = range$$1.from(),
                to = range$$1.to();var start = Math.max(end, from.line);end = Math.min(this.lastLine(), to.line - (to.ch ? 0 : 1)) + 1;for (var j = start; j < end; ++j) {
              indentLine(this, j, how);
            }var newRanges = this.doc.sel.ranges;if (from.ch == 0 && ranges.length == newRanges.length && newRanges[i].from().ch > 0) {
              replaceOneSelection(this.doc, i, new Range(from, newRanges[i].to()), sel_dontScroll);
            }
          } else if (range$$1.head.line > end) {
            indentLine(this, range$$1.head.line, how, true);end = range$$1.head.line;if (i == this.doc.sel.primIndex) {
              ensureCursorVisible(this);
            }
          }
        }
      }), getTokenAt: function getTokenAt(pos, precise) {
        return takeToken(this, pos, precise);
      }, getLineTokens: function getLineTokens(line, precise) {
        return takeToken(this, Pos(line), precise, true);
      }, getTokenTypeAt: function getTokenTypeAt(pos) {
        pos = _clipPos(this.doc, pos);var styles = getLineStyles(this, getLine(this.doc, pos.line));var before = 0,
            after = (styles.length - 1) / 2,
            ch = pos.ch;var type;if (ch == 0) {
          type = styles[2];
        } else {
          for (;;) {
            var mid = before + after >> 1;if ((mid ? styles[mid * 2 - 1] : 0) >= ch) {
              after = mid;
            } else if (styles[mid * 2 + 1] < ch) {
              before = mid + 1;
            } else {
              type = styles[mid * 2 + 2];break;
            }
          }
        }var cut = type ? type.indexOf("overlay ") : -1;return cut < 0 ? type : cut == 0 ? null : type.slice(0, cut - 1);
      }, getModeAt: function getModeAt(pos) {
        var mode = this.doc.mode;if (!mode.innerMode) {
          return mode;
        }return CodeMirror.innerMode(mode, this.getTokenAt(pos).state).mode;
      }, getHelper: function getHelper(pos, type) {
        return this.getHelpers(pos, type)[0];
      }, getHelpers: function getHelpers(pos, type) {
        var found = [];if (!helpers.hasOwnProperty(type)) {
          return found;
        }var help = helpers[type],
            mode = this.getModeAt(pos);if (typeof mode[type] == "string") {
          if (help[mode[type]]) {
            found.push(help[mode[type]]);
          }
        } else if (mode[type]) {
          for (var i = 0; i < mode[type].length; i++) {
            var val = help[mode[type][i]];if (val) {
              found.push(val);
            }
          }
        } else if (mode.helperType && help[mode.helperType]) {
          found.push(help[mode.helperType]);
        } else if (help[mode.name]) {
          found.push(help[mode.name]);
        }for (var i$1 = 0; i$1 < help._global.length; i$1++) {
          var cur = help._global[i$1];if (cur.pred(mode, this) && indexOf(found, cur.val) == -1) {
            found.push(cur.val);
          }
        }return found;
      }, getStateAfter: function getStateAfter(line, precise) {
        var doc = this.doc;line = clipLine(doc, line == null ? doc.first + doc.size - 1 : line);return getContextBefore(this, line + 1, precise).state;
      }, cursorCoords: function cursorCoords(start, mode) {
        var pos,
            range$$1 = this.doc.sel.primary();if (start == null) {
          pos = range$$1.head;
        } else if ((typeof start === "undefined" ? "undefined" : _typeof(start)) == "object") {
          pos = _clipPos(this.doc, start);
        } else {
          pos = start ? range$$1.from() : range$$1.to();
        }return _cursorCoords(this, pos, mode || "page");
      }, charCoords: function charCoords(pos, mode) {
        return _charCoords(this, _clipPos(this.doc, pos), mode || "page");
      }, coordsChar: function coordsChar(coords, mode) {
        coords = fromCoordSystem(this, coords, mode || "page");return _coordsChar(this, coords.left, coords.top);
      }, lineAtHeight: function lineAtHeight(height, mode) {
        height = fromCoordSystem(this, { top: height, left: 0 }, mode || "page").top;return _lineAtHeight(this.doc, height + this.display.viewOffset);
      }, heightAtLine: function heightAtLine(line, mode, includeWidgets) {
        var end = false,
            lineObj;if (typeof line == "number") {
          var last = this.doc.first + this.doc.size - 1;if (line < this.doc.first) {
            line = this.doc.first;
          } else if (line > last) {
            line = last;end = true;
          }lineObj = getLine(this.doc, line);
        } else {
          lineObj = line;
        }return intoCoordSystem(this, lineObj, { top: 0, left: 0 }, mode || "page", includeWidgets || end).top + (end ? this.doc.height - _heightAtLine(lineObj) : 0);
      }, defaultTextHeight: function defaultTextHeight() {
        return textHeight(this.display);
      }, defaultCharWidth: function defaultCharWidth() {
        return charWidth(this.display);
      }, getViewport: function getViewport() {
        return { from: this.display.viewFrom, to: this.display.viewTo };
      }, addWidget: function addWidget(pos, node, scroll, vert, horiz) {
        var display = this.display;pos = _cursorCoords(this, _clipPos(this.doc, pos));var top = pos.bottom,
            left = pos.left;node.style.position = "absolute";node.setAttribute("cm-ignore-events", "true");this.display.input.setUneditable(node);display.sizer.appendChild(node);if (vert == "over") {
          top = pos.top;
        } else if (vert == "above" || vert == "near") {
          var vspace = Math.max(display.wrapper.clientHeight, this.doc.height),
              hspace = Math.max(display.sizer.clientWidth, display.lineSpace.clientWidth);if ((vert == "above" || pos.bottom + node.offsetHeight > vspace) && pos.top > node.offsetHeight) {
            top = pos.top - node.offsetHeight;
          } else if (pos.bottom + node.offsetHeight <= vspace) {
            top = pos.bottom;
          }if (left + node.offsetWidth > hspace) {
            left = hspace - node.offsetWidth;
          }
        }node.style.top = top + "px";node.style.left = node.style.right = "";if (horiz == "right") {
          left = display.sizer.clientWidth - node.offsetWidth;node.style.right = "0px";
        } else {
          if (horiz == "left") {
            left = 0;
          } else if (horiz == "middle") {
            left = (display.sizer.clientWidth - node.offsetWidth) / 2;
          }node.style.left = left + "px";
        }if (scroll) {
          scrollIntoView(this, { left: left, top: top, right: left + node.offsetWidth, bottom: top + node.offsetHeight });
        }
      }, triggerOnKeyDown: methodOp(onKeyDown), triggerOnKeyPress: methodOp(onKeyPress), triggerOnKeyUp: onKeyUp, triggerOnMouseDown: methodOp(onMouseDown), execCommand: function execCommand(cmd) {
        if (commands.hasOwnProperty(cmd)) {
          return commands[cmd].call(null, this);
        }
      }, triggerElectric: methodOp(function (text) {
        triggerElectric(this, text);
      }), findPosH: function findPosH(from, amount, unit, visually) {
        var dir = 1;if (amount < 0) {
          dir = -1;amount = -amount;
        }var cur = _clipPos(this.doc, from);for (var i = 0; i < amount; ++i) {
          cur = _findPosH(this.doc, cur, dir, unit, visually);if (cur.hitSide) {
            break;
          }
        }return cur;
      }, moveH: methodOp(function (dir, unit) {
        var this$1 = this;this.extendSelectionsBy(function (range$$1) {
          if (this$1.display.shift || this$1.doc.extend || range$$1.empty()) {
            return _findPosH(this$1.doc, range$$1.head, dir, unit, this$1.options.rtlMoveVisually);
          } else {
            return dir < 0 ? range$$1.from() : range$$1.to();
          }
        }, sel_move);
      }), deleteH: methodOp(function (dir, unit) {
        var sel = this.doc.sel,
            doc = this.doc;if (sel.somethingSelected()) {
          doc.replaceSelection("", null, "+delete");
        } else {
          deleteNearSelection(this, function (range$$1) {
            var other = _findPosH(doc, range$$1.head, dir, unit, false);return dir < 0 ? { from: other, to: range$$1.head } : { from: range$$1.head, to: other };
          });
        }
      }), findPosV: function findPosV(from, amount, unit, goalColumn) {
        var dir = 1,
            x = goalColumn;if (amount < 0) {
          dir = -1;amount = -amount;
        }var cur = _clipPos(this.doc, from);for (var i = 0; i < amount; ++i) {
          var coords = _cursorCoords(this, cur, "div");if (x == null) {
            x = coords.left;
          } else {
            coords.left = x;
          }cur = _findPosV(this, coords, dir, unit);if (cur.hitSide) {
            break;
          }
        }return cur;
      }, moveV: methodOp(function (dir, unit) {
        var this$1 = this;var doc = this.doc,
            goals = [];var collapse = !this.display.shift && !doc.extend && doc.sel.somethingSelected();doc.extendSelectionsBy(function (range$$1) {
          if (collapse) {
            return dir < 0 ? range$$1.from() : range$$1.to();
          }var headPos = _cursorCoords(this$1, range$$1.head, "div");if (range$$1.goalColumn != null) {
            headPos.left = range$$1.goalColumn;
          }goals.push(headPos.left);var pos = _findPosV(this$1, headPos, dir, unit);if (unit == "page" && range$$1 == doc.sel.primary()) {
            addToScrollTop(this$1, _charCoords(this$1, pos, "div").top - headPos.top);
          }return pos;
        }, sel_move);if (goals.length) {
          for (var i = 0; i < doc.sel.ranges.length; i++) {
            doc.sel.ranges[i].goalColumn = goals[i];
          }
        }
      }), findWordAt: function findWordAt(pos) {
        var doc = this.doc,
            line = getLine(doc, pos.line).text;var start = pos.ch,
            end = pos.ch;if (line) {
          var helper = this.getHelper(pos, "wordChars");if ((pos.sticky == "before" || end == line.length) && start) {
            --start;
          } else {
            ++end;
          }var startChar = line.charAt(start);var check = isWordChar(startChar, helper) ? function (ch) {
            return isWordChar(ch, helper);
          } : /\s/.test(startChar) ? function (ch) {
            return (/\s/.test(ch)
            );
          } : function (ch) {
            return !/\s/.test(ch) && !isWordChar(ch);
          };while (start > 0 && check(line.charAt(start - 1))) {
            --start;
          }while (end < line.length && check(line.charAt(end))) {
            ++end;
          }
        }return new Range(Pos(pos.line, start), Pos(pos.line, end));
      }, toggleOverwrite: function toggleOverwrite(value) {
        if (value != null && value == this.state.overwrite) {
          return;
        }if (this.state.overwrite = !this.state.overwrite) {
          addClass(this.display.cursorDiv, "CodeMirror-overwrite");
        } else {
          rmClass(this.display.cursorDiv, "CodeMirror-overwrite");
        }signal(this, "overwriteToggle", this, this.state.overwrite);
      }, hasFocus: function hasFocus() {
        return this.display.input.getField() == activeElt();
      }, isReadOnly: function isReadOnly() {
        return !!(this.options.readOnly || this.doc.cantEdit);
      }, scrollTo: methodOp(function (x, y) {
        scrollToCoords(this, x, y);
      }), getScrollInfo: function getScrollInfo() {
        var scroller = this.display.scroller;return { left: scroller.scrollLeft, top: scroller.scrollTop, height: scroller.scrollHeight - scrollGap(this) - this.display.barHeight, width: scroller.scrollWidth - scrollGap(this) - this.display.barWidth, clientHeight: displayHeight(this), clientWidth: displayWidth(this) };
      }, scrollIntoView: methodOp(function (range$$1, margin) {
        if (range$$1 == null) {
          range$$1 = { from: this.doc.sel.primary().head, to: null };if (margin == null) {
            margin = this.options.cursorScrollMargin;
          }
        } else if (typeof range$$1 == "number") {
          range$$1 = { from: Pos(range$$1, 0), to: null };
        } else if (range$$1.from == null) {
          range$$1 = { from: range$$1, to: null };
        }if (!range$$1.to) {
          range$$1.to = range$$1.from;
        }range$$1.margin = margin || 0;if (range$$1.from.line != null) {
          scrollToRange(this, range$$1);
        } else {
          scrollToCoordsRange(this, range$$1.from, range$$1.to, range$$1.margin);
        }
      }), setSize: methodOp(function (width, height) {
        var this$1 = this;var interpret = function interpret(val) {
          return typeof val == "number" || /^\d+$/.test(String(val)) ? val + "px" : val;
        };if (width != null) {
          this.display.wrapper.style.width = interpret(width);
        }if (height != null) {
          this.display.wrapper.style.height = interpret(height);
        }if (this.options.lineWrapping) {
          clearLineMeasurementCache(this);
        }var lineNo$$1 = this.display.viewFrom;this.doc.iter(lineNo$$1, this.display.viewTo, function (line) {
          if (line.widgets) {
            for (var i = 0; i < line.widgets.length; i++) {
              if (line.widgets[i].noHScroll) {
                regLineChange(this$1, lineNo$$1, "widget");break;
              }
            }
          }++lineNo$$1;
        });this.curOp.forceUpdate = true;signal(this, "refresh", this);
      }), operation: function operation(f) {
        return runInOp(this, f);
      }, startOperation: function startOperation() {
        return _startOperation(this);
      }, endOperation: function endOperation() {
        return _endOperation(this);
      }, refresh: methodOp(function () {
        var oldHeight = this.display.cachedTextHeight;regChange(this);this.curOp.forceUpdate = true;clearCaches(this);scrollToCoords(this, this.doc.scrollLeft, this.doc.scrollTop);updateGutterSpace(this.display);if (oldHeight == null || Math.abs(oldHeight - textHeight(this.display)) > .5) {
          estimateLineHeights(this);
        }signal(this, "refresh", this);
      }), swapDoc: methodOp(function (doc) {
        var old = this.doc;old.cm = null;if (this.state.selectingText) {
          this.state.selectingText();
        }attachDoc(this, doc);clearCaches(this);this.display.input.reset();scrollToCoords(this, doc.scrollLeft, doc.scrollTop);this.curOp.forceScroll = true;signalLater(this, "swapDoc", this, old);return old;
      }), phrase: function phrase(phraseText) {
        var phrases = this.options.phrases;return phrases && Object.prototype.hasOwnProperty.call(phrases, phraseText) ? phrases[phraseText] : phraseText;
      }, getInputField: function getInputField() {
        return this.display.input.getField();
      }, getWrapperElement: function getWrapperElement() {
        return this.display.wrapper;
      }, getScrollerElement: function getScrollerElement() {
        return this.display.scroller;
      }, getGutterElement: function getGutterElement() {
        return this.display.gutters;
      } };eventMixin(CodeMirror);CodeMirror.registerHelper = function (type, name, value) {
      if (!helpers.hasOwnProperty(type)) {
        helpers[type] = CodeMirror[type] = { _global: [] };
      }helpers[type][name] = value;
    };CodeMirror.registerGlobalHelper = function (type, name, predicate, value) {
      CodeMirror.registerHelper(type, name, value);helpers[type]._global.push({ pred: predicate, val: value });
    };
  }function _findPosH(doc, pos, dir, unit, visually) {
    var oldPos = pos;var origDir = dir;var lineObj = getLine(doc, pos.line);function findNextLine() {
      var l = pos.line + dir;if (l < doc.first || l >= doc.first + doc.size) {
        return false;
      }pos = new Pos(l, pos.ch, pos.sticky);return lineObj = getLine(doc, l);
    }function moveOnce(boundToLine) {
      var next;if (visually) {
        next = moveVisually(doc.cm, lineObj, pos, dir);
      } else {
        next = moveLogically(lineObj, pos, dir);
      }if (next == null) {
        if (!boundToLine && findNextLine()) {
          pos = endOfLine(visually, doc.cm, lineObj, pos.line, dir);
        } else {
          return false;
        }
      } else {
        pos = next;
      }return true;
    }if (unit == "char") {
      moveOnce();
    } else if (unit == "column") {
      moveOnce(true);
    } else if (unit == "word" || unit == "group") {
      var sawType = null,
          group = unit == "group";var helper = doc.cm && doc.cm.getHelper(pos, "wordChars");for (var first = true;; first = false) {
        if (dir < 0 && !moveOnce(!first)) {
          break;
        }var cur = lineObj.text.charAt(pos.ch) || "\n";var type = isWordChar(cur, helper) ? "w" : group && cur == "\n" ? "n" : !group || /\s/.test(cur) ? null : "p";if (group && !first && !type) {
          type = "s";
        }if (sawType && sawType != type) {
          if (dir < 0) {
            dir = 1;moveOnce();pos.sticky = "after";
          }break;
        }if (type) {
          sawType = type;
        }if (dir > 0 && !moveOnce(!first)) {
          break;
        }
      }
    }var result = skipAtomic(doc, pos, oldPos, origDir, true);if (equalCursorPos(oldPos, result)) {
      result.hitSide = true;
    }return result;
  }function _findPosV(cm, pos, dir, unit) {
    var doc = cm.doc,
        x = pos.left,
        y;if (unit == "page") {
      var pageSize = Math.min(cm.display.wrapper.clientHeight, window.innerHeight || document.documentElement.clientHeight);var moveAmount = Math.max(pageSize - .5 * textHeight(cm.display), 3);y = (dir > 0 ? pos.bottom : pos.top) + dir * moveAmount;
    } else if (unit == "line") {
      y = dir > 0 ? pos.bottom + 3 : pos.top - 3;
    }var target;for (;;) {
      target = _coordsChar(cm, x, y);if (!target.outside) {
        break;
      }if (dir < 0 ? y <= 0 : y >= doc.height) {
        target.hitSide = true;break;
      }y += dir * 5;
    }return target;
  }var ContentEditableInput = function ContentEditableInput(cm) {
    this.cm = cm;this.lastAnchorNode = this.lastAnchorOffset = this.lastFocusNode = this.lastFocusOffset = null;this.polling = new Delayed();this.composing = null;this.gracePeriod = false;this.readDOMTimeout = null;
  };ContentEditableInput.prototype.init = function (display) {
    var this$1 = this;var input = this,
        cm = input.cm;var div = input.div = display.lineDiv;disableBrowserMagic(div, cm.options.spellcheck, cm.options.autocorrect, cm.options.autocapitalize);on(div, "paste", function (e) {
      if (signalDOMEvent(cm, e) || handlePaste(e, cm)) {
        return;
      }if (ie_version <= 11) {
        setTimeout(operation(cm, function () {
          return this$1.updateFromDOM();
        }), 20);
      }
    });on(div, "compositionstart", function (e) {
      this$1.composing = { data: e.data, done: false };
    });on(div, "compositionupdate", function (e) {
      if (!this$1.composing) {
        this$1.composing = { data: e.data, done: false };
      }
    });on(div, "compositionend", function (e) {
      if (this$1.composing) {
        if (e.data != this$1.composing.data) {
          this$1.readFromDOMSoon();
        }this$1.composing.done = true;
      }
    });on(div, "touchstart", function () {
      return input.forceCompositionEnd();
    });on(div, "input", function () {
      if (!this$1.composing) {
        this$1.readFromDOMSoon();
      }
    });function onCopyCut(e) {
      if (signalDOMEvent(cm, e)) {
        return;
      }if (cm.somethingSelected()) {
        setLastCopied({ lineWise: false, text: cm.getSelections() });if (e.type == "cut") {
          cm.replaceSelection("", null, "cut");
        }
      } else if (!cm.options.lineWiseCopyCut) {
        return;
      } else {
        var ranges = copyableRanges(cm);setLastCopied({ lineWise: true, text: ranges.text });if (e.type == "cut") {
          cm.operation(function () {
            cm.setSelections(ranges.ranges, 0, sel_dontScroll);cm.replaceSelection("", null, "cut");
          });
        }
      }if (e.clipboardData) {
        e.clipboardData.clearData();var content = lastCopied.text.join("\n");e.clipboardData.setData("Text", content);if (e.clipboardData.getData("Text") == content) {
          e.preventDefault();return;
        }
      }var kludge = hiddenTextarea(),
          te = kludge.firstChild;cm.display.lineSpace.insertBefore(kludge, cm.display.lineSpace.firstChild);te.value = lastCopied.text.join("\n");var hadFocus = document.activeElement;selectInput(te);setTimeout(function () {
        cm.display.lineSpace.removeChild(kludge);hadFocus.focus();if (hadFocus == div) {
          input.showPrimarySelection();
        }
      }, 50);
    }on(div, "copy", onCopyCut);on(div, "cut", onCopyCut);
  };ContentEditableInput.prototype.prepareSelection = function () {
    var result = prepareSelection(this.cm, false);result.focus = this.cm.state.focused;return result;
  };ContentEditableInput.prototype.showSelection = function (info, takeFocus) {
    if (!info || !this.cm.display.view.length) {
      return;
    }if (info.focus || takeFocus) {
      this.showPrimarySelection();
    }this.showMultipleSelections(info);
  };ContentEditableInput.prototype.getSelection = function () {
    return this.cm.display.wrapper.ownerDocument.getSelection();
  };ContentEditableInput.prototype.showPrimarySelection = function () {
    var sel = this.getSelection(),
        cm = this.cm,
        prim = cm.doc.sel.primary();var from = prim.from(),
        to = prim.to();if (cm.display.viewTo == cm.display.viewFrom || from.line >= cm.display.viewTo || to.line < cm.display.viewFrom) {
      sel.removeAllRanges();return;
    }var curAnchor = domToPos(cm, sel.anchorNode, sel.anchorOffset);var curFocus = domToPos(cm, sel.focusNode, sel.focusOffset);if (curAnchor && !curAnchor.bad && curFocus && !curFocus.bad && cmp(minPos(curAnchor, curFocus), from) == 0 && cmp(maxPos(curAnchor, curFocus), to) == 0) {
      return;
    }var view = cm.display.view;var start = from.line >= cm.display.viewFrom && posToDOM(cm, from) || { node: view[0].measure.map[2], offset: 0 };var end = to.line < cm.display.viewTo && posToDOM(cm, to);if (!end) {
      var measure = view[view.length - 1].measure;var map$$1 = measure.maps ? measure.maps[measure.maps.length - 1] : measure.map;end = { node: map$$1[map$$1.length - 1], offset: map$$1[map$$1.length - 2] - map$$1[map$$1.length - 3] };
    }if (!start || !end) {
      sel.removeAllRanges();return;
    }var old = sel.rangeCount && sel.getRangeAt(0),
        rng;try {
      rng = range(start.node, start.offset, end.offset, end.node);
    } catch (e) {}if (rng) {
      if (!gecko && cm.state.focused) {
        sel.collapse(start.node, start.offset);if (!rng.collapsed) {
          sel.removeAllRanges();sel.addRange(rng);
        }
      } else {
        sel.removeAllRanges();sel.addRange(rng);
      }if (old && sel.anchorNode == null) {
        sel.addRange(old);
      } else if (gecko) {
        this.startGracePeriod();
      }
    }this.rememberSelection();
  };ContentEditableInput.prototype.startGracePeriod = function () {
    var this$1 = this;clearTimeout(this.gracePeriod);this.gracePeriod = setTimeout(function () {
      this$1.gracePeriod = false;if (this$1.selectionChanged()) {
        this$1.cm.operation(function () {
          return this$1.cm.curOp.selectionChanged = true;
        });
      }
    }, 20);
  };ContentEditableInput.prototype.showMultipleSelections = function (info) {
    removeChildrenAndAdd(this.cm.display.cursorDiv, info.cursors);removeChildrenAndAdd(this.cm.display.selectionDiv, info.selection);
  };ContentEditableInput.prototype.rememberSelection = function () {
    var sel = this.getSelection();this.lastAnchorNode = sel.anchorNode;this.lastAnchorOffset = sel.anchorOffset;this.lastFocusNode = sel.focusNode;this.lastFocusOffset = sel.focusOffset;
  };ContentEditableInput.prototype.selectionInEditor = function () {
    var sel = this.getSelection();if (!sel.rangeCount) {
      return false;
    }var node = sel.getRangeAt(0).commonAncestorContainer;return contains(this.div, node);
  };ContentEditableInput.prototype.focus = function () {
    if (this.cm.options.readOnly != "nocursor") {
      if (!this.selectionInEditor()) {
        this.showSelection(this.prepareSelection(), true);
      }this.div.focus();
    }
  };ContentEditableInput.prototype.blur = function () {
    this.div.blur();
  };ContentEditableInput.prototype.getField = function () {
    return this.div;
  };ContentEditableInput.prototype.supportsTouch = function () {
    return true;
  };ContentEditableInput.prototype.receivedFocus = function () {
    var input = this;if (this.selectionInEditor()) {
      this.pollSelection();
    } else {
      runInOp(this.cm, function () {
        return input.cm.curOp.selectionChanged = true;
      });
    }function poll() {
      if (input.cm.state.focused) {
        input.pollSelection();input.polling.set(input.cm.options.pollInterval, poll);
      }
    }this.polling.set(this.cm.options.pollInterval, poll);
  };ContentEditableInput.prototype.selectionChanged = function () {
    var sel = this.getSelection();return sel.anchorNode != this.lastAnchorNode || sel.anchorOffset != this.lastAnchorOffset || sel.focusNode != this.lastFocusNode || sel.focusOffset != this.lastFocusOffset;
  };ContentEditableInput.prototype.pollSelection = function () {
    if (this.readDOMTimeout != null || this.gracePeriod || !this.selectionChanged()) {
      return;
    }var sel = this.getSelection(),
        cm = this.cm;if (android && chrome && this.cm.display.gutterSpecs.length && isInGutter(sel.anchorNode)) {
      this.cm.triggerOnKeyDown({ type: "keydown", keyCode: 8, preventDefault: Math.abs });this.blur();this.focus();return;
    }if (this.composing) {
      return;
    }this.rememberSelection();var anchor = domToPos(cm, sel.anchorNode, sel.anchorOffset);var head = domToPos(cm, sel.focusNode, sel.focusOffset);if (anchor && head) {
      runInOp(cm, function () {
        setSelection(cm.doc, simpleSelection(anchor, head), sel_dontScroll);if (anchor.bad || head.bad) {
          cm.curOp.selectionChanged = true;
        }
      });
    }
  };ContentEditableInput.prototype.pollContent = function () {
    if (this.readDOMTimeout != null) {
      clearTimeout(this.readDOMTimeout);this.readDOMTimeout = null;
    }var cm = this.cm,
        display = cm.display,
        sel = cm.doc.sel.primary();var from = sel.from(),
        to = sel.to();if (from.ch == 0 && from.line > cm.firstLine()) {
      from = Pos(from.line - 1, getLine(cm.doc, from.line - 1).length);
    }if (to.ch == getLine(cm.doc, to.line).text.length && to.line < cm.lastLine()) {
      to = Pos(to.line + 1, 0);
    }if (from.line < display.viewFrom || to.line > display.viewTo - 1) {
      return false;
    }var fromIndex, fromLine, fromNode;if (from.line == display.viewFrom || (fromIndex = findViewIndex(cm, from.line)) == 0) {
      fromLine = lineNo(display.view[0].line);fromNode = display.view[0].node;
    } else {
      fromLine = lineNo(display.view[fromIndex].line);fromNode = display.view[fromIndex - 1].node.nextSibling;
    }var toIndex = findViewIndex(cm, to.line);var toLine, toNode;if (toIndex == display.view.length - 1) {
      toLine = display.viewTo - 1;toNode = display.lineDiv.lastChild;
    } else {
      toLine = lineNo(display.view[toIndex + 1].line) - 1;toNode = display.view[toIndex + 1].node.previousSibling;
    }if (!fromNode) {
      return false;
    }var newText = cm.doc.splitLines(domTextBetween(cm, fromNode, toNode, fromLine, toLine));var oldText = getBetween(cm.doc, Pos(fromLine, 0), Pos(toLine, getLine(cm.doc, toLine).text.length));while (newText.length > 1 && oldText.length > 1) {
      if (lst(newText) == lst(oldText)) {
        newText.pop();oldText.pop();toLine--;
      } else if (newText[0] == oldText[0]) {
        newText.shift();oldText.shift();fromLine++;
      } else {
        break;
      }
    }var cutFront = 0,
        cutEnd = 0;var newTop = newText[0],
        oldTop = oldText[0],
        maxCutFront = Math.min(newTop.length, oldTop.length);while (cutFront < maxCutFront && newTop.charCodeAt(cutFront) == oldTop.charCodeAt(cutFront)) {
      ++cutFront;
    }var newBot = lst(newText),
        oldBot = lst(oldText);var maxCutEnd = Math.min(newBot.length - (newText.length == 1 ? cutFront : 0), oldBot.length - (oldText.length == 1 ? cutFront : 0));while (cutEnd < maxCutEnd && newBot.charCodeAt(newBot.length - cutEnd - 1) == oldBot.charCodeAt(oldBot.length - cutEnd - 1)) {
      ++cutEnd;
    }if (newText.length == 1 && oldText.length == 1 && fromLine == from.line) {
      while (cutFront && cutFront > from.ch && newBot.charCodeAt(newBot.length - cutEnd - 1) == oldBot.charCodeAt(oldBot.length - cutEnd - 1)) {
        cutFront--;cutEnd++;
      }
    }newText[newText.length - 1] = newBot.slice(0, newBot.length - cutEnd).replace(/^\u200b+/, "");newText[0] = newText[0].slice(cutFront).replace(/\u200b+$/, "");var chFrom = Pos(fromLine, cutFront);var chTo = Pos(toLine, oldText.length ? lst(oldText).length - cutEnd : 0);if (newText.length > 1 || newText[0] || cmp(chFrom, chTo)) {
      _replaceRange(cm.doc, newText, chFrom, chTo, "+input");return true;
    }
  };ContentEditableInput.prototype.ensurePolled = function () {
    this.forceCompositionEnd();
  };ContentEditableInput.prototype.reset = function () {
    this.forceCompositionEnd();
  };ContentEditableInput.prototype.forceCompositionEnd = function () {
    if (!this.composing) {
      return;
    }clearTimeout(this.readDOMTimeout);this.composing = null;this.updateFromDOM();this.div.blur();this.div.focus();
  };ContentEditableInput.prototype.readFromDOMSoon = function () {
    var this$1 = this;if (this.readDOMTimeout != null) {
      return;
    }this.readDOMTimeout = setTimeout(function () {
      this$1.readDOMTimeout = null;if (this$1.composing) {
        if (this$1.composing.done) {
          this$1.composing = null;
        } else {
          return;
        }
      }this$1.updateFromDOM();
    }, 80);
  };ContentEditableInput.prototype.updateFromDOM = function () {
    var this$1 = this;if (this.cm.isReadOnly() || !this.pollContent()) {
      runInOp(this.cm, function () {
        return regChange(this$1.cm);
      });
    }
  };ContentEditableInput.prototype.setUneditable = function (node) {
    node.contentEditable = "false";
  };ContentEditableInput.prototype.onKeyPress = function (e) {
    if (e.charCode == 0 || this.composing) {
      return;
    }e.preventDefault();if (!this.cm.isReadOnly()) {
      operation(this.cm, applyTextInput)(this.cm, String.fromCharCode(e.charCode == null ? e.keyCode : e.charCode), 0);
    }
  };ContentEditableInput.prototype.readOnlyChanged = function (val) {
    this.div.contentEditable = String(val != "nocursor");
  };ContentEditableInput.prototype.onContextMenu = function () {};ContentEditableInput.prototype.resetPosition = function () {};ContentEditableInput.prototype.needsContentAttribute = true;function posToDOM(cm, pos) {
    var view = findViewForLine(cm, pos.line);if (!view || view.hidden) {
      return null;
    }var line = getLine(cm.doc, pos.line);var info = mapFromLineView(view, line, pos.line);var order = getOrder(line, cm.doc.direction),
        side = "left";if (order) {
      var partPos = getBidiPartAt(order, pos.ch);side = partPos % 2 ? "right" : "left";
    }var result = nodeAndOffsetInLineMap(info.map, pos.ch, side);result.offset = result.collapse == "right" ? result.end : result.start;return result;
  }function isInGutter(node) {
    for (var scan = node; scan; scan = scan.parentNode) {
      if (/CodeMirror-gutter-wrapper/.test(scan.className)) {
        return true;
      }
    }return false;
  }function badPos(pos, bad) {
    if (bad) {
      pos.bad = true;
    }return pos;
  }function domTextBetween(cm, from, to, fromLine, toLine) {
    var text = "",
        closing = false,
        lineSep = cm.doc.lineSeparator(),
        extraLinebreak = false;function recognizeMarker(id) {
      return function (marker) {
        return marker.id == id;
      };
    }function close() {
      if (closing) {
        text += lineSep;if (extraLinebreak) {
          text += lineSep;
        }closing = extraLinebreak = false;
      }
    }function addText(str) {
      if (str) {
        close();text += str;
      }
    }function walk(node) {
      if (node.nodeType == 1) {
        var cmText = node.getAttribute("cm-text");if (cmText) {
          addText(cmText);return;
        }var markerID = node.getAttribute("cm-marker"),
            range$$1;if (markerID) {
          var found = cm.findMarks(Pos(fromLine, 0), Pos(toLine + 1, 0), recognizeMarker(+markerID));if (found.length && (range$$1 = found[0].find(0))) {
            addText(getBetween(cm.doc, range$$1.from, range$$1.to).join(lineSep));
          }return;
        }if (node.getAttribute("contenteditable") == "false") {
          return;
        }var isBlock = /^(pre|div|p|li|table|br)$/i.test(node.nodeName);if (!/^br$/i.test(node.nodeName) && node.textContent.length == 0) {
          return;
        }if (isBlock) {
          close();
        }for (var i = 0; i < node.childNodes.length; i++) {
          walk(node.childNodes[i]);
        }if (/^(pre|p)$/i.test(node.nodeName)) {
          extraLinebreak = true;
        }if (isBlock) {
          closing = true;
        }
      } else if (node.nodeType == 3) {
        addText(node.nodeValue.replace(/\u200b/g, "").replace(/\u00a0/g, " "));
      }
    }for (;;) {
      walk(from);if (from == to) {
        break;
      }from = from.nextSibling;extraLinebreak = false;
    }return text;
  }function domToPos(cm, node, offset) {
    var lineNode;if (node == cm.display.lineDiv) {
      lineNode = cm.display.lineDiv.childNodes[offset];if (!lineNode) {
        return badPos(cm.clipPos(Pos(cm.display.viewTo - 1)), true);
      }node = null;offset = 0;
    } else {
      for (lineNode = node;; lineNode = lineNode.parentNode) {
        if (!lineNode || lineNode == cm.display.lineDiv) {
          return null;
        }if (lineNode.parentNode && lineNode.parentNode == cm.display.lineDiv) {
          break;
        }
      }
    }for (var i = 0; i < cm.display.view.length; i++) {
      var lineView = cm.display.view[i];if (lineView.node == lineNode) {
        return locateNodeInLineView(lineView, node, offset);
      }
    }
  }function locateNodeInLineView(lineView, node, offset) {
    var wrapper = lineView.text.firstChild,
        bad = false;if (!node || !contains(wrapper, node)) {
      return badPos(Pos(lineNo(lineView.line), 0), true);
    }if (node == wrapper) {
      bad = true;node = wrapper.childNodes[offset];offset = 0;if (!node) {
        var line = lineView.rest ? lst(lineView.rest) : lineView.line;return badPos(Pos(lineNo(line), line.text.length), bad);
      }
    }var textNode = node.nodeType == 3 ? node : null,
        topNode = node;if (!textNode && node.childNodes.length == 1 && node.firstChild.nodeType == 3) {
      textNode = node.firstChild;if (offset) {
        offset = textNode.nodeValue.length;
      }
    }while (topNode.parentNode != wrapper) {
      topNode = topNode.parentNode;
    }var measure = lineView.measure,
        maps = measure.maps;function find(textNode, topNode, offset) {
      for (var i = -1; i < (maps ? maps.length : 0); i++) {
        var map$$1 = i < 0 ? measure.map : maps[i];for (var j = 0; j < map$$1.length; j += 3) {
          var curNode = map$$1[j + 2];if (curNode == textNode || curNode == topNode) {
            var line = lineNo(i < 0 ? lineView.line : lineView.rest[i]);var ch = map$$1[j] + offset;if (offset < 0 || curNode != textNode) {
              ch = map$$1[j + (offset ? 1 : 0)];
            }return Pos(line, ch);
          }
        }
      }
    }var found = find(textNode, topNode, offset);if (found) {
      return badPos(found, bad);
    }for (var after = topNode.nextSibling, dist = textNode ? textNode.nodeValue.length - offset : 0; after; after = after.nextSibling) {
      found = find(after, after.firstChild, 0);if (found) {
        return badPos(Pos(found.line, found.ch - dist), bad);
      } else {
        dist += after.textContent.length;
      }
    }for (var before = topNode.previousSibling, dist$1 = offset; before; before = before.previousSibling) {
      found = find(before, before.firstChild, -1);if (found) {
        return badPos(Pos(found.line, found.ch + dist$1), bad);
      } else {
        dist$1 += before.textContent.length;
      }
    }
  }var TextareaInput = function TextareaInput(cm) {
    this.cm = cm;this.prevInput = "";this.pollingFast = false;this.polling = new Delayed();this.hasSelection = false;this.composing = null;
  };TextareaInput.prototype.init = function (display) {
    var this$1 = this;var input = this,
        cm = this.cm;this.createField(display);var te = this.textarea;display.wrapper.insertBefore(this.wrapper, display.wrapper.firstChild);if (ios) {
      te.style.width = "0px";
    }on(te, "input", function () {
      if (ie && ie_version >= 9 && this$1.hasSelection) {
        this$1.hasSelection = null;
      }input.poll();
    });on(te, "paste", function (e) {
      if (signalDOMEvent(cm, e) || handlePaste(e, cm)) {
        return;
      }cm.state.pasteIncoming = +new Date();input.fastPoll();
    });function prepareCopyCut(e) {
      if (signalDOMEvent(cm, e)) {
        return;
      }if (cm.somethingSelected()) {
        setLastCopied({ lineWise: false, text: cm.getSelections() });
      } else if (!cm.options.lineWiseCopyCut) {
        return;
      } else {
        var ranges = copyableRanges(cm);setLastCopied({ lineWise: true, text: ranges.text });if (e.type == "cut") {
          cm.setSelections(ranges.ranges, null, sel_dontScroll);
        } else {
          input.prevInput = "";te.value = ranges.text.join("\n");selectInput(te);
        }
      }if (e.type == "cut") {
        cm.state.cutIncoming = +new Date();
      }
    }on(te, "cut", prepareCopyCut);on(te, "copy", prepareCopyCut);on(display.scroller, "paste", function (e) {
      if (eventInWidget(display, e) || signalDOMEvent(cm, e)) {
        return;
      }if (!te.dispatchEvent) {
        cm.state.pasteIncoming = +new Date();input.focus();return;
      }var event = new Event("paste");event.clipboardData = e.clipboardData;te.dispatchEvent(event);
    });on(display.lineSpace, "selectstart", function (e) {
      if (!eventInWidget(display, e)) {
        e_preventDefault(e);
      }
    });on(te, "compositionstart", function () {
      var start = cm.getCursor("from");if (input.composing) {
        input.composing.range.clear();
      }input.composing = { start: start, range: cm.markText(start, cm.getCursor("to"), { className: "CodeMirror-composing" }) };
    });on(te, "compositionend", function () {
      if (input.composing) {
        input.poll();input.composing.range.clear();input.composing = null;
      }
    });
  };TextareaInput.prototype.createField = function (_display) {
    this.wrapper = hiddenTextarea();this.textarea = this.wrapper.firstChild;
  };TextareaInput.prototype.prepareSelection = function () {
    var cm = this.cm,
        display = cm.display,
        doc = cm.doc;var result = prepareSelection(cm);if (cm.options.moveInputWithCursor) {
      var headPos = _cursorCoords(cm, doc.sel.primary().head, "div");var wrapOff = display.wrapper.getBoundingClientRect(),
          lineOff = display.lineDiv.getBoundingClientRect();result.teTop = Math.max(0, Math.min(display.wrapper.clientHeight - 10, headPos.top + lineOff.top - wrapOff.top));result.teLeft = Math.max(0, Math.min(display.wrapper.clientWidth - 10, headPos.left + lineOff.left - wrapOff.left));
    }return result;
  };TextareaInput.prototype.showSelection = function (drawn) {
    var cm = this.cm,
        display = cm.display;removeChildrenAndAdd(display.cursorDiv, drawn.cursors);removeChildrenAndAdd(display.selectionDiv, drawn.selection);if (drawn.teTop != null) {
      this.wrapper.style.top = drawn.teTop + "px";this.wrapper.style.left = drawn.teLeft + "px";
    }
  };TextareaInput.prototype.reset = function (typing) {
    if (this.contextMenuPending || this.composing) {
      return;
    }var cm = this.cm;if (cm.somethingSelected()) {
      this.prevInput = "";var content = cm.getSelection();this.textarea.value = content;if (cm.state.focused) {
        selectInput(this.textarea);
      }if (ie && ie_version >= 9) {
        this.hasSelection = content;
      }
    } else if (!typing) {
      this.prevInput = this.textarea.value = "";if (ie && ie_version >= 9) {
        this.hasSelection = null;
      }
    }
  };TextareaInput.prototype.getField = function () {
    return this.textarea;
  };TextareaInput.prototype.supportsTouch = function () {
    return false;
  };TextareaInput.prototype.focus = function () {
    if (this.cm.options.readOnly != "nocursor" && (!mobile || activeElt() != this.textarea)) {
      try {
        this.textarea.focus();
      } catch (e) {}
    }
  };TextareaInput.prototype.blur = function () {
    this.textarea.blur();
  };TextareaInput.prototype.resetPosition = function () {
    this.wrapper.style.top = this.wrapper.style.left = 0;
  };TextareaInput.prototype.receivedFocus = function () {
    this.slowPoll();
  };TextareaInput.prototype.slowPoll = function () {
    var this$1 = this;if (this.pollingFast) {
      return;
    }this.polling.set(this.cm.options.pollInterval, function () {
      this$1.poll();if (this$1.cm.state.focused) {
        this$1.slowPoll();
      }
    });
  };TextareaInput.prototype.fastPoll = function () {
    var missed = false,
        input = this;input.pollingFast = true;function p() {
      var changed = input.poll();if (!changed && !missed) {
        missed = true;input.polling.set(60, p);
      } else {
        input.pollingFast = false;input.slowPoll();
      }
    }input.polling.set(20, p);
  };TextareaInput.prototype.poll = function () {
    var this$1 = this;var cm = this.cm,
        input = this.textarea,
        prevInput = this.prevInput;if (this.contextMenuPending || !cm.state.focused || hasSelection(input) && !prevInput && !this.composing || cm.isReadOnly() || cm.options.disableInput || cm.state.keySeq) {
      return false;
    }var text = input.value;if (text == prevInput && !cm.somethingSelected()) {
      return false;
    }if (ie && ie_version >= 9 && this.hasSelection === text || mac && /[\uf700-\uf7ff]/.test(text)) {
      cm.display.input.reset();return false;
    }if (cm.doc.sel == cm.display.selForContextMenu) {
      var first = text.charCodeAt(0);if (first == 8203 && !prevInput) {
        prevInput = "​";
      }if (first == 8666) {
        this.reset();return this.cm.execCommand("undo");
      }
    }var same = 0,
        l = Math.min(prevInput.length, text.length);while (same < l && prevInput.charCodeAt(same) == text.charCodeAt(same)) {
      ++same;
    }runInOp(cm, function () {
      applyTextInput(cm, text.slice(same), prevInput.length - same, null, this$1.composing ? "*compose" : null);if (text.length > 1e3 || text.indexOf("\n") > -1) {
        input.value = this$1.prevInput = "";
      } else {
        this$1.prevInput = text;
      }if (this$1.composing) {
        this$1.composing.range.clear();this$1.composing.range = cm.markText(this$1.composing.start, cm.getCursor("to"), { className: "CodeMirror-composing" });
      }
    });return true;
  };TextareaInput.prototype.ensurePolled = function () {
    if (this.pollingFast && this.poll()) {
      this.pollingFast = false;
    }
  };TextareaInput.prototype.onKeyPress = function () {
    if (ie && ie_version >= 9) {
      this.hasSelection = null;
    }this.fastPoll();
  };TextareaInput.prototype.onContextMenu = function (e) {
    var input = this,
        cm = input.cm,
        display = cm.display,
        te = input.textarea;if (input.contextMenuPending) {
      input.contextMenuPending();
    }var pos = posFromMouse(cm, e),
        scrollPos = display.scroller.scrollTop;if (!pos || presto) {
      return;
    }var reset = cm.options.resetSelectionOnContextMenu;if (reset && cm.doc.sel.contains(pos) == -1) {
      operation(cm, setSelection)(cm.doc, simpleSelection(pos), sel_dontScroll);
    }var oldCSS = te.style.cssText,
        oldWrapperCSS = input.wrapper.style.cssText;var wrapperBox = input.wrapper.offsetParent.getBoundingClientRect();input.wrapper.style.cssText = "position: static";te.style.cssText = "position: absolute; width: 30px; height: 30px;\n      top: " + (e.clientY - wrapperBox.top - 5) + "px; left: " + (e.clientX - wrapperBox.left - 5) + "px;\n      z-index: 1000; background: " + (ie ? "rgba(255, 255, 255, .05)" : "transparent") + ";\n      outline: none; border-width: 0; outline: none; overflow: hidden; opacity: .05; filter: alpha(opacity=5);";var oldScrollY;if (webkit) {
      oldScrollY = window.scrollY;
    }display.input.focus();if (webkit) {
      window.scrollTo(null, oldScrollY);
    }display.input.reset();if (!cm.somethingSelected()) {
      te.value = input.prevInput = " ";
    }input.contextMenuPending = rehide;display.selForContextMenu = cm.doc.sel;clearTimeout(display.detectingSelectAll);function prepareSelectAllHack() {
      if (te.selectionStart != null) {
        var selected = cm.somethingSelected();var extval = "​" + (selected ? te.value : "");te.value = "⇚";te.value = extval;input.prevInput = selected ? "" : "​";te.selectionStart = 1;te.selectionEnd = extval.length;display.selForContextMenu = cm.doc.sel;
      }
    }function rehide() {
      if (input.contextMenuPending != rehide) {
        return;
      }input.contextMenuPending = false;input.wrapper.style.cssText = oldWrapperCSS;te.style.cssText = oldCSS;if (ie && ie_version < 9) {
        display.scrollbars.setScrollTop(display.scroller.scrollTop = scrollPos);
      }if (te.selectionStart != null) {
        if (!ie || ie && ie_version < 9) {
          prepareSelectAllHack();
        }var i = 0,
            poll = function poll() {
          if (display.selForContextMenu == cm.doc.sel && te.selectionStart == 0 && te.selectionEnd > 0 && input.prevInput == "​") {
            operation(cm, selectAll)(cm);
          } else if (i++ < 10) {
            display.detectingSelectAll = setTimeout(poll, 500);
          } else {
            display.selForContextMenu = null;display.input.reset();
          }
        };display.detectingSelectAll = setTimeout(poll, 200);
      }
    }if (ie && ie_version >= 9) {
      prepareSelectAllHack();
    }if (captureRightClick) {
      e_stop(e);var mouseup = function mouseup() {
        off(window, "mouseup", mouseup);setTimeout(rehide, 20);
      };on(window, "mouseup", mouseup);
    } else {
      setTimeout(rehide, 50);
    }
  };TextareaInput.prototype.readOnlyChanged = function (val) {
    if (!val) {
      this.reset();
    }this.textarea.disabled = val == "nocursor";
  };TextareaInput.prototype.setUneditable = function () {};TextareaInput.prototype.needsContentAttribute = false;function fromTextArea(textarea, options) {
    options = options ? copyObj(options) : {};options.value = textarea.value;if (!options.tabindex && textarea.tabIndex) {
      options.tabindex = textarea.tabIndex;
    }if (!options.placeholder && textarea.placeholder) {
      options.placeholder = textarea.placeholder;
    }if (options.autofocus == null) {
      var hasFocus = activeElt();options.autofocus = hasFocus == textarea || textarea.getAttribute("autofocus") != null && hasFocus == document.body;
    }function save() {
      textarea.value = cm.getValue();
    }var realSubmit;if (textarea.form) {
      on(textarea.form, "submit", save);if (!options.leaveSubmitMethodAlone) {
        var form = textarea.form;realSubmit = form.submit;try {
          var wrappedSubmit = form.submit = function () {
            save();form.submit = realSubmit;form.submit();form.submit = wrappedSubmit;
          };
        } catch (e) {}
      }
    }options.finishInit = function (cm) {
      cm.save = save;cm.getTextArea = function () {
        return textarea;
      };cm.toTextArea = function () {
        cm.toTextArea = isNaN;save();textarea.parentNode.removeChild(cm.getWrapperElement());textarea.style.display = "";if (textarea.form) {
          off(textarea.form, "submit", save);if (!options.leaveSubmitMethodAlone && typeof textarea.form.submit == "function") {
            textarea.form.submit = realSubmit;
          }
        }
      };
    };textarea.style.display = "none";var cm = CodeMirror(function (node) {
      return textarea.parentNode.insertBefore(node, textarea.nextSibling);
    }, options);return cm;
  }function addLegacyProps(CodeMirror) {
    CodeMirror.off = off;CodeMirror.on = on;CodeMirror.wheelEventPixels = wheelEventPixels;CodeMirror.Doc = Doc;CodeMirror.splitLines = splitLinesAuto;CodeMirror.countColumn = countColumn;CodeMirror.findColumn = findColumn;CodeMirror.isWordChar = isWordCharBasic;CodeMirror.Pass = Pass;CodeMirror.signal = signal;CodeMirror.Line = Line;CodeMirror.changeEnd = changeEnd;CodeMirror.scrollbarModel = scrollbarModel;CodeMirror.Pos = Pos;CodeMirror.cmpPos = cmp;CodeMirror.modes = modes;CodeMirror.mimeModes = mimeModes;CodeMirror.resolveMode = resolveMode;CodeMirror.getMode = getMode;CodeMirror.modeExtensions = modeExtensions;CodeMirror.extendMode = extendMode;CodeMirror.copyState = copyState;CodeMirror.startState = startState;CodeMirror.innerMode = innerMode;CodeMirror.commands = commands;CodeMirror.keyMap = keyMap;CodeMirror.keyName = keyName;CodeMirror.isModifierKey = isModifierKey;CodeMirror.lookupKey = lookupKey;CodeMirror.normalizeKeyMap = normalizeKeyMap;CodeMirror.StringStream = StringStream;CodeMirror.SharedTextMarker = SharedTextMarker;CodeMirror.TextMarker = TextMarker;CodeMirror.LineWidget = LineWidget;CodeMirror.e_preventDefault = e_preventDefault;CodeMirror.e_stopPropagation = e_stopPropagation;CodeMirror.e_stop = e_stop;CodeMirror.addClass = addClass;CodeMirror.contains = contains;CodeMirror.rmClass = rmClass;CodeMirror.keyNames = keyNames;
  }defineOptions(CodeMirror);addEditorMethods(CodeMirror);var dontDelegate = "iter insert remove copy getEditor constructor".split(" ");for (var prop in Doc.prototype) {
    if (Doc.prototype.hasOwnProperty(prop) && indexOf(dontDelegate, prop) < 0) {
      CodeMirror.prototype[prop] = function (method) {
        return function () {
          return method.apply(this.doc, arguments);
        };
      }(Doc.prototype[prop]);
    }
  }eventMixin(Doc);CodeMirror.inputStyles = { textarea: TextareaInput, contenteditable: ContentEditableInput };CodeMirror.defineMode = function (name) {
    if (!CodeMirror.defaults.mode && name != "null") {
      CodeMirror.defaults.mode = name;
    }defineMode.apply(this, arguments);
  };CodeMirror.defineMIME = defineMIME;CodeMirror.defineMode("null", function () {
    return { token: function token(stream) {
        return stream.skipToEnd();
      } };
  });CodeMirror.defineMIME("text/plain", "null");CodeMirror.defineExtension = function (name, func) {
    CodeMirror.prototype[name] = func;
  };CodeMirror.defineDocExtension = function (name, func) {
    Doc.prototype[name] = func;
  };CodeMirror.fromTextArea = fromTextArea;addLegacyProps(CodeMirror);CodeMirror.version = "5.49.2";return CodeMirror;
}();(function () {
  CodeMirror.defineOption("autoCloseTags", false, function (cm, val, old) {
    if (old != CodeMirror.Init && old) cm.removeKeyMap("autoCloseTags");if (!val) return;var map = { name: "autoCloseTags" };if ((typeof val === "undefined" ? "undefined" : _typeof(val)) != "object" || val.whenClosing) map["'/'"] = function (cm) {
      return autoCloseSlash(cm);
    };if ((typeof val === "undefined" ? "undefined" : _typeof(val)) != "object" || val.whenOpening) map["'>'"] = function (cm) {
      return autoCloseGT(cm);
    };cm.addKeyMap(map);
  });var htmlDontClose = ["area", "base", "br", "col", "command", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"];var htmlIndent = ["applet", "blockquote", "body", "button", "div", "dl", "fieldset", "form", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head", "html", "iframe", "layer", "legend", "object", "ol", "p", "select", "table", "ul"];function autoCloseGT(cm) {
    var pos = cm.getCursor(),
        tok = cm.getTokenAt(pos);var inner = CodeMirror.innerMode(cm.getMode(), tok.state),
        state = inner.state;if (inner.mode.name != "xml" || !state.tagName || cm.getOption("disableInput")) return CodeMirror.Pass;var opt = cm.getOption("autoCloseTags"),
        html = inner.mode.configuration == "html";var dontCloseTags = (typeof opt === "undefined" ? "undefined" : _typeof(opt)) == "object" && opt.dontCloseTags || html && htmlDontClose;var indentTags = (typeof opt === "undefined" ? "undefined" : _typeof(opt)) == "object" && opt.indentTags || html && htmlIndent;var tagName = state.tagName;if (tok.end > pos.ch) tagName = tagName.slice(0, tagName.length - tok.end + pos.ch);var lowerTagName = tagName.toLowerCase();if (!tagName || tok.type == "string" && (tok.end != pos.ch || !/[\"\']/.test(tok.string.charAt(tok.string.length - 1)) || tok.string.length == 1) || tok.type == "tag" && state.type == "closeTag" || tok.string.indexOf("/") == tok.string.length - 1 || dontCloseTags && indexOf(dontCloseTags, lowerTagName) > -1 || CodeMirror.scanForClosingTag && CodeMirror.scanForClosingTag(cm, pos, tagName, Math.min(cm.lastLine() + 1, pos.line + 50))) return CodeMirror.Pass;var doIndent = indentTags && indexOf(indentTags, lowerTagName) > -1;var curPos = doIndent ? CodeMirror.Pos(pos.line + 1, 0) : CodeMirror.Pos(pos.line, pos.ch + 1);
    cm.replaceSelection(">" + (doIndent ? "\n\n" : "") + "</" + tagName + ">", { head: curPos, anchor: curPos });if (doIndent) {
      cm.indentLine(pos.line + 1, null, true);cm.indentLine(pos.line + 2, null);
    }
  }function autoCloseSlash(cm) {
    var pos = cm.getCursor(),
        tok = cm.getTokenAt(pos);var inner = CodeMirror.innerMode(cm.getMode(), tok.state),
        state = inner.state;if (tok.type == "string" || tok.string.charAt(0) != "<" || tok.start != pos.ch - 1 || inner.mode.name != "xml" || cm.getOption("disableInput")) return CodeMirror.Pass;var tagName = state.context && state.context.tagName;if (tagName) cm.replaceSelection("/" + tagName + ">", "end");
  }function indexOf(collection, elt) {
    if (collection.indexOf) return collection.indexOf(elt);for (var i = 0, e = collection.length; i < e; ++i) {
      if (collection[i] == elt) return i;
    }return -1;
  }
})();(function () {
  "use strict";
  var noOptions = {};var nonWS = /[^\s\u00a0]/;var Pos = CodeMirror.Pos;function firstNonWS(str) {
    var found = str.search(nonWS);return found == -1 ? 0 : found;
  }CodeMirror.commands.toggleComment = function (cm) {
    var from = cm.getCursor("start"),
        to = cm.getCursor("end");cm.uncomment(from, to) || cm.lineComment(from, to);
  };CodeMirror.defineExtension("lineComment", function (from, to, options) {
    if (!options) options = noOptions;var self = this,
        mode = self.getModeAt(from);var commentString = options.lineComment || mode.lineComment;if (!commentString) {
      if (options.blockCommentStart || mode.blockCommentStart) {
        options.fullLines = true;self.blockComment(from, to, options);
      }return;
    }var firstLine = self.getLine(from.line);if (firstLine == null) return;var end = Math.min(to.ch != 0 || to.line == from.line ? to.line + 1 : to.line, self.lastLine() + 1);var pad = options.padding == null ? " " : options.padding;var blankLines = options.commentBlankLines || from.line == to.line;self.operation(function () {
      if (options.indent) {
        var baseString = firstLine.slice(0, firstNonWS(firstLine));for (var i = from.line; i < end; ++i) {
          var line = self.getLine(i),
              cut = baseString.length;if (!blankLines && !nonWS.test(line)) continue;if (line.slice(0, cut) != baseString) cut = firstNonWS(line);self.replaceRange(baseString + commentString + pad, Pos(i, 0), Pos(i, cut));
        }
      } else {
        for (var i = from.line; i < end; ++i) {
          if (blankLines || nonWS.test(self.getLine(i))) self.replaceRange(commentString + pad, Pos(i, 0));
        }
      }
    });
  });CodeMirror.defineExtension("blockComment", function (from, to, options) {
    if (!options) options = noOptions;var self = this,
        mode = self.getModeAt(from);var startString = options.blockCommentStart || mode.blockCommentStart;var endString = options.blockCommentEnd || mode.blockCommentEnd;if (!startString || !endString) {
      if ((options.lineComment || mode.lineComment) && options.fullLines != false) self.lineComment(from, to, options);return;
    }var end = Math.min(to.line, self.lastLine());if (end != from.line && to.ch == 0 && nonWS.test(self.getLine(end))) --end;var pad = options.padding == null ? " " : options.padding;if (from.line > end) return;self.operation(function () {
      if (options.fullLines != false) {
        var lastLineHasText = nonWS.test(self.getLine(end));self.replaceRange(pad + endString, Pos(end));self.replaceRange(startString + pad, Pos(from.line, 0));var lead = options.blockCommentLead || mode.blockCommentLead;if (lead != null) for (var i = from.line + 1; i <= end; ++i) {
          if (i != end || lastLineHasText) self.replaceRange(lead + pad, Pos(i, 0));
        }
      } else {
        self.replaceRange(endString, to);self.replaceRange(startString, from);
      }
    });
  });CodeMirror.defineExtension("uncomment", function (from, to, options) {
    if (!options) options = noOptions;var self = this,
        mode = self.getModeAt(from);var end = Math.min(to.line, self.lastLine()),
        start = Math.min(from.line, end);var lineString = options.lineComment || mode.lineComment,
        lines = [];var pad = options.padding == null ? " " : options.padding,
        didSomething;lineComment: {
      if (!lineString) break lineComment;for (var i = start; i <= end; ++i) {
        var line = self.getLine(i);var found = line.indexOf(lineString);if (found > -1 && !/comment/.test(self.getTokenTypeAt(Pos(i, found + 1)))) found = -1;if (found == -1 && (i != end || i == start) && nonWS.test(line)) break lineComment;if (found > -1 && nonWS.test(line.slice(0, found))) break lineComment;lines.push(line);
      }self.operation(function () {
        for (var i = start; i <= end; ++i) {
          var line = lines[i - start];var pos = line.indexOf(lineString),
              endPos = pos + lineString.length;if (pos < 0) continue;if (line.slice(endPos, endPos + pad.length) == pad) endPos += pad.length;didSomething = true;self.replaceRange("", Pos(i, pos), Pos(i, endPos));
        }
      });if (didSomething) return true;
    }var startString = options.blockCommentStart || mode.blockCommentStart;var endString = options.blockCommentEnd || mode.blockCommentEnd;if (!startString || !endString) return false;var lead = options.blockCommentLead || mode.blockCommentLead;var startLine = self.getLine(start),
        endLine = end == start ? startLine : self.getLine(end);var open = startLine.indexOf(startString),
        close = endLine.lastIndexOf(endString);if (close == -1 && start != end) {
      endLine = self.getLine(--end);close = endLine.lastIndexOf(endString);
    }if (open == -1 || close == -1 || !/comment/.test(self.getTokenTypeAt(Pos(start, open + 1))) || !/comment/.test(self.getTokenTypeAt(Pos(end, close + 1)))) return false;self.operation(function () {
      self.replaceRange("", Pos(end, close - (pad && endLine.slice(close - pad.length, close) == pad ? pad.length : 0)), Pos(end, close + endString.length));var openEnd = open + startString.length;if (pad && startLine.slice(openEnd, openEnd + pad.length) == pad) openEnd += pad.length;self.replaceRange("", Pos(start, open), Pos(start, openEnd));if (lead) for (var i = start + 1; i <= end; ++i) {
        var line = self.getLine(i),
            found = line.indexOf(lead);if (found == -1 || nonWS.test(line.slice(0, found))) continue;var foundEnd = found + lead.length;if (pad && line.slice(foundEnd, foundEnd + pad.length) == pad) foundEnd += pad.length;self.replaceRange("", Pos(i, found), Pos(i, foundEnd));
      }
    });return true;
  });
})();CodeMirror.defineMode("css", function (config, parserConfig) {
  "use strict";
  if (!parserConfig.propertyKeywords) parserConfig = CodeMirror.resolveMode("text/css");var indentUnit = config.indentUnit,
      tokenHooks = parserConfig.tokenHooks,
      mediaTypes = parserConfig.mediaTypes || {},
      mediaFeatures = parserConfig.mediaFeatures || {},
      propertyKeywords = parserConfig.propertyKeywords || {},
      colorKeywords = parserConfig.colorKeywords || {},
      valueKeywords = parserConfig.valueKeywords || {},
      fontProperties = parserConfig.fontProperties || {},
      allowNested = parserConfig.allowNested;var type, override;function ret(style, tp) {
    type = tp;return style;
  }function tokenBase(stream, state) {
    var ch = stream.next();if (tokenHooks[ch]) {
      var result = tokenHooks[ch](stream, state);if (result !== false) return result;
    }if (ch == "@") {
      stream.eatWhile(/[\w\\\-]/);return ret("def", stream.current());
    } else if (ch == "=" || (ch == "~" || ch == "|") && stream.eat("=")) {
      return ret(null, "compare");
    } else if (ch == '"' || ch == "'") {
      state.tokenize = tokenString(ch);return state.tokenize(stream, state);
    } else if (ch == "#") {
      stream.eatWhile(/[\w\\\-]/);return ret("atom", "hash");
    } else if (ch == "!") {
      stream.match(/^\s*\w*/);return ret("keyword", "important");
    } else if (/\d/.test(ch) || ch == "." && stream.eat(/\d/)) {
      stream.eatWhile(/[\w.%]/);return ret("number", "unit");
    } else if (ch === "-") {
      if (/[\d.]/.test(stream.peek())) {
        stream.eatWhile(/[\w.%]/);return ret("number", "unit");
      } else if (stream.match(/^[^-]+-/)) {
        return ret("meta", "meta");
      }
    } else if (/[,+>*\/]/.test(ch)) {
      return ret(null, "select-op");
    } else if (ch == "." && stream.match(/^-?[_a-z][_a-z0-9-]*/i)) {
      return ret("qualifier", "qualifier");
    } else if (/[:;{}\[\]\(\)]/.test(ch)) {
      return ret(null, ch);
    } else if (ch == "u" && stream.match("rl(")) {
      stream.backUp(1);state.tokenize = tokenParenthesized;return ret("property", "word");
    } else if (/[\w\\\-]/.test(ch)) {
      stream.eatWhile(/[\w\\\-]/);return ret("property", "word");
    } else {
      return ret(null, null);
    }
  }function tokenString(quote) {
    return function (stream, state) {
      var escaped = false,
          ch;while ((ch = stream.next()) != null) {
        if (ch == quote && !escaped) {
          if (quote == ")") stream.backUp(1);break;
        }escaped = !escaped && ch == "\\";
      }if (ch == quote || !escaped && quote != ")") state.tokenize = null;return ret("string", "string");
    };
  }function tokenParenthesized(stream, state) {
    stream.next();if (!stream.match(/\s*[\"\']/, false)) state.tokenize = tokenString(")");else state.tokenize = null;return ret(null, "(");
  }function Context(type, indent, prev) {
    this.type = type;this.indent = indent;this.prev = prev;
  }function pushContext(state, stream, type) {
    state.context = new Context(type, stream.indentation() + indentUnit, state.context);return type;
  }function popContext(state) {
    state.context = state.context.prev;return state.context.type;
  }function pass(type, stream, state) {
    return states[state.context.type](type, stream, state);
  }function popAndPass(type, stream, state, n) {
    for (var i = n || 1; i > 0; i--) {
      state.context = state.context.prev;
    }return pass(type, stream, state);
  }function wordAsValue(stream) {
    var word = stream.current().toLowerCase();if (valueKeywords.hasOwnProperty(word)) override = "atom";else if (colorKeywords.hasOwnProperty(word)) override = "keyword";else override = "variable";
  }var states = {};states.top = function (type, stream, state) {
    if (type == "{") {
      return pushContext(state, stream, "block");
    } else if (type == "}" && state.context.prev) {
      return popContext(state);
    } else if (type == "@media") {
      return pushContext(state, stream, "media");
    } else if (type == "@font-face") {
      return "font_face_before";
    } else if (type && type.charAt(0) == "@") {
      return pushContext(state, stream, "at");
    } else if (type == "hash") {
      override = "builtin";
    } else if (type == "word") {
      override = "tag";
    } else if (type == "variable-definition") {
      return "maybeprop";
    } else if (type == "interpolation") {
      return pushContext(state, stream, "interpolation");
    } else if (type == ":") {
      return "pseudo";
    } else if (allowNested && type == "(") {
      return pushContext(state, stream, "params");
    }return state.context.type;
  };states.block = function (type, stream, state) {
    if (type == "word") {
      if (propertyKeywords.hasOwnProperty(stream.current().toLowerCase())) {
        override = "property";return "maybeprop";
      } else if (allowNested) {
        override = stream.match(/^\s*:/, false) ? "property" : "tag";return "block";
      } else {
        override += " error";return "maybeprop";
      }
    } else if (type == "meta") {
      return "block";
    } else if (!allowNested && (type == "hash" || type == "qualifier")) {
      override = "error";return "block";
    } else {
      return states.top(type, stream, state);
    }
  };states.maybeprop = function (type, stream, state) {
    if (type == ":") return pushContext(state, stream, "prop");return pass(type, stream, state);
  };states.prop = function (type, stream, state) {
    if (type == ";") return popContext(state);if (type == "{" && allowNested) return pushContext(state, stream, "propBlock");if (type == "}" || type == "{") return popAndPass(type, stream, state);if (type == "(") return pushContext(state, stream, "parens");if (type == "hash" && !/^#([0-9a-fA-f]{3}|[0-9a-fA-f]{6})$/.test(stream.current())) {
      override += " error";
    } else if (type == "word") {
      wordAsValue(stream);
    } else if (type == "interpolation") {
      return pushContext(state, stream, "interpolation");
    }return "prop";
  };states.propBlock = function (type, _stream, state) {
    if (type == "}") return popContext(state);if (type == "word") {
      override = "property";return "maybeprop";
    }return state.context.type;
  };states.parens = function (type, stream, state) {
    if (type == "{" || type == "}") return popAndPass(type, stream, state);if (type == ")") return popContext(state);return "parens";
  };states.pseudo = function (type, stream, state) {
    if (type == "word") {
      override = "variable-3";return state.context.type;
    }return pass(type, stream, state);
  };states.media = function (type, stream, state) {
    if (type == "(") return pushContext(state, stream, "media_parens");if (type == "}") return popAndPass(type, stream, state);if (type == "{") return popContext(state) && pushContext(state, stream, allowNested ? "block" : "top");if (type == "word") {
      var word = stream.current().toLowerCase();if (word == "only" || word == "not" || word == "and") override = "keyword";else if (mediaTypes.hasOwnProperty(word)) override = "attribute";else if (mediaFeatures.hasOwnProperty(word)) override = "property";else override = "error";
    }return state.context.type;
  };states.media_parens = function (type, stream, state) {
    if (type == ")") return popContext(state);if (type == "{" || type == "}") return popAndPass(type, stream, state, 2);return states.media(type, stream, state);
  };states.font_face_before = function (type, stream, state) {
    if (type == "{") return pushContext(state, stream, "font_face");return pass(type, stream, state);
  };states.font_face = function (type, stream, state) {
    if (type == "}") return popContext(state);if (type == "word") {
      if (!fontProperties.hasOwnProperty(stream.current().toLowerCase())) override = "error";else override = "property";return "maybeprop";
    }return "font_face";
  };states.at = function (type, stream, state) {
    if (type == ";") return popContext(state);if (type == "{" || type == "}") return popAndPass(type, stream, state);if (type == "word") override = "tag";else if (type == "hash") override = "builtin";return "at";
  };states.interpolation = function (type, stream, state) {
    if (type == "}") return popContext(state);if (type == "{" || type == ";") return popAndPass(type, stream, state);if (type != "variable") override = "error";return "interpolation";
  };states.params = function (type, stream, state) {
    if (type == ")") return popContext(state);if (type == "{" || type == "}") return popAndPass(type, stream, state);if (type == "word") wordAsValue(stream);return "params";
  };return { startState: function startState(base) {
      return { tokenize: null, state: "top", context: new Context("top", base || 0, null) };
    }, token: function token(stream, state) {
      if (!state.tokenize && stream.eatSpace()) return null;var style = (state.tokenize || tokenBase)(stream, state);if (style && (typeof style === "undefined" ? "undefined" : _typeof(style)) == "object") {
        type = style[1];style = style[0];
      }override = style;state.state = states[state.state](type, stream, state);return override;
    }, indent: function indent(state, textAfter) {
      var cx = state.context,
          ch = textAfter && textAfter.charAt(0);var indent = cx.indent;if (cx.prev && (ch == "}" && (cx.type == "block" || cx.type == "top" || cx.type == "interpolation" || cx.type == "font_face") || ch == ")" && (cx.type == "parens" || cx.type == "params" || cx.type == "media_parens") || ch == "{" && (cx.type == "at" || cx.type == "media"))) {
        indent = cx.indent - indentUnit;cx = cx.prev;
      }return indent;
    }, electricChars: "}", blockCommentStart: "/*", blockCommentEnd: "*/", fold: "brace" };
});(function () {
  function keySet(array) {
    var keys = {};for (var i = 0; i < array.length; ++i) {
      keys[array[i]] = true;
    }return keys;
  }var mediaTypes_ = ["all", "aural", "braille", "handheld", "print", "projection", "screen", "tty", "tv", "embossed"],
      mediaTypes = keySet(mediaTypes_);var mediaFeatures_ = ["width", "min-width", "max-width", "height", "min-height", "max-height", "device-width", "min-device-width", "max-device-width", "device-height", "min-device-height", "max-device-height", "aspect-ratio", "min-aspect-ratio", "max-aspect-ratio", "device-aspect-ratio", "min-device-aspect-ratio", "max-device-aspect-ratio", "color", "min-color", "max-color", "color-index", "min-color-index", "max-color-index", "monochrome", "min-monochrome", "max-monochrome", "resolution", "min-resolution", "max-resolution", "scan", "grid"],
      mediaFeatures = keySet(mediaFeatures_);var propertyKeywords_ = ["align-content", "align-items", "align-self", "alignment-adjust", "alignment-baseline", "anchor-point", "animation", "animation-delay", "animation-direction", "animation-duration", "animation-iteration-count", "animation-name", "animation-play-state", "animation-timing-function", "appearance", "azimuth", "backface-visibility", "background", "background-attachment", "background-clip", "background-color", "background-image", "background-origin", "background-position", "background-repeat", "background-size", "baseline-shift", "binding", "bleed", "bookmark-label", "bookmark-level", "bookmark-state", "bookmark-target", "border", "border-bottom", "border-bottom-color", "border-bottom-left-radius", "border-bottom-right-radius", "border-bottom-style", "border-bottom-width", "border-collapse", "border-color", "border-image", "border-image-outset", "border-image-repeat", "border-image-slice", "border-image-source", "border-image-width", "border-left", "border-left-color", "border-left-style", "border-left-width", "border-radius", "border-right", "border-right-color", "border-right-style", "border-right-width", "border-spacing", "border-style", "border-top", "border-top-color", "border-top-left-radius", "border-top-right-radius", "border-top-style", "border-top-width", "border-width", "bottom", "box-decoration-break", "box-shadow", "box-sizing", "break-after", "break-before", "break-inside", "caption-side", "clear", "clip", "color", "color-profile", "column-count", "column-fill", "column-gap", "column-rule", "column-rule-color", "column-rule-style", "column-rule-width", "column-span", "column-width", "columns", "content", "counter-increment", "counter-reset", "crop", "cue", "cue-after", "cue-before", "cursor", "direction", "display", "dominant-baseline", "drop-initial-after-adjust", "drop-initial-after-align", "drop-initial-before-adjust", "drop-initial-before-align", "drop-initial-size", "drop-initial-value", "elevation", "empty-cells", "fit", "fit-position", "flex", "flex-basis", "flex-direction", "flex-flow", "flex-grow", "flex-shrink", "flex-wrap", "float", "float-offset", "flow-from", "flow-into", "font", "font-feature-settings", "font-family", "font-kerning", "font-language-override", "font-size", "font-size-adjust", "font-stretch", "font-style", "font-synthesis", "font-variant", "font-variant-alternates", "font-variant-caps", "font-variant-east-asian", "font-variant-ligatures", "font-variant-numeric", "font-variant-position", "font-weight", "grid-cell", "grid-column", "grid-column-align", "grid-column-sizing", "grid-column-span", "grid-columns", "grid-flow", "grid-row", "grid-row-align", "grid-row-sizing", "grid-row-span", "grid-rows", "grid-template", "hanging-punctuation", "height", "hyphens", "icon", "image-orientation", "image-rendering", "image-resolution", "inline-box-align", "justify-content", "left", "letter-spacing", "line-break", "line-height", "line-stacking", "line-stacking-ruby", "line-stacking-shift", "line-stacking-strategy", "list-style", "list-style-image", "list-style-position", "list-style-type", "margin", "margin-bottom", "margin-left", "margin-right", "margin-top", "marker-offset", "marks", "marquee-direction", "marquee-loop", "marquee-play-count", "marquee-speed", "marquee-style", "max-height", "max-width", "min-height", "min-width", "move-to", "nav-down", "nav-index", "nav-left", "nav-right", "nav-up", "opacity", "order", "orphans", "outline", "outline-color", "outline-offset", "outline-style", "outline-width", "overflow", "overflow-style", "overflow-wrap", "overflow-x", "overflow-y", "padding", "padding-bottom", "padding-left", "padding-right", "padding-top", "page", "page-break-after", "page-break-before", "page-break-inside", "page-policy", "pause", "pause-after", "pause-before", "perspective", "perspective-origin", "pitch", "pitch-range", "play-during", "position", "presentation-level", "punctuation-trim", "quotes", "region-break-after", "region-break-before", "region-break-inside", "region-fragment", "rendering-intent", "resize", "rest", "rest-after", "rest-before", "richness", "right", "rotation", "rotation-point", "ruby-align", "ruby-overhang", "ruby-position", "ruby-span", "shape-inside", "shape-outside", "size", "speak", "speak-as", "speak-header", "speak-numeral", "speak-punctuation", "speech-rate", "stress", "string-set", "tab-size", "table-layout", "target", "target-name", "target-new", "target-position", "text-align", "text-align-last", "text-decoration", "text-decoration-color", "text-decoration-line", "text-decoration-skip", "text-decoration-style", "text-emphasis", "text-emphasis-color", "text-emphasis-position", "text-emphasis-style", "text-height", "text-indent", "text-justify", "text-outline", "text-overflow", "text-shadow", "text-size-adjust", "text-space-collapse", "text-transform", "text-underline-position", "text-wrap", "top", "transform", "transform-origin", "transform-style", "transition", "transition-delay", "transition-duration", "transition-property", "transition-timing-function", "unicode-bidi", "vertical-align", "visibility", "voice-balance", "voice-duration", "voice-family", "voice-pitch", "voice-range", "voice-rate", "voice-stress", "voice-volume", "volume", "white-space", "widows", "width", "word-break", "word-spacing", "word-wrap", "z-index", "zoom", "clip-path", "clip-rule", "mask", "enable-background", "filter", "flood-color", "flood-opacity", "lighting-color", "stop-color", "stop-opacity", "pointer-events", "color-interpolation", "color-interpolation-filters", "color-profile", "color-rendering", "fill", "fill-opacity", "fill-rule", "image-rendering", "marker", "marker-end", "marker-mid", "marker-start", "shape-rendering", "stroke", "stroke-dasharray", "stroke-dashoffset", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity", "stroke-width", "text-rendering", "baseline-shift", "dominant-baseline", "glyph-orientation-horizontal", "glyph-orientation-vertical", "kerning", "text-anchor", "writing-mode"],
      propertyKeywords = keySet(propertyKeywords_);var colorKeywords_ = ["aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque", "black", "blanchedalmond", "blue", "blueviolet", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dodgerblue", "firebrick", "floralwhite", "forestgreen", "fuchsia", "gainsboro", "ghostwhite", "gold", "goldenrod", "gray", "grey", "green", "greenyellow", "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender", "lavenderblush", "lawngreen", "lemonchiffon", "lightblue", "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgreen", "lightpink", "lightsalmon", "lightseagreen", "lightskyblue", "lightslategray", "lightsteelblue", "lightyellow", "lime", "limegreen", "linen", "magenta", "maroon", "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue", "mintcream", "mistyrose", "moccasin", "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orange", "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise", "palevioletred", "papayawhip", "peachpuff", "peru", "pink", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray", "snow", "springgreen", "steelblue", "tan", "teal", "thistle", "tomato", "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow", "yellowgreen"],
      colorKeywords = keySet(colorKeywords_);var valueKeywords_ = ["above", "absolute", "activeborder", "activecaption", "afar", "after-white-space", "ahead", "alias", "all", "all-scroll", "alternate", "always", "amharic", "amharic-abegede", "antialiased", "appworkspace", "arabic-indic", "armenian", "asterisks", "auto", "avoid", "avoid-column", "avoid-page", "avoid-region", "background", "backwards", "baseline", "below", "bidi-override", "binary", "bengali", "blink", "block", "block-axis", "bold", "bolder", "border", "border-box", "both", "bottom", "break", "break-all", "break-word", "button", "button-bevel", "buttonface", "buttonhighlight", "buttonshadow", "buttontext", "cambodian", "capitalize", "caps-lock-indicator", "caption", "captiontext", "caret", "cell", "center", "checkbox", "circle", "cjk-earthly-branch", "cjk-heavenly-stem", "cjk-ideographic", "clear", "clip", "close-quote", "col-resize", "collapse", "column", "compact", "condensed", "contain", "content", "content-box", "context-menu", "continuous", "copy", "cover", "crop", "cross", "crosshair", "currentcolor", "cursive", "dashed", "decimal", "decimal-leading-zero", "default", "default-button", "destination-atop", "destination-in", "destination-out", "destination-over", "devanagari", "disc", "discard", "document", "dot-dash", "dot-dot-dash", "dotted", "double", "down", "e-resize", "ease", "ease-in", "ease-in-out", "ease-out", "element", "ellipse", "ellipsis", "embed", "end", "ethiopic", "ethiopic-abegede", "ethiopic-abegede-am-et", "ethiopic-abegede-gez", "ethiopic-abegede-ti-er", "ethiopic-abegede-ti-et", "ethiopic-halehame-aa-er", "ethiopic-halehame-aa-et", "ethiopic-halehame-am-et", "ethiopic-halehame-gez", "ethiopic-halehame-om-et", "ethiopic-halehame-sid-et", "ethiopic-halehame-so-et", "ethiopic-halehame-ti-er", "ethiopic-halehame-ti-et", "ethiopic-halehame-tig", "ew-resize", "expanded", "extra-condensed", "extra-expanded", "fantasy", "fast", "fill", "fixed", "flat", "footnotes", "forwards", "from", "geometricPrecision", "georgian", "graytext", "groove", "gujarati", "gurmukhi", "hand", "hangul", "hangul-consonant", "hebrew", "help", "hidden", "hide", "higher", "highlight", "highlighttext", "hiragana", "hiragana-iroha", "horizontal", "hsl", "hsla", "icon", "ignore", "inactiveborder", "inactivecaption", "inactivecaptiontext", "infinite", "infobackground", "infotext", "inherit", "initial", "inline", "inline-axis", "inline-block", "inline-table", "inset", "inside", "intrinsic", "invert", "italic", "justify", "kannada", "katakana", "katakana-iroha", "keep-all", "khmer", "landscape", "lao", "large", "larger", "left", "level", "lighter", "line-through", "linear", "lines", "list-item", "listbox", "listitem", "local", "logical", "loud", "lower", "lower-alpha", "lower-armenian", "lower-greek", "lower-hexadecimal", "lower-latin", "lower-norwegian", "lower-roman", "lowercase", "ltr", "malayalam", "match", "media-controls-background", "media-current-time-display", "media-fullscreen-button", "media-mute-button", "media-play-button", "media-return-to-realtime-button", "media-rewind-button", "media-seek-back-button", "media-seek-forward-button", "media-slider", "media-sliderthumb", "media-time-remaining-display", "media-volume-slider", "media-volume-slider-container", "media-volume-sliderthumb", "medium", "menu", "menulist", "menulist-button", "menulist-text", "menulist-textfield", "menutext", "message-box", "middle", "min-intrinsic", "mix", "mongolian", "monospace", "move", "multiple", "myanmar", "n-resize", "narrower", "ne-resize", "nesw-resize", "no-close-quote", "no-drop", "no-open-quote", "no-repeat", "none", "normal", "not-allowed", "nowrap", "ns-resize", "nw-resize", "nwse-resize", "oblique", "octal", "open-quote", "optimizeLegibility", "optimizeSpeed", "oriya", "oromo", "outset", "outside", "outside-shape", "overlay", "overline", "padding", "padding-box", "painted", "page", "paused", "persian", "plus-darker", "plus-lighter", "pointer", "polygon", "portrait", "pre", "pre-line", "pre-wrap", "preserve-3d", "progress", "push-button", "radio", "read-only", "read-write", "read-write-plaintext-only", "rectangle", "region", "relative", "repeat", "repeat-x", "repeat-y", "reset", "reverse", "rgb", "rgba", "ridge", "right", "round", "row-resize", "rtl", "run-in", "running", "s-resize", "sans-serif", "scroll", "scrollbar", "se-resize", "searchfield", "searchfield-cancel-button", "searchfield-decoration", "searchfield-results-button", "searchfield-results-decoration", "semi-condensed", "semi-expanded", "separate", "serif", "show", "sidama", "single", "skip-white-space", "slide", "slider-horizontal", "slider-vertical", "sliderthumb-horizontal", "sliderthumb-vertical", "slow", "small", "small-caps", "small-caption", "smaller", "solid", "somali", "source-atop", "source-in", "source-out", "source-over", "space", "square", "square-button", "start", "static", "status-bar", "stretch", "stroke", "sub", "subpixel-antialiased", "super", "sw-resize", "table", "table-caption", "table-cell", "table-column", "table-column-group", "table-footer-group", "table-header-group", "table-row", "table-row-group", "telugu", "text", "text-bottom", "text-top", "textarea", "textfield", "thai", "thick", "thin", "threeddarkshadow", "threedface", "threedhighlight", "threedlightshadow", "threedshadow", "tibetan", "tigre", "tigrinya-er", "tigrinya-er-abegede", "tigrinya-et", "tigrinya-et-abegede", "to", "top", "transparent", "ultra-condensed", "ultra-expanded", "underline", "up", "upper-alpha", "upper-armenian", "upper-greek", "upper-hexadecimal", "upper-latin", "upper-norwegian", "upper-roman", "uppercase", "urdu", "url", "vertical", "vertical-text", "visible", "visibleFill", "visiblePainted", "visibleStroke", "visual", "w-resize", "wait", "wave", "wider", "window", "windowframe", "windowtext", "x-large", "x-small", "xor", "xx-large", "xx-small"],
      valueKeywords = keySet(valueKeywords_);var fontProperties_ = ["font-family", "src", "unicode-range", "font-variant", "font-feature-settings", "font-stretch", "font-weight", "font-style"],
      fontProperties = keySet(fontProperties_);var allWords = mediaTypes_.concat(mediaFeatures_).concat(propertyKeywords_).concat(colorKeywords_).concat(valueKeywords_);CodeMirror.registerHelper("hintWords", "css", allWords);function tokenCComment(stream, state) {
    var maybeEnd = false,
        ch;while ((ch = stream.next()) != null) {
      if (maybeEnd && ch == "/") {
        state.tokenize = null;break;
      }maybeEnd = ch == "*";
    }return ["comment", "comment"];
  }function tokenSGMLComment(stream, state) {
    if (stream.skipTo("-->")) {
      stream.match("-->");state.tokenize = null;
    } else {
      stream.skipToEnd();
    }return ["comment", "comment"];
  }CodeMirror.defineMIME("text/css", { mediaTypes: mediaTypes, mediaFeatures: mediaFeatures, propertyKeywords: propertyKeywords, colorKeywords: colorKeywords, valueKeywords: valueKeywords, fontProperties: fontProperties, tokenHooks: { "<": function _(stream, state) {
        if (!stream.match("!--")) return false;state.tokenize = tokenSGMLComment;return tokenSGMLComment(stream, state);
      }, "/": function _(stream, state) {
        if (!stream.eat("*")) return false;state.tokenize = tokenCComment;return tokenCComment(stream, state);
      } }, name: "css" });CodeMirror.defineMIME("text/x-scss", { mediaTypes: mediaTypes, mediaFeatures: mediaFeatures, propertyKeywords: propertyKeywords, colorKeywords: colorKeywords, valueKeywords: valueKeywords, fontProperties: fontProperties, allowNested: true, tokenHooks: { "/": function _(stream, state) {
        if (stream.eat("/")) {
          stream.skipToEnd();return ["comment", "comment"];
        } else if (stream.eat("*")) {
          state.tokenize = tokenCComment;return tokenCComment(stream, state);
        } else {
          return ["operator", "operator"];
        }
      }, ":": function _(stream) {
        if (stream.match(/\s*{/)) return [null, "{"];return false;
      }, $: function $(stream) {
        stream.match(/^[\w-]+/);if (stream.match(/^\s*:/, false)) return ["variable-2", "variable-definition"];return ["variable-2", "variable"];
      }, "#": function _(stream) {
        if (!stream.eat("{")) return false;return [null, "interpolation"];
      } }, name: "css", helperType: "scss" });CodeMirror.defineMIME("text/x-less", { mediaTypes: mediaTypes, mediaFeatures: mediaFeatures, propertyKeywords: propertyKeywords, colorKeywords: colorKeywords, valueKeywords: valueKeywords, fontProperties: fontProperties, allowNested: true, tokenHooks: { "/": function _(stream, state) {
        if (stream.eat("/")) {
          stream.skipToEnd();return ["comment", "comment"];
        } else if (stream.eat("*")) {
          state.tokenize = tokenCComment;return tokenCComment(stream, state);
        } else {
          return ["operator", "operator"];
        }
      }, "@": function _(stream) {
        if (stream.match(/^(charset|document|font-face|import|keyframes|media|namespace|page|supports)\b/, false)) return false;stream.eatWhile(/[\w\\\-]/);if (stream.match(/^\s*:/, false)) return ["variable-2", "variable-definition"];return ["variable-2", "variable"];
      }, "&": function _() {
        return ["atom", "atom"];
      } }, name: "css", helperType: "less" });
})();CodeMirror.defineMode("diff", function () {
  var TOKEN_NAMES = { "+": "positive", "-": "negative", "@": "meta" };return { token: function token(stream) {
      var tw_pos = stream.string.search(/[\t ]+?$/);if (!stream.sol() || tw_pos === 0) {
        stream.skipToEnd();return ("error " + (TOKEN_NAMES[stream.string.charAt(0)] || "")).replace(/ $/, "");
      }var token_name = TOKEN_NAMES[stream.peek()] || stream.skipToEnd();if (tw_pos === -1) {
        stream.skipToEnd();
      } else {
        stream.pos = tw_pos;
      }return token_name;
    } };
});CodeMirror.defineMIME("text/x-diff", "diff");CodeMirror.defineMode("edx_markdown", function (cmCfg, modeCfg) {
  var htmlFound = CodeMirror.mimeModes.hasOwnProperty("text/html");var htmlMode = CodeMirror.getMode(cmCfg, htmlFound ? "text/html" : "text/plain");var header = "header",
      code = "comment",
      quote = "quote",
      list = "string",
      hr = "hr",
      linktext = "link",
      linkhref = "string",
      em = "em",
      strong = "strong",
      emstrong = "emstrong";var hrRE = /^([*\-=_])(?:\s*\1){2,}\s*$/,
      ulRE = /^[*\-+]\s+/,
      olRE = /^[0-9]+\.\s+/,
      headerRE = /^(?:\={3,}|-{3,})$/,
      textRE = /^[^\[*_\\<>`]+/;function switchInline(stream, state, f) {
    state.f = state.inline = f;return f(stream, state);
  }function switchBlock(stream, state, f) {
    state.f = state.block = f;return f(stream, state);
  }function blankLine(state) {
    state.em = false;state.strong = false;if (!htmlFound && state.f == htmlBlock) {
      state.f = inlineNormal;state.block = blockNormal;
    }return null;
  }function escapeHtml(unsafe) {
    return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }function blockNormal(stream, state) {
    var match;if (state.indentationDiff >= 4) {
      state.indentation -= state.indentationDiff;stream.skipToEnd();return code;
    } else if (stream.eatSpace()) {
      return null;
    } else if (stream.peek() === "#" || stream.match(headerRE)) {
      state.header = true;
    } else if (stream.eat(">")) {
      state.indentation++;state.quote = true;
    } else if (stream.peek() === "[") {
      return switchInline(stream, state, footnoteLink);
    } else if (stream.match(hrRE, true)) {
      return hr;
    } else if (match = stream.match(ulRE, true) || stream.match(olRE, true)) {
      state.indentation += match[0].length;return list;
    }return switchInline(stream, state, state.inline);
  }function htmlBlock(stream, state) {
    var style = htmlMode.token(stream, state.htmlState);if (htmlFound && style === "tag" && state.htmlState.type !== "openTag" && !state.htmlState.context) {
      state.f = inlineNormal;state.block = blockNormal;
    }if (state.md_inside && stream.current().indexOf(">") != -1) {
      state.f = inlineNormal;state.block = blockNormal;state.htmlState.context = undefined;
    }return style;
  }function getType(state) {
    var styles = [];if (state.strong) {
      styles.push(state.em ? emstrong : strong);
    } else if (state.em) {
      styles.push(em);
    }if (state.header) {
      styles.push(header);
    }if (state.quote) {
      styles.push(quote);
    }return styles.length ? styles.join(" ") : null;
  }function handleText(stream, state) {
    if (stream.match(textRE, true)) {
      return getType(state);
    }return undefined;
  }function inlineNormal(stream, state) {
    var style = state.text(stream, state);if (typeof style !== "undefined") return style;var ch = stream.next();if (ch === "\\") {
      stream.next();return getType(state);
    }if (ch === "`") {
      return switchInline(stream, state, inlineElement(code, "`"));
    }if (ch === "[") {
      return switchInline(stream, state, linkText);
    }if (ch === "<" && stream.match(/^\w/, false)) {
      var md_inside = false;if (stream.string.indexOf(">") != -1) {
        var atts = stream.string.substring(1, stream.string.indexOf(">"));if (/markdown\s*=\s*('|"){0,1}1('|"){0,1}/.test(atts)) {
          state.md_inside = true;
        }
      }stream.backUp(1);return switchBlock(stream, state, htmlBlock);
    }if (ch === "<" && stream.match(/^\/\w*?>/)) {
      state.md_inside = false;return "tag";
    }var t = getType(state);if (ch === "*" || ch === "_") {
      if (stream.eat(ch)) {
        return (state.strong = !state.strong) ? getType(state) : t;
      }return (state.em = !state.em) ? getType(state) : t;
    }return getType(state);
  }function linkText(stream, state) {
    while (!stream.eol()) {
      var ch = stream.next();if (ch === "\\") stream.next();if (ch === "]") {
        state.inline = state.f = linkHref;return linktext;
      }
    }return linktext;
  }function linkHref(stream, state) {
    stream.eatSpace();var ch = stream.next();if (ch === "(" || ch === "[") {
      return switchInline(stream, state, inlineElement(linkhref, ch === "(" ? ")" : "]"));
    }return "error";
  }function footnoteLink(stream, state) {
    if (stream.match(/^[^\]]*\]:/, true)) {
      state.f = footnoteUrl;return linktext;
    }return switchInline(stream, state, inlineNormal);
  }function footnoteUrl(stream, state) {
    stream.eatSpace();stream.match(/^[^\s]+/, true);state.f = state.inline = inlineNormal;return linkhref;
  }function inlineRE(endChar) {
    if (!inlineRE[endChar]) {
      inlineRE[endChar] = new RegExp("^(?:[^\\\\\\" + endChar + "]|\\\\.)*(?:\\" + endChar + "|$)");
    }return inlineRE[endChar];
  }function inlineElement(type, endChar, next) {
    next = next || inlineNormal;return function (stream, state) {
      stream.match(inlineRE(endChar));state.inline = state.f = next;return type;
    };
  }return { startState: function startState() {
      return { f: blockNormal, block: blockNormal, htmlState: CodeMirror.startState(htmlMode), indentation: 0, inline: inlineNormal, text: handleText, em: false, strong: false, header: false, quote: false };
    }, copyState: function copyState(s) {
      return { f: s.f, block: s.block, htmlState: CodeMirror.copyState(htmlMode, s.htmlState), indentation: s.indentation, inline: s.inline, text: s.text, em: s.em, strong: s.strong, header: s.header, quote: s.quote, md_inside: s.md_inside };
    }, token: function token(stream, state) {
      if (stream.sol()) {
        if (stream.match(/^\s*$/, true)) {
          return blankLine(state);
        }state.header = false;state.quote = false;state.f = state.block;var indentation = stream.match(/^\s*/, true)[0].replace(/\t/g, "    ").length;state.indentationDiff = indentation - state.indentation;state.indentation = indentation;if (indentation > 0) {
          return null;
        }
      }return state.f(stream, state);
    }, blankLine: blankLine, getType: getType };
}, "xml");CodeMirror.defineMIME("text/x-markdown", "markdown");(function () {
  CodeMirror.extendMode("css", { commentStart: "/*", commentEnd: "*/", newlineAfterToken: function newlineAfterToken(_type, content) {
      return (/^[;{}]$/.test(content)
      );
    } });CodeMirror.extendMode("javascript", { commentStart: "/*", commentEnd: "*/", newlineAfterToken: function newlineAfterToken(_type, content, textAfter, state) {
      if (this.jsonMode) {
        return (/^[\[,{]$/.test(content) || /^}/.test(textAfter)
        );
      } else {
        if (content == ";" && state.lexical && state.lexical.type == ")") return false;return (/^[;{}]$/.test(content) && !/^;/.test(textAfter)
        );
      }
    } });var inlineElements = /^(a|abbr|acronym|area|base|bdo|big|br|button|caption|cite|code|col|colgroup|dd|del|dfn|em|frame|hr|iframe|img|input|ins|kbd|label|legend|link|map|object|optgroup|option|param|q|samp|script|select|small|span|strong|sub|sup|textarea|tt|var)$/;CodeMirror.extendMode("xml", { commentStart: "<!--", commentEnd: "-->", newlineAfterToken: function newlineAfterToken(type, content, textAfter, state) {
      var inline = false;if (this.configuration == "html") inline = state.context ? inlineElements.test(state.context.tagName) : false;return !inline && (type == "tag" && />$/.test(content) && state.context || /^</.test(textAfter));
    } });CodeMirror.defineExtension("commentRange", function (isComment, from, to) {
    var cm = this,
        curMode = CodeMirror.innerMode(cm.getMode(), cm.getTokenAt(from).state).mode;cm.operation(function () {
      if (isComment) {
        cm.replaceRange(curMode.commentEnd, to);cm.replaceRange(curMode.commentStart, from);if (from.line == to.line && from.ch == to.ch) cm.setCursor(from.line, from.ch + curMode.commentStart.length);
      } else {
        var selText = cm.getRange(from, to);var startIndex = selText.indexOf(curMode.commentStart);var endIndex = selText.lastIndexOf(curMode.commentEnd);if (startIndex > -1 && endIndex > -1 && endIndex > startIndex) {
          selText = selText.substr(0, startIndex) + selText.substring(startIndex + curMode.commentStart.length, endIndex) + selText.substr(endIndex + curMode.commentEnd.length);
        }cm.replaceRange(selText, from, to);
      }
    });
  });CodeMirror.defineExtension("autoIndentRange", function (from, to) {
    var cmInstance = this;this.operation(function () {
      for (var i = from.line; i <= to.line; i++) {
        cmInstance.indentLine(i, "smart");
      }
    });
  });CodeMirror.defineExtension("autoFormatRange", function (from, to) {
    var cm = this;var outer = cm.getMode(),
        text = cm.getRange(from, to).split("\n");var state = CodeMirror.copyState(outer, cm.getTokenAt(from).state);var tabSize = cm.getOption("tabSize");var out = "",
        lines = 0,
        atSol = from.ch == 0;function newline() {
      out += "\n";atSol = true;++lines;
    }for (var i = 0; i < text.length; ++i) {
      var stream = new CodeMirror.StringStream(text[i], tabSize);while (!stream.eol()) {
        var inner = CodeMirror.innerMode(outer, state);var style = outer.token(stream, state),
            cur = stream.current();stream.start = stream.pos;if (!atSol || /\S/.test(cur)) {
          out += cur;atSol = false;
        }if (!atSol && inner.mode.newlineAfterToken && inner.mode.newlineAfterToken(style, cur, stream.string.slice(stream.pos) || text[i + 1] || "", inner.state)) newline();
      }if (!stream.pos && outer.blankLine) outer.blankLine(state);if (!atSol && i < text.length - 1) newline();
    }cm.operation(function () {
      cm.replaceRange(out, from, to);for (var cur = from.line + 1, end = from.line + lines; cur <= end; ++cur) {
        cm.indentLine(cur, "smart");
      }cm.setSelection(from, cm.getCursor(false));
    });
  });
})();CodeMirror.defineMode("htmlembedded", function (config, parserConfig) {
  var scriptStartRegex = parserConfig.scriptStartRegex || /^<%/i,
      scriptEndRegex = parserConfig.scriptEndRegex || /^%>/i;var scriptingMode, htmlMixedMode;function htmlDispatch(stream, state) {
    if (stream.match(scriptStartRegex, false)) {
      state.token = scriptingDispatch;return scriptingMode.token(stream, state.scriptState);
    } else return htmlMixedMode.token(stream, state.htmlState);
  }function scriptingDispatch(stream, state) {
    if (stream.match(scriptEndRegex, false)) {
      state.token = htmlDispatch;return htmlMixedMode.token(stream, state.htmlState);
    } else return scriptingMode.token(stream, state.scriptState);
  }return { startState: function startState() {
      scriptingMode = scriptingMode || CodeMirror.getMode(config, parserConfig.scriptingModeSpec);htmlMixedMode = htmlMixedMode || CodeMirror.getMode(config, "htmlmixed");return { token: parserConfig.startOpen ? scriptingDispatch : htmlDispatch, htmlState: CodeMirror.startState(htmlMixedMode), scriptState: CodeMirror.startState(scriptingMode) };
    }, token: function token(stream, state) {
      return state.token(stream, state);
    }, indent: function indent(state, textAfter) {
      if (state.token == htmlDispatch) return htmlMixedMode.indent(state.htmlState, textAfter);else if (scriptingMode.indent) return scriptingMode.indent(state.scriptState, textAfter);
    }, copyState: function copyState(state) {
      return { token: state.token, htmlState: CodeMirror.copyState(htmlMixedMode, state.htmlState), scriptState: CodeMirror.copyState(scriptingMode, state.scriptState) };
    }, innerMode: function innerMode(state) {
      if (state.token == scriptingDispatch) return { state: state.scriptState, mode: scriptingMode };else return { state: state.htmlState, mode: htmlMixedMode };
    } };
}, "htmlmixed");CodeMirror.defineMIME("application/x-ejs", { name: "htmlembedded", scriptingModeSpec: "javascript" });CodeMirror.defineMIME("application/x-aspx", { name: "htmlembedded", scriptingModeSpec: "text/x-csharp" });CodeMirror.defineMIME("application/x-jsp", { name: "htmlembedded", scriptingModeSpec: "text/x-java" });CodeMirror.defineMIME("application/x-erb", { name: "htmlembedded", scriptingModeSpec: "ruby" });CodeMirror.defineMode("htmlmixed", function (config, parserConfig) {
  var htmlMode = CodeMirror.getMode(config, { name: "xml", htmlMode: true });var cssMode = CodeMirror.getMode(config, "css");var scriptTypes = [],
      scriptTypesConf = parserConfig && parserConfig.scriptTypes;scriptTypes.push({ matches: /^(?:text|application)\/(?:x-)?(?:java|ecma)script$|^$/i, mode: CodeMirror.getMode(config, "javascript") });if (scriptTypesConf) for (var i = 0; i < scriptTypesConf.length; ++i) {
    var conf = scriptTypesConf[i];scriptTypes.push({ matches: conf.matches, mode: conf.mode && CodeMirror.getMode(config, conf.mode) });
  }scriptTypes.push({ matches: /./, mode: CodeMirror.getMode(config, "text/plain") });function html(stream, state) {
    var tagName = state.htmlState.tagName;var style = htmlMode.token(stream, state.htmlState);if (tagName == "script" && /\btag\b/.test(style) && stream.current() == ">") {
      var scriptType = stream.string.slice(Math.max(0, stream.pos - 100), stream.pos).match(/\btype\s*=\s*("[^"]+"|'[^']+'|\S+)[^<]*$/i);scriptType = scriptType ? scriptType[1] : "";if (scriptType && /[\"\']/.test(scriptType.charAt(0))) scriptType = scriptType.slice(1, scriptType.length - 1);for (var i = 0; i < scriptTypes.length; ++i) {
        var tp = scriptTypes[i];if (typeof tp.matches == "string" ? scriptType == tp.matches : tp.matches.test(scriptType)) {
          if (tp.mode) {
            state.token = script;state.localMode = tp.mode;state.localState = tp.mode.startState && tp.mode.startState(htmlMode.indent(state.htmlState, ""));
          }break;
        }
      }
    } else if (tagName == "style" && /\btag\b/.test(style) && stream.current() == ">") {
      state.token = css;state.localMode = cssMode;state.localState = cssMode.startState(htmlMode.indent(state.htmlState, ""));
    }return style;
  }function maybeBackup(stream, pat, style) {
    var cur = stream.current();var close = cur.search(pat),
        m;if (close > -1) stream.backUp(cur.length - close);else if (m = cur.match(/<\/?$/)) {
      stream.backUp(cur.length);if (!stream.match(pat, false)) stream.match(cur);
    }return style;
  }function script(stream, state) {
    if (stream.match(/^<\/\s*script\s*>/i, false)) {
      state.token = html;state.localState = state.localMode = null;return html(stream, state);
    }return maybeBackup(stream, /<\/\s*script\s*>/, state.localMode.token(stream, state.localState));
  }function css(stream, state) {
    if (stream.match(/^<\/\s*style\s*>/i, false)) {
      state.token = html;state.localState = state.localMode = null;return html(stream, state);
    }return maybeBackup(stream, /<\/\s*style\s*>/, cssMode.token(stream, state.localState));
  }return { startState: function startState() {
      var state = htmlMode.startState();return { token: html, localMode: null, localState: null, htmlState: state };
    }, copyState: function copyState(state) {
      if (state.localState) var local = CodeMirror.copyState(state.localMode, state.localState);return { token: state.token, localMode: state.localMode, localState: local, htmlState: CodeMirror.copyState(htmlMode, state.htmlState) };
    }, token: function token(stream, state) {
      return state.token(stream, state);
    }, indent: function indent(state, textAfter) {
      if (!state.localMode || /^\s*<\//.test(textAfter)) return htmlMode.indent(state.htmlState, textAfter);else if (state.localMode.indent) return state.localMode.indent(state.localState, textAfter);else return CodeMirror.Pass;
    }, innerMode: function innerMode(state) {
      return { state: state.localState || state.htmlState, mode: state.localMode || htmlMode };
    } };
}, "xml", "javascript", "css");CodeMirror.defineMIME("text/html", "htmlmixed");CodeMirror.defineMode("javascript", function (config, parserConfig) {
  var indentUnit = config.indentUnit;var statementIndent = parserConfig.statementIndent;var jsonMode = parserConfig.json;var isTS = parserConfig.typescript;var keywords = function () {
    function kw(type) {
      return { type: type, style: "keyword" };
    }var A = kw("keyword a"),
        B = kw("keyword b"),
        C = kw("keyword c");var operator = kw("operator"),
        atom = { type: "atom", style: "atom" };var jsKeywords = { if: kw("if"), while: A, with: A, else: B, do: B, try: B, finally: B, return: C, break: C, continue: C, new: C, delete: C, throw: C, debugger: C, var: kw("var"), const: kw("var"), let: kw("var"), function: kw("function"), catch: kw("catch"), for: kw("for"), switch: kw("switch"), case: kw("case"), default: kw("default"), in: operator, typeof: operator, instanceof: operator, true: atom, false: atom, null: atom, undefined: atom, NaN: atom, Infinity: atom, this: kw("this"), module: kw("module"), class: kw("class"), super: kw("atom"), yield: C, export: kw("export"), import: kw("import"), extends: C };if (isTS) {
      var type = { type: "variable", style: "variable-3" };var tsKeywords = { interface: kw("interface"), extends: kw("extends"), constructor: kw("constructor"), public: kw("public"), private: kw("private"), protected: kw("protected"), static: kw("static"), string: type, number: type, bool: type, any: type };for (var attr in tsKeywords) {
        jsKeywords[attr] = tsKeywords[attr];
      }
    }return jsKeywords;
  }();var isOperatorChar = /[+\-*&%=<>!?|~^]/;function readRegexp(stream) {
    var escaped = false,
        next,
        inSet = false;while ((next = stream.next()) != null) {
      if (!escaped) {
        if (next == "/" && !inSet) return;if (next == "[") inSet = true;else if (inSet && next == "]") inSet = false;
      }escaped = !escaped && next == "\\";
    }
  }var type, content;function ret(tp, style, cont) {
    type = tp;content = cont;return style;
  }function tokenBase(stream, state) {
    var ch = stream.next();if (ch == '"' || ch == "'") {
      state.tokenize = tokenString(ch);return state.tokenize(stream, state);
    } else if (ch == "." && stream.match(/^\d+(?:[eE][+\-]?\d+)?/)) {
      return ret("number", "number");
    } else if (ch == "." && stream.match("..")) {
      return ret("spread", "meta");
    } else if (/[\[\]{}\(\),;\:\.]/.test(ch)) {
      return ret(ch);
    } else if (ch == "=" && stream.eat(">")) {
      return ret("=>", "operator");
    } else if (ch == "0" && stream.eat(/x/i)) {
      stream.eatWhile(/[\da-f]/i);return ret("number", "number");
    } else if (/\d/.test(ch)) {
      stream.match(/^\d*(?:\.\d*)?(?:[eE][+\-]?\d+)?/);return ret("number", "number");
    } else if (ch == "/") {
      if (stream.eat("*")) {
        state.tokenize = tokenComment;return tokenComment(stream, state);
      } else if (stream.eat("/")) {
        stream.skipToEnd();return ret("comment", "comment");
      } else if (state.lastType == "operator" || state.lastType == "keyword c" || state.lastType == "sof" || /^[\[{}\(,;:]$/.test(state.lastType)) {
        readRegexp(stream);stream.eatWhile(/[gimy]/);return ret("regexp", "string-2");
      } else {
        stream.eatWhile(isOperatorChar);return ret("operator", "operator", stream.current());
      }
    } else if (ch == "`") {
      state.tokenize = tokenQuasi;return tokenQuasi(stream, state);
    } else if (ch == "#") {
      stream.skipToEnd();return ret("error", "error");
    } else if (isOperatorChar.test(ch)) {
      stream.eatWhile(isOperatorChar);return ret("operator", "operator", stream.current());
    } else {
      stream.eatWhile(/[\w\$_]/);var word = stream.current(),
          known = keywords.propertyIsEnumerable(word) && keywords[word];return known && state.lastType != "." ? ret(known.type, known.style, word) : ret("variable", "variable", word);
    }
  }function tokenString(quote) {
    return function (stream, state) {
      var escaped = false,
          next;while ((next = stream.next()) != null) {
        if (next == quote && !escaped) break;escaped = !escaped && next == "\\";
      }if (!escaped) state.tokenize = tokenBase;return ret("string", "string");
    };
  }function tokenComment(stream, state) {
    var maybeEnd = false,
        ch;while (ch = stream.next()) {
      if (ch == "/" && maybeEnd) {
        state.tokenize = tokenBase;break;
      }maybeEnd = ch == "*";
    }return ret("comment", "comment");
  }function tokenQuasi(stream, state) {
    var escaped = false,
        next;while ((next = stream.next()) != null) {
      if (!escaped && (next == "`" || next == "$" && stream.eat("{"))) {
        state.tokenize = tokenBase;break;
      }escaped = !escaped && next == "\\";
    }return ret("quasi", "string-2", stream.current());
  }var brackets = "([{}])";function findFatArrow(stream, state) {
    if (state.fatArrowAt) state.fatArrowAt = null;var arrow = stream.string.indexOf("=>", stream.start);if (arrow < 0) return;var depth = 0,
        sawSomething = false;for (var pos = arrow - 1; pos >= 0; --pos) {
      var ch = stream.string.charAt(pos);var bracket = brackets.indexOf(ch);if (bracket >= 0 && bracket < 3) {
        if (!depth) {
          ++pos;break;
        }if (--depth == 0) break;
      } else if (bracket >= 3 && bracket < 6) {
        ++depth;
      } else if (/[$\w]/.test(ch)) {
        sawSomething = true;
      } else if (sawSomething && !depth) {
        ++pos;break;
      }
    }if (sawSomething && !depth) state.fatArrowAt = pos;
  }var atomicTypes = { atom: true, number: true, variable: true, string: true, regexp: true, this: true };function JSLexical(indented, column, type, align, prev, info) {
    this.indented = indented;this.column = column;this.type = type;this.prev = prev;this.info = info;if (align != null) this.align = align;
  }function inScope(state, varname) {
    for (var v = state.localVars; v; v = v.next) {
      if (v.name == varname) return true;
    }for (var cx = state.context; cx; cx = cx.prev) {
      for (var v = cx.vars; v; v = v.next) {
        if (v.name == varname) return true;
      }
    }
  }function parseJS(state, style, type, content, stream) {
    var cc = state.cc;cx.state = state;cx.stream = stream;cx.marked = null, cx.cc = cc;if (!state.lexical.hasOwnProperty("align")) state.lexical.align = true;while (true) {
      var combinator = cc.length ? cc.pop() : jsonMode ? expression : statement;if (combinator(type, content)) {
        while (cc.length && cc[cc.length - 1].lex) {
          cc.pop()();
        }if (cx.marked) return cx.marked;if (type == "variable" && inScope(state, content)) return "variable-2";return style;
      }
    }
  }var cx = { state: null, column: null, marked: null, cc: null };function pass() {
    for (var i = arguments.length - 1; i >= 0; i--) {
      cx.cc.push(arguments[i]);
    }
  }function cont() {
    pass.apply(null, arguments);return true;
  }function register(varname) {
    function inList(list) {
      for (var v = list; v; v = v.next) {
        if (v.name == varname) return true;
      }return false;
    }var state = cx.state;if (state.context) {
      cx.marked = "def";if (inList(state.localVars)) return;state.localVars = { name: varname, next: state.localVars };
    } else {
      if (inList(state.globalVars)) return;if (parserConfig.globalVars) state.globalVars = { name: varname, next: state.globalVars };
    }
  }var defaultVars = { name: "this", next: { name: "arguments" } };function pushcontext() {
    cx.state.context = { prev: cx.state.context, vars: cx.state.localVars };cx.state.localVars = defaultVars;
  }function popcontext() {
    cx.state.localVars = cx.state.context.vars;cx.state.context = cx.state.context.prev;
  }function pushlex(type, info) {
    var result = function result() {
      var state = cx.state,
          indent = state.indented;if (state.lexical.type == "stat") indent = state.lexical.indented;state.lexical = new JSLexical(indent, cx.stream.column(), type, null, state.lexical, info);
    };result.lex = true;return result;
  }function poplex() {
    var state = cx.state;if (state.lexical.prev) {
      if (state.lexical.type == ")") state.indented = state.lexical.indented;state.lexical = state.lexical.prev;
    }
  }poplex.lex = true;function expect(wanted) {
    return function (type) {
      if (type == wanted) return cont();else if (wanted == ";") return pass();else return cont(arguments.callee);
    };
  }function statement(type, value) {
    if (type == "var") return cont(pushlex("vardef", value.length), vardef, expect(";"), poplex);if (type == "keyword a") return cont(pushlex("form"), expression, statement, poplex);if (type == "keyword b") return cont(pushlex("form"), statement, poplex);if (type == "{") return cont(pushlex("}"), block, poplex);if (type == ";") return cont();if (type == "if") return cont(pushlex("form"), expression, statement, poplex, maybeelse);if (type == "function") return cont(functiondef);if (type == "for") return cont(pushlex("form"), forspec, statement, poplex);if (type == "variable") return cont(pushlex("stat"), maybelabel);if (type == "switch") return cont(pushlex("form"), expression, pushlex("}", "switch"), expect("{"), block, poplex, poplex);if (type == "case") return cont(expression, expect(":"));if (type == "default") return cont(expect(":"));if (type == "catch") return cont(pushlex("form"), pushcontext, expect("("), funarg, expect(")"), statement, poplex, popcontext);if (type == "module") return cont(pushlex("form"), pushcontext, afterModule, popcontext, poplex);if (type == "class") return cont(pushlex("form"), className, objlit, poplex);if (type == "export") return cont(pushlex("form"), afterExport, poplex);if (type == "import") return cont(pushlex("form"), afterImport, poplex);return pass(pushlex("stat"), expression, expect(";"), poplex);
  }function expression(type) {
    return expressionInner(type, false);
  }function expressionNoComma(type) {
    return expressionInner(type, true);
  }function expressionInner(type, noComma) {
    if (cx.state.fatArrowAt == cx.stream.start) {
      var body = noComma ? arrowBodyNoComma : arrowBody;if (type == "(") return cont(pushcontext, pushlex(")"), commasep(pattern, ")"), poplex, expect("=>"), body, popcontext);else if (type == "variable") return pass(pushcontext, pattern, expect("=>"), body, popcontext);
    }var maybeop = noComma ? maybeoperatorNoComma : maybeoperatorComma;if (atomicTypes.hasOwnProperty(type)) return cont(maybeop);if (type == "function") return cont(functiondef);if (type == "keyword c") return cont(noComma ? maybeexpressionNoComma : maybeexpression);if (type == "(") return cont(pushlex(")"), maybeexpression, comprehension, expect(")"), poplex, maybeop);if (type == "operator" || type == "spread") return cont(noComma ? expressionNoComma : expression);if (type == "[") return cont(pushlex("]"), arrayLiteral, poplex, maybeop);if (type == "{") return contCommasep(objprop, "}", null, maybeop);return cont();
  }function maybeexpression(type) {
    if (type.match(/[;\}\)\],]/)) return pass();return pass(expression);
  }function maybeexpressionNoComma(type) {
    if (type.match(/[;\}\)\],]/)) return pass();return pass(expressionNoComma);
  }function maybeoperatorComma(type, value) {
    if (type == ",") return cont(expression);return maybeoperatorNoComma(type, value, false);
  }function maybeoperatorNoComma(type, value, noComma) {
    var me = noComma == false ? maybeoperatorComma : maybeoperatorNoComma;var expr = noComma == false ? expression : expressionNoComma;if (value == "=>") return cont(pushcontext, noComma ? arrowBodyNoComma : arrowBody, popcontext);if (type == "operator") {
      if (/\+\+|--/.test(value)) return cont(me);if (value == "?") return cont(expression, expect(":"), expr);return cont(expr);
    }if (type == "quasi") {
      cx.cc.push(me);return quasi(value);
    }if (type == ";") return;if (type == "(") return contCommasep(expressionNoComma, ")", "call", me);if (type == ".") return cont(property, me);if (type == "[") return cont(pushlex("]"), maybeexpression, expect("]"), poplex, me);
  }function quasi(value) {
    if (value.slice(value.length - 2) != "${") return cont();return cont(expression, continueQuasi);
  }function continueQuasi(type) {
    if (type == "}") {
      cx.marked = "string-2";cx.state.tokenize = tokenQuasi;return cont();
    }
  }function arrowBody(type) {
    findFatArrow(cx.stream, cx.state);if (type == "{") return pass(statement);return pass(expression);
  }function arrowBodyNoComma(type) {
    findFatArrow(cx.stream, cx.state);if (type == "{") return pass(statement);return pass(expressionNoComma);
  }function maybelabel(type) {
    if (type == ":") return cont(poplex, statement);return pass(maybeoperatorComma, expect(";"), poplex);
  }function property(type) {
    if (type == "variable") {
      cx.marked = "property";return cont();
    }
  }function objprop(type, value) {
    if (type == "variable") {
      cx.marked = "property";if (value == "get" || value == "set") return cont(getterSetter);
    } else if (type == "number" || type == "string") {
      cx.marked = type + " property";
    } else if (type == "[") {
      return cont(expression, expect("]"), afterprop);
    }if (atomicTypes.hasOwnProperty(type)) return cont(afterprop);
  }function getterSetter(type) {
    if (type != "variable") return pass(afterprop);cx.marked = "property";return cont(functiondef);
  }function afterprop(type) {
    if (type == ":") return cont(expressionNoComma);if (type == "(") return pass(functiondef);
  }function commasep(what, end) {
    function proceed(type) {
      if (type == ",") {
        var lex = cx.state.lexical;if (lex.info == "call") lex.pos = (lex.pos || 0) + 1;return cont(what, proceed);
      }if (type == end) return cont();return cont(expect(end));
    }return function (type) {
      if (type == end) return cont();return pass(what, proceed);
    };
  }function contCommasep(what, end, info) {
    for (var i = 3; i < arguments.length; i++) {
      cx.cc.push(arguments[i]);
    }return cont(pushlex(end, info), commasep(what, end), poplex);
  }function block(type) {
    if (type == "}") return cont();return pass(statement, block);
  }function maybetype(type) {
    if (isTS && type == ":") return cont(typedef);
  }function typedef(type) {
    if (type == "variable") {
      cx.marked = "variable-3";return cont();
    }
  }function vardef() {
    return pass(pattern, maybetype, maybeAssign, vardefCont);
  }function pattern(type, value) {
    if (type == "variable") {
      register(value);return cont();
    }if (type == "[") return contCommasep(pattern, "]");if (type == "{") return contCommasep(proppattern, "}");
  }function proppattern(type, value) {
    if (type == "variable" && !cx.stream.match(/^\s*:/, false)) {
      register(value);return cont(maybeAssign);
    }if (type == "variable") cx.marked = "property";return cont(expect(":"), pattern, maybeAssign);
  }function maybeAssign(_type, value) {
    if (value == "=") return cont(expressionNoComma);
  }function vardefCont(type) {
    if (type == ",") return cont(vardef);
  }function maybeelse(type, value) {
    if (type == "keyword b" && value == "else") return cont(pushlex("form"), statement, poplex);
  }function forspec(type) {
    if (type == "(") return cont(pushlex(")"), forspec1, expect(")"), poplex);
  }function forspec1(type) {
    if (type == "var") return cont(vardef, expect(";"), forspec2);if (type == ";") return cont(forspec2);if (type == "variable") return cont(formaybeinof);return pass(expression, expect(";"), forspec2);
  }function formaybeinof(_type, value) {
    if (value == "in" || value == "of") {
      cx.marked = "keyword";return cont(expression);
    }return cont(maybeoperatorComma, forspec2);
  }function forspec2(type, value) {
    if (type == ";") return cont(forspec3);if (value == "in" || value == "of") {
      cx.marked = "keyword";return cont(expression);
    }return pass(expression, expect(";"), forspec3);
  }function forspec3(type) {
    if (type != ")") cont(expression);
  }function functiondef(type, value) {
    if (value == "*") {
      cx.marked = "keyword";return cont(functiondef);
    }if (type == "variable") {
      register(value);return cont(functiondef);
    }if (type == "(") return cont(pushcontext, pushlex(")"), commasep(funarg, ")"), poplex, statement, popcontext);
  }function funarg(type) {
    if (type == "spread") return cont(funarg);return pass(pattern, maybetype);
  }function className(type, value) {
    if (type == "variable") {
      register(value);return cont(classNameAfter);
    }
  }function classNameAfter(_type, value) {
    if (value == "extends") return cont(expression);
  }function objlit(type) {
    if (type == "{") return contCommasep(objprop, "}");
  }function afterModule(type, value) {
    if (type == "string") return cont(statement);if (type == "variable") {
      register(value);return cont(maybeFrom);
    }
  }function afterExport(_type, value) {
    if (value == "*") {
      cx.marked = "keyword";return cont(maybeFrom, expect(";"));
    }if (value == "default") {
      cx.marked = "keyword";return cont(expression, expect(";"));
    }return pass(statement);
  }function afterImport(type) {
    if (type == "string") return cont();return pass(importSpec, maybeFrom);
  }function importSpec(type, value) {
    if (type == "{") return contCommasep(importSpec, "}");if (type == "variable") register(value);return cont();
  }function maybeFrom(_type, value) {
    if (value == "from") {
      cx.marked = "keyword";return cont(expression);
    }
  }function arrayLiteral(type) {
    if (type == "]") return cont();return pass(expressionNoComma, maybeArrayComprehension);
  }function maybeArrayComprehension(type) {
    if (type == "for") return pass(comprehension, expect("]"));if (type == ",") return cont(commasep(expressionNoComma, "]"));return pass(commasep(expressionNoComma, "]"));
  }function comprehension(type) {
    if (type == "for") return cont(forspec, comprehension);if (type == "if") return cont(expression, comprehension);
  }return { startState: function startState(basecolumn) {
      var state = { tokenize: tokenBase, lastType: "sof", cc: [], lexical: new JSLexical((basecolumn || 0) - indentUnit, 0, "block", false), localVars: parserConfig.localVars, context: parserConfig.localVars && { vars: parserConfig.localVars }, indented: 0 };if (parserConfig.globalVars) state.globalVars = parserConfig.globalVars;return state;
    }, token: function token(stream, state) {
      if (stream.sol()) {
        if (!state.lexical.hasOwnProperty("align")) state.lexical.align = false;state.indented = stream.indentation();findFatArrow(stream, state);
      }if (state.tokenize != tokenComment && stream.eatSpace()) return null;var style = state.tokenize(stream, state);if (type == "comment") return style;state.lastType = type == "operator" && (content == "++" || content == "--") ? "incdec" : type;return parseJS(state, style, type, content, stream);
    }, indent: function indent(state, textAfter) {
      if (state.tokenize == tokenComment) return CodeMirror.Pass;if (state.tokenize != tokenBase) return 0;var firstChar = textAfter && textAfter.charAt(0),
          lexical = state.lexical;for (var i = state.cc.length - 1; i >= 0; --i) {
        var c = state.cc[i];if (c == poplex) lexical = lexical.prev;else if (c != maybeelse) break;
      }if (lexical.type == "stat" && firstChar == "}") lexical = lexical.prev;if (statementIndent && lexical.type == ")" && lexical.prev.type == "stat") lexical = lexical.prev;var type = lexical.type,
          closing = firstChar == type;if (type == "vardef") return lexical.indented + (state.lastType == "operator" || state.lastType == "," ? lexical.info + 1 : 0);else if (type == "form" && firstChar == "{") return lexical.indented;else if (type == "form") return lexical.indented + indentUnit;else if (type == "stat") return lexical.indented + (state.lastType == "operator" || state.lastType == "," ? statementIndent || indentUnit : 0);else if (lexical.info == "switch" && !closing && parserConfig.doubleIndentSwitch != false) return lexical.indented + (/^(?:case|default)\b/.test(textAfter) ? indentUnit : 2 * indentUnit);else if (lexical.align) return lexical.column + (closing ? 0 : 1);else return lexical.indented + (closing ? 0 : indentUnit);
    }, electricChars: ":{}", blockCommentStart: jsonMode ? null : "/*", blockCommentEnd: jsonMode ? null : "*/", lineComment: jsonMode ? null : "//", fold: "brace", helperType: jsonMode ? "json" : "javascript", jsonMode: jsonMode };
});CodeMirror.defineMIME("text/javascript", "javascript");CodeMirror.defineMIME("text/ecmascript", "javascript");CodeMirror.defineMIME("application/javascript", "javascript");CodeMirror.defineMIME("application/ecmascript", "javascript");CodeMirror.defineMIME("application/json", { name: "javascript", json: true });CodeMirror.defineMIME("application/x-json", { name: "javascript", json: true });CodeMirror.defineMIME("text/typescript", { name: "javascript", typescript: true });CodeMirror.defineMIME("application/typescript", { name: "javascript", typescript: true });(function () {
  var DEFAULT_MIN_CHARS = 2;var DEFAULT_TOKEN_STYLE = "matchhighlight";var DEFAULT_DELAY = 100;function State(options) {
    if ((typeof options === "undefined" ? "undefined" : _typeof(options)) == "object") {
      this.minChars = options.minChars;this.style = options.style;this.showToken = options.showToken;this.delay = options.delay;
    }if (this.style == null) this.style = DEFAULT_TOKEN_STYLE;if (this.minChars == null) this.minChars = DEFAULT_MIN_CHARS;if (this.delay == null) this.delay = DEFAULT_DELAY;this.overlay = this.timeout = null;
  }CodeMirror.defineOption("highlightSelectionMatches", false, function (cm, val, old) {
    if (old && old != CodeMirror.Init) {
      var over = cm.state.matchHighlighter.overlay;if (over) cm.removeOverlay(over);clearTimeout(cm.state.matchHighlighter.timeout);cm.state.matchHighlighter = null;cm.off("cursorActivity", cursorActivity);
    }if (val) {
      cm.state.matchHighlighter = new State(val);highlightMatches(cm);cm.on("cursorActivity", cursorActivity);
    }
  });function cursorActivity(cm) {
    var state = cm.state.matchHighlighter;clearTimeout(state.timeout);state.timeout = setTimeout(function () {
      highlightMatches(cm);
    }, state.delay);
  }function highlightMatches(cm) {
    cm.operation(function () {
      var state = cm.state.matchHighlighter;if (state.overlay) {
        cm.removeOverlay(state.overlay);state.overlay = null;
      }if (!cm.somethingSelected() && state.showToken) {
        var re = state.showToken === true ? /[\w$]/ : state.showToken;var cur = cm.getCursor(),
            line = cm.getLine(cur.line),
            start = cur.ch,
            end = start;while (start && re.test(line.charAt(start - 1))) {
          --start;
        }while (end < line.length && re.test(line.charAt(end))) {
          ++end;
        }if (start < end) cm.addOverlay(state.overlay = makeOverlay(line.slice(start, end), re, state.style));return;
      }if (cm.getCursor("head").line != cm.getCursor("anchor").line) return;var selection = cm.getSelection().replace(/^\s+|\s+$/g, "");if (selection.length >= state.minChars) cm.addOverlay(state.overlay = makeOverlay(selection, false, state.style));
    });
  }function boundariesAround(stream, re) {
    return (!stream.start || !re.test(stream.string.charAt(stream.start - 1))) && (stream.pos == stream.string.length || !re.test(stream.string.charAt(stream.pos)));
  }function makeOverlay(query, hasBoundary, style) {
    return { token: function token(stream) {
        if (stream.match(query) && (!hasBoundary || boundariesAround(stream, hasBoundary))) return style;stream.next();stream.skipTo(query.charAt(0)) || stream.skipToEnd();
      } };
  }
})();CodeMirror.defineMode("python", function (conf, parserConf) {
  var ERRORCLASS = "error";function wordRegexp(words) {
    return new RegExp("^((" + words.join(")|(") + "))\\b");
  }var singleOperators = parserConf.singleOperators || new RegExp("^[\\+\\-\\*/%&|\\^~<>!]");var singleDelimiters = parserConf.singleDelimiters || new RegExp("^[\\(\\)\\[\\]\\{\\}@,:`=;\\.]");var doubleOperators = parserConf.doubleOperators || new RegExp("^((==)|(!=)|(<=)|(>=)|(<>)|(<<)|(>>)|(//)|(\\*\\*))");var doubleDelimiters = parserConf.doubleDelimiters || new RegExp("^((\\+=)|(\\-=)|(\\*=)|(%=)|(/=)|(&=)|(\\|=)|(\\^=))");var tripleDelimiters = parserConf.tripleDelimiters || new RegExp("^((//=)|(>>=)|(<<=)|(\\*\\*=))");var identifiers = parserConf.identifiers || new RegExp("^[_A-Za-z][_A-Za-z0-9]*");var hangingIndent = parserConf.hangingIndent || parserConf.indentUnit;
  var wordOperators = wordRegexp(["and", "or", "not", "is", "in"]);var commonkeywords = ["as", "assert", "break", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "lambda", "pass", "raise", "return", "try", "while", "with", "yield"];var commonBuiltins = ["abs", "all", "any", "bin", "bool", "bytearray", "callable", "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "eval", "filter", "float", "format", "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow", "property", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip", "__import__", "NotImplemented", "Ellipsis", "__debug__"];var py2 = { builtins: ["apply", "basestring", "buffer", "cmp", "coerce", "execfile", "file", "intern", "long", "raw_input", "reduce", "reload", "unichr", "unicode", "xrange", "False", "True", "None"], keywords: ["exec", "print"] };var py3 = { builtins: ["ascii", "bytes", "exec", "print"], keywords: ["nonlocal", "False", "True", "None"] };if (parserConf.extra_keywords != undefined) {
    commonkeywords = commonkeywords.concat(parserConf.extra_keywords);
  }if (parserConf.extra_builtins != undefined) {
    commonBuiltins = commonBuiltins.concat(parserConf.extra_builtins);
  }if (!!parserConf.version && parseInt(parserConf.version, 10) === 3) {
    commonkeywords = commonkeywords.concat(py3.keywords);commonBuiltins = commonBuiltins.concat(py3.builtins);var stringPrefixes = new RegExp("^(([rb]|(br))?('{3}|\"{3}|['\"]))", "i");
  } else {
    commonkeywords = commonkeywords.concat(py2.keywords);commonBuiltins = commonBuiltins.concat(py2.builtins);var stringPrefixes = new RegExp("^(([rub]|(ur)|(br))?('{3}|\"{3}|['\"]))", "i");
  }var keywords = wordRegexp(commonkeywords);var builtins = wordRegexp(commonBuiltins);var indentInfo = null;function tokenBase(stream, state) {
    if (stream.sol()) {
      var scopeOffset = state.scopes[0].offset;if (stream.eatSpace()) {
        var lineOffset = stream.indentation();if (lineOffset > scopeOffset) {
          indentInfo = "indent";
        } else if (lineOffset < scopeOffset) {
          indentInfo = "dedent";
        }return null;
      } else {
        if (scopeOffset > 0) {
          dedent(stream, state);
        }
      }
    }if (stream.eatSpace()) {
      return null;
    }var ch = stream.peek();if (ch === "#") {
      stream.skipToEnd();return "comment";
    }if (stream.match(/^[0-9\.]/, false)) {
      var floatLiteral = false;if (stream.match(/^\d*\.\d+(e[\+\-]?\d+)?/i)) {
        floatLiteral = true;
      }if (stream.match(/^\d+\.\d*/)) {
        floatLiteral = true;
      }if (stream.match(/^\.\d+/)) {
        floatLiteral = true;
      }if (floatLiteral) {
        stream.eat(/J/i);return "number";
      }var intLiteral = false;if (stream.match(/^0x[0-9a-f]+/i)) {
        intLiteral = true;
      }if (stream.match(/^0b[01]+/i)) {
        intLiteral = true;
      }if (stream.match(/^0o[0-7]+/i)) {
        intLiteral = true;
      }if (stream.match(/^[1-9]\d*(e[\+\-]?\d+)?/)) {
        stream.eat(/J/i);intLiteral = true;
      }if (stream.match(/^0(?![\dx])/i)) {
        intLiteral = true;
      }if (intLiteral) {
        stream.eat(/L/i);return "number";
      }
    }if (stream.match(stringPrefixes)) {
      state.tokenize = tokenStringFactory(stream.current());return state.tokenize(stream, state);
    }if (stream.match(tripleDelimiters) || stream.match(doubleDelimiters)) {
      return null;
    }if (stream.match(doubleOperators) || stream.match(singleOperators) || stream.match(wordOperators)) {
      return "operator";
    }if (stream.match(singleDelimiters)) {
      return null;
    }if (stream.match(keywords)) {
      return "keyword";
    }if (stream.match(builtins)) {
      return "builtin";
    }if (stream.match(identifiers)) {
      if (state.lastToken == "def" || state.lastToken == "class") {
        return "def";
      }return "variable";
    }stream.next();return ERRORCLASS;
  }function tokenStringFactory(delimiter) {
    while ("rub".indexOf(delimiter.charAt(0).toLowerCase()) >= 0) {
      delimiter = delimiter.substr(1);
    }var singleline = delimiter.length == 1;var OUTCLASS = "string";function tokenString(stream, state) {
      while (!stream.eol()) {
        stream.eatWhile(/[^'"\\]/);if (stream.eat("\\")) {
          stream.next();if (singleline && stream.eol()) {
            return OUTCLASS;
          }
        } else if (stream.match(delimiter)) {
          state.tokenize = tokenBase;return OUTCLASS;
        } else {
          stream.eat(/['"]/);
        }
      }if (singleline) {
        if (parserConf.singleLineStringErrors) {
          return ERRORCLASS;
        } else {
          state.tokenize = tokenBase;
        }
      }return OUTCLASS;
    }tokenString.isString = true;return tokenString;
  }function indent(stream, state, type) {
    type = type || "py";var indentUnit = 0;if (type === "py") {
      if (state.scopes[0].type !== "py") {
        state.scopes[0].offset = stream.indentation();return;
      }for (var i = 0; i < state.scopes.length; ++i) {
        if (state.scopes[i].type === "py") {
          indentUnit = state.scopes[i].offset + conf.indentUnit;break;
        }
      }
    } else if (stream.match(/\s*($|#)/, false)) {
      indentUnit = stream.indentation() + hangingIndent;
    } else {
      indentUnit = stream.column() + stream.current().length;
    }state.scopes.unshift({ offset: indentUnit, type: type });
  }function dedent(stream, state, type) {
    type = type || "py";if (state.scopes.length == 1) return;if (state.scopes[0].type === "py") {
      var _indent = stream.indentation();var _indent_index = -1;for (var i = 0; i < state.scopes.length; ++i) {
        if (_indent === state.scopes[i].offset) {
          _indent_index = i;break;
        }
      }if (_indent_index === -1) {
        return true;
      }while (state.scopes[0].offset !== _indent) {
        state.scopes.shift();
      }return false;
    } else {
      if (type === "py") {
        state.scopes[0].offset = stream.indentation();return false;
      } else {
        if (state.scopes[0].type != type) {
          return true;
        }state.scopes.shift();return false;
      }
    }
  }function tokenLexer(stream, state) {
    indentInfo = null;var style = state.tokenize(stream, state);var current = stream.current();if (current === ".") {
      style = stream.match(identifiers, false) ? null : ERRORCLASS;if (style === null && state.lastStyle === "meta") {
        style = "meta";
      }return style;
    }if (current === "@") {
      return stream.match(identifiers, false) ? "meta" : ERRORCLASS;
    }if ((style === "variable" || style === "builtin") && state.lastStyle === "meta") {
      style = "meta";
    }if (current === "pass" || current === "return") {
      state.dedent += 1;
    }if (current === "lambda") state.lambda = true;if (current === ":" && !state.lambda && state.scopes[0].type == "py" || indentInfo === "indent") {
      indent(stream, state);
    }var delimiter_index = "[({".indexOf(current);if (delimiter_index !== -1) {
      indent(stream, state, "])}".slice(delimiter_index, delimiter_index + 1));
    }if (indentInfo === "dedent") {
      if (dedent(stream, state)) {
        return ERRORCLASS;
      }
    }delimiter_index = "])}".indexOf(current);if (delimiter_index !== -1) {
      if (dedent(stream, state, current)) {
        return ERRORCLASS;
      }
    }if (state.dedent > 0 && stream.eol() && state.scopes[0].type == "py") {
      if (state.scopes.length > 1) state.scopes.shift();state.dedent -= 1;
    }return style;
  }var external = { startState: function startState(basecolumn) {
      return { tokenize: tokenBase, scopes: [{ offset: basecolumn || 0, type: "py" }], lastStyle: null, lastToken: null, lambda: false, dedent: 0 };
    }, token: function token(stream, state) {
      var style = tokenLexer(stream, state);state.lastStyle = style;var current = stream.current();if (current && style) {
        state.lastToken = current;
      }if (stream.eol() && state.lambda) {
        state.lambda = false;
      }return style;
    }, indent: function indent(state) {
      if (state.tokenize != tokenBase) {
        return state.tokenize.isString ? CodeMirror.Pass : 0;
      }return state.scopes[0].offset;
    }, lineComment: "#", fold: "indent" };return external;
});CodeMirror.defineMIME("text/x-python", "python");(function () {
  "use strict";
  var words = function words(str) {
    return str.split(" ");
  };CodeMirror.defineMIME("text/x-cython", { name: "python", extra_keywords: words("by cdef cimport cpdef ctypedef enum except" + "extern gil include nogil property public" + "readonly struct union DEF IF ELIF ELSE") });
})();(function () {
  var Pos = CodeMirror.Pos;function SearchCursor(doc, query, pos, caseFold) {
    this.atOccurrence = false;this.doc = doc;if (caseFold == null && typeof query == "string") caseFold = false;pos = pos ? doc.clipPos(pos) : Pos(0, 0);this.pos = { from: pos, to: pos };if (typeof query != "string") {
      if (!query.global) query = new RegExp(query.source, query.ignoreCase ? "ig" : "g");this.matches = function (reverse, pos) {
        if (reverse) {
          query.lastIndex = 0;var line = doc.getLine(pos.line).slice(0, pos.ch),
              cutOff = 0,
              match,
              start;for (;;) {
            query.lastIndex = cutOff;var newMatch = query.exec(line);if (!newMatch) break;match = newMatch;start = match.index;cutOff = match.index + (match[0].length || 1);if (cutOff == line.length) break;
          }var matchLen = match && match[0].length || 0;if (!matchLen) {
            if (start == 0 && line.length == 0) {
              match = undefined;
            } else if (start != doc.getLine(pos.line).length) {
              matchLen++;
            }
          }
        } else {
          query.lastIndex = pos.ch;var line = doc.getLine(pos.line),
              match = query.exec(line);var matchLen = match && match[0].length || 0;var start = match && match.index;if (start + matchLen != line.length && !matchLen) matchLen = 1;
        }if (match && matchLen) return { from: Pos(pos.line, start), to: Pos(pos.line, start + matchLen), match: match };
      };
    } else {
      var origQuery = query;if (caseFold) query = query.toLowerCase();var fold = caseFold ? function (str) {
        return str.toLowerCase();
      } : function (str) {
        return str;
      };var target = query.split("\n");if (target.length == 1) {
        if (!query.length) {
          this.matches = function () {};
        } else {
          this.matches = function (reverse, pos) {
            if (reverse) {
              var orig = doc.getLine(pos.line).slice(0, pos.ch),
                  line = fold(orig);var match = line.lastIndexOf(query);if (match > -1) {
                match = adjustPos(orig, line, match);return { from: Pos(pos.line, match), to: Pos(pos.line, match + origQuery.length) };
              }
            } else {
              var orig = doc.getLine(pos.line).slice(pos.ch),
                  line = fold(orig);var match = line.indexOf(query);if (match > -1) {
                match = adjustPos(orig, line, match) + pos.ch;return { from: Pos(pos.line, match), to: Pos(pos.line, match + origQuery.length) };
              }
            }
          };
        }
      } else {
        var origTarget = origQuery.split("\n");this.matches = function (reverse, pos) {
          var last = target.length - 1;if (reverse) {
            if (pos.line - (target.length - 1) < doc.firstLine()) return;if (fold(doc.getLine(pos.line).slice(0, origTarget[last].length)) != target[target.length - 1]) return;var to = Pos(pos.line, origTarget[last].length);for (var ln = pos.line - 1, i = last - 1; i >= 1; --i, --ln) {
              if (target[i] != fold(doc.getLine(ln))) return;
            }var line = doc.getLine(ln),
                cut = line.length - origTarget[0].length;if (fold(line.slice(cut)) != target[0]) return;return { from: Pos(ln, cut), to: to };
          } else {
            if (pos.line + (target.length - 1) > doc.lastLine()) return;var line = doc.getLine(pos.line),
                cut = line.length - origTarget[0].length;if (fold(line.slice(cut)) != target[0]) return;var from = Pos(pos.line, cut);for (var ln = pos.line + 1, i = 1; i < last; ++i, ++ln) {
              if (target[i] != fold(doc.getLine(ln))) return;
            }if (doc.getLine(ln).slice(0, origTarget[last].length) != target[last]) return;return { from: from, to: Pos(ln, origTarget[last].length) };
          }
        };
      }
    }
  }SearchCursor.prototype = { findNext: function findNext() {
      return this.find(false);
    }, findPrevious: function findPrevious() {
      return this.find(true);
    }, find: function find(reverse) {
      var self = this,
          pos = this.doc.clipPos(reverse ? this.pos.from : this.pos.to);function savePosAndFail(line) {
        var pos = Pos(line, 0);self.pos = { from: pos, to: pos };self.atOccurrence = false;return false;
      }for (;;) {
        if (this.pos = this.matches(reverse, pos)) {
          this.atOccurrence = true;return this.pos.match || true;
        }if (reverse) {
          if (!pos.line) return savePosAndFail(0);pos = Pos(pos.line - 1, this.doc.getLine(pos.line - 1).length);
        } else {
          var maxLine = this.doc.lineCount();if (pos.line == maxLine - 1) return savePosAndFail(maxLine);pos = Pos(pos.line + 1, 0);
        }
      }
    }, from: function from() {
      if (this.atOccurrence) return this.pos.from;
    }, to: function to() {
      if (this.atOccurrence) return this.pos.to;
    }, replace: function replace(newText) {
      if (!this.atOccurrence) return;var lines = CodeMirror.splitLines(newText);this.doc.replaceRange(lines, this.pos.from, this.pos.to);this.pos.to = Pos(this.pos.from.line + lines.length - 1, lines[lines.length - 1].length + (lines.length == 1 ? this.pos.from.ch : 0));
    } };function adjustPos(orig, folded, pos) {
    if (orig.length == folded.length) return pos;for (var pos1 = Math.min(pos, orig.length);;) {
      var len1 = orig.slice(0, pos1).toLowerCase().length;if (len1 < pos) ++pos1;else if (len1 > pos) --pos1;else return pos1;
    }
  }CodeMirror.defineExtension("getSearchCursor", function (query, pos, caseFold) {
    return new SearchCursor(this.doc, query, pos, caseFold);
  });CodeMirror.defineDocExtension("getSearchCursor", function (query, pos, caseFold) {
    return new SearchCursor(this, query, pos, caseFold);
  });
})();(function () {
  function searchOverlay(query, caseInsensitive) {
    var startChar;if (typeof query == "string") {
      startChar = query.charAt(0);query = new RegExp("^" + query.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&"), caseInsensitive ? "i" : "");
    } else {
      query = new RegExp("^(?:" + query.source + ")", query.ignoreCase ? "i" : "");
    }if (typeof query == "string") return { token: function token(stream) {
        if (stream.match(query)) return "searching";stream.next();stream.skipTo(query.charAt(0)) || stream.skipToEnd();
      } };return { token: function token(stream) {
        if (stream.match(query)) return "searching";while (!stream.eol()) {
          stream.next();if (startChar) stream.skipTo(startChar) || stream.skipToEnd();if (stream.match(query, false)) break;
        }
      } };
  }function SearchState() {
    this.posFrom = this.posTo = this.query = null;this.overlay = null;
  }function getSearchState(cm) {
    return cm.state.search || (cm.state.search = new SearchState());
  }function queryCaseInsensitive(query) {
    return typeof query == "string" && query == query.toLowerCase();
  }function getSearchCursor(cm, query, pos) {
    return cm.getSearchCursor(query, pos, queryCaseInsensitive(query));
  }function dialog(cm, text, shortText, deflt, f) {
    if (cm.openDialog) cm.openDialog(text, f, { value: deflt });else f(prompt(shortText, deflt));
  }function confirmDialog(cm, text, shortText, fs) {
    if (cm.openConfirm) cm.openConfirm(text, fs);else if (confirm(shortText)) fs[0]();
  }function parseQuery(query) {
    var isRE = query.match(/^\/(.*)\/([a-z]*)$/);return isRE ? new RegExp(isRE[1], isRE[2].indexOf("i") == -1 ? "" : "i") : query;
  }var queryDialog = 'Search: <input type="text" style="width: 10em"/> <span style="color: #888">(Use /re/ syntax for regexp search)</span>';function doSearch(cm, rev) {
    var state = getSearchState(cm);if (state.query) return findNext(cm, rev);dialog(cm, queryDialog, "Search for:", cm.getSelection(), function (query) {
      cm.operation(function () {
        if (!query || state.query) return;state.query = parseQuery(query);cm.removeOverlay(state.overlay, queryCaseInsensitive(state.query));state.overlay = searchOverlay(state.query);cm.addOverlay(state.overlay);state.posFrom = state.posTo = cm.getCursor();findNext(cm, rev);
      });
    });
  }function findNext(cm, rev) {
    cm.operation(function () {
      var state = getSearchState(cm);var cursor = getSearchCursor(cm, state.query, rev ? state.posFrom : state.posTo);if (!cursor.find(rev)) {
        cursor = getSearchCursor(cm, state.query, rev ? CodeMirror.Pos(cm.lastLine()) : CodeMirror.Pos(cm.firstLine(), 0));if (!cursor.find(rev)) return;
      }cm.setSelection(cursor.from(), cursor.to());cm.scrollIntoView({ from: cursor.from(), to: cursor.to() });state.posFrom = cursor.from();state.posTo = cursor.to();
    });
  }function clearSearch(cm) {
    cm.operation(function () {
      var state = getSearchState(cm);if (!state.query) return;state.query = null;cm.removeOverlay(state.overlay);
    });
  }var replaceQueryDialog = 'Replace: <input type="text" style="width: 10em"/> <span style="color: #888">(Use /re/ syntax for regexp search)</span>';var replacementQueryDialog = 'With: <input type="text" style="width: 10em"/>';var doReplaceConfirm = "Replace? <button>Yes</button> <button>No</button> <button>Stop</button>";function replace(cm, all) {
    dialog(cm, replaceQueryDialog, "Replace:", cm.getSelection(), function (query) {
      if (!query) return;query = parseQuery(query);dialog(cm, replacementQueryDialog, "Replace with:", "", function (text) {
        if (all) {
          cm.operation(function () {
            for (var cursor = getSearchCursor(cm, query); cursor.findNext();) {
              if (typeof query != "string") {
                var match = cm.getRange(cursor.from(), cursor.to()).match(query);cursor.replace(text.replace(/\$(\d)/, function (_, i) {
                  return match[i];
                }));
              } else cursor.replace(text);
            }
          });
        } else {
          clearSearch(cm);var cursor = getSearchCursor(cm, query, cm.getCursor());var advance = function advance() {
            var start = cursor.from(),
                match;if (!(match = cursor.findNext())) {
              cursor = getSearchCursor(cm, query);if (!(match = cursor.findNext()) || start && cursor.from().line == start.line && cursor.from().ch == start.ch) return;
            }cm.setSelection(cursor.from(), cursor.to());cm.scrollIntoView({ from: cursor.from(), to: cursor.to() });confirmDialog(cm, doReplaceConfirm, "Replace?", [function () {
              doReplace(match);
            }, advance]);
          };var doReplace = function doReplace(match) {
            cursor.replace(typeof query == "string" ? text : text.replace(/\$(\d)/, function (_, i) {
              return match[i];
            }));advance();
          };advance();
        }
      });
    });
  }CodeMirror.commands.find = function (cm) {
    clearSearch(cm);doSearch(cm);
  };CodeMirror.commands.findNext = doSearch;CodeMirror.commands.findPrev = function (cm) {
    doSearch(cm, true);
  };CodeMirror.commands.clearSearch = clearSearch;CodeMirror.commands.replace = replace;CodeMirror.commands.replaceAll = function (cm) {
    replace(cm, true);
  };
})();CodeMirror.defineMode("xml", function (config, parserConfig) {
  var indentUnit = config.indentUnit;var multilineTagIndentFactor = parserConfig.multilineTagIndentFactor || 1;var multilineTagIndentPastTag = parserConfig.multilineTagIndentPastTag || true;var Kludges = parserConfig.htmlMode ? { autoSelfClosers: { area: true, base: true, br: true, col: true, command: true, embed: true, frame: true, hr: true, img: true, input: true, keygen: true, link: true, meta: true, param: true, source: true, track: true, wbr: true }, implicitlyClosed: { dd: true, li: true, optgroup: true, option: true, p: true, rp: true, rt: true, tbody: true, td: true, tfoot: true, th: true, tr: true }, contextGrabbers: { dd: { dd: true, dt: true }, dt: { dd: true, dt: true }, li: { li: true }, option: { option: true, optgroup: true }, optgroup: { optgroup: true }, p: { address: true, article: true, aside: true, blockquote: true, dir: true, div: true, dl: true, fieldset: true, footer: true, form: true, h1: true, h2: true, h3: true, h4: true, h5: true, h6: true, header: true, hgroup: true, hr: true, menu: true, nav: true, ol: true, p: true, pre: true, section: true, table: true, ul: true }, rp: { rp: true, rt: true }, rt: { rp: true, rt: true }, tbody: { tbody: true, tfoot: true }, td: { td: true, th: true }, tfoot: { tbody: true }, th: { td: true, th: true }, thead: { tbody: true, tfoot: true }, tr: { tr: true } }, doNotIndent: { pre: true }, allowUnquoted: true, allowMissing: true } : { autoSelfClosers: {}, implicitlyClosed: {}, contextGrabbers: {}, doNotIndent: {}, allowUnquoted: false, allowMissing: false };var alignCDATA = parserConfig.alignCDATA;var tagName, type, setStyle;function inText(stream, state) {
    function chain(parser) {
      state.tokenize = parser;return parser(stream, state);
    }var ch = stream.next();if (ch == "<") {
      if (stream.eat("!")) {
        if (stream.eat("[")) {
          if (stream.match("CDATA[")) return chain(inBlock("atom", "]]>"));else return null;
        } else if (stream.match("--")) {
          return chain(inBlock("comment", "-->"));
        } else if (stream.match("DOCTYPE", true, true)) {
          stream.eatWhile(/[\w\._\-]/);return chain(doctype(1));
        } else {
          return null;
        }
      } else if (stream.eat("?")) {
        stream.eatWhile(/[\w\._\-]/);state.tokenize = inBlock("meta", "?>");return "meta";
      } else {
        var isClose = stream.eat("/");tagName = "";var c;while (c = stream.eat(/[^\s\u00a0=<>\"\'\/?]/)) {
          tagName += c;
        }if (!tagName) return "tag error";type = isClose ? "closeTag" : "openTag";state.tokenize = inTag;return "tag";
      }
    } else if (ch == "&") {
      var ok;if (stream.eat("#")) {
        if (stream.eat("x")) {
          ok = stream.eatWhile(/[a-fA-F\d]/) && stream.eat(";");
        } else {
          ok = stream.eatWhile(/[\d]/) && stream.eat(";");
        }
      } else {
        ok = stream.eatWhile(/[\w\.\-:]/) && stream.eat(";");
      }return ok ? "atom" : "error";
    } else {
      stream.eatWhile(/[^&<]/);return null;
    }
  }function inTag(stream, state) {
    var ch = stream.next();if (ch == ">" || ch == "/" && stream.eat(">")) {
      state.tokenize = inText;type = ch == ">" ? "endTag" : "selfcloseTag";return "tag";
    } else if (ch == "=") {
      type = "equals";return null;
    } else if (ch == "<") {
      state.tokenize = inText;state.state = baseState;state.tagName = state.tagStart = null;var next = state.tokenize(stream, state);return next ? next + " error" : "error";
    } else if (/[\'\"]/.test(ch)) {
      state.tokenize = inAttribute(ch);state.stringStartCol = stream.column();return state.tokenize(stream, state);
    } else {
      stream.eatWhile(/[^\s\u00a0=<>\"\']/);return "word";
    }
  }function inAttribute(quote) {
    var closure = function closure(stream, state) {
      while (!stream.eol()) {
        if (stream.next() == quote) {
          state.tokenize = inTag;break;
        }
      }return "string";
    };closure.isInAttribute = true;return closure;
  }function inBlock(style, terminator) {
    return function (stream, state) {
      while (!stream.eol()) {
        if (stream.match(terminator)) {
          state.tokenize = inText;break;
        }stream.next();
      }return style;
    };
  }function doctype(depth) {
    return function (stream, state) {
      var ch;while ((ch = stream.next()) != null) {
        if (ch == "<") {
          state.tokenize = doctype(depth + 1);return state.tokenize(stream, state);
        } else if (ch == ">") {
          if (depth == 1) {
            state.tokenize = inText;break;
          } else {
            state.tokenize = doctype(depth - 1);return state.tokenize(stream, state);
          }
        }
      }return "meta";
    };
  }function Context(state, tagName, startOfLine) {
    this.prev = state.context;this.tagName = tagName;this.indent = state.indented;this.startOfLine = startOfLine;if (Kludges.doNotIndent.hasOwnProperty(tagName) || state.context && state.context.noIndent) this.noIndent = true;
  }function popContext(state) {
    if (state.context) state.context = state.context.prev;
  }function maybePopContext(state, nextTagName) {
    var parentTagName;while (true) {
      if (!state.context) {
        return;
      }parentTagName = state.context.tagName.toLowerCase();if (!Kludges.contextGrabbers.hasOwnProperty(parentTagName) || !Kludges.contextGrabbers[parentTagName].hasOwnProperty(nextTagName)) {
        return;
      }popContext(state);
    }
  }function baseState(type, stream, state) {
    if (type == "openTag") {
      state.tagName = tagName;state.tagStart = stream.column();return attrState;
    } else if (type == "closeTag") {
      var err = false;if (state.context) {
        if (state.context.tagName != tagName) {
          if (Kludges.implicitlyClosed.hasOwnProperty(state.context.tagName.toLowerCase())) popContext(state);err = !state.context || state.context.tagName != tagName;
        }
      } else {
        err = true;
      }if (err) setStyle = "error";return err ? closeStateErr : closeState;
    } else {
      return baseState;
    }
  }function closeState(type, _stream, state) {
    if (type != "endTag") {
      setStyle = "error";return closeState;
    }popContext(state);return baseState;
  }function closeStateErr(type, stream, state) {
    setStyle = "error";return closeState(type, stream, state);
  }function attrState(type, _stream, state) {
    if (type == "word") {
      setStyle = "attribute";return attrEqState;
    } else if (type == "endTag" || type == "selfcloseTag") {
      var tagName = state.tagName,
          tagStart = state.tagStart;state.tagName = state.tagStart = null;if (type == "selfcloseTag" || Kludges.autoSelfClosers.hasOwnProperty(tagName.toLowerCase())) {
        maybePopContext(state, tagName.toLowerCase());
      } else {
        maybePopContext(state, tagName.toLowerCase());state.context = new Context(state, tagName, tagStart == state.indented);
      }return baseState;
    }setStyle = "error";return attrState;
  }function attrEqState(type, stream, state) {
    if (type == "equals") return attrValueState;if (!Kludges.allowMissing) setStyle = "error";return attrState(type, stream, state);
  }function attrValueState(type, stream, state) {
    if (type == "string") return attrContinuedState;if (type == "word" && Kludges.allowUnquoted) {
      setStyle = "string";return attrState;
    }setStyle = "error";return attrState(type, stream, state);
  }function attrContinuedState(type, stream, state) {
    if (type == "string") return attrContinuedState;return attrState(type, stream, state);
  }return { startState: function startState() {
      return { tokenize: inText, state: baseState, indented: 0, tagName: null, tagStart: null, context: null };
    }, token: function token(stream, state) {
      if (!state.tagName && stream.sol()) state.indented = stream.indentation();if (stream.eatSpace()) return null;tagName = type = null;var style = state.tokenize(stream, state);if ((style || type) && style != "comment") {
        setStyle = null;state.state = state.state(type || style, stream, state);if (setStyle) style = setStyle == "error" ? style + " error" : setStyle;
      }return style;
    }, indent: function indent(state, textAfter, fullLine) {
      var context = state.context;if (state.tokenize.isInAttribute) {
        return state.stringStartCol + 1;
      }if (context && context.noIndent) return CodeMirror.Pass;if (state.tokenize != inTag && state.tokenize != inText) return fullLine ? fullLine.match(/^(\s*)/)[0].length : 0;if (state.tagName) {
        if (multilineTagIndentPastTag) return state.tagStart + state.tagName.length + 2;else return state.tagStart + indentUnit * multilineTagIndentFactor;
      }if (alignCDATA && /<!\[CDATA\[/.test(textAfter)) return 0;if (context && /^<\//.test(textAfter)) context = context.prev;while (context && !context.startOfLine) {
        context = context.prev;
      }if (context) return context.indent + indentUnit;else return 0;
    }, electricChars: "/", blockCommentStart: "<!--", blockCommentEnd: "-->", configuration: parserConfig.htmlMode ? "html" : "xml", helperType: parserConfig.htmlMode ? "html" : "xml" };
});CodeMirror.defineMIME("text/xml", "xml");CodeMirror.defineMIME("application/xml", "xml");if (!CodeMirror.mimeModes.hasOwnProperty("text/html")) CodeMirror.defineMIME("text/html", { name: "xml", htmlMode: true });CodeMirror.defineMode("yaml", function () {
  var cons = ["true", "false", "on", "off", "yes", "no"];var keywordRegex = new RegExp("\\b((" + cons.join(")|(") + "))$", "i");return { token: function token(stream, state) {
      var ch = stream.peek();var esc = state.escaped;state.escaped = false;if (ch == "#" && (stream.pos == 0 || /\s/.test(stream.string.charAt(stream.pos - 1)))) {
        stream.skipToEnd();return "comment";
      }if (state.literal && stream.indentation() > state.keyCol) {
        stream.skipToEnd();return "string";
      } else if (state.literal) {
        state.literal = false;
      }if (stream.sol()) {
        state.keyCol = 0;state.pair = false;state.pairStart = false;if (stream.match(/---/)) {
          return "def";
        }if (stream.match(/\.\.\./)) {
          return "def";
        }if (stream.match(/\s*-\s+/)) {
          return "meta";
        }
      }if (stream.match(/^(\{|\}|\[|\])/)) {
        if (ch == "{") state.inlinePairs++;else if (ch == "}") state.inlinePairs--;else if (ch == "[") state.inlineList++;else state.inlineList--;return "meta";
      }if (state.inlineList > 0 && !esc && ch == ",") {
        stream.next();return "meta";
      }if (state.inlinePairs > 0 && !esc && ch == ",") {
        state.keyCol = 0;state.pair = false;state.pairStart = false;stream.next();return "meta";
      }if (state.pairStart) {
        if (stream.match(/^\s*(\||\>)\s*/)) {
          state.literal = true;return "meta";
        }if (stream.match(/^\s*(\&|\*)[a-z0-9\._-]+\b/i)) {
          return "variable-2";
        }if (state.inlinePairs == 0 && stream.match(/^\s*-?[0-9\.\,]+\s?$/)) {
          return "number";
        }if (state.inlinePairs > 0 && stream.match(/^\s*-?[0-9\.\,]+\s?(?=(,|}))/)) {
          return "number";
        }if (stream.match(keywordRegex)) {
          return "keyword";
        }
      }if (!state.pair && stream.match(/^\s*\S+(?=\s*:($|\s))/i)) {
        state.pair = true;state.keyCol = stream.indentation();return "atom";
      }if (state.pair && stream.match(/^:\s*/)) {
        state.pairStart = true;return "meta";
      }state.pairStart = false;state.escaped = ch == "\\";stream.next();return null;
    }, startState: function startState() {
      return { pair: false, pairStart: false, keyCol: 0, inlinePairs: 0, inlineList: 0, literal: false, escaped: false };
    } };
});CodeMirror.defineMIME("text/x-yaml", "yaml");(function () {
  function dialogDiv(cm, template, bottom) {
    var wrap = cm.getWrapperElement();var dialog;dialog = wrap.appendChild(document.createElement("div"));if (bottom) {
      dialog.className = "CodeMirror-dialog CodeMirror-dialog-bottom";
    } else {
      dialog.className = "CodeMirror-dialog CodeMirror-dialog-top";
    }if (typeof template == "string") {
      dialog.innerHTML = template;
    } else {
      dialog.appendChild(template);
    }return dialog;
  }function closeNotification(cm, newVal) {
    if (cm.state.currentNotificationClose) cm.state.currentNotificationClose();cm.state.currentNotificationClose = newVal;
  }CodeMirror.defineExtension("openDialog", function (template, callback, options) {
    closeNotification(this, null);var dialog = dialogDiv(this, template, options && options.bottom);var closed = false,
        me = this;function close() {
      if (closed) return;closed = true;dialog.parentNode.removeChild(dialog);
    }var inp = dialog.getElementsByTagName("input")[0],
        button;if (inp) {
      if (options && options.value) inp.value = options.value;CodeMirror.on(inp, "keydown", function (e) {
        if (options && options.onKeyDown && options.onKeyDown(e, inp.value, close)) {
          return;
        }if (e.keyCode == 13 || e.keyCode == 27) {
          CodeMirror.e_stop(e);close();me.focus();if (e.keyCode == 13) callback(inp.value);
        }
      });if (options && options.onKeyUp) {
        CodeMirror.on(inp, "keyup", function (e) {
          options.onKeyUp(e, inp.value, close);
        });
      }if (options && options.value) inp.value = options.value;inp.focus();CodeMirror.on(inp, "blur", close);
    } else if (button = dialog.getElementsByTagName("button")[0]) {
      CodeMirror.on(button, "click", function () {
        close();me.focus();
      });button.focus();CodeMirror.on(button, "blur", close);
    }return close;
  });CodeMirror.defineExtension("openConfirm", function (template, callbacks, options) {
    closeNotification(this, null);var dialog = dialogDiv(this, template, options && options.bottom);var buttons = dialog.getElementsByTagName("button");var closed = false,
        me = this,
        blurring = 1;function close() {
      if (closed) return;closed = true;dialog.parentNode.removeChild(dialog);me.focus();
    }buttons[0].focus();for (var i = 0; i < buttons.length; ++i) {
      var b = buttons[i];(function (callback) {
        CodeMirror.on(b, "click", function (e) {
          CodeMirror.e_preventDefault(e);close();if (callback) callback(me);
        });
      })(callbacks[i]);CodeMirror.on(b, "blur", function () {
        --blurring;setTimeout(function () {
          if (blurring <= 0) close();
        }, 200);
      });CodeMirror.on(b, "focus", function () {
        ++blurring;
      });
    }
  });CodeMirror.defineExtension("openNotification", function (template, options) {
    closeNotification(this, close);var dialog = dialogDiv(this, template, options && options.bottom);var duration = options && (options.duration === undefined ? 5e3 : options.duration);var closed = false,
        doneTimer;function close() {
      if (closed) return;closed = true;clearTimeout(doneTimer);dialog.parentNode.removeChild(dialog);
    }CodeMirror.on(dialog, "click", function (e) {
      CodeMirror.e_preventDefault(e);close();
    });if (duration) doneTimer = setTimeout(close, options.duration);
  });
})();

/*** EXPORTS FROM exports-loader ***/
module.exports = window.CodeMirror;

/***/ }),

/***/ "./common/static/xmodule/descriptors/js/000-b82f6c436159f6bc7ca2513e29e82503.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(_, $) {/*** IMPORTS FROM imports-loader ***/
(function () {

    (function () {
        'use strict';

        var XModule = {};

        XModule.Descriptor = function () {
            /*
             * Bind the module to an element. This may be called multiple times,
             * if the element content has changed and so the module needs to be rebound
             *
             * @method: constructor
             * @param {html element} the .xmodule_edit section containing all of the descriptor content
             */
            var Descriptor = function Descriptor(element) {
                this.element = element;
                this.update = _.bind(this.update, this);
            };

            /*
             * Register a callback method to be called when the state of this
             * descriptor is updated. The callback will be passed the results
             * of calling the save method on this descriptor.
             */
            Descriptor.prototype.onUpdate = function (callback) {
                if (!this.callbacks) {
                    this.callbacks = [];
                }

                this.callbacks.push(callback);
            };

            /*
             * Notify registered callbacks that the state of this descriptor has changed
             */
            Descriptor.prototype.update = function () {
                var data, callbacks, i, length;

                data = this.save();
                callbacks = this.callbacks;
                length = callbacks.length;

                $.each(callbacks, function (index, callback) {
                    callback(data);
                });
            };

            /*
             * Return the current state of the descriptor (to be written to the module store)
             *
             * @method: save
             * @returns {object} An object containing children and data attributes (both optional).
             *                   The contents of the attributes will be saved to the server
             */
            Descriptor.prototype.save = function () {
                return {};
            };

            return Descriptor;
        }();

        this.XBlockToXModuleShim = function (runtime, element, initArgs) {
            /*
             * Load a single module (either an edit module or a display module)
             * from the supplied element, which should have a data-type attribute
             * specifying the class to load
             */
            var moduleType, module;

            if (initArgs) {
                moduleType = initArgs['xmodule-type'];
            }
            if (!moduleType) {
                moduleType = $(element).data('type');
            }

            if (moduleType === 'None') {
                return;
            }

            try {
                module = new window[moduleType](element, runtime);

                if ($(element).hasClass('xmodule_edit')) {
                    $(document).trigger('XModule.loaded.edit', [element, module]);
                }

                if ($(element).hasClass('xmodule_display')) {
                    $(document).trigger('XModule.loaded.display', [element, module]);
                }

                return module;
            } catch (error) {
                console.error('Unable to load ' + moduleType + ': ' + error.message);
            }
        };

        // Export this module. We do it at the end when everything is ready
        // because some RequireJS scripts require this module. If
        // `window.XModule` appears as defined before this file has a chance
        // to execute fully, then there is a chance that RequireJS will execute
        // some script prematurely.
        this.XModule = XModule;
    }).call(this);
}).call(window);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1), __webpack_require__(0)))

/***/ }),

/***/ "./common/static/xmodule/modules/js/000-b82f6c436159f6bc7ca2513e29e82503.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(_, $) {/*** IMPORTS FROM imports-loader ***/
(function () {

    (function () {
        'use strict';

        var XModule = {};

        XModule.Descriptor = function () {
            /*
             * Bind the module to an element. This may be called multiple times,
             * if the element content has changed and so the module needs to be rebound
             *
             * @method: constructor
             * @param {html element} the .xmodule_edit section containing all of the descriptor content
             */
            var Descriptor = function Descriptor(element) {
                this.element = element;
                this.update = _.bind(this.update, this);
            };

            /*
             * Register a callback method to be called when the state of this
             * descriptor is updated. The callback will be passed the results
             * of calling the save method on this descriptor.
             */
            Descriptor.prototype.onUpdate = function (callback) {
                if (!this.callbacks) {
                    this.callbacks = [];
                }

                this.callbacks.push(callback);
            };

            /*
             * Notify registered callbacks that the state of this descriptor has changed
             */
            Descriptor.prototype.update = function () {
                var data, callbacks, i, length;

                data = this.save();
                callbacks = this.callbacks;
                length = callbacks.length;

                $.each(callbacks, function (index, callback) {
                    callback(data);
                });
            };

            /*
             * Return the current state of the descriptor (to be written to the module store)
             *
             * @method: save
             * @returns {object} An object containing children and data attributes (both optional).
             *                   The contents of the attributes will be saved to the server
             */
            Descriptor.prototype.save = function () {
                return {};
            };

            return Descriptor;
        }();

        this.XBlockToXModuleShim = function (runtime, element, initArgs) {
            /*
             * Load a single module (either an edit module or a display module)
             * from the supplied element, which should have a data-type attribute
             * specifying the class to load
             */
            var moduleType, module;

            if (initArgs) {
                moduleType = initArgs['xmodule-type'];
            }
            if (!moduleType) {
                moduleType = $(element).data('type');
            }

            if (moduleType === 'None') {
                return;
            }

            try {
                module = new window[moduleType](element, runtime);

                if ($(element).hasClass('xmodule_edit')) {
                    $(document).trigger('XModule.loaded.edit', [element, module]);
                }

                if ($(element).hasClass('xmodule_display')) {
                    $(document).trigger('XModule.loaded.display', [element, module]);
                }

                return module;
            } catch (error) {
                console.error('Unable to load ' + moduleType + ': ' + error.message);
            }
        };

        // Export this module. We do it at the end when everything is ready
        // because some RequireJS scripts require this module. If
        // `window.XModule` appears as defined before this file has a chance
        // to execute fully, then there is a chance that RequireJS will execute
        // some script prematurely.
        this.XModule = XModule;
    }).call(this);
}).call(window);
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1), __webpack_require__(0)))

/***/ }),

/***/ "./node_modules/babel-polyfill/lib/index.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/* WEBPACK VAR INJECTION */(function(global) {

__webpack_require__("./node_modules/core-js/shim.js");

__webpack_require__("./node_modules/babel-polyfill/node_modules/regenerator-runtime/runtime.js");

__webpack_require__("./node_modules/core-js/fn/regexp/escape.js");

if (global._babelPolyfill) {
  throw new Error("only one instance of babel-polyfill is allowed");
}
global._babelPolyfill = true;

var DEFINE_PROPERTY = "defineProperty";
function define(O, key, value) {
  O[key] || Object[DEFINE_PROPERTY](O, key, {
    writable: true,
    configurable: true,
    value: value
  });
}

define(String.prototype, "padLeft", "".padStart);
define(String.prototype, "padRight", "".padEnd);

"pop,reverse,shift,keys,values,entries,indexOf,every,some,forEach,map,filter,find,findIndex,includes,join,slice,concat,push,splice,unshift,sort,lastIndexOf,reduce,reduceRight,copyWithin,fill".split(",").forEach(function (key) {
  [][key] && define(Array, key, Function.call.bind([][key]));
});
/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__("./node_modules/webpack/buildin/global.js")))

/***/ }),

/***/ "./node_modules/babel-polyfill/node_modules/regenerator-runtime/runtime.js":
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {/**
 * Copyright (c) 2014, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * https://raw.github.com/facebook/regenerator/master/LICENSE file. An
 * additional grant of patent rights can be found in the PATENTS file in
 * the same directory.
 */

!(function(global) {
  "use strict";

  var Op = Object.prototype;
  var hasOwn = Op.hasOwnProperty;
  var undefined; // More compressible than void 0.
  var $Symbol = typeof Symbol === "function" ? Symbol : {};
  var iteratorSymbol = $Symbol.iterator || "@@iterator";
  var asyncIteratorSymbol = $Symbol.asyncIterator || "@@asyncIterator";
  var toStringTagSymbol = $Symbol.toStringTag || "@@toStringTag";

  var inModule = typeof module === "object";
  var runtime = global.regeneratorRuntime;
  if (runtime) {
    if (inModule) {
      // If regeneratorRuntime is defined globally and we're in a module,
      // make the exports object identical to regeneratorRuntime.
      module.exports = runtime;
    }
    // Don't bother evaluating the rest of this file if the runtime was
    // already defined globally.
    return;
  }

  // Define the runtime globally (as expected by generated code) as either
  // module.exports (if we're in a module) or a new, empty object.
  runtime = global.regeneratorRuntime = inModule ? module.exports : {};

  function wrap(innerFn, outerFn, self, tryLocsList) {
    // If outerFn provided and outerFn.prototype is a Generator, then outerFn.prototype instanceof Generator.
    var protoGenerator = outerFn && outerFn.prototype instanceof Generator ? outerFn : Generator;
    var generator = Object.create(protoGenerator.prototype);
    var context = new Context(tryLocsList || []);

    // The ._invoke method unifies the implementations of the .next,
    // .throw, and .return methods.
    generator._invoke = makeInvokeMethod(innerFn, self, context);

    return generator;
  }
  runtime.wrap = wrap;

  // Try/catch helper to minimize deoptimizations. Returns a completion
  // record like context.tryEntries[i].completion. This interface could
  // have been (and was previously) designed to take a closure to be
  // invoked without arguments, but in all the cases we care about we
  // already have an existing method we want to call, so there's no need
  // to create a new function object. We can even get away with assuming
  // the method takes exactly one argument, since that happens to be true
  // in every case, so we don't have to touch the arguments object. The
  // only additional allocation required is the completion record, which
  // has a stable shape and so hopefully should be cheap to allocate.
  function tryCatch(fn, obj, arg) {
    try {
      return { type: "normal", arg: fn.call(obj, arg) };
    } catch (err) {
      return { type: "throw", arg: err };
    }
  }

  var GenStateSuspendedStart = "suspendedStart";
  var GenStateSuspendedYield = "suspendedYield";
  var GenStateExecuting = "executing";
  var GenStateCompleted = "completed";

  // Returning this object from the innerFn has the same effect as
  // breaking out of the dispatch switch statement.
  var ContinueSentinel = {};

  // Dummy constructor functions that we use as the .constructor and
  // .constructor.prototype properties for functions that return Generator
  // objects. For full spec compliance, you may wish to configure your
  // minifier not to mangle the names of these two functions.
  function Generator() {}
  function GeneratorFunction() {}
  function GeneratorFunctionPrototype() {}

  // This is a polyfill for %IteratorPrototype% for environments that
  // don't natively support it.
  var IteratorPrototype = {};
  IteratorPrototype[iteratorSymbol] = function () {
    return this;
  };

  var getProto = Object.getPrototypeOf;
  var NativeIteratorPrototype = getProto && getProto(getProto(values([])));
  if (NativeIteratorPrototype &&
      NativeIteratorPrototype !== Op &&
      hasOwn.call(NativeIteratorPrototype, iteratorSymbol)) {
    // This environment has a native %IteratorPrototype%; use it instead
    // of the polyfill.
    IteratorPrototype = NativeIteratorPrototype;
  }

  var Gp = GeneratorFunctionPrototype.prototype =
    Generator.prototype = Object.create(IteratorPrototype);
  GeneratorFunction.prototype = Gp.constructor = GeneratorFunctionPrototype;
  GeneratorFunctionPrototype.constructor = GeneratorFunction;
  GeneratorFunctionPrototype[toStringTagSymbol] =
    GeneratorFunction.displayName = "GeneratorFunction";

  // Helper for defining the .next, .throw, and .return methods of the
  // Iterator interface in terms of a single ._invoke method.
  function defineIteratorMethods(prototype) {
    ["next", "throw", "return"].forEach(function(method) {
      prototype[method] = function(arg) {
        return this._invoke(method, arg);
      };
    });
  }

  runtime.isGeneratorFunction = function(genFun) {
    var ctor = typeof genFun === "function" && genFun.constructor;
    return ctor
      ? ctor === GeneratorFunction ||
        // For the native GeneratorFunction constructor, the best we can
        // do is to check its .name property.
        (ctor.displayName || ctor.name) === "GeneratorFunction"
      : false;
  };

  runtime.mark = function(genFun) {
    if (Object.setPrototypeOf) {
      Object.setPrototypeOf(genFun, GeneratorFunctionPrototype);
    } else {
      genFun.__proto__ = GeneratorFunctionPrototype;
      if (!(toStringTagSymbol in genFun)) {
        genFun[toStringTagSymbol] = "GeneratorFunction";
      }
    }
    genFun.prototype = Object.create(Gp);
    return genFun;
  };

  // Within the body of any async function, `await x` is transformed to
  // `yield regeneratorRuntime.awrap(x)`, so that the runtime can test
  // `hasOwn.call(value, "__await")` to determine if the yielded value is
  // meant to be awaited.
  runtime.awrap = function(arg) {
    return { __await: arg };
  };

  function AsyncIterator(generator) {
    function invoke(method, arg, resolve, reject) {
      var record = tryCatch(generator[method], generator, arg);
      if (record.type === "throw") {
        reject(record.arg);
      } else {
        var result = record.arg;
        var value = result.value;
        if (value &&
            typeof value === "object" &&
            hasOwn.call(value, "__await")) {
          return Promise.resolve(value.__await).then(function(value) {
            invoke("next", value, resolve, reject);
          }, function(err) {
            invoke("throw", err, resolve, reject);
          });
        }

        return Promise.resolve(value).then(function(unwrapped) {
          // When a yielded Promise is resolved, its final value becomes
          // the .value of the Promise<{value,done}> result for the
          // current iteration. If the Promise is rejected, however, the
          // result for this iteration will be rejected with the same
          // reason. Note that rejections of yielded Promises are not
          // thrown back into the generator function, as is the case
          // when an awaited Promise is rejected. This difference in
          // behavior between yield and await is important, because it
          // allows the consumer to decide what to do with the yielded
          // rejection (swallow it and continue, manually .throw it back
          // into the generator, abandon iteration, whatever). With
          // await, by contrast, there is no opportunity to examine the
          // rejection reason outside the generator function, so the
          // only option is to throw it from the await expression, and
          // let the generator function handle the exception.
          result.value = unwrapped;
          resolve(result);
        }, reject);
      }
    }

    if (typeof global.process === "object" && global.process.domain) {
      invoke = global.process.domain.bind(invoke);
    }

    var previousPromise;

    function enqueue(method, arg) {
      function callInvokeWithMethodAndArg() {
        return new Promise(function(resolve, reject) {
          invoke(method, arg, resolve, reject);
        });
      }

      return previousPromise =
        // If enqueue has been called before, then we want to wait until
        // all previous Promises have been resolved before calling invoke,
        // so that results are always delivered in the correct order. If
        // enqueue has not been called before, then it is important to
        // call invoke immediately, without waiting on a callback to fire,
        // so that the async generator function has the opportunity to do
        // any necessary setup in a predictable way. This predictability
        // is why the Promise constructor synchronously invokes its
        // executor callback, and why async functions synchronously
        // execute code before the first await. Since we implement simple
        // async functions in terms of async generators, it is especially
        // important to get this right, even though it requires care.
        previousPromise ? previousPromise.then(
          callInvokeWithMethodAndArg,
          // Avoid propagating failures to Promises returned by later
          // invocations of the iterator.
          callInvokeWithMethodAndArg
        ) : callInvokeWithMethodAndArg();
    }

    // Define the unified helper method that is used to implement .next,
    // .throw, and .return (see defineIteratorMethods).
    this._invoke = enqueue;
  }

  defineIteratorMethods(AsyncIterator.prototype);
  AsyncIterator.prototype[asyncIteratorSymbol] = function () {
    return this;
  };
  runtime.AsyncIterator = AsyncIterator;

  // Note that simple async functions are implemented on top of
  // AsyncIterator objects; they just return a Promise for the value of
  // the final result produced by the iterator.
  runtime.async = function(innerFn, outerFn, self, tryLocsList) {
    var iter = new AsyncIterator(
      wrap(innerFn, outerFn, self, tryLocsList)
    );

    return runtime.isGeneratorFunction(outerFn)
      ? iter // If outerFn is a generator, return the full iterator.
      : iter.next().then(function(result) {
          return result.done ? result.value : iter.next();
        });
  };

  function makeInvokeMethod(innerFn, self, context) {
    var state = GenStateSuspendedStart;

    return function invoke(method, arg) {
      if (state === GenStateExecuting) {
        throw new Error("Generator is already running");
      }

      if (state === GenStateCompleted) {
        if (method === "throw") {
          throw arg;
        }

        // Be forgiving, per 25.3.3.3.3 of the spec:
        // https://people.mozilla.org/~jorendorff/es6-draft.html#sec-generatorresume
        return doneResult();
      }

      context.method = method;
      context.arg = arg;

      while (true) {
        var delegate = context.delegate;
        if (delegate) {
          var delegateResult = maybeInvokeDelegate(delegate, context);
          if (delegateResult) {
            if (delegateResult === ContinueSentinel) continue;
            return delegateResult;
          }
        }

        if (context.method === "next") {
          // Setting context._sent for legacy support of Babel's
          // function.sent implementation.
          context.sent = context._sent = context.arg;

        } else if (context.method === "throw") {
          if (state === GenStateSuspendedStart) {
            state = GenStateCompleted;
            throw context.arg;
          }

          context.dispatchException(context.arg);

        } else if (context.method === "return") {
          context.abrupt("return", context.arg);
        }

        state = GenStateExecuting;

        var record = tryCatch(innerFn, self, context);
        if (record.type === "normal") {
          // If an exception is thrown from innerFn, we leave state ===
          // GenStateExecuting and loop back for another invocation.
          state = context.done
            ? GenStateCompleted
            : GenStateSuspendedYield;

          if (record.arg === ContinueSentinel) {
            continue;
          }

          return {
            value: record.arg,
            done: context.done
          };

        } else if (record.type === "throw") {
          state = GenStateCompleted;
          // Dispatch the exception by looping back around to the
          // context.dispatchException(context.arg) call above.
          context.method = "throw";
          context.arg = record.arg;
        }
      }
    };
  }

  // Call delegate.iterator[context.method](context.arg) and handle the
  // result, either by returning a { value, done } result from the
  // delegate iterator, or by modifying context.method and context.arg,
  // setting context.delegate to null, and returning the ContinueSentinel.
  function maybeInvokeDelegate(delegate, context) {
    var method = delegate.iterator[context.method];
    if (method === undefined) {
      // A .throw or .return when the delegate iterator has no .throw
      // method always terminates the yield* loop.
      context.delegate = null;

      if (context.method === "throw") {
        if (delegate.iterator.return) {
          // If the delegate iterator has a return method, give it a
          // chance to clean up.
          context.method = "return";
          context.arg = undefined;
          maybeInvokeDelegate(delegate, context);

          if (context.method === "throw") {
            // If maybeInvokeDelegate(context) changed context.method from
            // "return" to "throw", let that override the TypeError below.
            return ContinueSentinel;
          }
        }

        context.method = "throw";
        context.arg = new TypeError(
          "The iterator does not provide a 'throw' method");
      }

      return ContinueSentinel;
    }

    var record = tryCatch(method, delegate.iterator, context.arg);

    if (record.type === "throw") {
      context.method = "throw";
      context.arg = record.arg;
      context.delegate = null;
      return ContinueSentinel;
    }

    var info = record.arg;

    if (! info) {
      context.method = "throw";
      context.arg = new TypeError("iterator result is not an object");
      context.delegate = null;
      return ContinueSentinel;
    }

    if (info.done) {
      // Assign the result of the finished delegate to the temporary
      // variable specified by delegate.resultName (see delegateYield).
      context[delegate.resultName] = info.value;

      // Resume execution at the desired location (see delegateYield).
      context.next = delegate.nextLoc;

      // If context.method was "throw" but the delegate handled the
      // exception, let the outer generator proceed normally. If
      // context.method was "next", forget context.arg since it has been
      // "consumed" by the delegate iterator. If context.method was
      // "return", allow the original .return call to continue in the
      // outer generator.
      if (context.method !== "return") {
        context.method = "next";
        context.arg = undefined;
      }

    } else {
      // Re-yield the result returned by the delegate method.
      return info;
    }

    // The delegate iterator is finished, so forget it and continue with
    // the outer generator.
    context.delegate = null;
    return ContinueSentinel;
  }

  // Define Generator.prototype.{next,throw,return} in terms of the
  // unified ._invoke helper method.
  defineIteratorMethods(Gp);

  Gp[toStringTagSymbol] = "Generator";

  // A Generator should always return itself as the iterator object when the
  // @@iterator function is called on it. Some browsers' implementations of the
  // iterator prototype chain incorrectly implement this, causing the Generator
  // object to not be returned from this call. This ensures that doesn't happen.
  // See https://github.com/facebook/regenerator/issues/274 for more details.
  Gp[iteratorSymbol] = function() {
    return this;
  };

  Gp.toString = function() {
    return "[object Generator]";
  };

  function pushTryEntry(locs) {
    var entry = { tryLoc: locs[0] };

    if (1 in locs) {
      entry.catchLoc = locs[1];
    }

    if (2 in locs) {
      entry.finallyLoc = locs[2];
      entry.afterLoc = locs[3];
    }

    this.tryEntries.push(entry);
  }

  function resetTryEntry(entry) {
    var record = entry.completion || {};
    record.type = "normal";
    delete record.arg;
    entry.completion = record;
  }

  function Context(tryLocsList) {
    // The root entry object (effectively a try statement without a catch
    // or a finally block) gives us a place to store values thrown from
    // locations where there is no enclosing try statement.
    this.tryEntries = [{ tryLoc: "root" }];
    tryLocsList.forEach(pushTryEntry, this);
    this.reset(true);
  }

  runtime.keys = function(object) {
    var keys = [];
    for (var key in object) {
      keys.push(key);
    }
    keys.reverse();

    // Rather than returning an object with a next method, we keep
    // things simple and return the next function itself.
    return function next() {
      while (keys.length) {
        var key = keys.pop();
        if (key in object) {
          next.value = key;
          next.done = false;
          return next;
        }
      }

      // To avoid creating an additional object, we just hang the .value
      // and .done properties off the next function object itself. This
      // also ensures that the minifier will not anonymize the function.
      next.done = true;
      return next;
    };
  };

  function values(iterable) {
    if (iterable) {
      var iteratorMethod = iterable[iteratorSymbol];
      if (iteratorMethod) {
        return iteratorMethod.call(iterable);
      }

      if (typeof iterable.next === "function") {
        return iterable;
      }

      if (!isNaN(iterable.length)) {
        var i = -1, next = function next() {
          while (++i < iterable.length) {
            if (hasOwn.call(iterable, i)) {
              next.value = iterable[i];
              next.done = false;
              return next;
            }
          }

          next.value = undefined;
          next.done = true;

          return next;
        };

        return next.next = next;
      }
    }

    // Return an iterator with no values.
    return { next: doneResult };
  }
  runtime.values = values;

  function doneResult() {
    return { value: undefined, done: true };
  }

  Context.prototype = {
    constructor: Context,

    reset: function(skipTempReset) {
      this.prev = 0;
      this.next = 0;
      // Resetting context._sent for legacy support of Babel's
      // function.sent implementation.
      this.sent = this._sent = undefined;
      this.done = false;
      this.delegate = null;

      this.method = "next";
      this.arg = undefined;

      this.tryEntries.forEach(resetTryEntry);

      if (!skipTempReset) {
        for (var name in this) {
          // Not sure about the optimal order of these conditions:
          if (name.charAt(0) === "t" &&
              hasOwn.call(this, name) &&
              !isNaN(+name.slice(1))) {
            this[name] = undefined;
          }
        }
      }
    },

    stop: function() {
      this.done = true;

      var rootEntry = this.tryEntries[0];
      var rootRecord = rootEntry.completion;
      if (rootRecord.type === "throw") {
        throw rootRecord.arg;
      }

      return this.rval;
    },

    dispatchException: function(exception) {
      if (this.done) {
        throw exception;
      }

      var context = this;
      function handle(loc, caught) {
        record.type = "throw";
        record.arg = exception;
        context.next = loc;

        if (caught) {
          // If the dispatched exception was caught by a catch block,
          // then let that catch block handle the exception normally.
          context.method = "next";
          context.arg = undefined;
        }

        return !! caught;
      }

      for (var i = this.tryEntries.length - 1; i >= 0; --i) {
        var entry = this.tryEntries[i];
        var record = entry.completion;

        if (entry.tryLoc === "root") {
          // Exception thrown outside of any try block that could handle
          // it, so set the completion value of the entire function to
          // throw the exception.
          return handle("end");
        }

        if (entry.tryLoc <= this.prev) {
          var hasCatch = hasOwn.call(entry, "catchLoc");
          var hasFinally = hasOwn.call(entry, "finallyLoc");

          if (hasCatch && hasFinally) {
            if (this.prev < entry.catchLoc) {
              return handle(entry.catchLoc, true);
            } else if (this.prev < entry.finallyLoc) {
              return handle(entry.finallyLoc);
            }

          } else if (hasCatch) {
            if (this.prev < entry.catchLoc) {
              return handle(entry.catchLoc, true);
            }

          } else if (hasFinally) {
            if (this.prev < entry.finallyLoc) {
              return handle(entry.finallyLoc);
            }

          } else {
            throw new Error("try statement without catch or finally");
          }
        }
      }
    },

    abrupt: function(type, arg) {
      for (var i = this.tryEntries.length - 1; i >= 0; --i) {
        var entry = this.tryEntries[i];
        if (entry.tryLoc <= this.prev &&
            hasOwn.call(entry, "finallyLoc") &&
            this.prev < entry.finallyLoc) {
          var finallyEntry = entry;
          break;
        }
      }

      if (finallyEntry &&
          (type === "break" ||
           type === "continue") &&
          finallyEntry.tryLoc <= arg &&
          arg <= finallyEntry.finallyLoc) {
        // Ignore the finally entry if control is not jumping to a
        // location outside the try/catch block.
        finallyEntry = null;
      }

      var record = finallyEntry ? finallyEntry.completion : {};
      record.type = type;
      record.arg = arg;

      if (finallyEntry) {
        this.method = "next";
        this.next = finallyEntry.finallyLoc;
        return ContinueSentinel;
      }

      return this.complete(record);
    },

    complete: function(record, afterLoc) {
      if (record.type === "throw") {
        throw record.arg;
      }

      if (record.type === "break" ||
          record.type === "continue") {
        this.next = record.arg;
      } else if (record.type === "return") {
        this.rval = this.arg = record.arg;
        this.method = "return";
        this.next = "end";
      } else if (record.type === "normal" && afterLoc) {
        this.next = afterLoc;
      }

      return ContinueSentinel;
    },

    finish: function(finallyLoc) {
      for (var i = this.tryEntries.length - 1; i >= 0; --i) {
        var entry = this.tryEntries[i];
        if (entry.finallyLoc === finallyLoc) {
          this.complete(entry.completion, entry.afterLoc);
          resetTryEntry(entry);
          return ContinueSentinel;
        }
      }
    },

    "catch": function(tryLoc) {
      for (var i = this.tryEntries.length - 1; i >= 0; --i) {
        var entry = this.tryEntries[i];
        if (entry.tryLoc === tryLoc) {
          var record = entry.completion;
          if (record.type === "throw") {
            var thrown = record.arg;
            resetTryEntry(entry);
          }
          return thrown;
        }
      }

      // The context.catch method must only be called with a location
      // argument that corresponds to a known catch block.
      throw new Error("illegal catch attempt");
    },

    delegateYield: function(iterable, resultName, nextLoc) {
      this.delegate = {
        iterator: values(iterable),
        resultName: resultName,
        nextLoc: nextLoc
      };

      if (this.method === "next") {
        // Deliberately forget the last sent value so that we don't
        // accidentally pass it on to the delegate.
        this.arg = undefined;
      }

      return ContinueSentinel;
    }
  };
})(
  // Among the various tricks for obtaining a reference to the global
  // object, this seems to be the most reliable technique that does not
  // use indirect eval (which violates Content Security Policy).
  typeof global === "object" ? global :
  typeof window === "object" ? window :
  typeof self === "object" ? self : this
);

/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__("./node_modules/webpack/buildin/global.js")))

/***/ }),

/***/ "./node_modules/core-js/fn/regexp/escape.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/core.regexp.escape.js");
module.exports = __webpack_require__("./node_modules/core-js/modules/_core.js").RegExp.escape;


/***/ }),

/***/ "./node_modules/core-js/modules/_a-function.js":
/***/ (function(module, exports) {

module.exports = function (it) {
  if (typeof it != 'function') throw TypeError(it + ' is not a function!');
  return it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_a-number-value.js":
/***/ (function(module, exports, __webpack_require__) {

var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
module.exports = function (it, msg) {
  if (typeof it != 'number' && cof(it) != 'Number') throw TypeError(msg);
  return +it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_add-to-unscopables.js":
/***/ (function(module, exports, __webpack_require__) {

// 22.1.3.31 Array.prototype[@@unscopables]
var UNSCOPABLES = __webpack_require__("./node_modules/core-js/modules/_wks.js")('unscopables');
var ArrayProto = Array.prototype;
if (ArrayProto[UNSCOPABLES] == undefined) __webpack_require__("./node_modules/core-js/modules/_hide.js")(ArrayProto, UNSCOPABLES, {});
module.exports = function (key) {
  ArrayProto[UNSCOPABLES][key] = true;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_an-instance.js":
/***/ (function(module, exports) {

module.exports = function (it, Constructor, name, forbiddenField) {
  if (!(it instanceof Constructor) || (forbiddenField !== undefined && forbiddenField in it)) {
    throw TypeError(name + ': incorrect invocation!');
  } return it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_an-object.js":
/***/ (function(module, exports, __webpack_require__) {

var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
module.exports = function (it) {
  if (!isObject(it)) throw TypeError(it + ' is not an object!');
  return it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-copy-within.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
// 22.1.3.3 Array.prototype.copyWithin(target, start, end = this.length)

var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");

module.exports = [].copyWithin || function copyWithin(target /* = 0 */, start /* = 0, end = @length */) {
  var O = toObject(this);
  var len = toLength(O.length);
  var to = toAbsoluteIndex(target, len);
  var from = toAbsoluteIndex(start, len);
  var end = arguments.length > 2 ? arguments[2] : undefined;
  var count = Math.min((end === undefined ? len : toAbsoluteIndex(end, len)) - from, len - to);
  var inc = 1;
  if (from < to && to < from + count) {
    inc = -1;
    from += count - 1;
    to += count - 1;
  }
  while (count-- > 0) {
    if (from in O) O[to] = O[from];
    else delete O[to];
    to += inc;
    from += inc;
  } return O;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-fill.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
// 22.1.3.6 Array.prototype.fill(value, start = 0, end = this.length)

var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
module.exports = function fill(value /* , start = 0, end = @length */) {
  var O = toObject(this);
  var length = toLength(O.length);
  var aLen = arguments.length;
  var index = toAbsoluteIndex(aLen > 1 ? arguments[1] : undefined, length);
  var end = aLen > 2 ? arguments[2] : undefined;
  var endPos = end === undefined ? length : toAbsoluteIndex(end, length);
  while (endPos > index) O[index++] = value;
  return O;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-from-iterable.js":
/***/ (function(module, exports, __webpack_require__) {

var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");

module.exports = function (iter, ITERATOR) {
  var result = [];
  forOf(iter, false, result.push, result, ITERATOR);
  return result;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-includes.js":
/***/ (function(module, exports, __webpack_require__) {

// false -> Array#indexOf
// true  -> Array#includes
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
module.exports = function (IS_INCLUDES) {
  return function ($this, el, fromIndex) {
    var O = toIObject($this);
    var length = toLength(O.length);
    var index = toAbsoluteIndex(fromIndex, length);
    var value;
    // Array#includes uses SameValueZero equality algorithm
    // eslint-disable-next-line no-self-compare
    if (IS_INCLUDES && el != el) while (length > index) {
      value = O[index++];
      // eslint-disable-next-line no-self-compare
      if (value != value) return true;
    // Array#indexOf ignores holes, Array#includes - not
    } else for (;length > index; index++) if (IS_INCLUDES || index in O) {
      if (O[index] === el) return IS_INCLUDES || index || 0;
    } return !IS_INCLUDES && -1;
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-methods.js":
/***/ (function(module, exports, __webpack_require__) {

// 0 -> Array#forEach
// 1 -> Array#map
// 2 -> Array#filter
// 3 -> Array#some
// 4 -> Array#every
// 5 -> Array#find
// 6 -> Array#findIndex
var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var IObject = __webpack_require__("./node_modules/core-js/modules/_iobject.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var asc = __webpack_require__("./node_modules/core-js/modules/_array-species-create.js");
module.exports = function (TYPE, $create) {
  var IS_MAP = TYPE == 1;
  var IS_FILTER = TYPE == 2;
  var IS_SOME = TYPE == 3;
  var IS_EVERY = TYPE == 4;
  var IS_FIND_INDEX = TYPE == 6;
  var NO_HOLES = TYPE == 5 || IS_FIND_INDEX;
  var create = $create || asc;
  return function ($this, callbackfn, that) {
    var O = toObject($this);
    var self = IObject(O);
    var f = ctx(callbackfn, that, 3);
    var length = toLength(self.length);
    var index = 0;
    var result = IS_MAP ? create($this, length) : IS_FILTER ? create($this, 0) : undefined;
    var val, res;
    for (;length > index; index++) if (NO_HOLES || index in self) {
      val = self[index];
      res = f(val, index, O);
      if (TYPE) {
        if (IS_MAP) result[index] = res;   // map
        else if (res) switch (TYPE) {
          case 3: return true;             // some
          case 5: return val;              // find
          case 6: return index;            // findIndex
          case 2: result.push(val);        // filter
        } else if (IS_EVERY) return false; // every
      }
    }
    return IS_FIND_INDEX ? -1 : IS_SOME || IS_EVERY ? IS_EVERY : result;
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-reduce.js":
/***/ (function(module, exports, __webpack_require__) {

var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var IObject = __webpack_require__("./node_modules/core-js/modules/_iobject.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");

module.exports = function (that, callbackfn, aLen, memo, isRight) {
  aFunction(callbackfn);
  var O = toObject(that);
  var self = IObject(O);
  var length = toLength(O.length);
  var index = isRight ? length - 1 : 0;
  var i = isRight ? -1 : 1;
  if (aLen < 2) for (;;) {
    if (index in self) {
      memo = self[index];
      index += i;
      break;
    }
    index += i;
    if (isRight ? index < 0 : length <= index) {
      throw TypeError('Reduce of empty array with no initial value');
    }
  }
  for (;isRight ? index >= 0 : length > index; index += i) if (index in self) {
    memo = callbackfn(memo, self[index], index, O);
  }
  return memo;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-species-constructor.js":
/***/ (function(module, exports, __webpack_require__) {

var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var isArray = __webpack_require__("./node_modules/core-js/modules/_is-array.js");
var SPECIES = __webpack_require__("./node_modules/core-js/modules/_wks.js")('species');

module.exports = function (original) {
  var C;
  if (isArray(original)) {
    C = original.constructor;
    // cross-realm fallback
    if (typeof C == 'function' && (C === Array || isArray(C.prototype))) C = undefined;
    if (isObject(C)) {
      C = C[SPECIES];
      if (C === null) C = undefined;
    }
  } return C === undefined ? Array : C;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_array-species-create.js":
/***/ (function(module, exports, __webpack_require__) {

// 9.4.2.3 ArraySpeciesCreate(originalArray, length)
var speciesConstructor = __webpack_require__("./node_modules/core-js/modules/_array-species-constructor.js");

module.exports = function (original, length) {
  return new (speciesConstructor(original))(length);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_bind.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var invoke = __webpack_require__("./node_modules/core-js/modules/_invoke.js");
var arraySlice = [].slice;
var factories = {};

var construct = function (F, len, args) {
  if (!(len in factories)) {
    for (var n = [], i = 0; i < len; i++) n[i] = 'a[' + i + ']';
    // eslint-disable-next-line no-new-func
    factories[len] = Function('F,a', 'return new F(' + n.join(',') + ')');
  } return factories[len](F, args);
};

module.exports = Function.bind || function bind(that /* , ...args */) {
  var fn = aFunction(this);
  var partArgs = arraySlice.call(arguments, 1);
  var bound = function (/* args... */) {
    var args = partArgs.concat(arraySlice.call(arguments));
    return this instanceof bound ? construct(fn, args.length, args) : invoke(fn, args, that);
  };
  if (isObject(fn.prototype)) bound.prototype = fn.prototype;
  return bound;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_classof.js":
/***/ (function(module, exports, __webpack_require__) {

// getting tag from 19.1.3.6 Object.prototype.toString()
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
var TAG = __webpack_require__("./node_modules/core-js/modules/_wks.js")('toStringTag');
// ES3 wrong here
var ARG = cof(function () { return arguments; }()) == 'Arguments';

// fallback for IE11 Script Access Denied error
var tryGet = function (it, key) {
  try {
    return it[key];
  } catch (e) { /* empty */ }
};

module.exports = function (it) {
  var O, T, B;
  return it === undefined ? 'Undefined' : it === null ? 'Null'
    // @@toStringTag case
    : typeof (T = tryGet(O = Object(it), TAG)) == 'string' ? T
    // builtinTag case
    : ARG ? cof(O)
    // ES3 arguments fallback
    : (B = cof(O)) == 'Object' && typeof O.callee == 'function' ? 'Arguments' : B;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_cof.js":
/***/ (function(module, exports) {

var toString = {}.toString;

module.exports = function (it) {
  return toString.call(it).slice(8, -1);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_collection-strong.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var create = __webpack_require__("./node_modules/core-js/modules/_object-create.js");
var redefineAll = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js");
var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");
var $iterDefine = __webpack_require__("./node_modules/core-js/modules/_iter-define.js");
var step = __webpack_require__("./node_modules/core-js/modules/_iter-step.js");
var setSpecies = __webpack_require__("./node_modules/core-js/modules/_set-species.js");
var DESCRIPTORS = __webpack_require__("./node_modules/core-js/modules/_descriptors.js");
var fastKey = __webpack_require__("./node_modules/core-js/modules/_meta.js").fastKey;
var validate = __webpack_require__("./node_modules/core-js/modules/_validate-collection.js");
var SIZE = DESCRIPTORS ? '_s' : 'size';

var getEntry = function (that, key) {
  // fast case
  var index = fastKey(key);
  var entry;
  if (index !== 'F') return that._i[index];
  // frozen object case
  for (entry = that._f; entry; entry = entry.n) {
    if (entry.k == key) return entry;
  }
};

module.exports = {
  getConstructor: function (wrapper, NAME, IS_MAP, ADDER) {
    var C = wrapper(function (that, iterable) {
      anInstance(that, C, NAME, '_i');
      that._t = NAME;         // collection type
      that._i = create(null); // index
      that._f = undefined;    // first entry
      that._l = undefined;    // last entry
      that[SIZE] = 0;         // size
      if (iterable != undefined) forOf(iterable, IS_MAP, that[ADDER], that);
    });
    redefineAll(C.prototype, {
      // 23.1.3.1 Map.prototype.clear()
      // 23.2.3.2 Set.prototype.clear()
      clear: function clear() {
        for (var that = validate(this, NAME), data = that._i, entry = that._f; entry; entry = entry.n) {
          entry.r = true;
          if (entry.p) entry.p = entry.p.n = undefined;
          delete data[entry.i];
        }
        that._f = that._l = undefined;
        that[SIZE] = 0;
      },
      // 23.1.3.3 Map.prototype.delete(key)
      // 23.2.3.4 Set.prototype.delete(value)
      'delete': function (key) {
        var that = validate(this, NAME);
        var entry = getEntry(that, key);
        if (entry) {
          var next = entry.n;
          var prev = entry.p;
          delete that._i[entry.i];
          entry.r = true;
          if (prev) prev.n = next;
          if (next) next.p = prev;
          if (that._f == entry) that._f = next;
          if (that._l == entry) that._l = prev;
          that[SIZE]--;
        } return !!entry;
      },
      // 23.2.3.6 Set.prototype.forEach(callbackfn, thisArg = undefined)
      // 23.1.3.5 Map.prototype.forEach(callbackfn, thisArg = undefined)
      forEach: function forEach(callbackfn /* , that = undefined */) {
        validate(this, NAME);
        var f = ctx(callbackfn, arguments.length > 1 ? arguments[1] : undefined, 3);
        var entry;
        while (entry = entry ? entry.n : this._f) {
          f(entry.v, entry.k, this);
          // revert to the last existing entry
          while (entry && entry.r) entry = entry.p;
        }
      },
      // 23.1.3.7 Map.prototype.has(key)
      // 23.2.3.7 Set.prototype.has(value)
      has: function has(key) {
        return !!getEntry(validate(this, NAME), key);
      }
    });
    if (DESCRIPTORS) dP(C.prototype, 'size', {
      get: function () {
        return validate(this, NAME)[SIZE];
      }
    });
    return C;
  },
  def: function (that, key, value) {
    var entry = getEntry(that, key);
    var prev, index;
    // change existing entry
    if (entry) {
      entry.v = value;
    // create new entry
    } else {
      that._l = entry = {
        i: index = fastKey(key, true), // <- index
        k: key,                        // <- key
        v: value,                      // <- value
        p: prev = that._l,             // <- previous entry
        n: undefined,                  // <- next entry
        r: false                       // <- removed
      };
      if (!that._f) that._f = entry;
      if (prev) prev.n = entry;
      that[SIZE]++;
      // add to index
      if (index !== 'F') that._i[index] = entry;
    } return that;
  },
  getEntry: getEntry,
  setStrong: function (C, NAME, IS_MAP) {
    // add .keys, .values, .entries, [@@iterator]
    // 23.1.3.4, 23.1.3.8, 23.1.3.11, 23.1.3.12, 23.2.3.5, 23.2.3.8, 23.2.3.10, 23.2.3.11
    $iterDefine(C, NAME, function (iterated, kind) {
      this._t = validate(iterated, NAME); // target
      this._k = kind;                     // kind
      this._l = undefined;                // previous
    }, function () {
      var that = this;
      var kind = that._k;
      var entry = that._l;
      // revert to the last existing entry
      while (entry && entry.r) entry = entry.p;
      // get next entry
      if (!that._t || !(that._l = entry = entry ? entry.n : that._t._f)) {
        // or finish the iteration
        that._t = undefined;
        return step(1);
      }
      // return step by kind
      if (kind == 'keys') return step(0, entry.k);
      if (kind == 'values') return step(0, entry.v);
      return step(0, [entry.k, entry.v]);
    }, IS_MAP ? 'entries' : 'values', !IS_MAP, true);

    // add [@@species], 23.1.2.2, 23.2.2.2
    setSpecies(NAME);
  }
};


/***/ }),

/***/ "./node_modules/core-js/modules/_collection-to-json.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/DavidBruant/Map-Set.prototype.toJSON
var classof = __webpack_require__("./node_modules/core-js/modules/_classof.js");
var from = __webpack_require__("./node_modules/core-js/modules/_array-from-iterable.js");
module.exports = function (NAME) {
  return function toJSON() {
    if (classof(this) != NAME) throw TypeError(NAME + "#toJSON isn't generic");
    return from(this);
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_collection-weak.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var redefineAll = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js");
var getWeak = __webpack_require__("./node_modules/core-js/modules/_meta.js").getWeak;
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");
var createArrayMethod = __webpack_require__("./node_modules/core-js/modules/_array-methods.js");
var $has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var validate = __webpack_require__("./node_modules/core-js/modules/_validate-collection.js");
var arrayFind = createArrayMethod(5);
var arrayFindIndex = createArrayMethod(6);
var id = 0;

// fallback for uncaught frozen keys
var uncaughtFrozenStore = function (that) {
  return that._l || (that._l = new UncaughtFrozenStore());
};
var UncaughtFrozenStore = function () {
  this.a = [];
};
var findUncaughtFrozen = function (store, key) {
  return arrayFind(store.a, function (it) {
    return it[0] === key;
  });
};
UncaughtFrozenStore.prototype = {
  get: function (key) {
    var entry = findUncaughtFrozen(this, key);
    if (entry) return entry[1];
  },
  has: function (key) {
    return !!findUncaughtFrozen(this, key);
  },
  set: function (key, value) {
    var entry = findUncaughtFrozen(this, key);
    if (entry) entry[1] = value;
    else this.a.push([key, value]);
  },
  'delete': function (key) {
    var index = arrayFindIndex(this.a, function (it) {
      return it[0] === key;
    });
    if (~index) this.a.splice(index, 1);
    return !!~index;
  }
};

module.exports = {
  getConstructor: function (wrapper, NAME, IS_MAP, ADDER) {
    var C = wrapper(function (that, iterable) {
      anInstance(that, C, NAME, '_i');
      that._t = NAME;      // collection type
      that._i = id++;      // collection id
      that._l = undefined; // leak store for uncaught frozen objects
      if (iterable != undefined) forOf(iterable, IS_MAP, that[ADDER], that);
    });
    redefineAll(C.prototype, {
      // 23.3.3.2 WeakMap.prototype.delete(key)
      // 23.4.3.3 WeakSet.prototype.delete(value)
      'delete': function (key) {
        if (!isObject(key)) return false;
        var data = getWeak(key);
        if (data === true) return uncaughtFrozenStore(validate(this, NAME))['delete'](key);
        return data && $has(data, this._i) && delete data[this._i];
      },
      // 23.3.3.4 WeakMap.prototype.has(key)
      // 23.4.3.4 WeakSet.prototype.has(value)
      has: function has(key) {
        if (!isObject(key)) return false;
        var data = getWeak(key);
        if (data === true) return uncaughtFrozenStore(validate(this, NAME)).has(key);
        return data && $has(data, this._i);
      }
    });
    return C;
  },
  def: function (that, key, value) {
    var data = getWeak(anObject(key), true);
    if (data === true) uncaughtFrozenStore(that).set(key, value);
    else data[that._i] = value;
    return that;
  },
  ufstore: uncaughtFrozenStore
};


/***/ }),

/***/ "./node_modules/core-js/modules/_collection.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var redefineAll = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js");
var meta = __webpack_require__("./node_modules/core-js/modules/_meta.js");
var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");
var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var $iterDetect = __webpack_require__("./node_modules/core-js/modules/_iter-detect.js");
var setToStringTag = __webpack_require__("./node_modules/core-js/modules/_set-to-string-tag.js");
var inheritIfRequired = __webpack_require__("./node_modules/core-js/modules/_inherit-if-required.js");

module.exports = function (NAME, wrapper, methods, common, IS_MAP, IS_WEAK) {
  var Base = global[NAME];
  var C = Base;
  var ADDER = IS_MAP ? 'set' : 'add';
  var proto = C && C.prototype;
  var O = {};
  var fixMethod = function (KEY) {
    var fn = proto[KEY];
    redefine(proto, KEY,
      KEY == 'delete' ? function (a) {
        return IS_WEAK && !isObject(a) ? false : fn.call(this, a === 0 ? 0 : a);
      } : KEY == 'has' ? function has(a) {
        return IS_WEAK && !isObject(a) ? false : fn.call(this, a === 0 ? 0 : a);
      } : KEY == 'get' ? function get(a) {
        return IS_WEAK && !isObject(a) ? undefined : fn.call(this, a === 0 ? 0 : a);
      } : KEY == 'add' ? function add(a) { fn.call(this, a === 0 ? 0 : a); return this; }
        : function set(a, b) { fn.call(this, a === 0 ? 0 : a, b); return this; }
    );
  };
  if (typeof C != 'function' || !(IS_WEAK || proto.forEach && !fails(function () {
    new C().entries().next();
  }))) {
    // create collection constructor
    C = common.getConstructor(wrapper, NAME, IS_MAP, ADDER);
    redefineAll(C.prototype, methods);
    meta.NEED = true;
  } else {
    var instance = new C();
    // early implementations not supports chaining
    var HASNT_CHAINING = instance[ADDER](IS_WEAK ? {} : -0, 1) != instance;
    // V8 ~  Chromium 40- weak-collections throws on primitives, but should return false
    var THROWS_ON_PRIMITIVES = fails(function () { instance.has(1); });
    // most early implementations doesn't supports iterables, most modern - not close it correctly
    var ACCEPT_ITERABLES = $iterDetect(function (iter) { new C(iter); }); // eslint-disable-line no-new
    // for early implementations -0 and +0 not the same
    var BUGGY_ZERO = !IS_WEAK && fails(function () {
      // V8 ~ Chromium 42- fails only with 5+ elements
      var $instance = new C();
      var index = 5;
      while (index--) $instance[ADDER](index, index);
      return !$instance.has(-0);
    });
    if (!ACCEPT_ITERABLES) {
      C = wrapper(function (target, iterable) {
        anInstance(target, C, NAME);
        var that = inheritIfRequired(new Base(), target, C);
        if (iterable != undefined) forOf(iterable, IS_MAP, that[ADDER], that);
        return that;
      });
      C.prototype = proto;
      proto.constructor = C;
    }
    if (THROWS_ON_PRIMITIVES || BUGGY_ZERO) {
      fixMethod('delete');
      fixMethod('has');
      IS_MAP && fixMethod('get');
    }
    if (BUGGY_ZERO || HASNT_CHAINING) fixMethod(ADDER);
    // weak collections should not contains .clear method
    if (IS_WEAK && proto.clear) delete proto.clear;
  }

  setToStringTag(C, NAME);

  O[NAME] = C;
  $export($export.G + $export.W + $export.F * (C != Base), O);

  if (!IS_WEAK) common.setStrong(C, NAME, IS_MAP);

  return C;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_core.js":
/***/ (function(module, exports) {

var core = module.exports = { version: '2.5.3' };
if (typeof __e == 'number') __e = core; // eslint-disable-line no-undef


/***/ }),

/***/ "./node_modules/core-js/modules/_create-property.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $defineProperty = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var createDesc = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");

module.exports = function (object, index, value) {
  if (index in object) $defineProperty.f(object, index, createDesc(0, value));
  else object[index] = value;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_ctx.js":
/***/ (function(module, exports, __webpack_require__) {

// optional / simple context binding
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
module.exports = function (fn, that, length) {
  aFunction(fn);
  if (that === undefined) return fn;
  switch (length) {
    case 1: return function (a) {
      return fn.call(that, a);
    };
    case 2: return function (a, b) {
      return fn.call(that, a, b);
    };
    case 3: return function (a, b, c) {
      return fn.call(that, a, b, c);
    };
  }
  return function (/* ...args */) {
    return fn.apply(that, arguments);
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_date-to-iso-string.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 20.3.4.36 / 15.9.5.43 Date.prototype.toISOString()
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var getTime = Date.prototype.getTime;
var $toISOString = Date.prototype.toISOString;

var lz = function (num) {
  return num > 9 ? num : '0' + num;
};

// PhantomJS / old WebKit has a broken implementations
module.exports = (fails(function () {
  return $toISOString.call(new Date(-5e13 - 1)) != '0385-07-25T07:06:39.999Z';
}) || !fails(function () {
  $toISOString.call(new Date(NaN));
})) ? function toISOString() {
  if (!isFinite(getTime.call(this))) throw RangeError('Invalid time value');
  var d = this;
  var y = d.getUTCFullYear();
  var m = d.getUTCMilliseconds();
  var s = y < 0 ? '-' : y > 9999 ? '+' : '';
  return s + ('00000' + Math.abs(y)).slice(s ? -6 : -4) +
    '-' + lz(d.getUTCMonth() + 1) + '-' + lz(d.getUTCDate()) +
    'T' + lz(d.getUTCHours()) + ':' + lz(d.getUTCMinutes()) +
    ':' + lz(d.getUTCSeconds()) + '.' + (m > 99 ? m : '0' + lz(m)) + 'Z';
} : $toISOString;


/***/ }),

/***/ "./node_modules/core-js/modules/_date-to-primitive.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var NUMBER = 'number';

module.exports = function (hint) {
  if (hint !== 'string' && hint !== NUMBER && hint !== 'default') throw TypeError('Incorrect hint');
  return toPrimitive(anObject(this), hint != NUMBER);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_defined.js":
/***/ (function(module, exports) {

// 7.2.1 RequireObjectCoercible(argument)
module.exports = function (it) {
  if (it == undefined) throw TypeError("Can't call method on  " + it);
  return it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_descriptors.js":
/***/ (function(module, exports, __webpack_require__) {

// Thank's IE8 for his funny defineProperty
module.exports = !__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return Object.defineProperty({}, 'a', { get: function () { return 7; } }).a != 7;
});


/***/ }),

/***/ "./node_modules/core-js/modules/_dom-create.js":
/***/ (function(module, exports, __webpack_require__) {

var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var document = __webpack_require__("./node_modules/core-js/modules/_global.js").document;
// typeof document.createElement is 'object' in old IE
var is = isObject(document) && isObject(document.createElement);
module.exports = function (it) {
  return is ? document.createElement(it) : {};
};


/***/ }),

/***/ "./node_modules/core-js/modules/_enum-bug-keys.js":
/***/ (function(module, exports) {

// IE 8- don't enum bug keys
module.exports = (
  'constructor,hasOwnProperty,isPrototypeOf,propertyIsEnumerable,toLocaleString,toString,valueOf'
).split(',');


/***/ }),

/***/ "./node_modules/core-js/modules/_enum-keys.js":
/***/ (function(module, exports, __webpack_require__) {

// all enumerable object keys, includes symbols
var getKeys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");
var gOPS = __webpack_require__("./node_modules/core-js/modules/_object-gops.js");
var pIE = __webpack_require__("./node_modules/core-js/modules/_object-pie.js");
module.exports = function (it) {
  var result = getKeys(it);
  var getSymbols = gOPS.f;
  if (getSymbols) {
    var symbols = getSymbols(it);
    var isEnum = pIE.f;
    var i = 0;
    var key;
    while (symbols.length > i) if (isEnum.call(it, key = symbols[i++])) result.push(key);
  } return result;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_export.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var core = __webpack_require__("./node_modules/core-js/modules/_core.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var PROTOTYPE = 'prototype';

var $export = function (type, name, source) {
  var IS_FORCED = type & $export.F;
  var IS_GLOBAL = type & $export.G;
  var IS_STATIC = type & $export.S;
  var IS_PROTO = type & $export.P;
  var IS_BIND = type & $export.B;
  var target = IS_GLOBAL ? global : IS_STATIC ? global[name] || (global[name] = {}) : (global[name] || {})[PROTOTYPE];
  var exports = IS_GLOBAL ? core : core[name] || (core[name] = {});
  var expProto = exports[PROTOTYPE] || (exports[PROTOTYPE] = {});
  var key, own, out, exp;
  if (IS_GLOBAL) source = name;
  for (key in source) {
    // contains in native
    own = !IS_FORCED && target && target[key] !== undefined;
    // export native or passed
    out = (own ? target : source)[key];
    // bind timers to global for call from export context
    exp = IS_BIND && own ? ctx(out, global) : IS_PROTO && typeof out == 'function' ? ctx(Function.call, out) : out;
    // extend global
    if (target) redefine(target, key, out, type & $export.U);
    // export
    if (exports[key] != out) hide(exports, key, exp);
    if (IS_PROTO && expProto[key] != out) expProto[key] = out;
  }
};
global.core = core;
// type bitmap
$export.F = 1;   // forced
$export.G = 2;   // global
$export.S = 4;   // static
$export.P = 8;   // proto
$export.B = 16;  // bind
$export.W = 32;  // wrap
$export.U = 64;  // safe
$export.R = 128; // real proto method for `library`
module.exports = $export;


/***/ }),

/***/ "./node_modules/core-js/modules/_fails-is-regexp.js":
/***/ (function(module, exports, __webpack_require__) {

var MATCH = __webpack_require__("./node_modules/core-js/modules/_wks.js")('match');
module.exports = function (KEY) {
  var re = /./;
  try {
    '/./'[KEY](re);
  } catch (e) {
    try {
      re[MATCH] = false;
      return !'/./'[KEY](re);
    } catch (f) { /* empty */ }
  } return true;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_fails.js":
/***/ (function(module, exports) {

module.exports = function (exec) {
  try {
    return !!exec();
  } catch (e) {
    return true;
  }
};


/***/ }),

/***/ "./node_modules/core-js/modules/_fix-re-wks.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
var wks = __webpack_require__("./node_modules/core-js/modules/_wks.js");

module.exports = function (KEY, length, exec) {
  var SYMBOL = wks(KEY);
  var fns = exec(defined, SYMBOL, ''[KEY]);
  var strfn = fns[0];
  var rxfn = fns[1];
  if (fails(function () {
    var O = {};
    O[SYMBOL] = function () { return 7; };
    return ''[KEY](O) != 7;
  })) {
    redefine(String.prototype, KEY, strfn);
    hide(RegExp.prototype, SYMBOL, length == 2
      // 21.2.5.8 RegExp.prototype[@@replace](string, replaceValue)
      // 21.2.5.11 RegExp.prototype[@@split](string, limit)
      ? function (string, arg) { return rxfn.call(string, this, arg); }
      // 21.2.5.6 RegExp.prototype[@@match](string)
      // 21.2.5.9 RegExp.prototype[@@search](string)
      : function (string) { return rxfn.call(string, this); }
    );
  }
};


/***/ }),

/***/ "./node_modules/core-js/modules/_flags.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 21.2.5.3 get RegExp.prototype.flags
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
module.exports = function () {
  var that = anObject(this);
  var result = '';
  if (that.global) result += 'g';
  if (that.ignoreCase) result += 'i';
  if (that.multiline) result += 'm';
  if (that.unicode) result += 'u';
  if (that.sticky) result += 'y';
  return result;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_flatten-into-array.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://tc39.github.io/proposal-flatMap/#sec-FlattenIntoArray
var isArray = __webpack_require__("./node_modules/core-js/modules/_is-array.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var IS_CONCAT_SPREADABLE = __webpack_require__("./node_modules/core-js/modules/_wks.js")('isConcatSpreadable');

function flattenIntoArray(target, original, source, sourceLen, start, depth, mapper, thisArg) {
  var targetIndex = start;
  var sourceIndex = 0;
  var mapFn = mapper ? ctx(mapper, thisArg, 3) : false;
  var element, spreadable;

  while (sourceIndex < sourceLen) {
    if (sourceIndex in source) {
      element = mapFn ? mapFn(source[sourceIndex], sourceIndex, original) : source[sourceIndex];

      spreadable = false;
      if (isObject(element)) {
        spreadable = element[IS_CONCAT_SPREADABLE];
        spreadable = spreadable !== undefined ? !!spreadable : isArray(element);
      }

      if (spreadable && depth > 0) {
        targetIndex = flattenIntoArray(target, original, element, toLength(element.length), targetIndex, depth - 1) - 1;
      } else {
        if (targetIndex >= 0x1fffffffffffff) throw TypeError();
        target[targetIndex] = element;
      }

      targetIndex++;
    }
    sourceIndex++;
  }
  return targetIndex;
}

module.exports = flattenIntoArray;


/***/ }),

/***/ "./node_modules/core-js/modules/_for-of.js":
/***/ (function(module, exports, __webpack_require__) {

var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var call = __webpack_require__("./node_modules/core-js/modules/_iter-call.js");
var isArrayIter = __webpack_require__("./node_modules/core-js/modules/_is-array-iter.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var getIterFn = __webpack_require__("./node_modules/core-js/modules/core.get-iterator-method.js");
var BREAK = {};
var RETURN = {};
var exports = module.exports = function (iterable, entries, fn, that, ITERATOR) {
  var iterFn = ITERATOR ? function () { return iterable; } : getIterFn(iterable);
  var f = ctx(fn, that, entries ? 2 : 1);
  var index = 0;
  var length, step, iterator, result;
  if (typeof iterFn != 'function') throw TypeError(iterable + ' is not iterable!');
  // fast case for arrays with default iterator
  if (isArrayIter(iterFn)) for (length = toLength(iterable.length); length > index; index++) {
    result = entries ? f(anObject(step = iterable[index])[0], step[1]) : f(iterable[index]);
    if (result === BREAK || result === RETURN) return result;
  } else for (iterator = iterFn.call(iterable); !(step = iterator.next()).done;) {
    result = call(iterator, f, step.value, entries);
    if (result === BREAK || result === RETURN) return result;
  }
};
exports.BREAK = BREAK;
exports.RETURN = RETURN;


/***/ }),

/***/ "./node_modules/core-js/modules/_global.js":
/***/ (function(module, exports) {

// https://github.com/zloirock/core-js/issues/86#issuecomment-115759028
var global = module.exports = typeof window != 'undefined' && window.Math == Math
  ? window : typeof self != 'undefined' && self.Math == Math ? self
  // eslint-disable-next-line no-new-func
  : Function('return this')();
if (typeof __g == 'number') __g = global; // eslint-disable-line no-undef


/***/ }),

/***/ "./node_modules/core-js/modules/_has.js":
/***/ (function(module, exports) {

var hasOwnProperty = {}.hasOwnProperty;
module.exports = function (it, key) {
  return hasOwnProperty.call(it, key);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_hide.js":
/***/ (function(module, exports, __webpack_require__) {

var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var createDesc = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");
module.exports = __webpack_require__("./node_modules/core-js/modules/_descriptors.js") ? function (object, key, value) {
  return dP.f(object, key, createDesc(1, value));
} : function (object, key, value) {
  object[key] = value;
  return object;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_html.js":
/***/ (function(module, exports, __webpack_require__) {

var document = __webpack_require__("./node_modules/core-js/modules/_global.js").document;
module.exports = document && document.documentElement;


/***/ }),

/***/ "./node_modules/core-js/modules/_ie8-dom-define.js":
/***/ (function(module, exports, __webpack_require__) {

module.exports = !__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && !__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return Object.defineProperty(__webpack_require__("./node_modules/core-js/modules/_dom-create.js")('div'), 'a', { get: function () { return 7; } }).a != 7;
});


/***/ }),

/***/ "./node_modules/core-js/modules/_inherit-if-required.js":
/***/ (function(module, exports, __webpack_require__) {

var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var setPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_set-proto.js").set;
module.exports = function (that, target, C) {
  var S = target.constructor;
  var P;
  if (S !== C && typeof S == 'function' && (P = S.prototype) !== C.prototype && isObject(P) && setPrototypeOf) {
    setPrototypeOf(that, P);
  } return that;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_invoke.js":
/***/ (function(module, exports) {

// fast apply, http://jsperf.lnkit.com/fast-apply/5
module.exports = function (fn, args, that) {
  var un = that === undefined;
  switch (args.length) {
    case 0: return un ? fn()
                      : fn.call(that);
    case 1: return un ? fn(args[0])
                      : fn.call(that, args[0]);
    case 2: return un ? fn(args[0], args[1])
                      : fn.call(that, args[0], args[1]);
    case 3: return un ? fn(args[0], args[1], args[2])
                      : fn.call(that, args[0], args[1], args[2]);
    case 4: return un ? fn(args[0], args[1], args[2], args[3])
                      : fn.call(that, args[0], args[1], args[2], args[3]);
  } return fn.apply(that, args);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iobject.js":
/***/ (function(module, exports, __webpack_require__) {

// fallback for non-array-like ES3 and non-enumerable old V8 strings
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
// eslint-disable-next-line no-prototype-builtins
module.exports = Object('z').propertyIsEnumerable(0) ? Object : function (it) {
  return cof(it) == 'String' ? it.split('') : Object(it);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_is-array-iter.js":
/***/ (function(module, exports, __webpack_require__) {

// check on default Array iterator
var Iterators = __webpack_require__("./node_modules/core-js/modules/_iterators.js");
var ITERATOR = __webpack_require__("./node_modules/core-js/modules/_wks.js")('iterator');
var ArrayProto = Array.prototype;

module.exports = function (it) {
  return it !== undefined && (Iterators.Array === it || ArrayProto[ITERATOR] === it);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_is-array.js":
/***/ (function(module, exports, __webpack_require__) {

// 7.2.2 IsArray(argument)
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
module.exports = Array.isArray || function isArray(arg) {
  return cof(arg) == 'Array';
};


/***/ }),

/***/ "./node_modules/core-js/modules/_is-integer.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.3 Number.isInteger(number)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var floor = Math.floor;
module.exports = function isInteger(it) {
  return !isObject(it) && isFinite(it) && floor(it) === it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_is-object.js":
/***/ (function(module, exports) {

module.exports = function (it) {
  return typeof it === 'object' ? it !== null : typeof it === 'function';
};


/***/ }),

/***/ "./node_modules/core-js/modules/_is-regexp.js":
/***/ (function(module, exports, __webpack_require__) {

// 7.2.8 IsRegExp(argument)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
var MATCH = __webpack_require__("./node_modules/core-js/modules/_wks.js")('match');
module.exports = function (it) {
  var isRegExp;
  return isObject(it) && ((isRegExp = it[MATCH]) !== undefined ? !!isRegExp : cof(it) == 'RegExp');
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iter-call.js":
/***/ (function(module, exports, __webpack_require__) {

// call something on iterator step with safe closing on error
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
module.exports = function (iterator, fn, value, entries) {
  try {
    return entries ? fn(anObject(value)[0], value[1]) : fn(value);
  // 7.4.6 IteratorClose(iterator, completion)
  } catch (e) {
    var ret = iterator['return'];
    if (ret !== undefined) anObject(ret.call(iterator));
    throw e;
  }
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iter-create.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var create = __webpack_require__("./node_modules/core-js/modules/_object-create.js");
var descriptor = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");
var setToStringTag = __webpack_require__("./node_modules/core-js/modules/_set-to-string-tag.js");
var IteratorPrototype = {};

// 25.1.2.1.1 %IteratorPrototype%[@@iterator]()
__webpack_require__("./node_modules/core-js/modules/_hide.js")(IteratorPrototype, __webpack_require__("./node_modules/core-js/modules/_wks.js")('iterator'), function () { return this; });

module.exports = function (Constructor, NAME, next) {
  Constructor.prototype = create(IteratorPrototype, { next: descriptor(1, next) });
  setToStringTag(Constructor, NAME + ' Iterator');
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iter-define.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var LIBRARY = __webpack_require__("./node_modules/core-js/modules/_library.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var Iterators = __webpack_require__("./node_modules/core-js/modules/_iterators.js");
var $iterCreate = __webpack_require__("./node_modules/core-js/modules/_iter-create.js");
var setToStringTag = __webpack_require__("./node_modules/core-js/modules/_set-to-string-tag.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var ITERATOR = __webpack_require__("./node_modules/core-js/modules/_wks.js")('iterator');
var BUGGY = !([].keys && 'next' in [].keys()); // Safari has buggy iterators w/o `next`
var FF_ITERATOR = '@@iterator';
var KEYS = 'keys';
var VALUES = 'values';

var returnThis = function () { return this; };

module.exports = function (Base, NAME, Constructor, next, DEFAULT, IS_SET, FORCED) {
  $iterCreate(Constructor, NAME, next);
  var getMethod = function (kind) {
    if (!BUGGY && kind in proto) return proto[kind];
    switch (kind) {
      case KEYS: return function keys() { return new Constructor(this, kind); };
      case VALUES: return function values() { return new Constructor(this, kind); };
    } return function entries() { return new Constructor(this, kind); };
  };
  var TAG = NAME + ' Iterator';
  var DEF_VALUES = DEFAULT == VALUES;
  var VALUES_BUG = false;
  var proto = Base.prototype;
  var $native = proto[ITERATOR] || proto[FF_ITERATOR] || DEFAULT && proto[DEFAULT];
  var $default = (!BUGGY && $native) || getMethod(DEFAULT);
  var $entries = DEFAULT ? !DEF_VALUES ? $default : getMethod('entries') : undefined;
  var $anyNative = NAME == 'Array' ? proto.entries || $native : $native;
  var methods, key, IteratorPrototype;
  // Fix native
  if ($anyNative) {
    IteratorPrototype = getPrototypeOf($anyNative.call(new Base()));
    if (IteratorPrototype !== Object.prototype && IteratorPrototype.next) {
      // Set @@toStringTag to native iterators
      setToStringTag(IteratorPrototype, TAG, true);
      // fix for some old engines
      if (!LIBRARY && !has(IteratorPrototype, ITERATOR)) hide(IteratorPrototype, ITERATOR, returnThis);
    }
  }
  // fix Array#{values, @@iterator}.name in V8 / FF
  if (DEF_VALUES && $native && $native.name !== VALUES) {
    VALUES_BUG = true;
    $default = function values() { return $native.call(this); };
  }
  // Define iterator
  if ((!LIBRARY || FORCED) && (BUGGY || VALUES_BUG || !proto[ITERATOR])) {
    hide(proto, ITERATOR, $default);
  }
  // Plug for library
  Iterators[NAME] = $default;
  Iterators[TAG] = returnThis;
  if (DEFAULT) {
    methods = {
      values: DEF_VALUES ? $default : getMethod(VALUES),
      keys: IS_SET ? $default : getMethod(KEYS),
      entries: $entries
    };
    if (FORCED) for (key in methods) {
      if (!(key in proto)) redefine(proto, key, methods[key]);
    } else $export($export.P + $export.F * (BUGGY || VALUES_BUG), NAME, methods);
  }
  return methods;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iter-detect.js":
/***/ (function(module, exports, __webpack_require__) {

var ITERATOR = __webpack_require__("./node_modules/core-js/modules/_wks.js")('iterator');
var SAFE_CLOSING = false;

try {
  var riter = [7][ITERATOR]();
  riter['return'] = function () { SAFE_CLOSING = true; };
  // eslint-disable-next-line no-throw-literal
  Array.from(riter, function () { throw 2; });
} catch (e) { /* empty */ }

module.exports = function (exec, skipClosing) {
  if (!skipClosing && !SAFE_CLOSING) return false;
  var safe = false;
  try {
    var arr = [7];
    var iter = arr[ITERATOR]();
    iter.next = function () { return { done: safe = true }; };
    arr[ITERATOR] = function () { return iter; };
    exec(arr);
  } catch (e) { /* empty */ }
  return safe;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iter-step.js":
/***/ (function(module, exports) {

module.exports = function (done, value) {
  return { value: value, done: !!done };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_iterators.js":
/***/ (function(module, exports) {

module.exports = {};


/***/ }),

/***/ "./node_modules/core-js/modules/_library.js":
/***/ (function(module, exports) {

module.exports = false;


/***/ }),

/***/ "./node_modules/core-js/modules/_math-expm1.js":
/***/ (function(module, exports) {

// 20.2.2.14 Math.expm1(x)
var $expm1 = Math.expm1;
module.exports = (!$expm1
  // Old FF bug
  || $expm1(10) > 22025.465794806719 || $expm1(10) < 22025.4657948067165168
  // Tor Browser bug
  || $expm1(-2e-17) != -2e-17
) ? function expm1(x) {
  return (x = +x) == 0 ? x : x > -1e-6 && x < 1e-6 ? x + x * x / 2 : Math.exp(x) - 1;
} : $expm1;


/***/ }),

/***/ "./node_modules/core-js/modules/_math-fround.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.16 Math.fround(x)
var sign = __webpack_require__("./node_modules/core-js/modules/_math-sign.js");
var pow = Math.pow;
var EPSILON = pow(2, -52);
var EPSILON32 = pow(2, -23);
var MAX32 = pow(2, 127) * (2 - EPSILON32);
var MIN32 = pow(2, -126);

var roundTiesToEven = function (n) {
  return n + 1 / EPSILON - 1 / EPSILON;
};

module.exports = Math.fround || function fround(x) {
  var $abs = Math.abs(x);
  var $sign = sign(x);
  var a, result;
  if ($abs < MIN32) return $sign * roundTiesToEven($abs / MIN32 / EPSILON32) * MIN32 * EPSILON32;
  a = (1 + EPSILON32 / EPSILON) * $abs;
  result = a - (a - $abs);
  // eslint-disable-next-line no-self-compare
  if (result > MAX32 || result != result) return $sign * Infinity;
  return $sign * result;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_math-log1p.js":
/***/ (function(module, exports) {

// 20.2.2.20 Math.log1p(x)
module.exports = Math.log1p || function log1p(x) {
  return (x = +x) > -1e-8 && x < 1e-8 ? x - x * x / 2 : Math.log(1 + x);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_math-scale.js":
/***/ (function(module, exports) {

// https://rwaldron.github.io/proposal-math-extensions/
module.exports = Math.scale || function scale(x, inLow, inHigh, outLow, outHigh) {
  if (
    arguments.length === 0
      // eslint-disable-next-line no-self-compare
      || x != x
      // eslint-disable-next-line no-self-compare
      || inLow != inLow
      // eslint-disable-next-line no-self-compare
      || inHigh != inHigh
      // eslint-disable-next-line no-self-compare
      || outLow != outLow
      // eslint-disable-next-line no-self-compare
      || outHigh != outHigh
  ) return NaN;
  if (x === Infinity || x === -Infinity) return x;
  return (x - inLow) * (outHigh - outLow) / (inHigh - inLow) + outLow;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_math-sign.js":
/***/ (function(module, exports) {

// 20.2.2.28 Math.sign(x)
module.exports = Math.sign || function sign(x) {
  // eslint-disable-next-line no-self-compare
  return (x = +x) == 0 || x != x ? x : x < 0 ? -1 : 1;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_meta.js":
/***/ (function(module, exports, __webpack_require__) {

var META = __webpack_require__("./node_modules/core-js/modules/_uid.js")('meta');
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var setDesc = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var id = 0;
var isExtensible = Object.isExtensible || function () {
  return true;
};
var FREEZE = !__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return isExtensible(Object.preventExtensions({}));
});
var setMeta = function (it) {
  setDesc(it, META, { value: {
    i: 'O' + ++id, // object ID
    w: {}          // weak collections IDs
  } });
};
var fastKey = function (it, create) {
  // return primitive with prefix
  if (!isObject(it)) return typeof it == 'symbol' ? it : (typeof it == 'string' ? 'S' : 'P') + it;
  if (!has(it, META)) {
    // can't set metadata to uncaught frozen object
    if (!isExtensible(it)) return 'F';
    // not necessary to add metadata
    if (!create) return 'E';
    // add missing metadata
    setMeta(it);
  // return object ID
  } return it[META].i;
};
var getWeak = function (it, create) {
  if (!has(it, META)) {
    // can't set metadata to uncaught frozen object
    if (!isExtensible(it)) return true;
    // not necessary to add metadata
    if (!create) return false;
    // add missing metadata
    setMeta(it);
  // return hash weak collections IDs
  } return it[META].w;
};
// add metadata on freeze-family methods calling
var onFreeze = function (it) {
  if (FREEZE && meta.NEED && isExtensible(it) && !has(it, META)) setMeta(it);
  return it;
};
var meta = module.exports = {
  KEY: META,
  NEED: false,
  fastKey: fastKey,
  getWeak: getWeak,
  onFreeze: onFreeze
};


/***/ }),

/***/ "./node_modules/core-js/modules/_metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var Map = __webpack_require__("./node_modules/core-js/modules/es6.map.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var shared = __webpack_require__("./node_modules/core-js/modules/_shared.js")('metadata');
var store = shared.store || (shared.store = new (__webpack_require__("./node_modules/core-js/modules/es6.weak-map.js"))());

var getOrCreateMetadataMap = function (target, targetKey, create) {
  var targetMetadata = store.get(target);
  if (!targetMetadata) {
    if (!create) return undefined;
    store.set(target, targetMetadata = new Map());
  }
  var keyMetadata = targetMetadata.get(targetKey);
  if (!keyMetadata) {
    if (!create) return undefined;
    targetMetadata.set(targetKey, keyMetadata = new Map());
  } return keyMetadata;
};
var ordinaryHasOwnMetadata = function (MetadataKey, O, P) {
  var metadataMap = getOrCreateMetadataMap(O, P, false);
  return metadataMap === undefined ? false : metadataMap.has(MetadataKey);
};
var ordinaryGetOwnMetadata = function (MetadataKey, O, P) {
  var metadataMap = getOrCreateMetadataMap(O, P, false);
  return metadataMap === undefined ? undefined : metadataMap.get(MetadataKey);
};
var ordinaryDefineOwnMetadata = function (MetadataKey, MetadataValue, O, P) {
  getOrCreateMetadataMap(O, P, true).set(MetadataKey, MetadataValue);
};
var ordinaryOwnMetadataKeys = function (target, targetKey) {
  var metadataMap = getOrCreateMetadataMap(target, targetKey, false);
  var keys = [];
  if (metadataMap) metadataMap.forEach(function (_, key) { keys.push(key); });
  return keys;
};
var toMetaKey = function (it) {
  return it === undefined || typeof it == 'symbol' ? it : String(it);
};
var exp = function (O) {
  $export($export.S, 'Reflect', O);
};

module.exports = {
  store: store,
  map: getOrCreateMetadataMap,
  has: ordinaryHasOwnMetadata,
  get: ordinaryGetOwnMetadata,
  set: ordinaryDefineOwnMetadata,
  keys: ordinaryOwnMetadataKeys,
  key: toMetaKey,
  exp: exp
};


/***/ }),

/***/ "./node_modules/core-js/modules/_microtask.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var macrotask = __webpack_require__("./node_modules/core-js/modules/_task.js").set;
var Observer = global.MutationObserver || global.WebKitMutationObserver;
var process = global.process;
var Promise = global.Promise;
var isNode = __webpack_require__("./node_modules/core-js/modules/_cof.js")(process) == 'process';

module.exports = function () {
  var head, last, notify;

  var flush = function () {
    var parent, fn;
    if (isNode && (parent = process.domain)) parent.exit();
    while (head) {
      fn = head.fn;
      head = head.next;
      try {
        fn();
      } catch (e) {
        if (head) notify();
        else last = undefined;
        throw e;
      }
    } last = undefined;
    if (parent) parent.enter();
  };

  // Node.js
  if (isNode) {
    notify = function () {
      process.nextTick(flush);
    };
  // browsers with MutationObserver, except iOS Safari - https://github.com/zloirock/core-js/issues/339
  } else if (Observer && !(global.navigator && global.navigator.standalone)) {
    var toggle = true;
    var node = document.createTextNode('');
    new Observer(flush).observe(node, { characterData: true }); // eslint-disable-line no-new
    notify = function () {
      node.data = toggle = !toggle;
    };
  // environments with maybe non-completely correct, but existent Promise
  } else if (Promise && Promise.resolve) {
    var promise = Promise.resolve();
    notify = function () {
      promise.then(flush);
    };
  // for other environments - macrotask based on:
  // - setImmediate
  // - MessageChannel
  // - window.postMessag
  // - onreadystatechange
  // - setTimeout
  } else {
    notify = function () {
      // strange IE + webpack dev server bug - use .call(global)
      macrotask.call(global, flush);
    };
  }

  return function (fn) {
    var task = { fn: fn, next: undefined };
    if (last) last.next = task;
    if (!head) {
      head = task;
      notify();
    } last = task;
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_new-promise-capability.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 25.4.1.5 NewPromiseCapability(C)
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");

function PromiseCapability(C) {
  var resolve, reject;
  this.promise = new C(function ($$resolve, $$reject) {
    if (resolve !== undefined || reject !== undefined) throw TypeError('Bad Promise constructor');
    resolve = $$resolve;
    reject = $$reject;
  });
  this.resolve = aFunction(resolve);
  this.reject = aFunction(reject);
}

module.exports.f = function (C) {
  return new PromiseCapability(C);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-assign.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 19.1.2.1 Object.assign(target, source, ...)
var getKeys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");
var gOPS = __webpack_require__("./node_modules/core-js/modules/_object-gops.js");
var pIE = __webpack_require__("./node_modules/core-js/modules/_object-pie.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var IObject = __webpack_require__("./node_modules/core-js/modules/_iobject.js");
var $assign = Object.assign;

// should work with symbols and should have deterministic property order (V8 bug)
module.exports = !$assign || __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  var A = {};
  var B = {};
  // eslint-disable-next-line no-undef
  var S = Symbol();
  var K = 'abcdefghijklmnopqrst';
  A[S] = 7;
  K.split('').forEach(function (k) { B[k] = k; });
  return $assign({}, A)[S] != 7 || Object.keys($assign({}, B)).join('') != K;
}) ? function assign(target, source) { // eslint-disable-line no-unused-vars
  var T = toObject(target);
  var aLen = arguments.length;
  var index = 1;
  var getSymbols = gOPS.f;
  var isEnum = pIE.f;
  while (aLen > index) {
    var S = IObject(arguments[index++]);
    var keys = getSymbols ? getKeys(S).concat(getSymbols(S)) : getKeys(S);
    var length = keys.length;
    var j = 0;
    var key;
    while (length > j) if (isEnum.call(S, key = keys[j++])) T[key] = S[key];
  } return T;
} : $assign;


/***/ }),

/***/ "./node_modules/core-js/modules/_object-create.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.2 / 15.2.3.5 Object.create(O [, Properties])
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var dPs = __webpack_require__("./node_modules/core-js/modules/_object-dps.js");
var enumBugKeys = __webpack_require__("./node_modules/core-js/modules/_enum-bug-keys.js");
var IE_PROTO = __webpack_require__("./node_modules/core-js/modules/_shared-key.js")('IE_PROTO');
var Empty = function () { /* empty */ };
var PROTOTYPE = 'prototype';

// Create object with fake `null` prototype: use iframe Object with cleared prototype
var createDict = function () {
  // Thrash, waste and sodomy: IE GC bug
  var iframe = __webpack_require__("./node_modules/core-js/modules/_dom-create.js")('iframe');
  var i = enumBugKeys.length;
  var lt = '<';
  var gt = '>';
  var iframeDocument;
  iframe.style.display = 'none';
  __webpack_require__("./node_modules/core-js/modules/_html.js").appendChild(iframe);
  iframe.src = 'javascript:'; // eslint-disable-line no-script-url
  // createDict = iframe.contentWindow.Object;
  // html.removeChild(iframe);
  iframeDocument = iframe.contentWindow.document;
  iframeDocument.open();
  iframeDocument.write(lt + 'script' + gt + 'document.F=Object' + lt + '/script' + gt);
  iframeDocument.close();
  createDict = iframeDocument.F;
  while (i--) delete createDict[PROTOTYPE][enumBugKeys[i]];
  return createDict();
};

module.exports = Object.create || function create(O, Properties) {
  var result;
  if (O !== null) {
    Empty[PROTOTYPE] = anObject(O);
    result = new Empty();
    Empty[PROTOTYPE] = null;
    // add "__proto__" for Object.getPrototypeOf polyfill
    result[IE_PROTO] = O;
  } else result = createDict();
  return Properties === undefined ? result : dPs(result, Properties);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-dp.js":
/***/ (function(module, exports, __webpack_require__) {

var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var IE8_DOM_DEFINE = __webpack_require__("./node_modules/core-js/modules/_ie8-dom-define.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var dP = Object.defineProperty;

exports.f = __webpack_require__("./node_modules/core-js/modules/_descriptors.js") ? Object.defineProperty : function defineProperty(O, P, Attributes) {
  anObject(O);
  P = toPrimitive(P, true);
  anObject(Attributes);
  if (IE8_DOM_DEFINE) try {
    return dP(O, P, Attributes);
  } catch (e) { /* empty */ }
  if ('get' in Attributes || 'set' in Attributes) throw TypeError('Accessors not supported!');
  if ('value' in Attributes) O[P] = Attributes.value;
  return O;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-dps.js":
/***/ (function(module, exports, __webpack_require__) {

var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var getKeys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");

module.exports = __webpack_require__("./node_modules/core-js/modules/_descriptors.js") ? Object.defineProperties : function defineProperties(O, Properties) {
  anObject(O);
  var keys = getKeys(Properties);
  var length = keys.length;
  var i = 0;
  var P;
  while (length > i) dP.f(O, P = keys[i++], Properties[P]);
  return O;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-forced-pam.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// Forced replacement prototype accessors methods
module.exports = __webpack_require__("./node_modules/core-js/modules/_library.js") || !__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  var K = Math.random();
  // In FF throws only define methods
  // eslint-disable-next-line no-undef, no-useless-call
  __defineSetter__.call(null, K, function () { /* empty */ });
  delete __webpack_require__("./node_modules/core-js/modules/_global.js")[K];
});


/***/ }),

/***/ "./node_modules/core-js/modules/_object-gopd.js":
/***/ (function(module, exports, __webpack_require__) {

var pIE = __webpack_require__("./node_modules/core-js/modules/_object-pie.js");
var createDesc = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var IE8_DOM_DEFINE = __webpack_require__("./node_modules/core-js/modules/_ie8-dom-define.js");
var gOPD = Object.getOwnPropertyDescriptor;

exports.f = __webpack_require__("./node_modules/core-js/modules/_descriptors.js") ? gOPD : function getOwnPropertyDescriptor(O, P) {
  O = toIObject(O);
  P = toPrimitive(P, true);
  if (IE8_DOM_DEFINE) try {
    return gOPD(O, P);
  } catch (e) { /* empty */ }
  if (has(O, P)) return createDesc(!pIE.f.call(O, P), O[P]);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-gopn-ext.js":
/***/ (function(module, exports, __webpack_require__) {

// fallback for IE11 buggy Object.getOwnPropertyNames with iframe and window
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var gOPN = __webpack_require__("./node_modules/core-js/modules/_object-gopn.js").f;
var toString = {}.toString;

var windowNames = typeof window == 'object' && window && Object.getOwnPropertyNames
  ? Object.getOwnPropertyNames(window) : [];

var getWindowNames = function (it) {
  try {
    return gOPN(it);
  } catch (e) {
    return windowNames.slice();
  }
};

module.exports.f = function getOwnPropertyNames(it) {
  return windowNames && toString.call(it) == '[object Window]' ? getWindowNames(it) : gOPN(toIObject(it));
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-gopn.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.7 / 15.2.3.4 Object.getOwnPropertyNames(O)
var $keys = __webpack_require__("./node_modules/core-js/modules/_object-keys-internal.js");
var hiddenKeys = __webpack_require__("./node_modules/core-js/modules/_enum-bug-keys.js").concat('length', 'prototype');

exports.f = Object.getOwnPropertyNames || function getOwnPropertyNames(O) {
  return $keys(O, hiddenKeys);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-gops.js":
/***/ (function(module, exports) {

exports.f = Object.getOwnPropertySymbols;


/***/ }),

/***/ "./node_modules/core-js/modules/_object-gpo.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.9 / 15.2.3.2 Object.getPrototypeOf(O)
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var IE_PROTO = __webpack_require__("./node_modules/core-js/modules/_shared-key.js")('IE_PROTO');
var ObjectProto = Object.prototype;

module.exports = Object.getPrototypeOf || function (O) {
  O = toObject(O);
  if (has(O, IE_PROTO)) return O[IE_PROTO];
  if (typeof O.constructor == 'function' && O instanceof O.constructor) {
    return O.constructor.prototype;
  } return O instanceof Object ? ObjectProto : null;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-keys-internal.js":
/***/ (function(module, exports, __webpack_require__) {

var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var arrayIndexOf = __webpack_require__("./node_modules/core-js/modules/_array-includes.js")(false);
var IE_PROTO = __webpack_require__("./node_modules/core-js/modules/_shared-key.js")('IE_PROTO');

module.exports = function (object, names) {
  var O = toIObject(object);
  var i = 0;
  var result = [];
  var key;
  for (key in O) if (key != IE_PROTO) has(O, key) && result.push(key);
  // Don't enum bug & hidden keys
  while (names.length > i) if (has(O, key = names[i++])) {
    ~arrayIndexOf(result, key) || result.push(key);
  }
  return result;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-keys.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.14 / 15.2.3.14 Object.keys(O)
var $keys = __webpack_require__("./node_modules/core-js/modules/_object-keys-internal.js");
var enumBugKeys = __webpack_require__("./node_modules/core-js/modules/_enum-bug-keys.js");

module.exports = Object.keys || function keys(O) {
  return $keys(O, enumBugKeys);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-pie.js":
/***/ (function(module, exports) {

exports.f = {}.propertyIsEnumerable;


/***/ }),

/***/ "./node_modules/core-js/modules/_object-sap.js":
/***/ (function(module, exports, __webpack_require__) {

// most Object methods by ES6 should accept primitives
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var core = __webpack_require__("./node_modules/core-js/modules/_core.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
module.exports = function (KEY, exec) {
  var fn = (core.Object || {})[KEY] || Object[KEY];
  var exp = {};
  exp[KEY] = exec(fn);
  $export($export.S + $export.F * fails(function () { fn(1); }), 'Object', exp);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_object-to-array.js":
/***/ (function(module, exports, __webpack_require__) {

var getKeys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var isEnum = __webpack_require__("./node_modules/core-js/modules/_object-pie.js").f;
module.exports = function (isEntries) {
  return function (it) {
    var O = toIObject(it);
    var keys = getKeys(O);
    var length = keys.length;
    var i = 0;
    var result = [];
    var key;
    while (length > i) if (isEnum.call(O, key = keys[i++])) {
      result.push(isEntries ? [key, O[key]] : O[key]);
    } return result;
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_own-keys.js":
/***/ (function(module, exports, __webpack_require__) {

// all object keys, includes non-enumerable and symbols
var gOPN = __webpack_require__("./node_modules/core-js/modules/_object-gopn.js");
var gOPS = __webpack_require__("./node_modules/core-js/modules/_object-gops.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var Reflect = __webpack_require__("./node_modules/core-js/modules/_global.js").Reflect;
module.exports = Reflect && Reflect.ownKeys || function ownKeys(it) {
  var keys = gOPN.f(anObject(it));
  var getSymbols = gOPS.f;
  return getSymbols ? keys.concat(getSymbols(it)) : keys;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_parse-float.js":
/***/ (function(module, exports, __webpack_require__) {

var $parseFloat = __webpack_require__("./node_modules/core-js/modules/_global.js").parseFloat;
var $trim = __webpack_require__("./node_modules/core-js/modules/_string-trim.js").trim;

module.exports = 1 / $parseFloat(__webpack_require__("./node_modules/core-js/modules/_string-ws.js") + '-0') !== -Infinity ? function parseFloat(str) {
  var string = $trim(String(str), 3);
  var result = $parseFloat(string);
  return result === 0 && string.charAt(0) == '-' ? -0 : result;
} : $parseFloat;


/***/ }),

/***/ "./node_modules/core-js/modules/_parse-int.js":
/***/ (function(module, exports, __webpack_require__) {

var $parseInt = __webpack_require__("./node_modules/core-js/modules/_global.js").parseInt;
var $trim = __webpack_require__("./node_modules/core-js/modules/_string-trim.js").trim;
var ws = __webpack_require__("./node_modules/core-js/modules/_string-ws.js");
var hex = /^[-+]?0[xX]/;

module.exports = $parseInt(ws + '08') !== 8 || $parseInt(ws + '0x16') !== 22 ? function parseInt(str, radix) {
  var string = $trim(String(str), 3);
  return $parseInt(string, (radix >>> 0) || (hex.test(string) ? 16 : 10));
} : $parseInt;


/***/ }),

/***/ "./node_modules/core-js/modules/_perform.js":
/***/ (function(module, exports) {

module.exports = function (exec) {
  try {
    return { e: false, v: exec() };
  } catch (e) {
    return { e: true, v: e };
  }
};


/***/ }),

/***/ "./node_modules/core-js/modules/_promise-resolve.js":
/***/ (function(module, exports, __webpack_require__) {

var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var newPromiseCapability = __webpack_require__("./node_modules/core-js/modules/_new-promise-capability.js");

module.exports = function (C, x) {
  anObject(C);
  if (isObject(x) && x.constructor === C) return x;
  var promiseCapability = newPromiseCapability.f(C);
  var resolve = promiseCapability.resolve;
  resolve(x);
  return promiseCapability.promise;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_property-desc.js":
/***/ (function(module, exports) {

module.exports = function (bitmap, value) {
  return {
    enumerable: !(bitmap & 1),
    configurable: !(bitmap & 2),
    writable: !(bitmap & 4),
    value: value
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_redefine-all.js":
/***/ (function(module, exports, __webpack_require__) {

var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
module.exports = function (target, src, safe) {
  for (var key in src) redefine(target, key, src[key], safe);
  return target;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_redefine.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var SRC = __webpack_require__("./node_modules/core-js/modules/_uid.js")('src');
var TO_STRING = 'toString';
var $toString = Function[TO_STRING];
var TPL = ('' + $toString).split(TO_STRING);

__webpack_require__("./node_modules/core-js/modules/_core.js").inspectSource = function (it) {
  return $toString.call(it);
};

(module.exports = function (O, key, val, safe) {
  var isFunction = typeof val == 'function';
  if (isFunction) has(val, 'name') || hide(val, 'name', key);
  if (O[key] === val) return;
  if (isFunction) has(val, SRC) || hide(val, SRC, O[key] ? '' + O[key] : TPL.join(String(key)));
  if (O === global) {
    O[key] = val;
  } else if (!safe) {
    delete O[key];
    hide(O, key, val);
  } else if (O[key]) {
    O[key] = val;
  } else {
    hide(O, key, val);
  }
// add fake Function#toString for correct work wrapped methods / constructors with methods like LoDash isNative
})(Function.prototype, TO_STRING, function toString() {
  return typeof this == 'function' && this[SRC] || $toString.call(this);
});


/***/ }),

/***/ "./node_modules/core-js/modules/_replacer.js":
/***/ (function(module, exports) {

module.exports = function (regExp, replace) {
  var replacer = replace === Object(replace) ? function (part) {
    return replace[part];
  } : replace;
  return function (it) {
    return String(it).replace(regExp, replacer);
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_same-value.js":
/***/ (function(module, exports) {

// 7.2.9 SameValue(x, y)
module.exports = Object.is || function is(x, y) {
  // eslint-disable-next-line no-self-compare
  return x === y ? x !== 0 || 1 / x === 1 / y : x != x && y != y;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_set-collection-from.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://tc39.github.io/proposal-setmap-offrom/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");

module.exports = function (COLLECTION) {
  $export($export.S, COLLECTION, { from: function from(source /* , mapFn, thisArg */) {
    var mapFn = arguments[1];
    var mapping, A, n, cb;
    aFunction(this);
    mapping = mapFn !== undefined;
    if (mapping) aFunction(mapFn);
    if (source == undefined) return new this();
    A = [];
    if (mapping) {
      n = 0;
      cb = ctx(mapFn, arguments[2], 2);
      forOf(source, false, function (nextItem) {
        A.push(cb(nextItem, n++));
      });
    } else {
      forOf(source, false, A.push, A);
    }
    return new this(A);
  } });
};


/***/ }),

/***/ "./node_modules/core-js/modules/_set-collection-of.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://tc39.github.io/proposal-setmap-offrom/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

module.exports = function (COLLECTION) {
  $export($export.S, COLLECTION, { of: function of() {
    var length = arguments.length;
    var A = new Array(length);
    while (length--) A[length] = arguments[length];
    return new this(A);
  } });
};


/***/ }),

/***/ "./node_modules/core-js/modules/_set-proto.js":
/***/ (function(module, exports, __webpack_require__) {

// Works with __proto__ only. Old v8 can't work with null proto objects.
/* eslint-disable no-proto */
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var check = function (O, proto) {
  anObject(O);
  if (!isObject(proto) && proto !== null) throw TypeError(proto + ": can't set as prototype!");
};
module.exports = {
  set: Object.setPrototypeOf || ('__proto__' in {} ? // eslint-disable-line
    function (test, buggy, set) {
      try {
        set = __webpack_require__("./node_modules/core-js/modules/_ctx.js")(Function.call, __webpack_require__("./node_modules/core-js/modules/_object-gopd.js").f(Object.prototype, '__proto__').set, 2);
        set(test, []);
        buggy = !(test instanceof Array);
      } catch (e) { buggy = true; }
      return function setPrototypeOf(O, proto) {
        check(O, proto);
        if (buggy) O.__proto__ = proto;
        else set(O, proto);
        return O;
      };
    }({}, false) : undefined),
  check: check
};


/***/ }),

/***/ "./node_modules/core-js/modules/_set-species.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var DESCRIPTORS = __webpack_require__("./node_modules/core-js/modules/_descriptors.js");
var SPECIES = __webpack_require__("./node_modules/core-js/modules/_wks.js")('species');

module.exports = function (KEY) {
  var C = global[KEY];
  if (DESCRIPTORS && C && !C[SPECIES]) dP.f(C, SPECIES, {
    configurable: true,
    get: function () { return this; }
  });
};


/***/ }),

/***/ "./node_modules/core-js/modules/_set-to-string-tag.js":
/***/ (function(module, exports, __webpack_require__) {

var def = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var TAG = __webpack_require__("./node_modules/core-js/modules/_wks.js")('toStringTag');

module.exports = function (it, tag, stat) {
  if (it && !has(it = stat ? it : it.prototype, TAG)) def(it, TAG, { configurable: true, value: tag });
};


/***/ }),

/***/ "./node_modules/core-js/modules/_shared-key.js":
/***/ (function(module, exports, __webpack_require__) {

var shared = __webpack_require__("./node_modules/core-js/modules/_shared.js")('keys');
var uid = __webpack_require__("./node_modules/core-js/modules/_uid.js");
module.exports = function (key) {
  return shared[key] || (shared[key] = uid(key));
};


/***/ }),

/***/ "./node_modules/core-js/modules/_shared.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var SHARED = '__core-js_shared__';
var store = global[SHARED] || (global[SHARED] = {});
module.exports = function (key) {
  return store[key] || (store[key] = {});
};


/***/ }),

/***/ "./node_modules/core-js/modules/_species-constructor.js":
/***/ (function(module, exports, __webpack_require__) {

// 7.3.20 SpeciesConstructor(O, defaultConstructor)
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var SPECIES = __webpack_require__("./node_modules/core-js/modules/_wks.js")('species');
module.exports = function (O, D) {
  var C = anObject(O).constructor;
  var S;
  return C === undefined || (S = anObject(C)[SPECIES]) == undefined ? D : aFunction(S);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_strict-method.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");

module.exports = function (method, arg) {
  return !!method && fails(function () {
    // eslint-disable-next-line no-useless-call
    arg ? method.call(null, function () { /* empty */ }, 1) : method.call(null);
  });
};


/***/ }),

/***/ "./node_modules/core-js/modules/_string-at.js":
/***/ (function(module, exports, __webpack_require__) {

var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
// true  -> String#at
// false -> String#codePointAt
module.exports = function (TO_STRING) {
  return function (that, pos) {
    var s = String(defined(that));
    var i = toInteger(pos);
    var l = s.length;
    var a, b;
    if (i < 0 || i >= l) return TO_STRING ? '' : undefined;
    a = s.charCodeAt(i);
    return a < 0xd800 || a > 0xdbff || i + 1 === l || (b = s.charCodeAt(i + 1)) < 0xdc00 || b > 0xdfff
      ? TO_STRING ? s.charAt(i) : a
      : TO_STRING ? s.slice(i, i + 2) : (a - 0xd800 << 10) + (b - 0xdc00) + 0x10000;
  };
};


/***/ }),

/***/ "./node_modules/core-js/modules/_string-context.js":
/***/ (function(module, exports, __webpack_require__) {

// helper for String#{startsWith, endsWith, includes}
var isRegExp = __webpack_require__("./node_modules/core-js/modules/_is-regexp.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");

module.exports = function (that, searchString, NAME) {
  if (isRegExp(searchString)) throw TypeError('String#' + NAME + " doesn't accept regex!");
  return String(defined(that));
};


/***/ }),

/***/ "./node_modules/core-js/modules/_string-html.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
var quot = /"/g;
// B.2.3.2.1 CreateHTML(string, tag, attribute, value)
var createHTML = function (string, tag, attribute, value) {
  var S = String(defined(string));
  var p1 = '<' + tag;
  if (attribute !== '') p1 += ' ' + attribute + '="' + String(value).replace(quot, '&quot;') + '"';
  return p1 + '>' + S + '</' + tag + '>';
};
module.exports = function (NAME, exec) {
  var O = {};
  O[NAME] = exec(createHTML);
  $export($export.P + $export.F * fails(function () {
    var test = ''[NAME]('"');
    return test !== test.toLowerCase() || test.split('"').length > 3;
  }), 'String', O);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_string-pad.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/tc39/proposal-string-pad-start-end
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var repeat = __webpack_require__("./node_modules/core-js/modules/_string-repeat.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");

module.exports = function (that, maxLength, fillString, left) {
  var S = String(defined(that));
  var stringLength = S.length;
  var fillStr = fillString === undefined ? ' ' : String(fillString);
  var intMaxLength = toLength(maxLength);
  if (intMaxLength <= stringLength || fillStr == '') return S;
  var fillLen = intMaxLength - stringLength;
  var stringFiller = repeat.call(fillStr, Math.ceil(fillLen / fillStr.length));
  if (stringFiller.length > fillLen) stringFiller = stringFiller.slice(0, fillLen);
  return left ? stringFiller + S : S + stringFiller;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_string-repeat.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");

module.exports = function repeat(count) {
  var str = String(defined(this));
  var res = '';
  var n = toInteger(count);
  if (n < 0 || n == Infinity) throw RangeError("Count can't be negative");
  for (;n > 0; (n >>>= 1) && (str += str)) if (n & 1) res += str;
  return res;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_string-trim.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var spaces = __webpack_require__("./node_modules/core-js/modules/_string-ws.js");
var space = '[' + spaces + ']';
var non = '\u200b\u0085';
var ltrim = RegExp('^' + space + space + '*');
var rtrim = RegExp(space + space + '*$');

var exporter = function (KEY, exec, ALIAS) {
  var exp = {};
  var FORCE = fails(function () {
    return !!spaces[KEY]() || non[KEY]() != non;
  });
  var fn = exp[KEY] = FORCE ? exec(trim) : spaces[KEY];
  if (ALIAS) exp[ALIAS] = fn;
  $export($export.P + $export.F * FORCE, 'String', exp);
};

// 1 -> String#trimLeft
// 2 -> String#trimRight
// 3 -> String#trim
var trim = exporter.trim = function (string, TYPE) {
  string = String(defined(string));
  if (TYPE & 1) string = string.replace(ltrim, '');
  if (TYPE & 2) string = string.replace(rtrim, '');
  return string;
};

module.exports = exporter;


/***/ }),

/***/ "./node_modules/core-js/modules/_string-ws.js":
/***/ (function(module, exports) {

module.exports = '\x09\x0A\x0B\x0C\x0D\x20\xA0\u1680\u180E\u2000\u2001\u2002\u2003' +
  '\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u3000\u2028\u2029\uFEFF';


/***/ }),

/***/ "./node_modules/core-js/modules/_task.js":
/***/ (function(module, exports, __webpack_require__) {

var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var invoke = __webpack_require__("./node_modules/core-js/modules/_invoke.js");
var html = __webpack_require__("./node_modules/core-js/modules/_html.js");
var cel = __webpack_require__("./node_modules/core-js/modules/_dom-create.js");
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var process = global.process;
var setTask = global.setImmediate;
var clearTask = global.clearImmediate;
var MessageChannel = global.MessageChannel;
var Dispatch = global.Dispatch;
var counter = 0;
var queue = {};
var ONREADYSTATECHANGE = 'onreadystatechange';
var defer, channel, port;
var run = function () {
  var id = +this;
  // eslint-disable-next-line no-prototype-builtins
  if (queue.hasOwnProperty(id)) {
    var fn = queue[id];
    delete queue[id];
    fn();
  }
};
var listener = function (event) {
  run.call(event.data);
};
// Node.js 0.9+ & IE10+ has setImmediate, otherwise:
if (!setTask || !clearTask) {
  setTask = function setImmediate(fn) {
    var args = [];
    var i = 1;
    while (arguments.length > i) args.push(arguments[i++]);
    queue[++counter] = function () {
      // eslint-disable-next-line no-new-func
      invoke(typeof fn == 'function' ? fn : Function(fn), args);
    };
    defer(counter);
    return counter;
  };
  clearTask = function clearImmediate(id) {
    delete queue[id];
  };
  // Node.js 0.8-
  if (__webpack_require__("./node_modules/core-js/modules/_cof.js")(process) == 'process') {
    defer = function (id) {
      process.nextTick(ctx(run, id, 1));
    };
  // Sphere (JS game engine) Dispatch API
  } else if (Dispatch && Dispatch.now) {
    defer = function (id) {
      Dispatch.now(ctx(run, id, 1));
    };
  // Browsers with MessageChannel, includes WebWorkers
  } else if (MessageChannel) {
    channel = new MessageChannel();
    port = channel.port2;
    channel.port1.onmessage = listener;
    defer = ctx(port.postMessage, port, 1);
  // Browsers with postMessage, skip WebWorkers
  // IE8 has postMessage, but it's sync & typeof its postMessage is 'object'
  } else if (global.addEventListener && typeof postMessage == 'function' && !global.importScripts) {
    defer = function (id) {
      global.postMessage(id + '', '*');
    };
    global.addEventListener('message', listener, false);
  // IE8-
  } else if (ONREADYSTATECHANGE in cel('script')) {
    defer = function (id) {
      html.appendChild(cel('script'))[ONREADYSTATECHANGE] = function () {
        html.removeChild(this);
        run.call(id);
      };
    };
  // Rest old browsers
  } else {
    defer = function (id) {
      setTimeout(ctx(run, id, 1), 0);
    };
  }
}
module.exports = {
  set: setTask,
  clear: clearTask
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-absolute-index.js":
/***/ (function(module, exports, __webpack_require__) {

var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var max = Math.max;
var min = Math.min;
module.exports = function (index, length) {
  index = toInteger(index);
  return index < 0 ? max(index + length, 0) : min(index, length);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-index.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/ecma262/#sec-toindex
var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
module.exports = function (it) {
  if (it === undefined) return 0;
  var number = toInteger(it);
  var length = toLength(number);
  if (number !== length) throw RangeError('Wrong length!');
  return length;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-integer.js":
/***/ (function(module, exports) {

// 7.1.4 ToInteger
var ceil = Math.ceil;
var floor = Math.floor;
module.exports = function (it) {
  return isNaN(it = +it) ? 0 : (it > 0 ? floor : ceil)(it);
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-iobject.js":
/***/ (function(module, exports, __webpack_require__) {

// to indexed object, toObject with fallback for non-array-like ES3 strings
var IObject = __webpack_require__("./node_modules/core-js/modules/_iobject.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
module.exports = function (it) {
  return IObject(defined(it));
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-length.js":
/***/ (function(module, exports, __webpack_require__) {

// 7.1.15 ToLength
var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var min = Math.min;
module.exports = function (it) {
  return it > 0 ? min(toInteger(it), 0x1fffffffffffff) : 0; // pow(2, 53) - 1 == 9007199254740991
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-object.js":
/***/ (function(module, exports, __webpack_require__) {

// 7.1.13 ToObject(argument)
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
module.exports = function (it) {
  return Object(defined(it));
};


/***/ }),

/***/ "./node_modules/core-js/modules/_to-primitive.js":
/***/ (function(module, exports, __webpack_require__) {

// 7.1.1 ToPrimitive(input [, PreferredType])
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
// instead of the ES6 spec version, we didn't implement @@toPrimitive case
// and the second argument - flag - preferred type is a string
module.exports = function (it, S) {
  if (!isObject(it)) return it;
  var fn, val;
  if (S && typeof (fn = it.toString) == 'function' && !isObject(val = fn.call(it))) return val;
  if (typeof (fn = it.valueOf) == 'function' && !isObject(val = fn.call(it))) return val;
  if (!S && typeof (fn = it.toString) == 'function' && !isObject(val = fn.call(it))) return val;
  throw TypeError("Can't convert object to primitive value");
};


/***/ }),

/***/ "./node_modules/core-js/modules/_typed-array.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

if (__webpack_require__("./node_modules/core-js/modules/_descriptors.js")) {
  var LIBRARY = __webpack_require__("./node_modules/core-js/modules/_library.js");
  var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
  var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
  var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
  var $typed = __webpack_require__("./node_modules/core-js/modules/_typed.js");
  var $buffer = __webpack_require__("./node_modules/core-js/modules/_typed-buffer.js");
  var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
  var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
  var propertyDesc = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");
  var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
  var redefineAll = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js");
  var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
  var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
  var toIndex = __webpack_require__("./node_modules/core-js/modules/_to-index.js");
  var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
  var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
  var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
  var classof = __webpack_require__("./node_modules/core-js/modules/_classof.js");
  var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
  var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
  var isArrayIter = __webpack_require__("./node_modules/core-js/modules/_is-array-iter.js");
  var create = __webpack_require__("./node_modules/core-js/modules/_object-create.js");
  var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
  var gOPN = __webpack_require__("./node_modules/core-js/modules/_object-gopn.js").f;
  var getIterFn = __webpack_require__("./node_modules/core-js/modules/core.get-iterator-method.js");
  var uid = __webpack_require__("./node_modules/core-js/modules/_uid.js");
  var wks = __webpack_require__("./node_modules/core-js/modules/_wks.js");
  var createArrayMethod = __webpack_require__("./node_modules/core-js/modules/_array-methods.js");
  var createArrayIncludes = __webpack_require__("./node_modules/core-js/modules/_array-includes.js");
  var speciesConstructor = __webpack_require__("./node_modules/core-js/modules/_species-constructor.js");
  var ArrayIterators = __webpack_require__("./node_modules/core-js/modules/es6.array.iterator.js");
  var Iterators = __webpack_require__("./node_modules/core-js/modules/_iterators.js");
  var $iterDetect = __webpack_require__("./node_modules/core-js/modules/_iter-detect.js");
  var setSpecies = __webpack_require__("./node_modules/core-js/modules/_set-species.js");
  var arrayFill = __webpack_require__("./node_modules/core-js/modules/_array-fill.js");
  var arrayCopyWithin = __webpack_require__("./node_modules/core-js/modules/_array-copy-within.js");
  var $DP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
  var $GOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js");
  var dP = $DP.f;
  var gOPD = $GOPD.f;
  var RangeError = global.RangeError;
  var TypeError = global.TypeError;
  var Uint8Array = global.Uint8Array;
  var ARRAY_BUFFER = 'ArrayBuffer';
  var SHARED_BUFFER = 'Shared' + ARRAY_BUFFER;
  var BYTES_PER_ELEMENT = 'BYTES_PER_ELEMENT';
  var PROTOTYPE = 'prototype';
  var ArrayProto = Array[PROTOTYPE];
  var $ArrayBuffer = $buffer.ArrayBuffer;
  var $DataView = $buffer.DataView;
  var arrayForEach = createArrayMethod(0);
  var arrayFilter = createArrayMethod(2);
  var arraySome = createArrayMethod(3);
  var arrayEvery = createArrayMethod(4);
  var arrayFind = createArrayMethod(5);
  var arrayFindIndex = createArrayMethod(6);
  var arrayIncludes = createArrayIncludes(true);
  var arrayIndexOf = createArrayIncludes(false);
  var arrayValues = ArrayIterators.values;
  var arrayKeys = ArrayIterators.keys;
  var arrayEntries = ArrayIterators.entries;
  var arrayLastIndexOf = ArrayProto.lastIndexOf;
  var arrayReduce = ArrayProto.reduce;
  var arrayReduceRight = ArrayProto.reduceRight;
  var arrayJoin = ArrayProto.join;
  var arraySort = ArrayProto.sort;
  var arraySlice = ArrayProto.slice;
  var arrayToString = ArrayProto.toString;
  var arrayToLocaleString = ArrayProto.toLocaleString;
  var ITERATOR = wks('iterator');
  var TAG = wks('toStringTag');
  var TYPED_CONSTRUCTOR = uid('typed_constructor');
  var DEF_CONSTRUCTOR = uid('def_constructor');
  var ALL_CONSTRUCTORS = $typed.CONSTR;
  var TYPED_ARRAY = $typed.TYPED;
  var VIEW = $typed.VIEW;
  var WRONG_LENGTH = 'Wrong length!';

  var $map = createArrayMethod(1, function (O, length) {
    return allocate(speciesConstructor(O, O[DEF_CONSTRUCTOR]), length);
  });

  var LITTLE_ENDIAN = fails(function () {
    // eslint-disable-next-line no-undef
    return new Uint8Array(new Uint16Array([1]).buffer)[0] === 1;
  });

  var FORCED_SET = !!Uint8Array && !!Uint8Array[PROTOTYPE].set && fails(function () {
    new Uint8Array(1).set({});
  });

  var toOffset = function (it, BYTES) {
    var offset = toInteger(it);
    if (offset < 0 || offset % BYTES) throw RangeError('Wrong offset!');
    return offset;
  };

  var validate = function (it) {
    if (isObject(it) && TYPED_ARRAY in it) return it;
    throw TypeError(it + ' is not a typed array!');
  };

  var allocate = function (C, length) {
    if (!(isObject(C) && TYPED_CONSTRUCTOR in C)) {
      throw TypeError('It is not a typed array constructor!');
    } return new C(length);
  };

  var speciesFromList = function (O, list) {
    return fromList(speciesConstructor(O, O[DEF_CONSTRUCTOR]), list);
  };

  var fromList = function (C, list) {
    var index = 0;
    var length = list.length;
    var result = allocate(C, length);
    while (length > index) result[index] = list[index++];
    return result;
  };

  var addGetter = function (it, key, internal) {
    dP(it, key, { get: function () { return this._d[internal]; } });
  };

  var $from = function from(source /* , mapfn, thisArg */) {
    var O = toObject(source);
    var aLen = arguments.length;
    var mapfn = aLen > 1 ? arguments[1] : undefined;
    var mapping = mapfn !== undefined;
    var iterFn = getIterFn(O);
    var i, length, values, result, step, iterator;
    if (iterFn != undefined && !isArrayIter(iterFn)) {
      for (iterator = iterFn.call(O), values = [], i = 0; !(step = iterator.next()).done; i++) {
        values.push(step.value);
      } O = values;
    }
    if (mapping && aLen > 2) mapfn = ctx(mapfn, arguments[2], 2);
    for (i = 0, length = toLength(O.length), result = allocate(this, length); length > i; i++) {
      result[i] = mapping ? mapfn(O[i], i) : O[i];
    }
    return result;
  };

  var $of = function of(/* ...items */) {
    var index = 0;
    var length = arguments.length;
    var result = allocate(this, length);
    while (length > index) result[index] = arguments[index++];
    return result;
  };

  // iOS Safari 6.x fails here
  var TO_LOCALE_BUG = !!Uint8Array && fails(function () { arrayToLocaleString.call(new Uint8Array(1)); });

  var $toLocaleString = function toLocaleString() {
    return arrayToLocaleString.apply(TO_LOCALE_BUG ? arraySlice.call(validate(this)) : validate(this), arguments);
  };

  var proto = {
    copyWithin: function copyWithin(target, start /* , end */) {
      return arrayCopyWithin.call(validate(this), target, start, arguments.length > 2 ? arguments[2] : undefined);
    },
    every: function every(callbackfn /* , thisArg */) {
      return arrayEvery(validate(this), callbackfn, arguments.length > 1 ? arguments[1] : undefined);
    },
    fill: function fill(value /* , start, end */) { // eslint-disable-line no-unused-vars
      return arrayFill.apply(validate(this), arguments);
    },
    filter: function filter(callbackfn /* , thisArg */) {
      return speciesFromList(this, arrayFilter(validate(this), callbackfn,
        arguments.length > 1 ? arguments[1] : undefined));
    },
    find: function find(predicate /* , thisArg */) {
      return arrayFind(validate(this), predicate, arguments.length > 1 ? arguments[1] : undefined);
    },
    findIndex: function findIndex(predicate /* , thisArg */) {
      return arrayFindIndex(validate(this), predicate, arguments.length > 1 ? arguments[1] : undefined);
    },
    forEach: function forEach(callbackfn /* , thisArg */) {
      arrayForEach(validate(this), callbackfn, arguments.length > 1 ? arguments[1] : undefined);
    },
    indexOf: function indexOf(searchElement /* , fromIndex */) {
      return arrayIndexOf(validate(this), searchElement, arguments.length > 1 ? arguments[1] : undefined);
    },
    includes: function includes(searchElement /* , fromIndex */) {
      return arrayIncludes(validate(this), searchElement, arguments.length > 1 ? arguments[1] : undefined);
    },
    join: function join(separator) { // eslint-disable-line no-unused-vars
      return arrayJoin.apply(validate(this), arguments);
    },
    lastIndexOf: function lastIndexOf(searchElement /* , fromIndex */) { // eslint-disable-line no-unused-vars
      return arrayLastIndexOf.apply(validate(this), arguments);
    },
    map: function map(mapfn /* , thisArg */) {
      return $map(validate(this), mapfn, arguments.length > 1 ? arguments[1] : undefined);
    },
    reduce: function reduce(callbackfn /* , initialValue */) { // eslint-disable-line no-unused-vars
      return arrayReduce.apply(validate(this), arguments);
    },
    reduceRight: function reduceRight(callbackfn /* , initialValue */) { // eslint-disable-line no-unused-vars
      return arrayReduceRight.apply(validate(this), arguments);
    },
    reverse: function reverse() {
      var that = this;
      var length = validate(that).length;
      var middle = Math.floor(length / 2);
      var index = 0;
      var value;
      while (index < middle) {
        value = that[index];
        that[index++] = that[--length];
        that[length] = value;
      } return that;
    },
    some: function some(callbackfn /* , thisArg */) {
      return arraySome(validate(this), callbackfn, arguments.length > 1 ? arguments[1] : undefined);
    },
    sort: function sort(comparefn) {
      return arraySort.call(validate(this), comparefn);
    },
    subarray: function subarray(begin, end) {
      var O = validate(this);
      var length = O.length;
      var $begin = toAbsoluteIndex(begin, length);
      return new (speciesConstructor(O, O[DEF_CONSTRUCTOR]))(
        O.buffer,
        O.byteOffset + $begin * O.BYTES_PER_ELEMENT,
        toLength((end === undefined ? length : toAbsoluteIndex(end, length)) - $begin)
      );
    }
  };

  var $slice = function slice(start, end) {
    return speciesFromList(this, arraySlice.call(validate(this), start, end));
  };

  var $set = function set(arrayLike /* , offset */) {
    validate(this);
    var offset = toOffset(arguments[1], 1);
    var length = this.length;
    var src = toObject(arrayLike);
    var len = toLength(src.length);
    var index = 0;
    if (len + offset > length) throw RangeError(WRONG_LENGTH);
    while (index < len) this[offset + index] = src[index++];
  };

  var $iterators = {
    entries: function entries() {
      return arrayEntries.call(validate(this));
    },
    keys: function keys() {
      return arrayKeys.call(validate(this));
    },
    values: function values() {
      return arrayValues.call(validate(this));
    }
  };

  var isTAIndex = function (target, key) {
    return isObject(target)
      && target[TYPED_ARRAY]
      && typeof key != 'symbol'
      && key in target
      && String(+key) == String(key);
  };
  var $getDesc = function getOwnPropertyDescriptor(target, key) {
    return isTAIndex(target, key = toPrimitive(key, true))
      ? propertyDesc(2, target[key])
      : gOPD(target, key);
  };
  var $setDesc = function defineProperty(target, key, desc) {
    if (isTAIndex(target, key = toPrimitive(key, true))
      && isObject(desc)
      && has(desc, 'value')
      && !has(desc, 'get')
      && !has(desc, 'set')
      // TODO: add validation descriptor w/o calling accessors
      && !desc.configurable
      && (!has(desc, 'writable') || desc.writable)
      && (!has(desc, 'enumerable') || desc.enumerable)
    ) {
      target[key] = desc.value;
      return target;
    } return dP(target, key, desc);
  };

  if (!ALL_CONSTRUCTORS) {
    $GOPD.f = $getDesc;
    $DP.f = $setDesc;
  }

  $export($export.S + $export.F * !ALL_CONSTRUCTORS, 'Object', {
    getOwnPropertyDescriptor: $getDesc,
    defineProperty: $setDesc
  });

  if (fails(function () { arrayToString.call({}); })) {
    arrayToString = arrayToLocaleString = function toString() {
      return arrayJoin.call(this);
    };
  }

  var $TypedArrayPrototype$ = redefineAll({}, proto);
  redefineAll($TypedArrayPrototype$, $iterators);
  hide($TypedArrayPrototype$, ITERATOR, $iterators.values);
  redefineAll($TypedArrayPrototype$, {
    slice: $slice,
    set: $set,
    constructor: function () { /* noop */ },
    toString: arrayToString,
    toLocaleString: $toLocaleString
  });
  addGetter($TypedArrayPrototype$, 'buffer', 'b');
  addGetter($TypedArrayPrototype$, 'byteOffset', 'o');
  addGetter($TypedArrayPrototype$, 'byteLength', 'l');
  addGetter($TypedArrayPrototype$, 'length', 'e');
  dP($TypedArrayPrototype$, TAG, {
    get: function () { return this[TYPED_ARRAY]; }
  });

  // eslint-disable-next-line max-statements
  module.exports = function (KEY, BYTES, wrapper, CLAMPED) {
    CLAMPED = !!CLAMPED;
    var NAME = KEY + (CLAMPED ? 'Clamped' : '') + 'Array';
    var GETTER = 'get' + KEY;
    var SETTER = 'set' + KEY;
    var TypedArray = global[NAME];
    var Base = TypedArray || {};
    var TAC = TypedArray && getPrototypeOf(TypedArray);
    var FORCED = !TypedArray || !$typed.ABV;
    var O = {};
    var TypedArrayPrototype = TypedArray && TypedArray[PROTOTYPE];
    var getter = function (that, index) {
      var data = that._d;
      return data.v[GETTER](index * BYTES + data.o, LITTLE_ENDIAN);
    };
    var setter = function (that, index, value) {
      var data = that._d;
      if (CLAMPED) value = (value = Math.round(value)) < 0 ? 0 : value > 0xff ? 0xff : value & 0xff;
      data.v[SETTER](index * BYTES + data.o, value, LITTLE_ENDIAN);
    };
    var addElement = function (that, index) {
      dP(that, index, {
        get: function () {
          return getter(this, index);
        },
        set: function (value) {
          return setter(this, index, value);
        },
        enumerable: true
      });
    };
    if (FORCED) {
      TypedArray = wrapper(function (that, data, $offset, $length) {
        anInstance(that, TypedArray, NAME, '_d');
        var index = 0;
        var offset = 0;
        var buffer, byteLength, length, klass;
        if (!isObject(data)) {
          length = toIndex(data);
          byteLength = length * BYTES;
          buffer = new $ArrayBuffer(byteLength);
        } else if (data instanceof $ArrayBuffer || (klass = classof(data)) == ARRAY_BUFFER || klass == SHARED_BUFFER) {
          buffer = data;
          offset = toOffset($offset, BYTES);
          var $len = data.byteLength;
          if ($length === undefined) {
            if ($len % BYTES) throw RangeError(WRONG_LENGTH);
            byteLength = $len - offset;
            if (byteLength < 0) throw RangeError(WRONG_LENGTH);
          } else {
            byteLength = toLength($length) * BYTES;
            if (byteLength + offset > $len) throw RangeError(WRONG_LENGTH);
          }
          length = byteLength / BYTES;
        } else if (TYPED_ARRAY in data) {
          return fromList(TypedArray, data);
        } else {
          return $from.call(TypedArray, data);
        }
        hide(that, '_d', {
          b: buffer,
          o: offset,
          l: byteLength,
          e: length,
          v: new $DataView(buffer)
        });
        while (index < length) addElement(that, index++);
      });
      TypedArrayPrototype = TypedArray[PROTOTYPE] = create($TypedArrayPrototype$);
      hide(TypedArrayPrototype, 'constructor', TypedArray);
    } else if (!fails(function () {
      TypedArray(1);
    }) || !fails(function () {
      new TypedArray(-1); // eslint-disable-line no-new
    }) || !$iterDetect(function (iter) {
      new TypedArray(); // eslint-disable-line no-new
      new TypedArray(null); // eslint-disable-line no-new
      new TypedArray(1.5); // eslint-disable-line no-new
      new TypedArray(iter); // eslint-disable-line no-new
    }, true)) {
      TypedArray = wrapper(function (that, data, $offset, $length) {
        anInstance(that, TypedArray, NAME);
        var klass;
        // `ws` module bug, temporarily remove validation length for Uint8Array
        // https://github.com/websockets/ws/pull/645
        if (!isObject(data)) return new Base(toIndex(data));
        if (data instanceof $ArrayBuffer || (klass = classof(data)) == ARRAY_BUFFER || klass == SHARED_BUFFER) {
          return $length !== undefined
            ? new Base(data, toOffset($offset, BYTES), $length)
            : $offset !== undefined
              ? new Base(data, toOffset($offset, BYTES))
              : new Base(data);
        }
        if (TYPED_ARRAY in data) return fromList(TypedArray, data);
        return $from.call(TypedArray, data);
      });
      arrayForEach(TAC !== Function.prototype ? gOPN(Base).concat(gOPN(TAC)) : gOPN(Base), function (key) {
        if (!(key in TypedArray)) hide(TypedArray, key, Base[key]);
      });
      TypedArray[PROTOTYPE] = TypedArrayPrototype;
      if (!LIBRARY) TypedArrayPrototype.constructor = TypedArray;
    }
    var $nativeIterator = TypedArrayPrototype[ITERATOR];
    var CORRECT_ITER_NAME = !!$nativeIterator
      && ($nativeIterator.name == 'values' || $nativeIterator.name == undefined);
    var $iterator = $iterators.values;
    hide(TypedArray, TYPED_CONSTRUCTOR, true);
    hide(TypedArrayPrototype, TYPED_ARRAY, NAME);
    hide(TypedArrayPrototype, VIEW, true);
    hide(TypedArrayPrototype, DEF_CONSTRUCTOR, TypedArray);

    if (CLAMPED ? new TypedArray(1)[TAG] != NAME : !(TAG in TypedArrayPrototype)) {
      dP(TypedArrayPrototype, TAG, {
        get: function () { return NAME; }
      });
    }

    O[NAME] = TypedArray;

    $export($export.G + $export.W + $export.F * (TypedArray != Base), O);

    $export($export.S, NAME, {
      BYTES_PER_ELEMENT: BYTES
    });

    $export($export.S + $export.F * fails(function () { Base.of.call(TypedArray, 1); }), NAME, {
      from: $from,
      of: $of
    });

    if (!(BYTES_PER_ELEMENT in TypedArrayPrototype)) hide(TypedArrayPrototype, BYTES_PER_ELEMENT, BYTES);

    $export($export.P, NAME, proto);

    setSpecies(NAME);

    $export($export.P + $export.F * FORCED_SET, NAME, { set: $set });

    $export($export.P + $export.F * !CORRECT_ITER_NAME, NAME, $iterators);

    if (!LIBRARY && TypedArrayPrototype.toString != arrayToString) TypedArrayPrototype.toString = arrayToString;

    $export($export.P + $export.F * fails(function () {
      new TypedArray(1).slice();
    }), NAME, { slice: $slice });

    $export($export.P + $export.F * (fails(function () {
      return [1, 2].toLocaleString() != new TypedArray([1, 2]).toLocaleString();
    }) || !fails(function () {
      TypedArrayPrototype.toLocaleString.call([1, 2]);
    })), NAME, { toLocaleString: $toLocaleString });

    Iterators[NAME] = CORRECT_ITER_NAME ? $nativeIterator : $iterator;
    if (!LIBRARY && !CORRECT_ITER_NAME) hide(TypedArrayPrototype, ITERATOR, $iterator);
  };
} else module.exports = function () { /* empty */ };


/***/ }),

/***/ "./node_modules/core-js/modules/_typed-buffer.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var DESCRIPTORS = __webpack_require__("./node_modules/core-js/modules/_descriptors.js");
var LIBRARY = __webpack_require__("./node_modules/core-js/modules/_library.js");
var $typed = __webpack_require__("./node_modules/core-js/modules/_typed.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var redefineAll = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var toIndex = __webpack_require__("./node_modules/core-js/modules/_to-index.js");
var gOPN = __webpack_require__("./node_modules/core-js/modules/_object-gopn.js").f;
var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var arrayFill = __webpack_require__("./node_modules/core-js/modules/_array-fill.js");
var setToStringTag = __webpack_require__("./node_modules/core-js/modules/_set-to-string-tag.js");
var ARRAY_BUFFER = 'ArrayBuffer';
var DATA_VIEW = 'DataView';
var PROTOTYPE = 'prototype';
var WRONG_LENGTH = 'Wrong length!';
var WRONG_INDEX = 'Wrong index!';
var $ArrayBuffer = global[ARRAY_BUFFER];
var $DataView = global[DATA_VIEW];
var Math = global.Math;
var RangeError = global.RangeError;
// eslint-disable-next-line no-shadow-restricted-names
var Infinity = global.Infinity;
var BaseBuffer = $ArrayBuffer;
var abs = Math.abs;
var pow = Math.pow;
var floor = Math.floor;
var log = Math.log;
var LN2 = Math.LN2;
var BUFFER = 'buffer';
var BYTE_LENGTH = 'byteLength';
var BYTE_OFFSET = 'byteOffset';
var $BUFFER = DESCRIPTORS ? '_b' : BUFFER;
var $LENGTH = DESCRIPTORS ? '_l' : BYTE_LENGTH;
var $OFFSET = DESCRIPTORS ? '_o' : BYTE_OFFSET;

// IEEE754 conversions based on https://github.com/feross/ieee754
function packIEEE754(value, mLen, nBytes) {
  var buffer = new Array(nBytes);
  var eLen = nBytes * 8 - mLen - 1;
  var eMax = (1 << eLen) - 1;
  var eBias = eMax >> 1;
  var rt = mLen === 23 ? pow(2, -24) - pow(2, -77) : 0;
  var i = 0;
  var s = value < 0 || value === 0 && 1 / value < 0 ? 1 : 0;
  var e, m, c;
  value = abs(value);
  // eslint-disable-next-line no-self-compare
  if (value != value || value === Infinity) {
    // eslint-disable-next-line no-self-compare
    m = value != value ? 1 : 0;
    e = eMax;
  } else {
    e = floor(log(value) / LN2);
    if (value * (c = pow(2, -e)) < 1) {
      e--;
      c *= 2;
    }
    if (e + eBias >= 1) {
      value += rt / c;
    } else {
      value += rt * pow(2, 1 - eBias);
    }
    if (value * c >= 2) {
      e++;
      c /= 2;
    }
    if (e + eBias >= eMax) {
      m = 0;
      e = eMax;
    } else if (e + eBias >= 1) {
      m = (value * c - 1) * pow(2, mLen);
      e = e + eBias;
    } else {
      m = value * pow(2, eBias - 1) * pow(2, mLen);
      e = 0;
    }
  }
  for (; mLen >= 8; buffer[i++] = m & 255, m /= 256, mLen -= 8);
  e = e << mLen | m;
  eLen += mLen;
  for (; eLen > 0; buffer[i++] = e & 255, e /= 256, eLen -= 8);
  buffer[--i] |= s * 128;
  return buffer;
}
function unpackIEEE754(buffer, mLen, nBytes) {
  var eLen = nBytes * 8 - mLen - 1;
  var eMax = (1 << eLen) - 1;
  var eBias = eMax >> 1;
  var nBits = eLen - 7;
  var i = nBytes - 1;
  var s = buffer[i--];
  var e = s & 127;
  var m;
  s >>= 7;
  for (; nBits > 0; e = e * 256 + buffer[i], i--, nBits -= 8);
  m = e & (1 << -nBits) - 1;
  e >>= -nBits;
  nBits += mLen;
  for (; nBits > 0; m = m * 256 + buffer[i], i--, nBits -= 8);
  if (e === 0) {
    e = 1 - eBias;
  } else if (e === eMax) {
    return m ? NaN : s ? -Infinity : Infinity;
  } else {
    m = m + pow(2, mLen);
    e = e - eBias;
  } return (s ? -1 : 1) * m * pow(2, e - mLen);
}

function unpackI32(bytes) {
  return bytes[3] << 24 | bytes[2] << 16 | bytes[1] << 8 | bytes[0];
}
function packI8(it) {
  return [it & 0xff];
}
function packI16(it) {
  return [it & 0xff, it >> 8 & 0xff];
}
function packI32(it) {
  return [it & 0xff, it >> 8 & 0xff, it >> 16 & 0xff, it >> 24 & 0xff];
}
function packF64(it) {
  return packIEEE754(it, 52, 8);
}
function packF32(it) {
  return packIEEE754(it, 23, 4);
}

function addGetter(C, key, internal) {
  dP(C[PROTOTYPE], key, { get: function () { return this[internal]; } });
}

function get(view, bytes, index, isLittleEndian) {
  var numIndex = +index;
  var intIndex = toIndex(numIndex);
  if (intIndex + bytes > view[$LENGTH]) throw RangeError(WRONG_INDEX);
  var store = view[$BUFFER]._b;
  var start = intIndex + view[$OFFSET];
  var pack = store.slice(start, start + bytes);
  return isLittleEndian ? pack : pack.reverse();
}
function set(view, bytes, index, conversion, value, isLittleEndian) {
  var numIndex = +index;
  var intIndex = toIndex(numIndex);
  if (intIndex + bytes > view[$LENGTH]) throw RangeError(WRONG_INDEX);
  var store = view[$BUFFER]._b;
  var start = intIndex + view[$OFFSET];
  var pack = conversion(+value);
  for (var i = 0; i < bytes; i++) store[start + i] = pack[isLittleEndian ? i : bytes - i - 1];
}

if (!$typed.ABV) {
  $ArrayBuffer = function ArrayBuffer(length) {
    anInstance(this, $ArrayBuffer, ARRAY_BUFFER);
    var byteLength = toIndex(length);
    this._b = arrayFill.call(new Array(byteLength), 0);
    this[$LENGTH] = byteLength;
  };

  $DataView = function DataView(buffer, byteOffset, byteLength) {
    anInstance(this, $DataView, DATA_VIEW);
    anInstance(buffer, $ArrayBuffer, DATA_VIEW);
    var bufferLength = buffer[$LENGTH];
    var offset = toInteger(byteOffset);
    if (offset < 0 || offset > bufferLength) throw RangeError('Wrong offset!');
    byteLength = byteLength === undefined ? bufferLength - offset : toLength(byteLength);
    if (offset + byteLength > bufferLength) throw RangeError(WRONG_LENGTH);
    this[$BUFFER] = buffer;
    this[$OFFSET] = offset;
    this[$LENGTH] = byteLength;
  };

  if (DESCRIPTORS) {
    addGetter($ArrayBuffer, BYTE_LENGTH, '_l');
    addGetter($DataView, BUFFER, '_b');
    addGetter($DataView, BYTE_LENGTH, '_l');
    addGetter($DataView, BYTE_OFFSET, '_o');
  }

  redefineAll($DataView[PROTOTYPE], {
    getInt8: function getInt8(byteOffset) {
      return get(this, 1, byteOffset)[0] << 24 >> 24;
    },
    getUint8: function getUint8(byteOffset) {
      return get(this, 1, byteOffset)[0];
    },
    getInt16: function getInt16(byteOffset /* , littleEndian */) {
      var bytes = get(this, 2, byteOffset, arguments[1]);
      return (bytes[1] << 8 | bytes[0]) << 16 >> 16;
    },
    getUint16: function getUint16(byteOffset /* , littleEndian */) {
      var bytes = get(this, 2, byteOffset, arguments[1]);
      return bytes[1] << 8 | bytes[0];
    },
    getInt32: function getInt32(byteOffset /* , littleEndian */) {
      return unpackI32(get(this, 4, byteOffset, arguments[1]));
    },
    getUint32: function getUint32(byteOffset /* , littleEndian */) {
      return unpackI32(get(this, 4, byteOffset, arguments[1])) >>> 0;
    },
    getFloat32: function getFloat32(byteOffset /* , littleEndian */) {
      return unpackIEEE754(get(this, 4, byteOffset, arguments[1]), 23, 4);
    },
    getFloat64: function getFloat64(byteOffset /* , littleEndian */) {
      return unpackIEEE754(get(this, 8, byteOffset, arguments[1]), 52, 8);
    },
    setInt8: function setInt8(byteOffset, value) {
      set(this, 1, byteOffset, packI8, value);
    },
    setUint8: function setUint8(byteOffset, value) {
      set(this, 1, byteOffset, packI8, value);
    },
    setInt16: function setInt16(byteOffset, value /* , littleEndian */) {
      set(this, 2, byteOffset, packI16, value, arguments[2]);
    },
    setUint16: function setUint16(byteOffset, value /* , littleEndian */) {
      set(this, 2, byteOffset, packI16, value, arguments[2]);
    },
    setInt32: function setInt32(byteOffset, value /* , littleEndian */) {
      set(this, 4, byteOffset, packI32, value, arguments[2]);
    },
    setUint32: function setUint32(byteOffset, value /* , littleEndian */) {
      set(this, 4, byteOffset, packI32, value, arguments[2]);
    },
    setFloat32: function setFloat32(byteOffset, value /* , littleEndian */) {
      set(this, 4, byteOffset, packF32, value, arguments[2]);
    },
    setFloat64: function setFloat64(byteOffset, value /* , littleEndian */) {
      set(this, 8, byteOffset, packF64, value, arguments[2]);
    }
  });
} else {
  if (!fails(function () {
    $ArrayBuffer(1);
  }) || !fails(function () {
    new $ArrayBuffer(-1); // eslint-disable-line no-new
  }) || fails(function () {
    new $ArrayBuffer(); // eslint-disable-line no-new
    new $ArrayBuffer(1.5); // eslint-disable-line no-new
    new $ArrayBuffer(NaN); // eslint-disable-line no-new
    return $ArrayBuffer.name != ARRAY_BUFFER;
  })) {
    $ArrayBuffer = function ArrayBuffer(length) {
      anInstance(this, $ArrayBuffer);
      return new BaseBuffer(toIndex(length));
    };
    var ArrayBufferProto = $ArrayBuffer[PROTOTYPE] = BaseBuffer[PROTOTYPE];
    for (var keys = gOPN(BaseBuffer), j = 0, key; keys.length > j;) {
      if (!((key = keys[j++]) in $ArrayBuffer)) hide($ArrayBuffer, key, BaseBuffer[key]);
    }
    if (!LIBRARY) ArrayBufferProto.constructor = $ArrayBuffer;
  }
  // iOS Safari 7.x bug
  var view = new $DataView(new $ArrayBuffer(2));
  var $setInt8 = $DataView[PROTOTYPE].setInt8;
  view.setInt8(0, 2147483648);
  view.setInt8(1, 2147483649);
  if (view.getInt8(0) || !view.getInt8(1)) redefineAll($DataView[PROTOTYPE], {
    setInt8: function setInt8(byteOffset, value) {
      $setInt8.call(this, byteOffset, value << 24 >> 24);
    },
    setUint8: function setUint8(byteOffset, value) {
      $setInt8.call(this, byteOffset, value << 24 >> 24);
    }
  }, true);
}
setToStringTag($ArrayBuffer, ARRAY_BUFFER);
setToStringTag($DataView, DATA_VIEW);
hide($DataView[PROTOTYPE], $typed.VIEW, true);
exports[ARRAY_BUFFER] = $ArrayBuffer;
exports[DATA_VIEW] = $DataView;


/***/ }),

/***/ "./node_modules/core-js/modules/_typed.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var uid = __webpack_require__("./node_modules/core-js/modules/_uid.js");
var TYPED = uid('typed_array');
var VIEW = uid('view');
var ABV = !!(global.ArrayBuffer && global.DataView);
var CONSTR = ABV;
var i = 0;
var l = 9;
var Typed;

var TypedArrayConstructors = (
  'Int8Array,Uint8Array,Uint8ClampedArray,Int16Array,Uint16Array,Int32Array,Uint32Array,Float32Array,Float64Array'
).split(',');

while (i < l) {
  if (Typed = global[TypedArrayConstructors[i++]]) {
    hide(Typed.prototype, TYPED, true);
    hide(Typed.prototype, VIEW, true);
  } else CONSTR = false;
}

module.exports = {
  ABV: ABV,
  CONSTR: CONSTR,
  TYPED: TYPED,
  VIEW: VIEW
};


/***/ }),

/***/ "./node_modules/core-js/modules/_uid.js":
/***/ (function(module, exports) {

var id = 0;
var px = Math.random();
module.exports = function (key) {
  return 'Symbol('.concat(key === undefined ? '' : key, ')_', (++id + px).toString(36));
};


/***/ }),

/***/ "./node_modules/core-js/modules/_user-agent.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var navigator = global.navigator;

module.exports = navigator && navigator.userAgent || '';


/***/ }),

/***/ "./node_modules/core-js/modules/_validate-collection.js":
/***/ (function(module, exports, __webpack_require__) {

var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
module.exports = function (it, TYPE) {
  if (!isObject(it) || it._t !== TYPE) throw TypeError('Incompatible receiver, ' + TYPE + ' required!');
  return it;
};


/***/ }),

/***/ "./node_modules/core-js/modules/_wks-define.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var core = __webpack_require__("./node_modules/core-js/modules/_core.js");
var LIBRARY = __webpack_require__("./node_modules/core-js/modules/_library.js");
var wksExt = __webpack_require__("./node_modules/core-js/modules/_wks-ext.js");
var defineProperty = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
module.exports = function (name) {
  var $Symbol = core.Symbol || (core.Symbol = LIBRARY ? {} : global.Symbol || {});
  if (name.charAt(0) != '_' && !(name in $Symbol)) defineProperty($Symbol, name, { value: wksExt.f(name) });
};


/***/ }),

/***/ "./node_modules/core-js/modules/_wks-ext.js":
/***/ (function(module, exports, __webpack_require__) {

exports.f = __webpack_require__("./node_modules/core-js/modules/_wks.js");


/***/ }),

/***/ "./node_modules/core-js/modules/_wks.js":
/***/ (function(module, exports, __webpack_require__) {

var store = __webpack_require__("./node_modules/core-js/modules/_shared.js")('wks');
var uid = __webpack_require__("./node_modules/core-js/modules/_uid.js");
var Symbol = __webpack_require__("./node_modules/core-js/modules/_global.js").Symbol;
var USE_SYMBOL = typeof Symbol == 'function';

var $exports = module.exports = function (name) {
  return store[name] || (store[name] =
    USE_SYMBOL && Symbol[name] || (USE_SYMBOL ? Symbol : uid)('Symbol.' + name));
};

$exports.store = store;


/***/ }),

/***/ "./node_modules/core-js/modules/core.get-iterator-method.js":
/***/ (function(module, exports, __webpack_require__) {

var classof = __webpack_require__("./node_modules/core-js/modules/_classof.js");
var ITERATOR = __webpack_require__("./node_modules/core-js/modules/_wks.js")('iterator');
var Iterators = __webpack_require__("./node_modules/core-js/modules/_iterators.js");
module.exports = __webpack_require__("./node_modules/core-js/modules/_core.js").getIteratorMethod = function (it) {
  if (it != undefined) return it[ITERATOR]
    || it['@@iterator']
    || Iterators[classof(it)];
};


/***/ }),

/***/ "./node_modules/core-js/modules/core.regexp.escape.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/benjamingr/RexExp.escape
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $re = __webpack_require__("./node_modules/core-js/modules/_replacer.js")(/[\\^$*+?.()|[\]{}]/g, '\\$&');

$export($export.S, 'RegExp', { escape: function escape(it) { return $re(it); } });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.copy-within.js":
/***/ (function(module, exports, __webpack_require__) {

// 22.1.3.3 Array.prototype.copyWithin(target, start, end = this.length)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.P, 'Array', { copyWithin: __webpack_require__("./node_modules/core-js/modules/_array-copy-within.js") });

__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")('copyWithin');


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.every.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $every = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(4);

$export($export.P + $export.F * !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].every, true), 'Array', {
  // 22.1.3.5 / 15.4.4.16 Array.prototype.every(callbackfn [, thisArg])
  every: function every(callbackfn /* , thisArg */) {
    return $every(this, callbackfn, arguments[1]);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.fill.js":
/***/ (function(module, exports, __webpack_require__) {

// 22.1.3.6 Array.prototype.fill(value, start = 0, end = this.length)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.P, 'Array', { fill: __webpack_require__("./node_modules/core-js/modules/_array-fill.js") });

__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")('fill');


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.filter.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $filter = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(2);

$export($export.P + $export.F * !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].filter, true), 'Array', {
  // 22.1.3.7 / 15.4.4.20 Array.prototype.filter(callbackfn [, thisArg])
  filter: function filter(callbackfn /* , thisArg */) {
    return $filter(this, callbackfn, arguments[1]);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.find-index.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 22.1.3.9 Array.prototype.findIndex(predicate, thisArg = undefined)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $find = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(6);
var KEY = 'findIndex';
var forced = true;
// Shouldn't skip holes
if (KEY in []) Array(1)[KEY](function () { forced = false; });
$export($export.P + $export.F * forced, 'Array', {
  findIndex: function findIndex(callbackfn /* , that = undefined */) {
    return $find(this, callbackfn, arguments.length > 1 ? arguments[1] : undefined);
  }
});
__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")(KEY);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.find.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 22.1.3.8 Array.prototype.find(predicate, thisArg = undefined)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $find = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(5);
var KEY = 'find';
var forced = true;
// Shouldn't skip holes
if (KEY in []) Array(1)[KEY](function () { forced = false; });
$export($export.P + $export.F * forced, 'Array', {
  find: function find(callbackfn /* , that = undefined */) {
    return $find(this, callbackfn, arguments.length > 1 ? arguments[1] : undefined);
  }
});
__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")(KEY);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.for-each.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $forEach = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(0);
var STRICT = __webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].forEach, true);

$export($export.P + $export.F * !STRICT, 'Array', {
  // 22.1.3.10 / 15.4.4.18 Array.prototype.forEach(callbackfn [, thisArg])
  forEach: function forEach(callbackfn /* , thisArg */) {
    return $forEach(this, callbackfn, arguments[1]);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.from.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var call = __webpack_require__("./node_modules/core-js/modules/_iter-call.js");
var isArrayIter = __webpack_require__("./node_modules/core-js/modules/_is-array-iter.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var createProperty = __webpack_require__("./node_modules/core-js/modules/_create-property.js");
var getIterFn = __webpack_require__("./node_modules/core-js/modules/core.get-iterator-method.js");

$export($export.S + $export.F * !__webpack_require__("./node_modules/core-js/modules/_iter-detect.js")(function (iter) { Array.from(iter); }), 'Array', {
  // 22.1.2.1 Array.from(arrayLike, mapfn = undefined, thisArg = undefined)
  from: function from(arrayLike /* , mapfn = undefined, thisArg = undefined */) {
    var O = toObject(arrayLike);
    var C = typeof this == 'function' ? this : Array;
    var aLen = arguments.length;
    var mapfn = aLen > 1 ? arguments[1] : undefined;
    var mapping = mapfn !== undefined;
    var index = 0;
    var iterFn = getIterFn(O);
    var length, result, step, iterator;
    if (mapping) mapfn = ctx(mapfn, aLen > 2 ? arguments[2] : undefined, 2);
    // if object isn't iterable or it's array with default iterator - use simple case
    if (iterFn != undefined && !(C == Array && isArrayIter(iterFn))) {
      for (iterator = iterFn.call(O), result = new C(); !(step = iterator.next()).done; index++) {
        createProperty(result, index, mapping ? call(iterator, mapfn, [step.value, index], true) : step.value);
      }
    } else {
      length = toLength(O.length);
      for (result = new C(length); length > index; index++) {
        createProperty(result, index, mapping ? mapfn(O[index], index) : O[index]);
      }
    }
    result.length = index;
    return result;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.index-of.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $indexOf = __webpack_require__("./node_modules/core-js/modules/_array-includes.js")(false);
var $native = [].indexOf;
var NEGATIVE_ZERO = !!$native && 1 / [1].indexOf(1, -0) < 0;

$export($export.P + $export.F * (NEGATIVE_ZERO || !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")($native)), 'Array', {
  // 22.1.3.11 / 15.4.4.14 Array.prototype.indexOf(searchElement [, fromIndex])
  indexOf: function indexOf(searchElement /* , fromIndex = 0 */) {
    return NEGATIVE_ZERO
      // convert -0 to +0
      ? $native.apply(this, arguments) || 0
      : $indexOf(this, searchElement, arguments[1]);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.is-array.js":
/***/ (function(module, exports, __webpack_require__) {

// 22.1.2.2 / 15.4.3.2 Array.isArray(arg)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Array', { isArray: __webpack_require__("./node_modules/core-js/modules/_is-array.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.iterator.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var addToUnscopables = __webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js");
var step = __webpack_require__("./node_modules/core-js/modules/_iter-step.js");
var Iterators = __webpack_require__("./node_modules/core-js/modules/_iterators.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");

// 22.1.3.4 Array.prototype.entries()
// 22.1.3.13 Array.prototype.keys()
// 22.1.3.29 Array.prototype.values()
// 22.1.3.30 Array.prototype[@@iterator]()
module.exports = __webpack_require__("./node_modules/core-js/modules/_iter-define.js")(Array, 'Array', function (iterated, kind) {
  this._t = toIObject(iterated); // target
  this._i = 0;                   // next index
  this._k = kind;                // kind
// 22.1.5.2.1 %ArrayIteratorPrototype%.next()
}, function () {
  var O = this._t;
  var kind = this._k;
  var index = this._i++;
  if (!O || index >= O.length) {
    this._t = undefined;
    return step(1);
  }
  if (kind == 'keys') return step(0, index);
  if (kind == 'values') return step(0, O[index]);
  return step(0, [index, O[index]]);
}, 'values');

// argumentsList[@@iterator] is %ArrayProto_values% (9.4.4.6, 9.4.4.7)
Iterators.Arguments = Iterators.Array;

addToUnscopables('keys');
addToUnscopables('values');
addToUnscopables('entries');


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.join.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 22.1.3.13 Array.prototype.join(separator)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var arrayJoin = [].join;

// fallback for not array-like strings
$export($export.P + $export.F * (__webpack_require__("./node_modules/core-js/modules/_iobject.js") != Object || !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")(arrayJoin)), 'Array', {
  join: function join(separator) {
    return arrayJoin.call(toIObject(this), separator === undefined ? ',' : separator);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.last-index-of.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var $native = [].lastIndexOf;
var NEGATIVE_ZERO = !!$native && 1 / [1].lastIndexOf(1, -0) < 0;

$export($export.P + $export.F * (NEGATIVE_ZERO || !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")($native)), 'Array', {
  // 22.1.3.14 / 15.4.4.15 Array.prototype.lastIndexOf(searchElement [, fromIndex])
  lastIndexOf: function lastIndexOf(searchElement /* , fromIndex = @[*-1] */) {
    // convert -0 to +0
    if (NEGATIVE_ZERO) return $native.apply(this, arguments) || 0;
    var O = toIObject(this);
    var length = toLength(O.length);
    var index = length - 1;
    if (arguments.length > 1) index = Math.min(index, toInteger(arguments[1]));
    if (index < 0) index = length + index;
    for (;index >= 0; index--) if (index in O) if (O[index] === searchElement) return index || 0;
    return -1;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.map.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $map = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(1);

$export($export.P + $export.F * !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].map, true), 'Array', {
  // 22.1.3.15 / 15.4.4.19 Array.prototype.map(callbackfn [, thisArg])
  map: function map(callbackfn /* , thisArg */) {
    return $map(this, callbackfn, arguments[1]);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.of.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var createProperty = __webpack_require__("./node_modules/core-js/modules/_create-property.js");

// WebKit Array.of isn't generic
$export($export.S + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  function F() { /* empty */ }
  return !(Array.of.call(F) instanceof F);
}), 'Array', {
  // 22.1.2.3 Array.of( ...items)
  of: function of(/* ...args */) {
    var index = 0;
    var aLen = arguments.length;
    var result = new (typeof this == 'function' ? this : Array)(aLen);
    while (aLen > index) createProperty(result, index, arguments[index++]);
    result.length = aLen;
    return result;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.reduce-right.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $reduce = __webpack_require__("./node_modules/core-js/modules/_array-reduce.js");

$export($export.P + $export.F * !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].reduceRight, true), 'Array', {
  // 22.1.3.19 / 15.4.4.22 Array.prototype.reduceRight(callbackfn [, initialValue])
  reduceRight: function reduceRight(callbackfn /* , initialValue */) {
    return $reduce(this, callbackfn, arguments.length, arguments[1], true);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.reduce.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $reduce = __webpack_require__("./node_modules/core-js/modules/_array-reduce.js");

$export($export.P + $export.F * !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].reduce, true), 'Array', {
  // 22.1.3.18 / 15.4.4.21 Array.prototype.reduce(callbackfn [, initialValue])
  reduce: function reduce(callbackfn /* , initialValue */) {
    return $reduce(this, callbackfn, arguments.length, arguments[1], false);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.slice.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var html = __webpack_require__("./node_modules/core-js/modules/_html.js");
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var arraySlice = [].slice;

// fallback for not array-like ES3 strings and DOM objects
$export($export.P + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  if (html) arraySlice.call(html);
}), 'Array', {
  slice: function slice(begin, end) {
    var len = toLength(this.length);
    var klass = cof(this);
    end = end === undefined ? len : end;
    if (klass == 'Array') return arraySlice.call(this, begin, end);
    var start = toAbsoluteIndex(begin, len);
    var upTo = toAbsoluteIndex(end, len);
    var size = toLength(upTo - start);
    var cloned = new Array(size);
    var i = 0;
    for (; i < size; i++) cloned[i] = klass == 'String'
      ? this.charAt(start + i)
      : this[start + i];
    return cloned;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.some.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $some = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(3);

$export($export.P + $export.F * !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")([].some, true), 'Array', {
  // 22.1.3.23 / 15.4.4.17 Array.prototype.some(callbackfn [, thisArg])
  some: function some(callbackfn /* , thisArg */) {
    return $some(this, callbackfn, arguments[1]);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.sort.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var $sort = [].sort;
var test = [1, 2, 3];

$export($export.P + $export.F * (fails(function () {
  // IE8-
  test.sort(undefined);
}) || !fails(function () {
  // V8 bug
  test.sort(null);
  // Old WebKit
}) || !__webpack_require__("./node_modules/core-js/modules/_strict-method.js")($sort)), 'Array', {
  // 22.1.3.25 Array.prototype.sort(comparefn)
  sort: function sort(comparefn) {
    return comparefn === undefined
      ? $sort.call(toObject(this))
      : $sort.call(toObject(this), aFunction(comparefn));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.array.species.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_set-species.js")('Array');


/***/ }),

/***/ "./node_modules/core-js/modules/es6.date.now.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.3.3.1 / 15.9.4.4 Date.now()
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Date', { now: function () { return new Date().getTime(); } });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.date.to-iso-string.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.3.4.36 / 15.9.5.43 Date.prototype.toISOString()
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toISOString = __webpack_require__("./node_modules/core-js/modules/_date-to-iso-string.js");

// PhantomJS / old WebKit has a broken implementations
$export($export.P + $export.F * (Date.prototype.toISOString !== toISOString), 'Date', {
  toISOString: toISOString
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.date.to-json.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");

$export($export.P + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return new Date(NaN).toJSON() !== null
    || Date.prototype.toJSON.call({ toISOString: function () { return 1; } }) !== 1;
}), 'Date', {
  // eslint-disable-next-line no-unused-vars
  toJSON: function toJSON(key) {
    var O = toObject(this);
    var pv = toPrimitive(O);
    return typeof pv == 'number' && !isFinite(pv) ? null : O.toISOString();
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.date.to-primitive.js":
/***/ (function(module, exports, __webpack_require__) {

var TO_PRIMITIVE = __webpack_require__("./node_modules/core-js/modules/_wks.js")('toPrimitive');
var proto = Date.prototype;

if (!(TO_PRIMITIVE in proto)) __webpack_require__("./node_modules/core-js/modules/_hide.js")(proto, TO_PRIMITIVE, __webpack_require__("./node_modules/core-js/modules/_date-to-primitive.js"));


/***/ }),

/***/ "./node_modules/core-js/modules/es6.date.to-string.js":
/***/ (function(module, exports, __webpack_require__) {

var DateProto = Date.prototype;
var INVALID_DATE = 'Invalid Date';
var TO_STRING = 'toString';
var $toString = DateProto[TO_STRING];
var getTime = DateProto.getTime;
if (new Date(NaN) + '' != INVALID_DATE) {
  __webpack_require__("./node_modules/core-js/modules/_redefine.js")(DateProto, TO_STRING, function toString() {
    var value = getTime.call(this);
    // eslint-disable-next-line no-self-compare
    return value === value ? $toString.call(this) : INVALID_DATE;
  });
}


/***/ }),

/***/ "./node_modules/core-js/modules/es6.function.bind.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.2.3.2 / 15.3.4.5 Function.prototype.bind(thisArg, args...)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.P, 'Function', { bind: __webpack_require__("./node_modules/core-js/modules/_bind.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.function.has-instance.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var HAS_INSTANCE = __webpack_require__("./node_modules/core-js/modules/_wks.js")('hasInstance');
var FunctionProto = Function.prototype;
// 19.2.3.6 Function.prototype[@@hasInstance](V)
if (!(HAS_INSTANCE in FunctionProto)) __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f(FunctionProto, HAS_INSTANCE, { value: function (O) {
  if (typeof this != 'function' || !isObject(O)) return false;
  if (!isObject(this.prototype)) return O instanceof this;
  // for environment w/o native `@@hasInstance` logic enough `instanceof`, but add this:
  while (O = getPrototypeOf(O)) if (this.prototype === O) return true;
  return false;
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.function.name.js":
/***/ (function(module, exports, __webpack_require__) {

var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var FProto = Function.prototype;
var nameRE = /^\s*function ([^ (]*)/;
var NAME = 'name';

// 19.2.4.2 name
NAME in FProto || __webpack_require__("./node_modules/core-js/modules/_descriptors.js") && dP(FProto, NAME, {
  configurable: true,
  get: function () {
    try {
      return ('' + this).match(nameRE)[1];
    } catch (e) {
      return '';
    }
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.map.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var strong = __webpack_require__("./node_modules/core-js/modules/_collection-strong.js");
var validate = __webpack_require__("./node_modules/core-js/modules/_validate-collection.js");
var MAP = 'Map';

// 23.1 Map Objects
module.exports = __webpack_require__("./node_modules/core-js/modules/_collection.js")(MAP, function (get) {
  return function Map() { return get(this, arguments.length > 0 ? arguments[0] : undefined); };
}, {
  // 23.1.3.6 Map.prototype.get(key)
  get: function get(key) {
    var entry = strong.getEntry(validate(this, MAP), key);
    return entry && entry.v;
  },
  // 23.1.3.9 Map.prototype.set(key, value)
  set: function set(key, value) {
    return strong.def(validate(this, MAP), key === 0 ? 0 : key, value);
  }
}, strong, true);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.acosh.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.3 Math.acosh(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var log1p = __webpack_require__("./node_modules/core-js/modules/_math-log1p.js");
var sqrt = Math.sqrt;
var $acosh = Math.acosh;

$export($export.S + $export.F * !($acosh
  // V8 bug: https://code.google.com/p/v8/issues/detail?id=3509
  && Math.floor($acosh(Number.MAX_VALUE)) == 710
  // Tor Browser bug: Math.acosh(Infinity) -> NaN
  && $acosh(Infinity) == Infinity
), 'Math', {
  acosh: function acosh(x) {
    return (x = +x) < 1 ? NaN : x > 94906265.62425156
      ? Math.log(x) + Math.LN2
      : log1p(x - 1 + sqrt(x - 1) * sqrt(x + 1));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.asinh.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.5 Math.asinh(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $asinh = Math.asinh;

function asinh(x) {
  return !isFinite(x = +x) || x == 0 ? x : x < 0 ? -asinh(-x) : Math.log(x + Math.sqrt(x * x + 1));
}

// Tor Browser bug: Math.asinh(0) -> -0
$export($export.S + $export.F * !($asinh && 1 / $asinh(0) > 0), 'Math', { asinh: asinh });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.atanh.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.7 Math.atanh(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $atanh = Math.atanh;

// Tor Browser bug: Math.atanh(-0) -> 0
$export($export.S + $export.F * !($atanh && 1 / $atanh(-0) < 0), 'Math', {
  atanh: function atanh(x) {
    return (x = +x) == 0 ? x : Math.log((1 + x) / (1 - x)) / 2;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.cbrt.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.9 Math.cbrt(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var sign = __webpack_require__("./node_modules/core-js/modules/_math-sign.js");

$export($export.S, 'Math', {
  cbrt: function cbrt(x) {
    return sign(x = +x) * Math.pow(Math.abs(x), 1 / 3);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.clz32.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.11 Math.clz32(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  clz32: function clz32(x) {
    return (x >>>= 0) ? 31 - Math.floor(Math.log(x + 0.5) * Math.LOG2E) : 32;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.cosh.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.12 Math.cosh(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var exp = Math.exp;

$export($export.S, 'Math', {
  cosh: function cosh(x) {
    return (exp(x = +x) + exp(-x)) / 2;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.expm1.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.14 Math.expm1(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $expm1 = __webpack_require__("./node_modules/core-js/modules/_math-expm1.js");

$export($export.S + $export.F * ($expm1 != Math.expm1), 'Math', { expm1: $expm1 });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.fround.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.16 Math.fround(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { fround: __webpack_require__("./node_modules/core-js/modules/_math-fround.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.hypot.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.17 Math.hypot([value1[, value2[, … ]]])
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var abs = Math.abs;

$export($export.S, 'Math', {
  hypot: function hypot(value1, value2) { // eslint-disable-line no-unused-vars
    var sum = 0;
    var i = 0;
    var aLen = arguments.length;
    var larg = 0;
    var arg, div;
    while (i < aLen) {
      arg = abs(arguments[i++]);
      if (larg < arg) {
        div = larg / arg;
        sum = sum * div * div + 1;
        larg = arg;
      } else if (arg > 0) {
        div = arg / larg;
        sum += div * div;
      } else sum += arg;
    }
    return larg === Infinity ? Infinity : larg * Math.sqrt(sum);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.imul.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.18 Math.imul(x, y)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $imul = Math.imul;

// some WebKit versions fails with big numbers, some has wrong arity
$export($export.S + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return $imul(0xffffffff, 5) != -5 || $imul.length != 2;
}), 'Math', {
  imul: function imul(x, y) {
    var UINT16 = 0xffff;
    var xn = +x;
    var yn = +y;
    var xl = UINT16 & xn;
    var yl = UINT16 & yn;
    return 0 | xl * yl + ((UINT16 & xn >>> 16) * yl + xl * (UINT16 & yn >>> 16) << 16 >>> 0);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.log10.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.21 Math.log10(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  log10: function log10(x) {
    return Math.log(x) * Math.LOG10E;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.log1p.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.20 Math.log1p(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { log1p: __webpack_require__("./node_modules/core-js/modules/_math-log1p.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.log2.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.22 Math.log2(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  log2: function log2(x) {
    return Math.log(x) / Math.LN2;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.sign.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.28 Math.sign(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { sign: __webpack_require__("./node_modules/core-js/modules/_math-sign.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.sinh.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.30 Math.sinh(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var expm1 = __webpack_require__("./node_modules/core-js/modules/_math-expm1.js");
var exp = Math.exp;

// V8 near Chromium 38 has a problem with very small numbers
$export($export.S + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return !Math.sinh(-2e-17) != -2e-17;
}), 'Math', {
  sinh: function sinh(x) {
    return Math.abs(x = +x) < 1
      ? (expm1(x) - expm1(-x)) / 2
      : (exp(x - 1) - exp(-x - 1)) * (Math.E / 2);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.tanh.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.33 Math.tanh(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var expm1 = __webpack_require__("./node_modules/core-js/modules/_math-expm1.js");
var exp = Math.exp;

$export($export.S, 'Math', {
  tanh: function tanh(x) {
    var a = expm1(x = +x);
    var b = expm1(-x);
    return a == Infinity ? 1 : b == Infinity ? -1 : (a - b) / (exp(x) + exp(-x));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.math.trunc.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.2.2.34 Math.trunc(x)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  trunc: function trunc(it) {
    return (it > 0 ? Math.floor : Math.ceil)(it);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.constructor.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");
var inheritIfRequired = __webpack_require__("./node_modules/core-js/modules/_inherit-if-required.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var gOPN = __webpack_require__("./node_modules/core-js/modules/_object-gopn.js").f;
var gOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js").f;
var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var $trim = __webpack_require__("./node_modules/core-js/modules/_string-trim.js").trim;
var NUMBER = 'Number';
var $Number = global[NUMBER];
var Base = $Number;
var proto = $Number.prototype;
// Opera ~12 has broken Object#toString
var BROKEN_COF = cof(__webpack_require__("./node_modules/core-js/modules/_object-create.js")(proto)) == NUMBER;
var TRIM = 'trim' in String.prototype;

// 7.1.3 ToNumber(argument)
var toNumber = function (argument) {
  var it = toPrimitive(argument, false);
  if (typeof it == 'string' && it.length > 2) {
    it = TRIM ? it.trim() : $trim(it, 3);
    var first = it.charCodeAt(0);
    var third, radix, maxCode;
    if (first === 43 || first === 45) {
      third = it.charCodeAt(2);
      if (third === 88 || third === 120) return NaN; // Number('+0x1') should be NaN, old V8 fix
    } else if (first === 48) {
      switch (it.charCodeAt(1)) {
        case 66: case 98: radix = 2; maxCode = 49; break; // fast equal /^0b[01]+$/i
        case 79: case 111: radix = 8; maxCode = 55; break; // fast equal /^0o[0-7]+$/i
        default: return +it;
      }
      for (var digits = it.slice(2), i = 0, l = digits.length, code; i < l; i++) {
        code = digits.charCodeAt(i);
        // parseInt parses a string to a first unavailable symbol
        // but ToNumber should return NaN if a string contains unavailable symbols
        if (code < 48 || code > maxCode) return NaN;
      } return parseInt(digits, radix);
    }
  } return +it;
};

if (!$Number(' 0o1') || !$Number('0b1') || $Number('+0x1')) {
  $Number = function Number(value) {
    var it = arguments.length < 1 ? 0 : value;
    var that = this;
    return that instanceof $Number
      // check on 1..constructor(foo) case
      && (BROKEN_COF ? fails(function () { proto.valueOf.call(that); }) : cof(that) != NUMBER)
        ? inheritIfRequired(new Base(toNumber(it)), that, $Number) : toNumber(it);
  };
  for (var keys = __webpack_require__("./node_modules/core-js/modules/_descriptors.js") ? gOPN(Base) : (
    // ES3:
    'MAX_VALUE,MIN_VALUE,NaN,NEGATIVE_INFINITY,POSITIVE_INFINITY,' +
    // ES6 (in case, if modules with ES6 Number statics required before):
    'EPSILON,isFinite,isInteger,isNaN,isSafeInteger,MAX_SAFE_INTEGER,' +
    'MIN_SAFE_INTEGER,parseFloat,parseInt,isInteger'
  ).split(','), j = 0, key; keys.length > j; j++) {
    if (has(Base, key = keys[j]) && !has($Number, key)) {
      dP($Number, key, gOPD(Base, key));
    }
  }
  $Number.prototype = proto;
  proto.constructor = $Number;
  __webpack_require__("./node_modules/core-js/modules/_redefine.js")(global, NUMBER, $Number);
}


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.epsilon.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.1 Number.EPSILON
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Number', { EPSILON: Math.pow(2, -52) });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.is-finite.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.2 Number.isFinite(number)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var _isFinite = __webpack_require__("./node_modules/core-js/modules/_global.js").isFinite;

$export($export.S, 'Number', {
  isFinite: function isFinite(it) {
    return typeof it == 'number' && _isFinite(it);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.is-integer.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.3 Number.isInteger(number)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Number', { isInteger: __webpack_require__("./node_modules/core-js/modules/_is-integer.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.is-nan.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.4 Number.isNaN(number)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Number', {
  isNaN: function isNaN(number) {
    // eslint-disable-next-line no-self-compare
    return number != number;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.is-safe-integer.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.5 Number.isSafeInteger(number)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var isInteger = __webpack_require__("./node_modules/core-js/modules/_is-integer.js");
var abs = Math.abs;

$export($export.S, 'Number', {
  isSafeInteger: function isSafeInteger(number) {
    return isInteger(number) && abs(number) <= 0x1fffffffffffff;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.max-safe-integer.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.6 Number.MAX_SAFE_INTEGER
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Number', { MAX_SAFE_INTEGER: 0x1fffffffffffff });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.min-safe-integer.js":
/***/ (function(module, exports, __webpack_require__) {

// 20.1.2.10 Number.MIN_SAFE_INTEGER
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Number', { MIN_SAFE_INTEGER: -0x1fffffffffffff });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.parse-float.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $parseFloat = __webpack_require__("./node_modules/core-js/modules/_parse-float.js");
// 20.1.2.12 Number.parseFloat(string)
$export($export.S + $export.F * (Number.parseFloat != $parseFloat), 'Number', { parseFloat: $parseFloat });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.parse-int.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $parseInt = __webpack_require__("./node_modules/core-js/modules/_parse-int.js");
// 20.1.2.13 Number.parseInt(string, radix)
$export($export.S + $export.F * (Number.parseInt != $parseInt), 'Number', { parseInt: $parseInt });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.to-fixed.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var aNumberValue = __webpack_require__("./node_modules/core-js/modules/_a-number-value.js");
var repeat = __webpack_require__("./node_modules/core-js/modules/_string-repeat.js");
var $toFixed = 1.0.toFixed;
var floor = Math.floor;
var data = [0, 0, 0, 0, 0, 0];
var ERROR = 'Number.toFixed: incorrect invocation!';
var ZERO = '0';

var multiply = function (n, c) {
  var i = -1;
  var c2 = c;
  while (++i < 6) {
    c2 += n * data[i];
    data[i] = c2 % 1e7;
    c2 = floor(c2 / 1e7);
  }
};
var divide = function (n) {
  var i = 6;
  var c = 0;
  while (--i >= 0) {
    c += data[i];
    data[i] = floor(c / n);
    c = (c % n) * 1e7;
  }
};
var numToString = function () {
  var i = 6;
  var s = '';
  while (--i >= 0) {
    if (s !== '' || i === 0 || data[i] !== 0) {
      var t = String(data[i]);
      s = s === '' ? t : s + repeat.call(ZERO, 7 - t.length) + t;
    }
  } return s;
};
var pow = function (x, n, acc) {
  return n === 0 ? acc : n % 2 === 1 ? pow(x, n - 1, acc * x) : pow(x * x, n / 2, acc);
};
var log = function (x) {
  var n = 0;
  var x2 = x;
  while (x2 >= 4096) {
    n += 12;
    x2 /= 4096;
  }
  while (x2 >= 2) {
    n += 1;
    x2 /= 2;
  } return n;
};

$export($export.P + $export.F * (!!$toFixed && (
  0.00008.toFixed(3) !== '0.000' ||
  0.9.toFixed(0) !== '1' ||
  1.255.toFixed(2) !== '1.25' ||
  1000000000000000128.0.toFixed(0) !== '1000000000000000128'
) || !__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  // V8 ~ Android 4.3-
  $toFixed.call({});
})), 'Number', {
  toFixed: function toFixed(fractionDigits) {
    var x = aNumberValue(this, ERROR);
    var f = toInteger(fractionDigits);
    var s = '';
    var m = ZERO;
    var e, z, j, k;
    if (f < 0 || f > 20) throw RangeError(ERROR);
    // eslint-disable-next-line no-self-compare
    if (x != x) return 'NaN';
    if (x <= -1e21 || x >= 1e21) return String(x);
    if (x < 0) {
      s = '-';
      x = -x;
    }
    if (x > 1e-21) {
      e = log(x * pow(2, 69, 1)) - 69;
      z = e < 0 ? x * pow(2, -e, 1) : x / pow(2, e, 1);
      z *= 0x10000000000000;
      e = 52 - e;
      if (e > 0) {
        multiply(0, z);
        j = f;
        while (j >= 7) {
          multiply(1e7, 0);
          j -= 7;
        }
        multiply(pow(10, j, 1), 0);
        j = e - 1;
        while (j >= 23) {
          divide(1 << 23);
          j -= 23;
        }
        divide(1 << j);
        multiply(1, 1);
        divide(2);
        m = numToString();
      } else {
        multiply(0, z);
        multiply(1 << -e, 0);
        m = numToString() + repeat.call(ZERO, f);
      }
    }
    if (f > 0) {
      k = m.length;
      m = s + (k <= f ? '0.' + repeat.call(ZERO, f - k) + m : m.slice(0, k - f) + '.' + m.slice(k - f));
    } else {
      m = s + m;
    } return m;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.number.to-precision.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var aNumberValue = __webpack_require__("./node_modules/core-js/modules/_a-number-value.js");
var $toPrecision = 1.0.toPrecision;

$export($export.P + $export.F * ($fails(function () {
  // IE7-
  return $toPrecision.call(1, undefined) !== '1';
}) || !$fails(function () {
  // V8 ~ Android 4.3-
  $toPrecision.call({});
})), 'Number', {
  toPrecision: function toPrecision(precision) {
    var that = aNumberValue(this, 'Number#toPrecision: incorrect invocation!');
    return precision === undefined ? $toPrecision.call(that) : $toPrecision.call(that, precision);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.assign.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.3.1 Object.assign(target, source)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S + $export.F, 'Object', { assign: __webpack_require__("./node_modules/core-js/modules/_object-assign.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.create.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
// 19.1.2.2 / 15.2.3.5 Object.create(O [, Properties])
$export($export.S, 'Object', { create: __webpack_require__("./node_modules/core-js/modules/_object-create.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.define-properties.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
// 19.1.2.3 / 15.2.3.7 Object.defineProperties(O, Properties)
$export($export.S + $export.F * !__webpack_require__("./node_modules/core-js/modules/_descriptors.js"), 'Object', { defineProperties: __webpack_require__("./node_modules/core-js/modules/_object-dps.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.define-property.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
// 19.1.2.4 / 15.2.3.6 Object.defineProperty(O, P, Attributes)
$export($export.S + $export.F * !__webpack_require__("./node_modules/core-js/modules/_descriptors.js"), 'Object', { defineProperty: __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.freeze.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.5 Object.freeze(O)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var meta = __webpack_require__("./node_modules/core-js/modules/_meta.js").onFreeze;

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('freeze', function ($freeze) {
  return function freeze(it) {
    return $freeze && isObject(it) ? $freeze(meta(it)) : it;
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.get-own-property-descriptor.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.6 Object.getOwnPropertyDescriptor(O, P)
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var $getOwnPropertyDescriptor = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js").f;

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('getOwnPropertyDescriptor', function () {
  return function getOwnPropertyDescriptor(it, key) {
    return $getOwnPropertyDescriptor(toIObject(it), key);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.get-own-property-names.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.7 Object.getOwnPropertyNames(O)
__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('getOwnPropertyNames', function () {
  return __webpack_require__("./node_modules/core-js/modules/_object-gopn-ext.js").f;
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.get-prototype-of.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.9 Object.getPrototypeOf(O)
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var $getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('getPrototypeOf', function () {
  return function getPrototypeOf(it) {
    return $getPrototypeOf(toObject(it));
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.is-extensible.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.11 Object.isExtensible(O)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('isExtensible', function ($isExtensible) {
  return function isExtensible(it) {
    return isObject(it) ? $isExtensible ? $isExtensible(it) : true : false;
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.is-frozen.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.12 Object.isFrozen(O)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('isFrozen', function ($isFrozen) {
  return function isFrozen(it) {
    return isObject(it) ? $isFrozen ? $isFrozen(it) : false : true;
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.is-sealed.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.13 Object.isSealed(O)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('isSealed', function ($isSealed) {
  return function isSealed(it) {
    return isObject(it) ? $isSealed ? $isSealed(it) : false : true;
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.is.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.3.10 Object.is(value1, value2)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
$export($export.S, 'Object', { is: __webpack_require__("./node_modules/core-js/modules/_same-value.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.keys.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.14 Object.keys(O)
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var $keys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('keys', function () {
  return function keys(it) {
    return $keys(toObject(it));
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.prevent-extensions.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.15 Object.preventExtensions(O)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var meta = __webpack_require__("./node_modules/core-js/modules/_meta.js").onFreeze;

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('preventExtensions', function ($preventExtensions) {
  return function preventExtensions(it) {
    return $preventExtensions && isObject(it) ? $preventExtensions(meta(it)) : it;
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.seal.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.2.17 Object.seal(O)
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var meta = __webpack_require__("./node_modules/core-js/modules/_meta.js").onFreeze;

__webpack_require__("./node_modules/core-js/modules/_object-sap.js")('seal', function ($seal) {
  return function seal(it) {
    return $seal && isObject(it) ? $seal(meta(it)) : it;
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.set-prototype-of.js":
/***/ (function(module, exports, __webpack_require__) {

// 19.1.3.19 Object.setPrototypeOf(O, proto)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
$export($export.S, 'Object', { setPrototypeOf: __webpack_require__("./node_modules/core-js/modules/_set-proto.js").set });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.object.to-string.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 19.1.3.6 Object.prototype.toString()
var classof = __webpack_require__("./node_modules/core-js/modules/_classof.js");
var test = {};
test[__webpack_require__("./node_modules/core-js/modules/_wks.js")('toStringTag')] = 'z';
if (test + '' != '[object z]') {
  __webpack_require__("./node_modules/core-js/modules/_redefine.js")(Object.prototype, 'toString', function toString() {
    return '[object ' + classof(this) + ']';
  }, true);
}


/***/ }),

/***/ "./node_modules/core-js/modules/es6.parse-float.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $parseFloat = __webpack_require__("./node_modules/core-js/modules/_parse-float.js");
// 18.2.4 parseFloat(string)
$export($export.G + $export.F * (parseFloat != $parseFloat), { parseFloat: $parseFloat });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.parse-int.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $parseInt = __webpack_require__("./node_modules/core-js/modules/_parse-int.js");
// 18.2.5 parseInt(string, radix)
$export($export.G + $export.F * (parseInt != $parseInt), { parseInt: $parseInt });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.promise.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var LIBRARY = __webpack_require__("./node_modules/core-js/modules/_library.js");
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var ctx = __webpack_require__("./node_modules/core-js/modules/_ctx.js");
var classof = __webpack_require__("./node_modules/core-js/modules/_classof.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");
var speciesConstructor = __webpack_require__("./node_modules/core-js/modules/_species-constructor.js");
var task = __webpack_require__("./node_modules/core-js/modules/_task.js").set;
var microtask = __webpack_require__("./node_modules/core-js/modules/_microtask.js")();
var newPromiseCapabilityModule = __webpack_require__("./node_modules/core-js/modules/_new-promise-capability.js");
var perform = __webpack_require__("./node_modules/core-js/modules/_perform.js");
var promiseResolve = __webpack_require__("./node_modules/core-js/modules/_promise-resolve.js");
var PROMISE = 'Promise';
var TypeError = global.TypeError;
var process = global.process;
var $Promise = global[PROMISE];
var isNode = classof(process) == 'process';
var empty = function () { /* empty */ };
var Internal, newGenericPromiseCapability, OwnPromiseCapability, Wrapper;
var newPromiseCapability = newGenericPromiseCapability = newPromiseCapabilityModule.f;

var USE_NATIVE = !!function () {
  try {
    // correct subclassing with @@species support
    var promise = $Promise.resolve(1);
    var FakePromise = (promise.constructor = {})[__webpack_require__("./node_modules/core-js/modules/_wks.js")('species')] = function (exec) {
      exec(empty, empty);
    };
    // unhandled rejections tracking support, NodeJS Promise without it fails @@species test
    return (isNode || typeof PromiseRejectionEvent == 'function') && promise.then(empty) instanceof FakePromise;
  } catch (e) { /* empty */ }
}();

// helpers
var isThenable = function (it) {
  var then;
  return isObject(it) && typeof (then = it.then) == 'function' ? then : false;
};
var notify = function (promise, isReject) {
  if (promise._n) return;
  promise._n = true;
  var chain = promise._c;
  microtask(function () {
    var value = promise._v;
    var ok = promise._s == 1;
    var i = 0;
    var run = function (reaction) {
      var handler = ok ? reaction.ok : reaction.fail;
      var resolve = reaction.resolve;
      var reject = reaction.reject;
      var domain = reaction.domain;
      var result, then;
      try {
        if (handler) {
          if (!ok) {
            if (promise._h == 2) onHandleUnhandled(promise);
            promise._h = 1;
          }
          if (handler === true) result = value;
          else {
            if (domain) domain.enter();
            result = handler(value);
            if (domain) domain.exit();
          }
          if (result === reaction.promise) {
            reject(TypeError('Promise-chain cycle'));
          } else if (then = isThenable(result)) {
            then.call(result, resolve, reject);
          } else resolve(result);
        } else reject(value);
      } catch (e) {
        reject(e);
      }
    };
    while (chain.length > i) run(chain[i++]); // variable length - can't use forEach
    promise._c = [];
    promise._n = false;
    if (isReject && !promise._h) onUnhandled(promise);
  });
};
var onUnhandled = function (promise) {
  task.call(global, function () {
    var value = promise._v;
    var unhandled = isUnhandled(promise);
    var result, handler, console;
    if (unhandled) {
      result = perform(function () {
        if (isNode) {
          process.emit('unhandledRejection', value, promise);
        } else if (handler = global.onunhandledrejection) {
          handler({ promise: promise, reason: value });
        } else if ((console = global.console) && console.error) {
          console.error('Unhandled promise rejection', value);
        }
      });
      // Browsers should not trigger `rejectionHandled` event if it was handled here, NodeJS - should
      promise._h = isNode || isUnhandled(promise) ? 2 : 1;
    } promise._a = undefined;
    if (unhandled && result.e) throw result.v;
  });
};
var isUnhandled = function (promise) {
  return promise._h !== 1 && (promise._a || promise._c).length === 0;
};
var onHandleUnhandled = function (promise) {
  task.call(global, function () {
    var handler;
    if (isNode) {
      process.emit('rejectionHandled', promise);
    } else if (handler = global.onrejectionhandled) {
      handler({ promise: promise, reason: promise._v });
    }
  });
};
var $reject = function (value) {
  var promise = this;
  if (promise._d) return;
  promise._d = true;
  promise = promise._w || promise; // unwrap
  promise._v = value;
  promise._s = 2;
  if (!promise._a) promise._a = promise._c.slice();
  notify(promise, true);
};
var $resolve = function (value) {
  var promise = this;
  var then;
  if (promise._d) return;
  promise._d = true;
  promise = promise._w || promise; // unwrap
  try {
    if (promise === value) throw TypeError("Promise can't be resolved itself");
    if (then = isThenable(value)) {
      microtask(function () {
        var wrapper = { _w: promise, _d: false }; // wrap
        try {
          then.call(value, ctx($resolve, wrapper, 1), ctx($reject, wrapper, 1));
        } catch (e) {
          $reject.call(wrapper, e);
        }
      });
    } else {
      promise._v = value;
      promise._s = 1;
      notify(promise, false);
    }
  } catch (e) {
    $reject.call({ _w: promise, _d: false }, e); // wrap
  }
};

// constructor polyfill
if (!USE_NATIVE) {
  // 25.4.3.1 Promise(executor)
  $Promise = function Promise(executor) {
    anInstance(this, $Promise, PROMISE, '_h');
    aFunction(executor);
    Internal.call(this);
    try {
      executor(ctx($resolve, this, 1), ctx($reject, this, 1));
    } catch (err) {
      $reject.call(this, err);
    }
  };
  // eslint-disable-next-line no-unused-vars
  Internal = function Promise(executor) {
    this._c = [];             // <- awaiting reactions
    this._a = undefined;      // <- checked in isUnhandled reactions
    this._s = 0;              // <- state
    this._d = false;          // <- done
    this._v = undefined;      // <- value
    this._h = 0;              // <- rejection state, 0 - default, 1 - handled, 2 - unhandled
    this._n = false;          // <- notify
  };
  Internal.prototype = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js")($Promise.prototype, {
    // 25.4.5.3 Promise.prototype.then(onFulfilled, onRejected)
    then: function then(onFulfilled, onRejected) {
      var reaction = newPromiseCapability(speciesConstructor(this, $Promise));
      reaction.ok = typeof onFulfilled == 'function' ? onFulfilled : true;
      reaction.fail = typeof onRejected == 'function' && onRejected;
      reaction.domain = isNode ? process.domain : undefined;
      this._c.push(reaction);
      if (this._a) this._a.push(reaction);
      if (this._s) notify(this, false);
      return reaction.promise;
    },
    // 25.4.5.1 Promise.prototype.catch(onRejected)
    'catch': function (onRejected) {
      return this.then(undefined, onRejected);
    }
  });
  OwnPromiseCapability = function () {
    var promise = new Internal();
    this.promise = promise;
    this.resolve = ctx($resolve, promise, 1);
    this.reject = ctx($reject, promise, 1);
  };
  newPromiseCapabilityModule.f = newPromiseCapability = function (C) {
    return C === $Promise || C === Wrapper
      ? new OwnPromiseCapability(C)
      : newGenericPromiseCapability(C);
  };
}

$export($export.G + $export.W + $export.F * !USE_NATIVE, { Promise: $Promise });
__webpack_require__("./node_modules/core-js/modules/_set-to-string-tag.js")($Promise, PROMISE);
__webpack_require__("./node_modules/core-js/modules/_set-species.js")(PROMISE);
Wrapper = __webpack_require__("./node_modules/core-js/modules/_core.js")[PROMISE];

// statics
$export($export.S + $export.F * !USE_NATIVE, PROMISE, {
  // 25.4.4.5 Promise.reject(r)
  reject: function reject(r) {
    var capability = newPromiseCapability(this);
    var $$reject = capability.reject;
    $$reject(r);
    return capability.promise;
  }
});
$export($export.S + $export.F * (LIBRARY || !USE_NATIVE), PROMISE, {
  // 25.4.4.6 Promise.resolve(x)
  resolve: function resolve(x) {
    return promiseResolve(LIBRARY && this === Wrapper ? $Promise : this, x);
  }
});
$export($export.S + $export.F * !(USE_NATIVE && __webpack_require__("./node_modules/core-js/modules/_iter-detect.js")(function (iter) {
  $Promise.all(iter)['catch'](empty);
})), PROMISE, {
  // 25.4.4.1 Promise.all(iterable)
  all: function all(iterable) {
    var C = this;
    var capability = newPromiseCapability(C);
    var resolve = capability.resolve;
    var reject = capability.reject;
    var result = perform(function () {
      var values = [];
      var index = 0;
      var remaining = 1;
      forOf(iterable, false, function (promise) {
        var $index = index++;
        var alreadyCalled = false;
        values.push(undefined);
        remaining++;
        C.resolve(promise).then(function (value) {
          if (alreadyCalled) return;
          alreadyCalled = true;
          values[$index] = value;
          --remaining || resolve(values);
        }, reject);
      });
      --remaining || resolve(values);
    });
    if (result.e) reject(result.v);
    return capability.promise;
  },
  // 25.4.4.4 Promise.race(iterable)
  race: function race(iterable) {
    var C = this;
    var capability = newPromiseCapability(C);
    var reject = capability.reject;
    var result = perform(function () {
      forOf(iterable, false, function (promise) {
        C.resolve(promise).then(capability.resolve, reject);
      });
    });
    if (result.e) reject(result.v);
    return capability.promise;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.apply.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.1 Reflect.apply(target, thisArgument, argumentsList)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var rApply = (__webpack_require__("./node_modules/core-js/modules/_global.js").Reflect || {}).apply;
var fApply = Function.apply;
// MS Edge argumentsList argument is optional
$export($export.S + $export.F * !__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  rApply(function () { /* empty */ });
}), 'Reflect', {
  apply: function apply(target, thisArgument, argumentsList) {
    var T = aFunction(target);
    var L = anObject(argumentsList);
    return rApply ? rApply(T, thisArgument, L) : fApply.call(T, thisArgument, L);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.construct.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.2 Reflect.construct(target, argumentsList [, newTarget])
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var create = __webpack_require__("./node_modules/core-js/modules/_object-create.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var bind = __webpack_require__("./node_modules/core-js/modules/_bind.js");
var rConstruct = (__webpack_require__("./node_modules/core-js/modules/_global.js").Reflect || {}).construct;

// MS Edge supports only 2 arguments and argumentsList argument is optional
// FF Nightly sets third argument as `new.target`, but does not create `this` from it
var NEW_TARGET_BUG = fails(function () {
  function F() { /* empty */ }
  return !(rConstruct(function () { /* empty */ }, [], F) instanceof F);
});
var ARGS_BUG = !fails(function () {
  rConstruct(function () { /* empty */ });
});

$export($export.S + $export.F * (NEW_TARGET_BUG || ARGS_BUG), 'Reflect', {
  construct: function construct(Target, args /* , newTarget */) {
    aFunction(Target);
    anObject(args);
    var newTarget = arguments.length < 3 ? Target : aFunction(arguments[2]);
    if (ARGS_BUG && !NEW_TARGET_BUG) return rConstruct(Target, args, newTarget);
    if (Target == newTarget) {
      // w/o altered newTarget, optimization for 0-4 arguments
      switch (args.length) {
        case 0: return new Target();
        case 1: return new Target(args[0]);
        case 2: return new Target(args[0], args[1]);
        case 3: return new Target(args[0], args[1], args[2]);
        case 4: return new Target(args[0], args[1], args[2], args[3]);
      }
      // w/o altered newTarget, lot of arguments case
      var $args = [null];
      $args.push.apply($args, args);
      return new (bind.apply(Target, $args))();
    }
    // with altered newTarget, not support built-in constructors
    var proto = newTarget.prototype;
    var instance = create(isObject(proto) ? proto : Object.prototype);
    var result = Function.apply.call(Target, instance, args);
    return isObject(result) ? result : instance;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.define-property.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.3 Reflect.defineProperty(target, propertyKey, attributes)
var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");

// MS Edge has broken Reflect.defineProperty - throwing instead of returning false
$export($export.S + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  // eslint-disable-next-line no-undef
  Reflect.defineProperty(dP.f({}, 1, { value: 1 }), 1, { value: 2 });
}), 'Reflect', {
  defineProperty: function defineProperty(target, propertyKey, attributes) {
    anObject(target);
    propertyKey = toPrimitive(propertyKey, true);
    anObject(attributes);
    try {
      dP.f(target, propertyKey, attributes);
      return true;
    } catch (e) {
      return false;
    }
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.delete-property.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.4 Reflect.deleteProperty(target, propertyKey)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var gOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js").f;
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");

$export($export.S, 'Reflect', {
  deleteProperty: function deleteProperty(target, propertyKey) {
    var desc = gOPD(anObject(target), propertyKey);
    return desc && !desc.configurable ? false : delete target[propertyKey];
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.enumerate.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 26.1.5 Reflect.enumerate(target)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var Enumerate = function (iterated) {
  this._t = anObject(iterated); // target
  this._i = 0;                  // next index
  var keys = this._k = [];      // keys
  var key;
  for (key in iterated) keys.push(key);
};
__webpack_require__("./node_modules/core-js/modules/_iter-create.js")(Enumerate, 'Object', function () {
  var that = this;
  var keys = that._k;
  var key;
  do {
    if (that._i >= keys.length) return { value: undefined, done: true };
  } while (!((key = keys[that._i++]) in that._t));
  return { value: key, done: false };
});

$export($export.S, 'Reflect', {
  enumerate: function enumerate(target) {
    return new Enumerate(target);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.get-own-property-descriptor.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.7 Reflect.getOwnPropertyDescriptor(target, propertyKey)
var gOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");

$export($export.S, 'Reflect', {
  getOwnPropertyDescriptor: function getOwnPropertyDescriptor(target, propertyKey) {
    return gOPD.f(anObject(target), propertyKey);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.get-prototype-of.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.8 Reflect.getPrototypeOf(target)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var getProto = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");

$export($export.S, 'Reflect', {
  getPrototypeOf: function getPrototypeOf(target) {
    return getProto(anObject(target));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.get.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.6 Reflect.get(target, propertyKey [, receiver])
var gOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");

function get(target, propertyKey /* , receiver */) {
  var receiver = arguments.length < 3 ? target : arguments[2];
  var desc, proto;
  if (anObject(target) === receiver) return target[propertyKey];
  if (desc = gOPD.f(target, propertyKey)) return has(desc, 'value')
    ? desc.value
    : desc.get !== undefined
      ? desc.get.call(receiver)
      : undefined;
  if (isObject(proto = getPrototypeOf(target))) return get(proto, propertyKey, receiver);
}

$export($export.S, 'Reflect', { get: get });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.has.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.9 Reflect.has(target, propertyKey)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Reflect', {
  has: function has(target, propertyKey) {
    return propertyKey in target;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.is-extensible.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.10 Reflect.isExtensible(target)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var $isExtensible = Object.isExtensible;

$export($export.S, 'Reflect', {
  isExtensible: function isExtensible(target) {
    anObject(target);
    return $isExtensible ? $isExtensible(target) : true;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.own-keys.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.11 Reflect.ownKeys(target)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Reflect', { ownKeys: __webpack_require__("./node_modules/core-js/modules/_own-keys.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.prevent-extensions.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.12 Reflect.preventExtensions(target)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var $preventExtensions = Object.preventExtensions;

$export($export.S, 'Reflect', {
  preventExtensions: function preventExtensions(target) {
    anObject(target);
    try {
      if ($preventExtensions) $preventExtensions(target);
      return true;
    } catch (e) {
      return false;
    }
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.set-prototype-of.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.14 Reflect.setPrototypeOf(target, proto)
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var setProto = __webpack_require__("./node_modules/core-js/modules/_set-proto.js");

if (setProto) $export($export.S, 'Reflect', {
  setPrototypeOf: function setPrototypeOf(target, proto) {
    setProto.check(target, proto);
    try {
      setProto.set(target, proto);
      return true;
    } catch (e) {
      return false;
    }
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.reflect.set.js":
/***/ (function(module, exports, __webpack_require__) {

// 26.1.13 Reflect.set(target, propertyKey, V [, receiver])
var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var gOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var createDesc = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");

function set(target, propertyKey, V /* , receiver */) {
  var receiver = arguments.length < 4 ? target : arguments[3];
  var ownDesc = gOPD.f(anObject(target), propertyKey);
  var existingDescriptor, proto;
  if (!ownDesc) {
    if (isObject(proto = getPrototypeOf(target))) {
      return set(proto, propertyKey, V, receiver);
    }
    ownDesc = createDesc(0);
  }
  if (has(ownDesc, 'value')) {
    if (ownDesc.writable === false || !isObject(receiver)) return false;
    existingDescriptor = gOPD.f(receiver, propertyKey) || createDesc(0);
    existingDescriptor.value = V;
    dP.f(receiver, propertyKey, existingDescriptor);
    return true;
  }
  return ownDesc.set === undefined ? false : (ownDesc.set.call(receiver, V), true);
}

$export($export.S, 'Reflect', { set: set });


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.constructor.js":
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var inheritIfRequired = __webpack_require__("./node_modules/core-js/modules/_inherit-if-required.js");
var dP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f;
var gOPN = __webpack_require__("./node_modules/core-js/modules/_object-gopn.js").f;
var isRegExp = __webpack_require__("./node_modules/core-js/modules/_is-regexp.js");
var $flags = __webpack_require__("./node_modules/core-js/modules/_flags.js");
var $RegExp = global.RegExp;
var Base = $RegExp;
var proto = $RegExp.prototype;
var re1 = /a/g;
var re2 = /a/g;
// "new" creates a new object, old webkit buggy here
var CORRECT_NEW = new $RegExp(re1) !== re1;

if (__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && (!CORRECT_NEW || __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  re2[__webpack_require__("./node_modules/core-js/modules/_wks.js")('match')] = false;
  // RegExp constructor can alter flags and IsRegExp works correct with @@match
  return $RegExp(re1) != re1 || $RegExp(re2) == re2 || $RegExp(re1, 'i') != '/a/i';
}))) {
  $RegExp = function RegExp(p, f) {
    var tiRE = this instanceof $RegExp;
    var piRE = isRegExp(p);
    var fiU = f === undefined;
    return !tiRE && piRE && p.constructor === $RegExp && fiU ? p
      : inheritIfRequired(CORRECT_NEW
        ? new Base(piRE && !fiU ? p.source : p, f)
        : Base((piRE = p instanceof $RegExp) ? p.source : p, piRE && fiU ? $flags.call(p) : f)
      , tiRE ? this : proto, $RegExp);
  };
  var proxy = function (key) {
    key in $RegExp || dP($RegExp, key, {
      configurable: true,
      get: function () { return Base[key]; },
      set: function (it) { Base[key] = it; }
    });
  };
  for (var keys = gOPN(Base), i = 0; keys.length > i;) proxy(keys[i++]);
  proto.constructor = $RegExp;
  $RegExp.prototype = proto;
  __webpack_require__("./node_modules/core-js/modules/_redefine.js")(global, 'RegExp', $RegExp);
}

__webpack_require__("./node_modules/core-js/modules/_set-species.js")('RegExp');


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.flags.js":
/***/ (function(module, exports, __webpack_require__) {

// 21.2.5.3 get RegExp.prototype.flags()
if (__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && /./g.flags != 'g') __webpack_require__("./node_modules/core-js/modules/_object-dp.js").f(RegExp.prototype, 'flags', {
  configurable: true,
  get: __webpack_require__("./node_modules/core-js/modules/_flags.js")
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.match.js":
/***/ (function(module, exports, __webpack_require__) {

// @@match logic
__webpack_require__("./node_modules/core-js/modules/_fix-re-wks.js")('match', 1, function (defined, MATCH, $match) {
  // 21.1.3.11 String.prototype.match(regexp)
  return [function match(regexp) {
    'use strict';
    var O = defined(this);
    var fn = regexp == undefined ? undefined : regexp[MATCH];
    return fn !== undefined ? fn.call(regexp, O) : new RegExp(regexp)[MATCH](String(O));
  }, $match];
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.replace.js":
/***/ (function(module, exports, __webpack_require__) {

// @@replace logic
__webpack_require__("./node_modules/core-js/modules/_fix-re-wks.js")('replace', 2, function (defined, REPLACE, $replace) {
  // 21.1.3.14 String.prototype.replace(searchValue, replaceValue)
  return [function replace(searchValue, replaceValue) {
    'use strict';
    var O = defined(this);
    var fn = searchValue == undefined ? undefined : searchValue[REPLACE];
    return fn !== undefined
      ? fn.call(searchValue, O, replaceValue)
      : $replace.call(String(O), searchValue, replaceValue);
  }, $replace];
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.search.js":
/***/ (function(module, exports, __webpack_require__) {

// @@search logic
__webpack_require__("./node_modules/core-js/modules/_fix-re-wks.js")('search', 1, function (defined, SEARCH, $search) {
  // 21.1.3.15 String.prototype.search(regexp)
  return [function search(regexp) {
    'use strict';
    var O = defined(this);
    var fn = regexp == undefined ? undefined : regexp[SEARCH];
    return fn !== undefined ? fn.call(regexp, O) : new RegExp(regexp)[SEARCH](String(O));
  }, $search];
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.split.js":
/***/ (function(module, exports, __webpack_require__) {

// @@split logic
__webpack_require__("./node_modules/core-js/modules/_fix-re-wks.js")('split', 2, function (defined, SPLIT, $split) {
  'use strict';
  var isRegExp = __webpack_require__("./node_modules/core-js/modules/_is-regexp.js");
  var _split = $split;
  var $push = [].push;
  var $SPLIT = 'split';
  var LENGTH = 'length';
  var LAST_INDEX = 'lastIndex';
  if (
    'abbc'[$SPLIT](/(b)*/)[1] == 'c' ||
    'test'[$SPLIT](/(?:)/, -1)[LENGTH] != 4 ||
    'ab'[$SPLIT](/(?:ab)*/)[LENGTH] != 2 ||
    '.'[$SPLIT](/(.?)(.?)/)[LENGTH] != 4 ||
    '.'[$SPLIT](/()()/)[LENGTH] > 1 ||
    ''[$SPLIT](/.?/)[LENGTH]
  ) {
    var NPCG = /()??/.exec('')[1] === undefined; // nonparticipating capturing group
    // based on es5-shim implementation, need to rework it
    $split = function (separator, limit) {
      var string = String(this);
      if (separator === undefined && limit === 0) return [];
      // If `separator` is not a regex, use native split
      if (!isRegExp(separator)) return _split.call(string, separator, limit);
      var output = [];
      var flags = (separator.ignoreCase ? 'i' : '') +
                  (separator.multiline ? 'm' : '') +
                  (separator.unicode ? 'u' : '') +
                  (separator.sticky ? 'y' : '');
      var lastLastIndex = 0;
      var splitLimit = limit === undefined ? 4294967295 : limit >>> 0;
      // Make `global` and avoid `lastIndex` issues by working with a copy
      var separatorCopy = new RegExp(separator.source, flags + 'g');
      var separator2, match, lastIndex, lastLength, i;
      // Doesn't need flags gy, but they don't hurt
      if (!NPCG) separator2 = new RegExp('^' + separatorCopy.source + '$(?!\\s)', flags);
      while (match = separatorCopy.exec(string)) {
        // `separatorCopy.lastIndex` is not reliable cross-browser
        lastIndex = match.index + match[0][LENGTH];
        if (lastIndex > lastLastIndex) {
          output.push(string.slice(lastLastIndex, match.index));
          // Fix browsers whose `exec` methods don't consistently return `undefined` for NPCG
          // eslint-disable-next-line no-loop-func
          if (!NPCG && match[LENGTH] > 1) match[0].replace(separator2, function () {
            for (i = 1; i < arguments[LENGTH] - 2; i++) if (arguments[i] === undefined) match[i] = undefined;
          });
          if (match[LENGTH] > 1 && match.index < string[LENGTH]) $push.apply(output, match.slice(1));
          lastLength = match[0][LENGTH];
          lastLastIndex = lastIndex;
          if (output[LENGTH] >= splitLimit) break;
        }
        if (separatorCopy[LAST_INDEX] === match.index) separatorCopy[LAST_INDEX]++; // Avoid an infinite loop
      }
      if (lastLastIndex === string[LENGTH]) {
        if (lastLength || !separatorCopy.test('')) output.push('');
      } else output.push(string.slice(lastLastIndex));
      return output[LENGTH] > splitLimit ? output.slice(0, splitLimit) : output;
    };
  // Chakra, V8
  } else if ('0'[$SPLIT](undefined, 0)[LENGTH]) {
    $split = function (separator, limit) {
      return separator === undefined && limit === 0 ? [] : _split.call(this, separator, limit);
    };
  }
  // 21.1.3.17 String.prototype.split(separator, limit)
  return [function split(separator, limit) {
    var O = defined(this);
    var fn = separator == undefined ? undefined : separator[SPLIT];
    return fn !== undefined ? fn.call(separator, O, limit) : $split.call(String(O), separator, limit);
  }, $split];
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.regexp.to-string.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

__webpack_require__("./node_modules/core-js/modules/es6.regexp.flags.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var $flags = __webpack_require__("./node_modules/core-js/modules/_flags.js");
var DESCRIPTORS = __webpack_require__("./node_modules/core-js/modules/_descriptors.js");
var TO_STRING = 'toString';
var $toString = /./[TO_STRING];

var define = function (fn) {
  __webpack_require__("./node_modules/core-js/modules/_redefine.js")(RegExp.prototype, TO_STRING, fn, true);
};

// 21.2.5.14 RegExp.prototype.toString()
if (__webpack_require__("./node_modules/core-js/modules/_fails.js")(function () { return $toString.call({ source: 'a', flags: 'b' }) != '/a/b'; })) {
  define(function toString() {
    var R = anObject(this);
    return '/'.concat(R.source, '/',
      'flags' in R ? R.flags : !DESCRIPTORS && R instanceof RegExp ? $flags.call(R) : undefined);
  });
// FF44- RegExp#toString has a wrong name
} else if ($toString.name != TO_STRING) {
  define(function toString() {
    return $toString.call(this);
  });
}


/***/ }),

/***/ "./node_modules/core-js/modules/es6.set.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var strong = __webpack_require__("./node_modules/core-js/modules/_collection-strong.js");
var validate = __webpack_require__("./node_modules/core-js/modules/_validate-collection.js");
var SET = 'Set';

// 23.2 Set Objects
module.exports = __webpack_require__("./node_modules/core-js/modules/_collection.js")(SET, function (get) {
  return function Set() { return get(this, arguments.length > 0 ? arguments[0] : undefined); };
}, {
  // 23.2.3.1 Set.prototype.add(value)
  add: function add(value) {
    return strong.def(validate(this, SET), value = value === 0 ? 0 : value, value);
  }
}, strong);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.anchor.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.2 String.prototype.anchor(name)
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('anchor', function (createHTML) {
  return function anchor(name) {
    return createHTML(this, 'a', 'name', name);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.big.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.3 String.prototype.big()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('big', function (createHTML) {
  return function big() {
    return createHTML(this, 'big', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.blink.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.4 String.prototype.blink()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('blink', function (createHTML) {
  return function blink() {
    return createHTML(this, 'blink', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.bold.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.5 String.prototype.bold()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('bold', function (createHTML) {
  return function bold() {
    return createHTML(this, 'b', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.code-point-at.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $at = __webpack_require__("./node_modules/core-js/modules/_string-at.js")(false);
$export($export.P, 'String', {
  // 21.1.3.3 String.prototype.codePointAt(pos)
  codePointAt: function codePointAt(pos) {
    return $at(this, pos);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.ends-with.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
// 21.1.3.6 String.prototype.endsWith(searchString [, endPosition])

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var context = __webpack_require__("./node_modules/core-js/modules/_string-context.js");
var ENDS_WITH = 'endsWith';
var $endsWith = ''[ENDS_WITH];

$export($export.P + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails-is-regexp.js")(ENDS_WITH), 'String', {
  endsWith: function endsWith(searchString /* , endPosition = @length */) {
    var that = context(this, searchString, ENDS_WITH);
    var endPosition = arguments.length > 1 ? arguments[1] : undefined;
    var len = toLength(that.length);
    var end = endPosition === undefined ? len : Math.min(toLength(endPosition), len);
    var search = String(searchString);
    return $endsWith
      ? $endsWith.call(that, search, end)
      : that.slice(end - search.length, end) === search;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.fixed.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.6 String.prototype.fixed()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('fixed', function (createHTML) {
  return function fixed() {
    return createHTML(this, 'tt', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.fontcolor.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.7 String.prototype.fontcolor(color)
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('fontcolor', function (createHTML) {
  return function fontcolor(color) {
    return createHTML(this, 'font', 'color', color);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.fontsize.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.8 String.prototype.fontsize(size)
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('fontsize', function (createHTML) {
  return function fontsize(size) {
    return createHTML(this, 'font', 'size', size);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.from-code-point.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
var fromCharCode = String.fromCharCode;
var $fromCodePoint = String.fromCodePoint;

// length should be 1, old FF problem
$export($export.S + $export.F * (!!$fromCodePoint && $fromCodePoint.length != 1), 'String', {
  // 21.1.2.2 String.fromCodePoint(...codePoints)
  fromCodePoint: function fromCodePoint(x) { // eslint-disable-line no-unused-vars
    var res = [];
    var aLen = arguments.length;
    var i = 0;
    var code;
    while (aLen > i) {
      code = +arguments[i++];
      if (toAbsoluteIndex(code, 0x10ffff) !== code) throw RangeError(code + ' is not a valid code point');
      res.push(code < 0x10000
        ? fromCharCode(code)
        : fromCharCode(((code -= 0x10000) >> 10) + 0xd800, code % 0x400 + 0xdc00)
      );
    } return res.join('');
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.includes.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
// 21.1.3.7 String.prototype.includes(searchString, position = 0)

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var context = __webpack_require__("./node_modules/core-js/modules/_string-context.js");
var INCLUDES = 'includes';

$export($export.P + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails-is-regexp.js")(INCLUDES), 'String', {
  includes: function includes(searchString /* , position = 0 */) {
    return !!~context(this, searchString, INCLUDES)
      .indexOf(searchString, arguments.length > 1 ? arguments[1] : undefined);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.italics.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.9 String.prototype.italics()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('italics', function (createHTML) {
  return function italics() {
    return createHTML(this, 'i', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.iterator.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $at = __webpack_require__("./node_modules/core-js/modules/_string-at.js")(true);

// 21.1.3.27 String.prototype[@@iterator]()
__webpack_require__("./node_modules/core-js/modules/_iter-define.js")(String, 'String', function (iterated) {
  this._t = String(iterated); // target
  this._i = 0;                // next index
// 21.1.5.2.1 %StringIteratorPrototype%.next()
}, function () {
  var O = this._t;
  var index = this._i;
  var point;
  if (index >= O.length) return { value: undefined, done: true };
  point = $at(O, index);
  this._i += point.length;
  return { value: point, done: false };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.link.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.10 String.prototype.link(url)
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('link', function (createHTML) {
  return function link(url) {
    return createHTML(this, 'a', 'href', url);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.raw.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");

$export($export.S, 'String', {
  // 21.1.2.4 String.raw(callSite, ...substitutions)
  raw: function raw(callSite) {
    var tpl = toIObject(callSite.raw);
    var len = toLength(tpl.length);
    var aLen = arguments.length;
    var res = [];
    var i = 0;
    while (len > i) {
      res.push(String(tpl[i++]));
      if (i < aLen) res.push(String(arguments[i]));
    } return res.join('');
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.repeat.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.P, 'String', {
  // 21.1.3.13 String.prototype.repeat(count)
  repeat: __webpack_require__("./node_modules/core-js/modules/_string-repeat.js")
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.small.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.11 String.prototype.small()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('small', function (createHTML) {
  return function small() {
    return createHTML(this, 'small', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.starts-with.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
// 21.1.3.18 String.prototype.startsWith(searchString [, position ])

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var context = __webpack_require__("./node_modules/core-js/modules/_string-context.js");
var STARTS_WITH = 'startsWith';
var $startsWith = ''[STARTS_WITH];

$export($export.P + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails-is-regexp.js")(STARTS_WITH), 'String', {
  startsWith: function startsWith(searchString /* , position = 0 */) {
    var that = context(this, searchString, STARTS_WITH);
    var index = toLength(Math.min(arguments.length > 1 ? arguments[1] : undefined, that.length));
    var search = String(searchString);
    return $startsWith
      ? $startsWith.call(that, search, index)
      : that.slice(index, index + search.length) === search;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.strike.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.12 String.prototype.strike()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('strike', function (createHTML) {
  return function strike() {
    return createHTML(this, 'strike', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.sub.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.13 String.prototype.sub()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('sub', function (createHTML) {
  return function sub() {
    return createHTML(this, 'sub', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.sup.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// B.2.3.14 String.prototype.sup()
__webpack_require__("./node_modules/core-js/modules/_string-html.js")('sup', function (createHTML) {
  return function sup() {
    return createHTML(this, 'sup', '', '');
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.string.trim.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// 21.1.3.25 String.prototype.trim()
__webpack_require__("./node_modules/core-js/modules/_string-trim.js")('trim', function ($trim) {
  return function trim() {
    return $trim(this, 3);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.symbol.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// ECMAScript 6 symbols shim
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var has = __webpack_require__("./node_modules/core-js/modules/_has.js");
var DESCRIPTORS = __webpack_require__("./node_modules/core-js/modules/_descriptors.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var META = __webpack_require__("./node_modules/core-js/modules/_meta.js").KEY;
var $fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var shared = __webpack_require__("./node_modules/core-js/modules/_shared.js");
var setToStringTag = __webpack_require__("./node_modules/core-js/modules/_set-to-string-tag.js");
var uid = __webpack_require__("./node_modules/core-js/modules/_uid.js");
var wks = __webpack_require__("./node_modules/core-js/modules/_wks.js");
var wksExt = __webpack_require__("./node_modules/core-js/modules/_wks-ext.js");
var wksDefine = __webpack_require__("./node_modules/core-js/modules/_wks-define.js");
var enumKeys = __webpack_require__("./node_modules/core-js/modules/_enum-keys.js");
var isArray = __webpack_require__("./node_modules/core-js/modules/_is-array.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var createDesc = __webpack_require__("./node_modules/core-js/modules/_property-desc.js");
var _create = __webpack_require__("./node_modules/core-js/modules/_object-create.js");
var gOPNExt = __webpack_require__("./node_modules/core-js/modules/_object-gopn-ext.js");
var $GOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js");
var $DP = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");
var $keys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");
var gOPD = $GOPD.f;
var dP = $DP.f;
var gOPN = gOPNExt.f;
var $Symbol = global.Symbol;
var $JSON = global.JSON;
var _stringify = $JSON && $JSON.stringify;
var PROTOTYPE = 'prototype';
var HIDDEN = wks('_hidden');
var TO_PRIMITIVE = wks('toPrimitive');
var isEnum = {}.propertyIsEnumerable;
var SymbolRegistry = shared('symbol-registry');
var AllSymbols = shared('symbols');
var OPSymbols = shared('op-symbols');
var ObjectProto = Object[PROTOTYPE];
var USE_NATIVE = typeof $Symbol == 'function';
var QObject = global.QObject;
// Don't use setters in Qt Script, https://github.com/zloirock/core-js/issues/173
var setter = !QObject || !QObject[PROTOTYPE] || !QObject[PROTOTYPE].findChild;

// fallback for old Android, https://code.google.com/p/v8/issues/detail?id=687
var setSymbolDesc = DESCRIPTORS && $fails(function () {
  return _create(dP({}, 'a', {
    get: function () { return dP(this, 'a', { value: 7 }).a; }
  })).a != 7;
}) ? function (it, key, D) {
  var protoDesc = gOPD(ObjectProto, key);
  if (protoDesc) delete ObjectProto[key];
  dP(it, key, D);
  if (protoDesc && it !== ObjectProto) dP(ObjectProto, key, protoDesc);
} : dP;

var wrap = function (tag) {
  var sym = AllSymbols[tag] = _create($Symbol[PROTOTYPE]);
  sym._k = tag;
  return sym;
};

var isSymbol = USE_NATIVE && typeof $Symbol.iterator == 'symbol' ? function (it) {
  return typeof it == 'symbol';
} : function (it) {
  return it instanceof $Symbol;
};

var $defineProperty = function defineProperty(it, key, D) {
  if (it === ObjectProto) $defineProperty(OPSymbols, key, D);
  anObject(it);
  key = toPrimitive(key, true);
  anObject(D);
  if (has(AllSymbols, key)) {
    if (!D.enumerable) {
      if (!has(it, HIDDEN)) dP(it, HIDDEN, createDesc(1, {}));
      it[HIDDEN][key] = true;
    } else {
      if (has(it, HIDDEN) && it[HIDDEN][key]) it[HIDDEN][key] = false;
      D = _create(D, { enumerable: createDesc(0, false) });
    } return setSymbolDesc(it, key, D);
  } return dP(it, key, D);
};
var $defineProperties = function defineProperties(it, P) {
  anObject(it);
  var keys = enumKeys(P = toIObject(P));
  var i = 0;
  var l = keys.length;
  var key;
  while (l > i) $defineProperty(it, key = keys[i++], P[key]);
  return it;
};
var $create = function create(it, P) {
  return P === undefined ? _create(it) : $defineProperties(_create(it), P);
};
var $propertyIsEnumerable = function propertyIsEnumerable(key) {
  var E = isEnum.call(this, key = toPrimitive(key, true));
  if (this === ObjectProto && has(AllSymbols, key) && !has(OPSymbols, key)) return false;
  return E || !has(this, key) || !has(AllSymbols, key) || has(this, HIDDEN) && this[HIDDEN][key] ? E : true;
};
var $getOwnPropertyDescriptor = function getOwnPropertyDescriptor(it, key) {
  it = toIObject(it);
  key = toPrimitive(key, true);
  if (it === ObjectProto && has(AllSymbols, key) && !has(OPSymbols, key)) return;
  var D = gOPD(it, key);
  if (D && has(AllSymbols, key) && !(has(it, HIDDEN) && it[HIDDEN][key])) D.enumerable = true;
  return D;
};
var $getOwnPropertyNames = function getOwnPropertyNames(it) {
  var names = gOPN(toIObject(it));
  var result = [];
  var i = 0;
  var key;
  while (names.length > i) {
    if (!has(AllSymbols, key = names[i++]) && key != HIDDEN && key != META) result.push(key);
  } return result;
};
var $getOwnPropertySymbols = function getOwnPropertySymbols(it) {
  var IS_OP = it === ObjectProto;
  var names = gOPN(IS_OP ? OPSymbols : toIObject(it));
  var result = [];
  var i = 0;
  var key;
  while (names.length > i) {
    if (has(AllSymbols, key = names[i++]) && (IS_OP ? has(ObjectProto, key) : true)) result.push(AllSymbols[key]);
  } return result;
};

// 19.4.1.1 Symbol([description])
if (!USE_NATIVE) {
  $Symbol = function Symbol() {
    if (this instanceof $Symbol) throw TypeError('Symbol is not a constructor!');
    var tag = uid(arguments.length > 0 ? arguments[0] : undefined);
    var $set = function (value) {
      if (this === ObjectProto) $set.call(OPSymbols, value);
      if (has(this, HIDDEN) && has(this[HIDDEN], tag)) this[HIDDEN][tag] = false;
      setSymbolDesc(this, tag, createDesc(1, value));
    };
    if (DESCRIPTORS && setter) setSymbolDesc(ObjectProto, tag, { configurable: true, set: $set });
    return wrap(tag);
  };
  redefine($Symbol[PROTOTYPE], 'toString', function toString() {
    return this._k;
  });

  $GOPD.f = $getOwnPropertyDescriptor;
  $DP.f = $defineProperty;
  __webpack_require__("./node_modules/core-js/modules/_object-gopn.js").f = gOPNExt.f = $getOwnPropertyNames;
  __webpack_require__("./node_modules/core-js/modules/_object-pie.js").f = $propertyIsEnumerable;
  __webpack_require__("./node_modules/core-js/modules/_object-gops.js").f = $getOwnPropertySymbols;

  if (DESCRIPTORS && !__webpack_require__("./node_modules/core-js/modules/_library.js")) {
    redefine(ObjectProto, 'propertyIsEnumerable', $propertyIsEnumerable, true);
  }

  wksExt.f = function (name) {
    return wrap(wks(name));
  };
}

$export($export.G + $export.W + $export.F * !USE_NATIVE, { Symbol: $Symbol });

for (var es6Symbols = (
  // 19.4.2.2, 19.4.2.3, 19.4.2.4, 19.4.2.6, 19.4.2.8, 19.4.2.9, 19.4.2.10, 19.4.2.11, 19.4.2.12, 19.4.2.13, 19.4.2.14
  'hasInstance,isConcatSpreadable,iterator,match,replace,search,species,split,toPrimitive,toStringTag,unscopables'
).split(','), j = 0; es6Symbols.length > j;)wks(es6Symbols[j++]);

for (var wellKnownSymbols = $keys(wks.store), k = 0; wellKnownSymbols.length > k;) wksDefine(wellKnownSymbols[k++]);

$export($export.S + $export.F * !USE_NATIVE, 'Symbol', {
  // 19.4.2.1 Symbol.for(key)
  'for': function (key) {
    return has(SymbolRegistry, key += '')
      ? SymbolRegistry[key]
      : SymbolRegistry[key] = $Symbol(key);
  },
  // 19.4.2.5 Symbol.keyFor(sym)
  keyFor: function keyFor(sym) {
    if (!isSymbol(sym)) throw TypeError(sym + ' is not a symbol!');
    for (var key in SymbolRegistry) if (SymbolRegistry[key] === sym) return key;
  },
  useSetter: function () { setter = true; },
  useSimple: function () { setter = false; }
});

$export($export.S + $export.F * !USE_NATIVE, 'Object', {
  // 19.1.2.2 Object.create(O [, Properties])
  create: $create,
  // 19.1.2.4 Object.defineProperty(O, P, Attributes)
  defineProperty: $defineProperty,
  // 19.1.2.3 Object.defineProperties(O, Properties)
  defineProperties: $defineProperties,
  // 19.1.2.6 Object.getOwnPropertyDescriptor(O, P)
  getOwnPropertyDescriptor: $getOwnPropertyDescriptor,
  // 19.1.2.7 Object.getOwnPropertyNames(O)
  getOwnPropertyNames: $getOwnPropertyNames,
  // 19.1.2.8 Object.getOwnPropertySymbols(O)
  getOwnPropertySymbols: $getOwnPropertySymbols
});

// 24.3.2 JSON.stringify(value [, replacer [, space]])
$JSON && $export($export.S + $export.F * (!USE_NATIVE || $fails(function () {
  var S = $Symbol();
  // MS Edge converts symbol values to JSON as {}
  // WebKit converts symbol values to JSON as null
  // V8 throws on boxed symbols
  return _stringify([S]) != '[null]' || _stringify({ a: S }) != '{}' || _stringify(Object(S)) != '{}';
})), 'JSON', {
  stringify: function stringify(it) {
    var args = [it];
    var i = 1;
    var replacer, $replacer;
    while (arguments.length > i) args.push(arguments[i++]);
    $replacer = replacer = args[1];
    if (!isObject(replacer) && it === undefined || isSymbol(it)) return; // IE8 returns string on undefined
    if (!isArray(replacer)) replacer = function (key, value) {
      if (typeof $replacer == 'function') value = $replacer.call(this, key, value);
      if (!isSymbol(value)) return value;
    };
    args[1] = replacer;
    return _stringify.apply($JSON, args);
  }
});

// 19.4.3.4 Symbol.prototype[@@toPrimitive](hint)
$Symbol[PROTOTYPE][TO_PRIMITIVE] || __webpack_require__("./node_modules/core-js/modules/_hide.js")($Symbol[PROTOTYPE], TO_PRIMITIVE, $Symbol[PROTOTYPE].valueOf);
// 19.4.3.5 Symbol.prototype[@@toStringTag]
setToStringTag($Symbol, 'Symbol');
// 20.2.1.9 Math[@@toStringTag]
setToStringTag(Math, 'Math', true);
// 24.3.3 JSON[@@toStringTag]
setToStringTag(global.JSON, 'JSON', true);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.array-buffer.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $typed = __webpack_require__("./node_modules/core-js/modules/_typed.js");
var buffer = __webpack_require__("./node_modules/core-js/modules/_typed-buffer.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var toAbsoluteIndex = __webpack_require__("./node_modules/core-js/modules/_to-absolute-index.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var ArrayBuffer = __webpack_require__("./node_modules/core-js/modules/_global.js").ArrayBuffer;
var speciesConstructor = __webpack_require__("./node_modules/core-js/modules/_species-constructor.js");
var $ArrayBuffer = buffer.ArrayBuffer;
var $DataView = buffer.DataView;
var $isView = $typed.ABV && ArrayBuffer.isView;
var $slice = $ArrayBuffer.prototype.slice;
var VIEW = $typed.VIEW;
var ARRAY_BUFFER = 'ArrayBuffer';

$export($export.G + $export.W + $export.F * (ArrayBuffer !== $ArrayBuffer), { ArrayBuffer: $ArrayBuffer });

$export($export.S + $export.F * !$typed.CONSTR, ARRAY_BUFFER, {
  // 24.1.3.1 ArrayBuffer.isView(arg)
  isView: function isView(it) {
    return $isView && $isView(it) || isObject(it) && VIEW in it;
  }
});

$export($export.P + $export.U + $export.F * __webpack_require__("./node_modules/core-js/modules/_fails.js")(function () {
  return !new $ArrayBuffer(2).slice(1, undefined).byteLength;
}), ARRAY_BUFFER, {
  // 24.1.4.3 ArrayBuffer.prototype.slice(start, end)
  slice: function slice(start, end) {
    if ($slice !== undefined && end === undefined) return $slice.call(anObject(this), start); // FF fix
    var len = anObject(this).byteLength;
    var first = toAbsoluteIndex(start, len);
    var final = toAbsoluteIndex(end === undefined ? len : end, len);
    var result = new (speciesConstructor(this, $ArrayBuffer))(toLength(final - first));
    var viewS = new $DataView(this);
    var viewT = new $DataView(result);
    var index = 0;
    while (first < final) {
      viewT.setUint8(index++, viewS.getUint8(first++));
    } return result;
  }
});

__webpack_require__("./node_modules/core-js/modules/_set-species.js")(ARRAY_BUFFER);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.data-view.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
$export($export.G + $export.W + $export.F * !__webpack_require__("./node_modules/core-js/modules/_typed.js").ABV, {
  DataView: __webpack_require__("./node_modules/core-js/modules/_typed-buffer.js").DataView
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.float32-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Float32', 4, function (init) {
  return function Float32Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.float64-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Float64', 8, function (init) {
  return function Float64Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.int16-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Int16', 2, function (init) {
  return function Int16Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.int32-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Int32', 4, function (init) {
  return function Int32Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.int8-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Int8', 1, function (init) {
  return function Int8Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.uint16-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Uint16', 2, function (init) {
  return function Uint16Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.uint32-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Uint32', 4, function (init) {
  return function Uint32Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.uint8-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Uint8', 1, function (init) {
  return function Uint8Array(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
});


/***/ }),

/***/ "./node_modules/core-js/modules/es6.typed.uint8-clamped-array.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_typed-array.js")('Uint8', 1, function (init) {
  return function Uint8ClampedArray(data, byteOffset, length) {
    return init(this, data, byteOffset, length);
  };
}, true);


/***/ }),

/***/ "./node_modules/core-js/modules/es6.weak-map.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var each = __webpack_require__("./node_modules/core-js/modules/_array-methods.js")(0);
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var meta = __webpack_require__("./node_modules/core-js/modules/_meta.js");
var assign = __webpack_require__("./node_modules/core-js/modules/_object-assign.js");
var weak = __webpack_require__("./node_modules/core-js/modules/_collection-weak.js");
var isObject = __webpack_require__("./node_modules/core-js/modules/_is-object.js");
var fails = __webpack_require__("./node_modules/core-js/modules/_fails.js");
var validate = __webpack_require__("./node_modules/core-js/modules/_validate-collection.js");
var WEAK_MAP = 'WeakMap';
var getWeak = meta.getWeak;
var isExtensible = Object.isExtensible;
var uncaughtFrozenStore = weak.ufstore;
var tmp = {};
var InternalMap;

var wrapper = function (get) {
  return function WeakMap() {
    return get(this, arguments.length > 0 ? arguments[0] : undefined);
  };
};

var methods = {
  // 23.3.3.3 WeakMap.prototype.get(key)
  get: function get(key) {
    if (isObject(key)) {
      var data = getWeak(key);
      if (data === true) return uncaughtFrozenStore(validate(this, WEAK_MAP)).get(key);
      return data ? data[this._i] : undefined;
    }
  },
  // 23.3.3.5 WeakMap.prototype.set(key, value)
  set: function set(key, value) {
    return weak.def(validate(this, WEAK_MAP), key, value);
  }
};

// 23.3 WeakMap Objects
var $WeakMap = module.exports = __webpack_require__("./node_modules/core-js/modules/_collection.js")(WEAK_MAP, wrapper, methods, weak, true, true);

// IE11 WeakMap frozen keys fix
if (fails(function () { return new $WeakMap().set((Object.freeze || Object)(tmp), 7).get(tmp) != 7; })) {
  InternalMap = weak.getConstructor(wrapper, WEAK_MAP);
  assign(InternalMap.prototype, methods);
  meta.NEED = true;
  each(['delete', 'has', 'get', 'set'], function (key) {
    var proto = $WeakMap.prototype;
    var method = proto[key];
    redefine(proto, key, function (a, b) {
      // store frozen objects on internal weakmap shim
      if (isObject(a) && !isExtensible(a)) {
        if (!this._f) this._f = new InternalMap();
        var result = this._f[key](a, b);
        return key == 'set' ? this : result;
      // store all the rest on native weakmap
      } return method.call(this, a, b);
    });
  });
}


/***/ }),

/***/ "./node_modules/core-js/modules/es6.weak-set.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var weak = __webpack_require__("./node_modules/core-js/modules/_collection-weak.js");
var validate = __webpack_require__("./node_modules/core-js/modules/_validate-collection.js");
var WEAK_SET = 'WeakSet';

// 23.4 WeakSet Objects
__webpack_require__("./node_modules/core-js/modules/_collection.js")(WEAK_SET, function (get) {
  return function WeakSet() { return get(this, arguments.length > 0 ? arguments[0] : undefined); };
}, {
  // 23.4.3.1 WeakSet.prototype.add(value)
  add: function add(value) {
    return weak.def(validate(this, WEAK_SET), value, true);
  }
}, weak, false, true);


/***/ }),

/***/ "./node_modules/core-js/modules/es7.array.flat-map.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://tc39.github.io/proposal-flatMap/#sec-Array.prototype.flatMap
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var flattenIntoArray = __webpack_require__("./node_modules/core-js/modules/_flatten-into-array.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var arraySpeciesCreate = __webpack_require__("./node_modules/core-js/modules/_array-species-create.js");

$export($export.P, 'Array', {
  flatMap: function flatMap(callbackfn /* , thisArg */) {
    var O = toObject(this);
    var sourceLen, A;
    aFunction(callbackfn);
    sourceLen = toLength(O.length);
    A = arraySpeciesCreate(O, 0);
    flattenIntoArray(A, O, O, sourceLen, 0, 1, callbackfn, arguments[1]);
    return A;
  }
});

__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")('flatMap');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.array.flatten.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://tc39.github.io/proposal-flatMap/#sec-Array.prototype.flatten
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var flattenIntoArray = __webpack_require__("./node_modules/core-js/modules/_flatten-into-array.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var toInteger = __webpack_require__("./node_modules/core-js/modules/_to-integer.js");
var arraySpeciesCreate = __webpack_require__("./node_modules/core-js/modules/_array-species-create.js");

$export($export.P, 'Array', {
  flatten: function flatten(/* depthArg = 1 */) {
    var depthArg = arguments[0];
    var O = toObject(this);
    var sourceLen = toLength(O.length);
    var A = arraySpeciesCreate(O, 0);
    flattenIntoArray(A, O, O, sourceLen, 0, depthArg === undefined ? 1 : toInteger(depthArg));
    return A;
  }
});

__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")('flatten');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.array.includes.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/tc39/Array.prototype.includes
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $includes = __webpack_require__("./node_modules/core-js/modules/_array-includes.js")(true);

$export($export.P, 'Array', {
  includes: function includes(el /* , fromIndex = 0 */) {
    return $includes(this, el, arguments.length > 1 ? arguments[1] : undefined);
  }
});

__webpack_require__("./node_modules/core-js/modules/_add-to-unscopables.js")('includes');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.asap.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/rwaldron/tc39-notes/blob/master/es6/2014-09/sept-25.md#510-globalasap-for-enqueuing-a-microtask
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var microtask = __webpack_require__("./node_modules/core-js/modules/_microtask.js")();
var process = __webpack_require__("./node_modules/core-js/modules/_global.js").process;
var isNode = __webpack_require__("./node_modules/core-js/modules/_cof.js")(process) == 'process';

$export($export.G, {
  asap: function asap(fn) {
    var domain = isNode && process.domain;
    microtask(domain ? domain.bind(fn) : fn);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.error.is-error.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/ljharb/proposal-is-error
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var cof = __webpack_require__("./node_modules/core-js/modules/_cof.js");

$export($export.S, 'Error', {
  isError: function isError(it) {
    return cof(it) === 'Error';
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.global.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/tc39/proposal-global
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.G, { global: __webpack_require__("./node_modules/core-js/modules/_global.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.map.from.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-map.from
__webpack_require__("./node_modules/core-js/modules/_set-collection-from.js")('Map');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.map.of.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-map.of
__webpack_require__("./node_modules/core-js/modules/_set-collection-of.js")('Map');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.map.to-json.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/DavidBruant/Map-Set.prototype.toJSON
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.P + $export.R, 'Map', { toJSON: __webpack_require__("./node_modules/core-js/modules/_collection-to-json.js")('Map') });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.clamp.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  clamp: function clamp(x, lower, upper) {
    return Math.min(upper, Math.max(lower, x));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.deg-per-rad.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { DEG_PER_RAD: Math.PI / 180 });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.degrees.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var RAD_PER_DEG = 180 / Math.PI;

$export($export.S, 'Math', {
  degrees: function degrees(radians) {
    return radians * RAD_PER_DEG;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.fscale.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var scale = __webpack_require__("./node_modules/core-js/modules/_math-scale.js");
var fround = __webpack_require__("./node_modules/core-js/modules/_math-fround.js");

$export($export.S, 'Math', {
  fscale: function fscale(x, inLow, inHigh, outLow, outHigh) {
    return fround(scale(x, inLow, inHigh, outLow, outHigh));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.iaddh.js":
/***/ (function(module, exports, __webpack_require__) {

// https://gist.github.com/BrendanEich/4294d5c212a6d2254703
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  iaddh: function iaddh(x0, x1, y0, y1) {
    var $x0 = x0 >>> 0;
    var $x1 = x1 >>> 0;
    var $y0 = y0 >>> 0;
    return $x1 + (y1 >>> 0) + (($x0 & $y0 | ($x0 | $y0) & ~($x0 + $y0 >>> 0)) >>> 31) | 0;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.imulh.js":
/***/ (function(module, exports, __webpack_require__) {

// https://gist.github.com/BrendanEich/4294d5c212a6d2254703
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  imulh: function imulh(u, v) {
    var UINT16 = 0xffff;
    var $u = +u;
    var $v = +v;
    var u0 = $u & UINT16;
    var v0 = $v & UINT16;
    var u1 = $u >> 16;
    var v1 = $v >> 16;
    var t = (u1 * v0 >>> 0) + (u0 * v0 >>> 16);
    return u1 * v1 + (t >> 16) + ((u0 * v1 >>> 0) + (t & UINT16) >> 16);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.isubh.js":
/***/ (function(module, exports, __webpack_require__) {

// https://gist.github.com/BrendanEich/4294d5c212a6d2254703
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  isubh: function isubh(x0, x1, y0, y1) {
    var $x0 = x0 >>> 0;
    var $x1 = x1 >>> 0;
    var $y0 = y0 >>> 0;
    return $x1 - (y1 >>> 0) - ((~$x0 & $y0 | ~($x0 ^ $y0) & $x0 - $y0 >>> 0) >>> 31) | 0;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.rad-per-deg.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { RAD_PER_DEG: 180 / Math.PI });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.radians.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var DEG_PER_RAD = Math.PI / 180;

$export($export.S, 'Math', {
  radians: function radians(degrees) {
    return degrees * DEG_PER_RAD;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.scale.js":
/***/ (function(module, exports, __webpack_require__) {

// https://rwaldron.github.io/proposal-math-extensions/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { scale: __webpack_require__("./node_modules/core-js/modules/_math-scale.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.signbit.js":
/***/ (function(module, exports, __webpack_require__) {

// http://jfbastien.github.io/papers/Math.signbit.html
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', { signbit: function signbit(x) {
  // eslint-disable-next-line no-self-compare
  return (x = +x) != x ? x : x == 0 ? 1 / x == Infinity : x > 0;
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.math.umulh.js":
/***/ (function(module, exports, __webpack_require__) {

// https://gist.github.com/BrendanEich/4294d5c212a6d2254703
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'Math', {
  umulh: function umulh(u, v) {
    var UINT16 = 0xffff;
    var $u = +u;
    var $v = +v;
    var u0 = $u & UINT16;
    var v0 = $v & UINT16;
    var u1 = $u >>> 16;
    var v1 = $v >>> 16;
    var t = (u1 * v0 >>> 0) + (u0 * v0 >>> 16);
    return u1 * v1 + (t >>> 16) + ((u0 * v1 >>> 0) + (t & UINT16) >>> 16);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.define-getter.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var $defineProperty = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");

// B.2.2.2 Object.prototype.__defineGetter__(P, getter)
__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && $export($export.P + __webpack_require__("./node_modules/core-js/modules/_object-forced-pam.js"), 'Object', {
  __defineGetter__: function __defineGetter__(P, getter) {
    $defineProperty.f(toObject(this), P, { get: aFunction(getter), enumerable: true, configurable: true });
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.define-setter.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var $defineProperty = __webpack_require__("./node_modules/core-js/modules/_object-dp.js");

// B.2.2.3 Object.prototype.__defineSetter__(P, setter)
__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && $export($export.P + __webpack_require__("./node_modules/core-js/modules/_object-forced-pam.js"), 'Object', {
  __defineSetter__: function __defineSetter__(P, setter) {
    $defineProperty.f(toObject(this), P, { set: aFunction(setter), enumerable: true, configurable: true });
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.entries.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/tc39/proposal-object-values-entries
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $entries = __webpack_require__("./node_modules/core-js/modules/_object-to-array.js")(true);

$export($export.S, 'Object', {
  entries: function entries(it) {
    return $entries(it);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.get-own-property-descriptors.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/tc39/proposal-object-getownpropertydescriptors
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var ownKeys = __webpack_require__("./node_modules/core-js/modules/_own-keys.js");
var toIObject = __webpack_require__("./node_modules/core-js/modules/_to-iobject.js");
var gOPD = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js");
var createProperty = __webpack_require__("./node_modules/core-js/modules/_create-property.js");

$export($export.S, 'Object', {
  getOwnPropertyDescriptors: function getOwnPropertyDescriptors(object) {
    var O = toIObject(object);
    var getDesc = gOPD.f;
    var keys = ownKeys(O);
    var result = {};
    var i = 0;
    var key, desc;
    while (keys.length > i) {
      desc = getDesc(O, key = keys[i++]);
      if (desc !== undefined) createProperty(result, key, desc);
    }
    return result;
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.lookup-getter.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var getOwnPropertyDescriptor = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js").f;

// B.2.2.4 Object.prototype.__lookupGetter__(P)
__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && $export($export.P + __webpack_require__("./node_modules/core-js/modules/_object-forced-pam.js"), 'Object', {
  __lookupGetter__: function __lookupGetter__(P) {
    var O = toObject(this);
    var K = toPrimitive(P, true);
    var D;
    do {
      if (D = getOwnPropertyDescriptor(O, K)) return D.get;
    } while (O = getPrototypeOf(O));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.lookup-setter.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var toObject = __webpack_require__("./node_modules/core-js/modules/_to-object.js");
var toPrimitive = __webpack_require__("./node_modules/core-js/modules/_to-primitive.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var getOwnPropertyDescriptor = __webpack_require__("./node_modules/core-js/modules/_object-gopd.js").f;

// B.2.2.5 Object.prototype.__lookupSetter__(P)
__webpack_require__("./node_modules/core-js/modules/_descriptors.js") && $export($export.P + __webpack_require__("./node_modules/core-js/modules/_object-forced-pam.js"), 'Object', {
  __lookupSetter__: function __lookupSetter__(P) {
    var O = toObject(this);
    var K = toPrimitive(P, true);
    var D;
    do {
      if (D = getOwnPropertyDescriptor(O, K)) return D.set;
    } while (O = getPrototypeOf(O));
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.object.values.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/tc39/proposal-object-values-entries
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $values = __webpack_require__("./node_modules/core-js/modules/_object-to-array.js")(false);

$export($export.S, 'Object', {
  values: function values(it) {
    return $values(it);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.observable.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/zenparsing/es-observable
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var core = __webpack_require__("./node_modules/core-js/modules/_core.js");
var microtask = __webpack_require__("./node_modules/core-js/modules/_microtask.js")();
var OBSERVABLE = __webpack_require__("./node_modules/core-js/modules/_wks.js")('observable');
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var anInstance = __webpack_require__("./node_modules/core-js/modules/_an-instance.js");
var redefineAll = __webpack_require__("./node_modules/core-js/modules/_redefine-all.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var forOf = __webpack_require__("./node_modules/core-js/modules/_for-of.js");
var RETURN = forOf.RETURN;

var getMethod = function (fn) {
  return fn == null ? undefined : aFunction(fn);
};

var cleanupSubscription = function (subscription) {
  var cleanup = subscription._c;
  if (cleanup) {
    subscription._c = undefined;
    cleanup();
  }
};

var subscriptionClosed = function (subscription) {
  return subscription._o === undefined;
};

var closeSubscription = function (subscription) {
  if (!subscriptionClosed(subscription)) {
    subscription._o = undefined;
    cleanupSubscription(subscription);
  }
};

var Subscription = function (observer, subscriber) {
  anObject(observer);
  this._c = undefined;
  this._o = observer;
  observer = new SubscriptionObserver(this);
  try {
    var cleanup = subscriber(observer);
    var subscription = cleanup;
    if (cleanup != null) {
      if (typeof cleanup.unsubscribe === 'function') cleanup = function () { subscription.unsubscribe(); };
      else aFunction(cleanup);
      this._c = cleanup;
    }
  } catch (e) {
    observer.error(e);
    return;
  } if (subscriptionClosed(this)) cleanupSubscription(this);
};

Subscription.prototype = redefineAll({}, {
  unsubscribe: function unsubscribe() { closeSubscription(this); }
});

var SubscriptionObserver = function (subscription) {
  this._s = subscription;
};

SubscriptionObserver.prototype = redefineAll({}, {
  next: function next(value) {
    var subscription = this._s;
    if (!subscriptionClosed(subscription)) {
      var observer = subscription._o;
      try {
        var m = getMethod(observer.next);
        if (m) return m.call(observer, value);
      } catch (e) {
        try {
          closeSubscription(subscription);
        } finally {
          throw e;
        }
      }
    }
  },
  error: function error(value) {
    var subscription = this._s;
    if (subscriptionClosed(subscription)) throw value;
    var observer = subscription._o;
    subscription._o = undefined;
    try {
      var m = getMethod(observer.error);
      if (!m) throw value;
      value = m.call(observer, value);
    } catch (e) {
      try {
        cleanupSubscription(subscription);
      } finally {
        throw e;
      }
    } cleanupSubscription(subscription);
    return value;
  },
  complete: function complete(value) {
    var subscription = this._s;
    if (!subscriptionClosed(subscription)) {
      var observer = subscription._o;
      subscription._o = undefined;
      try {
        var m = getMethod(observer.complete);
        value = m ? m.call(observer, value) : undefined;
      } catch (e) {
        try {
          cleanupSubscription(subscription);
        } finally {
          throw e;
        }
      } cleanupSubscription(subscription);
      return value;
    }
  }
});

var $Observable = function Observable(subscriber) {
  anInstance(this, $Observable, 'Observable', '_f')._f = aFunction(subscriber);
};

redefineAll($Observable.prototype, {
  subscribe: function subscribe(observer) {
    return new Subscription(observer, this._f);
  },
  forEach: function forEach(fn) {
    var that = this;
    return new (core.Promise || global.Promise)(function (resolve, reject) {
      aFunction(fn);
      var subscription = that.subscribe({
        next: function (value) {
          try {
            return fn(value);
          } catch (e) {
            reject(e);
            subscription.unsubscribe();
          }
        },
        error: reject,
        complete: resolve
      });
    });
  }
});

redefineAll($Observable, {
  from: function from(x) {
    var C = typeof this === 'function' ? this : $Observable;
    var method = getMethod(anObject(x)[OBSERVABLE]);
    if (method) {
      var observable = anObject(method.call(x));
      return observable.constructor === C ? observable : new C(function (observer) {
        return observable.subscribe(observer);
      });
    }
    return new C(function (observer) {
      var done = false;
      microtask(function () {
        if (!done) {
          try {
            if (forOf(x, false, function (it) {
              observer.next(it);
              if (done) return RETURN;
            }) === RETURN) return;
          } catch (e) {
            if (done) throw e;
            observer.error(e);
            return;
          } observer.complete();
        }
      });
      return function () { done = true; };
    });
  },
  of: function of() {
    for (var i = 0, l = arguments.length, items = new Array(l); i < l;) items[i] = arguments[i++];
    return new (typeof this === 'function' ? this : $Observable)(function (observer) {
      var done = false;
      microtask(function () {
        if (!done) {
          for (var j = 0; j < items.length; ++j) {
            observer.next(items[j]);
            if (done) return;
          } observer.complete();
        }
      });
      return function () { done = true; };
    });
  }
});

hide($Observable.prototype, OBSERVABLE, function () { return this; });

$export($export.G, { Observable: $Observable });

__webpack_require__("./node_modules/core-js/modules/_set-species.js")('Observable');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.promise.finally.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
// https://github.com/tc39/proposal-promise-finally

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var core = __webpack_require__("./node_modules/core-js/modules/_core.js");
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var speciesConstructor = __webpack_require__("./node_modules/core-js/modules/_species-constructor.js");
var promiseResolve = __webpack_require__("./node_modules/core-js/modules/_promise-resolve.js");

$export($export.P + $export.R, 'Promise', { 'finally': function (onFinally) {
  var C = speciesConstructor(this, core.Promise || global.Promise);
  var isFunction = typeof onFinally == 'function';
  return this.then(
    isFunction ? function (x) {
      return promiseResolve(C, onFinally()).then(function () { return x; });
    } : onFinally,
    isFunction ? function (e) {
      return promiseResolve(C, onFinally()).then(function () { throw e; });
    } : onFinally
  );
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.promise.try.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/tc39/proposal-promise-try
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var newPromiseCapability = __webpack_require__("./node_modules/core-js/modules/_new-promise-capability.js");
var perform = __webpack_require__("./node_modules/core-js/modules/_perform.js");

$export($export.S, 'Promise', { 'try': function (callbackfn) {
  var promiseCapability = newPromiseCapability.f(this);
  var result = perform(callbackfn);
  (result.e ? promiseCapability.reject : promiseCapability.resolve)(result.v);
  return promiseCapability.promise;
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.define-metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var toMetaKey = metadata.key;
var ordinaryDefineOwnMetadata = metadata.set;

metadata.exp({ defineMetadata: function defineMetadata(metadataKey, metadataValue, target, targetKey) {
  ordinaryDefineOwnMetadata(metadataKey, metadataValue, anObject(target), toMetaKey(targetKey));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.delete-metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var toMetaKey = metadata.key;
var getOrCreateMetadataMap = metadata.map;
var store = metadata.store;

metadata.exp({ deleteMetadata: function deleteMetadata(metadataKey, target /* , targetKey */) {
  var targetKey = arguments.length < 3 ? undefined : toMetaKey(arguments[2]);
  var metadataMap = getOrCreateMetadataMap(anObject(target), targetKey, false);
  if (metadataMap === undefined || !metadataMap['delete'](metadataKey)) return false;
  if (metadataMap.size) return true;
  var targetMetadata = store.get(target);
  targetMetadata['delete'](targetKey);
  return !!targetMetadata.size || store['delete'](target);
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.get-metadata-keys.js":
/***/ (function(module, exports, __webpack_require__) {

var Set = __webpack_require__("./node_modules/core-js/modules/es6.set.js");
var from = __webpack_require__("./node_modules/core-js/modules/_array-from-iterable.js");
var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var ordinaryOwnMetadataKeys = metadata.keys;
var toMetaKey = metadata.key;

var ordinaryMetadataKeys = function (O, P) {
  var oKeys = ordinaryOwnMetadataKeys(O, P);
  var parent = getPrototypeOf(O);
  if (parent === null) return oKeys;
  var pKeys = ordinaryMetadataKeys(parent, P);
  return pKeys.length ? oKeys.length ? from(new Set(oKeys.concat(pKeys))) : pKeys : oKeys;
};

metadata.exp({ getMetadataKeys: function getMetadataKeys(target /* , targetKey */) {
  return ordinaryMetadataKeys(anObject(target), arguments.length < 2 ? undefined : toMetaKey(arguments[1]));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.get-metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var ordinaryHasOwnMetadata = metadata.has;
var ordinaryGetOwnMetadata = metadata.get;
var toMetaKey = metadata.key;

var ordinaryGetMetadata = function (MetadataKey, O, P) {
  var hasOwn = ordinaryHasOwnMetadata(MetadataKey, O, P);
  if (hasOwn) return ordinaryGetOwnMetadata(MetadataKey, O, P);
  var parent = getPrototypeOf(O);
  return parent !== null ? ordinaryGetMetadata(MetadataKey, parent, P) : undefined;
};

metadata.exp({ getMetadata: function getMetadata(metadataKey, target /* , targetKey */) {
  return ordinaryGetMetadata(metadataKey, anObject(target), arguments.length < 3 ? undefined : toMetaKey(arguments[2]));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.get-own-metadata-keys.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var ordinaryOwnMetadataKeys = metadata.keys;
var toMetaKey = metadata.key;

metadata.exp({ getOwnMetadataKeys: function getOwnMetadataKeys(target /* , targetKey */) {
  return ordinaryOwnMetadataKeys(anObject(target), arguments.length < 2 ? undefined : toMetaKey(arguments[1]));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.get-own-metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var ordinaryGetOwnMetadata = metadata.get;
var toMetaKey = metadata.key;

metadata.exp({ getOwnMetadata: function getOwnMetadata(metadataKey, target /* , targetKey */) {
  return ordinaryGetOwnMetadata(metadataKey, anObject(target)
    , arguments.length < 3 ? undefined : toMetaKey(arguments[2]));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.has-metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var getPrototypeOf = __webpack_require__("./node_modules/core-js/modules/_object-gpo.js");
var ordinaryHasOwnMetadata = metadata.has;
var toMetaKey = metadata.key;

var ordinaryHasMetadata = function (MetadataKey, O, P) {
  var hasOwn = ordinaryHasOwnMetadata(MetadataKey, O, P);
  if (hasOwn) return true;
  var parent = getPrototypeOf(O);
  return parent !== null ? ordinaryHasMetadata(MetadataKey, parent, P) : false;
};

metadata.exp({ hasMetadata: function hasMetadata(metadataKey, target /* , targetKey */) {
  return ordinaryHasMetadata(metadataKey, anObject(target), arguments.length < 3 ? undefined : toMetaKey(arguments[2]));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.has-own-metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var ordinaryHasOwnMetadata = metadata.has;
var toMetaKey = metadata.key;

metadata.exp({ hasOwnMetadata: function hasOwnMetadata(metadataKey, target /* , targetKey */) {
  return ordinaryHasOwnMetadata(metadataKey, anObject(target)
    , arguments.length < 3 ? undefined : toMetaKey(arguments[2]));
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.reflect.metadata.js":
/***/ (function(module, exports, __webpack_require__) {

var $metadata = __webpack_require__("./node_modules/core-js/modules/_metadata.js");
var anObject = __webpack_require__("./node_modules/core-js/modules/_an-object.js");
var aFunction = __webpack_require__("./node_modules/core-js/modules/_a-function.js");
var toMetaKey = $metadata.key;
var ordinaryDefineOwnMetadata = $metadata.set;

$metadata.exp({ metadata: function metadata(metadataKey, metadataValue) {
  return function decorator(target, targetKey) {
    ordinaryDefineOwnMetadata(
      metadataKey, metadataValue,
      (targetKey !== undefined ? anObject : aFunction)(target),
      toMetaKey(targetKey)
    );
  };
} });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.set.from.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-set.from
__webpack_require__("./node_modules/core-js/modules/_set-collection-from.js")('Set');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.set.of.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-set.of
__webpack_require__("./node_modules/core-js/modules/_set-collection-of.js")('Set');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.set.to-json.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/DavidBruant/Map-Set.prototype.toJSON
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.P + $export.R, 'Set', { toJSON: __webpack_require__("./node_modules/core-js/modules/_collection-to-json.js")('Set') });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.string.at.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/mathiasbynens/String.prototype.at
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $at = __webpack_require__("./node_modules/core-js/modules/_string-at.js")(true);

$export($export.P, 'String', {
  at: function at(pos) {
    return $at(this, pos);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.string.match-all.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://tc39.github.io/String.prototype.matchAll/
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var defined = __webpack_require__("./node_modules/core-js/modules/_defined.js");
var toLength = __webpack_require__("./node_modules/core-js/modules/_to-length.js");
var isRegExp = __webpack_require__("./node_modules/core-js/modules/_is-regexp.js");
var getFlags = __webpack_require__("./node_modules/core-js/modules/_flags.js");
var RegExpProto = RegExp.prototype;

var $RegExpStringIterator = function (regexp, string) {
  this._r = regexp;
  this._s = string;
};

__webpack_require__("./node_modules/core-js/modules/_iter-create.js")($RegExpStringIterator, 'RegExp String', function next() {
  var match = this._r.exec(this._s);
  return { value: match, done: match === null };
});

$export($export.P, 'String', {
  matchAll: function matchAll(regexp) {
    defined(this);
    if (!isRegExp(regexp)) throw TypeError(regexp + ' is not a regexp!');
    var S = String(this);
    var flags = 'flags' in RegExpProto ? String(regexp.flags) : getFlags.call(regexp);
    var rx = new RegExp(regexp.source, ~flags.indexOf('g') ? flags : 'g' + flags);
    rx.lastIndex = toLength(regexp.lastIndex);
    return new $RegExpStringIterator(rx, S);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.string.pad-end.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/tc39/proposal-string-pad-start-end
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $pad = __webpack_require__("./node_modules/core-js/modules/_string-pad.js");
var userAgent = __webpack_require__("./node_modules/core-js/modules/_user-agent.js");

// https://github.com/zloirock/core-js/issues/280
$export($export.P + $export.F * /Version\/10\.\d+(\.\d+)? Safari\//.test(userAgent), 'String', {
  padEnd: function padEnd(maxLength /* , fillString = ' ' */) {
    return $pad(this, maxLength, arguments.length > 1 ? arguments[1] : undefined, false);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.string.pad-start.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/tc39/proposal-string-pad-start-end
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $pad = __webpack_require__("./node_modules/core-js/modules/_string-pad.js");
var userAgent = __webpack_require__("./node_modules/core-js/modules/_user-agent.js");

// https://github.com/zloirock/core-js/issues/280
$export($export.P + $export.F * /Version\/10\.\d+(\.\d+)? Safari\//.test(userAgent), 'String', {
  padStart: function padStart(maxLength /* , fillString = ' ' */) {
    return $pad(this, maxLength, arguments.length > 1 ? arguments[1] : undefined, true);
  }
});


/***/ }),

/***/ "./node_modules/core-js/modules/es7.string.trim-left.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/sebmarkbage/ecmascript-string-left-right-trim
__webpack_require__("./node_modules/core-js/modules/_string-trim.js")('trimLeft', function ($trim) {
  return function trimLeft() {
    return $trim(this, 1);
  };
}, 'trimStart');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.string.trim-right.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";

// https://github.com/sebmarkbage/ecmascript-string-left-right-trim
__webpack_require__("./node_modules/core-js/modules/_string-trim.js")('trimRight', function ($trim) {
  return function trimRight() {
    return $trim(this, 2);
  };
}, 'trimEnd');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.symbol.async-iterator.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_wks-define.js")('asyncIterator');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.symbol.observable.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/_wks-define.js")('observable');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.system.global.js":
/***/ (function(module, exports, __webpack_require__) {

// https://github.com/tc39/proposal-global
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");

$export($export.S, 'System', { global: __webpack_require__("./node_modules/core-js/modules/_global.js") });


/***/ }),

/***/ "./node_modules/core-js/modules/es7.weak-map.from.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-weakmap.from
__webpack_require__("./node_modules/core-js/modules/_set-collection-from.js")('WeakMap');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.weak-map.of.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-weakmap.of
__webpack_require__("./node_modules/core-js/modules/_set-collection-of.js")('WeakMap');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.weak-set.from.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-weakset.from
__webpack_require__("./node_modules/core-js/modules/_set-collection-from.js")('WeakSet');


/***/ }),

/***/ "./node_modules/core-js/modules/es7.weak-set.of.js":
/***/ (function(module, exports, __webpack_require__) {

// https://tc39.github.io/proposal-setmap-offrom/#sec-weakset.of
__webpack_require__("./node_modules/core-js/modules/_set-collection-of.js")('WeakSet');


/***/ }),

/***/ "./node_modules/core-js/modules/web.dom.iterable.js":
/***/ (function(module, exports, __webpack_require__) {

var $iterators = __webpack_require__("./node_modules/core-js/modules/es6.array.iterator.js");
var getKeys = __webpack_require__("./node_modules/core-js/modules/_object-keys.js");
var redefine = __webpack_require__("./node_modules/core-js/modules/_redefine.js");
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var hide = __webpack_require__("./node_modules/core-js/modules/_hide.js");
var Iterators = __webpack_require__("./node_modules/core-js/modules/_iterators.js");
var wks = __webpack_require__("./node_modules/core-js/modules/_wks.js");
var ITERATOR = wks('iterator');
var TO_STRING_TAG = wks('toStringTag');
var ArrayValues = Iterators.Array;

var DOMIterables = {
  CSSRuleList: true, // TODO: Not spec compliant, should be false.
  CSSStyleDeclaration: false,
  CSSValueList: false,
  ClientRectList: false,
  DOMRectList: false,
  DOMStringList: false,
  DOMTokenList: true,
  DataTransferItemList: false,
  FileList: false,
  HTMLAllCollection: false,
  HTMLCollection: false,
  HTMLFormElement: false,
  HTMLSelectElement: false,
  MediaList: true, // TODO: Not spec compliant, should be false.
  MimeTypeArray: false,
  NamedNodeMap: false,
  NodeList: true,
  PaintRequestList: false,
  Plugin: false,
  PluginArray: false,
  SVGLengthList: false,
  SVGNumberList: false,
  SVGPathSegList: false,
  SVGPointList: false,
  SVGStringList: false,
  SVGTransformList: false,
  SourceBufferList: false,
  StyleSheetList: true, // TODO: Not spec compliant, should be false.
  TextTrackCueList: false,
  TextTrackList: false,
  TouchList: false
};

for (var collections = getKeys(DOMIterables), i = 0; i < collections.length; i++) {
  var NAME = collections[i];
  var explicit = DOMIterables[NAME];
  var Collection = global[NAME];
  var proto = Collection && Collection.prototype;
  var key;
  if (proto) {
    if (!proto[ITERATOR]) hide(proto, ITERATOR, ArrayValues);
    if (!proto[TO_STRING_TAG]) hide(proto, TO_STRING_TAG, NAME);
    Iterators[NAME] = ArrayValues;
    if (explicit) for (key in $iterators) if (!proto[key]) redefine(proto, key, $iterators[key], true);
  }
}


/***/ }),

/***/ "./node_modules/core-js/modules/web.immediate.js":
/***/ (function(module, exports, __webpack_require__) {

var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var $task = __webpack_require__("./node_modules/core-js/modules/_task.js");
$export($export.G + $export.B, {
  setImmediate: $task.set,
  clearImmediate: $task.clear
});


/***/ }),

/***/ "./node_modules/core-js/modules/web.timers.js":
/***/ (function(module, exports, __webpack_require__) {

// ie9- setTimeout & setInterval additional parameters fix
var global = __webpack_require__("./node_modules/core-js/modules/_global.js");
var $export = __webpack_require__("./node_modules/core-js/modules/_export.js");
var userAgent = __webpack_require__("./node_modules/core-js/modules/_user-agent.js");
var slice = [].slice;
var MSIE = /MSIE .\./.test(userAgent); // <- dirty ie9- check
var wrap = function (set) {
  return function (fn, time /* , ...args */) {
    var boundArgs = arguments.length > 2;
    var args = boundArgs ? slice.call(arguments, 2) : false;
    return set(boundArgs ? function () {
      // eslint-disable-next-line no-new-func
      (typeof fn == 'function' ? fn : Function(fn)).apply(this, args);
    } : fn, time);
  };
};
$export($export.G + $export.B + $export.F * MSIE, {
  setTimeout: wrap(global.setTimeout),
  setInterval: wrap(global.setInterval)
});


/***/ }),

/***/ "./node_modules/core-js/shim.js":
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__("./node_modules/core-js/modules/es6.symbol.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.create.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.define-property.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.define-properties.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.get-own-property-descriptor.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.get-prototype-of.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.keys.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.get-own-property-names.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.freeze.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.seal.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.prevent-extensions.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.is-frozen.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.is-sealed.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.is-extensible.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.assign.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.is.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.set-prototype-of.js");
__webpack_require__("./node_modules/core-js/modules/es6.object.to-string.js");
__webpack_require__("./node_modules/core-js/modules/es6.function.bind.js");
__webpack_require__("./node_modules/core-js/modules/es6.function.name.js");
__webpack_require__("./node_modules/core-js/modules/es6.function.has-instance.js");
__webpack_require__("./node_modules/core-js/modules/es6.parse-int.js");
__webpack_require__("./node_modules/core-js/modules/es6.parse-float.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.constructor.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.to-fixed.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.to-precision.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.epsilon.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.is-finite.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.is-integer.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.is-nan.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.is-safe-integer.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.max-safe-integer.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.min-safe-integer.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.parse-float.js");
__webpack_require__("./node_modules/core-js/modules/es6.number.parse-int.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.acosh.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.asinh.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.atanh.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.cbrt.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.clz32.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.cosh.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.expm1.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.fround.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.hypot.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.imul.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.log10.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.log1p.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.log2.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.sign.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.sinh.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.tanh.js");
__webpack_require__("./node_modules/core-js/modules/es6.math.trunc.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.from-code-point.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.raw.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.trim.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.iterator.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.code-point-at.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.ends-with.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.includes.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.repeat.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.starts-with.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.anchor.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.big.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.blink.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.bold.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.fixed.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.fontcolor.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.fontsize.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.italics.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.link.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.small.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.strike.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.sub.js");
__webpack_require__("./node_modules/core-js/modules/es6.string.sup.js");
__webpack_require__("./node_modules/core-js/modules/es6.date.now.js");
__webpack_require__("./node_modules/core-js/modules/es6.date.to-json.js");
__webpack_require__("./node_modules/core-js/modules/es6.date.to-iso-string.js");
__webpack_require__("./node_modules/core-js/modules/es6.date.to-string.js");
__webpack_require__("./node_modules/core-js/modules/es6.date.to-primitive.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.is-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.from.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.of.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.join.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.slice.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.sort.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.for-each.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.map.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.filter.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.some.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.every.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.reduce.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.reduce-right.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.index-of.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.last-index-of.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.copy-within.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.fill.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.find.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.find-index.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.species.js");
__webpack_require__("./node_modules/core-js/modules/es6.array.iterator.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.constructor.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.to-string.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.flags.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.match.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.replace.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.search.js");
__webpack_require__("./node_modules/core-js/modules/es6.regexp.split.js");
__webpack_require__("./node_modules/core-js/modules/es6.promise.js");
__webpack_require__("./node_modules/core-js/modules/es6.map.js");
__webpack_require__("./node_modules/core-js/modules/es6.set.js");
__webpack_require__("./node_modules/core-js/modules/es6.weak-map.js");
__webpack_require__("./node_modules/core-js/modules/es6.weak-set.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.array-buffer.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.data-view.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.int8-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.uint8-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.uint8-clamped-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.int16-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.uint16-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.int32-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.uint32-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.float32-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.typed.float64-array.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.apply.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.construct.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.define-property.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.delete-property.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.enumerate.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.get.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.get-own-property-descriptor.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.get-prototype-of.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.has.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.is-extensible.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.own-keys.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.prevent-extensions.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.set.js");
__webpack_require__("./node_modules/core-js/modules/es6.reflect.set-prototype-of.js");
__webpack_require__("./node_modules/core-js/modules/es7.array.includes.js");
__webpack_require__("./node_modules/core-js/modules/es7.array.flat-map.js");
__webpack_require__("./node_modules/core-js/modules/es7.array.flatten.js");
__webpack_require__("./node_modules/core-js/modules/es7.string.at.js");
__webpack_require__("./node_modules/core-js/modules/es7.string.pad-start.js");
__webpack_require__("./node_modules/core-js/modules/es7.string.pad-end.js");
__webpack_require__("./node_modules/core-js/modules/es7.string.trim-left.js");
__webpack_require__("./node_modules/core-js/modules/es7.string.trim-right.js");
__webpack_require__("./node_modules/core-js/modules/es7.string.match-all.js");
__webpack_require__("./node_modules/core-js/modules/es7.symbol.async-iterator.js");
__webpack_require__("./node_modules/core-js/modules/es7.symbol.observable.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.get-own-property-descriptors.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.values.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.entries.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.define-getter.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.define-setter.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.lookup-getter.js");
__webpack_require__("./node_modules/core-js/modules/es7.object.lookup-setter.js");
__webpack_require__("./node_modules/core-js/modules/es7.map.to-json.js");
__webpack_require__("./node_modules/core-js/modules/es7.set.to-json.js");
__webpack_require__("./node_modules/core-js/modules/es7.map.of.js");
__webpack_require__("./node_modules/core-js/modules/es7.set.of.js");
__webpack_require__("./node_modules/core-js/modules/es7.weak-map.of.js");
__webpack_require__("./node_modules/core-js/modules/es7.weak-set.of.js");
__webpack_require__("./node_modules/core-js/modules/es7.map.from.js");
__webpack_require__("./node_modules/core-js/modules/es7.set.from.js");
__webpack_require__("./node_modules/core-js/modules/es7.weak-map.from.js");
__webpack_require__("./node_modules/core-js/modules/es7.weak-set.from.js");
__webpack_require__("./node_modules/core-js/modules/es7.global.js");
__webpack_require__("./node_modules/core-js/modules/es7.system.global.js");
__webpack_require__("./node_modules/core-js/modules/es7.error.is-error.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.clamp.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.deg-per-rad.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.degrees.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.fscale.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.iaddh.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.isubh.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.imulh.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.rad-per-deg.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.radians.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.scale.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.umulh.js");
__webpack_require__("./node_modules/core-js/modules/es7.math.signbit.js");
__webpack_require__("./node_modules/core-js/modules/es7.promise.finally.js");
__webpack_require__("./node_modules/core-js/modules/es7.promise.try.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.define-metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.delete-metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.get-metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.get-metadata-keys.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.get-own-metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.get-own-metadata-keys.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.has-metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.has-own-metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.reflect.metadata.js");
__webpack_require__("./node_modules/core-js/modules/es7.asap.js");
__webpack_require__("./node_modules/core-js/modules/es7.observable.js");
__webpack_require__("./node_modules/core-js/modules/web.timers.js");
__webpack_require__("./node_modules/core-js/modules/web.immediate.js");
__webpack_require__("./node_modules/core-js/modules/web.dom.iterable.js");
module.exports = __webpack_require__("./node_modules/core-js/modules/_core.js");


/***/ }),

/***/ "./node_modules/edx-ui-toolkit/src/js/utils/html-utils.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * Useful functions for dealing with HTML.
 *
 * In particular, these functions default to being safe against
 * Cross Site Scripting (XSS) attacks. You can read more about
 * the best practices for handling proper escaping in the Open edX
 * platform with
 * [Preventing Cross Site Scripting Vulnerabilities][1].
 * [1]: http://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/safe_templates.html
 *
 * @module HtmlUtils
 */
(function(define) {
    'use strict';
    !(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(1), __webpack_require__(0), __webpack_require__("./node_modules/edx-ui-toolkit/src/js/utils/string-utils.js")], __WEBPACK_AMD_DEFINE_RESULT__ = function(_, $, StringUtils) {
        var HtmlUtils, ensureHtml, interpolateHtml, joinHtml, HTML, template, setHtml, append, prepend;

        /**
         * Creates an HTML snippet.
         *
         * The intention of an HTML snippet is to communicate that the string
         * it represents contains HTML that has been safely escaped as necessary.
         * As an example, this allows `HtmlUtils.interpolate` to understand that
         * it does not need to further escape this HTML.
         *
         * @param {string} htmlString The string of HTML.
         */
        function HtmlSnippet(htmlString) {
            this.text = htmlString;
        }
        HtmlSnippet.prototype.valueOf = function() {
            return this.text;
        };
        HtmlSnippet.prototype.toString = function() {
            return this.text;
        };

        /**
         * Helper function to create an HTML snippet from a string.
         *
         * The intention of an HTML snippet is to communicate that the string
         * it represents contains HTML that has been safely escaped as necessary.
         *
         * @param {string} htmlString The string of HTML.
         * @returns {HtmlSnippet} An HTML snippet that can be safely rendered.
         */
        HTML = function(htmlString) {
            return new HtmlSnippet(htmlString);
        };

        /**
         * Ensures that the provided text is properly HTML-escaped.
         *
         * If a plain text string is provided, then it will be HTML-escaped and
         * returned as an HtmlSnippet. If the parameter is an HTML snippet
         * then it will be returned directly so as not to double escape it.
         *
         * @param {(string|HtmlSnippet)} html Either a plain text string
         * or an HTML snippet.
         * @returns {HtmlSnippet} A safely escaped HTML snippet.
         */
        ensureHtml = function(html) {
            if (html instanceof HtmlSnippet) {
                return html;
            } else {
                return HTML(_.escape(html));
            }
        };

        /**
         * Returns an HTML snippet by interpolating the provided parameters.
         *
         * The text is provided as a tokenized format string where parameters
         * are indicated via curly braces, e.g. `'Hello {name}'`. These tokens are
         * replaced by the parameter value of the same name.
         *
         * Parameter values will be rendered using their toString methods and then
         * HTML-escaped. The only exception is that instances of the class HTML
         * are rendered without escaping as their contract declares that they are
         * already valid HTML.
         *
         * Example:
         *
         *~~~ javascript
         * HtmlUtils.interpolateHtml(
         *     'You are enrolling in {spanStart}{courseName}{spanEnd}',
         *     {
         *         courseName: 'Rock & Roll 101',
         *         spanStart: HtmlUtils.HTML('<span class="course-title">'),
         *         spanEnd: HtmlUtils.HTML('</span>')
         *     }
         * );
         *~~~
         *
         * returns:
         *
         *~~~ javascript
         * 'You are enrolling in <span class="course-title">Rock &amp; Roll 101</span>'
         *~~~
         *
         * Note: typically the formatString will need to be internationalized, in which
         * case it will be wrapped with a call to an i18n lookup function. If using
         * the Django i18n library this would look like:
         *
         *~~~ javascript
         * HtmlUtils.interpolateHtml(
         *     gettext('You are enrolling in {spanStart}{courseName}{spanEnd}'),
         *     ...
         * );
         *~~~
         *
         * @param {string} formatString The string to be interpolated.
         * @param {Object} parameters An optional set of parameters for interpolation.
         * @returns {HtmlSnippet} The resulting safely escaped HTML snippet.
         */
        interpolateHtml = function(formatString, parameters) {
            var result = StringUtils.interpolate(
                ensureHtml(formatString).toString(),
                _.mapObject(parameters, ensureHtml)
            );
            return HTML(result);
        };

        /**
         * Joins multiple strings and/or HTML snippets together to produce
         * a single safely escaped HTML snippet.
         *
         * For each item, if it is provided as an HTML snippet then it is joined
         * directly. If the item is a string then it is assumed to be unescaped and
         * so it is first escaped before being joined.
         *
         * @param {...(string|HtmlSnippet)} items The strings and/or HTML snippets
         * to be joined together.
         * @returns {HtmlSnippet} The resulting safely escaped HTML snippet.
         */
        joinHtml = function() {
            var html = '',
                argumentCount = arguments.length,
                i;
            for (i = 0; i < argumentCount; i++) {
                html += ensureHtml(arguments[i]);
            }
            return HTML(html);
        };

        /**
         * Returns a function that renders an Underscore template as an HTML snippet.
         *
         * Note: This helper function makes the following context parameters
         * available to the template in addition to those passed in:
         *
         *   - `HtmlUtils`: the `HtmlUtils` helper class
         *   - `StringUtils`: the `StringUtils` helper class
         *
         * @param {string} text
         * @param {object} settings
         * @returns {function} A function that returns a rendered HTML snippet.
         */
        template = function(text, settings) {
            return function(data) {
                var augmentedData = _.extend(
                    {
                        HtmlUtils: HtmlUtils,
                        StringUtils: StringUtils
                    },
                    data || {}
                );
                return HTML(_.template(text, settings)(augmentedData));
            };
        };

        /**
         * A wrapper for `$.html` that safely escapes the provided HTML.
         *
         * If the HTML is provided as an HTML snippet then it is used directly.
         * If the value is a string then it is assumed to be unescaped and
         * so it is first escaped before being used.
         *
         * @param {element} element The element or elements to be updated.
         * @param {(string|HtmlSnippet)} html The desired HTML, either as a
         * plain string or as an HTML snippet.
         * @returns {JQuery} The JQuery object representing the element or elements.
         */
        setHtml = function(element, html) {
            return $(element).html(ensureHtml(html).toString());
        };

        /**
         * A wrapper for `$.append` that safely escapes the provided HTML.
         *
         * If the HTML is provided as an HTML snippet then it is used directly.
         * If the value is a string then it is assumed to be unescaped and
         * so it is first escaped before being used.
         *
         * @param {element} element The element or elements to be updated.
         * @param {(string|HtmlSnippet)} html The desired HTML, either as a
         * plain string or as an HTML snippet.
         * @returns {JQuery} The JQuery object representing the element or elements.
         */
        append = function(element, html) {
            return $(element).append(ensureHtml(html).toString());
        };

        /**
         * A wrapper for `$.prepend` that safely escapes the provided HTML.
         *
         * If the HTML is provided as an HTML snippet then it is used directly.
         * If the value is a string then it is assumed to be unescaped and
         * so it is first escaped before being used.
         *
         * @param {element} element The element or elements to be updated.
         * @param {(string|HtmlSnippet)} html The desired HTML, either as a
         * plain string or as an HTML snippet.
         * @returns {JQuery} The JQuery object representing the element or elements.
         */
        prepend = function(element, html) {
            return $(element).prepend(ensureHtml(html).toString());
        };

        HtmlUtils = {
            append: append,
            ensureHtml: ensureHtml,
            HTML: HTML,
            HtmlSnippet: HtmlSnippet,
            interpolateHtml: interpolateHtml,
            joinHtml: joinHtml,
            prepend: prepend,
            setHtml: setHtml,
            template: template
        };

        return HtmlUtils;
    }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
}).call(
    this,
    // Pick a define function as follows:
    // 1. Use the default 'define' function if it is available
    // 2. If not, use 'RequireJS.define' if that is available
    // 3. else use the GlobalLoader to install the class into the edx namespace
    // eslint-disable-next-line no-nested-ternary
    __webpack_require__("./node_modules/webpack/buildin/amd-define.js")
);


/***/ }),

/***/ "./node_modules/edx-ui-toolkit/src/js/utils/string-utils.js":
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
 * Useful functions for dealing with strings.
 *
 * @module StringUtils
 */
(function(define) {
    'use strict';
    !(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_RESULT__ = function() {
        var interpolate;

        /**
         * Returns a string created by interpolating the provided parameters.
         *
         * The text is provided as a tokenized format string where parameters are
         * indicated via curly braces, e.g. 'Hello {name}'. These tokens are
         * replaced by the parameter value of the same name.
         *
         * Parameter values will be rendered using their toString methods and then
         * HTML-escaped. The only exception is that instances of the class HTML
         * are rendered without escaping as their contract declares that they are
         * already valid HTML.
         *
         * Example:
         *
         *~~~ javascript
         * HtmlUtils.interpolate(
         *     'You are enrolling in {spanStart}{courseName}{spanEnd}',
         *     {
         *         courseName: 'Rock & Roll 101',
         *         spanStart: HtmlUtils.HTML('<span class="course-title">'),
         *         spanEnd: HtmlUtils.HTML('</span>')
         *     }
         * );
         *~~~
         *
         * returns:
         *
         *~~~ javascript
         * 'You are enrolling in <span class="course-title">Rock &amp; Roll 101</span>'
         *~~~
         *
         * Note: typically the formatString will need to be internationalized, in which
         * case it will be wrapped with a call to an i18n lookup function. In Django,
         * this would look like:
         *
         *~~~ javascript
         * HtmlUtils.interpolate(
         *     gettext('You are enrolling in {spanStart}{courseName}{spanEnd}'),
         *     ...
         * );
         *~~~
         *
         * @param {string} formatString The string to be interpolated.
         * @param {Object} parameters An optional set of parameters to the template.
         * @returns {string} A string with the values interpolated.
         */
        interpolate = function(formatString, parameters) {
            return formatString.replace(/{\w+}/g,
                function(parameter) {
                    var parameterName = parameter.slice(1, -1);
                    return String(parameters[parameterName]);
                });
        };

        return {
            interpolate: interpolate
        };
    }.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
}).call(
    this,
    // Pick a define function as follows:
    // 1. Use the default 'define' function if it is available
    // 2. If not, use 'RequireJS.define' if that is available
    // 3. else use the GlobalLoader to install the class into the edx namespace
    // eslint-disable-next-line no-nested-ternary
    __webpack_require__("./node_modules/webpack/buildin/amd-define.js")
);


/***/ }),

/***/ "./node_modules/fbjs/lib/emptyFunction.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";


/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 * 
 */

function makeEmptyFunction(arg) {
  return function () {
    return arg;
  };
}

/**
 * This function accepts and discards inputs; it has no side effects. This is
 * primarily useful idiomatically for overridable function endpoints which
 * always need to be callable, since JS lacks a null-call idiom ala Cocoa.
 */
var emptyFunction = function emptyFunction() {};

emptyFunction.thatReturns = makeEmptyFunction;
emptyFunction.thatReturnsFalse = makeEmptyFunction(false);
emptyFunction.thatReturnsTrue = makeEmptyFunction(true);
emptyFunction.thatReturnsNull = makeEmptyFunction(null);
emptyFunction.thatReturnsThis = function () {
  return this;
};
emptyFunction.thatReturnsArgument = function (arg) {
  return arg;
};

module.exports = emptyFunction;

/***/ }),

/***/ "./node_modules/fbjs/lib/emptyObject.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */



var emptyObject = {};

if (true) {
  Object.freeze(emptyObject);
}

module.exports = emptyObject;

/***/ }),

/***/ "./node_modules/fbjs/lib/invariant.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */



/**
 * Use invariant() to assert state which your program assumes to be true.
 *
 * Provide sprintf-style format (only %s is supported) and arguments
 * to provide information about what broke and what you were
 * expecting.
 *
 * The invariant message will be stripped in production, but the invariant
 * will remain to ensure logic does not differ in production.
 */

var validateFormat = function validateFormat(format) {};

if (true) {
  validateFormat = function validateFormat(format) {
    if (format === undefined) {
      throw new Error('invariant requires an error message argument');
    }
  };
}

function invariant(condition, format, a, b, c, d, e, f) {
  validateFormat(format);

  if (!condition) {
    var error;
    if (format === undefined) {
      error = new Error('Minified exception occurred; use the non-minified dev environment ' + 'for the full error message and additional helpful warnings.');
    } else {
      var args = [a, b, c, d, e, f];
      var argIndex = 0;
      error = new Error(format.replace(/%s/g, function () {
        return args[argIndex++];
      }));
      error.name = 'Invariant Violation';
    }

    error.framesToPop = 1; // we don't care about invariant's own frame
    throw error;
  }
}

module.exports = invariant;

/***/ }),

/***/ "./node_modules/fbjs/lib/warning.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/**
 * Copyright (c) 2014-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */



var emptyFunction = __webpack_require__("./node_modules/fbjs/lib/emptyFunction.js");

/**
 * Similar to invariant but only logs a warning if the condition is not met.
 * This can be used to log issues in development environments in critical
 * paths. Removing the logging code for production environments will keep the
 * same logic and follow the same code paths.
 */

var warning = emptyFunction;

if (true) {
  var printWarning = function printWarning(format) {
    for (var _len = arguments.length, args = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
      args[_key - 1] = arguments[_key];
    }

    var argIndex = 0;
    var message = 'Warning: ' + format.replace(/%s/g, function () {
      return args[argIndex++];
    });
    if (typeof console !== 'undefined') {
      console.error(message);
    }
    try {
      // --- Welcome to debugging React ---
      // This error was thrown as a convenience so that you can use this stack
      // to find the callsite that caused this warning to fire.
      throw new Error(message);
    } catch (x) {}
  };

  warning = function warning(condition, format) {
    if (format === undefined) {
      throw new Error('`warning(condition, format, ...args)` requires a warning ' + 'message argument');
    }

    if (format.indexOf('Failed Composite propType: ') === 0) {
      return; // Ignore CompositeComponent proptype check.
    }

    if (!condition) {
      for (var _len2 = arguments.length, args = Array(_len2 > 2 ? _len2 - 2 : 0), _key2 = 2; _key2 < _len2; _key2++) {
        args[_key2 - 2] = arguments[_key2];
      }

      printWarning.apply(undefined, [format].concat(args));
    }
  };
}

module.exports = warning;

/***/ }),

/***/ "./node_modules/object-assign/index.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/*
object-assign
(c) Sindre Sorhus
@license MIT
*/


/* eslint-disable no-unused-vars */
var getOwnPropertySymbols = Object.getOwnPropertySymbols;
var hasOwnProperty = Object.prototype.hasOwnProperty;
var propIsEnumerable = Object.prototype.propertyIsEnumerable;

function toObject(val) {
	if (val === null || val === undefined) {
		throw new TypeError('Object.assign cannot be called with null or undefined');
	}

	return Object(val);
}

function shouldUseNative() {
	try {
		if (!Object.assign) {
			return false;
		}

		// Detect buggy property enumeration order in older V8 versions.

		// https://bugs.chromium.org/p/v8/issues/detail?id=4118
		var test1 = new String('abc');  // eslint-disable-line no-new-wrappers
		test1[5] = 'de';
		if (Object.getOwnPropertyNames(test1)[0] === '5') {
			return false;
		}

		// https://bugs.chromium.org/p/v8/issues/detail?id=3056
		var test2 = {};
		for (var i = 0; i < 10; i++) {
			test2['_' + String.fromCharCode(i)] = i;
		}
		var order2 = Object.getOwnPropertyNames(test2).map(function (n) {
			return test2[n];
		});
		if (order2.join('') !== '0123456789') {
			return false;
		}

		// https://bugs.chromium.org/p/v8/issues/detail?id=3056
		var test3 = {};
		'abcdefghijklmnopqrst'.split('').forEach(function (letter) {
			test3[letter] = letter;
		});
		if (Object.keys(Object.assign({}, test3)).join('') !==
				'abcdefghijklmnopqrst') {
			return false;
		}

		return true;
	} catch (err) {
		// We don't expect any of the above to throw, but better to be safe.
		return false;
	}
}

module.exports = shouldUseNative() ? Object.assign : function (target, source) {
	var from;
	var to = toObject(target);
	var symbols;

	for (var s = 1; s < arguments.length; s++) {
		from = Object(arguments[s]);

		for (var key in from) {
			if (hasOwnProperty.call(from, key)) {
				to[key] = from[key];
			}
		}

		if (getOwnPropertySymbols) {
			symbols = getOwnPropertySymbols(from);
			for (var i = 0; i < symbols.length; i++) {
				if (propIsEnumerable.call(from, symbols[i])) {
					to[symbols[i]] = from[symbols[i]];
				}
			}
		}
	}

	return to;
};


/***/ }),

/***/ "./node_modules/prop-types/checkPropTypes.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */



if (true) {
  var invariant = __webpack_require__("./node_modules/fbjs/lib/invariant.js");
  var warning = __webpack_require__("./node_modules/fbjs/lib/warning.js");
  var ReactPropTypesSecret = __webpack_require__("./node_modules/prop-types/lib/ReactPropTypesSecret.js");
  var loggedTypeFailures = {};
}

/**
 * Assert that the values match with the type specs.
 * Error messages are memorized and will only be shown once.
 *
 * @param {object} typeSpecs Map of name to a ReactPropType
 * @param {object} values Runtime values that need to be type-checked
 * @param {string} location e.g. "prop", "context", "child context"
 * @param {string} componentName Name of the component for error messages.
 * @param {?Function} getStack Returns the component stack.
 * @private
 */
function checkPropTypes(typeSpecs, values, location, componentName, getStack) {
  if (true) {
    for (var typeSpecName in typeSpecs) {
      if (typeSpecs.hasOwnProperty(typeSpecName)) {
        var error;
        // Prop type validation may throw. In case they do, we don't want to
        // fail the render phase where it didn't fail before. So we log it.
        // After these have been cleaned up, we'll let them throw.
        try {
          // This is intentionally an invariant that gets caught. It's the same
          // behavior as without this statement except with a better message.
          invariant(typeof typeSpecs[typeSpecName] === 'function', '%s: %s type `%s` is invalid; it must be a function, usually from ' + 'the `prop-types` package, but received `%s`.', componentName || 'React class', location, typeSpecName, typeof typeSpecs[typeSpecName]);
          error = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, ReactPropTypesSecret);
        } catch (ex) {
          error = ex;
        }
        warning(!error || error instanceof Error, '%s: type specification of %s `%s` is invalid; the type checker ' + 'function must return `null` or an `Error` but returned a %s. ' + 'You may have forgotten to pass an argument to the type checker ' + 'creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and ' + 'shape all require an argument).', componentName || 'React class', location, typeSpecName, typeof error);
        if (error instanceof Error && !(error.message in loggedTypeFailures)) {
          // Only monitor this failure once because there tends to be a lot of the
          // same error.
          loggedTypeFailures[error.message] = true;

          var stack = getStack ? getStack() : '';

          warning(false, 'Failed %s type: %s%s', location, error.message, stack != null ? stack : '');
        }
      }
    }
  }
}

module.exports = checkPropTypes;


/***/ }),

/***/ "./node_modules/prop-types/factoryWithTypeCheckers.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */



var emptyFunction = __webpack_require__("./node_modules/fbjs/lib/emptyFunction.js");
var invariant = __webpack_require__("./node_modules/fbjs/lib/invariant.js");
var warning = __webpack_require__("./node_modules/fbjs/lib/warning.js");
var assign = __webpack_require__("./node_modules/object-assign/index.js");

var ReactPropTypesSecret = __webpack_require__("./node_modules/prop-types/lib/ReactPropTypesSecret.js");
var checkPropTypes = __webpack_require__("./node_modules/prop-types/checkPropTypes.js");

module.exports = function(isValidElement, throwOnDirectAccess) {
  /* global Symbol */
  var ITERATOR_SYMBOL = typeof Symbol === 'function' && Symbol.iterator;
  var FAUX_ITERATOR_SYMBOL = '@@iterator'; // Before Symbol spec.

  /**
   * Returns the iterator method function contained on the iterable object.
   *
   * Be sure to invoke the function with the iterable as context:
   *
   *     var iteratorFn = getIteratorFn(myIterable);
   *     if (iteratorFn) {
   *       var iterator = iteratorFn.call(myIterable);
   *       ...
   *     }
   *
   * @param {?object} maybeIterable
   * @return {?function}
   */
  function getIteratorFn(maybeIterable) {
    var iteratorFn = maybeIterable && (ITERATOR_SYMBOL && maybeIterable[ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL]);
    if (typeof iteratorFn === 'function') {
      return iteratorFn;
    }
  }

  /**
   * Collection of methods that allow declaration and validation of props that are
   * supplied to React components. Example usage:
   *
   *   var Props = require('ReactPropTypes');
   *   var MyArticle = React.createClass({
   *     propTypes: {
   *       // An optional string prop named "description".
   *       description: Props.string,
   *
   *       // A required enum prop named "category".
   *       category: Props.oneOf(['News','Photos']).isRequired,
   *
   *       // A prop named "dialog" that requires an instance of Dialog.
   *       dialog: Props.instanceOf(Dialog).isRequired
   *     },
   *     render: function() { ... }
   *   });
   *
   * A more formal specification of how these methods are used:
   *
   *   type := array|bool|func|object|number|string|oneOf([...])|instanceOf(...)
   *   decl := ReactPropTypes.{type}(.isRequired)?
   *
   * Each and every declaration produces a function with the same signature. This
   * allows the creation of custom validation functions. For example:
   *
   *  var MyLink = React.createClass({
   *    propTypes: {
   *      // An optional string or URI prop named "href".
   *      href: function(props, propName, componentName) {
   *        var propValue = props[propName];
   *        if (propValue != null && typeof propValue !== 'string' &&
   *            !(propValue instanceof URI)) {
   *          return new Error(
   *            'Expected a string or an URI for ' + propName + ' in ' +
   *            componentName
   *          );
   *        }
   *      }
   *    },
   *    render: function() {...}
   *  });
   *
   * @internal
   */

  var ANONYMOUS = '<<anonymous>>';

  // Important!
  // Keep this list in sync with production version in `./factoryWithThrowingShims.js`.
  var ReactPropTypes = {
    array: createPrimitiveTypeChecker('array'),
    bool: createPrimitiveTypeChecker('boolean'),
    func: createPrimitiveTypeChecker('function'),
    number: createPrimitiveTypeChecker('number'),
    object: createPrimitiveTypeChecker('object'),
    string: createPrimitiveTypeChecker('string'),
    symbol: createPrimitiveTypeChecker('symbol'),

    any: createAnyTypeChecker(),
    arrayOf: createArrayOfTypeChecker,
    element: createElementTypeChecker(),
    instanceOf: createInstanceTypeChecker,
    node: createNodeChecker(),
    objectOf: createObjectOfTypeChecker,
    oneOf: createEnumTypeChecker,
    oneOfType: createUnionTypeChecker,
    shape: createShapeTypeChecker,
    exact: createStrictShapeTypeChecker,
  };

  /**
   * inlined Object.is polyfill to avoid requiring consumers ship their own
   * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is
   */
  /*eslint-disable no-self-compare*/
  function is(x, y) {
    // SameValue algorithm
    if (x === y) {
      // Steps 1-5, 7-10
      // Steps 6.b-6.e: +0 != -0
      return x !== 0 || 1 / x === 1 / y;
    } else {
      // Step 6.a: NaN == NaN
      return x !== x && y !== y;
    }
  }
  /*eslint-enable no-self-compare*/

  /**
   * We use an Error-like object for backward compatibility as people may call
   * PropTypes directly and inspect their output. However, we don't use real
   * Errors anymore. We don't inspect their stack anyway, and creating them
   * is prohibitively expensive if they are created too often, such as what
   * happens in oneOfType() for any type before the one that matched.
   */
  function PropTypeError(message) {
    this.message = message;
    this.stack = '';
  }
  // Make `instanceof Error` still work for returned errors.
  PropTypeError.prototype = Error.prototype;

  function createChainableTypeChecker(validate) {
    if (true) {
      var manualPropTypeCallCache = {};
      var manualPropTypeWarningCount = 0;
    }
    function checkType(isRequired, props, propName, componentName, location, propFullName, secret) {
      componentName = componentName || ANONYMOUS;
      propFullName = propFullName || propName;

      if (secret !== ReactPropTypesSecret) {
        if (throwOnDirectAccess) {
          // New behavior only for users of `prop-types` package
          invariant(
            false,
            'Calling PropTypes validators directly is not supported by the `prop-types` package. ' +
            'Use `PropTypes.checkPropTypes()` to call them. ' +
            'Read more at http://fb.me/use-check-prop-types'
          );
        } else if ("development" !== 'production' && typeof console !== 'undefined') {
          // Old behavior for people using React.PropTypes
          var cacheKey = componentName + ':' + propName;
          if (
            !manualPropTypeCallCache[cacheKey] &&
            // Avoid spamming the console because they are often not actionable except for lib authors
            manualPropTypeWarningCount < 3
          ) {
            warning(
              false,
              'You are manually calling a React.PropTypes validation ' +
              'function for the `%s` prop on `%s`. This is deprecated ' +
              'and will throw in the standalone `prop-types` package. ' +
              'You may be seeing this warning due to a third-party PropTypes ' +
              'library. See https://fb.me/react-warning-dont-call-proptypes ' + 'for details.',
              propFullName,
              componentName
            );
            manualPropTypeCallCache[cacheKey] = true;
            manualPropTypeWarningCount++;
          }
        }
      }
      if (props[propName] == null) {
        if (isRequired) {
          if (props[propName] === null) {
            return new PropTypeError('The ' + location + ' `' + propFullName + '` is marked as required ' + ('in `' + componentName + '`, but its value is `null`.'));
          }
          return new PropTypeError('The ' + location + ' `' + propFullName + '` is marked as required in ' + ('`' + componentName + '`, but its value is `undefined`.'));
        }
        return null;
      } else {
        return validate(props, propName, componentName, location, propFullName);
      }
    }

    var chainedCheckType = checkType.bind(null, false);
    chainedCheckType.isRequired = checkType.bind(null, true);

    return chainedCheckType;
  }

  function createPrimitiveTypeChecker(expectedType) {
    function validate(props, propName, componentName, location, propFullName, secret) {
      var propValue = props[propName];
      var propType = getPropType(propValue);
      if (propType !== expectedType) {
        // `propValue` being instance of, say, date/regexp, pass the 'object'
        // check, but we can offer a more precise error message here rather than
        // 'of type `object`'.
        var preciseType = getPreciseType(propValue);

        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type ' + ('`' + preciseType + '` supplied to `' + componentName + '`, expected ') + ('`' + expectedType + '`.'));
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createAnyTypeChecker() {
    return createChainableTypeChecker(emptyFunction.thatReturnsNull);
  }

  function createArrayOfTypeChecker(typeChecker) {
    function validate(props, propName, componentName, location, propFullName) {
      if (typeof typeChecker !== 'function') {
        return new PropTypeError('Property `' + propFullName + '` of component `' + componentName + '` has invalid PropType notation inside arrayOf.');
      }
      var propValue = props[propName];
      if (!Array.isArray(propValue)) {
        var propType = getPropType(propValue);
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type ' + ('`' + propType + '` supplied to `' + componentName + '`, expected an array.'));
      }
      for (var i = 0; i < propValue.length; i++) {
        var error = typeChecker(propValue, i, componentName, location, propFullName + '[' + i + ']', ReactPropTypesSecret);
        if (error instanceof Error) {
          return error;
        }
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createElementTypeChecker() {
    function validate(props, propName, componentName, location, propFullName) {
      var propValue = props[propName];
      if (!isValidElement(propValue)) {
        var propType = getPropType(propValue);
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type ' + ('`' + propType + '` supplied to `' + componentName + '`, expected a single ReactElement.'));
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createInstanceTypeChecker(expectedClass) {
    function validate(props, propName, componentName, location, propFullName) {
      if (!(props[propName] instanceof expectedClass)) {
        var expectedClassName = expectedClass.name || ANONYMOUS;
        var actualClassName = getClassName(props[propName]);
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type ' + ('`' + actualClassName + '` supplied to `' + componentName + '`, expected ') + ('instance of `' + expectedClassName + '`.'));
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createEnumTypeChecker(expectedValues) {
    if (!Array.isArray(expectedValues)) {
       true ? warning(false, 'Invalid argument supplied to oneOf, expected an instance of array.') : void 0;
      return emptyFunction.thatReturnsNull;
    }

    function validate(props, propName, componentName, location, propFullName) {
      var propValue = props[propName];
      for (var i = 0; i < expectedValues.length; i++) {
        if (is(propValue, expectedValues[i])) {
          return null;
        }
      }

      var valuesString = JSON.stringify(expectedValues);
      return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of value `' + propValue + '` ' + ('supplied to `' + componentName + '`, expected one of ' + valuesString + '.'));
    }
    return createChainableTypeChecker(validate);
  }

  function createObjectOfTypeChecker(typeChecker) {
    function validate(props, propName, componentName, location, propFullName) {
      if (typeof typeChecker !== 'function') {
        return new PropTypeError('Property `' + propFullName + '` of component `' + componentName + '` has invalid PropType notation inside objectOf.');
      }
      var propValue = props[propName];
      var propType = getPropType(propValue);
      if (propType !== 'object') {
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type ' + ('`' + propType + '` supplied to `' + componentName + '`, expected an object.'));
      }
      for (var key in propValue) {
        if (propValue.hasOwnProperty(key)) {
          var error = typeChecker(propValue, key, componentName, location, propFullName + '.' + key, ReactPropTypesSecret);
          if (error instanceof Error) {
            return error;
          }
        }
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createUnionTypeChecker(arrayOfTypeCheckers) {
    if (!Array.isArray(arrayOfTypeCheckers)) {
       true ? warning(false, 'Invalid argument supplied to oneOfType, expected an instance of array.') : void 0;
      return emptyFunction.thatReturnsNull;
    }

    for (var i = 0; i < arrayOfTypeCheckers.length; i++) {
      var checker = arrayOfTypeCheckers[i];
      if (typeof checker !== 'function') {
        warning(
          false,
          'Invalid argument supplied to oneOfType. Expected an array of check functions, but ' +
          'received %s at index %s.',
          getPostfixForTypeWarning(checker),
          i
        );
        return emptyFunction.thatReturnsNull;
      }
    }

    function validate(props, propName, componentName, location, propFullName) {
      for (var i = 0; i < arrayOfTypeCheckers.length; i++) {
        var checker = arrayOfTypeCheckers[i];
        if (checker(props, propName, componentName, location, propFullName, ReactPropTypesSecret) == null) {
          return null;
        }
      }

      return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` supplied to ' + ('`' + componentName + '`.'));
    }
    return createChainableTypeChecker(validate);
  }

  function createNodeChecker() {
    function validate(props, propName, componentName, location, propFullName) {
      if (!isNode(props[propName])) {
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` supplied to ' + ('`' + componentName + '`, expected a ReactNode.'));
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createShapeTypeChecker(shapeTypes) {
    function validate(props, propName, componentName, location, propFullName) {
      var propValue = props[propName];
      var propType = getPropType(propValue);
      if (propType !== 'object') {
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type `' + propType + '` ' + ('supplied to `' + componentName + '`, expected `object`.'));
      }
      for (var key in shapeTypes) {
        var checker = shapeTypes[key];
        if (!checker) {
          continue;
        }
        var error = checker(propValue, key, componentName, location, propFullName + '.' + key, ReactPropTypesSecret);
        if (error) {
          return error;
        }
      }
      return null;
    }
    return createChainableTypeChecker(validate);
  }

  function createStrictShapeTypeChecker(shapeTypes) {
    function validate(props, propName, componentName, location, propFullName) {
      var propValue = props[propName];
      var propType = getPropType(propValue);
      if (propType !== 'object') {
        return new PropTypeError('Invalid ' + location + ' `' + propFullName + '` of type `' + propType + '` ' + ('supplied to `' + componentName + '`, expected `object`.'));
      }
      // We need to check all keys in case some are required but missing from
      // props.
      var allKeys = assign({}, props[propName], shapeTypes);
      for (var key in allKeys) {
        var checker = shapeTypes[key];
        if (!checker) {
          return new PropTypeError(
            'Invalid ' + location + ' `' + propFullName + '` key `' + key + '` supplied to `' + componentName + '`.' +
            '\nBad object: ' + JSON.stringify(props[propName], null, '  ') +
            '\nValid keys: ' +  JSON.stringify(Object.keys(shapeTypes), null, '  ')
          );
        }
        var error = checker(propValue, key, componentName, location, propFullName + '.' + key, ReactPropTypesSecret);
        if (error) {
          return error;
        }
      }
      return null;
    }

    return createChainableTypeChecker(validate);
  }

  function isNode(propValue) {
    switch (typeof propValue) {
      case 'number':
      case 'string':
      case 'undefined':
        return true;
      case 'boolean':
        return !propValue;
      case 'object':
        if (Array.isArray(propValue)) {
          return propValue.every(isNode);
        }
        if (propValue === null || isValidElement(propValue)) {
          return true;
        }

        var iteratorFn = getIteratorFn(propValue);
        if (iteratorFn) {
          var iterator = iteratorFn.call(propValue);
          var step;
          if (iteratorFn !== propValue.entries) {
            while (!(step = iterator.next()).done) {
              if (!isNode(step.value)) {
                return false;
              }
            }
          } else {
            // Iterator will provide entry [k,v] tuples rather than values.
            while (!(step = iterator.next()).done) {
              var entry = step.value;
              if (entry) {
                if (!isNode(entry[1])) {
                  return false;
                }
              }
            }
          }
        } else {
          return false;
        }

        return true;
      default:
        return false;
    }
  }

  function isSymbol(propType, propValue) {
    // Native Symbol.
    if (propType === 'symbol') {
      return true;
    }

    // 19.4.3.5 Symbol.prototype[@@toStringTag] === 'Symbol'
    if (propValue['@@toStringTag'] === 'Symbol') {
      return true;
    }

    // Fallback for non-spec compliant Symbols which are polyfilled.
    if (typeof Symbol === 'function' && propValue instanceof Symbol) {
      return true;
    }

    return false;
  }

  // Equivalent of `typeof` but with special handling for array and regexp.
  function getPropType(propValue) {
    var propType = typeof propValue;
    if (Array.isArray(propValue)) {
      return 'array';
    }
    if (propValue instanceof RegExp) {
      // Old webkits (at least until Android 4.0) return 'function' rather than
      // 'object' for typeof a RegExp. We'll normalize this here so that /bla/
      // passes PropTypes.object.
      return 'object';
    }
    if (isSymbol(propType, propValue)) {
      return 'symbol';
    }
    return propType;
  }

  // This handles more types than `getPropType`. Only used for error messages.
  // See `createPrimitiveTypeChecker`.
  function getPreciseType(propValue) {
    if (typeof propValue === 'undefined' || propValue === null) {
      return '' + propValue;
    }
    var propType = getPropType(propValue);
    if (propType === 'object') {
      if (propValue instanceof Date) {
        return 'date';
      } else if (propValue instanceof RegExp) {
        return 'regexp';
      }
    }
    return propType;
  }

  // Returns a string that is postfixed to a warning about an invalid type.
  // For example, "undefined" or "of type array"
  function getPostfixForTypeWarning(value) {
    var type = getPreciseType(value);
    switch (type) {
      case 'array':
      case 'object':
        return 'an ' + type;
      case 'boolean':
      case 'date':
      case 'regexp':
        return 'a ' + type;
      default:
        return type;
    }
  }

  // Returns class name of the object, if any.
  function getClassName(propValue) {
    if (!propValue.constructor || !propValue.constructor.name) {
      return ANONYMOUS;
    }
    return propValue.constructor.name;
  }

  ReactPropTypes.checkPropTypes = checkPropTypes;
  ReactPropTypes.PropTypes = ReactPropTypes;

  return ReactPropTypes;
};


/***/ }),

/***/ "./node_modules/prop-types/index.js":
/***/ (function(module, exports, __webpack_require__) {

/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

if (true) {
  var REACT_ELEMENT_TYPE = (typeof Symbol === 'function' &&
    Symbol.for &&
    Symbol.for('react.element')) ||
    0xeac7;

  var isValidElement = function(object) {
    return typeof object === 'object' &&
      object !== null &&
      object.$$typeof === REACT_ELEMENT_TYPE;
  };

  // By explicitly using `prop-types` you are opting into new development behavior.
  // http://fb.me/prop-types-in-prod
  var throwOnDirectAccess = true;
  module.exports = __webpack_require__("./node_modules/prop-types/factoryWithTypeCheckers.js")(isValidElement, throwOnDirectAccess);
} else {
  // By explicitly using `prop-types` you are opting into new production behavior.
  // http://fb.me/prop-types-in-prod
  module.exports = require('./factoryWithThrowingShims')();
}


/***/ }),

/***/ "./node_modules/prop-types/lib/ReactPropTypesSecret.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/**
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */



var ReactPropTypesSecret = 'SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED';

module.exports = ReactPropTypesSecret;


/***/ }),

/***/ "./node_modules/react/cjs/react.development.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";
/** @license React v16.1.0
 * react.development.js
 *
 * Copyright (c) 2013-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */



if (true) {
  (function() {
'use strict';

var _assign = __webpack_require__("./node_modules/object-assign/index.js");
var invariant = __webpack_require__("./node_modules/fbjs/lib/invariant.js");
var emptyObject = __webpack_require__("./node_modules/fbjs/lib/emptyObject.js");
var warning = __webpack_require__("./node_modules/fbjs/lib/warning.js");
var emptyFunction = __webpack_require__("./node_modules/fbjs/lib/emptyFunction.js");
var checkPropTypes = __webpack_require__("./node_modules/prop-types/checkPropTypes.js");

// TODO: this is special because it gets imported during build.

var ReactVersion = '16.1.0';

/**
 * WARNING: DO NOT manually require this module.
 * This is a replacement for `invariant(...)` used by the error code system
 * and will _only_ be required by the corresponding babel pass.
 * It always throws.
 */

// Exports React.Fragment
var enableReactFragment = false;
// Exports ReactDOM.createRoot



// Mutating mode (React DOM, React ART, React Native):

// Experimental noop mode (currently unused):

// Experimental persistent mode (CS):


// Only used in www builds.

/**
 * Forked from fbjs/warning:
 * https://github.com/facebook/fbjs/blob/e66ba20ad5be433eb54423f2b097d829324d9de6/packages/fbjs/src/__forks__/warning.js
 *
 * Only change is we use console.warn instead of console.error,
 * and do nothing when 'console' is not supported.
 * This really simplifies the code.
 * ---
 * Similar to invariant but only logs a warning if the condition is not met.
 * This can be used to log issues in development environments in critical
 * paths. Removing the logging code for production environments will keep the
 * same logic and follow the same code paths.
 */

var lowPriorityWarning = function () {};

{
  var printWarning = function (format) {
    for (var _len = arguments.length, args = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
      args[_key - 1] = arguments[_key];
    }

    var argIndex = 0;
    var message = 'Warning: ' + format.replace(/%s/g, function () {
      return args[argIndex++];
    });
    if (typeof console !== 'undefined') {
      console.warn(message);
    }
    try {
      // --- Welcome to debugging React ---
      // This error was thrown as a convenience so that you can use this stack
      // to find the callsite that caused this warning to fire.
      throw new Error(message);
    } catch (x) {}
  };

  lowPriorityWarning = function (condition, format) {
    if (format === undefined) {
      throw new Error('`warning(condition, format, ...args)` requires a warning ' + 'message argument');
    }
    if (!condition) {
      for (var _len2 = arguments.length, args = Array(_len2 > 2 ? _len2 - 2 : 0), _key2 = 2; _key2 < _len2; _key2++) {
        args[_key2 - 2] = arguments[_key2];
      }

      printWarning.apply(undefined, [format].concat(args));
    }
  };
}

var lowPriorityWarning$1 = lowPriorityWarning;

var didWarnStateUpdateForUnmountedComponent = {};

function warnNoop(publicInstance, callerName) {
  {
    var constructor = publicInstance.constructor;
    var componentName = constructor && (constructor.displayName || constructor.name) || 'ReactClass';
    var warningKey = componentName + '.' + callerName;
    if (didWarnStateUpdateForUnmountedComponent[warningKey]) {
      return;
    }
    warning(false, '%s(...): Can only update a mounted or mounting component. ' + 'This usually means you called %s() on an unmounted component. ' + 'This is a no-op.\n\nPlease check the code for the %s component.', callerName, callerName, componentName);
    didWarnStateUpdateForUnmountedComponent[warningKey] = true;
  }
}

/**
 * This is the abstract API for an update queue.
 */
var ReactNoopUpdateQueue = {
  /**
   * Checks whether or not this composite component is mounted.
   * @param {ReactClass} publicInstance The instance we want to test.
   * @return {boolean} True if mounted, false otherwise.
   * @protected
   * @final
   */
  isMounted: function (publicInstance) {
    return false;
  },

  /**
   * Forces an update. This should only be invoked when it is known with
   * certainty that we are **not** in a DOM transaction.
   *
   * You may want to call this when you know that some deeper aspect of the
   * component's state has changed but `setState` was not called.
   *
   * This will not invoke `shouldComponentUpdate`, but it will invoke
   * `componentWillUpdate` and `componentDidUpdate`.
   *
   * @param {ReactClass} publicInstance The instance that should rerender.
   * @param {?function} callback Called after component is updated.
   * @param {?string} callerName name of the calling function in the public API.
   * @internal
   */
  enqueueForceUpdate: function (publicInstance, callback, callerName) {
    warnNoop(publicInstance, 'forceUpdate');
  },

  /**
   * Replaces all of the state. Always use this or `setState` to mutate state.
   * You should treat `this.state` as immutable.
   *
   * There is no guarantee that `this.state` will be immediately updated, so
   * accessing `this.state` after calling this method may return the old value.
   *
   * @param {ReactClass} publicInstance The instance that should rerender.
   * @param {object} completeState Next state.
   * @param {?function} callback Called after component is updated.
   * @param {?string} callerName name of the calling function in the public API.
   * @internal
   */
  enqueueReplaceState: function (publicInstance, completeState, callback, callerName) {
    warnNoop(publicInstance, 'replaceState');
  },

  /**
   * Sets a subset of the state. This only exists because _pendingState is
   * internal. This provides a merging strategy that is not available to deep
   * properties which is confusing. TODO: Expose pendingState or don't use it
   * during the merge.
   *
   * @param {ReactClass} publicInstance The instance that should rerender.
   * @param {object} partialState Next partial state to be merged with state.
   * @param {?function} callback Called after component is updated.
   * @param {?string} Name of the calling function in the public API.
   * @internal
   */
  enqueueSetState: function (publicInstance, partialState, callback, callerName) {
    warnNoop(publicInstance, 'setState');
  }
};

/**
 * Base class helpers for the updating state of a component.
 */
function Component(props, context, updater) {
  this.props = props;
  this.context = context;
  this.refs = emptyObject;
  // We initialize the default updater but the real one gets injected by the
  // renderer.
  this.updater = updater || ReactNoopUpdateQueue;
}

Component.prototype.isReactComponent = {};

/**
 * Sets a subset of the state. Always use this to mutate
 * state. You should treat `this.state` as immutable.
 *
 * There is no guarantee that `this.state` will be immediately updated, so
 * accessing `this.state` after calling this method may return the old value.
 *
 * There is no guarantee that calls to `setState` will run synchronously,
 * as they may eventually be batched together.  You can provide an optional
 * callback that will be executed when the call to setState is actually
 * completed.
 *
 * When a function is provided to setState, it will be called at some point in
 * the future (not synchronously). It will be called with the up to date
 * component arguments (state, props, context). These values can be different
 * from this.* because your function may be called after receiveProps but before
 * shouldComponentUpdate, and this new state, props, and context will not yet be
 * assigned to this.
 *
 * @param {object|function} partialState Next partial state or function to
 *        produce next partial state to be merged with current state.
 * @param {?function} callback Called after state is updated.
 * @final
 * @protected
 */
Component.prototype.setState = function (partialState, callback) {
  !(typeof partialState === 'object' || typeof partialState === 'function' || partialState == null) ? invariant(false, 'setState(...): takes an object of state variables to update or a function which returns an object of state variables.') : void 0;
  this.updater.enqueueSetState(this, partialState, callback, 'setState');
};

/**
 * Forces an update. This should only be invoked when it is known with
 * certainty that we are **not** in a DOM transaction.
 *
 * You may want to call this when you know that some deeper aspect of the
 * component's state has changed but `setState` was not called.
 *
 * This will not invoke `shouldComponentUpdate`, but it will invoke
 * `componentWillUpdate` and `componentDidUpdate`.
 *
 * @param {?function} callback Called after update is complete.
 * @final
 * @protected
 */
Component.prototype.forceUpdate = function (callback) {
  this.updater.enqueueForceUpdate(this, callback, 'forceUpdate');
};

/**
 * Deprecated APIs. These APIs used to exist on classic React classes but since
 * we would like to deprecate them, we're not going to move them over to this
 * modern base class. Instead, we define a getter that warns if it's accessed.
 */
{
  var deprecatedAPIs = {
    isMounted: ['isMounted', 'Instead, make sure to clean up subscriptions and pending requests in ' + 'componentWillUnmount to prevent memory leaks.'],
    replaceState: ['replaceState', 'Refactor your code to use setState instead (see ' + 'https://github.com/facebook/react/issues/3236).']
  };
  var defineDeprecationWarning = function (methodName, info) {
    Object.defineProperty(Component.prototype, methodName, {
      get: function () {
        lowPriorityWarning$1(false, '%s(...) is deprecated in plain JavaScript React classes. %s', info[0], info[1]);
        return undefined;
      }
    });
  };
  for (var fnName in deprecatedAPIs) {
    if (deprecatedAPIs.hasOwnProperty(fnName)) {
      defineDeprecationWarning(fnName, deprecatedAPIs[fnName]);
    }
  }
}

/**
 * Base class helpers for the updating state of a component.
 */
function PureComponent(props, context, updater) {
  // Duplicated from Component.
  this.props = props;
  this.context = context;
  this.refs = emptyObject;
  // We initialize the default updater but the real one gets injected by the
  // renderer.
  this.updater = updater || ReactNoopUpdateQueue;
}

function ComponentDummy() {}
ComponentDummy.prototype = Component.prototype;
var pureComponentPrototype = PureComponent.prototype = new ComponentDummy();
pureComponentPrototype.constructor = PureComponent;
// Avoid an extra prototype jump for these methods.
_assign(pureComponentPrototype, Component.prototype);
pureComponentPrototype.isPureReactComponent = true;

function AsyncComponent(props, context, updater) {
  // Duplicated from Component.
  this.props = props;
  this.context = context;
  this.refs = emptyObject;
  // We initialize the default updater but the real one gets injected by the
  // renderer.
  this.updater = updater || ReactNoopUpdateQueue;
}

var asyncComponentPrototype = AsyncComponent.prototype = new ComponentDummy();
asyncComponentPrototype.constructor = AsyncComponent;
// Avoid an extra prototype jump for these methods.
_assign(asyncComponentPrototype, Component.prototype);
asyncComponentPrototype.unstable_isAsyncReactComponent = true;
asyncComponentPrototype.render = function () {
  return this.props.children;
};

/**
 * Keeps track of the current owner.
 *
 * The current owner is the component who should own any components that are
 * currently being constructed.
 */
var ReactCurrentOwner = {
  /**
   * @internal
   * @type {ReactComponent}
   */
  current: null
};

var hasOwnProperty = Object.prototype.hasOwnProperty;

// The Symbol used to tag the ReactElement type. If there is no native Symbol
// nor polyfill, then a plain number is used for performance.
var REACT_ELEMENT_TYPE$1 = typeof Symbol === 'function' && Symbol['for'] && Symbol['for']('react.element') || 0xeac7;

var RESERVED_PROPS = {
  key: true,
  ref: true,
  __self: true,
  __source: true
};

var specialPropKeyWarningShown;
var specialPropRefWarningShown;

function hasValidRef(config) {
  {
    if (hasOwnProperty.call(config, 'ref')) {
      var getter = Object.getOwnPropertyDescriptor(config, 'ref').get;
      if (getter && getter.isReactWarning) {
        return false;
      }
    }
  }
  return config.ref !== undefined;
}

function hasValidKey(config) {
  {
    if (hasOwnProperty.call(config, 'key')) {
      var getter = Object.getOwnPropertyDescriptor(config, 'key').get;
      if (getter && getter.isReactWarning) {
        return false;
      }
    }
  }
  return config.key !== undefined;
}

function defineKeyPropWarningGetter(props, displayName) {
  var warnAboutAccessingKey = function () {
    if (!specialPropKeyWarningShown) {
      specialPropKeyWarningShown = true;
      warning(false, '%s: `key` is not a prop. Trying to access it will result ' + 'in `undefined` being returned. If you need to access the same ' + 'value within the child component, you should pass it as a different ' + 'prop. (https://fb.me/react-special-props)', displayName);
    }
  };
  warnAboutAccessingKey.isReactWarning = true;
  Object.defineProperty(props, 'key', {
    get: warnAboutAccessingKey,
    configurable: true
  });
}

function defineRefPropWarningGetter(props, displayName) {
  var warnAboutAccessingRef = function () {
    if (!specialPropRefWarningShown) {
      specialPropRefWarningShown = true;
      warning(false, '%s: `ref` is not a prop. Trying to access it will result ' + 'in `undefined` being returned. If you need to access the same ' + 'value within the child component, you should pass it as a different ' + 'prop. (https://fb.me/react-special-props)', displayName);
    }
  };
  warnAboutAccessingRef.isReactWarning = true;
  Object.defineProperty(props, 'ref', {
    get: warnAboutAccessingRef,
    configurable: true
  });
}

/**
 * Factory method to create a new React element. This no longer adheres to
 * the class pattern, so do not use new to call it. Also, no instanceof check
 * will work. Instead test $$typeof field against Symbol.for('react.element') to check
 * if something is a React Element.
 *
 * @param {*} type
 * @param {*} key
 * @param {string|object} ref
 * @param {*} self A *temporary* helper to detect places where `this` is
 * different from the `owner` when React.createElement is called, so that we
 * can warn. We want to get rid of owner and replace string `ref`s with arrow
 * functions, and as long as `this` and owner are the same, there will be no
 * change in behavior.
 * @param {*} source An annotation object (added by a transpiler or otherwise)
 * indicating filename, line number, and/or other information.
 * @param {*} owner
 * @param {*} props
 * @internal
 */
var ReactElement = function (type, key, ref, self, source, owner, props) {
  var element = {
    // This tag allow us to uniquely identify this as a React Element
    $$typeof: REACT_ELEMENT_TYPE$1,

    // Built-in properties that belong on the element
    type: type,
    key: key,
    ref: ref,
    props: props,

    // Record the component responsible for creating this element.
    _owner: owner
  };

  {
    // The validation flag is currently mutative. We put it on
    // an external backing store so that we can freeze the whole object.
    // This can be replaced with a WeakMap once they are implemented in
    // commonly used development environments.
    element._store = {};

    // To make comparing ReactElements easier for testing purposes, we make
    // the validation flag non-enumerable (where possible, which should
    // include every environment we run tests in), so the test framework
    // ignores it.
    Object.defineProperty(element._store, 'validated', {
      configurable: false,
      enumerable: false,
      writable: true,
      value: false
    });
    // self and source are DEV only properties.
    Object.defineProperty(element, '_self', {
      configurable: false,
      enumerable: false,
      writable: false,
      value: self
    });
    // Two elements created in two different places should be considered
    // equal for testing purposes and therefore we hide it from enumeration.
    Object.defineProperty(element, '_source', {
      configurable: false,
      enumerable: false,
      writable: false,
      value: source
    });
    if (Object.freeze) {
      Object.freeze(element.props);
      Object.freeze(element);
    }
  }

  return element;
};

/**
 * Create and return a new ReactElement of the given type.
 * See https://reactjs.org/docs/react-api.html#createelement
 */
function createElement(type, config, children) {
  var propName;

  // Reserved names are extracted
  var props = {};

  var key = null;
  var ref = null;
  var self = null;
  var source = null;

  if (config != null) {
    if (hasValidRef(config)) {
      ref = config.ref;
    }
    if (hasValidKey(config)) {
      key = '' + config.key;
    }

    self = config.__self === undefined ? null : config.__self;
    source = config.__source === undefined ? null : config.__source;
    // Remaining properties are added to a new props object
    for (propName in config) {
      if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
        props[propName] = config[propName];
      }
    }
  }

  // Children can be more than one argument, and those are transferred onto
  // the newly allocated props object.
  var childrenLength = arguments.length - 2;
  if (childrenLength === 1) {
    props.children = children;
  } else if (childrenLength > 1) {
    var childArray = Array(childrenLength);
    for (var i = 0; i < childrenLength; i++) {
      childArray[i] = arguments[i + 2];
    }
    {
      if (Object.freeze) {
        Object.freeze(childArray);
      }
    }
    props.children = childArray;
  }

  // Resolve default props
  if (type && type.defaultProps) {
    var defaultProps = type.defaultProps;
    for (propName in defaultProps) {
      if (props[propName] === undefined) {
        props[propName] = defaultProps[propName];
      }
    }
  }
  {
    if (key || ref) {
      if (typeof props.$$typeof === 'undefined' || props.$$typeof !== REACT_ELEMENT_TYPE$1) {
        var displayName = typeof type === 'function' ? type.displayName || type.name || 'Unknown' : type;
        if (key) {
          defineKeyPropWarningGetter(props, displayName);
        }
        if (ref) {
          defineRefPropWarningGetter(props, displayName);
        }
      }
    }
  }
  return ReactElement(type, key, ref, self, source, ReactCurrentOwner.current, props);
}

/**
 * Return a function that produces ReactElements of a given type.
 * See https://reactjs.org/docs/react-api.html#createfactory
 */


function cloneAndReplaceKey(oldElement, newKey) {
  var newElement = ReactElement(oldElement.type, newKey, oldElement.ref, oldElement._self, oldElement._source, oldElement._owner, oldElement.props);

  return newElement;
}

/**
 * Clone and return a new ReactElement using element as the starting point.
 * See https://reactjs.org/docs/react-api.html#cloneelement
 */
function cloneElement(element, config, children) {
  var propName;

  // Original props are copied
  var props = _assign({}, element.props);

  // Reserved names are extracted
  var key = element.key;
  var ref = element.ref;
  // Self is preserved since the owner is preserved.
  var self = element._self;
  // Source is preserved since cloneElement is unlikely to be targeted by a
  // transpiler, and the original source is probably a better indicator of the
  // true owner.
  var source = element._source;

  // Owner will be preserved, unless ref is overridden
  var owner = element._owner;

  if (config != null) {
    if (hasValidRef(config)) {
      // Silently steal the ref from the parent.
      ref = config.ref;
      owner = ReactCurrentOwner.current;
    }
    if (hasValidKey(config)) {
      key = '' + config.key;
    }

    // Remaining properties override existing props
    var defaultProps;
    if (element.type && element.type.defaultProps) {
      defaultProps = element.type.defaultProps;
    }
    for (propName in config) {
      if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
        if (config[propName] === undefined && defaultProps !== undefined) {
          // Resolve default props
          props[propName] = defaultProps[propName];
        } else {
          props[propName] = config[propName];
        }
      }
    }
  }

  // Children can be more than one argument, and those are transferred onto
  // the newly allocated props object.
  var childrenLength = arguments.length - 2;
  if (childrenLength === 1) {
    props.children = children;
  } else if (childrenLength > 1) {
    var childArray = Array(childrenLength);
    for (var i = 0; i < childrenLength; i++) {
      childArray[i] = arguments[i + 2];
    }
    props.children = childArray;
  }

  return ReactElement(element.type, key, ref, self, source, owner, props);
}

/**
 * Verifies the object is a ReactElement.
 * See https://reactjs.org/docs/react-api.html#isvalidelement
 * @param {?object} object
 * @return {boolean} True if `object` is a valid component.
 * @final
 */
function isValidElement(object) {
  return typeof object === 'object' && object !== null && object.$$typeof === REACT_ELEMENT_TYPE$1;
}

var ReactDebugCurrentFrame = {};

{
  // Component that is being worked on
  ReactDebugCurrentFrame.getCurrentStack = null;

  ReactDebugCurrentFrame.getStackAddendum = function () {
    var impl = ReactDebugCurrentFrame.getCurrentStack;
    if (impl) {
      return impl();
    }
    return null;
  };
}

var ITERATOR_SYMBOL = typeof Symbol === 'function' && Symbol.iterator;
var FAUX_ITERATOR_SYMBOL = '@@iterator'; // Before Symbol spec.
// The Symbol used to tag the ReactElement type. If there is no native Symbol
// nor polyfill, then a plain number is used for performance.
var REACT_ELEMENT_TYPE = typeof Symbol === 'function' && Symbol['for'] && Symbol['for']('react.element') || 0xeac7;
var REACT_PORTAL_TYPE = typeof Symbol === 'function' && Symbol['for'] && Symbol['for']('react.portal') || 0xeaca;
var SEPARATOR = '.';
var SUBSEPARATOR = ':';

/**
 * Escape and wrap key so it is safe to use as a reactid
 *
 * @param {string} key to be escaped.
 * @return {string} the escaped key.
 */
function escape(key) {
  var escapeRegex = /[=:]/g;
  var escaperLookup = {
    '=': '=0',
    ':': '=2'
  };
  var escapedString = ('' + key).replace(escapeRegex, function (match) {
    return escaperLookup[match];
  });

  return '$' + escapedString;
}

/**
 * TODO: Test that a single child and an array with one item have the same key
 * pattern.
 */

var didWarnAboutMaps = false;

var userProvidedKeyEscapeRegex = /\/+/g;
function escapeUserProvidedKey(text) {
  return ('' + text).replace(userProvidedKeyEscapeRegex, '$&/');
}

var POOL_SIZE = 10;
var traverseContextPool = [];
function getPooledTraverseContext(mapResult, keyPrefix, mapFunction, mapContext) {
  if (traverseContextPool.length) {
    var traverseContext = traverseContextPool.pop();
    traverseContext.result = mapResult;
    traverseContext.keyPrefix = keyPrefix;
    traverseContext.func = mapFunction;
    traverseContext.context = mapContext;
    traverseContext.count = 0;
    return traverseContext;
  } else {
    return {
      result: mapResult,
      keyPrefix: keyPrefix,
      func: mapFunction,
      context: mapContext,
      count: 0
    };
  }
}

function releaseTraverseContext(traverseContext) {
  traverseContext.result = null;
  traverseContext.keyPrefix = null;
  traverseContext.func = null;
  traverseContext.context = null;
  traverseContext.count = 0;
  if (traverseContextPool.length < POOL_SIZE) {
    traverseContextPool.push(traverseContext);
  }
}

/**
 * @param {?*} children Children tree container.
 * @param {!string} nameSoFar Name of the key path so far.
 * @param {!function} callback Callback to invoke with each child found.
 * @param {?*} traverseContext Used to pass information throughout the traversal
 * process.
 * @return {!number} The number of children in this subtree.
 */
function traverseAllChildrenImpl(children, nameSoFar, callback, traverseContext) {
  var type = typeof children;

  if (type === 'undefined' || type === 'boolean') {
    // All of the above are perceived as null.
    children = null;
  }

  if (children === null || type === 'string' || type === 'number' ||
  // The following is inlined from ReactElement. This means we can optimize
  // some checks. React Fiber also inlines this logic for similar purposes.
  type === 'object' && children.$$typeof === REACT_ELEMENT_TYPE || type === 'object' && children.$$typeof === REACT_PORTAL_TYPE) {
    callback(traverseContext, children,
    // If it's the only child, treat the name as if it was wrapped in an array
    // so that it's consistent if the number of children grows.
    nameSoFar === '' ? SEPARATOR + getComponentKey(children, 0) : nameSoFar);
    return 1;
  }

  var child;
  var nextName;
  var subtreeCount = 0; // Count of children found in the current subtree.
  var nextNamePrefix = nameSoFar === '' ? SEPARATOR : nameSoFar + SUBSEPARATOR;

  if (Array.isArray(children)) {
    for (var i = 0; i < children.length; i++) {
      child = children[i];
      nextName = nextNamePrefix + getComponentKey(child, i);
      subtreeCount += traverseAllChildrenImpl(child, nextName, callback, traverseContext);
    }
  } else {
    var iteratorFn = ITERATOR_SYMBOL && children[ITERATOR_SYMBOL] || children[FAUX_ITERATOR_SYMBOL];
    if (typeof iteratorFn === 'function') {
      {
        // Warn about using Maps as children
        if (iteratorFn === children.entries) {
          warning(didWarnAboutMaps, 'Using Maps as children is unsupported and will likely yield ' + 'unexpected results. Convert it to a sequence/iterable of keyed ' + 'ReactElements instead.%s', ReactDebugCurrentFrame.getStackAddendum());
          didWarnAboutMaps = true;
        }
      }

      var iterator = iteratorFn.call(children);
      var step;
      var ii = 0;
      while (!(step = iterator.next()).done) {
        child = step.value;
        nextName = nextNamePrefix + getComponentKey(child, ii++);
        subtreeCount += traverseAllChildrenImpl(child, nextName, callback, traverseContext);
      }
    } else if (type === 'object') {
      var addendum = '';
      {
        addendum = ' If you meant to render a collection of children, use an array ' + 'instead.' + ReactDebugCurrentFrame.getStackAddendum();
      }
      var childrenString = '' + children;
      invariant(false, 'Objects are not valid as a React child (found: %s).%s', childrenString === '[object Object]' ? 'object with keys {' + Object.keys(children).join(', ') + '}' : childrenString, addendum);
    }
  }

  return subtreeCount;
}

/**
 * Traverses children that are typically specified as `props.children`, but
 * might also be specified through attributes:
 *
 * - `traverseAllChildren(this.props.children, ...)`
 * - `traverseAllChildren(this.props.leftPanelChildren, ...)`
 *
 * The `traverseContext` is an optional argument that is passed through the
 * entire traversal. It can be used to store accumulations or anything else that
 * the callback might find relevant.
 *
 * @param {?*} children Children tree object.
 * @param {!function} callback To invoke upon traversing each child.
 * @param {?*} traverseContext Context for traversal.
 * @return {!number} The number of children in this subtree.
 */
function traverseAllChildren(children, callback, traverseContext) {
  if (children == null) {
    return 0;
  }

  return traverseAllChildrenImpl(children, '', callback, traverseContext);
}

/**
 * Generate a key string that identifies a component within a set.
 *
 * @param {*} component A component that could contain a manual key.
 * @param {number} index Index that is used if a manual key is not provided.
 * @return {string}
 */
function getComponentKey(component, index) {
  // Do some typechecking here since we call this blindly. We want to ensure
  // that we don't block potential future ES APIs.
  if (typeof component === 'object' && component !== null && component.key != null) {
    // Explicit key
    return escape(component.key);
  }
  // Implicit key determined by the index in the set
  return index.toString(36);
}

function forEachSingleChild(bookKeeping, child, name) {
  var func = bookKeeping.func,
      context = bookKeeping.context;

  func.call(context, child, bookKeeping.count++);
}

/**
 * Iterates through children that are typically specified as `props.children`.
 *
 * See https://reactjs.org/docs/react-api.html#react.children.foreach
 *
 * The provided forEachFunc(child, index) will be called for each
 * leaf child.
 *
 * @param {?*} children Children tree container.
 * @param {function(*, int)} forEachFunc
 * @param {*} forEachContext Context for forEachContext.
 */
function forEachChildren(children, forEachFunc, forEachContext) {
  if (children == null) {
    return children;
  }
  var traverseContext = getPooledTraverseContext(null, null, forEachFunc, forEachContext);
  traverseAllChildren(children, forEachSingleChild, traverseContext);
  releaseTraverseContext(traverseContext);
}

function mapSingleChildIntoContext(bookKeeping, child, childKey) {
  var result = bookKeeping.result,
      keyPrefix = bookKeeping.keyPrefix,
      func = bookKeeping.func,
      context = bookKeeping.context;


  var mappedChild = func.call(context, child, bookKeeping.count++);
  if (Array.isArray(mappedChild)) {
    mapIntoWithKeyPrefixInternal(mappedChild, result, childKey, emptyFunction.thatReturnsArgument);
  } else if (mappedChild != null) {
    if (isValidElement(mappedChild)) {
      mappedChild = cloneAndReplaceKey(mappedChild,
      // Keep both the (mapped) and old keys if they differ, just as
      // traverseAllChildren used to do for objects as children
      keyPrefix + (mappedChild.key && (!child || child.key !== mappedChild.key) ? escapeUserProvidedKey(mappedChild.key) + '/' : '') + childKey);
    }
    result.push(mappedChild);
  }
}

function mapIntoWithKeyPrefixInternal(children, array, prefix, func, context) {
  var escapedPrefix = '';
  if (prefix != null) {
    escapedPrefix = escapeUserProvidedKey(prefix) + '/';
  }
  var traverseContext = getPooledTraverseContext(array, escapedPrefix, func, context);
  traverseAllChildren(children, mapSingleChildIntoContext, traverseContext);
  releaseTraverseContext(traverseContext);
}

/**
 * Maps children that are typically specified as `props.children`.
 *
 * See https://reactjs.org/docs/react-api.html#react.children.map
 *
 * The provided mapFunction(child, key, index) will be called for each
 * leaf child.
 *
 * @param {?*} children Children tree container.
 * @param {function(*, int)} func The map function.
 * @param {*} context Context for mapFunction.
 * @return {object} Object containing the ordered map of results.
 */
function mapChildren(children, func, context) {
  if (children == null) {
    return children;
  }
  var result = [];
  mapIntoWithKeyPrefixInternal(children, result, null, func, context);
  return result;
}

/**
 * Count the number of children that are typically specified as
 * `props.children`.
 *
 * See https://reactjs.org/docs/react-api.html#react.children.count
 *
 * @param {?*} children Children tree container.
 * @return {number} The number of children.
 */
function countChildren(children, context) {
  return traverseAllChildren(children, emptyFunction.thatReturnsNull, null);
}

/**
 * Flatten a children object (typically specified as `props.children`) and
 * return an array with appropriately re-keyed children.
 *
 * See https://reactjs.org/docs/react-api.html#react.children.toarray
 */
function toArray(children) {
  var result = [];
  mapIntoWithKeyPrefixInternal(children, result, null, emptyFunction.thatReturnsArgument);
  return result;
}

/**
 * Returns the first child in a collection of children and verifies that there
 * is only one child in the collection.
 *
 * See https://reactjs.org/docs/react-api.html#react.children.only
 *
 * The current implementation of this function assumes that a single child gets
 * passed without a wrapper, but the purpose of this helper function is to
 * abstract away the particular structure of children.
 *
 * @param {?object} children Child collection structure.
 * @return {ReactElement} The first and only `ReactElement` contained in the
 * structure.
 */
function onlyChild(children) {
  !isValidElement(children) ? invariant(false, 'React.Children.only expected to receive a single React element child.') : void 0;
  return children;
}

var describeComponentFrame = function (name, source, ownerName) {
  return '\n    in ' + (name || 'Unknown') + (source ? ' (at ' + source.fileName.replace(/^.*[\\\/]/, '') + ':' + source.lineNumber + ')' : ownerName ? ' (created by ' + ownerName + ')' : '');
};

function getComponentName(fiber) {
  var type = fiber.type;

  if (typeof type === 'string') {
    return type;
  }
  if (typeof type === 'function') {
    return type.displayName || type.name;
  }
  return null;
}

/**
 * ReactElementValidator provides a wrapper around a element factory
 * which validates the props passed to the element. This is intended to be
 * used only in DEV and could be replaced by a static type checker for languages
 * that support it.
 */

{
  var currentlyValidatingElement = null;

  var getDisplayName = function (element) {
    if (element == null) {
      return '#empty';
    } else if (typeof element === 'string' || typeof element === 'number') {
      return '#text';
    } else if (typeof element.type === 'string') {
      return element.type;
    } else if (element.type === REACT_FRAGMENT_TYPE$1) {
      return 'React.Fragment';
    } else {
      return element.type.displayName || element.type.name || 'Unknown';
    }
  };

  var getStackAddendum = function () {
    var stack = '';
    if (currentlyValidatingElement) {
      var name = getDisplayName(currentlyValidatingElement);
      var owner = currentlyValidatingElement._owner;
      stack += describeComponentFrame(name, currentlyValidatingElement._source, owner && getComponentName(owner));
    }
    stack += ReactDebugCurrentFrame.getStackAddendum() || '';
    return stack;
  };

  var REACT_FRAGMENT_TYPE$1 = typeof Symbol === 'function' && Symbol['for'] && Symbol['for']('react.fragment') || 0xeacb;

  var VALID_FRAGMENT_PROPS = new Map([['children', true], ['key', true]]);
}

var ITERATOR_SYMBOL$1 = typeof Symbol === 'function' && Symbol.iterator;
var FAUX_ITERATOR_SYMBOL$1 = '@@iterator'; // Before Symbol spec.

function getDeclarationErrorAddendum() {
  if (ReactCurrentOwner.current) {
    var name = getComponentName(ReactCurrentOwner.current);
    if (name) {
      return '\n\nCheck the render method of `' + name + '`.';
    }
  }
  return '';
}

function getSourceInfoErrorAddendum(elementProps) {
  if (elementProps !== null && elementProps !== undefined && elementProps.__source !== undefined) {
    var source = elementProps.__source;
    var fileName = source.fileName.replace(/^.*[\\\/]/, '');
    var lineNumber = source.lineNumber;
    return '\n\nCheck your code at ' + fileName + ':' + lineNumber + '.';
  }
  return '';
}

/**
 * Warn if there's no key explicitly set on dynamic arrays of children or
 * object keys are not valid. This allows us to keep track of children between
 * updates.
 */
var ownerHasKeyUseWarning = {};

function getCurrentComponentErrorInfo(parentType) {
  var info = getDeclarationErrorAddendum();

  if (!info) {
    var parentName = typeof parentType === 'string' ? parentType : parentType.displayName || parentType.name;
    if (parentName) {
      info = '\n\nCheck the top-level render call using <' + parentName + '>.';
    }
  }
  return info;
}

/**
 * Warn if the element doesn't have an explicit key assigned to it.
 * This element is in an array. The array could grow and shrink or be
 * reordered. All children that haven't already been validated are required to
 * have a "key" property assigned to it. Error statuses are cached so a warning
 * will only be shown once.
 *
 * @internal
 * @param {ReactElement} element Element that requires a key.
 * @param {*} parentType element's parent's type.
 */
function validateExplicitKey(element, parentType) {
  if (!element._store || element._store.validated || element.key != null) {
    return;
  }
  element._store.validated = true;

  var currentComponentErrorInfo = getCurrentComponentErrorInfo(parentType);
  if (ownerHasKeyUseWarning[currentComponentErrorInfo]) {
    return;
  }
  ownerHasKeyUseWarning[currentComponentErrorInfo] = true;

  // Usually the current owner is the offender, but if it accepts children as a
  // property, it may be the creator of the child that's responsible for
  // assigning it a key.
  var childOwner = '';
  if (element && element._owner && element._owner !== ReactCurrentOwner.current) {
    // Give the component that originally created this child.
    childOwner = ' It was passed a child from ' + getComponentName(element._owner) + '.';
  }

  currentlyValidatingElement = element;
  {
    warning(false, 'Each child in an array or iterator should have a unique "key" prop.' + '%s%s See https://fb.me/react-warning-keys for more information.%s', currentComponentErrorInfo, childOwner, getStackAddendum());
  }
  currentlyValidatingElement = null;
}

/**
 * Ensure that every element either is passed in a static location, in an
 * array with an explicit keys property defined, or in an object literal
 * with valid key property.
 *
 * @internal
 * @param {ReactNode} node Statically passed child of any type.
 * @param {*} parentType node's parent's type.
 */
function validateChildKeys(node, parentType) {
  if (typeof node !== 'object') {
    return;
  }
  if (Array.isArray(node)) {
    for (var i = 0; i < node.length; i++) {
      var child = node[i];
      if (isValidElement(child)) {
        validateExplicitKey(child, parentType);
      }
    }
  } else if (isValidElement(node)) {
    // This element was passed in a valid location.
    if (node._store) {
      node._store.validated = true;
    }
  } else if (node) {
    var iteratorFn = ITERATOR_SYMBOL$1 && node[ITERATOR_SYMBOL$1] || node[FAUX_ITERATOR_SYMBOL$1];
    if (typeof iteratorFn === 'function') {
      // Entry iterators used to provide implicit keys,
      // but now we print a separate warning for them later.
      if (iteratorFn !== node.entries) {
        var iterator = iteratorFn.call(node);
        var step;
        while (!(step = iterator.next()).done) {
          if (isValidElement(step.value)) {
            validateExplicitKey(step.value, parentType);
          }
        }
      }
    }
  }
}

/**
 * Given an element, validate that its props follow the propTypes definition,
 * provided by the type.
 *
 * @param {ReactElement} element
 */
function validatePropTypes(element) {
  var componentClass = element.type;
  if (typeof componentClass !== 'function') {
    return;
  }
  var name = componentClass.displayName || componentClass.name;
  var propTypes = componentClass.propTypes;

  if (propTypes) {
    currentlyValidatingElement = element;
    checkPropTypes(propTypes, element.props, 'prop', name, getStackAddendum);
    currentlyValidatingElement = null;
  }
  if (typeof componentClass.getDefaultProps === 'function') {
    warning(componentClass.getDefaultProps.isReactClassApproved, 'getDefaultProps is only used on classic React.createClass ' + 'definitions. Use a static property named `defaultProps` instead.');
  }
}

/**
 * Given a fragment, validate that it can only be provided with fragment props
 * @param {ReactElement} fragment
 */
function validateFragmentProps(fragment) {
  currentlyValidatingElement = fragment;

  var _iteratorNormalCompletion = true;
  var _didIteratorError = false;
  var _iteratorError = undefined;

  try {
    for (var _iterator = Object.keys(fragment.props)[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
      var key = _step.value;

      if (!VALID_FRAGMENT_PROPS.has(key)) {
        warning(false, 'Invalid prop `%s` supplied to `React.Fragment`. ' + 'React.Fragment can only have `key` and `children` props.%s', key, getStackAddendum());
        break;
      }
    }
  } catch (err) {
    _didIteratorError = true;
    _iteratorError = err;
  } finally {
    try {
      if (!_iteratorNormalCompletion && _iterator['return']) {
        _iterator['return']();
      }
    } finally {
      if (_didIteratorError) {
        throw _iteratorError;
      }
    }
  }

  if (fragment.ref !== null) {
    warning(false, 'Invalid attribute `ref` supplied to `React.Fragment`.%s', getStackAddendum());
  }

  currentlyValidatingElement = null;
}

function createElementWithValidation(type, props, children) {
  var validType = typeof type === 'string' || typeof type === 'function' || typeof type === 'symbol' || typeof type === 'number';
  // We warn in this case but don't throw. We expect the element creation to
  // succeed and there will likely be errors in render.
  if (!validType) {
    var info = '';
    if (type === undefined || typeof type === 'object' && type !== null && Object.keys(type).length === 0) {
      info += ' You likely forgot to export your component from the file ' + "it's defined in.";
    }

    var sourceInfo = getSourceInfoErrorAddendum(props);
    if (sourceInfo) {
      info += sourceInfo;
    } else {
      info += getDeclarationErrorAddendum();
    }

    info += getStackAddendum() || '';

    warning(false, 'React.createElement: type is invalid -- expected a string (for ' + 'built-in components) or a class/function (for composite ' + 'components) but got: %s.%s', type == null ? type : typeof type, info);
  }

  var element = createElement.apply(this, arguments);

  // The result can be nullish if a mock or a custom function is used.
  // TODO: Drop this when these are no longer allowed as the type argument.
  if (element == null) {
    return element;
  }

  // Skip key warning if the type isn't valid since our key validation logic
  // doesn't expect a non-string/function type and can throw confusing errors.
  // We don't want exception behavior to differ between dev and prod.
  // (Rendering will throw with a helpful message and as soon as the type is
  // fixed, the key warnings will appear.)
  if (validType) {
    for (var i = 2; i < arguments.length; i++) {
      validateChildKeys(arguments[i], type);
    }
  }

  if (typeof type === 'symbol' && type === REACT_FRAGMENT_TYPE$1) {
    validateFragmentProps(element);
  } else {
    validatePropTypes(element);
  }

  return element;
}

function createFactoryWithValidation(type) {
  var validatedFactory = createElementWithValidation.bind(null, type);
  // Legacy hook TODO: Warn if this is accessed
  validatedFactory.type = type;

  {
    Object.defineProperty(validatedFactory, 'type', {
      enumerable: false,
      get: function () {
        lowPriorityWarning$1(false, 'Factory.type is deprecated. Access the class directly ' + 'before passing it to createFactory.');
        Object.defineProperty(this, 'type', {
          value: type
        });
        return type;
      }
    });
  }

  return validatedFactory;
}

function cloneElementWithValidation(element, props, children) {
  var newElement = cloneElement.apply(this, arguments);
  for (var i = 2; i < arguments.length; i++) {
    validateChildKeys(arguments[i], newElement.type);
  }
  validatePropTypes(newElement);
  return newElement;
}

var REACT_FRAGMENT_TYPE = typeof Symbol === 'function' && Symbol['for'] && Symbol['for']('react.fragment') || 0xeacb;

var React = {
  Children: {
    map: mapChildren,
    forEach: forEachChildren,
    count: countChildren,
    toArray: toArray,
    only: onlyChild
  },

  Component: Component,
  PureComponent: PureComponent,
  unstable_AsyncComponent: AsyncComponent,

  createElement: createElementWithValidation,
  cloneElement: cloneElementWithValidation,
  createFactory: createFactoryWithValidation,
  isValidElement: isValidElement,

  version: ReactVersion,

  __SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED: {
    ReactCurrentOwner: ReactCurrentOwner,
    // Used by renderers to avoid bundling object-assign twice in UMD bundles:
    assign: _assign
  }
};

if (enableReactFragment) {
  React.Fragment = REACT_FRAGMENT_TYPE;
}

{
  _assign(React.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, {
    // These should not be included in production.
    ReactDebugCurrentFrame: ReactDebugCurrentFrame,
    // Shim for React DOM 16.0.0 which still destructured (but not used) this.
    // TODO: remove in React 17.0.
    ReactComponentTreeHook: {}
  });
}



var React$2 = Object.freeze({
	default: React
});

var React$3 = ( React$2 && React ) || React$2;

// TODO: decide on the top-level export form.
// This is hacky but makes it work with both Rollup and Jest.
var react = React$3['default'] ? React$3['default'] : React$3;

module.exports = react;
  })();
}


/***/ }),

/***/ "./node_modules/react/index.js":
/***/ (function(module, exports, __webpack_require__) {

"use strict";


if (false) {
  module.exports = require('./cjs/react.production.min.js');
} else {
  module.exports = __webpack_require__("./node_modules/react/cjs/react.development.js");
}


/***/ }),

/***/ "./node_modules/webpack/buildin/amd-define.js":
/***/ (function(module, exports) {

module.exports = function() {
	throw new Error("define cannot be used indirect");
};


/***/ }),

/***/ "./node_modules/webpack/buildin/global.js":
/***/ (function(module, exports) {

var g;

// This works in non-strict mode
g = (function() {
	return this;
})();

try {
	// This works if eval is allowed (see CSP)
	g = g || Function("return this")() || (1,eval)("this");
} catch(e) {
	// This works if the window reference is available
	if(typeof window === "object")
		g = window;
}

// g can still be undefined, but nothing to do about it...
// We return undefined, instead of nothing here, so it's
// easier to handle this case. if(!global) { ...}

module.exports = g;


/***/ }),

/***/ "./node_modules/webpack/buildin/module.js":
/***/ (function(module, exports) {

module.exports = function(module) {
	if(!module.webpackPolyfill) {
		module.deprecate = function() {};
		module.paths = [];
		// module.parent = undefined by default
		if(!module.children) module.children = [];
		Object.defineProperty(module, "loaded", {
			enumerable: true,
			get: function() {
				return module.l;
			}
		});
		Object.defineProperty(module, "id", {
			enumerable: true,
			get: function() {
				return module.i;
			}
		});
		module.webpackPolyfill = 1;
	}
	return module;
};


/***/ }),

/***/ 0:
/***/ (function(module, exports) {

(function() { module.exports = window["jQuery"]; }());

/***/ }),

/***/ 1:
/***/ (function(module, exports) {

(function() { module.exports = window["_"]; }());

/***/ }),

/***/ 2:
/***/ (function(module, exports) {

(function() { module.exports = window["Backbone"]; }());

/***/ })

/******/ })));
//# sourceMappingURL=commons.js.map