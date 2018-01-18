import _ from 'underscore';
import Backbone from 'backbone';

import certificateTpl from '../../../templates/learner_dashboard/certificate_list.underscore';

class CertificateListView extends Backbone.View {
  initialize(options) {
    this.tpl = _.template(certificateTpl);
    this.title = options.title || false;
    this.render();
  }

  render() {
    const data = {
      title: this.title,
      certificateList: this.collection.toJSON(),
    };

    this.$el.html(this.tpl(data));
  }
}

export default CertificateListView;
