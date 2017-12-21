import whichCountry from 'which-country';
import 'jquery.cookie';
import $ from 'jquery'; // eslint-disable-line import/extensions

export class Currency {  // eslint-disable-line import/prefer-default-export

  setCookie(countryCode, l10nData) {
    function pick(curr, arr) {
      const obj = {};
      arr.forEach((key) => {
        obj[key] = curr[key];
      });
      return obj;
    }
    const userCountryData = pick(l10nData, [countryCode]);
    let countryL10nData = userCountryData[countryCode];

    if (countryL10nData) {
      countryL10nData.countryCode = countryCode;
      $.cookie('edx-price-l10n', JSON.stringify(countryL10nData), {
        domain: 'edx.org',
        expires: 1,
      });
    } else {
      countryL10nData = {
        countryCode: 'USA',
        symbol: '$',
        rate: '1',
        code: 'USD',
      };
    }
    this.countryL10nData = countryL10nData;
  }

  setPrice() {
    const l10nCookie = this.countryL10nData;
    const price = $(this.selector).filter(':visible')[0];
    const regexMatch = this.regex.exec(price.value);
    const dollars = parseFloat(regexMatch[2]);
    const converted = dollars * l10nCookie.rate;
    const string = `${l10nCookie.symbol}${Math.round(converted)} ${l10nCookie.code}`;
    // Use regex to change displayed price on track selection
    // based on edx-price-l10n cookie currency_data
    price.value = price.value.replace(regexMatch[0], string);
  }

  getL10nData(countryCode) {
    const l10nData = JSON.parse($('#currency_data').attr('value'));
    if (l10nData) {
      this.setCookie(countryCode, l10nData);
    }
  }

  getCountry(position) {
    const countryCode = whichCountry([position.coords.longitude, position.coords.latitude]);
    this.countryL10nData = JSON.parse($.cookie('edx-price-l10n'));

    if (countryCode) {
      if (!(this.countryL10nData && this.countryL10nData.countryCode === countryCode)) {
        // If pricing cookie has not been set or the country is not correct
        // Make API call and set the cookie
        this.getL10nData(countryCode);
      }
    }
    this.setPrice();
  }

  getCountryCaller(position) {
    const caller = function callerFunction() {
      this.getCountry(position);
    }.bind(this);
    $(document).ready(caller);
  }

  getUserLocation() {
    // Get user location from browser
    navigator.geolocation.getCurrentPosition(this.getCountryCaller.bind(this));
  }

  constructor(options) {
    this.selector = options.selector || 'input[name="verified_mode"]';
    this.regex = options.regex || /(\$)(\d*)( USD)/g;

    if (!options.skipInitialize) {
      this.getUserLocation();
    }
  }
}
