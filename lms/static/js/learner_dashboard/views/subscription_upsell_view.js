/* eslint-disable import/no-extraneous-dependencies, import/no-duplicates,
 import/order, import/no-self-import, import/no-cycle, import/no-useless-path-segments,
  import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member */
// eslint-disable-next-line import/no-extraneous-dependencies
import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import subscriptionUpsellTpl from '../../../templates/learner_dashboard/subscription_upsell_view.underscore';

class SubscriptionUpsellView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-subscription-upsell',
        };
        // eslint-disable-next-line prefer-object-spread
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(subscriptionUpsellTpl);
        this.data = options.context;
        this.render();
    }

    render() {
        // eslint-disable-next-line no-undef
        const data = $.extend(this.context, {
            minSubscriptionPrice: '$39',
            trialLength: 7,
        });
        HtmlUtils.setHtml(this.$el, this.tpl(data));
    }
}

export default SubscriptionUpsellView;
