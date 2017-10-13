/* globals loadFixtures */

import $ from 'jquery'; // eslint-disable-line import/extensions
import { Currency } from '../currency';

describe('Currency factory', () => {
  let currency;
  let canadaPosition;
  let usaPosition;
  let japanPosition;

  beforeEach(() => {
    loadFixtures('course_experience/fixtures/course-currency-fragment.html');
    currency = new Currency(true);
    canadaPosition = {
      coords: {
        latitude: 58.773884,
        longitude: -124.882581,
      },
    };
    usaPosition = {
      coords: {
        latitude: 42.366202,
        longitude: -71.973095,
      },
    };
    japanPosition = {
      coords: {
        latitude: 35.857826,
        longitude: 137.737495,
      },
    };
    $.cookie('edx-price-l10n', null, { path: '/' });
  });

  describe('converts price to local currency', () => {
    it('when location is US', () => {
      currency.getCountry(usaPosition);
      expect($('input[name="verified_mode"]').filter(':visible')[0].value).toEqual('Pursue a Verified Certificate ($100 USD)');
    });

    it('when location is an unsupported country', () => {
      currency.getCountry(japanPosition);
      expect($('input[name="verified_mode"]').filter(':visible')[0].value).toEqual('Pursue a Verified Certificate ($100 USD)');
    });

    it('when cookie is not set and country is supported', () => {
      currency.getCountry(canadaPosition);
      expect($('input[name="verified_mode"]').filter(':visible')[0].value).toEqual('Pursue a Verified Certificate ($220 CAD)');
    });

    it('when cookie is set to same country', () => {
      currency.getCountry(canadaPosition);
      $.cookie('edx-price-l10n', '{"rate":2.2,"code":"CAD","symbol":"$","countryCode":"CAN"}', { expires: 1 });
      expect($('input[name="verified_mode"]').filter(':visible')[0].value).toEqual('Pursue a Verified Certificate ($220 CAD)');
    });

    it('when cookie is set to different country', () => {
      currency.getCountry(canadaPosition);
      $.cookie('edx-price-l10n', '{"rate":1,"code":"USD","symbol":"$","countryCode":"USA"}', { expires: 1 });
      expect($('input[name="verified_mode"]').filter(':visible')[0].value).toEqual('Pursue a Verified Certificate ($220 CAD)');
    });
  });
});
