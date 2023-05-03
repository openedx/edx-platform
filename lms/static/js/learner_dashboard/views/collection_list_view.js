import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import emptyProgramsListTpl from '../../../templates/learner_dashboard/empty_programs_list.underscore';

class CollectionListView extends Backbone.View {
    initialize(data) {
        this.childView = data.childView;
        this.context = data.context;
        this.titleContext = data.titleContext;
    }

    render() {
        if (!this.collection.length) {
            if (this.context.marketingUrl) {
                // Only show the advertising panel if the link is passed in
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(emptyProgramsListTpl)(this.context));
            }
        } else {
            const childList = [];

            this.collection.each((model) => {
                const child = new this.childView({ // eslint-disable-line new-cap
                    model,
                    context: this.context,
                });
                childList.push(child.el);
            }, this);

            if (this.titleContext) {
                this.$el.before(HtmlUtils.ensureHtml(this.getTitleHtml()).toString());
            }

            this.$el.html(HtmlUtils.HTML(childList).toString());
        }
    }

    getTitleHtml() {
        const titleHtml = HtmlUtils.joinHtml(
            HtmlUtils.HTML('<'),
            this.titleContext.el,
            HtmlUtils.HTML(' class="sr-only collection-title">'),
            StringUtils.interpolate(this.titleContext.title),
            HtmlUtils.HTML('</'),
            this.titleContext.el,
            HtmlUtils.HTML('>'));
        return titleHtml;
    }
}

export default CollectionListView;
