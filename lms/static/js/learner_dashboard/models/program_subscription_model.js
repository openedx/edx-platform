import Backbone from 'backbone';
import moment from 'moment';

import DateUtils from 'edx-ui-toolkit/js/utils/date-utils';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';


/**
 * Model for Program Subscription Data.
 */
class ProgramSubscriptionModel extends Backbone.Model {
    constructor({ context }, ...args) {
        const {
            subscriptionData: [data = {}],
            programData: { subscription_prices },
            urls = {},
            userPreferences = {},
            subscriptionsTrialLength: trialLength = 7,
        } = context;

        const priceInUSD = subscription_prices?.find(({ currency }) => currency === 'USD');

        const subscriptionState = data.subscription_state?.toLowerCase() ?? '';
        const subscriptionPrice = StringUtils.interpolate(
            gettext('${price}/month {currency}'),
            {
                price: parseFloat(priceInUSD?.price),
                currency: priceInUSD?.currency,
            }
        );

        const subscriptionUrl =
            subscriptionState === 'active'
                ? urls.manage_subscription_url
                : urls.buy_subscription_url;

        const hasActiveTrial = false;

        const remainingDays = 0;

        const [currentPeriodEnd] = ProgramSubscriptionModel.formatDate(
            data.current_period_end,
            userPreferences
        );
        const [trialEndDate, trialEndTime] = ['', ''];

        super(
            {
                hasActiveTrial,
                currentPeriodEnd,
                remainingDays,
                subscriptionPrice,
                subscriptionState,
                subscriptionUrl,
                trialEndDate,
                trialEndTime,
                trialLength,
            },
            ...args
        );
    }

    static formatDate(date, userPreferences) {
        if (!date) {
            return ['', ''];
        }

        const userTimezone = (
            userPreferences.time_zone || moment?.tz?.guess?.() || 'UTC'
        );
        const userLanguage = userPreferences['pref-lang'] || 'en';
        const context = {
            datetime: date,
            timezone: userTimezone,
            language: userLanguage,
            format: DateUtils.dateFormatEnum.shortDate,
        };

        const localDate = DateUtils.localize(context);
        const localTime = '';

        return [localDate, localTime];
    }
}

export default ProgramSubscriptionModel;
