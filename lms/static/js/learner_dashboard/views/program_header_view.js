import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import pageTpl from '../../../templates/learner_dashboard/program_header_view.underscore';
import MicroMastersLogo from '../../../images/programs/micromasters-program-details.svg';
import XSeriesLogo from '../../../images/programs/xseries-program-details.svg';
import ProfessionalCertificateLogo from '../../../images/programs/professional-certificate-program-details.svg';

class ProgramHeaderView extends Backbone.View {
  constructor(options) {
    const defaults = {
      el: '.js-program-header',
    };
    super(Object.assign({}, defaults, options));
  }

  initialize() {
    this.breakpoints = {
      min: {
        medium: '768px',
        large: '1180px',
      },
    };
    this.tpl = HtmlUtils.template(pageTpl);
    this.render();
  }

  getLogo() {
    const type = this.model.get('programData').type;
    let logo = false;

    if (type === 'MicroMasters') {
      logo = MicroMastersLogo;
    } else if (type === 'XSeries') {
      logo = XSeriesLogo;
    } else if (type === 'Professional Certificate') {
      logo = ProfessionalCertificateLogo;
    }
    return logo;
  }

  render() {
    const data = $.extend(this.model.toJSON(), {
      breakpoints: this.breakpoints,
      logo: this.getLogo(),
    });

    if (this.model.get('programData')) {
      HtmlUtils.setHtml(this.$el, this.tpl(data));
    }
  }
}

export default ProgramHeaderView;
