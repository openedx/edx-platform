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
    it('when location is the default (US)', () => {
      $.cookie('edx-price-l10n', '{"rate":1,"code":"USD","symbol":"$","countryCode":"US"}', { path: '/' });
      currency = new Currency();
      expect($('[name="verified_mode"].no-discount').filter(':visible').text()).toEqual('Pursue a Verified Certificate($100 USD)');
    });
    it('when cookie is set to a different country', () => {
      $.cookie('edx-price-l10n', '{"rate":2.2,"code":"CAD","symbol":"$","countryCode":"CAN"}', { expires: 1 });
      currency = new Currency();
      expect($('[name="verified_mode"].no-discount').filter(':visible').text()).toEqual('Pursue a Verified Certificate($220 CAD)');
    });
    it('when cookie is set to a different country with a discount', () => {
      $.cookie('edx-price-l10n', '{"rate":2.2,"code":"CAD","symbol":"$","countryCode":"CAN"}', { expires: 1 });
      currency = new Currency();
      expect($('[name="verified_mode"].discount').filter(':visible').text()).toEqual('Pursue a Verified Certificate($198 CAD $220 CAD)');
    });
  });
});
