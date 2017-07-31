define(['js/views/xblock_validation', 'js/models/xblock_validation'],
function(XBlockValidationView, XBlockValidationModel) {
    'use strict';
    return function(validationMessages, hasEditingUrl, isRoot, isUnit, validationEle) {
        var model, response;

        if (hasEditingUrl && !isRoot) {
            validationMessages.showSummaryOnly = true;
        }
        response = validationMessages;
        response.isUnit = isUnit;

        model = new XBlockValidationModel(response, {parse: true});

        if (!model.get('empty')) {
            new XBlockValidationView({el: validationEle, model: model, root: isRoot}).render();
        }
    };
});
