/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
