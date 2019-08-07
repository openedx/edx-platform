import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import certificateTpl from '../../../templates/learner_dashboard/certificate_list.underscore';

class CertificateListView extends Backbone.View {
  initialize(options) {
    this.tpl = HtmlUtils.template(certificateTpl);
    this.title = options.title || false;
    this.render();
  }

  render() {
    const data = {
      title: this.title,
      certificateList: this.collection.toJSON(),
    };

    HtmlUtils.setHtml(this.$el, this.tpl(data));
  }
}

export default CertificateListView;
