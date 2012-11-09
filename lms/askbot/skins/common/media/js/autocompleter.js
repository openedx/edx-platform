/**
 * AutoCompleter Object, refactored closure style from
 * jQuery autocomplete plugin
 * @param {Object=} options Settings
 * @constructor
 */
var AutoCompleter = function(options) {

    /**
     * Default options for autocomplete plugin
     */
    var defaults = {
        autocompleteMultiple: true,
        multipleSeparator: ' ',//a single character
        inputClass: 'acInput',
        loadingClass: 'acLoading',
        resultsClass: 'acResults',
        selectClass: 'acSelect',
        queryParamName: 'q',
        limitParamName: 'limit',
        extraParams: {},
        lineSeparator: '\n',
        cellSeparator: '|',
        minChars: 2,
        maxItemsToShow: 10,
        delay: 400,
        useCache: true,
        maxCacheLength: 10,
        matchSubset: true,
        matchCase: false,
        matchInside: true,
        mustMatch: false,
        preloadData: false,
        selectFirst: false,
        stopCharRegex: /\s+/,
        selectOnly: false,
        formatItem: null,           // TBD
        onItemSelect: false,
        autoFill: false,
        filterResults: true,
        sortResults: true,
        sortFunction: false,
        onNoMatch: false
    };

    /**
     * Options dictionary
     * @type Object
     * @private
     */
    this.options = $.extend({}, defaults, options);

    /**
     * Cached data
     * @type Object
     * @private
     */
    this.cacheData_ = {};

    /**
     * Number of cached data items
     * @type number
     * @private
     */
    this.cacheLength_ = 0;

    /**
     * Class name to mark selected item
     * @type string
     * @private
     */
    this.selectClass_ = 'jquery-autocomplete-selected-item';

    /**
     * Handler to activation timeout
     * @type ?number
     * @private
     */
    this.keyTimeout_ = null;

    /**
     * Last key pressed in the input field (store for behavior)
     * @type ?number
     * @private
     */
    this.lastKeyPressed_ = null;

    /**
     * Last value processed by the autocompleter
     * @type ?string
     * @private
     */
    this.lastProcessedValue_ = null;

    /**
     * Last value selected by the user
     * @type ?string
     * @private
     */
    this.lastSelectedValue_ = null;

    /**
     * Is this autocompleter active?
     * @type boolean
     * @private
     */
    this.active_ = false;

    /**
     * Is it OK to finish on blur?
     * @type boolean
     * @private
     */
    this.finishOnBlur_ = true;

    this.options.minChars = parseInt(this.options.minChars, 10);
    if (isNaN(this.options.minChars) || this.options.minChars < 1) {
        this.options.minChars = 2;
    }

    this.options.maxItemsToShow = parseInt(this.options.maxItemsToShow, 10);
    if (isNaN(this.options.maxItemsToShow) || this.options.maxItemsToShow < 1) {
        this.options.maxItemsToShow = 10;
    }

    this.options.maxCacheLength = parseInt(this.options.maxCacheLength, 10);
    if (isNaN(this.options.maxCacheLength) || this.options.maxCacheLength < 1) {
        this.options.maxCacheLength = 10;
    }

    if (this.options['preloadData'] === true){
        this.fetchRemoteData('', function(){});
    }
};
inherits(AutoCompleter, WrappedElement);

AutoCompleter.prototype.decorate = function(element){

    /**
     * Init DOM elements repository
     */
    this._element = element;

    /**
     * Switch off the native autocomplete
     */
    this._element.attr('autocomplete', 'off');

    /**
     * Create DOM element to hold results
     */
    this._results = $('<div></div>').hide();
    if (this.options.resultsClass) {
        this._results.addClass(this.options.resultsClass);
    }
    this._results.css({
        position: 'absolute'
    });
    $('body').append(this._results);

    this.setEventHandlers();
};

AutoCompleter.prototype.setEventHandlers = function(){
    /**
     * Shortcut to self
     */
    var self = this;

    /**
     * Attach keyboard monitoring to $elem
     */
    self._element.keydown(function(e) {
        self.lastKeyPressed_ = e.keyCode;
        switch(self.lastKeyPressed_) {

            case 38: // up
                e.preventDefault();
                if (self.active_) {
                    self.focusPrev();
                } else {
                    self.activate();
                }
                return false;
            break;

            case 40: // down
                e.preventDefault();
                if (self.active_) {
                    self.focusNext();
                } else {
                    self.activate();
                }
                return false;
            break;

            case 9: // tab
            case 13: // return
                if (self.active_) {
                    e.preventDefault();
                    self.selectCurrent();
                    return false;
                }
            break;

            case 27: // escape
                if (self.active_) {
                    e.preventDefault();
                    self.finish();
                    return false;
                }
            break;

            default:
                self.activate();

        }
    });
    self._element.blur(function() {
        if (self.finishOnBlur_) {
            setTimeout(function() { self.finish(); }, 200);
        }
    });
};

AutoCompleter.prototype.position = function() {
    var offset = this._element.offset();
    this._results.css({
        top: offset.top + this._element.outerHeight(),
        left: offset.left
    });
};

AutoCompleter.prototype.cacheRead = function(filter) {
    var filterLength, searchLength, search, maxPos, pos;
    if (this.options.useCache) {
        filter = String(filter);
        filterLength = filter.length;
        if (this.options.matchSubset) {
            searchLength = 1;
        } else {
            searchLength = filterLength;
        }
        while (searchLength <= filterLength) {
            if (this.options.matchInside) {
                maxPos = filterLength - searchLength;
            } else {
                maxPos = 0;
            }
            pos = 0;
            while (pos <= maxPos) {
                search = filter.substr(0, searchLength);
                if (this.cacheData_[search] !== undefined) {
                    return this.cacheData_[search];
                }
                pos++;
            }
            searchLength++;
        }
    }
    return false;
};

AutoCompleter.prototype.cacheWrite = function(filter, data) {
    if (this.options.useCache) {
        if (this.cacheLength_ >= this.options.maxCacheLength) {
            this.cacheFlush();
        }
        filter = String(filter);
        if (this.cacheData_[filter] !== undefined) {
            this.cacheLength_++;
        }
        return this.cacheData_[filter] = data;
    }
    return false;
};

AutoCompleter.prototype.cacheFlush = function() {
    this.cacheData_ = {};
    this.cacheLength_ = 0;
};

AutoCompleter.prototype.callHook = function(hook, data) {
    var f = this.options[hook];
    if (f && $.isFunction(f)) {
        return f(data, this);
    }
    return false;
};

AutoCompleter.prototype.activate = function() {
    var self = this;
    var activateNow = function() {
        self.activateNow();
    };
    var delay = parseInt(this.options.delay, 10);
    if (isNaN(delay) || delay <= 0) {
        delay = 250;
    }
    if (this.keyTimeout_) {
        clearTimeout(this.keyTimeout_);
    }
    this.keyTimeout_ = setTimeout(activateNow, delay);
};

AutoCompleter.prototype.activateNow = function() {
    var value = this.getValue();
    if (value !== this.lastProcessedValue_ && value !== this.lastSelectedValue_) {
        if (value.length >= this.options.minChars) {
            this.active_ = true;
            this.lastProcessedValue_ = value;
            this.fetchData(value);
        }
    }
};

AutoCompleter.prototype.fetchData = function(value) {
    if (this.options.data) {
        this.filterAndShowResults(this.options.data, value);
    } else {
        var self = this;
        this.fetchRemoteData(value, function(remoteData) {
            self.filterAndShowResults(remoteData, value);
        });
    }
};

AutoCompleter.prototype.fetchRemoteData = function(filter, callback) {
    var data = this.cacheRead(filter);
    if (data) {
        callback(data);
    } else {
        var self = this;
        if (this._element){
            this._element.addClass(this.options.loadingClass);
        }
        var ajaxCallback = function(data) {
            var parsed = false;
            if (data !== false) {
                parsed = self.parseRemoteData(data);
                self.options.data = parsed;//cache data forever - E.F.
                self.cacheWrite(filter, parsed);
            }
            if (self._element){
                self._element.removeClass(self.options.loadingClass);
            }
            callback(parsed);
        };
        $.ajax({
            url: this.makeUrl(filter),
            success: ajaxCallback,
            error: function() {
                ajaxCallback(false);
            }
        });
    }
};

AutoCompleter.prototype.setOption = function(name, value){
    this.options[name] = value;
};

AutoCompleter.prototype.setExtraParam = function(name, value) {
    var index = $.trim(String(name));
    if (index) {
        if (!this.options.extraParams) {
            this.options.extraParams = {};
        }
        if (this.options.extraParams[index] !== value) {
            this.options.extraParams[index] = value;
            this.cacheFlush();
        }
    }
};

AutoCompleter.prototype.makeUrl = function(param) {
    var self = this;
    var url = this.options.url;
    var params = $.extend({}, this.options.extraParams);
    // If options.queryParamName === false, append query to url
    // instead of using a GET parameter
    if (this.options.queryParamName === false) {
        url += encodeURIComponent(param);
    } else {
        params[this.options.queryParamName] = param;
    }

    if (this.options.limitParamName && this.options.maxItemsToShow) {
        params[this.options.limitParamName] = this.options.maxItemsToShow;
    }

    var urlAppend = [];
    $.each(params, function(index, value) {
        urlAppend.push(self.makeUrlParam(index, value));
    });
    if (urlAppend.length) {
        url += url.indexOf('?') == -1 ? '?' : '&';
        url += urlAppend.join('&');
    }
    return url;
};

AutoCompleter.prototype.makeUrlParam = function(name, value) {
    return String(name) + '=' + encodeURIComponent(value);
};

/**
 * Sanitize CR and LF, then split into lines
 */
AutoCompleter.prototype.splitText = function(text) {
    return String(text).replace(/(\r\n|\r|\n)/g, '\n').split(this.options.lineSeparator);
};

AutoCompleter.prototype.parseRemoteData = function(remoteData) {
    var value, lines, i, j, data;
    var results = [];
    var lines = this.splitText(remoteData);
    for (i = 0; i < lines.length; i++) {
        var line = lines[i].split(this.options.cellSeparator);
        data = [];
        for (j = 0; j < line.length; j++) {
            data.push(unescape(line[j]));
        }
        value = data.shift();
        results.push({ value: unescape(value), data: data });
    }
    return results;
};

AutoCompleter.prototype.filterAndShowResults = function(results, filter) {
    this.showResults(this.filterResults(results, filter), filter);
};

AutoCompleter.prototype.filterResults = function(results, filter) {

    var filtered = [];
    var value, data, i, result, type, include;
    var regex, pattern, testValue;

    for (i = 0; i < results.length; i++) {
        result = results[i];
        type = typeof result;
        if (type === 'string') {
            value = result;
            data = {};
        } else if ($.isArray(result)) {
            value = result[0];
            data = result.slice(1);
        } else if (type === 'object') {
            value = result.value;
            data = result.data;
        }
        value = String(value);
        if (value > '') {
            if (typeof data !== 'object') {
                data = {};
            }
            if (this.options.filterResults) {
                pattern = String(filter);
                testValue = String(value);
                if (!this.options.matchCase) {
                    pattern = pattern.toLowerCase();
                    testValue = testValue.toLowerCase();
                }
                include = testValue.indexOf(pattern);
                if (this.options.matchInside) {
                    include = include > -1;
                } else {
                    include = include === 0;
                }
            } else {
                include = true;
            }
            if (include) {
                filtered.push({ value: value, data: data });
            }
        }
    }

    if (this.options.sortResults) {
        filtered = this.sortResults(filtered, filter);
    }

    if (this.options.maxItemsToShow > 0 && this.options.maxItemsToShow < filtered.length) {
        filtered.length = this.options.maxItemsToShow;
    }

    return filtered;

};

AutoCompleter.prototype.sortResults = function(results, filter) {
    var self = this;
    var sortFunction = this.options.sortFunction;
    if (!$.isFunction(sortFunction)) {
        sortFunction = function(a, b, f) {
            return self.sortValueAlpha(a, b, f);
        };
    }
    results.sort(function(a, b) {
        return sortFunction(a, b, filter);
    });
    return results;
};

AutoCompleter.prototype.sortValueAlpha = function(a, b, filter) {
    a = String(a.value);
    b = String(b.value);
    if (!this.options.matchCase) {
        a = a.toLowerCase();
        b = b.toLowerCase();
    }
    if (a > b) {
        return 1;
    }
    if (a < b) {
        return -1;
    }
    return 0;
};

AutoCompleter.prototype.showResults = function(results, filter) {
    var self = this;
    var $ul = $('<ul></ul>');
    var i, result, $li, extraWidth, first = false, $first = false;
    var numResults = results.length;
    for (i = 0; i < numResults; i++) {
        result = results[i];
        $li = $('<li>' + this.showResult(result.value, result.data) + '</li>');
        $li.data('value', result.value);
        $li.data('data', result.data);
        $li.click(function() {
            var $this = $(this);
            self.selectItem($this);
        }).mousedown(function() {
            self.finishOnBlur_ = false;
        }).mouseup(function() {
            self.finishOnBlur_ = true;
        });
        $ul.append($li);
        if (first === false) {
            first = String(result.value);
            $first = $li;
            $li.addClass(this.options.firstItemClass);
        }
        if (i == numResults - 1) {
            $li.addClass(this.options.lastItemClass);
        }
    }

    // Alway recalculate position before showing since window size or
    // input element location may have changed. This fixes #14
    this.position();

    this._results.html($ul).show();
    extraWidth = this._results.outerWidth() - this._results.width();
    this._results.width(this._element.outerWidth() - extraWidth);
    $('li', this._results).hover(
        function() { self.focusItem(this); },
        function() { /* void */ }
    );
    if (this.autoFill(first, filter)) {
        this.focusItem($first);
    }
};

AutoCompleter.prototype.showResult = function(value, data) {
    if ($.isFunction(this.options.showResult)) {
        return this.options.showResult(value, data);
    } else {
        return value;
    }
};

AutoCompleter.prototype.autoFill = function(value, filter) {
    var lcValue, lcFilter, valueLength, filterLength;
    if (this.options.autoFill && this.lastKeyPressed_ != 8) {
        lcValue = String(value).toLowerCase();
        lcFilter = String(filter).toLowerCase();
        valueLength = value.length;
        filterLength = filter.length;
        if (lcValue.substr(0, filterLength) === lcFilter) {
            this._element.val(value);
            this.selectRange(filterLength, valueLength);
            return true;
        }
    }
    return false;
};

AutoCompleter.prototype.focusNext = function() {
    this.focusMove(+1);
};

AutoCompleter.prototype.focusPrev = function() {
    this.focusMove(-1);
};

AutoCompleter.prototype.focusMove = function(modifier) {
    var i, $items = $('li', this._results);
    modifier = parseInt(modifier, 10);
    for (var i = 0; i < $items.length; i++) {
        if ($($items[i]).hasClass(this.selectClass_)) {
            this.focusItem(i + modifier);
            return;
        }
    }
    this.focusItem(0);
};

AutoCompleter.prototype.focusItem = function(item) {
    var $item, $items = $('li', this._results);
    if ($items.length) {
        $items.removeClass(this.selectClass_).removeClass(this.options.selectClass);
        if (typeof item === 'number') {
            item = parseInt(item, 10);
            if (item < 0) {
                item = 0;
            } else if (item >= $items.length) {
                item = $items.length - 1;
            }
            $item = $($items[item]);
        } else {
            $item = $(item);
        }
        if ($item) {
            $item.addClass(this.selectClass_).addClass(this.options.selectClass);
        }
    }
};

AutoCompleter.prototype.selectCurrent = function() {
    var $item = $('li.' + this.selectClass_, this._results);
    if ($item.length == 1) {
        this.selectItem($item);
    } else {
        this.finish();
    }
};

AutoCompleter.prototype.selectItem = function($li) {
    var value = $li.data('value');
    var data = $li.data('data');
    var displayValue = this.displayValue(value, data);
    this.lastProcessedValue_ = displayValue;
    this.lastSelectedValue_ = displayValue;

    this.setValue(displayValue);

    this.setCaret(displayValue.length);
    this.callHook('onItemSelect', { value: value, data: data });
    this.finish();
};

/**
 * @return {boolean} true if the symbol matches something that is
 *                   considered content and false otherwise
 * @param {string} symbol - a single char string
 */
AutoCompleter.prototype.isContentChar = function(symbol){
    if (symbol.match(this.options['stopCharRegex'])){
        return false;
    } else if (symbol === this.options['multipleSeparator']){
        return false;
    } else {
        return true;
    }
};

/**
 * takes value from the input box
 * and saves _selection_start and _selection_end coordinates
 * respects settings autocompleteMultiple and
 * multipleSeparator
 * @return {string} the current word in the 
 * autocompletable word
 */
AutoCompleter.prototype.getValue = function(){
    var sel = this._element.getSelection();
    var text = this._element.val();
    var pos = sel.start;//estimated start
    //find real start
    var start = pos;
    for (cpos = pos; cpos >= 0; cpos = cpos - 1){
        if (cpos === text.length){
            continue;
        }
        var symbol = text.charAt(cpos);
        if (!this.isContentChar(symbol)){
            break;
        }
        start = cpos;
    }
    //find real end
    var end = pos;
    for (cpos = pos; cpos < text.length; cpos = cpos + 1){
        if (cpos === 0){
            continue;
        }
        var symbol = text.charAt(cpos);
        if (!this.isContentChar(symbol)){
            break;
        }
        end = cpos;
    }
    this._selection_start = start;
    this._selection_end = end;
    return text.substring(start, end);
}

/** 
 * sets value of the input box
 * by replacing the previous selection
 * with the value from the autocompleter
 */
AutoCompleter.prototype.setValue = function(val){
    var prefix = this._element.val().substring(0, this._selection_start);
    var postfix = this._element.val().substring(this._selection_end + 1);
    this._element.val(prefix + val + postfix);
};

AutoCompleter.prototype.displayValue = function(value, data) {
    if ($.isFunction(this.options.displayValue)) {
        return this.options.displayValue(value, data);
    } else {
        return value;
    }
};

AutoCompleter.prototype.finish = function() {
    if (this.keyTimeout_) {
        clearTimeout(this.keyTimeout_);
    }
    if (this._element.val() !== this.lastSelectedValue_) {
        if (this.options.mustMatch) {
            this._element.val('');
        }
        this.callHook('onNoMatch');
    }
    this._results.hide();
    this.lastKeyPressed_ = null;
    this.lastProcessedValue_ = null;
    if (this.active_) {
        this.callHook('onFinish');
    }
    this.active_ = false;
};

AutoCompleter.prototype.selectRange = function(start, end) {
    var input = this._element.get(0);
    if (input.setSelectionRange) {
        input.focus();
        input.setSelectionRange(start, end);
    } else if (this.createTextRange) {
        var range = this.createTextRange();
        range.collapse(true);
        range.moveEnd('character', end);
        range.moveStart('character', start);
        range.select();
    }
};

AutoCompleter.prototype.setCaret = function(pos) {
    this.selectRange(pos, pos);
};

