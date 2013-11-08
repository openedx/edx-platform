define(["codemirror", "utility"],
    function(CodeMirror) {
        var editWithCodeMirror = function(model, contentName, baseAssetUrl, textArea) {
            var content = rewriteStaticLinks(model.get(contentName), baseAssetUrl, '/static/');
            model.set(contentName, content);
            var $codeMirror = CodeMirror.fromTextArea(textArea, {
                mode: "text/html",
                lineNumbers: true,
                lineWrapping: true
            });
            $codeMirror.setValue(content);
            $codeMirror.clearHistory();
            return $codeMirror;
        };

        var changeContentToPreview = function (model, contentName, baseAssetUrl) {
            var content = rewriteStaticLinks(model.get(contentName), '/static/', baseAssetUrl);
            model.set(contentName, content);
            return content;
        };

        return {'editWithCodeMirror': editWithCodeMirror, 'changeContentToPreview': changeContentToPreview};
    }
);
