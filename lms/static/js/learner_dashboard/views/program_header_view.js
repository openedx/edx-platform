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
        // eslint-disable-next-line prefer-object-spread
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
        // eslint-disable-next-line prefer-destructuring
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

<<<<<<< HEAD
    getIsSubscribed() {
        const isSubscriptionEligible = this.model.get('isSubscriptionEligible');
        const subscriptionData = this.model.get('subscriptionData')?.[0];

        return (
            isSubscriptionEligible &&
            subscriptionData?.subscription_state === 'active'
        );
    }

=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    render() {
        // eslint-disable-next-line no-undef
        const data = $.extend(this.model.toJSON(), {
            breakpoints: this.breakpoints,
            logo: this.getLogo(),
<<<<<<< HEAD
            isSubscribed: this.getIsSubscribed(),
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        });

        if (this.model.get('programData')) {
            HtmlUtils.setHtml(this.$el, this.tpl(data));
        }
    }
}

export default ProgramHeaderView;
