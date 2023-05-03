import 'jquery.cookie';
import $ from 'jquery'; // eslint-disable-line import/extensions

export class Currency {  // eslint-disable-line import/prefer-default-export

    editText(price) {
        const l10nCookie = this.countryL10nData;
        const lmsregex = /(\$)([\d|.]*)( USD)/g;
        const priceText = price.text();
        const regexMatch = lmsregex.exec(priceText);
        if (regexMatch) {
            const currentPrice = regexMatch[2];
            const dollars = parseFloat(currentPrice);
            const newPrice = dollars * l10nCookie.rate;
            const newPriceString = `${l10nCookie.symbol}${Math.round(newPrice)} ${l10nCookie.code}`;
            // Change displayed price based on edx-price-l10n cookie currency_data
            price.text(newPriceString);
        }
    }

    setPrice() {
        $('.upgrade-price-string').each((i, price) => {
            // When the button includes two prices (discounted and previous)
            // we call the method twice, since it modifies one price at a time.
            // Could also be used to modify all prices on any page
            this.editText($(price));
        });
    }

    getCountry() {
        try {
            this.countryL10nData = JSON.parse($.cookie('edx-price-l10n'));
        } catch (e) {
            if (e instanceof SyntaxError) {
                // If cookie isn't proper JSON, log but continue. This will show the purchase experience
                // in a non-local currency but will not prevent the user from interacting with the page.
                console.error(e);
                console.error("Ignoring malformed 'edx-price-l10n' cookie.");
            } else {
                throw e;
            }
        }
        if (this.countryL10nData) {
            window.analytics.track('edx.bi.user.track_selection.local_currency_cookie_set');
            this.setPrice();
        }
    }

    constructor() {
        $(document).ready(() => {
            this.getCountry();
        });
    }
}
