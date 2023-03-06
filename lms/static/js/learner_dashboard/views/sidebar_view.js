import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import NewProgramsView from './explore_new_programs_view';

import sidebarTpl from '../../../templates/learner_dashboard/sidebar.underscore';

class SidebarView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.sidebar',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(data) {
        this.tpl = HtmlUtils.template(sidebarTpl);
        this.context = data.context;
    }

    render() {
        HtmlUtils.setHtml(this.$el, this.tpl(this.context));
        this.postRender();
    }

    postRender() {
        this.newProgramsView = new NewProgramsView({
            context: this.context,
        });
    }
}

export default SidebarView;
