(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([26],{

/***/ "./common/lib/xmodule/xmodule/assets/library_source_block/LibrarySourcedBlockPicker.jsx":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LibrarySourcedBlockPicker", function() { return LibrarySourcedBlockPicker; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_whatwg_fetch__ = __webpack_require__("./node_modules/whatwg-fetch/fetch.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0_whatwg_fetch___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_whatwg_fetch__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_prop_types__ = __webpack_require__("./node_modules/prop-types/index.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1_prop_types___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_prop_types__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_react__ = __webpack_require__("./node_modules/react/index.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_react___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_react__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3_underscore__ = __webpack_require__(1);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3_underscore___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_3_underscore__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_4__style_css__ = __webpack_require__("./common/lib/xmodule/xmodule/assets/library_source_block/style.css");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_4__style_css___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_4__style_css__);
var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _asyncToGenerator(fn) { return function () { var gen = fn.apply(this, arguments); return new Promise(function (resolve, reject) { function step(key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { return Promise.resolve(value).then(function (value) { step("next", value); }, function (err) { step("throw", err); }); } } return step("next"); }); }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

/* globals gettext */







var LibrarySourcedBlockPicker = function (_React$Component) {
  _inherits(LibrarySourcedBlockPicker, _React$Component);

  function LibrarySourcedBlockPicker(props) {
    _classCallCheck(this, LibrarySourcedBlockPicker);

    var _this = _possibleConstructorReturn(this, (LibrarySourcedBlockPicker.__proto__ || Object.getPrototypeOf(LibrarySourcedBlockPicker)).call(this, props));

    _this.state = {
      libraries: [],
      xblocks: [],
      searchedLibrary: '',
      libraryLoading: false,
      xblocksLoading: false,
      selectedLibrary: undefined,
      selectedXblocks: new Set(_this.props.selectedXblocks)
    };
    _this.onLibrarySearchInput = _this.onLibrarySearchInput.bind(_this);
    _this.onXBlockSearchInput = _this.onXBlockSearchInput.bind(_this);
    _this.onLibrarySelected = _this.onLibrarySelected.bind(_this);
    _this.onXblockSelected = _this.onXblockSelected.bind(_this);
    _this.onDeleteClick = _this.onDeleteClick.bind(_this);
    return _this;
  }

  _createClass(LibrarySourcedBlockPicker, [{
    key: 'componentDidMount',
    value: function componentDidMount() {
      this.fetchLibraries();
    }
  }, {
    key: 'fetchLibraries',
    value: function fetchLibraries() {
      var textSearch = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '';
      var page = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 1;
      var append = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : false;

      this.setState({
        libraries: append ? this.state.libraries : [],
        libraryLoading: true
      }, _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee() {
        var _this2 = this;

        var res;
        return regeneratorRuntime.wrap(function _callee$(_context) {
          while (1) {
            switch (_context.prev = _context.next) {
              case 0:
                _context.prev = 0;
                _context.next = 3;
                return fetch('/api/libraries/v2/?pagination=true&page=' + page + '&text_search=' + textSearch);

              case 3:
                res = _context.sent;
                _context.next = 6;
                return res.json();

              case 6:
                res = _context.sent;

                this.setState({
                  libraries: this.state.libraries.concat(res.results),
                  libraryLoading: false
                }, function () {
                  if (res.next) {
                    _this2.fetchLibraries(textSearch, page + 1, true);
                  }
                });
                _context.next = 14;
                break;

              case 10:
                _context.prev = 10;
                _context.t0 = _context['catch'](0);

                $('#library-sourced-block-picker').trigger('error', {
                  title: 'Could not fetch library',
                  message: _context.t0
                });
                this.setState({
                  libraries: [],
                  libraryLoading: false
                });

              case 14:
              case 'end':
                return _context.stop();
            }
          }
        }, _callee, this, [[0, 10]]);
      })));
    }
  }, {
    key: 'fetchXblocks',
    value: function fetchXblocks(library) {
      var textSearch = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : '';
      var page = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 1;
      var append = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : false;

      this.setState({
        xblocks: append ? this.state.xblocks : [],
        xblocksLoading: true
      }, _asyncToGenerator( /*#__PURE__*/regeneratorRuntime.mark(function _callee2() {
        var _this3 = this;

        var res;
        return regeneratorRuntime.wrap(function _callee2$(_context2) {
          while (1) {
            switch (_context2.prev = _context2.next) {
              case 0:
                _context2.prev = 0;
                _context2.next = 3;
                return fetch('/api/libraries/v2/' + library + '/blocks/?pagination=true&page=' + page + '&text_search=' + textSearch);

              case 3:
                res = _context2.sent;
                _context2.next = 6;
                return res.json();

              case 6:
                res = _context2.sent;

                this.setState({
                  xblocks: this.state.xblocks.concat(res.results),
                  xblocksLoading: false
                }, function () {
                  if (res.next) {
                    _this3.fetchXblocks(library, textSearch, page + 1, true);
                  }
                });
                _context2.next = 14;
                break;

              case 10:
                _context2.prev = 10;
                _context2.t0 = _context2['catch'](0);

                $('#library-sourced-block-picker').trigger('error', {
                  title: 'Could not fetch xblocks',
                  message: _context2.t0
                });
                this.setState({
                  xblocks: [],
                  xblocksLoading: false
                });

              case 14:
              case 'end':
                return _context2.stop();
            }
          }
        }, _callee2, this, [[0, 10]]);
      })));
    }
  }, {
    key: 'onLibrarySearchInput',
    value: function onLibrarySearchInput(event) {
      var _this4 = this;

      event.persist();
      this.setState({
        searchedLibrary: event.target.value
      });
      if (!this.debouncedFetchLibraries) {
        this.debouncedFetchLibraries = __WEBPACK_IMPORTED_MODULE_3_underscore___default.a.debounce(function (value) {
          _this4.fetchLibraries(value);
        }, 300);
      }
      this.debouncedFetchLibraries(event.target.value);
    }
  }, {
    key: 'onXBlockSearchInput',
    value: function onXBlockSearchInput(event) {
      var _this5 = this;

      event.persist();
      if (!this.debouncedFetchXblocks) {
        this.debouncedFetchXblocks = __WEBPACK_IMPORTED_MODULE_3_underscore___default.a.debounce(function (value) {
          _this5.fetchXblocks(_this5.state.selectedLibrary, value);
        }, 300);
      }
      this.debouncedFetchXblocks(event.target.value);
    }
  }, {
    key: 'onLibrarySelected',
    value: function onLibrarySelected(event) {
      this.setState({
        selectedLibrary: event.target.value
      });
      this.fetchXblocks(event.target.value);
    }
  }, {
    key: 'onXblockSelected',
    value: function onXblockSelected(event) {
      var state = new Set(this.state.selectedXblocks);
      if (event.target.checked) {
        state.add(event.target.value);
      } else {
        state.delete(event.target.value);
      }
      this.setState({
        selectedXblocks: state
      }, this.updateList);
    }
  }, {
    key: 'onDeleteClick',
    value: function onDeleteClick(event) {
      var value = void 0;
      if (event.target.tagName == 'SPAN') {
        value = event.target.parentElement.dataset.value;
      } else {
        value = event.target.dataset.value;
      }
      var state = new Set(this.state.selectedXblocks);
      state.delete(value);
      this.setState({
        selectedXblocks: state
      }, this.updateList);
    }
  }, {
    key: 'updateList',
    value: function updateList(list) {
      $('#library-sourced-block-picker').trigger('selected-xblocks', {
        sourceBlockIds: Array.from(this.state.selectedXblocks)
      });
    }
  }, {
    key: 'render',
    value: function render() {
      var _this6 = this;

      return __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
        'section',
        null,
        __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
          'div',
          { className: 'container-message wrapper-message' },
          __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
            'div',
            { className: 'message has-warnings', style: { margin: 0, color: "white" } },
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
              'p',
              { className: 'warning' },
              __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement('span', { className: 'icon fa fa-warning', 'aria-hidden': 'true' }),
              'Hitting \'Save and Import\' will import the latest versions of the selected blocks, overwriting any changes done to this block post-import.'
            )
          )
        ),
        __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
          'div',
          { style: { display: "flex", flexDirection: "row", justifyContent: "center" } },
          __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
            'div',
            { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.column },
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement('input', { type: 'text', className: [__WEBPACK_IMPORTED_MODULE_4__style_css___default.a.search], 'aria-label': 'Search for library', placeholder: 'Search for library', label: 'Search for library', name: 'librarySearch', onChange: this.onLibrarySearchInput }),
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
              'div',
              { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.elementList, onChange: this.onLibrarySelected },
              this.state.libraries.map(function (lib) {
                return __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                  'div',
                  { key: lib.id, className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.element },
                  __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement('input', { id: 'sourced-library-' + lib.id, type: 'radio', value: lib.id, name: 'library' }),
                  __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                    'label',
                    { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.elementItem, htmlFor: 'sourced-library-' + lib.id },
                    lib.title
                  )
                );
              }),
              this.state.libraryLoading && __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                'span',
                null,
                gettext('Loading...')
              )
            )
          ),
          __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
            'div',
            { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.column },
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement('input', { type: 'text', className: [__WEBPACK_IMPORTED_MODULE_4__style_css___default.a.search], 'aria-label': 'Search for XBlocks', placeholder: 'Search for XBlocks', name: 'xblockSearch', onChange: this.onXBlockSearchInput, disabled: !this.state.selectedLibrary || this.state.libraryLoading }),
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
              'div',
              { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.elementList, onChange: this.onXblockSelected },
              this.state.xblocks.map(function (block) {
                return __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                  'div',
                  { key: block.id, className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.element },
                  __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement('input', { id: 'sourced-block-' + block.id, type: 'checkbox', value: block.id, name: 'block', checked: _this6.state.selectedXblocks.has(block.id), readOnly: true }),
                  __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                    'label',
                    { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.elementItem, htmlFor: 'sourced-block-' + block.id },
                    block.display_name,
                    ' (',
                    block.id,
                    ')'
                  )
                );
              }),
              this.state.xblocksLoading && __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                'span',
                null,
                gettext('Loading...')
              )
            )
          ),
          __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
            'div',
            { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.column },
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
              'h4',
              { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.selectedBlocks },
              gettext('Selected blocks')
            ),
            __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
              'ul',
              null,
              Array.from(this.state.selectedXblocks).map(function (block) {
                return __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                  'li',
                  { key: block, className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.element, style: { display: "flex" } },
                  __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                    'label',
                    { className: __WEBPACK_IMPORTED_MODULE_4__style_css___default.a.elementItem },
                    block
                  ),
                  __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement(
                    'button',
                    { className: [__WEBPACK_IMPORTED_MODULE_4__style_css___default.a.remove], 'data-value': block, onClick: _this6.onDeleteClick, 'aria-label': 'Remove block' },
                    __WEBPACK_IMPORTED_MODULE_2_react___default.a.createElement('span', { 'aria-hidden': 'true', className: 'icon fa fa-times' })
                  )
                );
              })
            )
          )
        )
      );
    }
  }]);

  return LibrarySourcedBlockPicker;
}(__WEBPACK_IMPORTED_MODULE_2_react___default.a.Component);

LibrarySourcedBlockPicker.propTypes = {
  selectedXblocks: __WEBPACK_IMPORTED_MODULE_1_prop_types___default.a.array
};

LibrarySourcedBlockPicker.defaultProps = {
  selectedXblocks: []
};

 // eslint-disable-line import/prefer-default-export
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ }),

/***/ "./common/lib/xmodule/xmodule/assets/library_source_block/style.css":
/***/ (function(module, exports, __webpack_require__) {

// style-loader: Adds some css to the DOM by adding a <style> tag

// load the styles
var content = __webpack_require__("./node_modules/css-loader/index.js?{\"modules\":true}!./common/lib/xmodule/xmodule/assets/library_source_block/style.css");
if(typeof content === 'string') content = [[module.i, content, '']];
// Prepare cssTransformation
var transform;

var options = {}
options.transform = transform
// add the styles to the DOM
var update = __webpack_require__("./node_modules/style-loader/lib/addStyles.js")(content, options);
if(content.locals) module.exports = content.locals;
// Hot Module Replacement
if(false) {
	// When the styles change, update the <style> tags
	if(!content.locals) {
		module.hot.accept("!!../../../../../../node_modules/css-loader/index.js??ref--18-1!./style.css", function() {
			var newContent = require("!!../../../../../../node_modules/css-loader/index.js??ref--18-1!./style.css");
			if(typeof newContent === 'string') newContent = [[module.id, newContent, '']];
			update(newContent);
		});
	}
	// When the module is disposed, remove the <style> tags
	module.hot.dispose(function() { update(); });
}

/***/ }),

/***/ "./node_modules/css-loader/index.js?{\"modules\":true}!./common/lib/xmodule/xmodule/assets/library_source_block/style.css":
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__("./node_modules/css-loader/lib/css-base.js")(false);
// imports


// module
exports.push([module.i, "._7zTOU65j81biqF1exVAxw {\n  display: flex;\n  flex-direction: column;\n  margin: 10px;\n  max-width: 300px;\n  flex-grow: 1;\n}\n.-rMxuYKo3Kx822cCzwWvP {\n  margin-top: 10px;\n}\ninput._2riMgfzRbLl3hqEsWBr4ag {\n  width: 100% !important;\n  height: auto !important;\n}\n._9d7ApsmgEtdazHxiGd_rF > input[type='checkbox'],\n._9d7ApsmgEtdazHxiGd_rF > input[type='radio'] {\n  position: absolute;\n  width: 0 !important;\n  height: 0 !important;\n  top: -9999px;\n}\n._9d7ApsmgEtdazHxiGd_rF > ._1UEEHHEZYxl9YNFmAai5MJ {\n  display: flex;\n  flex-grow: 1;\n  padding: 0.625rem 1.25rem;\n  border: 1px solid rgba(0, 0, 0, 0.25);\n}\n._9d7ApsmgEtdazHxiGd_rF + ._9d7ApsmgEtdazHxiGd_rF > label {\n  border-top: 0;\n}\n._9d7ApsmgEtdazHxiGd_rF > input[type='checkbox']:focus + label,\n._9d7ApsmgEtdazHxiGd_rF > input[type='radio']:focus + label,\n._9d7ApsmgEtdazHxiGd_rF > input:hover + label {\n  background: #f6f6f7;\n  cursor: pointer;\n}\n._9d7ApsmgEtdazHxiGd_rF > input:checked + label {\n  background: #23419f;\n  color: #fff;\n}\n._9d7ApsmgEtdazHxiGd_rF > input[type='checkbox']:checked:focus + label,\n._9d7ApsmgEtdazHxiGd_rF > input[type='radio']:checked:focus + label,\n._9d7ApsmgEtdazHxiGd_rF > input:checked:hover + label {\n  background: #193787;\n  cursor: pointer;\n}\n._1sEfGi5PCH66T3SD3ff7IV {\n  padding: 12px 8px 20px;\n}\nbutton.NOgjgz-cqvvw_nvDfmzqx {\n  background: #e00;\n  color: #fff;\n  border: solid rgba(0,0,0,0.25) 1px;\n}\nbutton.NOgjgz-cqvvw_nvDfmzqx:focus,\nbutton.NOgjgz-cqvvw_nvDfmzqx:hover {\n  background: #d00;\n}\n", ""]);

// exports
exports.locals = {
	"column": "_7zTOU65j81biqF1exVAxw",
	"elementList": "-rMxuYKo3Kx822cCzwWvP",
	"search": "_2riMgfzRbLl3hqEsWBr4ag",
	"element": "_9d7ApsmgEtdazHxiGd_rF",
	"elementItem": "_1UEEHHEZYxl9YNFmAai5MJ",
	"selectedBlocks": "_1sEfGi5PCH66T3SD3ff7IV",
	"remove": "NOgjgz-cqvvw_nvDfmzqx"
};

/***/ }),

/***/ "./node_modules/css-loader/lib/css-base.js":
/***/ (function(module, exports) {

/*
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Tobias Koppers @sokra
*/
// css base code, injected by the css-loader
module.exports = function(useSourceMap) {
	var list = [];

	// return the list of modules as css string
	list.toString = function toString() {
		return this.map(function (item) {
			var content = cssWithMappingToString(item, useSourceMap);
			if(item[2]) {
				return "@media " + item[2] + "{" + content + "}";
			} else {
				return content;
			}
		}).join("");
	};

	// import a list of modules into the list
	list.i = function(modules, mediaQuery) {
		if(typeof modules === "string")
			modules = [[null, modules, ""]];
		var alreadyImportedModules = {};
		for(var i = 0; i < this.length; i++) {
			var id = this[i][0];
			if(typeof id === "number")
				alreadyImportedModules[id] = true;
		}
		for(i = 0; i < modules.length; i++) {
			var item = modules[i];
			// skip already imported module
			// this implementation is not 100% perfect for weird media query combinations
			//  when a module is imported multiple times with different media queries.
			//  I hope this will never occur (Hey this way we have smaller bundles)
			if(typeof item[0] !== "number" || !alreadyImportedModules[item[0]]) {
				if(mediaQuery && !item[2]) {
					item[2] = mediaQuery;
				} else if(mediaQuery) {
					item[2] = "(" + item[2] + ") and (" + mediaQuery + ")";
				}
				list.push(item);
			}
		}
	};
	return list;
};

function cssWithMappingToString(item, useSourceMap) {
	var content = item[1] || '';
	var cssMapping = item[3];
	if (!cssMapping) {
		return content;
	}

	if (useSourceMap && typeof btoa === 'function') {
		var sourceMapping = toComment(cssMapping);
		var sourceURLs = cssMapping.sources.map(function (source) {
			return '/*# sourceURL=' + cssMapping.sourceRoot + source + ' */'
		});

		return [content].concat(sourceURLs).concat([sourceMapping]).join('\n');
	}

	return [content].join('\n');
}

// Adapted from convert-source-map (MIT)
function toComment(sourceMap) {
	// eslint-disable-next-line no-undef
	var base64 = btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap))));
	var data = 'sourceMappingURL=data:application/json;charset=utf-8;base64,' + base64;

	return '/*# ' + data + ' */';
}


/***/ }),

/***/ "./node_modules/style-loader/lib/addStyles.js":
/***/ (function(module, exports, __webpack_require__) {

/*
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Tobias Koppers @sokra
*/

var stylesInDom = {};

var	memoize = function (fn) {
	var memo;

	return function () {
		if (typeof memo === "undefined") memo = fn.apply(this, arguments);
		return memo;
	};
};

var isOldIE = memoize(function () {
	// Test for IE <= 9 as proposed by Browserhacks
	// @see http://browserhacks.com/#hack-e71d8692f65334173fee715c222cb805
	// Tests for existence of standard globals is to allow style-loader
	// to operate correctly into non-standard environments
	// @see https://github.com/webpack-contrib/style-loader/issues/177
	return window && document && document.all && !window.atob;
});

var getElement = (function (fn) {
	var memo = {};

	return function(selector) {
		if (typeof memo[selector] === "undefined") {
			memo[selector] = fn.call(this, selector);
		}

		return memo[selector]
	};
})(function (target) {
	return document.querySelector(target)
});

var singleton = null;
var	singletonCounter = 0;
var	stylesInsertedAtTop = [];

var	fixUrls = __webpack_require__("./node_modules/style-loader/lib/urls.js");

module.exports = function(list, options) {
	if (typeof DEBUG !== "undefined" && DEBUG) {
		if (typeof document !== "object") throw new Error("The style-loader cannot be used in a non-browser environment");
	}

	options = options || {};

	options.attrs = typeof options.attrs === "object" ? options.attrs : {};

	// Force single-tag solution on IE6-9, which has a hard limit on the # of <style>
	// tags it will allow on a page
	if (!options.singleton) options.singleton = isOldIE();

	// By default, add <style> tags to the <head> element
	if (!options.insertInto) options.insertInto = "head";

	// By default, add <style> tags to the bottom of the target
	if (!options.insertAt) options.insertAt = "bottom";

	var styles = listToStyles(list, options);

	addStylesToDom(styles, options);

	return function update (newList) {
		var mayRemove = [];

		for (var i = 0; i < styles.length; i++) {
			var item = styles[i];
			var domStyle = stylesInDom[item.id];

			domStyle.refs--;
			mayRemove.push(domStyle);
		}

		if(newList) {
			var newStyles = listToStyles(newList, options);
			addStylesToDom(newStyles, options);
		}

		for (var i = 0; i < mayRemove.length; i++) {
			var domStyle = mayRemove[i];

			if(domStyle.refs === 0) {
				for (var j = 0; j < domStyle.parts.length; j++) domStyle.parts[j]();

				delete stylesInDom[domStyle.id];
			}
		}
	};
};

function addStylesToDom (styles, options) {
	for (var i = 0; i < styles.length; i++) {
		var item = styles[i];
		var domStyle = stylesInDom[item.id];

		if(domStyle) {
			domStyle.refs++;

			for(var j = 0; j < domStyle.parts.length; j++) {
				domStyle.parts[j](item.parts[j]);
			}

			for(; j < item.parts.length; j++) {
				domStyle.parts.push(addStyle(item.parts[j], options));
			}
		} else {
			var parts = [];

			for(var j = 0; j < item.parts.length; j++) {
				parts.push(addStyle(item.parts[j], options));
			}

			stylesInDom[item.id] = {id: item.id, refs: 1, parts: parts};
		}
	}
}

function listToStyles (list, options) {
	var styles = [];
	var newStyles = {};

	for (var i = 0; i < list.length; i++) {
		var item = list[i];
		var id = options.base ? item[0] + options.base : item[0];
		var css = item[1];
		var media = item[2];
		var sourceMap = item[3];
		var part = {css: css, media: media, sourceMap: sourceMap};

		if(!newStyles[id]) styles.push(newStyles[id] = {id: id, parts: [part]});
		else newStyles[id].parts.push(part);
	}

	return styles;
}

function insertStyleElement (options, style) {
	var target = getElement(options.insertInto)

	if (!target) {
		throw new Error("Couldn't find a style target. This probably means that the value for the 'insertInto' parameter is invalid.");
	}

	var lastStyleElementInsertedAtTop = stylesInsertedAtTop[stylesInsertedAtTop.length - 1];

	if (options.insertAt === "top") {
		if (!lastStyleElementInsertedAtTop) {
			target.insertBefore(style, target.firstChild);
		} else if (lastStyleElementInsertedAtTop.nextSibling) {
			target.insertBefore(style, lastStyleElementInsertedAtTop.nextSibling);
		} else {
			target.appendChild(style);
		}
		stylesInsertedAtTop.push(style);
	} else if (options.insertAt === "bottom") {
		target.appendChild(style);
	} else {
		throw new Error("Invalid value for parameter 'insertAt'. Must be 'top' or 'bottom'.");
	}
}

function removeStyleElement (style) {
	if (style.parentNode === null) return false;
	style.parentNode.removeChild(style);

	var idx = stylesInsertedAtTop.indexOf(style);
	if(idx >= 0) {
		stylesInsertedAtTop.splice(idx, 1);
	}
}

function createStyleElement (options) {
	var style = document.createElement("style");

	options.attrs.type = "text/css";

	addAttrs(style, options.attrs);
	insertStyleElement(options, style);

	return style;
}

function createLinkElement (options) {
	var link = document.createElement("link");

	options.attrs.type = "text/css";
	options.attrs.rel = "stylesheet";

	addAttrs(link, options.attrs);
	insertStyleElement(options, link);

	return link;
}

function addAttrs (el, attrs) {
	Object.keys(attrs).forEach(function (key) {
		el.setAttribute(key, attrs[key]);
	});
}

function addStyle (obj, options) {
	var style, update, remove, result;

	// If a transform function was defined, run it on the css
	if (options.transform && obj.css) {
	    result = options.transform(obj.css);

	    if (result) {
	    	// If transform returns a value, use that instead of the original css.
	    	// This allows running runtime transformations on the css.
	    	obj.css = result;
	    } else {
	    	// If the transform function returns a falsy value, don't add this css.
	    	// This allows conditional loading of css
	    	return function() {
	    		// noop
	    	};
	    }
	}

	if (options.singleton) {
		var styleIndex = singletonCounter++;

		style = singleton || (singleton = createStyleElement(options));

		update = applyToSingletonTag.bind(null, style, styleIndex, false);
		remove = applyToSingletonTag.bind(null, style, styleIndex, true);

	} else if (
		obj.sourceMap &&
		typeof URL === "function" &&
		typeof URL.createObjectURL === "function" &&
		typeof URL.revokeObjectURL === "function" &&
		typeof Blob === "function" &&
		typeof btoa === "function"
	) {
		style = createLinkElement(options);
		update = updateLink.bind(null, style, options);
		remove = function () {
			removeStyleElement(style);

			if(style.href) URL.revokeObjectURL(style.href);
		};
	} else {
		style = createStyleElement(options);
		update = applyToTag.bind(null, style);
		remove = function () {
			removeStyleElement(style);
		};
	}

	update(obj);

	return function updateStyle (newObj) {
		if (newObj) {
			if (
				newObj.css === obj.css &&
				newObj.media === obj.media &&
				newObj.sourceMap === obj.sourceMap
			) {
				return;
			}

			update(obj = newObj);
		} else {
			remove();
		}
	};
}

var replaceText = (function () {
	var textStore = [];

	return function (index, replacement) {
		textStore[index] = replacement;

		return textStore.filter(Boolean).join('\n');
	};
})();

function applyToSingletonTag (style, index, remove, obj) {
	var css = remove ? "" : obj.css;

	if (style.styleSheet) {
		style.styleSheet.cssText = replaceText(index, css);
	} else {
		var cssNode = document.createTextNode(css);
		var childNodes = style.childNodes;

		if (childNodes[index]) style.removeChild(childNodes[index]);

		if (childNodes.length) {
			style.insertBefore(cssNode, childNodes[index]);
		} else {
			style.appendChild(cssNode);
		}
	}
}

function applyToTag (style, obj) {
	var css = obj.css;
	var media = obj.media;

	if(media) {
		style.setAttribute("media", media)
	}

	if(style.styleSheet) {
		style.styleSheet.cssText = css;
	} else {
		while(style.firstChild) {
			style.removeChild(style.firstChild);
		}

		style.appendChild(document.createTextNode(css));
	}
}

function updateLink (link, options, obj) {
	var css = obj.css;
	var sourceMap = obj.sourceMap;

	/*
		If convertToAbsoluteUrls isn't defined, but sourcemaps are enabled
		and there is no publicPath defined then lets turn convertToAbsoluteUrls
		on by default.  Otherwise default to the convertToAbsoluteUrls option
		directly
	*/
	var autoFixUrls = options.convertToAbsoluteUrls === undefined && sourceMap;

	if (options.convertToAbsoluteUrls || autoFixUrls) {
		css = fixUrls(css);
	}

	if (sourceMap) {
		// http://stackoverflow.com/a/26603875
		css += "\n/*# sourceMappingURL=data:application/json;base64," + btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap)))) + " */";
	}

	var blob = new Blob([css], { type: "text/css" });

	var oldSrc = link.href;

	link.href = URL.createObjectURL(blob);

	if(oldSrc) URL.revokeObjectURL(oldSrc);
}


/***/ }),

/***/ "./node_modules/style-loader/lib/urls.js":
/***/ (function(module, exports) {


/**
 * When source maps are enabled, `style-loader` uses a link element with a data-uri to
 * embed the css on the page. This breaks all relative urls because now they are relative to a
 * bundle instead of the current page.
 *
 * One solution is to only use full urls, but that may be impossible.
 *
 * Instead, this function "fixes" the relative urls to be absolute according to the current page location.
 *
 * A rudimentary test suite is located at `test/fixUrls.js` and can be run via the `npm test` command.
 *
 */

module.exports = function (css) {
  // get current location
  var location = typeof window !== "undefined" && window.location;

  if (!location) {
    throw new Error("fixUrls requires window.location");
  }

	// blank or null?
	if (!css || typeof css !== "string") {
	  return css;
  }

  var baseUrl = location.protocol + "//" + location.host;
  var currentDir = baseUrl + location.pathname.replace(/\/[^\/]*$/, "/");

	// convert each url(...)
	/*
	This regular expression is just a way to recursively match brackets within
	a string.

	 /url\s*\(  = Match on the word "url" with any whitespace after it and then a parens
	   (  = Start a capturing group
	     (?:  = Start a non-capturing group
	         [^)(]  = Match anything that isn't a parentheses
	         |  = OR
	         \(  = Match a start parentheses
	             (?:  = Start another non-capturing groups
	                 [^)(]+  = Match anything that isn't a parentheses
	                 |  = OR
	                 \(  = Match a start parentheses
	                     [^)(]*  = Match anything that isn't a parentheses
	                 \)  = Match a end parentheses
	             )  = End Group
              *\) = Match anything and then a close parens
          )  = Close non-capturing group
          *  = Match anything
       )  = Close capturing group
	 \)  = Match a close parens

	 /gi  = Get all matches, not the first.  Be case insensitive.
	 */
	var fixedCss = css.replace(/url\s*\(((?:[^)(]|\((?:[^)(]+|\([^)(]*\))*\))*)\)/gi, function(fullMatch, origUrl) {
		// strip quotes (if they exist)
		var unquotedOrigUrl = origUrl
			.trim()
			.replace(/^"(.*)"$/, function(o, $1){ return $1; })
			.replace(/^'(.*)'$/, function(o, $1){ return $1; });

		// already a full url? no change
		if (/^(#|data:|http:\/\/|https:\/\/|file:\/\/\/)/i.test(unquotedOrigUrl)) {
		  return fullMatch;
		}

		// convert the url to a full url
		var newUrl;

		if (unquotedOrigUrl.indexOf("//") === 0) {
		  	//TODO: should we add protocol?
			newUrl = unquotedOrigUrl;
		} else if (unquotedOrigUrl.indexOf("/") === 0) {
			// path should be relative to the base url
			newUrl = baseUrl + unquotedOrigUrl; // already starts with '/'
		} else {
			// path should be relative to current directory
			newUrl = currentDir + unquotedOrigUrl.replace(/^\.\//, ""); // Strip leading './'
		}

		// send back the fixed url(...)
		return "url(" + JSON.stringify(newUrl) + ")";
	});

	// send back the fixed css
	return fixedCss;
};


/***/ }),

/***/ "./node_modules/whatwg-fetch/fetch.js":
/***/ (function(module, exports) {

(function(self) {
  'use strict';

  if (self.fetch) {
    return
  }

  var support = {
    searchParams: 'URLSearchParams' in self,
    iterable: 'Symbol' in self && 'iterator' in Symbol,
    blob: 'FileReader' in self && 'Blob' in self && (function() {
      try {
        new Blob()
        return true
      } catch(e) {
        return false
      }
    })(),
    formData: 'FormData' in self,
    arrayBuffer: 'ArrayBuffer' in self
  }

  if (support.arrayBuffer) {
    var viewClasses = [
      '[object Int8Array]',
      '[object Uint8Array]',
      '[object Uint8ClampedArray]',
      '[object Int16Array]',
      '[object Uint16Array]',
      '[object Int32Array]',
      '[object Uint32Array]',
      '[object Float32Array]',
      '[object Float64Array]'
    ]

    var isDataView = function(obj) {
      return obj && DataView.prototype.isPrototypeOf(obj)
    }

    var isArrayBufferView = ArrayBuffer.isView || function(obj) {
      return obj && viewClasses.indexOf(Object.prototype.toString.call(obj)) > -1
    }
  }

  function normalizeName(name) {
    if (typeof name !== 'string') {
      name = String(name)
    }
    if (/[^a-z0-9\-#$%&'*+.\^_`|~]/i.test(name)) {
      throw new TypeError('Invalid character in header field name')
    }
    return name.toLowerCase()
  }

  function normalizeValue(value) {
    if (typeof value !== 'string') {
      value = String(value)
    }
    return value
  }

  // Build a destructive iterator for the value list
  function iteratorFor(items) {
    var iterator = {
      next: function() {
        var value = items.shift()
        return {done: value === undefined, value: value}
      }
    }

    if (support.iterable) {
      iterator[Symbol.iterator] = function() {
        return iterator
      }
    }

    return iterator
  }

  function Headers(headers) {
    this.map = {}

    if (headers instanceof Headers) {
      headers.forEach(function(value, name) {
        this.append(name, value)
      }, this)
    } else if (Array.isArray(headers)) {
      headers.forEach(function(header) {
        this.append(header[0], header[1])
      }, this)
    } else if (headers) {
      Object.getOwnPropertyNames(headers).forEach(function(name) {
        this.append(name, headers[name])
      }, this)
    }
  }

  Headers.prototype.append = function(name, value) {
    name = normalizeName(name)
    value = normalizeValue(value)
    var oldValue = this.map[name]
    this.map[name] = oldValue ? oldValue+','+value : value
  }

  Headers.prototype['delete'] = function(name) {
    delete this.map[normalizeName(name)]
  }

  Headers.prototype.get = function(name) {
    name = normalizeName(name)
    return this.has(name) ? this.map[name] : null
  }

  Headers.prototype.has = function(name) {
    return this.map.hasOwnProperty(normalizeName(name))
  }

  Headers.prototype.set = function(name, value) {
    this.map[normalizeName(name)] = normalizeValue(value)
  }

  Headers.prototype.forEach = function(callback, thisArg) {
    for (var name in this.map) {
      if (this.map.hasOwnProperty(name)) {
        callback.call(thisArg, this.map[name], name, this)
      }
    }
  }

  Headers.prototype.keys = function() {
    var items = []
    this.forEach(function(value, name) { items.push(name) })
    return iteratorFor(items)
  }

  Headers.prototype.values = function() {
    var items = []
    this.forEach(function(value) { items.push(value) })
    return iteratorFor(items)
  }

  Headers.prototype.entries = function() {
    var items = []
    this.forEach(function(value, name) { items.push([name, value]) })
    return iteratorFor(items)
  }

  if (support.iterable) {
    Headers.prototype[Symbol.iterator] = Headers.prototype.entries
  }

  function consumed(body) {
    if (body.bodyUsed) {
      return Promise.reject(new TypeError('Already read'))
    }
    body.bodyUsed = true
  }

  function fileReaderReady(reader) {
    return new Promise(function(resolve, reject) {
      reader.onload = function() {
        resolve(reader.result)
      }
      reader.onerror = function() {
        reject(reader.error)
      }
    })
  }

  function readBlobAsArrayBuffer(blob) {
    var reader = new FileReader()
    var promise = fileReaderReady(reader)
    reader.readAsArrayBuffer(blob)
    return promise
  }

  function readBlobAsText(blob) {
    var reader = new FileReader()
    var promise = fileReaderReady(reader)
    reader.readAsText(blob)
    return promise
  }

  function readArrayBufferAsText(buf) {
    var view = new Uint8Array(buf)
    var chars = new Array(view.length)

    for (var i = 0; i < view.length; i++) {
      chars[i] = String.fromCharCode(view[i])
    }
    return chars.join('')
  }

  function bufferClone(buf) {
    if (buf.slice) {
      return buf.slice(0)
    } else {
      var view = new Uint8Array(buf.byteLength)
      view.set(new Uint8Array(buf))
      return view.buffer
    }
  }

  function Body() {
    this.bodyUsed = false

    this._initBody = function(body) {
      this._bodyInit = body
      if (!body) {
        this._bodyText = ''
      } else if (typeof body === 'string') {
        this._bodyText = body
      } else if (support.blob && Blob.prototype.isPrototypeOf(body)) {
        this._bodyBlob = body
      } else if (support.formData && FormData.prototype.isPrototypeOf(body)) {
        this._bodyFormData = body
      } else if (support.searchParams && URLSearchParams.prototype.isPrototypeOf(body)) {
        this._bodyText = body.toString()
      } else if (support.arrayBuffer && support.blob && isDataView(body)) {
        this._bodyArrayBuffer = bufferClone(body.buffer)
        // IE 10-11 can't handle a DataView body.
        this._bodyInit = new Blob([this._bodyArrayBuffer])
      } else if (support.arrayBuffer && (ArrayBuffer.prototype.isPrototypeOf(body) || isArrayBufferView(body))) {
        this._bodyArrayBuffer = bufferClone(body)
      } else {
        throw new Error('unsupported BodyInit type')
      }

      if (!this.headers.get('content-type')) {
        if (typeof body === 'string') {
          this.headers.set('content-type', 'text/plain;charset=UTF-8')
        } else if (this._bodyBlob && this._bodyBlob.type) {
          this.headers.set('content-type', this._bodyBlob.type)
        } else if (support.searchParams && URLSearchParams.prototype.isPrototypeOf(body)) {
          this.headers.set('content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        }
      }
    }

    if (support.blob) {
      this.blob = function() {
        var rejected = consumed(this)
        if (rejected) {
          return rejected
        }

        if (this._bodyBlob) {
          return Promise.resolve(this._bodyBlob)
        } else if (this._bodyArrayBuffer) {
          return Promise.resolve(new Blob([this._bodyArrayBuffer]))
        } else if (this._bodyFormData) {
          throw new Error('could not read FormData body as blob')
        } else {
          return Promise.resolve(new Blob([this._bodyText]))
        }
      }

      this.arrayBuffer = function() {
        if (this._bodyArrayBuffer) {
          return consumed(this) || Promise.resolve(this._bodyArrayBuffer)
        } else {
          return this.blob().then(readBlobAsArrayBuffer)
        }
      }
    }

    this.text = function() {
      var rejected = consumed(this)
      if (rejected) {
        return rejected
      }

      if (this._bodyBlob) {
        return readBlobAsText(this._bodyBlob)
      } else if (this._bodyArrayBuffer) {
        return Promise.resolve(readArrayBufferAsText(this._bodyArrayBuffer))
      } else if (this._bodyFormData) {
        throw new Error('could not read FormData body as text')
      } else {
        return Promise.resolve(this._bodyText)
      }
    }

    if (support.formData) {
      this.formData = function() {
        return this.text().then(decode)
      }
    }

    this.json = function() {
      return this.text().then(JSON.parse)
    }

    return this
  }

  // HTTP methods whose capitalization should be normalized
  var methods = ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT']

  function normalizeMethod(method) {
    var upcased = method.toUpperCase()
    return (methods.indexOf(upcased) > -1) ? upcased : method
  }

  function Request(input, options) {
    options = options || {}
    var body = options.body

    if (input instanceof Request) {
      if (input.bodyUsed) {
        throw new TypeError('Already read')
      }
      this.url = input.url
      this.credentials = input.credentials
      if (!options.headers) {
        this.headers = new Headers(input.headers)
      }
      this.method = input.method
      this.mode = input.mode
      if (!body && input._bodyInit != null) {
        body = input._bodyInit
        input.bodyUsed = true
      }
    } else {
      this.url = String(input)
    }

    this.credentials = options.credentials || this.credentials || 'omit'
    if (options.headers || !this.headers) {
      this.headers = new Headers(options.headers)
    }
    this.method = normalizeMethod(options.method || this.method || 'GET')
    this.mode = options.mode || this.mode || null
    this.referrer = null

    if ((this.method === 'GET' || this.method === 'HEAD') && body) {
      throw new TypeError('Body not allowed for GET or HEAD requests')
    }
    this._initBody(body)
  }

  Request.prototype.clone = function() {
    return new Request(this, { body: this._bodyInit })
  }

  function decode(body) {
    var form = new FormData()
    body.trim().split('&').forEach(function(bytes) {
      if (bytes) {
        var split = bytes.split('=')
        var name = split.shift().replace(/\+/g, ' ')
        var value = split.join('=').replace(/\+/g, ' ')
        form.append(decodeURIComponent(name), decodeURIComponent(value))
      }
    })
    return form
  }

  function parseHeaders(rawHeaders) {
    var headers = new Headers()
    rawHeaders.split(/\r?\n/).forEach(function(line) {
      var parts = line.split(':')
      var key = parts.shift().trim()
      if (key) {
        var value = parts.join(':').trim()
        headers.append(key, value)
      }
    })
    return headers
  }

  Body.call(Request.prototype)

  function Response(bodyInit, options) {
    if (!options) {
      options = {}
    }

    this.type = 'default'
    this.status = 'status' in options ? options.status : 200
    this.ok = this.status >= 200 && this.status < 300
    this.statusText = 'statusText' in options ? options.statusText : 'OK'
    this.headers = new Headers(options.headers)
    this.url = options.url || ''
    this._initBody(bodyInit)
  }

  Body.call(Response.prototype)

  Response.prototype.clone = function() {
    return new Response(this._bodyInit, {
      status: this.status,
      statusText: this.statusText,
      headers: new Headers(this.headers),
      url: this.url
    })
  }

  Response.error = function() {
    var response = new Response(null, {status: 0, statusText: ''})
    response.type = 'error'
    return response
  }

  var redirectStatuses = [301, 302, 303, 307, 308]

  Response.redirect = function(url, status) {
    if (redirectStatuses.indexOf(status) === -1) {
      throw new RangeError('Invalid status code')
    }

    return new Response(null, {status: status, headers: {location: url}})
  }

  self.Headers = Headers
  self.Request = Request
  self.Response = Response

  self.fetch = function(input, init) {
    return new Promise(function(resolve, reject) {
      var request = new Request(input, init)
      var xhr = new XMLHttpRequest()

      xhr.onload = function() {
        var options = {
          status: xhr.status,
          statusText: xhr.statusText,
          headers: parseHeaders(xhr.getAllResponseHeaders() || '')
        }
        options.url = 'responseURL' in xhr ? xhr.responseURL : options.headers.get('X-Request-URL')
        var body = 'response' in xhr ? xhr.response : xhr.responseText
        resolve(new Response(body, options))
      }

      xhr.onerror = function() {
        reject(new TypeError('Network request failed'))
      }

      xhr.ontimeout = function() {
        reject(new TypeError('Network request failed'))
      }

      xhr.open(request.method, request.url, true)

      if (request.credentials === 'include') {
        xhr.withCredentials = true
      }

      if ('responseType' in xhr && support.blob) {
        xhr.responseType = 'blob'
      }

      request.headers.forEach(function(value, name) {
        xhr.setRequestHeader(name, value)
      })

      xhr.send(typeof request._bodyInit === 'undefined' ? null : request._bodyInit)
    })
  }
  self.fetch.polyfill = true
})(typeof self !== 'undefined' ? self : this);


/***/ })

},["./common/lib/xmodule/xmodule/assets/library_source_block/LibrarySourcedBlockPicker.jsx"])));
//# sourceMappingURL=LibrarySourcedBlockPicker.js.map