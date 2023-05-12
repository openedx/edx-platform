// needs Markdown.Converter.js at the moment

(function() {
    // eslint-disable-next-line no-var
    var util = {},
        position = {},
        ui = {},
        doc = window.document,
        re = window.RegExp,
        nav = window.navigator,
        SETTINGS = {lineLength: 72},

        // Used to work around some browser bugs where we can't use feature testing.
        uaSniffed = {
            isIE: /msie/.test(nav.userAgent.toLowerCase()),
            isIE_5or6: /msie 6/.test(nav.userAgent.toLowerCase()) || /msie 5/.test(nav.userAgent.toLowerCase()),
            isOpera: /opera/.test(nav.userAgent.toLowerCase())
        };

    // -------------------------------------------------------------------
    //  YOUR CHANGES GO HERE
    //
    // I've tried to localize the things you are likely to change to
    // this area.
    // -------------------------------------------------------------------

    // The text that appears on the dialog box when entering links.
    // eslint-disable-next-line no-var
    var linkDialogText = gettext('Insert Hyperlink'),
        linkUrlHelpText = gettext("e.g. 'http://google.com'"),
        linkDestinationLabel = gettext('Link Description'),
        linkDestinationHelpText = gettext("e.g. 'google'"),
        linkDestinationError = gettext('Please provide a description of the link destination.'),
        linkDefaultText = 'http://'; // The default text that appears in input

    // The text that appears on the dialog box when entering Images.
    // eslint-disable-next-line no-var
    var imageDialogText = gettext('Insert Image (upload file or type URL)'),
        imageUrlHelpText = gettext("Type in a URL or use the \"Choose File\" button to upload a file from your machine. (e.g. 'http://example.com/img/clouds.jpg')"), // eslint-disable-line max-len
        imageDescriptionLabel = gettext('Image Description'),
        imageDefaultText = 'http://', // The default text that appears in input
        imageDescError = gettext('Please describe this image or agree that it has no contextual value by checking the checkbox.'), // eslint-disable-line max-len
        imageDescriptionHelpText = gettext("e.g. 'Sky with clouds'. The description is helpful for users who cannot see the image."), // eslint-disable-line max-len
        imageDescriptionHelpLink = {
            href: 'http://www.w3.org/TR/html5/embedded-content-0.html#alt',
            text: gettext('How to create useful text alternatives.')
        },
        imageIsDecorativeLabel = gettext('This image is for decorative purposes only and does not require a description.'); // eslint-disable-line max-len

    // Text that is shared between both link and image dialog boxes.
    // eslint-disable-next-line no-var
    var defaultHelpHoverTitle = gettext('Markdown Editing Help'),
        urlLabel = gettext('URL'),
        urlError = gettext('Please provide a valid URL.');

    // -------------------------------------------------------------------
    //  END OF YOUR CHANGES
    // -------------------------------------------------------------------

    // help, if given, should have a property "handler", the click handler for the help button,
    // and can have an optional property "title" for the button's tooltip (defaults to "Markdown Editing Help").
    // If help isn't given, not help button is created.
    //
    // The constructed editor object has the methods:
    // - getConverter() returns the markdown converter object that was passed to the constructor
    // - run() actually starts the editor; should be called after all necessary plugins are registered. Calling this more than once is a no-op.
    // - refreshPreview() forces the preview to be updated. This method is only available after run() was called.
    // eslint-disable-next-line no-undef
    Markdown.Editor = function(markdownConverter, idPostfix, help, imageUploadHandler) {
        idPostfix = idPostfix || '';

        /* eslint-disable-next-line no-multi-assign, no-undef, no-var */
        var hooks = this.hooks = new Markdown.HookCollection();
        hooks.addNoop('onPreviewPush'); // called with no arguments after the preview has been refreshed
        hooks.addNoop('postBlockquoteCreation'); // called with the user's selection *after* the blockquote was created; should return the actual to-be-inserted text
        hooks.addFalse('insertImageDialog'); /* called with one parameter: a callback to be called with the URL of the image. If the application creates
                                                  * its own image insertion dialog, this hook should return true, and the callback should be called with the chosen
                                                  * image url (or null if the user cancelled). If this hook returns false, the default dialog will be used.
                                                  */
        this.util = util;

        this.getConverter = function() { return markdownConverter; };

        // eslint-disable-next-line no-var
        var that = this,
            panels;

        this.run = function() {
            if (panels) { return; } // already initialized

            // eslint-disable-next-line no-use-before-define
            panels = new PanelCollection(idPostfix);
            /* eslint-disable-next-line no-use-before-define, no-var */
            var commandManager = new CommandManager(hooks);
            /* eslint-disable-next-line no-use-before-define, no-var */
            var previewManager = new PreviewManager(markdownConverter, panels, function(text, previewSet) { hooks.onPreviewPush(text, previewSet); });
            // eslint-disable-next-line no-var
            var undoManager, uiManager;

            if (!/\?noundo/.test(doc.location.href)) {
                // eslint-disable-next-line no-use-before-define
                undoManager = new UndoManager(function() {
                    previewManager.refresh();
                    // not available on the first call
                    if (uiManager) { uiManager.setUndoRedoButtonStates(); }
                }, panels);
                this.textOperation = function(f) {
                    undoManager.setCommandMode();
                    f();
                    that.refreshPreview();
                };
            }

            // eslint-disable-next-line no-use-before-define
            uiManager = new UIManager(idPostfix, panels, undoManager, previewManager, commandManager, help, imageUploadHandler);
            uiManager.setUndoRedoButtonStates();

            /* eslint-disable-next-line no-multi-assign, no-var */
            var forceRefresh = that.refreshPreview = function() { previewManager.refresh(true); };

            forceRefresh();
        };
    };

    // before: contains all the text in the input box BEFORE the selection.
    // after: contains all the text in the input box AFTER the selection.
    function Chunks() { }

    // startRegex: a regular expression to find the start tag
    // endRegex: a regular expresssion to find the end tag
    Chunks.prototype.findTags = function(startRegex, endRegex) {
        // eslint-disable-next-line no-var
        var chunkObj = this;
        // eslint-disable-next-line no-var
        var regex;

        if (startRegex) {
            regex = util.extendRegExp(startRegex, '', '$');

            this.before = this.before.replace(regex,
                function(match) {
                    chunkObj.startTag += match;
                    return '';
                });

            regex = util.extendRegExp(startRegex, '^', '');

            this.selection = this.selection.replace(regex,
                function(match) {
                    chunkObj.startTag += match;
                    return '';
                });
        }

        if (endRegex) {
            regex = util.extendRegExp(endRegex, '', '$');

            this.selection = this.selection.replace(regex,
                function(match) {
                    chunkObj.endTag = match + chunkObj.endTag;
                    return '';
                });

            regex = util.extendRegExp(endRegex, '^', '');

            this.after = this.after.replace(regex,
                function(match) {
                    chunkObj.endTag = match + chunkObj.endTag;
                    return '';
                });
        }
    };

    // If remove is false, the whitespace is transferred
    // to the before/after regions.
    //
    // If remove is true, the whitespace disappears.
    Chunks.prototype.trimWhitespace = function(remove) {
        // eslint-disable-next-line no-var
        var beforeReplacer, afterReplacer,
            that = this;
        if (remove) {
            // eslint-disable-next-line no-multi-assign
            beforeReplacer = afterReplacer = '';
        } else {
            beforeReplacer = function(s) { that.before += s; return ''; };
            afterReplacer = function(s) { that.after = s + that.after; return ''; };
        }

        this.selection = this.selection.replace(/^(\s*)/, beforeReplacer).replace(/(\s*)$/, afterReplacer);
    };

    Chunks.prototype.skipLines = function(nLinesBefore, nLinesAfter, findExtraNewlines) {
        if (nLinesBefore === undefined) {
            nLinesBefore = 1;
        }

        if (nLinesAfter === undefined) {
            nLinesAfter = 1;
        }

        nLinesBefore++;
        nLinesAfter++;

        // eslint-disable-next-line no-var
        var regexText;
        // eslint-disable-next-line no-var
        var replacementText;

        // chrome bug ... documented at: http://meta.stackoverflow.com/questions/63307/blockquote-glitch-in-editor-in-chrome-6-and-7/65985#65985
        if (navigator.userAgent.match(/Chrome/)) {
            'X'.match(/()./);
        }

        this.selection = this.selection.replace(/(^\n*)/, '');

        this.startTag += re.$1;

        this.selection = this.selection.replace(/(\n*$)/, '');
        this.endTag += re.$1;
        this.startTag = this.startTag.replace(/(^\n*)/, '');
        this.before += re.$1;
        this.endTag = this.endTag.replace(/(\n*$)/, '');
        this.after += re.$1;

        if (this.before) {
            // eslint-disable-next-line no-multi-assign
            regexText = replacementText = '';

            while (nLinesBefore--) {
                regexText += '\\n?';
                replacementText += '\n';
            }

            if (findExtraNewlines) {
                regexText = '\\n*';
            }
            this.before = this.before.replace(new re(regexText + '$', ''), replacementText);
        }

        if (this.after) {
            // eslint-disable-next-line no-multi-assign
            regexText = replacementText = '';

            while (nLinesAfter--) {
                regexText += '\\n?';
                replacementText += '\n';
            }
            if (findExtraNewlines) {
                regexText = '\\n*';
            }

            this.after = this.after.replace(new re(regexText, ''), replacementText);
        }
    };

    // end of Chunks

    function findAnEmptyToolbar(toolbarClassName) {
        // eslint-disable-next-line no-var
        var toolbars = doc.getElementsByClassName(toolbarClassName);
        // eslint-disable-next-line no-var
        for (var i = 0; i < toolbars.length; ++i) {
            // eslint-disable-next-line no-var
            var aToolbar = toolbars[i];
            // eslint-disable-next-line eqeqeq
            if (aToolbar.children.length == 0) {
                // eslint-disable-next-line no-var
                var anEmptyToolbar = aToolbar;
                return anEmptyToolbar;
            }
        }
        return null;
    }

    // A collection of the important regions on the page.
    // Cached so we don't have to keep traversing the DOM.
    // Also holds ieCachedRange and ieCachedScrollTop, where necessary; working around
    // this issue:
    // Internet explorer has problems with CSS sprite buttons that use HTML
    // lists.  When you click on the background image "button", IE will
    // select the non-existent link text and discard the selection in the
    // textarea.  The solution to this is to cache the textarea selection
    // on the button's mousedown event and set a flag.  In the part of the
    // code where we need to grab the selection, we check for the flag
    // and, if it's set, use the cached area instead of querying the
    // textarea.
    //
    // This ONLY affects Internet Explorer (tested on versions 6, 7
    // and 8) and ONLY on button clicks.  Keyboard shortcuts work
    // normally since the focus never leaves the textarea.
    function PanelCollection(postfix) {
        this.buttonBar = findAnEmptyToolbar('wmd-button-bar' + postfix);
        this.preview = doc.getElementById('wmd-preview' + postfix);
        this.input = doc.getElementById('wmd-input' + postfix);
    }

    util.isValidUrl = function(url) {
        return /^((?:http|https|ftp):\/{2}|\/)[^]+$/.test(url);
    };

    // Returns true if the DOM element is visible, false if it's hidden.
    // Checks if display is anything other than none.
    // eslint-disable-next-line consistent-return
    util.isVisible = function(elem) {
        if (window.getComputedStyle) {
            // Most browsers
            return window.getComputedStyle(elem, null).getPropertyValue('display') !== 'none';
        } else if (elem.currentStyle) {
            // IE
            return elem.currentStyle.display !== 'none';
        }
    };

    // Adds a listener callback to a DOM element which is fired on a specified
    // event.
    util.addEvent = function(elem, event, listener) {
        if (elem.attachEvent) {
            // IE only.  The "on" is mandatory.
            elem.attachEvent('on' + event, listener);
        } else {
            // Other browsers.
            elem.addEventListener(event, listener, false);
        }
    };

    // Removes a listener callback from a DOM element which is fired on a specified
    // event.
    util.removeEvent = function(elem, event, listener) {
        if (elem.detachEvent) {
            // IE only.  The "on" is mandatory.
            elem.detachEvent('on' + event, listener);
        } else {
            // Other browsers.
            elem.removeEventListener(event, listener, false);
        }
    };

    // Converts \r\n and \r to \n.
    util.fixEolChars = function(text) {
        text = text.replace(/\r\n/g, '\n');
        text = text.replace(/\r/g, '\n');
        return text;
    };

    // Extends a regular expression.  Returns a new RegExp
    // using pre + regex + post as the expression.
    // Used in a few functions where we have a base
    // expression and we want to pre- or append some
    // conditions to it (e.g. adding "$" to the end).
    // The flags are unchanged.
    //
    // regex is a RegExp, pre and post are strings.
    util.extendRegExp = function(regex, pre, post) {
        if (pre === null || pre === undefined) {
            pre = '';
        }
        if (post === null || post === undefined) {
            post = '';
        }

        // eslint-disable-next-line no-var
        var pattern = regex.toString();
        // eslint-disable-next-line no-var
        var flags;

        // Replace the flags with empty space and store them.
        pattern = pattern.replace(/\/([gim]*)$/, function(wholeMatch, flagsPart) {
            flags = flagsPart;
            return '';
        });

        // Remove the slash delimiters on the regular expression.
        pattern = pattern.replace(/(^\/|\/$)/g, '');
        pattern = pre + pattern + post;

        return new re(pattern, flags);
    };

    // UNFINISHED
    // The assignment in the while loop makes jslint cranky.
    // I'll change it to a better loop later.
    position.getTop = function(elem, isInner) {
        // eslint-disable-next-line no-var
        var result = elem.offsetTop;
        if (!isInner) {
            // eslint-disable-next-line no-cond-assign
            while (elem = elem.offsetParent) {
                result += elem.offsetTop;
            }
        }
        return result;
    };

    position.getHeight = function(elem) {
        return elem.offsetHeight || elem.scrollHeight;
    };

    position.getWidth = function(elem) {
        return elem.offsetWidth || elem.scrollWidth;
    };

    position.getPageSize = function() {
        // eslint-disable-next-line no-var
        var scrollWidth, scrollHeight;
        // eslint-disable-next-line no-var
        var innerWidth, innerHeight;

        // It's not very clear which blocks work with which browsers.
        if (self.innerHeight && self.scrollMaxY) {
            scrollWidth = doc.body.scrollWidth;
            scrollHeight = self.innerHeight + self.scrollMaxY;
        } else if (doc.body.scrollHeight > doc.body.offsetHeight) {
            scrollWidth = doc.body.scrollWidth;
            scrollHeight = doc.body.scrollHeight;
        } else {
            scrollWidth = doc.body.offsetWidth;
            scrollHeight = doc.body.offsetHeight;
        }

        if (self.innerHeight) {
            // Non-IE browser
            innerWidth = self.innerWidth;
            innerHeight = self.innerHeight;
        } else if (doc.documentElement && doc.documentElement.clientHeight) {
            // Some versions of IE (IE 6 w/ a DOCTYPE declaration)
            innerWidth = doc.documentElement.clientWidth;
            innerHeight = doc.documentElement.clientHeight;
        } else if (doc.body) {
            // Other versions of IE
            innerWidth = doc.body.clientWidth;
            innerHeight = doc.body.clientHeight;
        }

        // eslint-disable-next-line no-var
        var maxWidth = Math.max(scrollWidth, innerWidth);
        // eslint-disable-next-line no-var
        var maxHeight = Math.max(scrollHeight, innerHeight);
        return [maxWidth, maxHeight, innerWidth, innerHeight];
    };

    // Handles pushing and popping TextareaStates for undo/redo commands.
    // I should rename the stack variables to list.
    function UndoManager(callback, panels) {
        // eslint-disable-next-line no-var
        var undoObj = this;
        // eslint-disable-next-line no-var
        var undoStack = []; // A stack of undo states
        // eslint-disable-next-line no-var
        var stackPtr = 0; // The index of the current state
        // eslint-disable-next-line no-var
        var mode = 'none';
        // eslint-disable-next-line no-var
        var lastState; // The last state
        // eslint-disable-next-line no-var
        var timer; // The setTimeout handle for cancelling the timer
        // eslint-disable-next-line no-var
        var inputStateObj;

        // Set the mode for later logic steps.
        // eslint-disable-next-line no-var
        var setMode = function(newMode, noSave) {
            // eslint-disable-next-line eqeqeq
            if (mode != newMode) {
                mode = newMode;
                if (!noSave) {
                    // eslint-disable-next-line no-use-before-define
                    saveState();
                }
            }

            // eslint-disable-next-line eqeqeq
            if (!uaSniffed.isIE || mode != 'moving') {
                // eslint-disable-next-line no-use-before-define
                timer = setTimeout(refreshState, 1);
            } else {
                inputStateObj = null;
            }
        };

        // eslint-disable-next-line no-var
        var refreshState = function(isInitialState) {
            // eslint-disable-next-line no-use-before-define
            inputStateObj = new TextareaState(panels, isInitialState);
            timer = undefined;
        };

        this.setCommandMode = function() {
            mode = 'command';
            // eslint-disable-next-line no-use-before-define
            saveState();
            timer = setTimeout(refreshState, 0);
        };

        this.canUndo = function() {
            return stackPtr > 1;
        };

        this.canRedo = function() {
            if (undoStack[stackPtr + 1]) {
                return true;
            }
            return false;
        };

        // Removes the last state and restores it.
        this.undo = function() {
            if (undoObj.canUndo()) {
                if (lastState) {
                    // What about setting state -1 to null or checking for undefined?
                    lastState.restore();
                    lastState = null;
                } else {
                    // eslint-disable-next-line no-use-before-define
                    undoStack[stackPtr] = new TextareaState(panels);
                    undoStack[--stackPtr].restore();

                    if (callback) {
                        callback();
                    }
                }
            }

            mode = 'none';
            panels.input.focus();
            refreshState();
        };

        // Redo an action.
        this.redo = function() {
            if (undoObj.canRedo()) {
                undoStack[++stackPtr].restore();

                if (callback) {
                    callback();
                }
            }

            mode = 'none';
            panels.input.focus();
            refreshState();
        };

        // Push the input area state to the stack.
        /* eslint-disable-next-line consistent-return, no-var */
        var saveState = function() {
            /* eslint-disable-next-line no-use-before-define, no-var */
            var currState = inputStateObj || new TextareaState(panels);

            if (!currState) {
                return false;
            }
            // eslint-disable-next-line eqeqeq
            if (mode == 'moving') {
                if (!lastState) {
                    lastState = currState;
                }
                // eslint-disable-next-line consistent-return
                return;
            }
            if (lastState) {
                // eslint-disable-next-line eqeqeq
                if (undoStack[stackPtr - 1].text != lastState.text) {
                    undoStack[stackPtr++] = lastState;
                }
                lastState = null;
            }
            undoStack[stackPtr++] = currState;
            undoStack[stackPtr + 1] = null;
            if (callback) {
                callback();
            }
        };

        // eslint-disable-next-line no-var
        var handleCtrlYZ = function(event) {
            // eslint-disable-next-line no-var
            var handled = false;

            if (event.ctrlKey || event.metaKey) {
                // IE and Opera do not support charCode.
                // eslint-disable-next-line no-var
                var keyCode = event.charCode || event.keyCode;
                // eslint-disable-next-line no-var
                var keyCodeChar = String.fromCharCode(keyCode);

                // eslint-disable-next-line default-case
                switch (keyCodeChar) {
                case 'y':
                    undoObj.redo();
                    handled = true;
                    break;

                case 'z':
                    if (!event.shiftKey) {
                        undoObj.undo();
                    } else {
                        undoObj.redo();
                    }
                    handled = true;
                    break;
                }
            }

            if (handled) {
                if (event.preventDefault) {
                    event.preventDefault();
                }
                if (window.event) {
                    window.event.returnValue = false;
                }
            }
        };

        // Set the mode depending on what is going on in the input area.
        // eslint-disable-next-line no-var
        var handleModeChange = function(event) {
            if (!event.ctrlKey && !event.metaKey) {
                // eslint-disable-next-line no-var
                var keyCode = event.keyCode;

                if ((keyCode >= 33 && keyCode <= 40) || (keyCode >= 63232 && keyCode <= 63235)) {
                    // 33 - 40: page up/dn and arrow keys
                    // 63232 - 63235: page up/dn and arrow keys on safari
                    setMode('moving');
                // eslint-disable-next-line eqeqeq
                } else if (keyCode == 8 || keyCode == 46 || keyCode == 127) {
                    // 8: backspace
                    // 46: delete
                    // 127: delete
                    setMode('deleting');
                // eslint-disable-next-line eqeqeq
                } else if (keyCode == 13) {
                    // 13: Enter
                    setMode('newlines');
                // eslint-disable-next-line eqeqeq
                } else if (keyCode == 27) {
                    // 27: escape
                    setMode('escape');
                // eslint-disable-next-line eqeqeq
                } else if ((keyCode < 16 || keyCode > 20) && keyCode != 91) {
                    // 16-20 are shift, etc.
                    // 91: left window key
                    // I think this might be a little messed up since there are
                    // a lot of nonprinting keys above 20.
                    setMode('typing');
                }
            }
        };

        // eslint-disable-next-line no-var
        var setEventHandlers = function() {
            util.addEvent(panels.input, 'keypress', function(event) {
                // keyCode 89: y
                // keyCode 90: z
                // eslint-disable-next-line eqeqeq
                if ((event.ctrlKey || event.metaKey) && (event.keyCode == 89 || event.keyCode == 90)) {
                    event.preventDefault();
                }
            });

            // eslint-disable-next-line no-var
            var handlePaste = function() {
                // eslint-disable-next-line eqeqeq
                if (uaSniffed.isIE || (inputStateObj && inputStateObj.text != panels.input.value)) {
                    // eslint-disable-next-line eqeqeq
                    if (timer == undefined) {
                        mode = 'paste';
                        saveState();
                        refreshState();
                    }
                }
            };

            util.addEvent(panels.input, 'keydown', handleCtrlYZ);
            util.addEvent(panels.input, 'keydown', handleModeChange);
            util.addEvent(panels.input, 'mousedown', function() {
                setMode('moving');
            });

            panels.input.onpaste = handlePaste;
            panels.input.ondrop = handlePaste;
        };

        // eslint-disable-next-line no-var
        var init = function() {
            setEventHandlers();
            refreshState(true);
            saveState();
        };

        init();
    }

    // end of UndoManager

    // The input textarea state/contents.
    // This is used to implement undo/redo by the undo manager.
    function TextareaState(panels, isInitialState) {
        // Aliases
        // eslint-disable-next-line no-var
        var stateObj = this;
        // eslint-disable-next-line no-var
        var inputArea = panels.input;
        this.init = function() {
            if (!util.isVisible(inputArea)) {
                return;
            }
            if (!isInitialState && doc.activeElement && doc.activeElement !== inputArea) { // this happens when tabbing out of the input box
                return;
            }

            this.setInputAreaSelectionStartEnd();
            this.scrollTop = inputArea.scrollTop;
            // eslint-disable-next-line no-mixed-operators
            if (!this.text && inputArea.selectionStart || inputArea.selectionStart === 0) {
                this.text = inputArea.value;
            }
        };

        // Sets the selected text in the input box after we've performed an
        // operation.
        this.setInputAreaSelection = function() {
            if (!util.isVisible(inputArea)) {
                return;
            }

            if (inputArea.selectionStart !== undefined && !uaSniffed.isOpera) {
                inputArea.focus();
                inputArea.selectionStart = stateObj.start;
                inputArea.selectionEnd = stateObj.end;
                inputArea.scrollTop = stateObj.scrollTop;
            } else if (doc.selection) {
                if (doc.activeElement && doc.activeElement !== inputArea) {
                    return;
                }

                inputArea.focus();
                // eslint-disable-next-line no-var
                var range = inputArea.createTextRange();
                range.moveStart('character', -inputArea.value.length);
                range.moveEnd('character', -inputArea.value.length);
                range.moveEnd('character', stateObj.end);
                range.moveStart('character', stateObj.start);
                range.select();
            }
        };

        this.setInputAreaSelectionStartEnd = function() {
            if (!panels.ieCachedRange && (inputArea.selectionStart || inputArea.selectionStart === 0)) {
                stateObj.start = inputArea.selectionStart;
                stateObj.end = inputArea.selectionEnd;
            } else if (doc.selection) {
                stateObj.text = util.fixEolChars(inputArea.value);

                // IE loses the selection in the textarea when buttons are
                // clicked.  On IE we cache the selection. Here, if something is cached,
                // we take it.
                // eslint-disable-next-line no-var
                var range = panels.ieCachedRange || doc.selection.createRange();

                // eslint-disable-next-line no-var
                var fixedRange = util.fixEolChars(range.text);
                // eslint-disable-next-line no-var
                var marker = '\x07';
                // eslint-disable-next-line no-var
                var markedRange = marker + fixedRange + marker;
                range.text = markedRange;
                // eslint-disable-next-line no-var
                var inputText = util.fixEolChars(inputArea.value);

                range.moveStart('character', -markedRange.length);
                range.text = fixedRange;

                stateObj.start = inputText.indexOf(marker);
                stateObj.end = inputText.lastIndexOf(marker) - marker.length;

                // eslint-disable-next-line no-var
                var len = stateObj.text.length - util.fixEolChars(inputArea.value).length;

                if (len) {
                    range.moveStart('character', -fixedRange.length);
                    while (len--) {
                        fixedRange += '\n';
                        stateObj.end += 1;
                    }
                    range.text = fixedRange;
                }

                if (panels.ieCachedRange) { stateObj.scrollTop = panels.ieCachedScrollTop; } // this is set alongside with ieCachedRange

                panels.ieCachedRange = null;

                this.setInputAreaSelection();
            }
        };

        // Restore this state into the input area.
        this.restore = function() {
            // eslint-disable-next-line eqeqeq
            if (stateObj.text != undefined && stateObj.text != inputArea.value) {
                inputArea.value = stateObj.text;
            }
            this.setInputAreaSelection();
            inputArea.scrollTop = stateObj.scrollTop;
        };

        // Gets a collection of HTML chunks from the inptut textarea.
        this.getChunks = function() {
            // eslint-disable-next-line no-var
            var chunk = new Chunks();
            chunk.before = util.fixEolChars(stateObj.text.substring(0, stateObj.start));
            chunk.startTag = '';
            chunk.selection = util.fixEolChars(stateObj.text.substring(stateObj.start, stateObj.end));
            chunk.endTag = '';
            chunk.after = util.fixEolChars(stateObj.text.substring(stateObj.end));
            chunk.scrollTop = stateObj.scrollTop;

            return chunk;
        };

        // Sets the TextareaState properties given a chunk of markdown.
        this.setChunks = function(chunk) {
            chunk.before += chunk.startTag;
            chunk.after = chunk.endTag + chunk.after;

            this.start = chunk.before.length;
            this.end = chunk.before.length + chunk.selection.length;
            this.text = chunk.before + chunk.selection + chunk.after;
            this.scrollTop = chunk.scrollTop;
        };
        this.init();
    }

    function PreviewManager(converter, panels, previewPushCallback) {
        /* eslint-disable-next-line no-unused-vars, no-var */
        var managerObj = this;
        // eslint-disable-next-line no-var
        var timeout;
        // eslint-disable-next-line no-var
        var elapsedTime;
        // eslint-disable-next-line no-var
        var oldInputText;
        // eslint-disable-next-line no-var
        var maxDelay = 3000;
        // eslint-disable-next-line no-var
        var startType = 'delayed'; // The other legal value is "manual"

        // Adds event listeners to elements
        // eslint-disable-next-line no-var
        var setupEvents = function(inputElem, listener) {
            util.addEvent(inputElem, 'input', listener);
            inputElem.onpaste = listener;
            inputElem.ondrop = listener;

            util.addEvent(inputElem, 'keypress', listener);
            util.addEvent(inputElem, 'keydown', listener);
        };

        // eslint-disable-next-line no-var
        var getDocScrollTop = function() {
            // eslint-disable-next-line no-var
            var result = 0;

            if (window.innerHeight) {
                result = window.pageYOffset;
            } else
            if (doc.documentElement && doc.documentElement.scrollTop) {
                result = doc.documentElement.scrollTop;
            } else
            if (doc.body) {
                result = doc.body.scrollTop;
            }

            return result;
        };

        // eslint-disable-next-line no-var
        var makePreviewHtml = function() {
            // If there is no registered preview panel
            // there is nothing to do.
            if (!panels.preview) { return; }

            // eslint-disable-next-line no-var
            var text = panels.input.value;
            // eslint-disable-next-line eqeqeq
            if (text && text == oldInputText) {
                return; // Input text hasn't changed.
            } else {
                oldInputText = text;
            }

            // eslint-disable-next-line no-var
            var prevTime = new Date().getTime();

            text = converter.makeHtml(text);

            // Calculate the processing time of the HTML creation.
            // It's used as the delay time in the event listener.
            // eslint-disable-next-line no-var
            var currTime = new Date().getTime();
            elapsedTime = currTime - prevTime;

            // eslint-disable-next-line no-use-before-define
            pushPreviewHtml(text);
        };

        // setTimeout is already used.  Used as an event listener.
        // eslint-disable-next-line no-var
        var applyTimeout = function() {
            if (timeout) {
                clearTimeout(timeout);
                timeout = undefined;
            }

            if (startType !== 'manual') {
                // eslint-disable-next-line no-var
                var delay = 0;

                if (startType === 'delayed') {
                    delay = elapsedTime;
                }

                if (delay > maxDelay) {
                    delay = maxDelay;
                }
                timeout = setTimeout(makePreviewHtml, delay);
            }
        };

        // eslint-disable-next-line no-var
        var getScaleFactor = function(panel) {
            if (panel.scrollHeight <= panel.clientHeight) {
                return 1;
            }
            return panel.scrollTop / (panel.scrollHeight - panel.clientHeight);
        };

        // eslint-disable-next-line no-var
        var setPanelScrollTops = function() {
            if (panels.preview) {
                panels.preview.scrollTop = (panels.preview.scrollHeight - panels.preview.clientHeight) * getScaleFactor(panels.preview);
            }
        };

        this.refresh = function(requiresRefresh) {
            if (requiresRefresh) {
                oldInputText = '';
                makePreviewHtml();
            } else {
                applyTimeout();
            }
        };

        this.processingTime = function() {
            return elapsedTime;
        };

        // eslint-disable-next-line no-var
        var isFirstTimeFilled = true;

        // IE doesn't let you use innerHTML if the element is contained somewhere in a table
        // (which is the case for inline editing) -- in that case, detach the element, set the
        // value, and reattach. Yes, that *is* ridiculous.
        // eslint-disable-next-line no-var
        var ieSafePreviewSet = function(text) {
            // eslint-disable-next-line no-var
            var preview = panels.preview;
            // eslint-disable-next-line no-var
            var parent = preview.parentNode;
            // eslint-disable-next-line no-var
            var sibling = preview.nextSibling;
            parent.removeChild(preview);
            preview.innerHTML = text;
            if (!sibling) { parent.appendChild(preview); } else { parent.insertBefore(preview, sibling); } // xss-lint: disable=javascript-jquery-insert-into-target
        };

        // eslint-disable-next-line no-var
        var nonSuckyBrowserPreviewSet = function(text) {
            panels.preview.innerHTML = text;
        };

        // eslint-disable-next-line no-var
        var previewSetter;

        /* eslint-disable-next-line consistent-return, no-var */
        var previewSet = function(text) {
            if (previewSetter) { return previewSetter(text); }

            try {
                nonSuckyBrowserPreviewSet(text);
                previewSetter = nonSuckyBrowserPreviewSet;
            } catch (e) {
                previewSetter = ieSafePreviewSet;
                previewSetter(text);
            }
        };

        // eslint-disable-next-line no-var
        var pushPreviewHtml = function(text) {
            // eslint-disable-next-line no-var
            var emptyTop = position.getTop(panels.input) - getDocScrollTop();

            if (panels.preview) {
                previewPushCallback(text, previewSet);
            }

            setPanelScrollTops();

            if (isFirstTimeFilled) {
                isFirstTimeFilled = false;
                return;
            }

            // eslint-disable-next-line no-var
            var fullTop = position.getTop(panels.input) - getDocScrollTop();

            if (uaSniffed.isIE) {
                setTimeout(function() {
                    window.scrollBy(0, fullTop - emptyTop);
                }, 0);
            } else {
                window.scrollBy(0, fullTop - emptyTop);
            }
        };

        // eslint-disable-next-line no-var
        var init = function() {
            setupEvents(panels.input, applyTimeout);
            makePreviewHtml();

            if (panels.preview) {
                panels.preview.scrollTop = 0;
            }
        };

        init();
    }

    // Creates the background behind the hyperlink text entry box.
    // And download dialog
    // Most of this has been moved to CSS but the div creation and
    // browser-specific hacks remain here.
    ui.createBackground = function() {
        // eslint-disable-next-line no-var
        var background = doc.createElement('div'),
            style = background.style;

        background.className = 'wmd-prompt-background';

        style.position = 'absolute';
        style.top = '0';

        style.zIndex = '1000';

        if (uaSniffed.isIE) {
            style.filter = 'alpha(opacity=50)';
        } else {
            style.opacity = '0.5';
        }

        // eslint-disable-next-line no-var
        var pageSize = position.getPageSize();
        style.height = pageSize[1] + 'px';

        if (uaSniffed.isIE) {
            style.left = doc.documentElement.scrollLeft;
            style.width = doc.documentElement.clientWidth;
        } else {
            style.left = '0';
            style.width = '100%';
        }

        doc.body.appendChild(background);
        return background;
    };

    // This simulates a modal dialog box and asks for the URL when you
    // click the hyperlink or image buttons.
    //
    // text: The html for the input box.
    // defaultInputText: The default value that appears in the input box.
    // callback: The function which is executed when the prompt is dismissed, either via OK or Cancel.
    //      It receives a single argument; either the entered text (if OK was chosen) or null (if Cancel
    //      was chosen).
    ui.prompt = function(title,
        // eslint-disable-next-line no-shadow
        urlLabel,
        urlHelp,
        // eslint-disable-next-line no-shadow
        urlError,
        urlDescLabel,
        urlDescHelp,
        urlDescHelpLink,
        urlDescError,
        defaultInputText,
        callback,
        // eslint-disable-next-line no-shadow
        imageIsDecorativeLabel,
        imageUploadHandler) {
        // These variables need to be declared at this level since they are used
        // in multiple functions.
        // eslint-disable-next-line no-var
        var dialog, // The dialog box.
            urlInput, // The text box where you enter the hyperlink.
            urlErrorMsg,
            descInput, // The text box where you enter the description.
            descErrorMsg,
            okButton,
            cancelButton;

        // Used as a keydown event handler. Esc dismisses the prompt.
        // Key code 27 is ESC.
        // eslint-disable-next-line no-var
        var checkEscape = function(key) {
            // eslint-disable-next-line no-var
            var code = (key.charCode || key.keyCode);
            if (code === 27) {
                // eslint-disable-next-line no-use-before-define
                close(true);
            }
        };

        // eslint-disable-next-line no-var
        var clearFormErrorMessages = function() {
            urlInput.classList.remove('has-error');
            urlErrorMsg.style.display = 'none';
            descInput.classList.remove('has-error');
            descErrorMsg.style.display = 'none';
        };

        // Dismisses the hyperlink input box.
        // isCancel is true if we don't care about the input text.
        // isCancel is false if we are going to keep the text.
        // eslint-disable-next-line no-var
        var close = function(isCancel) {
            util.removeEvent(doc.body, 'keydown', checkEscape);
            // eslint-disable-next-line no-var
            var url = urlInput.value.trim();
            // eslint-disable-next-line no-var
            var description = descInput.value.trim();

            clearFormErrorMessages();

            if (isCancel) {
                url = null;
            } else {
                // Fixes common pasting errors.
                url = url.replace(/^http:\/\/(https?|ftp):\/\//, '$1://');
                // doesn't change url if started with '/' (local)
                if (!/^(?:https?|ftp):\/\//.test(url) && url.charAt(0) !== '/') {
                    url = 'http://' + url;
                }
            }

            // eslint-disable-next-line no-var
            var isValidUrl = util.isValidUrl(url),
                isValidDesc = (
                    descInput.checkValidity()
                    && (descInput.required ? description.length : true)
                );

            if ((isValidUrl && isValidDesc) || isCancel) {
                dialog.parentNode.removeChild(dialog);
                callback(url, description);
            } else {
                // eslint-disable-next-line no-var
                var errorCount = 0;
                if (!isValidUrl) {
                    urlInput.classList.add('has-error');
                    urlErrorMsg.style.display = 'inline-block';
                    errorCount += 1;
                } if (!isValidDesc) {
                    descInput.classList.add('has-error');
                    descErrorMsg.style.display = 'inline-block';
                    errorCount += 1;
                }

                document.getElementById('wmd-editor-dialog-form-errors').textContent = [
                    // eslint-disable-next-line no-undef
                    interpolate( // xss-lint: disable=javascript-interpolate
                        ngettext(
                            // Translators: 'errorCount' is the number of errors found in the form.
                            '%(errorCount)s error found in form.', '%(errorCount)s errors found in form.',
                            errorCount
                        ), {errorCount: errorCount}, true
                    ),
                    !isValidUrl ? urlErrorMsg.textContent : '',
                    !isValidDesc ? descErrorMsg.textContent : ''
                ].join(' ');

                document.getElementById('wmd-editor-dialog-form-errors').focus();
            }

            return false;
        };

        // Create the text input box form/window.
        // eslint-disable-next-line no-var
        var createDialog = function() {
            // The main dialog box.
            dialog = doc.createElement('div');
            // eslint-disable-next-line no-undef
            dialog.innerHTML = _.template(
                document.getElementById('customwmd-prompt-template').innerHTML)({
                title: title,
                uploadFieldClass: (imageUploadHandler ? 'file-upload' : ''),
                urlLabel: urlLabel,
                urlError: urlError,
                urlHelp: urlHelp,
                urlDescLabel: urlDescLabel,
                descError: urlDescError,
                urlDescHelp: urlDescHelp,
                urlDescHelpLink: urlDescHelpLink,
                okText: gettext('OK'),
                cancelText: gettext('Cancel'),
                chooseFileText: gettext('Choose File'),
                imageIsDecorativeLabel: imageIsDecorativeLabel,
                imageUploadHandler: imageUploadHandler
            });
            dialog.setAttribute('dir', doc.head.getAttribute('dir'));
            dialog.setAttribute('role', 'dialog');
            dialog.setAttribute('tabindex', '-1');
            dialog.setAttribute('aria-labelledby', 'editorDialogTitle');
            dialog.className = 'wmd-prompt-dialog';
            dialog.style.padding = '10px;';
            dialog.style.position = 'fixed';
            dialog.style.width = '500px';
            dialog.style.zIndex = '1001';

            doc.body.appendChild(dialog);

            // This has to be done AFTER adding the dialog to the form if you
            // want it to be centered.
            util.addEvent(doc.body, 'keydown', checkEscape);
            dialog.style.top = '50%';
            dialog.style.left = '50%';
            dialog.style.display = 'block';
            if (uaSniffed.isIE_5or6) {
                dialog.style.position = 'absolute';
                dialog.style.top = doc.documentElement.scrollTop + 200 + 'px';
                dialog.style.left = '50%';
            }
            dialog.style.marginTop = -(position.getHeight(dialog) / 2) + 'px';
            dialog.style.marginLeft = -(position.getWidth(dialog) / 2) + 'px';

            urlInput = document.getElementById('new-url-input');
            urlErrorMsg = document.getElementById('new-url-input-field-message');
            descInput = document.getElementById('new-url-desc-input');
            descErrorMsg = document.getElementById('new-url-desc-input-field-message');
            urlInput.value = defaultInputText;

            okButton = document.getElementById('new-link-image-ok');
            cancelButton = document.getElementById('new-link-image-cancel');

            okButton.onclick = function() { return close(false); };
            cancelButton.onclick = function() { return close(true); };

            if (imageUploadHandler) {
                // eslint-disable-next-line no-var
                var startUploadHandler = function() {
                    document.getElementById('file-upload').onchange = function() {
                        imageUploadHandler(this, urlInput);
                        urlInput.focus();

                        // Ensures that a user can update their file choice.
                        startUploadHandler();
                    };
                };
                startUploadHandler();
                document.getElementById('file-upload-proxy').onclick = function() {
                    document.getElementById('file-upload').click();
                    return false;
                };
                document.getElementById('img-is-decorative').onchange = function() {
                    descInput.required = !descInput.required;
                };
            }

            // trap focus in the dialog box
            $(dialog).on('keydown', function(event) {
                // On tab backward from the first tabbable item in the prompt
                if (event.which === 9 && event.shiftKey && event.target === urlInput) {
                    event.preventDefault();
                    cancelButton.focus();
                // eslint-disable-next-line brace-style
                }
                // On tab forward from the last tabbable item in the prompt
                else if (event.which === 9 && !event.shiftKey && event.target === cancelButton) {
                    event.preventDefault();
                    urlInput.focus();
                }
            });
        };

        // Why is this in a zero-length timeout?
        // Is it working around a browser bug?
        setTimeout(function() {
            createDialog();

            // eslint-disable-next-line no-var
            var defTextLen = defaultInputText.length;
            if (urlInput.selectionStart !== undefined) {
                urlInput.selectionStart = 0;
                urlInput.selectionEnd = defTextLen;
            } else if (urlInput.createTextRange) {
                // eslint-disable-next-line no-var
                var range = urlInput.createTextRange();
                range.collapse(false);
                range.moveStart('character', -defTextLen);
                range.moveEnd('character', defTextLen);
                range.select();
            }

            dialog.focus();
        }, 0);
    };

    function UIManager(postfix, panels, undoManager, previewManager, commandManager, helpOptions, imageUploadHandler) {
        // eslint-disable-next-line no-var
        var inputBox = panels.input,
            buttons = {}; // buttons.undo, buttons.link, etc. The actual DOM elements.

        // eslint-disable-next-line no-use-before-define
        makeSpritedButtonRow();

        // eslint-disable-next-line no-var
        var keyEvent = 'keydown';
        if (uaSniffed.isOpera) {
            keyEvent = 'keypress';
        }

        util.addEvent(inputBox, keyEvent, function(key) {
            // Check to see if we have a button key and, if so execute the callback.
            if ((key.ctrlKey || key.metaKey) && !key.altKey && !key.shiftKey) {
                // eslint-disable-next-line no-var
                var keyCode = key.charCode || key.keyCode;
                // eslint-disable-next-line no-var
                var keyCodeStr = String.fromCharCode(keyCode).toLowerCase();

                switch (keyCodeStr) {
                case 'b':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.bold);
                    break;
                case 'i':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.italic);
                    break;
                case 'l':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.link);
                    break;
                case 'q':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.quote);
                    break;
                case 'k':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.code);
                    break;
                case 'g':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.image);
                    break;
                case 'o':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.olist);
                    break;
                case 'u':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.ulist);
                    break;
                case 'h':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.heading);
                    break;
                case 'r':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.hr);
                    break;
                case 'y':
                    // eslint-disable-next-line no-use-before-define
                    doClick(buttons.redo);
                    break;
                case 'z':
                    if (key.shiftKey) {
                        // eslint-disable-next-line no-use-before-define
                        doClick(buttons.redo);
                    } else {
                        // eslint-disable-next-line no-use-before-define
                        doClick(buttons.undo);
                    }
                    break;
                default:
                    return;
                }

                if (key.preventDefault) {
                    key.preventDefault();
                }

                if (window.event) {
                    window.event.returnValue = false;
                }
            }
        });

        // Auto-indent on shift-enter
        util.addEvent(inputBox, 'keyup', function(key) {
            if (key.shiftKey && !key.ctrlKey && !key.metaKey) {
                // eslint-disable-next-line no-var
                var keyCode = key.charCode || key.keyCode;
                // Character 13 is Enter
                if (keyCode === 13) {
                    // eslint-disable-next-line no-var
                    var fakeButton = {};
                    // eslint-disable-next-line no-use-before-define
                    fakeButton.textOp = bindCommand('doAutoindent');
                    // eslint-disable-next-line no-use-before-define
                    doClick(fakeButton);
                }
            }
        });

        // special handler because IE clears the context of the textbox on ESC
        if (uaSniffed.isIE) {
            // eslint-disable-next-line consistent-return
            util.addEvent(inputBox, 'keydown', function(key) {
                // eslint-disable-next-line no-var
                var code = key.keyCode;
                if (code === 27) {
                    return false;
                }
            });
        }

        // Perform the button's action.
        function doClick(button) {
            inputBox.focus();

            if (button.textOp) {
                if (undoManager) {
                    undoManager.setCommandMode();
                }

                // eslint-disable-next-line no-var
                var state = new TextareaState(panels);

                if (!state) {
                    return;
                }

                // eslint-disable-next-line no-var
                var chunks = state.getChunks();

                // Some commands launch a "modal" prompt dialog.  Javascript
                // can't really make a modal dialog box and the WMD code
                // will continue to execute while the dialog is displayed.
                // This prevents the dialog pattern I'm used to and means
                // I can't do something like this:
                //
                // var link = CreateLinkDialog();
                // makeMarkdownLink(link);
                //
                // Instead of this straightforward method of handling a
                // dialog I have to pass any code which would execute
                // after the dialog is dismissed (e.g. link creation)
                // in a function parameter.
                //
                // Yes this is awkward and I think it sucks, but there's
                // no real workaround.  Only the image and link code
                // create dialogs and require the function pointers.
                // eslint-disable-next-line no-var
                var fixupInputArea = function() {
                    inputBox.focus();

                    if (chunks) {
                        state.setChunks(chunks);
                    }

                    state.restore();
                    previewManager.refresh();
                };

                // eslint-disable-next-line no-var
                var noCleanup = button.textOp(chunks, fixupInputArea);

                if (!noCleanup) {
                    fixupInputArea();
                }
            }

            if (button.execute) {
                button.execute(undoManager);
            }
        }

        function setupButton(button, isEnabled) {
            // eslint-disable-next-line no-var
            var normalYShift = '0px';
            // eslint-disable-next-line no-var
            var disabledYShift = '-20px';
            // eslint-disable-next-line no-var
            var highlightYShift = '-40px';
            // eslint-disable-next-line no-var
            var image = button.getElementsByTagName('span')[0];
            if (isEnabled) {
                image.style.backgroundPosition = button.XShift + ' ' + normalYShift;
                button.onmouseover = function() {
                    image.style.backgroundPosition = this.XShift + ' ' + highlightYShift;
                };

                button.onmouseout = function() {
                    image.style.backgroundPosition = this.XShift + ' ' + normalYShift;
                };

                // IE tries to select the background image "button" text (it's
                // implemented in a list item) so we have to cache the selection
                // on mousedown.
                if (uaSniffed.isIE) {
                    button.onmousedown = function() {
                        if (doc.activeElement && doc.activeElement !== panels.input) { // we're not even in the input box, so there's no selection
                            return;
                        }
                        panels.ieCachedRange = document.selection.createRange();
                        panels.ieCachedScrollTop = panels.input.scrollTop;
                    };
                }

                if (!button.isHelp) {
                    button.onclick = function() {
                        if (this.onmouseout) {
                            this.onmouseout();
                        }
                        doClick(this);
                        return false;
                    };
                    util.addEvent(button, 'keydown', function(event) {
                        // eslint-disable-next-line no-var
                        var keyCode = event.charCode || event.keyCode;
                        // eslint-disable-next-line eqeqeq
                        if (keyCode == 32 || keyCode == 13) {
                            if (event.preventDefault) {
                                event.preventDefault();
                            }
                            if (window.event) {
                                window.event.returnValue = false;
                            }
                            doClick(button);
                        }
                    });
                }
                // This line does not appear in vanilla WMD. It was added by edX to improve accessibility.
                // It should become a separate commit applied to WMD's official HEAD if we remove this edited version
                // of WMD from Git and install it from NPM / a maintained public fork.
                button.removeAttribute('aria-disabled');
            } else {
                image.style.backgroundPosition = button.XShift + ' ' + disabledYShift;
                // eslint-disable-next-line no-multi-assign
                button.onmouseover = button.onmouseout = button.onclick = function() { };
                // This line does not appear in vanilla WMD. It was added by edX to improve accessibility.
                // It should become a separate commit applied to WMD's official HEAD if we remove this edited version
                // of WMD from Git and install it from NPM / a maintained public fork.
                button.setAttribute('aria-disabled', true);
            }
        }

        function bindCommand(method) {
            if (typeof method === 'string') { method = commandManager[method]; }
            return function() { method.apply(commandManager, arguments); };
        }

        function makeSpritedButtonRow() {
            // eslint-disable-next-line no-var
            var buttonBar = panels.buttonBar;

            /* eslint-disable-next-line no-unused-vars, no-var */
            var normalYShift = '0px';
            /* eslint-disable-next-line no-unused-vars, no-var */
            var disabledYShift = '-20px';
            /* eslint-disable-next-line no-unused-vars, no-var */
            var highlightYShift = '-40px';

            // eslint-disable-next-line no-var
            var buttonRow = document.createElement('div');
            buttonRow.setAttribute('role', 'toolbar');
            buttonRow.id = 'wmd-button-row' + postfix;
            buttonRow.className = 'wmd-button-row';
            buttonRow = buttonBar.appendChild(buttonRow);
            // eslint-disable-next-line no-var
            var xPosition = 0;
            // eslint-disable-next-line no-var
            var makeButton = function(id, title, XShift, textOp, tabIndex) {
                // eslint-disable-next-line no-var
                var button = document.createElement('button');
                button.tabIndex = tabIndex;
                button.className = 'wmd-button';
                button.style.left = xPosition + 'px';
                xPosition += 25;
                // eslint-disable-next-line no-var
                var buttonImage = document.createElement('span');
                button.id = id + postfix;
                button.appendChild(buttonImage);
                button.title = title;
                button.XShift = XShift;
                if (textOp) { button.textOp = textOp; }
                setupButton(button, true);
                buttonRow.appendChild(button);
                return button;
            };
            // eslint-disable-next-line no-var
            var makeSpacer = function(num) {
                // eslint-disable-next-line no-var
                var spacer = document.createElement('span');
                spacer.setAttribute('role', 'separator');
                spacer.className = 'wmd-spacer wmd-spacer' + num;
                spacer.id = 'wmd-spacer' + num + postfix;
                buttonRow.appendChild(spacer);
                xPosition += 25;
            };

            buttons.bold = makeButton('wmd-bold-button', gettext('Bold (Ctrl+B)'), '0px', bindCommand('doBold'), 0);
            buttons.italic = makeButton('wmd-italic-button', gettext('Italic (Ctrl+I)'), '-20px', bindCommand('doItalic'), -1);
            makeSpacer(1);
            buttons.link = makeButton('wmd-link-button', gettext('Hyperlink (Ctrl+L)'), '-40px', bindCommand(function(chunk, postProcessing) {
                return this.doLinkOrImage(chunk, postProcessing, false);
            }), -1);
            buttons.quote = makeButton('wmd-quote-button', gettext('Blockquote (Ctrl+Q)'), '-60px', bindCommand('doBlockquote'), -1);
            buttons.code = makeButton('wmd-code-button', gettext('Code Sample (Ctrl+K)'), '-80px', bindCommand('doCode'), -1);
            buttons.image = makeButton('wmd-image-button', gettext('Image (Ctrl+G)'), '-100px', bindCommand(function(chunk, postProcessing) {
                return this.doLinkOrImage(chunk, postProcessing, true, imageUploadHandler);
            }), -1);
            makeSpacer(2);
            buttons.olist = makeButton('wmd-olist-button', gettext('Numbered List (Ctrl+O)'), '-120px', bindCommand(function(chunk, postProcessing) {
                this.doList(chunk, postProcessing, true);
            }), -1);
            buttons.ulist = makeButton('wmd-ulist-button', gettext('Bulleted List (Ctrl+U)'), '-140px', bindCommand(function(chunk, postProcessing) {
                this.doList(chunk, postProcessing, false);
            }), -1);
            buttons.heading = makeButton('wmd-heading-button', gettext('Heading (Ctrl+H)'), '-160px', bindCommand('doHeading'), -1);
            buttons.hr = makeButton('wmd-hr-button', gettext('Horizontal Rule (Ctrl+R)'), '-180px', bindCommand('doHorizontalRule'), -1);
            makeSpacer(3);
            buttons.undo = makeButton('wmd-undo-button', gettext('Undo (Ctrl+Z)'), '-200px', null, -1);
            buttons.undo.execute = function(manager) { if (manager) { manager.undo(); } };

            // eslint-disable-next-line no-var
            var redoTitle = /win/.test(nav.platform.toLowerCase())
                ? gettext('Redo (Ctrl+Y)')
                : gettext('Redo (Ctrl+Shift+Z)'); // mac and other non-Windows platforms

            buttons.redo = makeButton('wmd-redo-button', redoTitle, '-220px', null, -1);
            buttons.redo.execute = function(manager) { if (manager) { manager.redo(); } };

            if (helpOptions) {
                // eslint-disable-next-line no-var
                var helpButton = document.createElement('span');
                // eslint-disable-next-line no-var
                var helpButtonImage = document.createElement('span');
                helpButton.appendChild(helpButtonImage);
                helpButton.className = 'wmd-button wmd-help-button';
                helpButton.id = 'wmd-help-button' + postfix;
                helpButton.XShift = '-240px';
                helpButton.isHelp = true;
                helpButton.style.right = '0px';
                helpButton.title = helpOptions.title || defaultHelpHoverTitle;
                helpButton.onclick = helpOptions.handler;

                setupButton(helpButton, true);
                buttonRow.appendChild(helpButton);
                buttons.help = helpButton;
            }

            // eslint-disable-next-line no-use-before-define
            setUndoRedoButtonStates();
        }

        function setUndoRedoButtonStates() {
            if (undoManager) {
                setupButton(buttons.undo, undoManager.canUndo());
                setupButton(buttons.redo, undoManager.canRedo());
            }
        }

        this.setUndoRedoButtonStates = setUndoRedoButtonStates;
    }

    function CommandManager(pluginHooks) {
        this.hooks = pluginHooks;
    }

    // eslint-disable-next-line no-var
    var commandProto = CommandManager.prototype;

    // The markdown symbols - 4 spaces = code, > = blockquote, etc.
    commandProto.prefixes = '(?:\\s{4,}|\\s*>|\\s*-\\s+|\\s*\\d+\\.|=|\\+|-|_|\\*|#|\\s*\\[[^\n]]+\\]:)';

    // Remove markdown symbols from the chunk selection.
    commandProto.unwrap = function(chunk) {
        // eslint-disable-next-line no-var
        var txt = new re('([^\\n])\\n(?!(\\n|' + this.prefixes + '))', 'g');
        chunk.selection = chunk.selection.replace(txt, '$1 $2');
    };

    commandProto.wrap = function(chunk, len) {
        this.unwrap(chunk); // xss-lint: disable=javascript-jquery-insertion
        // eslint-disable-next-line no-var
        var regex = new re('(.{1,' + len + '})( +|$\\n?)', 'gm'),
            that = this;

        chunk.selection = chunk.selection.replace(regex, function(line, marked) {
            if (new re('^' + that.prefixes, '').test(line)) {
                return line;
            }
            return marked + '\n';
        });

        chunk.selection = chunk.selection.replace(/\s+$/, '');
    };

    commandProto.doBold = function(chunk, postProcessing) {
        return this.doBorI(chunk, postProcessing, 2, gettext('strong text'));
    };

    commandProto.doItalic = function(chunk, postProcessing) {
        return this.doBorI(chunk, postProcessing, 1, gettext('emphasized text'));
    };

    // chunk: The selected region that will be enclosed with */**
    // nStars: 1 for italics, 2 for bold
    // insertText: If you just click the button without highlighting text, this gets inserted
    commandProto.doBorI = function(chunk, postProcessing, nStars, insertText) {
        // Get rid of whitespace and fixup newlines.
        chunk.trimWhitespace();
        chunk.selection = chunk.selection.replace(/\n{2,}/g, '\n');

        // Look for stars before and after.  Is the chunk already marked up?
        // note that these regex matches cannot fail
        // eslint-disable-next-line no-var
        var starsBefore = /(\**$)/.exec(chunk.before)[0];
        // eslint-disable-next-line no-var
        var starsAfter = /(^\**)/.exec(chunk.after)[0];

        // eslint-disable-next-line no-var
        var prevStars = Math.min(starsBefore.length, starsAfter.length);

        // Remove stars if we have to since the button acts as a toggle.
        // eslint-disable-next-line eqeqeq
        if ((prevStars >= nStars) && (prevStars != 2 || nStars != 1)) {
            chunk.before = chunk.before.replace(re('[*]{' + nStars + '}$', ''), '');
            chunk.after = chunk.after.replace(re('^[*]{' + nStars + '}', ''), '');
        } else if (!chunk.selection && starsAfter) {
            // It's not really clear why this code is necessary.  It just moves
            // some arbitrary stuff around.
            chunk.after = chunk.after.replace(/^([*_]*)/, '');
            chunk.before = chunk.before.replace(/(\s?)$/, '');
            // eslint-disable-next-line no-var
            var whitespace = re.$1;
            chunk.before = chunk.before + starsAfter + whitespace;
        } else {
            // In most cases, if you don't have any selected text and click the button
            // you'll get a selected, marked up region with the default text inserted.
            if (!chunk.selection && !starsAfter) {
                chunk.selection = insertText;
            }

            // Add the true markup.
            // eslint-disable-next-line no-var
            var markup = nStars <= 1 ? '*' : '**'; // shouldn't the test be = ?
            chunk.before += markup;
            chunk.after = markup + chunk.after;
        }
    };

    commandProto.stripLinkDefs = function(text, defsToAdd) {
        text = text.replace(/^[ ]{0,3}\[(\d+)\]:[ \t]*\n?[ \t]*<?(\S+?)>?[ \t]*\n?[ \t]*(?:(\n*)["(](.+?)[")][ \t]*)?(?:\n+|$)/gm,
            function(totalMatch, id, link, newlines, title) {
                defsToAdd[id] = totalMatch.replace(/\s*$/, '');
                if (newlines) {
                    // Strip the title and return that separately.
                    defsToAdd[id] = totalMatch.replace(/["(](.+?)[")]$/, '');
                    return newlines + title;
                }
                return '';
            });

        return text;
    };

    commandProto.addLinkDef = function(chunk, linkDef) {
        // eslint-disable-next-line no-var
        var refNumber = 0; // The current reference number
        // eslint-disable-next-line no-var
        var defsToAdd = {}; //
        // Start with a clean slate by removing all previous link definitions.
        chunk.before = this.stripLinkDefs(chunk.before, defsToAdd);
        chunk.selection = this.stripLinkDefs(chunk.selection, defsToAdd);
        chunk.after = this.stripLinkDefs(chunk.after, defsToAdd);

        // eslint-disable-next-line no-var
        var defs = '';
        /* eslint-disable-next-line no-useless-escape, no-var */
        var regex = /(\[)((?:\[[^\]]*\]|[^\[\]])*)(\][ ]?(?:\n[ ]*)?\[)(\d+)(\])/g;

        // eslint-disable-next-line no-var
        var addDefNumber = function(def) {
            refNumber++;
            def = def.replace(/^[ ]{0,3}\[(\d+)\]:/, '  [' + refNumber + ']:');
            defs += '\n' + def;
        };

        // note that
        // a) the recursive call to getLink cannot go infinite, because by definition
        //    of regex, inner is always a proper substring of wholeMatch, and
        // b) more than one level of nesting is neither supported by the regex
        //    nor making a lot of sense (the only use case for nesting is a linked image)
        // eslint-disable-next-line no-var
        var getLink = function(wholeMatch, before, inner, afterInner, id, end) {
            inner = inner.replace(regex, getLink);
            if (defsToAdd[id]) {
                addDefNumber(defsToAdd[id]);
                return before + inner + afterInner + refNumber + end;
            }
            return wholeMatch;
        };

        chunk.before = chunk.before.replace(regex, getLink);

        if (linkDef) {
            addDefNumber(linkDef);
        } else {
            chunk.selection = chunk.selection.replace(regex, getLink);
        }

        // eslint-disable-next-line no-var
        var refOut = refNumber;

        chunk.after = chunk.after.replace(regex, getLink);

        if (chunk.after) {
            chunk.after = chunk.after.replace(/\n*$/, '');
        }
        if (!chunk.after) {
            chunk.selection = chunk.selection.replace(/\n*$/, '');
        }

        chunk.after += '\n\n' + defs;

        return refOut;
    };

    // takes the line as entered into the add link/as image dialog and makes
    // sure the URL and the optinal title are "nice".
    function properlyEncoded(linkdef) {
        return linkdef.replace(/^\s*(.*?)(?:\s+"(.+)")?\s*$/, function(wholematch, link, title) {
            link = link.replace(/\?.*$/, function(querypart) {
                return querypart.replace(/\+/g, ' '); // in the query string, a plus and a space are identical
            });
            link = decodeURIComponent(link); // unencode first, to prevent double encoding
            link = encodeURI(link).replace(/'/g, '%27').replace(/\(/g, '%28').replace(/\)/g, '%29');
            link = link.replace(/\?.*$/, function(querypart) {
                return querypart.replace(/\+/g, '%2b'); // since we replaced plus with spaces in the query part, all pluses that now appear where originally encoded
            });
            if (title) {
                title = title.trim ? title.trim() : title.replace(/^\s*/, '').replace(/\s*$/, '');
                title = $.trim(title).replace(/"/g, 'quot;').replace(/\(/g, '&#40;').replace(/\)/g, '&#41;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
            }
            return title ? link + ' "' + title + '"' : link;
        });
    }

    commandProto.doLinkOrImage = function(chunk, postProcessing, isImage, imageUploadHandler) {
        chunk.trimWhitespace();
        chunk.findTags(/\s*!?\[/, /\][ ]?(?:\n[ ]*)?(\[.*?\])?/);
        // eslint-disable-next-line no-var
        var background;

        if (chunk.endTag.length > 1 && chunk.startTag.length > 0) {
            chunk.startTag = chunk.startTag.replace(/!?\[/, '');
            chunk.endTag = '';
            this.addLinkDef(chunk, null);
        } else {
            // We're moving start and end tag back into the selection, since (as we're in the else block) we're not
            // *removing* a link, but *adding* one, so whatever findTags() found is now back to being part of the
            // link text. linkEnteredCallback takes care of escaping any brackets.
            chunk.selection = chunk.startTag + chunk.selection + chunk.endTag;
            // eslint-disable-next-line no-multi-assign
            chunk.startTag = chunk.endTag = '';

            if (/\n\n/.test(chunk.selection)) {
                this.addLinkDef(chunk, null);
                return;
            }
            // eslint-disable-next-line no-var
            var that = this;
            // The function to be executed when you enter a link and press OK or Cancel.
            // Marks up the link and adds the ref.
            // eslint-disable-next-line no-var
            var linkEnteredCallback = function(link, description) {
                background.parentNode.removeChild(background);

                if (link !== null) {
                    // (                          $1
                    //     [^\\]                  anything that's not a backslash
                    //     (?:\\\\)*              an even number (this includes zero) of backslashes
                    // )
                    // (?=                        followed by
                    //     [[\]]                  an opening or closing bracket
                    // )
                    //
                    // In other words, a non-escaped bracket. These have to be escaped now to make sure they
                    // don't count as the end of the link or similar.
                    // Note that the actual bracket has to be a lookahead, because (in case of to subsequent brackets),
                    // the bracket in one match may be the "not a backslash" character in the next match, so it
                    // should not be consumed by the first match.
                    // The "prepend a space and finally remove it" steps makes sure there is a "not a backslash" at the
                    // start of the string, so this also works if the selection begins with a bracket. We cannot solve
                    // this by anchoring with ^, because in the case that the selection starts with two brackets, this
                    // would mean a zero-width match at the start. Since zero-width matches advance the string position,
                    // the first bracket could then not act as the "not a backslash" for the second.
                    chunk.selection = (' ' + chunk.selection).replace(/([^\\](?:\\\\)*)(?=[[\]])/g, '$1\\').substr(1);

                    // eslint-disable-next-line no-var
                    var linkDef = ' [999]: ' + properlyEncoded(link);

                    // eslint-disable-next-line no-var
                    var num = that.addLinkDef(chunk, linkDef);
                    chunk.startTag = isImage ? '![' : '[';
                    chunk.endTag = '][' + num + ']';

                    if (!chunk.selection) {
                        if (isImage) {
                            chunk.selection = description || '';
                        } else {
                            chunk.selection = description || gettext('enter link description here');
                        }
                    }
                }
                postProcessing();
            };

            background = ui.createBackground();

            if (isImage) {
                if (!this.hooks.insertImageDialog(linkEnteredCallback)) {
                    ui.prompt(
                        imageDialogText,
                        urlLabel,
                        imageUrlHelpText,
                        urlError,
                        imageDescriptionLabel,
                        imageDescriptionHelpText,
                        imageDescriptionHelpLink,
                        imageDescError,
                        imageDefaultText,
                        linkEnteredCallback,
                        imageIsDecorativeLabel,
                        imageUploadHandler
                    );
                }
            } else {
                ui.prompt(
                    linkDialogText,
                    urlLabel,
                    linkUrlHelpText,
                    urlError,
                    linkDestinationLabel,
                    linkDestinationHelpText,
                    '',
                    linkDestinationError,
                    linkDefaultText,
                    linkEnteredCallback
                );
            }
            // eslint-disable-next-line consistent-return
            return true;
        }
    };

    // When making a list, hitting shift-enter will put your cursor on the next line
    // at the current indent level.
    // eslint-disable-next-line no-unused-vars
    commandProto.doAutoindent = function(chunk, postProcessing) {
        // eslint-disable-next-line no-var
        var commandMgr = this,
            fakeSelection = false;

        chunk.before = chunk.before.replace(/(\n|^)[ ]{0,3}([*+-]|\d+[.])[ \t]*\n$/, '\n\n');
        chunk.before = chunk.before.replace(/(\n|^)[ ]{0,3}>[ \t]*\n$/, '\n\n');
        chunk.before = chunk.before.replace(/(\n|^)[ \t]+\n$/, '\n\n');

        // There's no selection, end the cursor wasn't at the end of the line:
        // The user wants to split the current list item / code line / blockquote line
        // (for the latter it doesn't really matter) in two. Temporarily select the
        // (rest of the) line to achieve this.
        if (!chunk.selection && !/^[ \t]*(?:\n|$)/.test(chunk.after)) {
            chunk.after = chunk.after.replace(/^[^\n]*/, function(wholeMatch) {
                chunk.selection = wholeMatch;
                return '';
            });
            fakeSelection = true;
        }

        if (/(\n|^)[ ]{0,3}([*+-]|\d+[.])[ \t]+.*\n$/.test(chunk.before)) {
            if (commandMgr.doList) {
                commandMgr.doList(chunk);
            }
        }
        if (/(\n|^)[ ]{0,3}>[ \t]+.*\n$/.test(chunk.before)) {
            if (commandMgr.doBlockquote) {
                commandMgr.doBlockquote(chunk);
            }
        }
        if (/(\n|^)(\t|[ ]{4,}).*\n$/.test(chunk.before)) {
            if (commandMgr.doCode) {
                commandMgr.doCode(chunk);
            }
        }

        if (fakeSelection) {
            chunk.after = chunk.selection + chunk.after;
            chunk.selection = '';
        }
    };

    // eslint-disable-next-line no-unused-vars
    commandProto.doBlockquote = function(chunk, postProcessing) {
        chunk.selection = chunk.selection.replace(/^(\n*)([^\r]+?)(\n*)$/,
            function(totalMatch, newlinesBefore, text, newlinesAfter) {
                chunk.before += newlinesBefore;
                chunk.after = newlinesAfter + chunk.after;
                return text;
            });

        chunk.before = chunk.before.replace(/(>[ \t]*)$/,
            function(totalMatch, blankLine) {
                chunk.selection = blankLine + chunk.selection;
                return '';
            });

        chunk.selection = chunk.selection.replace(/^(\s|>)+$/, '');
        chunk.selection = chunk.selection || gettext('Blockquote');

        // The original code uses a regular expression to find out how much of the
        // text *directly before* the selection already was a blockquote:

        /*
        if (chunk.before) {
        chunk.before = chunk.before.replace(/\n?$/, "\n");
        }
        chunk.before = chunk.before.replace(/(((\n|^)(\n[ \t]*)*>(.+\n)*.*)+(\n[ \t]*)*$)/,
        function (totalMatch) {
        chunk.startTag = totalMatch;
        return "";
        });
        */

        // This comes down to:
        // Go backwards as many lines a possible, such that each line
        //  a) starts with ">", or
        //  b) is almost empty, except for whitespace, or
        //  c) is preceeded by an unbroken chain of non-empty lines
        //     leading up to a line that starts with ">" and at least one more character
        // and in addition
        //  d) at least one line fulfills a)
        //
        // Since this is essentially a backwards-moving regex, it's susceptible to
        // catstrophic backtracking and can cause the browser to hang;
        // see e.g. http://meta.stackoverflow.com/questions/9807.
        //
        // Hence we replaced this by a simple state machine that just goes through the
        // lines and checks for a), b), and c).

        // eslint-disable-next-line no-var
        var match = '',
            leftOver = '',
            line;
        if (chunk.before) {
            // eslint-disable-next-line no-var
            var lines = chunk.before.replace(/\n$/, '').split('\n');
            // eslint-disable-next-line no-var
            var inChain = false;
            // eslint-disable-next-line no-var
            for (var i = 0; i < lines.length; i++) {
                // eslint-disable-next-line no-var
                var good = false;
                line = lines[i];
                inChain = inChain && line.length > 0; // c) any non-empty line continues the chain
                if (/^>/.test(line)) { // a)
                    good = true;
                    // c) any line that starts with ">" and has at least one more character starts the chain
                    if (!inChain && line.length > 1) { inChain = true; }
                } else if (/^[ \t]*$/.test(line)) { // b)
                    good = true;
                } else {
                    good = inChain; // c) the line is not empty and does not start with ">", so it matches if and only if we're in the chain
                }
                if (good) {
                    match += line + '\n';
                } else {
                    leftOver += match + line;
                    match = '\n';
                }
            }
            if (!/(^|\n)>/.test(match)) { // d)
                leftOver += match;
                match = '';
            }
        }

        chunk.startTag = match;
        chunk.before = leftOver;

        // end of change

        if (chunk.after) {
            chunk.after = chunk.after.replace(/^\n?/, '\n');
        }

        chunk.after = chunk.after.replace(/^(((\n|^)(\n[ \t]*)*>(.+\n)*.*)+(\n[ \t]*)*)/,
            function(totalMatch) {
                chunk.endTag = totalMatch;
                return '';
            }
        );

        // eslint-disable-next-line no-var
        var replaceBlanksInTags = function(useBracket) {
            // eslint-disable-next-line no-var
            var replacement = useBracket ? '> ' : '';

            if (chunk.startTag) {
                chunk.startTag = chunk.startTag.replace(/\n((>|\s)*)\n$/,
                    function(totalMatch, markdown) {
                        return '\n' + markdown.replace(/^[ ]{0,3}>?[ \t]*$/gm, replacement) + '\n';
                    });
            }
            if (chunk.endTag) {
                chunk.endTag = chunk.endTag.replace(/^\n((>|\s)*)\n/,
                    function(totalMatch, markdown) {
                        return '\n' + markdown.replace(/^[ ]{0,3}>?[ \t]*$/gm, replacement) + '\n';
                    });
            }
        };

        if (/^(?![ ]{0,3}>)/m.test(chunk.selection)) {
            this.wrap(chunk, SETTINGS.lineLength - 2); // xss-lint: disable=javascript-jquery-insertion
            chunk.selection = chunk.selection.replace(/^/gm, '> ');
            replaceBlanksInTags(true);
            chunk.skipLines();
        } else {
            chunk.selection = chunk.selection.replace(/^[ ]{0,3}> ?/gm, '');
            this.unwrap(chunk); // xss-lint: disable=javascript-jquery-insertion
            replaceBlanksInTags(false);

            if (!/^(\n|^)[ ]{0,3}>/.test(chunk.selection) && chunk.startTag) {
                chunk.startTag = chunk.startTag.replace(/\n{0,2}$/, '\n\n');
            }

            if (!/(\n|^)[ ]{0,3}>.*$/.test(chunk.selection) && chunk.endTag) {
                chunk.endTag = chunk.endTag.replace(/^\n{0,2}/, '\n\n');
            }
        }

        chunk.selection = this.hooks.postBlockquoteCreation(chunk.selection);

        if (!/\n/.test(chunk.selection)) {
            chunk.selection = chunk.selection.replace(/^(> *)/,
                function(wholeMatch, blanks) {
                    chunk.startTag += blanks;
                    return '';
                });
        }
    };

    // eslint-disable-next-line no-unused-vars
    commandProto.doCode = function(chunk, postProcessing) {
        // eslint-disable-next-line no-var
        var hasTextBefore = /\S[ ]*$/.test(chunk.before);
        // eslint-disable-next-line no-var
        var hasTextAfter = /^[ ]*\S/.test(chunk.after);

        // Use 'four space' markdown if the selection is on its own
        // line or is multiline.
        if ((!hasTextAfter && !hasTextBefore) || /\n/.test(chunk.selection)) {
            chunk.before = chunk.before.replace(/[ ]{4}$/,
                function(totalMatch) {
                    chunk.selection = totalMatch + chunk.selection;
                    return '';
                });

            // eslint-disable-next-line no-var
            var nLinesBack = 1;
            // eslint-disable-next-line no-var
            var nLinesForward = 1;

            if (/(\n|^)(\t|[ ]{4,}).*\n$/.test(chunk.before)) {
                nLinesBack = 0;
            }
            if (/^\n(\t|[ ]{4,})/.test(chunk.after)) {
                nLinesForward = 0;
            }

            chunk.skipLines(nLinesBack, nLinesForward);

            if (!chunk.selection) {
                chunk.startTag = '    ';
                chunk.selection = gettext('enter code here');
            } else {
                if (/^[ ]{0,3}\S/m.test(chunk.selection)) {
                    if (/\n/.test(chunk.selection)) { chunk.selection = chunk.selection.replace(/^/gm, '    '); } else // if it's not multiline, do not select the four added spaces; this is more consistent with the doList behavior
                    // eslint-disable-next-line brace-style
                    { chunk.before += '    '; }
                } else {
                    chunk.selection = chunk.selection.replace(/^[ ]{4}/gm, '');
                }
            }
        } else {
            // Use backticks (`) to delimit the code block.

            chunk.trimWhitespace();
            chunk.findTags(/`/, /`/);

            if (!chunk.startTag && !chunk.endTag) {
                // eslint-disable-next-line no-multi-assign
                chunk.startTag = chunk.endTag = '`';
                if (!chunk.selection) {
                    chunk.selection = gettext('enter code here');
                }
            } else if (chunk.endTag && !chunk.startTag) {
                chunk.before += chunk.endTag;
                chunk.endTag = '';
            } else {
                // eslint-disable-next-line no-multi-assign
                chunk.startTag = chunk.endTag = '';
            }
        }
    };

    commandProto.doList = function(chunk, postProcessing, isNumberedList) {
        // These are identical except at the very beginning and end.
        // Should probably use the regex extension function to make this clearer.
        // eslint-disable-next-line no-var
        var previousItemsRegex = /(\n|^)(([ ]{0,3}([*+-]|\d+[.])[ \t]+.*)(\n.+|\n{2,}([*+-].*|\d+[.])[ \t]+.*|\n{2,}[ \t]+\S.*)*)\n*$/;
        // eslint-disable-next-line no-var
        var nextItemsRegex = /^\n*(([ ]{0,3}([*+-]|\d+[.])[ \t]+.*)(\n.+|\n{2,}([*+-].*|\d+[.])[ \t]+.*|\n{2,}[ \t]+\S.*)*)\n*/;

        // The default bullet is a dash but others are possible.
        // This has nothing to do with the particular HTML bullet,
        // it's just a markdown bullet.
        // eslint-disable-next-line no-var
        var bullet = '-';

        // The number in a numbered list.
        // eslint-disable-next-line no-var
        var num = 1;

        // Get the item prefix - e.g. " 1. " for a numbered list, " - " for a bulleted list.
        // eslint-disable-next-line no-var
        var getItemPrefix = function() {
            // eslint-disable-next-line no-var
            var prefix;
            if (isNumberedList) {
                prefix = ' ' + num + '. ';
                num++;
            } else {
                prefix = ' ' + bullet + ' ';
            }
            return prefix;
        };

        // Fixes the prefixes of the other list items.
        // eslint-disable-next-line no-var
        var getPrefixedItem = function(itemText) {
            // The numbering flag is unset when called by autoindent.
            if (isNumberedList === undefined) {
                isNumberedList = /^\s*\d/.test(itemText);
            }

            // Renumber/bullet the list element.
            itemText = itemText.replace(/^[ ]{0,3}([*+-]|\d+[.])\s/gm,
                // eslint-disable-next-line no-unused-vars
                function(_) {
                    return getItemPrefix();
                });

            return itemText;
        };

        chunk.findTags(/(\n|^)*[ ]{0,3}([*+-]|\d+[.])\s+/, null);

        if (chunk.before && !/\n$/.test(chunk.before) && !/^\n/.test(chunk.startTag)) {
            chunk.before += chunk.startTag;
            chunk.startTag = '';
        }

        if (chunk.startTag) {
            // eslint-disable-next-line no-var
            var hasDigits = /\d+[.]/.test(chunk.startTag);
            chunk.startTag = '';
            chunk.selection = chunk.selection.replace(/\n[ ]{4}/g, '\n');
            this.unwrap(chunk); // xss-lint: disable=javascript-jquery-insertion
            chunk.skipLines();

            if (hasDigits) {
                // Have to renumber the bullet points if this is a numbered list.
                chunk.after = chunk.after.replace(nextItemsRegex, getPrefixedItem);
            }
            // eslint-disable-next-line eqeqeq
            if (isNumberedList == hasDigits) {
                return;
            }
        }

        // eslint-disable-next-line no-var
        var nLinesUp = 1;

        chunk.before = chunk.before.replace(previousItemsRegex,
            function(itemText) {
                if (/^\s*([*+-])/.test(itemText)) {
                    bullet = re.$1;
                }
                nLinesUp = /[^\n]\n\n[^\n]/.test(itemText) ? 1 : 0;
                return getPrefixedItem(itemText);
            });

        if (!chunk.selection) {
            chunk.selection = gettext('List item');
        }

        // eslint-disable-next-line no-var
        var prefix = getItemPrefix();

        // eslint-disable-next-line no-var
        var nLinesDown = 1;

        chunk.after = chunk.after.replace(nextItemsRegex,
            function(itemText) {
                nLinesDown = /[^\n]\n\n[^\n]/.test(itemText) ? 1 : 0;
                return getPrefixedItem(itemText);
            });

        chunk.trimWhitespace(true);
        chunk.skipLines(nLinesUp, nLinesDown, true);
        chunk.startTag = prefix;
        // eslint-disable-next-line no-var
        var spaces = prefix.replace(/./g, ' ');
        this.wrap(chunk, SETTINGS.lineLength - spaces.length); // xss-lint: disable=javascript-jquery-insertion
        chunk.selection = chunk.selection.replace(/\n/g, '\n' + spaces);
    };

    // eslint-disable-next-line no-unused-vars
    commandProto.doHeading = function(chunk, postProcessing) {
        // Remove leading/trailing whitespace and reduce internal spaces to single spaces.
        chunk.selection = chunk.selection.replace(/\s+/g, ' ');
        chunk.selection = chunk.selection.replace(/(^\s+|\s+$)/g, '');

        // If we clicked the button with no selected text, we just
        // make a level 2 hash header around some default text.
        if (!chunk.selection) {
            chunk.startTag = '## ';
            chunk.selection = gettext('Heading');
            chunk.endTag = ' ##';
            return;
        }

        // eslint-disable-next-line no-var
        var headerLevel = 0; // The existing header level of the selected text.

        // Remove any existing hash heading markdown and save the header level.
        chunk.findTags(/#+[ ]*/, /[ ]*#+/);
        if (/#+/.test(chunk.startTag)) {
            headerLevel = re.lastMatch.length;
        }
        // eslint-disable-next-line no-multi-assign
        chunk.startTag = chunk.endTag = '';

        // Try to get the current header level by looking for - and = in the line
        // below the selection.
        chunk.findTags(null, /\s?(-+|=+)/);
        if (/=+/.test(chunk.endTag)) {
            headerLevel = 1;
        }
        if (/-+/.test(chunk.endTag)) {
            headerLevel = 2;
        }

        // Skip to the next line so we can create the header markdown.
        // eslint-disable-next-line no-multi-assign
        chunk.startTag = chunk.endTag = '';
        chunk.skipLines(1, 1);

        // We make a level 2 header if there is no current header.
        // If there is a header level, we substract one from the header level.
        // If it's already a level 1 header, it's removed.
        /* eslint-disable-next-line eqeqeq, no-var */
        var headerLevelToCreate = headerLevel == 0 ? 2 : headerLevel - 1;

        if (headerLevelToCreate > 0) {
            // The button only creates level 1 and 2 underline headers.
            // Why not have it iterate over hash header levels?  Wouldn't that be easier and cleaner?
            // eslint-disable-next-line no-var
            var headerChar = headerLevelToCreate >= 2 ? '-' : '=';
            // eslint-disable-next-line no-var
            var len = chunk.selection.length;
            if (len > SETTINGS.lineLength) {
                len = SETTINGS.lineLength;
            }
            chunk.endTag = '\n';
            while (len--) {
                chunk.endTag += headerChar;
            }
        }
    };

    // eslint-disable-next-line no-unused-vars
    commandProto.doHorizontalRule = function(chunk, postProcessing) {
        chunk.startTag = '----------\n';
        chunk.selection = '';
        chunk.skipLines(2, 1, true);
    };
}());
