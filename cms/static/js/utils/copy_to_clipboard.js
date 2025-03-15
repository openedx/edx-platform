define(['jquery'], function($) {
    'use strict';

    function copyToClipboard(id, textToCopy) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(textToCopy);
            changeButtonText(id);
            return;
        }
        const textArea = document.createElement('textarea');
        textArea.value = textToCopy;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        changeButtonText(id);
    }

    function changeButtonText(id, delay = 2000) {
        const buttonId = `#${id}`;
        const textClass = '.copy-link-button-text';

        const previewShareLinkText = $(buttonId).find(textClass).html();
        const shareLinkCopiedText = gettext('Copied');
        $(buttonId).find(textClass).text(shareLinkCopiedText);

        setTimeout(() => {
            $(buttonId).find(textClass).text(previewShareLinkText);
        }, delay);
    }
    return {copyToClipboard};
});
