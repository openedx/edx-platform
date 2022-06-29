/**
 * plugin.js
 *
 * Copyright 2013 Web Power, www.webpower.nl
 * @author Arjan Haverkamp
 */

/* jshint unused:false */
/* global tinymce:true */

tinymce.PluginManager.requireLangPack('codemirror')

tinymce.PluginManager.add('codemirror', function (editor, url) {
    function showSourceEditor() {
        editor.focus()
        editor.selection.collapse(true)

        // Insert caret marker
        if (editor.settings.codemirror.saveCursorPosition) {
            editor.selection.setContent('<span style="display: none;" class="CmCaReT">&#x0;</span>')
        }

        // EDX: Use Iframe based URLs
        // Determine the origin of the window that will host the code editor.
        // If tinyMCE's baseURL is relative, then static files are hosted in the
        // same origin as the containing page. If it is not relative, then we know that
        // the origin of the iframe hosting the code editor will match the origin
        // of tinyMCE's baseURL, as they are both hosted on the CDN.
        var codeEditorOrigin;
        var index = tinyMCE.baseURL.indexOf("/static/");
        if (index > 0) {
            codeEditorOrigin = tinyMCE.baseURL.substring(0, index);
        }
        else {
            codeEditorOrigin = window.location.origin;
        }

        // Send the path location for CodeMirror and the parent origin to use in postMessage.
        var sourceHtmlParams = "?CodeMirrorPath=" + editor.settings.codemirror.path +
            "&ParentOrigin=" + window.location.origin;
        var codemirrorWidth = 800
        if (editor.settings.codemirror.width) {
            codemirrorWidth = editor.settings.codemirror.width
        }

        var codemirrorHeight = 550
        if (editor.settings.codemirror.height) {
            codemirrorHeight = editor.settings.codemirror.height
        }

        var buttonsConfig = (tinymce.majorVersion < 5)
            ? [
                {
                    text: 'Ok',
                    subtype: 'primary',
                    onclick: function() {
                        var doc = document.querySelectorAll('.mce-container-body>iframe')[0]
                        doc.contentWindow.submit()
                        win.close()
                    }
                },
                {
                    text: 'Cancel',
                    onclick: 'close'
                }
            ]
            : [
                {
                    type: 'custom',
                    text: 'Ok',
                    name: 'codemirrorOk',
                    primary: true
                },
                {
                    type: 'cancel',
                    text: 'Cancel',
                    name: 'codemirrorCancel'
                }
            ]

        var config = {
            title: 'HTML source code',
            url: url + '/source.html' + sourceHtmlParams,
            width: codemirrorWidth,
            height: codemirrorHeight,
            resizable: true,
            maximizable: true,
            fullScreen: editor.settings.codemirror.fullscreen,
            saveCursorPosition: false,
            buttons: buttonsConfig,
            // EDX: Use the onClose callback to remove the message listener.
            onClose: function () {
                window.removeEventListener("message", messageListener);
            }
        }

        if (tinymce.majorVersion >= 5) {
            config.onAction = function (dialogApi, actionData) {
                // EDX: Change the onAction to use messages instead of window object references
                if (actionData.name === 'codemirrorOk') {
                    postToCodeEditor({type: "save"});
                } else if (actionData.name === 'codemirrorCancel') {
                    postToCodeEditor({type: "cancel"});
                    win.close();
                }
            }
        }

        var win = (tinymce.majorVersion < 5)
            ? editor.windowManager.open(config)
            : editor.windowManager.openUrl(config)

        // EDX: The if block is commented because,
        // In TinyMCE windowManager.openUrl returns a dialog instance API object
        // and not a window object. So fullscreen cannot be called directly on `win`. 
        // if (editor.settings.codemirror.fullscreen) {
        //     win.fullscreen(true)
        // }

        // EDX: Functions to send message to the CodeMirror Iframe and listen to
        // messages posted by the iframe
        var postToCodeEditor = function (message) {
            win.sendMessage(message);
        };
        var messageListener = function (event) {
            // Check that the message came from the code editor.
            if (codeEditorOrigin !== event.origin) {
                return;
            }

            var source;
            if (event.data.type === "init") {
                source = { content: editor.getContent({ source_view: true }) };
                // Post an event to allow rewriting of static links on the content.
                editor.fire("ShowCodeEditor", source);

                postToCodeEditor(
                    {
                        type: "init",
                        content: source.content
                    }
                );
                editor.dom.remove(editor.dom.select('.CmCaReT'));
            }
            else if (event.data.type === "setText") {
                source = { content: event.data.text };
                var isDirty = event.data.isDirty;

                // Post an event to allow rewriting of static links on the content.
                editor.fire('SaveCodeEditor', source);

                editor.setContent(source.content);

                // Set cursor:
                var el = editor.dom.select('span#CmCaReT')[0];
                if (el) {
                    editor.selection.scrollIntoView(el);
                    editor.selection.setCursorLocation(el, 0);
                    editor.dom.remove(el);
                }
                // EDX: added because CmCaReT span was getting left in when caret was within a style tag.
                // Make sure to strip it out (and accept that caret will not be in the correct place).
                else {
                    var content = editor.getContent();
                    var strippedContent = content.replace('<span id="CmCaReT"></span>', '');
                    if (content !== strippedContent) {
                        editor.setContent(strippedContent);
                    }
                }

                // EDX: moved block of code from original location since we may change content in bug fix code above.
                editor.isNotDirty = !isDirty;
                if (isDirty) {
                    editor.nodeChanged();
                }
            }
            else if (event.data.type === "closeWindow") {
                win.close();
            }
        }

        window.addEventListener("message", messageListener, false);
    }

    if (tinymce.majorVersion < 5) {
        // Add a button to the button bar
        editor.addButton('code', {
            title: 'Source code',
            icon: 'code',
            onclick: showSourceEditor
        })

        // Add a menu item to the tools menu
        editor.addMenuItem('code', {
            icon: 'code',
            text: 'Source code',
            context: 'tools',
            onclick: showSourceEditor
        })
    } else {
        // EDX changed to show "HTML" on toolbar button
        editor.ui.registry.addButton('code', {
            text: 'HTML',
            tooltip: 'Edit HTML',
            onAction: showSourceEditor
        })

        editor.ui.registry.addMenuItem('code', {
            icon: 'sourcecode',
            text: 'Edit HTML',
            onAction: showSourceEditor,
            context: 'tools'
        })
    }
})
