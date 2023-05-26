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
        } = context;

        const priceInUSD = subscription_prices?.find(({ currency }) => currency === 'USD');
        const trialMoment = moment(
            DateUtils.localizeTime(
                DateUtils.stringToMoment(data.trial_end),
                'UTC'
            )
        );

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

        const hasActiveTrial =
            subscriptionState === 'active' && data.trial_end
                ? trialMoment.isAfter(moment.utc())
                : false;

        const remainingDays = trialMoment.diff(moment.utc(), 'days');

        const [nextPaymentDate] = ProgramSubscriptionModel.formatDate(
            data.next_payment_date,
            userPreferences
        );
        const [trialEndDate, trialEndTime] = ProgramSubscriptionModel.formatDate(
            data.trial_end,
            userPreferences
        );

        const trialLength = 7;

        super(
            {
                hasActiveTrial,
                nextPaymentDate,
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

        const userTimezone = userPreferences.time_zone || 'UTC';
        const userLanguage = userPreferences['pref-lang'] || 'en';
        const context = {
            datetime: date,
            timezone: userTimezone,
            language: userLanguage,
            format: DateUtils.dateFormatEnum.shortDate,
        };

        const localDate = DateUtils.localize(context);
        const localTime = DateUtils.localizeTime(
            DateUtils.stringToMoment(date),
            userTimezone
        ).format('HH:mm');

        return [localDate, localTime];
    }
}

export default ProgramSubscriptionModel;
