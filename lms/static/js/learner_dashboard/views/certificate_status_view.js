import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import certificateStatusTpl from '../../../templates/learner_dashboard/certificate_status.underscore';
import certificateIconTpl from '../../../templates/learner_dashboard/certificate_icon.underscore';

class CertificateStatusView extends Backbone.View {
    initialize(options) {
        this.statusTpl = HtmlUtils.template(certificateStatusTpl);
        this.iconTpl = HtmlUtils.template(certificateIconTpl);
        this.$el = options.$el;
        this.render();
    }

    render() {
        let data = this.model.toJSON();

        data = $.extend(data, { certificateSvg: this.iconTpl() });
        HtmlUtils.setHtml(this.$el, this.statusTpl(data));
    }
}

export default CertificateStatusView;
