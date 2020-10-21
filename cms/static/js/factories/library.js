import * as $ from 'jquery';
import * as _ from 'underscore';
import * as XBlockInfo from 'js/models/xblock_info';
import * as PagedContainerPage from 'js/views/pages/paged_container';
import * as LibraryContainerView from 'js/views/library_container';
import * as ComponentTemplates from 'js/collections/component_template';
import * as xmoduleLoader from 'xmodule';
import './base';
import 'cms/js/main';
import 'xblock/cms.runtime.v1';

'use strict';
export default function LibraryFactory(componentTemplates, XBlockInfoJson, options) {
    var main_options = {
        el: $('#content'),
        model: new XBlockInfo(XBlockInfoJson, {parse: true}),
        templates: new ComponentTemplates(componentTemplates, {parse: true}),
        action: 'view',
        viewClass: LibraryContainerView,
        canEdit: true
    };

    xmoduleLoader.done(function() {
        var view = new PagedContainerPage(_.extend(main_options, options));
        view.render();
    });
};

export {LibraryFactory}
