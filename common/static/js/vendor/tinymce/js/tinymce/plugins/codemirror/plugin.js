/**
 * plugin.js
 *
 * Copyright 2013 Web Power, www.webpower.nl
 * @author Arjan Haverkamp
 */

/* jshint unused:false */
/* global tinymce:true */

tinymce.PluginManager.requireLangPack('codemirror')

tinymce.PluginManager.add('codemirror', function(editor, url) {
    function showSourceEditor() {
        editor.focus()
        editor.selection.collapse(true)

        // Insert caret marker
        if (editor.settings.codemirror.saveCursorPosition) {
            editor.selection.setContent('<span style="display: none;" class="CmCaReT">&#x0;</span>')
        }

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
            url: url + '/source.html',
            width: codemirrorWidth,
            height: codemirrorHeight,
            resizable: true,
            maximizable: true,
            fullScreen: editor.settings.codemirror.fullscreen,
            saveCursorPosition: false,
            buttons: buttonsConfig
        }

        if (tinymce.majorVersion >= 5) {
            config.onAction = function (dialogApi, actionData) {
                if (actionData.name === 'codemirrorOk') {
                    var doc = document.querySelectorAll('.tox-dialog__body-iframe iframe')[0]
                    doc.contentWindow.submit()
                    editor.undoManager.add()
                    win.close()
                }
            }
        }

        var win = (tinymce.majorVersion < 5)
            ? editor.windowManager.open(config)
            : editor.windowManager.openUrl(config)

        if (editor.settings.codemirror.fullscreen) {
            win.fullscreen(true)
        }
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
