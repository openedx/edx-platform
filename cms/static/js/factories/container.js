import * as $ from 'jquery';
import * as _ from 'underscore';
import * as XBlockContainerInfo from 'js/models/xblock_container_info';
import * as ContainerPage from 'js/views/pages/container';
import * as ComponentTemplates from 'js/collections/component_template';
import * as xmoduleLoader from 'xmodule';
import './base';
import 'cms/js/main';
import 'xblock/cms.runtime.v1';

'use strict';
export default function ContainerFactory(componentTemplates, XBlockInfoJson, action, options) {
    var main_options = {
        el: $('#content'),
        model: new XBlockContainerInfo(XBlockInfoJson, {parse: true}),
        action: action,
        templates: new ComponentTemplates(componentTemplates, {parse: true})
    };

    xmoduleLoader.done(function() {
        var view = new ContainerPage(_.extend(main_options, options));
        view.render();
    });
};

export {ContainerFactory}
