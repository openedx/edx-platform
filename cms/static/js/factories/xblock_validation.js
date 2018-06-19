
import * as XBlockValidationView from 'js/views/xblock_validation';
import * as XBlockValidationModel from 'js/models/xblock_validation';

'use strict';
export default function XBlockValidationFactory(validationMessages, hasEditingUrl, isRoot, isUnit, validationEle) {
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

export {XBlockValidationFactory}
