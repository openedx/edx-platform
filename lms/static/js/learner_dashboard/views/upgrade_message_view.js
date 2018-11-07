import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import upgradeMessageTpl from '../../../templates/learner_dashboard/upgrade_message.underscore';

class UpgradeMessageView extends Backbone.View {
  initialize(options) {
    this.messageTpl = HtmlUtils.template(upgradeMessageTpl);
    this.$el = options.$el;
    this.render();
  }

  render() {
    const data = this.model.toJSON();
    HtmlUtils.setHtml(this.$el, this.messageTpl(data));
  }
}

export default UpgradeMessageView;
