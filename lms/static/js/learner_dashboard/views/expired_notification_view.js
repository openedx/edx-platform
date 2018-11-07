import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import expiredNotificationTpl from '../../../templates/learner_dashboard/expired_notification.underscore';

class ExpiredNotificationView extends Backbone.View {
  initialize(options) {
    this.expiredNotificationTpl = HtmlUtils.template(expiredNotificationTpl);
    this.$el = options.$el;
    this.render();
  }

  render() {
    const data = this.model.toJSON();
    HtmlUtils.setHtml(this.$el, this.expiredNotificationTpl(data));
  }
}

export default ExpiredNotificationView;
