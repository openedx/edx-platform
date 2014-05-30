/*
** Annotator 1.2.6-dev-dc18206
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-05-16 18:01:57Z
*/


(function() {
  var $, Annotator, Delegator, LinkParser, Range, findChild, fn, functions, g, getNodeName, getNodePosition, gettext, simpleXPathJQuery, simpleXPathPure, util, _Annotator, _gettext, _i, _j, _len, _len1, _ref, _ref1, _t,
    __slice = [].slice,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  simpleXPathJQuery = function(relativeRoot) {
    var jq;

    jq = this.map(function() {
      var elem, idx, path, tagName;

      path = '';
      elem = this;
      while (elem && elem.nodeType === 1 && elem !== relativeRoot) {
        tagName = elem.tagName.replace(":", "\\:");
        idx = $(elem.parentNode).children(tagName).index(elem) + 1;
        idx = "[" + idx + "]";
        path = "/" + elem.tagName.toLowerCase() + idx + path;
        elem = elem.parentNode;
      }
      return path;
    });
    return jq.get();
  };

  simpleXPathPure = function(relativeRoot) {
    var getPathSegment, getPathTo, jq, rootNode;

    getPathSegment = function(node) {
      var name, pos;

      name = getNodeName(node);
      pos = getNodePosition(node);
      return "" + name + "[" + pos + "]";
    };
    rootNode = relativeRoot;
    getPathTo = function(node) {
      var xpath;

      xpath = '';
      while (node !== rootNode) {
        if (node == null) {
          throw new Error("Called getPathTo on a node which was not a descendant of @rootNode. " + rootNode);
        }
        xpath = (getPathSegment(node)) + '/' + xpath;
        node = node.parentNode;
      }
      xpath = '/' + xpath;
      xpath = xpath.replace(/\/$/, '');
      return xpath;
    };
    jq = this.map(function() {
      var path;

      path = getPathTo(this);
      return path;
    });
    return jq.get();
  };

  findChild = function(node, type, index) {
    var child, children, found, name, _i, _len;

    if (!node.hasChildNodes()) {
      throw new Error("XPath error: node has no children!");
    }
    children = node.childNodes;
    found = 0;
    for (_i = 0, _len = children.length; _i < _len; _i++) {
      child = children[_i];
      name = getNodeName(child);
      if (name === type) {
        found += 1;
        if (found === index) {
          return child;
        }
      }
    }
    throw new Error("XPath error: wanted child not found.");
  };

  getNodeName = function(node) {
    var nodeName;

    nodeName = node.nodeName.toLowerCase();
    switch (nodeName) {
      case "#text":
        return "text()";
      case "#comment":
        return "comment()";
      case "#cdata-section":
        return "cdata-section()";
      default:
        return nodeName;
    }
  };

  getNodePosition = function(node) {
    var pos, tmp;

    pos = 0;
    tmp = node;
    while (tmp) {
      if (tmp.nodeName === node.nodeName) {
        pos++;
      }
      tmp = tmp.previousSibling;
    }
    return pos;
  };

  gettext = null;

  if (typeof Gettext !== "undefined" && Gettext !== null) {
    _gettext = new Gettext({
      domain: "annotator"
    });
    gettext = function(msgid) {
      return _gettext.gettext(msgid);
    };
  } else {
    gettext = function(msgid) {
      return msgid;
    };
  }

  _t = function(msgid) {
    return gettext(msgid);
  };

  if (!(typeof jQuery !== "undefined" && jQuery !== null ? (_ref = jQuery.fn) != null ? _ref.jquery : void 0 : void 0)) {
    console.error(_t("Annotator requires jQuery: have you included lib/vendor/jquery.js?"));
  }

  if (!(JSON && JSON.parse && JSON.stringify)) {
    console.error(_t("Annotator requires a JSON implementation: have you included lib/vendor/json2.js?"));
  }

  $ = jQuery.sub();

  $.flatten = function(array) {
    var flatten;

    flatten = function(ary) {
      var el, flat, _i, _len;

      flat = [];
      for (_i = 0, _len = ary.length; _i < _len; _i++) {
        el = ary[_i];
        flat = flat.concat(el && $.isArray(el) ? flatten(el) : el);
      }
      return flat;
    };
    return flatten(array);
  };

  $.plugin = function(name, object) {
    return jQuery.fn[name] = function(options) {
      var args;

      args = Array.prototype.slice.call(arguments, 1);
      return this.each(function() {
        var instance;

        instance = $.data(this, name);
        if (instance) {
          return options && instance[options].apply(instance, args);
        } else {
          instance = new object(this, options);
          return $.data(this, name, instance);
        }
      });
    };
  };

  $.fn.textNodes = function() {
    var getTextNodes;

    getTextNodes = function(node) {
      var nodes;

      if (node && node.nodeType !== 3) {
        nodes = [];
        if (node.nodeType !== 8) {
          node = node.lastChild;
          while (node) {
            nodes.push(getTextNodes(node));
            node = node.previousSibling;
          }
        }
        return nodes.reverse();
      } else {
        return node;
      }
    };
    return this.map(function() {
      return $.flatten(getTextNodes(this));
    });
  };

  $.fn.xpath = function(relativeRoot) {
    var exception, result;

    try {
      result = simpleXPathJQuery.call(this, relativeRoot);
    } catch (_error) {
      exception = _error;
      console.log("jQuery-based XPath construction failed! Falling back to manual.");
      result = simpleXPathPure.call(this, relativeRoot);
    }
    return result;
  };

  $.xpath = function(xp, root) {
    var idx, name, node, step, steps, _i, _len, _ref1;

    steps = xp.substring(1).split("/");
    node = root;
    for (_i = 0, _len = steps.length; _i < _len; _i++) {
      step = steps[_i];
      _ref1 = step.split("["), name = _ref1[0], idx = _ref1[1];
      idx = idx != null ? parseInt((idx != null ? idx.split("]") : void 0)[0]) : 1;
      node = findChild(node, name.toLowerCase(), idx);
    }
    return node;
  };

  $.escape = function(html) {
    return html.replace(/&(?!\w+;)/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  };

  $.fn.escape = function(html) {
    if (arguments.length) {
      return this.html($.escape(html));
    }
    return this.html();
  };

  $.fn.reverse = []._reverse || [].reverse;

  functions = ["log", "debug", "info", "warn", "exception", "assert", "dir", "dirxml", "trace", "group", "groupEnd", "groupCollapsed", "time", "timeEnd", "profile", "profileEnd", "count", "clear", "table", "error", "notifyFirebug", "firebug", "userObjects"];

  if (typeof console !== "undefined" && console !== null) {
    if (console.group == null) {
      console.group = function(name) {
        return console.log("GROUP: ", name);
      };
    }
    if (console.groupCollapsed == null) {
      console.groupCollapsed = console.group;
    }
    for (_i = 0, _len = functions.length; _i < _len; _i++) {
      fn = functions[_i];
      if (console[fn] == null) {
        console[fn] = function() {
          return console.log(_t("Not implemented:") + (" console." + name));
        };
      }
    }
  } else {
    this.console = {};
    for (_j = 0, _len1 = functions.length; _j < _len1; _j++) {
      fn = functions[_j];
      this.console[fn] = function() {};
    }
    this.console['error'] = function() {
      var args;

      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      return alert("ERROR: " + (args.join(', ')));
    };
    this.console['warn'] = function() {
      var args;

      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      return alert("WARNING: " + (args.join(', ')));
    };
  }

  Delegator = (function() {
    Delegator.prototype.events = {};

    Delegator.prototype.options = {};

    Delegator.prototype.element = null;

    function Delegator(element, options) {
      this.options = $.extend(true, {}, this.options, options);
      this.element = $(element);
      this.on = this.subscribe;
      this.addEvents();
    }

    Delegator.prototype.addEvents = function() {
      var event, functionName, sel, selector, _k, _ref1, _ref2, _results;

      _ref1 = this.events;
      _results = [];
      for (sel in _ref1) {
        functionName = _ref1[sel];
        _ref2 = sel.split(' '), selector = 2 <= _ref2.length ? __slice.call(_ref2, 0, _k = _ref2.length - 1) : (_k = 0, []), event = _ref2[_k++];
        _results.push(this.addEvent(selector.join(' '), event, functionName));
      }
      return _results;
    };

    Delegator.prototype.addEvent = function(bindTo, event, functionName) {
      var closure, isBlankSelector,
        _this = this;

      closure = function() {
        return _this[functionName].apply(_this, arguments);
      };
      isBlankSelector = typeof bindTo === 'string' && bindTo.replace(/\s+/g, '') === '';
      if (isBlankSelector) {
        bindTo = this.element;
      }
      if (typeof bindTo === 'string') {
        this.element.delegate(bindTo, event, closure);
      } else {
        if (this.isCustomEvent(event)) {
          this.subscribe(event, closure);
        } else {
          $(bindTo).bind(event, closure);
        }
      }
      return this;
    };

    Delegator.prototype.isCustomEvent = function(event) {
      event = event.split('.')[0];
      return $.inArray(event, Delegator.natives) === -1;
    };

    Delegator.prototype.publish = function() {
      this.element.triggerHandler.apply(this.element, arguments);
      return this;
    };

    Delegator.prototype.subscribe = function(event, callback) {
      var closure;

      closure = function() {
        return callback.apply(this, [].slice.call(arguments, 1));
      };
      closure.guid = callback.guid = ($.guid += 1);
      this.element.bind(event, closure);
      return this;
    };

    Delegator.prototype.unsubscribe = function() {
      this.element.unbind.apply(this.element, arguments);
      return this;
    };

    return Delegator;

  })();

  Delegator.natives = (function() {
    var key, specials, val;

    specials = (function() {
      var _ref1, _results;

      _ref1 = jQuery.event.special;
      _results = [];
      for (key in _ref1) {
        if (!__hasProp.call(_ref1, key)) continue;
        val = _ref1[key];
        _results.push(key);
      }
      return _results;
    })();
    return "blur focus focusin focusout load resize scroll unload click dblclick\nmousedown mouseup mousemove mouseover mouseout mouseenter mouseleave\nchange select submit keydown keypress keyup error".split(/[^a-z]+/).concat(specials);
  })();

  Range = {};

  Range.sniff = function(r) {
    if (r.commonAncestorContainer != null) {
      return new Range.BrowserRange(r);
    } else if (typeof r.start === "string") {
      return new Range.SerializedRange(r);
    } else if (r.start && typeof r.start === "object") {
      return new Range.NormalizedRange(r);
    } else {
      console.error(_t("Could not sniff range type"));
      return false;
    }
  };

  Range.nodeFromXPath = function(xpath, root) {
    var customResolver, evaluateXPath, namespace, node, segment;

    if (root == null) {
      root = document;
    }
    evaluateXPath = function(xp, nsResolver) {
      var exception;

      if (nsResolver == null) {
        nsResolver = null;
      }
      try {
        return document.evaluate('.' + xp, root, nsResolver, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
      } catch (_error) {
        exception = _error;
        console.log("XPath evaluation failed.");
        console.log("Trying fallback...");
        return $.xpath(xp, root);
      }
    };
    if (!$.isXMLDoc(document.documentElement)) {
      return evaluateXPath(xpath);
    } else {
      customResolver = document.createNSResolver(document.ownerDocument === null ? document.documentElement : document.ownerDocument.documentElement);
      node = evaluateXPath(xpath, customResolver);
      if (!node) {
        xpath = ((function() {
          var _k, _len2, _ref1, _results;

          _ref1 = xpath.split('/');
          _results = [];
          for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
            segment = _ref1[_k];
            if (segment && segment.indexOf(':') === -1) {
              _results.push(segment.replace(/^([a-z]+)/, 'xhtml:$1'));
            } else {
              _results.push(segment);
            }
          }
          return _results;
        })()).join('/');
        namespace = document.lookupNamespaceURI(null);
        customResolver = function(ns) {
          if (ns === 'xhtml') {
            return namespace;
          } else {
            return document.documentElement.getAttribute('xmlns:' + ns);
          }
        };
        node = evaluateXPath(xpath, customResolver);
      }
      return node;
    }
  };

  Range.RangeError = (function(_super) {
    __extends(RangeError, _super);

    function RangeError(type, message, parent) {
      this.type = type;
      this.message = message;
      this.parent = parent != null ? parent : null;
      RangeError.__super__.constructor.call(this, this.message);
    }

    return RangeError;

  })(Error);

  Range.BrowserRange = (function() {
    function BrowserRange(obj) {
      this.commonAncestorContainer = obj.commonAncestorContainer;
      this.startContainer = obj.startContainer;
      this.startOffset = obj.startOffset;
      this.endContainer = obj.endContainer;
      this.endOffset = obj.endOffset;
    }

    BrowserRange.prototype.normalize = function(root) {
      var it, node, nr, offset, p, r, _k, _len2, _ref1;

      if (this.tainted) {
        console.error(_t("You may only call normalize() once on a BrowserRange!"));
        return false;
      } else {
        this.tainted = true;
      }
      r = {};
      nr = {};
      _ref1 = ['start', 'end'];
      for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
        p = _ref1[_k];
        node = this[p + 'Container'];
        offset = this[p + 'Offset'];
        if (node.nodeType === 1) {
          it = node.childNodes[offset];
          node = it || node.childNodes[offset - 1];
          if (node.nodeType === 1 && !node.firstChild) {
            it = null;
            node = node.previousSibling;
          }
          while (node.nodeType !== 3) {
            node = node.firstChild;
          }
          offset = it ? 0 : node.nodeValue.length;
        }
        r[p] = node;
        r[p + 'Offset'] = offset;
      }
      nr.start = r.startOffset > 0 ? r.start.splitText(r.startOffset) : r.start;
      if (r.start === r.end) {
        if ((r.endOffset - r.startOffset) < nr.start.nodeValue.length) {
          nr.start.splitText(r.endOffset - r.startOffset);
        }
        nr.end = nr.start;
      } else {
        if (r.endOffset < r.end.nodeValue.length) {
          r.end.splitText(r.endOffset);
        }
        nr.end = r.end;
      }
      nr.commonAncestor = this.commonAncestorContainer;
      while (nr.commonAncestor.nodeType !== 1) {
        nr.commonAncestor = nr.commonAncestor.parentNode;
      }
      return new Range.NormalizedRange(nr);
    };

    BrowserRange.prototype.serialize = function(root, ignoreSelector) {
      return this.normalize(root).serialize(root, ignoreSelector);
    };

    return BrowserRange;

  })();

  Range.NormalizedRange = (function() {
    function NormalizedRange(obj) {
      this.commonAncestor = obj.commonAncestor;
      this.start = obj.start;
      this.end = obj.end;
    }

    NormalizedRange.prototype.normalize = function(root) {
      return this;
    };

    NormalizedRange.prototype.limit = function(bounds) {
      var nodes, parent, startParents, _k, _len2, _ref1;

      nodes = $.grep(this.textNodes(), function(node) {
        return node.parentNode === bounds || $.contains(bounds, node.parentNode);
      });
      if (!nodes.length) {
        return null;
      }
      this.start = nodes[0];
      this.end = nodes[nodes.length - 1];
      startParents = $(this.start).parents();
      _ref1 = $(this.end).parents();
      for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
        parent = _ref1[_k];
        if (startParents.index(parent) !== -1) {
          this.commonAncestor = parent;
          break;
        }
      }
      return this;
    };

    NormalizedRange.prototype.serialize = function(root, ignoreSelector) {
      var end, serialization, start;

      serialization = function(node, isEnd) {
        var n, nodes, offset, origParent, textNodes, xpath, _k, _len2;

        if (ignoreSelector) {
          origParent = $(node).parents(":not(" + ignoreSelector + ")").eq(0);
        } else {
          origParent = $(node).parent();
        }
        xpath = origParent.xpath(root)[0];
        textNodes = origParent.textNodes();
        nodes = textNodes.slice(0, textNodes.index(node));
        offset = 0;
        for (_k = 0, _len2 = nodes.length; _k < _len2; _k++) {
          n = nodes[_k];
          offset += n.nodeValue.length;
        }
        if (isEnd) {
          return [xpath, offset + node.nodeValue.length];
        } else {
          return [xpath, offset];
        }
      };
      start = serialization(this.start);
      end = serialization(this.end, true);
      return new Range.SerializedRange({
        start: start[0],
        end: end[0],
        startOffset: start[1],
        endOffset: end[1]
      });
    };

    NormalizedRange.prototype.text = function() {
      var node;

      return ((function() {
        var _k, _len2, _ref1, _results;

        _ref1 = this.textNodes();
        _results = [];
        for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
          node = _ref1[_k];
          _results.push(node.nodeValue);
        }
        return _results;
      }).call(this)).join('');
    };

    NormalizedRange.prototype.textNodes = function() {
      var end, start, textNodes, _ref1;

      textNodes = $(this.commonAncestor).textNodes();
      _ref1 = [textNodes.index(this.start), textNodes.index(this.end)], start = _ref1[0], end = _ref1[1];
      return $.makeArray(textNodes.slice(start, +end + 1 || 9e9));
    };

    NormalizedRange.prototype.toRange = function() {
      var range;

      range = document.createRange();
      range.setStartBefore(this.start);
      range.setEndAfter(this.end);
      return range;
    };

    return NormalizedRange;

  })();

  Range.SerializedRange = (function() {
    function SerializedRange(obj) {
      this.start = obj.start;
      this.startOffset = obj.startOffset;
      this.end = obj.end;
      this.endOffset = obj.endOffset;
    }

    SerializedRange.prototype.normalize = function(root) {
      var contains, e, length, node, p, range, tn, _k, _l, _len2, _len3, _ref1, _ref2;

      range = {};
      _ref1 = ['start', 'end'];
      for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
        p = _ref1[_k];
        try {
          node = Range.nodeFromXPath(this[p], root);
        } catch (_error) {
          e = _error;
          throw new Range.RangeError(p, ("Error while finding " + p + " node: " + this[p] + ": ") + e, e);
        }
        if (!node) {
          throw new Range.RangeError(p, "Couldn't find " + p + " node: " + this[p]);
        }
        length = 0;
        _ref2 = $(node).textNodes();
        for (_l = 0, _len3 = _ref2.length; _l < _len3; _l++) {
          tn = _ref2[_l];
          if (length + tn.nodeValue.length >= this[p + 'Offset']) {
            range[p + 'Container'] = tn;
            range[p + 'Offset'] = this[p + 'Offset'] - length;
            break;
          } else {
            length += tn.nodeValue.length;
          }
        }
        if (range[p + 'Offset'] == null) {
          throw new Range.RangeError("" + p + "offset", "Couldn't find offset " + this[p + 'Offset'] + " in element " + this[p]);
        }
      }
      contains = document.compareDocumentPosition == null ? function(a, b) {
        return a.contains(b);
      } : function(a, b) {
        return a.compareDocumentPosition(b) & 16;
      };
      $(range.startContainer).parents().each(function() {
        if (contains(this, range.endContainer)) {
          range.commonAncestorContainer = this;
          return false;
        }
      });
      return new Range.BrowserRange(range).normalize(root);
    };

    SerializedRange.prototype.serialize = function(root, ignoreSelector) {
      return this.normalize(root).serialize(root, ignoreSelector);
    };

    SerializedRange.prototype.toObject = function() {
      return {
        start: this.start,
        startOffset: this.startOffset,
        end: this.end,
        endOffset: this.endOffset
      };
    };

    return SerializedRange;

  })();

  util = {
    uuid: (function() {
      var counter;

      counter = 0;
      return function() {
        return counter++;
      };
    })(),
    getGlobal: function() {
      return (function() {
        return this;
      })();
    },
    maxZIndex: function($elements) {
      var all, el;

      all = (function() {
        var _k, _len2, _results;

        _results = [];
        for (_k = 0, _len2 = $elements.length; _k < _len2; _k++) {
          el = $elements[_k];
          if ($(el).css('position') === 'static') {
            _results.push(-1);
          } else {
            _results.push(parseInt($(el).css('z-index'), 10) || -1);
          }
        }
        return _results;
      })();
      return Math.max.apply(Math, all);
    },
    mousePosition: function(e, offsetEl) {
      var offset;

      offset = $(offsetEl).position();
      return {
        top: e.pageY - offset.top,
        left: e.pageX - offset.left
      };
    },
    preventEventDefault: function(event) {
      return event != null ? typeof event.preventDefault === "function" ? event.preventDefault() : void 0 : void 0;
    }
  };

  _Annotator = this.Annotator;

  Annotator = (function(_super) {
    __extends(Annotator, _super);

    Annotator.prototype.events = {
      ".annotator-adder button click": "onAdderClick",
      ".annotator-adder button mousedown": "onAdderMousedown",
      ".annotator-hl mouseover": "onHighlightMouseover",
      ".annotator-hl mouseout": "startViewerHideTimer"
    };

    Annotator.prototype.html = {
      adder: '<div class="annotator-adder"><button>' + _t('Annotate') + '</button></div>',
      wrapper: '<div class="annotator-wrapper"></div>'
    };

    Annotator.prototype.options = {
      readOnly: false
    };

    Annotator.prototype.plugins = {};

    Annotator.prototype.editor = null;

    Annotator.prototype.viewer = null;

    Annotator.prototype.selectedRanges = null;

    Annotator.prototype.mouseIsDown = false;

    Annotator.prototype.ignoreMouseup = false;

    Annotator.prototype.viewerHideTimer = null;

    function Annotator(element, options) {
      this.onDeleteAnnotation = __bind(this.onDeleteAnnotation, this);
      this.onEditAnnotation = __bind(this.onEditAnnotation, this);
      this.onAdderClick = __bind(this.onAdderClick, this);
      this.onAdderMousedown = __bind(this.onAdderMousedown, this);
      this.onHighlightMouseover = __bind(this.onHighlightMouseover, this);
      this.checkForEndSelection = __bind(this.checkForEndSelection, this);
      this.checkForStartSelection = __bind(this.checkForStartSelection, this);
      this.clearViewerHideTimer = __bind(this.clearViewerHideTimer, this);
      this.startViewerHideTimer = __bind(this.startViewerHideTimer, this);
      this.showViewer = __bind(this.showViewer, this);
      this.onEditorSubmit = __bind(this.onEditorSubmit, this);
      this.onEditorHide = __bind(this.onEditorHide, this);
      this.showEditor = __bind(this.showEditor, this);      Annotator.__super__.constructor.apply(this, arguments);
      this.plugins = {};
      if (!Annotator.supported()) {
        return this;
      }
      if (!this.options.readOnly) {
        this._setupDocumentEvents();
      }
      this._setupWrapper()._setupViewer()._setupEditor();
      this._setupDynamicStyle();
      this.adder = $(this.html.adder).appendTo(this.wrapper).hide();
    }

    Annotator.prototype._setupWrapper = function() {
      this.wrapper = $(this.html.wrapper);
      this.element.find('script').remove();
      this.element.wrapInner(this.wrapper);
      this.wrapper = this.element.find('.annotator-wrapper');
      return this;
    };

    Annotator.prototype._setupViewer = function() {
      var _this = this;

      this.viewer = new Annotator.Viewer({
        readOnly: this.options.readOnly
      });
      this.viewer.hide().on("edit", this.onEditAnnotation).on("delete", this.onDeleteAnnotation).addField({
        load: function(field, annotation) {
          if (annotation.text) {
            $(field).escape(annotation.text);
          } else {
            $(field).html("<i>" + (_t('No Comment')) + "</i>");
          }
          return _this.publish('annotationViewerTextField', [field, annotation]);
        }
      }).element.appendTo(this.wrapper).bind({
        "mouseover": this.clearViewerHideTimer,
        "mouseout": this.startViewerHideTimer
      });
      return this;
    };

    Annotator.prototype._setupEditor = function() {
      this.editor = new Annotator.Editor();
      this.editor.hide().on('hide', this.onEditorHide).on('save', this.onEditorSubmit).addField({
        type: 'textarea',
        label: _t('Comments') + '\u2026',
        load: function(field, annotation) {
          return $(field).find('textarea').val(annotation.text || '');
        },
        submit: function(field, annotation) {
          return annotation.text = $(field).find('textarea').val();
        }
      });
      this.editor.element.appendTo(this.wrapper);
      return this;
    };

    Annotator.prototype._setupDocumentEvents = function() {
      $(document).bind({
        "mouseup": this.checkForEndSelection,
        "mousedown": this.checkForStartSelection
      });
      return this;
    };

    Annotator.prototype._setupDynamicStyle = function() {
      var max, sel, style, x;

      style = $('#annotator-dynamic-style');
      if (!style.length) {
        style = $('<style id="annotator-dynamic-style"></style>').appendTo(document.head);
      }
      sel = '*' + ((function() {
        var _k, _len2, _ref1, _results;

        _ref1 = ['adder', 'outer', 'notice', 'filter'];
        _results = [];
        for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
          x = _ref1[_k];
          _results.push(":not(.annotator-" + x + ")");
        }
        return _results;
      })()).join('');
      max = util.maxZIndex($(document.body).find(sel));
      max = Math.max(max, 1000);
      style.text([".annotator-adder, .annotator-outer, .annotator-notice {", "  z-index: " + (max + 20) + ";", "}", ".annotator-filter {", "  z-index: " + (max + 10) + ";", "}"].join("\n"));
      return this;
    };

    Annotator.prototype.getSelectedRanges = function() {
      var browserRange, i, normedRange, r, ranges, rangesToIgnore, selection, _k, _len2;

      selection = util.getGlobal().getSelection();
      ranges = [];
      rangesToIgnore = [];
      if (!selection.isCollapsed) {
        ranges = (function() {
          var _k, _ref1, _results;

          _results = [];
          for (i = _k = 0, _ref1 = selection.rangeCount; 0 <= _ref1 ? _k < _ref1 : _k > _ref1; i = 0 <= _ref1 ? ++_k : --_k) {
            r = selection.getRangeAt(i);
            browserRange = new Range.BrowserRange(r);
            normedRange = browserRange.normalize().limit(this.wrapper[0]);
            if (normedRange === null) {
              rangesToIgnore.push(r);
            }
            _results.push(normedRange);
          }
          return _results;
        }).call(this);
        selection.removeAllRanges();
      }
      for (_k = 0, _len2 = rangesToIgnore.length; _k < _len2; _k++) {
        r = rangesToIgnore[_k];
        selection.addRange(r);
      }
      return $.grep(ranges, function(range) {
        if (range) {
          selection.addRange(range.toRange());
        }
        return range;
      });
    };

    Annotator.prototype.createAnnotation = function() {
      var annotation;

      annotation = {};
      this.publish('beforeAnnotationCreated', [annotation]);
      return annotation;
    };

    Annotator.prototype.setupAnnotation = function(annotation) {
      var e, normed, normedRanges, r, root, _k, _l, _len2, _len3, _ref1;

      root = this.wrapper[0];
      annotation.ranges || (annotation.ranges = this.selectedRanges);
      normedRanges = [];
      _ref1 = annotation.ranges;
      for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
        r = _ref1[_k];
        try {
          normedRanges.push(Range.sniff(r).normalize(root));
        } catch (_error) {
          e = _error;
          if (e instanceof Range.RangeError) {
            this.publish('rangeNormalizeFail', [annotation, r, e]);
          } else {
            throw e;
          }
        }
      }
      annotation.quote = [];
      annotation.ranges = [];
      annotation.highlights = [];
      for (_l = 0, _len3 = normedRanges.length; _l < _len3; _l++) {
        normed = normedRanges[_l];
        annotation.quote.push($.trim(normed.text()));
        annotation.ranges.push(normed.serialize(this.wrapper[0], '.annotator-hl'));
        $.merge(annotation.highlights, this.highlightRange(normed));
      }
      annotation.quote = annotation.quote.join(' / ');
      $(annotation.highlights).data('annotation', annotation);
      return annotation;
    };

    Annotator.prototype.updateAnnotation = function(annotation) {
      this.publish('beforeAnnotationUpdated', [annotation]);
      this.publish('annotationUpdated', [annotation]);
      return annotation;
    };

    Annotator.prototype.deleteAnnotation = function(annotation) {
      var child, h, _k, _len2, _ref1;

      if (annotation.highlights != null) {
        _ref1 = annotation.highlights;
        for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
          h = _ref1[_k];
          if (!(h.parentNode != null)) {
            continue;
          }
          child = h.childNodes[0];
          $(h).replaceWith(h.childNodes);
        }
      }
      this.publish('annotationDeleted', [annotation]);
      return annotation;
    };

    Annotator.prototype.loadAnnotations = function(annotations) {
      var clone, loader,
        _this = this;

      if (annotations == null) {
        annotations = [];
      }
      loader = function(annList) {
        var n, now, _k, _len2;

        if (annList == null) {
          annList = [];
        }
        now = annList.splice(0, 10);
        for (_k = 0, _len2 = now.length; _k < _len2; _k++) {
          n = now[_k];
          _this.setupAnnotation(n);
        }
        if (annList.length > 0) {
          return setTimeout((function() {
            return loader(annList);
          }), 10);
        } else {
          return _this.publish('annotationsLoaded', [clone]);
        }
      };
      clone = annotations.slice();
      if (annotations.length) {
        loader(annotations);
      }
      return this;
    };

    Annotator.prototype.dumpAnnotations = function() {
      if (this.plugins['Store']) {
        return this.plugins['Store'].dumpAnnotations();
      } else {
        console.warn(_t("Can't dump annotations without Store plugin."));
        return false;
      }
    };

    Annotator.prototype.highlightRange = function(normedRange, cssClass) {
      var hl, node, white, _k, _len2, _ref1, _results;

      if (cssClass == null) {
        cssClass = 'annotator-hl';
      }
      white = /^\s*$/;
      hl = $("<span class='" + cssClass + "'></span>");
      _ref1 = normedRange.textNodes();
      _results = [];
      for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
        node = _ref1[_k];
        if (!white.test(node.nodeValue)) {
          _results.push($(node).wrapAll(hl).parent().show()[0]);
        }
      }
      return _results;
    };

    Annotator.prototype.highlightRanges = function(normedRanges, cssClass) {
      var highlights, r, _k, _len2;

      if (cssClass == null) {
        cssClass = 'annotator-hl';
      }
      highlights = [];
      for (_k = 0, _len2 = normedRanges.length; _k < _len2; _k++) {
        r = normedRanges[_k];
        $.merge(highlights, this.highlightRange(r, cssClass));
      }
      return highlights;
    };

    Annotator.prototype.addPlugin = function(name, options) {
      var klass, _base;

      if (this.plugins[name]) {
        console.error(_t("You cannot have more than one instance of any plugin."));
      } else {
        klass = Annotator.Plugin[name];
        if (typeof klass === 'function') {
          this.plugins[name] = new klass(this.element[0], options);
          this.plugins[name].annotator = this;
          if (typeof (_base = this.plugins[name]).pluginInit === "function") {
            _base.pluginInit();
          }
        } else {
          console.error(_t("Could not load ") + name + _t(" plugin. Have you included the appropriate <script> tag?"));
        }
      }
      return this;
    };

    Annotator.prototype.showEditor = function(annotation, location) {
      this.editor.element.css(location);
      this.editor.load(annotation);
      this.publish('annotationEditorShown', [this.editor, annotation]);
      return this;
    };

    Annotator.prototype.onEditorHide = function() {
      this.publish('annotationEditorHidden', [this.editor]);
      return this.ignoreMouseup = false;
    };

    Annotator.prototype.onEditorSubmit = function(annotation) {
      return this.publish('annotationEditorSubmit', [this.editor, annotation]);
    };

    Annotator.prototype.showViewer = function(annotations, location) {
      this.viewer.element.css(location);
      this.viewer.load(annotations);
      return this.publish('annotationViewerShown', [this.viewer, annotations]);
    };

    Annotator.prototype.startViewerHideTimer = function() {
      if (!this.viewerHideTimer) {
        return this.viewerHideTimer = setTimeout(this.viewer.hide, 250);
      }
    };

    Annotator.prototype.clearViewerHideTimer = function() {
      clearTimeout(this.viewerHideTimer);
      return this.viewerHideTimer = false;
    };

    Annotator.prototype.checkForStartSelection = function(event) {
      if (!(event && this.isAnnotator(event.target))) {
        this.startViewerHideTimer();
        return this.mouseIsDown = true;
      }
    };

    Annotator.prototype.checkForEndSelection = function(event) {
      var container, range, _k, _len2, _ref1;

      this.mouseIsDown = false;
      if (this.ignoreMouseup) {
        return;
      }
      this.selectedRanges = this.getSelectedRanges();
      _ref1 = this.selectedRanges;
      for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
        range = _ref1[_k];
        container = range.commonAncestor;
        if ($(container).hasClass('annotator-hl')) {
          container = $(container).parents('[class^=annotator-hl]')[0];
        }
        if (this.isAnnotator(container)) {
          return;
        }
      }
      if (event && this.selectedRanges.length) {
        return this.adder.css(util.mousePosition(event, this.wrapper[0])).show();
      } else {
        return this.adder.hide();
      }
    };

    Annotator.prototype.isAnnotator = function(element) {
      return !!$(element).parents().andSelf().filter('[class^=annotator-]').not(this.wrapper).length;
    };

    Annotator.prototype.onHighlightMouseover = function(event) {
      var annotations;

      this.clearViewerHideTimer();
      if (this.mouseIsDown || this.viewer.isShown()) {
        return false;
      }
      annotations = $(event.target).parents('.annotator-hl').andSelf().map(function() {
        return $(this).data("annotation");
      });
      return this.showViewer($.makeArray(annotations), util.mousePosition(event, this.wrapper[0]));
    };

    Annotator.prototype.onAdderMousedown = function(event) {
      if (event != null) {
        event.preventDefault();
      }
      return this.ignoreMouseup = true;
    };

    Annotator.prototype.onAdderClick = function(event) {
      var annotation, cancel, cleanup, position, save,
        _this = this;

      if (event != null) {
        event.preventDefault();
      }
      position = this.adder.position();
      this.adder.hide();
      annotation = this.setupAnnotation(this.createAnnotation());
      $(annotation.highlights).addClass('annotator-hl-temporary');
      save = function() {
        cleanup();
        $(annotation.highlights).removeClass('annotator-hl-temporary');
        return _this.publish('annotationCreated', [annotation]);
      };
      cancel = function() {
        cleanup();
        return _this.deleteAnnotation(annotation);
      };
      cleanup = function() {
        _this.unsubscribe('annotationEditorHidden', cancel);
        return _this.unsubscribe('annotationEditorSubmit', save);
      };
      this.subscribe('annotationEditorHidden', cancel);
      this.subscribe('annotationEditorSubmit', save);
      return this.showEditor(annotation, position);
    };

    Annotator.prototype.onEditAnnotation = function(annotation) {
      var cleanup, offset, update,
        _this = this;

      offset = this.viewer.element.position();
      update = function() {
        cleanup();
        return _this.updateAnnotation(annotation);
      };
      cleanup = function() {
        _this.unsubscribe('annotationEditorHidden', cleanup);
        return _this.unsubscribe('annotationEditorSubmit', update);
      };
      this.subscribe('annotationEditorHidden', cleanup);
      this.subscribe('annotationEditorSubmit', update);
      this.viewer.hide();
      return this.showEditor(annotation, offset);
    };

    Annotator.prototype.onDeleteAnnotation = function(annotation) {
      this.viewer.hide();
      return this.deleteAnnotation(annotation);
    };

    return Annotator;

  })(Delegator);

  Annotator.Plugin = (function(_super) {
    __extends(Plugin, _super);

    function Plugin(element, options) {
      Plugin.__super__.constructor.apply(this, arguments);
    }

    Plugin.prototype.pluginInit = function() {};

    return Plugin;

  })(Delegator);

  g = util.getGlobal();

  if (((_ref1 = g.document) != null ? _ref1.evaluate : void 0) == null) {
    $.getScript('//assets.annotateit.org/vendor/xpath.min.js');
  }

  if (g.getSelection == null) {
    $.getScript('//assets.annotateit.org/vendor/ierange.min.js');
  }

  if (g.JSON == null) {
    $.getScript('//assets.annotateit.org/vendor/json2.min.js');
  }

  Annotator.$ = $;

  Annotator.Delegator = Delegator;

  Annotator.Range = Range;

  Annotator._t = _t;

  Annotator.supported = function() {
    return (function() {
      return !!this.getSelection;
    })();
  };

  Annotator.noConflict = function() {
    util.getGlobal().Annotator = _Annotator;
    return this;
  };

  $.plugin('annotator', Annotator);

  this.Annotator = Annotator;

  Annotator.Widget = (function(_super) {
    __extends(Widget, _super);

    Widget.prototype.classes = {
      hide: 'annotator-hide',
      invert: {
        x: 'annotator-invert-x',
        y: 'annotator-invert-y'
      }
    };

    function Widget(element, options) {
      Widget.__super__.constructor.apply(this, arguments);
      this.classes = $.extend({}, Annotator.Widget.prototype.classes, this.classes);
    }

    Widget.prototype.checkOrientation = function() {
      var current, offset, viewport, widget, window;

      this.resetOrientation();
      window = $(util.getGlobal());
      widget = this.element.children(":first");
      offset = widget.offset();
      viewport = {
        top: window.scrollTop(),
        right: window.width() + window.scrollLeft()
      };
      current = {
        top: offset.top,
        right: offset.left + widget.width()
      };
      if ((current.top - viewport.top) < 0) {
        this.invertY();
      }
      if ((current.right - viewport.right) > 0) {
        this.invertX();
      }
      return this;
    };

    Widget.prototype.resetOrientation = function() {
      this.element.removeClass(this.classes.invert.x).removeClass(this.classes.invert.y);
      return this;
    };

    Widget.prototype.invertX = function() {
      this.element.addClass(this.classes.invert.x);
      return this;
    };

    Widget.prototype.invertY = function() {
      this.element.addClass(this.classes.invert.y);
      return this;
    };

    Widget.prototype.isInvertedY = function() {
      return this.element.hasClass(this.classes.invert.y);
    };

    Widget.prototype.isInvertedX = function() {
      return this.element.hasClass(this.classes.invert.x);
    };

    return Widget;

  })(Delegator);

  Annotator.Editor = (function(_super) {
    __extends(Editor, _super);

    Editor.prototype.events = {
      "form submit": "submit",
      ".annotator-save click": "submit",
      ".annotator-cancel click": "hide",
      ".annotator-cancel mouseover": "onCancelButtonMouseover",
      "textarea keydown": "processKeypress"
    };

    Editor.prototype.classes = {
      hide: 'annotator-hide',
      focus: 'annotator-focus'
    };

    Editor.prototype.html = "<div class=\"annotator-outer annotator-editor\">\n  <form class=\"annotator-widget\">\n    <ul class=\"annotator-listing\"></ul>\n    <div class=\"annotator-controls\">\n      <a href=\"#cancel\" class=\"annotator-cancel\">" + _t('Cancel') + "</a>\n<a href=\"#save\" class=\"annotator-save annotator-focus\">" + _t('Save') + "</a>\n    </div>\n  </form>\n</div>";

    Editor.prototype.options = {};

    function Editor(options) {
      this.onCancelButtonMouseover = __bind(this.onCancelButtonMouseover, this);
      this.processKeypress = __bind(this.processKeypress, this);
      this.submit = __bind(this.submit, this);
      this.load = __bind(this.load, this);
      this.hide = __bind(this.hide, this);
      this.show = __bind(this.show, this);      Editor.__super__.constructor.call(this, $(this.html)[0], options);
      this.fields = [];
      this.annotation = {};
    }

    Editor.prototype.show = function(event) {
      util.preventEventDefault(event);
      this.element.removeClass(this.classes.hide);
      this.element.find('.annotator-save').addClass(this.classes.focus);
      this.checkOrientation();
      this.element.find(":input:first").focus();
      this.setupDraggables();
      return this.publish('show');
    };

    Editor.prototype.hide = function(event) {
      util.preventEventDefault(event);
      this.element.addClass(this.classes.hide);
      return this.publish('hide');
    };

    Editor.prototype.load = function(annotation) {
      var field, _k, _len2, _ref2;

      this.annotation = annotation;
      this.publish('load', [this.annotation]);
      _ref2 = this.fields;
      for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
        field = _ref2[_k];
        field.load(field.element, this.annotation);
      }
      return this.show();
    };

    Editor.prototype.submit = function(event) {
      var field, _k, _len2, _ref2;

      util.preventEventDefault(event);
      _ref2 = this.fields;
      for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
        field = _ref2[_k];
        field.submit(field.element, this.annotation);
      }
      this.publish('save', [this.annotation]);
      return this.hide();
    };

    Editor.prototype.addField = function(options) {
      var element, field, input;

      field = $.extend({
        id: 'annotator-field-' + util.uuid(),
        type: 'input',
        label: '',
        load: function() {},
        submit: function() {}
      }, options);
      input = null;
      element = $('<li class="annotator-item" />');
      field.element = element[0];
      switch (field.type) {
        case 'textarea':
          input = $('<textarea />');
          break;
        case 'input':
        case 'checkbox':
          input = $('<input />');
      }
      element.append(input);
      input.attr({
        id: field.id,
        placeholder: field.label
      });
      if (field.type === 'checkbox') {
        input[0].type = 'checkbox';
        element.addClass('annotator-checkbox');
        element.append($('<label />', {
          "for": field.id,
          html: field.label
        }));
      }
      this.element.find('ul:first').append(element);
      this.fields.push(field);
      return field.element;
    };

    Editor.prototype.checkOrientation = function() {
      var controls, list;

      Editor.__super__.checkOrientation.apply(this, arguments);
      list = this.element.find('ul');
      controls = this.element.find('.annotator-controls');
      if (this.element.hasClass(this.classes.invert.y)) {
        controls.insertBefore(list);
      } else if (controls.is(':first-child')) {
        controls.insertAfter(list);
      }
      return this;
    };

    Editor.prototype.processKeypress = function(event) {
      if (event.keyCode === 27) {
        return this.hide();
      } else if (event.keyCode === 13 && !event.shiftKey) {
        return this.submit();
      }
    };

    Editor.prototype.onCancelButtonMouseover = function() {
      return this.element.find('.' + this.classes.focus).removeClass(this.classes.focus);
    };

    Editor.prototype.setupDraggables = function() {
      var classes, controls, cornerItem, editor, mousedown, onMousedown, onMousemove, onMouseup, resize, textarea, throttle,
        _this = this;

      this.element.find('.annotator-resize').remove();
      if (this.element.hasClass(this.classes.invert.y)) {
        cornerItem = this.element.find('.annotator-item:last');
      } else {
        cornerItem = this.element.find('.annotator-item:first');
      }
      if (cornerItem) {
        $('<span class="annotator-resize"></span>').appendTo(cornerItem);
      }
      mousedown = null;
      classes = this.classes;
      editor = this.element;
      textarea = null;
      resize = editor.find('.annotator-resize');
      controls = editor.find('.annotator-controls');
      throttle = false;
      onMousedown = function(event) {
        if (event.target === this) {
          mousedown = {
            element: this,
            top: event.pageY,
            left: event.pageX
          };
          textarea = editor.find('textarea:first');
          $(window).bind({
            'mouseup.annotator-editor-resize': onMouseup,
            'mousemove.annotator-editor-resize': onMousemove
          });
          return event.preventDefault();
        }
      };
      onMouseup = function() {
        mousedown = null;
        return $(window).unbind('.annotator-editor-resize');
      };
      onMousemove = function(event) {
        var diff, directionX, directionY, height, width;

        if (mousedown && throttle === false) {
          diff = {
            top: event.pageY - mousedown.top,
            left: event.pageX - mousedown.left
          };
          if (mousedown.element === resize[0]) {
            height = textarea.outerHeight();
            width = textarea.outerWidth();
            directionX = editor.hasClass(classes.invert.x) ? -1 : 1;
            directionY = editor.hasClass(classes.invert.y) ? 1 : -1;
            textarea.height(height + (diff.top * directionY));
            textarea.width(width + (diff.left * directionX));
            if (textarea.outerHeight() !== height) {
              mousedown.top = event.pageY;
            }
            if (textarea.outerWidth() !== width) {
              mousedown.left = event.pageX;
            }
          } else if (mousedown.element === controls[0]) {
            editor.css({
              top: parseInt(editor.css('top'), 10) + diff.top,
              left: parseInt(editor.css('left'), 10) + diff.left
            });
            mousedown.top = event.pageY;
            mousedown.left = event.pageX;
          }
          throttle = true;
          return setTimeout(function() {
            return throttle = false;
          }, 1000 / 60);
        }
      };
      resize.bind('mousedown', onMousedown);
      return controls.bind('mousedown', onMousedown);
    };

    return Editor;

  })(Annotator.Widget);

  Annotator.Viewer = (function(_super) {
    __extends(Viewer, _super);

    Viewer.prototype.events = {
      ".annotator-edit click": "onEditClick",
      ".annotator-delete click": "onDeleteClick"
    };

    Viewer.prototype.classes = {
      hide: 'annotator-hide',
      showControls: 'annotator-visible'
    };

    Viewer.prototype.html = {
      element: "<div class=\"annotator-outer annotator-viewer\">\n  <ul class=\"annotator-widget annotator-listing\"></ul>\n</div>",
      item: "<li class=\"annotator-annotation annotator-item\">\n  <span class=\"annotator-controls\">\n    <a href=\"#\" title=\"View as webpage\" class=\"annotator-link\">View as webpage</a>\n    <button title=\"Edit\" class=\"annotator-edit\">Edit</button>\n    <button title=\"Delete\" class=\"annotator-delete\">Delete</button>\n  </span>\n</li>"
    };

    Viewer.prototype.options = {
      readOnly: false
    };

    function Viewer(options) {
      this.onDeleteClick = __bind(this.onDeleteClick, this);
      this.onEditClick = __bind(this.onEditClick, this);
      this.load = __bind(this.load, this);
      this.hide = __bind(this.hide, this);
      this.show = __bind(this.show, this);      Viewer.__super__.constructor.call(this, $(this.html.element)[0], options);
      this.item = $(this.html.item)[0];
      this.fields = [];
      this.annotations = [];
    }

    Viewer.prototype.show = function(event) {
      var controls,
        _this = this;

      util.preventEventDefault(event);
      controls = this.element.find('.annotator-controls').addClass(this.classes.showControls);
      setTimeout((function() {
        return controls.removeClass(_this.classes.showControls);
      }), 500);
      this.element.removeClass(this.classes.hide);
      return this.checkOrientation().publish('show');
    };

    Viewer.prototype.isShown = function() {
      return !this.element.hasClass(this.classes.hide);
    };

    Viewer.prototype.hide = function(event) {
      util.preventEventDefault(event);
      this.element.addClass(this.classes.hide);
      return this.publish('hide');
    };

    Viewer.prototype.load = function(annotations) {
      var annotation, controller, controls, del, edit, element, field, item, link, links, list, _k, _l, _len2, _len3, _ref2, _ref3;

      this.annotations = annotations || [];
      list = this.element.find('ul:first').empty();
      _ref2 = this.annotations;
      for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
        annotation = _ref2[_k];
        item = $(this.item).clone().appendTo(list).data('annotation', annotation);
        controls = item.find('.annotator-controls');
        link = controls.find('.annotator-link');
        edit = controls.find('.annotator-edit');
        del = controls.find('.annotator-delete');
        links = new LinkParser(annotation.links || []).get('alternate', {
          'type': 'text/html'
        });
        if (links.length === 0 || (links[0].href == null)) {
          link.remove();
        } else {
          link.attr('href', links[0].href);
        }
        if (this.options.readOnly) {
          edit.remove();
          del.remove();
        } else {
          controller = {
            showEdit: function() {
              return edit.removeAttr('disabled');
            },
            hideEdit: function() {
              return edit.attr('disabled', 'disabled');
            },
            showDelete: function() {
              return del.removeAttr('disabled');
            },
            hideDelete: function() {
              return del.attr('disabled', 'disabled');
            }
          };
        }
        _ref3 = this.fields;
        for (_l = 0, _len3 = _ref3.length; _l < _len3; _l++) {
          field = _ref3[_l];
          element = $(field.element).clone().appendTo(item)[0];
          field.load(element, annotation, controller);
        }
      }
      this.publish('load', [this.annotations]);
      return this.show();
    };

    Viewer.prototype.addField = function(options) {
      var field;

      field = $.extend({
        load: function() {}
      }, options);
      field.element = $('<div />')[0];
      this.fields.push(field);
      field.element;
      return this;
    };

    Viewer.prototype.onEditClick = function(event) {
      return this.onButtonClick(event, 'edit');
    };

    Viewer.prototype.onDeleteClick = function(event) {
      return this.onButtonClick(event, 'delete');
    };

    Viewer.prototype.onButtonClick = function(event, type) {
      var item;

      item = $(event.target).parents('.annotator-annotation');
      return this.publish(type, [item.data('annotation')]);
    };

    return Viewer;

  })(Annotator.Widget);

  LinkParser = (function() {
    function LinkParser(data) {
      this.data = data;
    }

    LinkParser.prototype.get = function(rel, cond) {
      var d, k, keys, match, v, _k, _len2, _ref2, _results;

      if (cond == null) {
        cond = {};
      }
      cond = $.extend({}, cond, {
        rel: rel
      });
      keys = (function() {
        var _results;

        _results = [];
        for (k in cond) {
          if (!__hasProp.call(cond, k)) continue;
          v = cond[k];
          _results.push(k);
        }
        return _results;
      })();
      _ref2 = this.data;
      _results = [];
      for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
        d = _ref2[_k];
        match = keys.reduce((function(m, k) {
          return m && (d[k] === cond[k]);
        }), true);
        if (match) {
          _results.push(d);
        } else {
          continue;
        }
      }
      return _results;
    };

    return LinkParser;

  })();

  Annotator = Annotator || {};

  Annotator.Notification = (function(_super) {
    __extends(Notification, _super);

    Notification.prototype.events = {
      "click": "hide"
    };

    Notification.prototype.options = {
      html: "<div class='annotator-notice'></div>",
      classes: {
        show: "annotator-notice-show",
        info: "annotator-notice-info",
        success: "annotator-notice-success",
        error: "annotator-notice-error"
      }
    };

    function Notification(options) {
      this.hide = __bind(this.hide, this);
      this.show = __bind(this.show, this);      Notification.__super__.constructor.call(this, $(this.options.html).appendTo(document.body)[0], options);
    }

    Notification.prototype.show = function(message, status) {
      if (status == null) {
        status = Annotator.Notification.INFO;
      }
      $(this.element).addClass(this.options.classes.show).addClass(this.options.classes[status]).escape(message || "");
      setTimeout(this.hide, 5000);
      return this;
    };

    Notification.prototype.hide = function() {
      $(this.element).removeClass(this.options.classes.show);
      return this;
    };

    return Notification;

  })(Delegator);

  Annotator.Notification.INFO = 'show';

  Annotator.Notification.SUCCESS = 'success';

  Annotator.Notification.ERROR = 'error';

  $(function() {
    var notification;

    notification = new Annotator.Notification;
    Annotator.showNotification = notification.show;
    return Annotator.hideNotification = notification.hide;
  });

}).call(this);
