/* 
 HighlightTags Annotator Plugin v1.0 (https://github.com/lduarte1991/tags-annotator)
 Copyright (C) 2014 Luis F Duarte
 License: https://github.com/lduarte1991/tags-annotator/blob/master/LICENSE.rst
 
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License
 as published by the Free Software Foundation; either version 2
 of the License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
  
 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/
/*===============================================================================
  ===============================================================================
  ===============================================================================
  ===============================================================================
  ==============================================================================*/
/*
 * jQuery Plugin: Tokenizing Autocomplete Text Entry
 * Version 1.6.0
 *
 * Copyright (c) 2009 James Smith (http://loopj.com)
 * Licensed jointly under the GPL and MIT licenses,
 * choose which one suits your project best!
 *
 */

(function ($) {
// Default settings
var DEFAULT_SETTINGS = {
    // Search settings
    method: "GET",
    contentType: "json",
    queryParam: "q",
    searchDelay: 300,
    minChars: 1,
    propertyToSearch: "name",
    jsonContainer: null,

    // Display settings
    hintText: "Type in a search term",
    noResultsText: "Not Found. Hit ENTER to add a personal tag.",
    searchingText: "Searching...",
    deleteText: "&times;",
    animateDropdown: true,

    // Tokenization settings
    tokenLimit: null,
    tokenDelimiter: ",",
    preventDuplicates: false,

    // Output settings
    tokenValue: "id",

    // Prepopulation settings
    prePopulate: null,
    processPrePopulate: false,

    // Manipulation settings
    idPrefix: "token-input-",

    // Formatters
    resultsFormatter: function(item){ return "<li>" + item[this.propertyToSearch]+ "</li>" },
    tokenFormatter: function(item) { return "<li><p>" + item[this.propertyToSearch] + "</p></li>" },

    // Callbacks
    onResult: null,
    onAdd: null,
    onDelete: null,
    onReady: null
};

// Default classes to use when theming
var DEFAULT_CLASSES = {
    tokenList: "token-input-list",
    token: "token-input-token",
    tokenDelete: "token-input-delete-token",
    selectedToken: "token-input-selected-token",
    highlightedToken: "token-input-highlighted-token",
    dropdown: "token-input-dropdown",
    dropdownItem: "token-input-dropdown-item",
    dropdownItem2: "token-input-dropdown-item2",
    selectedDropdownItem: "token-input-selected-dropdown-item",
    inputToken: "token-input-input-token"
};

// Input box position "enum"
var POSITION = {
    BEFORE: 0,
    AFTER: 1,
    END: 2
};

// Keys "enum"
var KEY = {
    BACKSPACE: 8,
    TAB: 9,
    ENTER: 13,
    ESCAPE: 27,
    SPACE: 32,
    PAGE_UP: 33,
    PAGE_DOWN: 34,
    END: 35,
    HOME: 36,
    LEFT: 37,
    UP: 38,
    RIGHT: 39,
    DOWN: 40,
    NUMPAD_ENTER: 108,
    COMMA: 188
};

// Additional public (exposed) methods
var methods = {
    init: function(url_or_data_or_function, options) {
        var settings = $.extend({}, DEFAULT_SETTINGS, options || {});

        return this.each(function () {
            $(this).data("tokenInputObject", new $.TokenList(this, url_or_data_or_function, settings));
        });
    },
    clear: function() {
        this.data("tokenInputObject").clear();
        return this;
    },
    add: function(item) {
        this.data("tokenInputObject").add(item);
        return this;
    },
    remove: function(item) {
        this.data("tokenInputObject").remove(item);
        return this;
    },
    get: function() {
        return this.data("tokenInputObject").getTokens();
       }
}

// Expose the .tokenInput function to jQuery as a plugin
$.fn.tokenInput = function (method) {
    // Method calling and initialization logic
    if(methods[method]) {
        return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
    } else {
        return methods.init.apply(this, arguments);
    }
};

// TokenList class for each input
$.TokenList = function (input, url_or_data, settings) {
    //
    // Initialization
    //

    // Configure the data source
    if($.type(url_or_data) === "string" || $.type(url_or_data) === "function") {
        // Set the url to query against
        settings.url = url_or_data;

        // If the URL is a function, evaluate it here to do our initalization work
        var url = computeURL();

        // Make a smart guess about cross-domain if it wasn't explicitly specified
        if(settings.crossDomain === undefined) {
            if(url.indexOf("://") === -1) {
                settings.crossDomain = false;
            } else {
                settings.crossDomain = (location.href.split(/\/+/g)[1] !== url.split(/\/+/g)[1]);
            }
        }
    } else if(typeof(url_or_data) === "object") {
        // Set the local data to search through
        settings.local_data = url_or_data;
    }

    // Build class names
    if(settings.classes) {
        // Use custom class names
        settings.classes = $.extend({}, DEFAULT_CLASSES, settings.classes);
    } else if(settings.theme) {
        // Use theme-suffixed default class names
        settings.classes = {};
        $.each(DEFAULT_CLASSES, function(key, value) {
            settings.classes[key] = value + "-" + settings.theme;
        });
    } else {
        settings.classes = DEFAULT_CLASSES;
    }


    // Save the tokens
    var saved_tokens = [];

    // Keep track of the number of tokens in the list
    var token_count = 0;

    // Basic cache to save on db hits
    var cache = new $.TokenList.Cache();

    // Keep track of the timeout, old vals
    var timeout;
    var input_val;

    // Create a new text input an attach keyup events
    var input_box = $("<input type=\"text\"  autocomplete=\"off\">")
        .css({
            outline: "none"
        })
        .attr("id", settings.idPrefix + input.id)
        .focus(function () {
            if (settings.tokenLimit === null || settings.tokenLimit !== token_count) {
                show_dropdown_hint();
            }
        })
        .blur(function () {
            hide_dropdown();
            $(this).val("");
        })
        .bind("keyup keydown blur update", resize_input)
        .keydown(function (event) {
            var previous_token;
            var next_token;

            switch(event.keyCode) {
                case KEY.LEFT:
                case KEY.RIGHT:
                case KEY.UP:
                case KEY.DOWN:
                    if(!$(this).val()) {
                        previous_token = input_token.prev();
                        next_token = input_token.next();

                        if((previous_token.length && previous_token.get(0) === selected_token) || (next_token.length && next_token.get(0) === selected_token)) {
                            // Check if there is a previous/next token and it is selected
                            if(event.keyCode === KEY.LEFT || event.keyCode === KEY.UP) {
                                deselect_token($(selected_token), POSITION.BEFORE);
                            } else {
                                deselect_token($(selected_token), POSITION.AFTER);
                            }
                        } else if((event.keyCode === KEY.LEFT || event.keyCode === KEY.UP) && previous_token.length) {
                            // We are moving left, select the previous token if it exists
                            select_token($(previous_token.get(0)));
                        } else if((event.keyCode === KEY.RIGHT || event.keyCode === KEY.DOWN) && next_token.length) {
                            // We are moving right, select the next token if it exists
                            select_token($(next_token.get(0)));
                        }
                    } else {
                        var dropdown_item = null;

                        if(event.keyCode === KEY.DOWN || event.keyCode === KEY.RIGHT) {
                            dropdown_item = $(selected_dropdown_item).next();
                        } else {
                            dropdown_item = $(selected_dropdown_item).prev();
                        }

                        if(dropdown_item.length) {
                            select_dropdown_item(dropdown_item);
                        }
                        return false;
                    }
                    break;

                case KEY.BACKSPACE:
                    previous_token = input_token.prev();

                    if(!$(this).val().length) {
                        if(selected_token) {
                            delete_token($(selected_token));
                            hidden_input.change();
                        } else if(previous_token.length) {
                            select_token($(previous_token.get(0)));
                        }

                        return false;
                    } else if($(this).val().length === 1) {
                        hide_dropdown();
                    } else {
                        // set a timeout just long enough to let this function finish.
                        setTimeout(function(){do_search();}, 5);
                    }
                    break;

                case KEY.TAB:
                case KEY.ENTER:
                case KEY.NUMPAD_ENTER:
                case KEY.COMMA:
                  if(selected_dropdown_item) {
                    add_token($(selected_dropdown_item).data("tokeninput"));
                    // this allows for tags to be color-coded based on instructor set-up
                    annotator.publish("colorEditorTags")
                    hidden_input.change();
                    return false;
                  } else{
                    add_token({id:$(this).val(), name:$(this).val()});
                    hidden_input.change();
                  } 
                  break;

                case KEY.ESCAPE:
                  hide_dropdown();
                  return true;

                default:
                    if(String.fromCharCode(event.which)) {
                        // set a timeout just long enough to let this function finish.
                        setTimeout(function(){do_search();}, 5);
                    }
                    break;
            }
        });

    // Keep a reference to the original input box
    var hidden_input = $(input)
                           .hide()
                           .val("")
                           .focus(function () {
                               input_box.focus();
                           })
                           .blur(function () {
                               input_box.blur();
                           });

    // Keep a reference to the selected token and dropdown item
    var selected_token = null;
    var selected_token_index = 0;
    var selected_dropdown_item = null;

    // The list to store the token items in
    var token_list = $("<ul />")
        .addClass(settings.classes.tokenList)
        .click(function (event) {
            var li = $(event.target).closest("li");
            if(li && li.get(0) && $.data(li.get(0), "tokeninput")) {
                toggle_select_token(li);
            } else {
                // Deselect selected token
                if(selected_token) {
                    deselect_token($(selected_token), POSITION.END);
                }

                // Focus input box
                input_box.focus();
            }
        })
        .mouseover(function (event) {
            var li = $(event.target).closest("li");
            if(li && selected_token !== this) {
                li.addClass(settings.classes.highlightedToken);
            }
        })
        .mouseout(function (event) {
            var li = $(event.target).closest("li");
            if(li && selected_token !== this) {
                li.removeClass(settings.classes.highlightedToken);
            }
        })
        .insertBefore(hidden_input);

    // The token holding the input box
    var input_token = $("<li />")
        .addClass(settings.classes.inputToken)
        .appendTo(token_list)
        .append(input_box);

    // The list to store the dropdown items in
    var dropdown = $("<div>")
        .addClass(settings.classes.dropdown)
        .appendTo("body")
        .hide();

    // Magic element to help us resize the text input
    var input_resizer = $("<tester/>")
        .insertAfter(input_box)
        .css({
            position: "absolute",
            top: -9999,
            left: -9999,
            width: "auto",
            fontSize: input_box.css("fontSize"),
            fontFamily: input_box.css("fontFamily"),
            fontWeight: input_box.css("fontWeight"),
            letterSpacing: input_box.css("letterSpacing"),
            whiteSpace: "nowrap"
        });

    // Pre-populate list if items exist
    hidden_input.val("");
    var li_data = settings.prePopulate || hidden_input.data("pre");
    if(settings.processPrePopulate && $.isFunction(settings.onResult)) {
        li_data = settings.onResult.call(hidden_input, li_data);
    }
    if(li_data && li_data.length) {
        $.each(li_data, function (index, value) {
            insert_token(value);
            checkTokenLimit();
        });
    }

    // Initialization is done
    if($.isFunction(settings.onReady)) {
        settings.onReady.call();
    }

    //
    // Public functions
    //

    this.clear = function() {
        token_list.children("li").each(function() {
            if ($(this).children("input").length === 0) {
                delete_token($(this));
            }
        });
    }

    this.add = function(item) {
        add_token(item);
    }

    this.remove = function(item) {
        token_list.children("li").each(function() {
            if ($(this).children("input").length === 0) {
                var currToken = $(this).data("tokeninput");
                var match = true;
                for (var prop in item) {
                    if (item[prop] !== currToken[prop]) {
                        match = false;
                        break;
                    }
                }
                if (match) {
                    delete_token($(this));
                }
            }
        });
    }
    
    this.getTokens = function() {
           return saved_tokens;
       }

    //
    // Private functions
    //

    function checkTokenLimit() {
        if(settings.tokenLimit !== null && token_count >= settings.tokenLimit) {
            input_box.hide();
            hide_dropdown();
            return;
        }
    }

    function resize_input() {
        if(input_val === (input_val = input_box.val())) {return;}

        // Enter new content into resizer and resize input accordingly
        var escaped = input_val.replace(/&/g, '&amp;').replace(/\s/g,' ').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        input_resizer.html(escaped);
        input_box.width(input_resizer.width() + 30);
    }

    function is_printable_character(keycode) {
        return ((keycode >= 48 && keycode <= 90) ||     // 0-1a-z
                (keycode >= 96 && keycode <= 111) ||    // numpad 0-9 + - / * .
                (keycode >= 186 && keycode <= 192) ||   // ; = , - . / ^
                (keycode >= 219 && keycode <= 222));    // ( \ ) '
    }

    // Inner function to a token to the list
    function insert_token(item) {
        var this_token = settings.tokenFormatter(item);
        this_token = $(this_token)
          .addClass(settings.classes.token)
          .insertBefore(input_token);

        // The 'delete token' button
        $("<span>" + settings.deleteText + "</span>")
            .addClass(settings.classes.tokenDelete)
            .appendTo(this_token)
            .click(function () {
                delete_token($(this).parent());
                hidden_input.change();
                return false;
            });

        // Store data on the token
        var token_data = {"id": item.id};
        token_data[settings.propertyToSearch] = item[settings.propertyToSearch];
        $.data(this_token.get(0), "tokeninput", item);

        // Save this token for duplicate checking
        saved_tokens = saved_tokens.slice(0,selected_token_index).concat([token_data]).concat(saved_tokens.slice(selected_token_index));
        selected_token_index++;

        // Update the hidden input
        update_hidden_input(saved_tokens, hidden_input);

        token_count += 1;

        // Check the token limit
        if(settings.tokenLimit !== null && token_count >= settings.tokenLimit) {
            input_box.hide();
            hide_dropdown();
        }

        return this_token;
    }

    // Add a token to the token list based on user input
    function add_token (item) {
        var callback = settings.onAdd;

        // See if the token already exists and select it if we don't want duplicates
        if(token_count > 0 && settings.preventDuplicates) {
            var found_existing_token = null;
            token_list.children().each(function () {
                var existing_token = $(this);
                var existing_data = $.data(existing_token.get(0), "tokeninput");
                if(existing_data && existing_data.id === item.id) {
                    found_existing_token = existing_token;
                    return false;
                }
            });

            if(found_existing_token) {
                select_token(found_existing_token);
                input_token.insertAfter(found_existing_token);
                input_box.focus();
                return;
            }
        }

        // Insert the new tokens
        if(settings.tokenLimit == null || token_count < settings.tokenLimit) {
            insert_token(item);
            checkTokenLimit();
        }

        // Clear input box
        input_box.val("");

        // Don't show the help dropdown, they've got the idea
        hide_dropdown();

        // Execute the onAdd callback if defined
        if($.isFunction(callback)) {
            callback.call(hidden_input,item);
        }
    }

    // Select a token in the token list
    function select_token (token) {
        token.addClass(settings.classes.selectedToken);
        selected_token = token.get(0);

        // Hide input box
        input_box.val("");

        // Hide dropdown if it is visible (eg if we clicked to select token)
        hide_dropdown();
    }

    // Deselect a token in the token list
    function deselect_token (token, position) {
        token.removeClass(settings.classes.selectedToken);
        selected_token = null;

        if(position === POSITION.BEFORE) {
            input_token.insertBefore(token);
            selected_token_index--;
        } else if(position === POSITION.AFTER) {
            input_token.insertAfter(token);
            selected_token_index++;
        } else {
            input_token.appendTo(token_list);
            selected_token_index = token_count;
        }

        // Show the input box and give it focus again
        input_box.focus();
    }

    // Toggle selection of a token in the token list
    function toggle_select_token(token) {
        var previous_selected_token = selected_token;

        if(selected_token) {
            deselect_token($(selected_token), POSITION.END);
        }

        if(previous_selected_token === token.get(0)) {
            deselect_token(token, POSITION.END);
        } else {
            select_token(token);
        }
    }

    // Delete a token from the token list
    function delete_token (token) {
        // Remove the id from the saved list
        var token_data = $.data(token.get(0), "tokeninput");
        var callback = settings.onDelete;

        var index = token.prevAll().length;
        if(index > selected_token_index) index--;

        // Delete the token
        token.remove();
        selected_token = null;

        // Show the input box and give it focus again
        input_box.focus();

        // Remove this token from the saved list
        saved_tokens = saved_tokens.slice(0,index).concat(saved_tokens.slice(index+1));
        if(index < selected_token_index) selected_token_index--;

        // Update the hidden input
        update_hidden_input(saved_tokens, hidden_input);

        token_count -= 1;

        if(settings.tokenLimit !== null) {
            input_box
                .show()
                .val("")
                .focus();
        }

        // Execute the onDelete callback if defined
        if($.isFunction(callback)) {
            callback.call(hidden_input,token_data);
        }
    }

    // Update the hidden input box value
    function update_hidden_input(saved_tokens, hidden_input) {
        var token_values = $.map(saved_tokens, function (el) {
            return el[settings.tokenValue];
        });
        hidden_input.val(token_values.join(settings.tokenDelimiter));

    }

    // Hide and clear the results dropdown
    function hide_dropdown () {
        dropdown.hide().empty();
        selected_dropdown_item = null;
    }

    function show_dropdown() {
        dropdown
            .css({
                position: "absolute",
                top: $(token_list).offset().top + $(token_list).outerHeight(),
                left: $(token_list).offset().left,
                zindex: 999
            })
            .show();
    }

    function show_dropdown_searching () {
        if(settings.searchingText) {
            dropdown.html("<p>"+settings.searchingText+"</p>");
            show_dropdown();
        }
    }

    function show_dropdown_hint () {
        if(settings.hintText) {
            dropdown.html("<p>"+settings.hintText+"</p>");
            show_dropdown();
        }
    }

    // Highlight the query part of the search term
    function highlight_term(value, term) {
        return value.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + term + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "<b>$1</b>");
    }
    
    function find_value_and_highlight_term(template, value, term) {
        return template.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + value + ")(?![^<>]*>)(?![^&;]+;)", "g"), highlight_term(value, term));
    }

    // Populate the results dropdown with some results
    function populate_dropdown (query, results) {
        if(results && results.length) {
            dropdown.empty();
            var dropdown_ul = $("<ul>")
                .appendTo(dropdown)
                .mouseover(function (event) {
                    select_dropdown_item($(event.target).closest("li"));
                })
                .mousedown(function (event) {
                    add_token($(event.target).closest("li").data("tokeninput"));
                    hidden_input.change();
                    return false;
                })
                .hide();

            $.each(results, function(index, value) {
                var this_li = settings.resultsFormatter(value);
                
                this_li = find_value_and_highlight_term(this_li ,value[settings.propertyToSearch], query);            
                
                this_li = $(this_li).appendTo(dropdown_ul);
                
                if(index % 2) {
                    this_li.addClass(settings.classes.dropdownItem);
                } else {
                    this_li.addClass(settings.classes.dropdownItem2);
                }

                if(index === 0) {
                    select_dropdown_item(this_li);
                }

                $.data(this_li.get(0), "tokeninput", value);
            });

            show_dropdown();

            if(settings.animateDropdown) {
                dropdown_ul.slideDown("fast");
            } else {
                dropdown_ul.show();
            }
        } else {
            if(settings.noResultsText) {
                dropdown.html("<p>"+settings.noResultsText+"</p>");
                show_dropdown();
            }
        }
    }

    // Highlight an item in the results dropdown
    function select_dropdown_item (item) {
        if(item) {
            if(selected_dropdown_item) {
                deselect_dropdown_item($(selected_dropdown_item));
            }

            item.addClass(settings.classes.selectedDropdownItem);
            selected_dropdown_item = item.get(0);
        }
    }

    // Remove highlighting from an item in the results dropdown
    function deselect_dropdown_item (item) {
        item.removeClass(settings.classes.selectedDropdownItem);
        selected_dropdown_item = null;
    }

    // Do a search and show the "searching" dropdown if the input is longer
    // than settings.minChars
    function do_search() {
        var query = input_box.val().toLowerCase();

        if(query && query.length) {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.AFTER);
            }

            if(query.length >= settings.minChars) {
                show_dropdown_searching();
                clearTimeout(timeout);

                timeout = setTimeout(function(){
                    run_search(query);
                }, settings.searchDelay);
            } else {
                hide_dropdown();
            }
        }
    }

    // Do the actual search
    function run_search(query) {
        var cache_key = query + computeURL();
        var cached_results = cache.get(cache_key);
        if(cached_results) {
            populate_dropdown(query, cached_results);
        } else {
            // Are we doing an ajax search or local data search?
            if(settings.url) {
                var url = computeURL();
                // Extract exisiting get params
                var ajax_params = {};
                ajax_params.data = {};
                if(url.indexOf("?") > -1) {
                    var parts = url.split("?");
                    ajax_params.url = parts[0];

                    var param_array = parts[1].split("&");
                    $.each(param_array, function (index, value) {
                        var kv = value.split("=");
                        ajax_params.data[kv[0]] = kv[1];
                    });
                } else {
                    ajax_params.url = url;
                }

                // Prepare the request
                ajax_params.data[settings.queryParam] = query;
                ajax_params.type = settings.method;
                ajax_params.dataType = settings.contentType;
                if(settings.crossDomain) {
                    ajax_params.dataType = "jsonp";
                }

                // Attach the success callback
                ajax_params.success = function(results) {
                  if($.isFunction(settings.onResult)) {
                      results = settings.onResult.call(hidden_input, results);
                  }
                  cache.add(cache_key, settings.jsonContainer ? results[settings.jsonContainer] : results);

                  // only populate the dropdown if the results are associated with the active search query
                  if(input_box.val().toLowerCase() === query) {
                      populate_dropdown(query, settings.jsonContainer ? results[settings.jsonContainer] : results);
                  }
                };

                // Make the request
                $.ajax(ajax_params);
            } else if(settings.local_data) {
                // Do the search through local data
                var results = $.grep(settings.local_data, function (row) {
                    return row[settings.propertyToSearch].toLowerCase().indexOf(query.toLowerCase()) > -1;
                });

                if($.isFunction(settings.onResult)) {
                    results = settings.onResult.call(hidden_input, results);
                }
                cache.add(cache_key, results);
                populate_dropdown(query, results);
            }
        }
    }

    // compute the dynamic URL
    function computeURL() {
        var url = settings.url;
        if(typeof settings.url == 'function') {
            url = settings.url.call();
        }
        return url;
    }
};

// Really basic cache for the results
$.TokenList.Cache = function (options) {
    var settings = $.extend({
        max_size: 500
    }, options);

    var data = {};
    var size = 0;

    var flush = function () {
        data = {};
        size = 0;
    };

    this.add = function (query, results) {
        if(size > settings.max_size) {
            flush();
        }

        if(!data[query]) {
            size += 1;
        }

        data[query] = results;
    };

    this.get = function (query) {
        return data[query];
    };
};
}(jQuery));

var _ref,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

Annotator.Plugin.HighlightTags = (function(_super) {
    __extends(HighlightTags, _super);
    
    HighlightTags.prototype.options = null;
    
    
    function HighlightTags(element,options) {
        this.pluginSubmit = __bind(this.pluginSubmit, this);
        this.updateViewer = __bind(this.updateViewer, this);
        this.colorize = __bind(this.colorize, this);
        this.updateField = __bind(this.updateField, this);
        this.externalCall = __bind(this.externalCall, this);
        this.colorizeEditorTags = __bind(this.colorizeEditorTags, this);

        this.options = options;
        _ref = HighlightTags.__super__.constructor.apply(this, arguments);
        return _ref;
    }
    
    //example variables to be used to receive input in the annotator view
    HighlightTags.prototype.field = null;
    HighlightTags.prototype.input = null;
    HighlightTags.prototype.colors = null;
    HighlightTags.prototype.isFirstTime = true;
    
    //this function will initialize the plug in. Create your fields here in the editor and viewer.
    HighlightTags.prototype.pluginInit = function() {
        console.log("HighlightTags-pluginInit");
        //Check that annotator is working
        if (!Annotator.supported()) {
            return; 
        }
        
        this.field = this.annotator.editor.addField({
            type: 'input',
            load: this.updateField,
            submit: this.pluginSubmit,
        });
        
        
        
        var self = this;
        
        var newfield = Annotator.$('<li class="annotator-item">'+ "<div><input placeholder =\"Add tags\" type=\"text\" id=\"tag-input\" name=\"tags\" /></div>"+'</li>');
                Annotator.$(self.field).replaceWith(newfield);
                self.field=newfield[0];
                
                //
        
            
        //-- Viewer
        var newview = this.annotator.viewer.addField({
            load: this.updateViewer,
        });
        
        this.colors = this.getHighlightTags();
        var self = this;

        // all of these need time for the annotations database to respond
        this.annotator.subscribe('annotationsLoaded', function(){setTimeout(function(){self.colorize()}, 1000)});
        this.annotator.subscribe('annotationUpdated', function(){setTimeout(function(){self.colorize()}, 1000)});
        this.annotator.subscribe('flaggedAnnotation', this.updateViewer);
        this.annotator.subscribe('annotationCreated', function(){setTimeout(function(){self.colorize()}, 1000)});
        this.annotator.subscribe('externalCallToHighlightTags', function(){setTimeout(function(){self.externalCall()}, 1000)});
        this.annotator.subscribe('colorEditorTags', this.colorizeEditorTags);
    };
    
    HighlightTags.prototype.getHighlightTags = function(){
        if (typeof this.options.tag != 'undefined') {
            var self = this;
            var final = {},    prelim = this.options.tag.split(",");
            prelim.forEach(function(item){
                var temp = item.split(":");
                final[temp[0]] = self.getRGB(temp[1]);
            });
            return final;
        }
        return {};
    }
    
    HighlightTags.prototype.getRGB = function(item){
        function getColorValues( color ){
    var values = { red:null, green:null, blue:null, alpha:null };
    if( typeof color == 'string' ){
        /* hex */
        if( color.indexOf('#') === 0 ){
            color = color.substr(1)
            if( color.length == 3 )
                values = {
                    red:   parseInt( color[0]+color[0], 16 ),
                    green: parseInt( color[1]+color[1], 16 ),
                    blue:  parseInt( color[2]+color[2], 16 ),
                    alpha: .3
                }
            else
                values = {
                    red:   parseInt( color.substr(0,2), 16 ),
                    green: parseInt( color.substr(2,2), 16 ),
                    blue:  parseInt( color.substr(4,2), 16 ),
                    alpha: .3
                }
        /* rgb */
        }else if( color.indexOf('rgb(') === 0 ){
            var pars = color.indexOf(',');
            values = {
                red:   parseInt(color.substr(4,pars)),
                green: parseInt(color.substr(pars+1,color.indexOf(',',pars))),
                blue:  parseInt(color.substr(color.indexOf(',',pars+1)+1,color.indexOf(')'))),
                alpha: .3
            }
        /* rgba */
        }else if( color.indexOf('rgba(') === 0 ){
            var pars = color.indexOf(','),
                repars = color.indexOf(',',pars+1);
            values = {
                red:   parseInt(color.substr(5,pars)),
                green: parseInt(color.substr(pars+1,repars)),
                blue:  parseInt(color.substr(color.indexOf(',',pars+1)+1,color.indexOf(',',repars))),
                alpha: parseFloat(color.substr(color.indexOf(',',repars+1)+1,color.indexOf(')')))
            }
        /* verbous */
        }else{
            var stdCol = { acqua:'#0ff',   teal:'#008080',   blue:'#00f',      navy:'#000080',
                           yellow:'#ff0',  olive:'#808000',  lime:'#0f0',      green:'#008000',
                           fuchsia:'#f0f', purple:'#800080', red:'#f00',       maroon:'#800000',
                           white:'#fff',   gray:'#808080',   silver:'#c0c0c0', black:'#000' };
            if( stdCol[color]!=undefined )
                values = getColorValues(stdCol[color]);
        }
    }
    return values
}
        return getColorValues(item)
    }
    
    HighlightTags.prototype.colorize = function() {
        
        var annotations = Array.prototype.slice.call($(".annotator-hl"));
        for (annNum = 0; annNum < annotations.length; ++annNum) {
            var anns = $.data(annotations[annNum],"annotation");
            if (typeof anns.tags !== "undefined" && anns.tags.length == 0) {
                
                // image annotations should not change the background of the highlight
                // only the border so as not to block the image behind it.
                if (anns.media !== "image") {
                    $(annotations[annNum]).css("background-color", "");
                } else {
                    $(annotations[annNum]).css("border", "2px solid rgb(255, 255, 255)");
                    $(annotations[annNum]).css("outline", "2px solid rgb(0, 0, 0)");
                }
            }

            if (typeof anns.tags !== "undefined" && this.colors !== {}) {
                
                for (var index = 0; index < anns.tags.length; ++index) {
                    if (anns.tags[index].indexOf("flagged-") == -1) {
                        if (typeof this.colors[anns.tags[index]] !== "undefined") {
                            var finalcolor = this.colors[anns.tags[index]];
                            // if it's a text change the background
                            if (anns.media !== "image") {
                                $(annotations[annNum]).css(
                                    "background", 
                                    // last value, 0.3 is the standard highlight opacity for annotator
                                    "rgba(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ", 0.3)"
                                );
                            } 
                            // if it's an image change the dark border/outline leave the white one as is
                            else {
                                $(annotations[annNum]).css(
                                    "outline",
                                    "2px solid rgb(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ")"
                                );
                            }
                        } else {
                            // if the last tag was not predetermined by instrutor background should go back to default
                            if (anns.media !== "image") {
                                $(annotations[annNum]).css(
                                    "background", 
                                    // returns the value to the inherited value without the above
                                    ""
                                );
                            }
                        }
                    }
                }
                
            } else {
                // if there are no tags or predefined colors, keep the background at default
                if (anns.media !== "image") {
                   $(annotations[annNum]).css("background","");
                }
            }
        }
        
        this.annotator.publish('colorizeCompleted');
    }
    
    HighlightTags.prototype.updateField = function(field, annotation) {
        // the first time that this plug in runs, the predetermined instructor tags are
        // added and stored for the dropdown list
        if(this.isFirstTime) {
            var tags = this.options.tag.split(",");
            var tokensavailable = [];

            // tags are given the structure that the dropdown/token function requires
            tags.forEach (function(tagnames) {
                lonename = tagnames.split(":");
                tokensavailable.push({'id': lonename[0], 'name': lonename[0]});
            });

            // they are then added to the appropriate input for tags in annotator
            $("#tag-input").tokenInput(tokensavailable);
            this.isFirstTime = false;
        }

        $('#token-input-tag-input').attr('placeholder', 'Add tags...');
        $('#tag-input').tokenInput('clear');            
        
        // loops through the tags already in the annotation and "add" them to this annotation
        if (typeof annotation.tags !== "undefined") {
            for (tagnum = 0; tagnum < annotation.tags.length; tagnum++) {
                var n = annotation.tags[tagnum];
                if (typeof this.annotator.plugins["HighlightTags"] !== 'undefined') {
                    // if there are flags, we must ignore them
                    if (annotation.tags[tagnum].indexOf("flagged-") == -1) {
                        $('#tag-input').tokenInput('add',{'id':n,'name':n});
                    }
                } else {
                    $('#tag-input').tokenInput('add', {'id': n, 'name': n});
                }
            }
        }
        this.colorizeEditorTags();
    }

    // this function adds the appropriate color to the tag divs for each annotation
    HighlightTags.prototype.colorizeEditorTags = function() {
        var self = this;
        $.each($('.annotator-editor .token-input-token'), function(key, tagdiv) {
            // default colors are black for text and the original powder blue (already default)
            var rgbColor = "";
            var textColor = "color:#000;";
            var par = $(tagdiv).find("p");

            // if the tag has a predetermined color attached to it, 
            // then it changes the background and turns text white
            if (typeof self.colors[par.html()] !== "undefined") {
                var finalcolor = self.colors[par.html()];
                rgbColor = "background-color:rgba(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ", 0.5);";
                textColor = "color:#fff;";
            }

            // note that to change the text color you must change it in the paragraph tag, not the div
            $(tagdiv).attr('style', rgbColor);
            par.attr('style', textColor);
        });    
    }
    
    // The following function is run when a person hits submit.
    HighlightTags.prototype.pluginSubmit = function(field, annotation) {
        var tokens = Array.prototype.slice.call($(".token-input-input-token").parent().find('.token-input-token'));
        var arr = [];
        tokens.forEach(function(element){
            tag = element.firstChild.firstChild;
            arr.push(tag.nodeValue);
        });
        annotation.tags = arr;
    }

    // The following allows you to edit the annotation popup when the viewer has already
    // hit submit and is just viewing the annotation.
    HighlightTags.prototype.updateViewer = function(field, annotation) {
        if (typeof annotation.tags != "undefined") {
            
            // if there are no tags, the space for tags in the pop up is removed and function ends
            if (annotation.tags.length == 0) {
                $(field).remove();
                return;
            }

            // otherwise we prepare to loop through them
            var nonFlagTags = true;
            var tokenList = "<ul class=\"token-input-list\">";

            for (tagnum = 0; tagnum < annotation.tags.length; ++tagnum){
                if (typeof this.annotator.plugins["Flagging"] !== 'undefined') {
                    // once again we ingore flags
                    if (annotation.tags[tagnum].indexOf("flagged-") == -1) {
                        
                        // once again, defaults are black for text and powder blue default from token function
                        var rgbColor = "";
                        var textColor = "#000";

                        // if there is a color associated with the tag, it will change the background
                        // and change the text to white
                        if (typeof this.colors[annotation.tags[tagnum]] !== "undefined") {
                            var finalcolor = this.colors[annotation.tags[tagnum]];
                            rgbColor = "style=\"background-color:rgba(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ", 0.5);\"";
                            textColor = "#fff";
                        }

                        // note: to change text color you need to do it in the paragrph tag not the div
                        tokenList += "<li class=\"token-input-token\"" + rgbColor + "><p style=\"color: " + textColor + ";\">"+ annotation.tags[tagnum]+"</p></span></li>";
                        nonFlagTags = false;
                    }
                } else {
                    tokenList += "<li class=\"token-input-token\"><p>"+ annotation.tags[tagnum]+"</p></span></li>";
                }
            }
            tokenList += "</ul>";
            $(field).append(tokenList);

            // the field for tags is removed also if all the tags ended up being flags
            if (nonFlagTags) {
                $(field).remove();
            }
            
        } else {
            $(field).remove();
        }
        this.annotator.publish("finishedDrawingTags");
    }
    
    // The following will call the colorize function during an external call and then return
    // an event signaling completion.
    HighlightTags.prototype.externalCall = function() {
        this.colorize();
        this.annotator.publish('finishedExternalCallToHighlightTags');
    }
    
    return HighlightTags;

})(Annotator.Plugin);
