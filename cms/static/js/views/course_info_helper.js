define(["codemirror", 'js/utils/handle_iframe_binding', "utility"],
    function(CodeMirror, IframeBinding) {
        var editWithCodeMirror = function(model, contentName, baseAssetUrl, textArea) {
            var content = rewriteStaticLinks(model.get(contentName), baseAssetUrl, '/static/');
            model.set(contentName, content);
            var $codeMirror = CodeMirror.fromTextArea(textArea, {
                mode: "text/html",
                lineNumbers: true,
                lineWrapping: true,
                autoCloseTags: true
            });
            $codeMirror.on('change', function () {
                    $('.save-button').removeClass('is-disabled').attr('aria-disabled', false);
            });
            $codeMirror.setValue(content);
            $codeMirror.clearHistory();
            return $codeMirror;
        };

        var changeContentToPreview = function (model, contentName, baseAssetUrl) {
            var content = rewriteStaticLinks(model.get(contentName), '/static/', baseAssetUrl);
            // Modify iframe (add wmode=transparent in url querystring) and embed (add wmode=transparent as attribute)
            // tags in html string (content) so both tags will attach to dom and don't create z-index problem for other popups
            // Note: content is modified before assigning to model because embed tags should be modified before rendering
            // as they are static objects as compared to iframes
            content = IframeBinding.iframeBindingHtml(content);
            model.set(contentName, content);
            return content;
        };

        return {'editWithCodeMirror': editWithCodeMirror, 'changeContentToPreview': changeContentToPreview};
    }
);
