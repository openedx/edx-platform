import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import subscriptionUpsellTpl from '../../../templates/learner_dashboard/subscription_upsell_view.underscore';

class SubscriptionUpsellView extends Backbone.View {
    constructor(options) {
        const defaults = {
            el: '.js-subscription-upsell',
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(subscriptionUpsellTpl);
        this.data = options.context;
        this.render();
    }

    render() {
        const data = $.extend(this.context, {
            // TODO: get from api
            min_subscription_price: '$39',
            trial_length: 7,
        });
        HtmlUtils.setHtml(this.$el, this.tpl(data));
    }
}

export default SubscriptionUpsellView;
