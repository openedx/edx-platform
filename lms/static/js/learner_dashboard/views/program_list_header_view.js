import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import programListHeaderTpl from '../../../templates/learner_dashboard/program_list_header_view.underscore';

class ProgramListHeaderView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-program-list-header',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize({ context }) {
        this.context = context;
        this.tpl = HtmlUtils.template(programListHeaderTpl);
        this.render();
    }

    render() {
        HtmlUtils.setHtml(this.$el, this.tpl(this.context));
    }
}

export default ProgramListHeaderView;
