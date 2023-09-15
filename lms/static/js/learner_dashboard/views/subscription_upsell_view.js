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
        this.subscriptionUpsellModel = new Backbone.Model(
            options.subscriptionUpsellData,
        );
        this.render();
    }

    render() {
        const data = this.subscriptionUpsellModel.toJSON();
        HtmlUtils.setHtml(this.$el, this.tpl(data));
    }
}

export default SubscriptionUpsellView;
