import * as TabsModel from 'js/models/explicit_url';
import * as TabsEditView from 'js/views/tabs';
import * as xmoduleLoader from 'xmodule';
import './base';
import 'cms/js/main';
import 'xblock/cms.runtime.v1';

'use strict';
export default function EditTabsFactory(courseLocation, explicitUrl) {
    xmoduleLoader.done(function() {
        var model = new TabsModel({
                id: courseLocation,
                explicit_url: explicitUrl
            }),
            editView;

        editView = new TabsEditView({
            el: $('.tab-list'),
            model: model,
            mast: $('.wrapper-mast')
        });
    });
};

export {EditTabsFactory}
