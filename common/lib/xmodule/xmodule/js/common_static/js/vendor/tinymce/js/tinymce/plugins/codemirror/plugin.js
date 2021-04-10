/**
 * plugin.js
 *
 * Copyright 2013 Web Power, www.webpower.nl
 * @author Arjan Haverkamp
 */

/*jshint unused:false */
/*global tinymce:true */

tinymce.PluginManager.requireLangPack('codemirror');

tinymce.PluginManager.add('codemirror', function(editor, url) {

	function showSourceEditor() {
		// Insert caret marker
		editor.focus();
		editor.selection.collapse(true);
		editor.selection.setContent('<span class="CmCaReT" style="display:none">&#0;</span>');

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

		// Open editor window
		var win = editor.windowManager.open({
			title: 'HTML source code',
            url: url + '/source.html' + sourceHtmlParams,
            width: 800,
            height: 550,
            resizable: true,
            maximizable: true,
            buttons: [
                { text: 'OK', subtype: 'primary', onclick: function () {
                    postToCodeEditor({type: "save"});
                }},
                { text: 'Cancel', onclick: function () {
                    postToCodeEditor({type: "cancel"});
                }}
            ]

        });

        // The master version of TinyMCE has a win.getContentWindow() method. This is its implementation.
        var codeWindow = win.getEl().getElementsByTagName('iframe')[0].contentWindow;

        var postToCodeEditor = function (data) {
            codeWindow.postMessage(data, codeEditorOrigin);
        };

        var messageListener = function (event) {
            // Check that the message came from the code editor.
            if (codeEditorOrigin !== event.origin) {
                return;
            }

            var source;
            if (event.data.type === "init") {
                source = {content: editor.getContent({source_view: true})};
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
                source = {content: event.data.text};
                var isDirty = event.data.isDirty;

                // Post an event to allow rewriting of static links on the content.
                editor.fire('SaveCodeEditor', source);

                editor.setContent(source.content);

                // Set cursor:
                var el = editor.dom.select('span#CmCaReT')[0];
                if (el) {
                    editor.selection.scrollIntoView(el);
                    editor.selection.setCursorLocation(el,0);
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
        };

        win.on("close", function() {
            window.removeEventListener("message", messageListener);
        });

        window.addEventListener("message", messageListener, false);

	}

	// Add a button to the button bar
    // EDX changed to show "HTML" on toolbar button
	editor.addButton('code', {
		title: 'Edit HTML',
        text: 'HTML',
		icon: false,
		onclick: showSourceEditor
	});

	// Add a menu item to the tools menu
	editor.addMenuItem('code', {
		icon: 'code',
		text: 'Edit HTML',
		context: 'tools',
		onclick: showSourceEditor
	});
});
