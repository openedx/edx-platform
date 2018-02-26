import whichCountry from 'which-country';
import 'jquery.cookie';
import $ from 'jquery'; // eslint-disable-line import/extensions

export class Currency {  // eslint-disable-line import/prefer-default-export

  setPrice() {
    const l10nCookie = this.countryL10nData;
    const lmsregex = /(\$)(\d*)( USD)/g;
    const price = $('input[name="verified_mode"]').filter(':visible')[0];
    const regexMatch = lmsregex.exec(price.value);
    const dollars = parseFloat(regexMatch[2]);
    const converted = dollars * l10nCookie.rate;
    const string = `${l10nCookie.symbol}${Math.round(converted)} ${l10nCookie.code}`;
    // Use regex to change displayed price on track selection
    // based on edx-price-l10n cookie currency_data
    price.value = price.value.replace(regexMatch[0], string);
  }

  getCountry() {
    this.countryL10nData = JSON.parse($.cookie('edx-price-l10n'));
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
