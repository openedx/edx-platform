import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import exploreTpl from '../../../templates/learner_dashboard/explore_new_programs.underscore';

class ExploreNewProgramsView extends Backbone.View {
  constructor(options) {
    const defaults = {
      el: '.program-advertise',
    };
    super(Object.assign({}, defaults, options));
  }

  initialize(data) {
    this.tpl = HtmlUtils.template(exploreTpl);
    this.context = data.context;
    this.$parentEl = $(this.parentEl);

    if (this.context.marketingUrl) {
      // Only render if there is a link
      this.render();
    } else {
      // If not rendering, remove el because styles are applied to it
      this.remove();
    }
  }

  render() {
    HtmlUtils.setHtml(this.$el, this.tpl(this.context));
  }
}

export default ExploreNewProgramsView;
