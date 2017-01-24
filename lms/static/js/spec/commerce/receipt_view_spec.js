define([
    'jquery',
    'jquery.ajax-retry',
    'js/commerce/views/receipt_view',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
],
    function($, AjaxRetry, ReceiptView, AjaxHelpers) {
        'use strict';
        describe('edx.commerce.ReceiptView', function() {
            var data, courseResponseData, providerResponseData, mockRequests, mockRender, createReceiptView,
                createProduct, createLine, createOrderResponse, doCheckVerification, doCheckVerificationNagRendered,
                userResponseData;

            createReceiptView = function() {
                return new ReceiptView({el: $('#receipt-container')});
            };

            mockRequests = function(requests, method, apiUrl, responseData) {
                AjaxHelpers.expectRequest(requests, method, apiUrl);
                AjaxHelpers.respondWithJson(requests, responseData);
            };

            mockRender = function(useEcommerceOrderNumber, isVerified, requestInThemedSite) {
                var requests, view, orderUrlFormat,
                    actualRequestInThemedSite = requestInThemedSite;
                if (typeof actualRequestInThemedSite === 'undefined') {
                    actualRequestInThemedSite = 'False';
                }
                requests = AjaxHelpers.requests(this);
                $('#receipt-container').data({
                    verified: isVerified,
                    'is-request-in-themed-site': actualRequestInThemedSite
                });
                view = createReceiptView();
                view.useEcommerceApi = true;
                if (useEcommerceOrderNumber) {
                    view.ecommerceOrderNumber = 'EDX-123456';
                    orderUrlFormat = '/api/commerce/v1/orders/EDX-123456/';
                } else {
                    view.ecommerceBasketId = 'EDX-123456';
                    orderUrlFormat = '/api/commerce/v0/baskets/EDX-123456/order/';
                }
                view.render();
                mockRequests(requests, 'GET', orderUrlFormat, data);

                mockRequests(
                    requests, 'GET', '/commerce/checkout/verification_status/?course_id=' +
                    encodeURIComponent('course-v1:edx+dummy+2015_T3'), {is_verification_required: true}
                );

                mockRequests(
                    requests, 'GET', '/api/courses/v1/courses/course-v1:edx+dummy+2015_T3/', courseResponseData
                );

                mockRequests(
                    requests, 'GET', '/api/user/v1/accounts/user-1', userResponseData
                );

                mockRequests(requests, 'GET', '/api/credit/v1/providers/edx/', providerResponseData);
                return view;
            };

            createProduct = function(attributes) {
                var actualAttributes = attributes;
                if (typeof actualAttributes === 'undefined') {
                    actualAttributes = [
                        {
                            name: 'certificate_type',
                            value: 'verified'
                        },
                        {
                            name: 'course_key',
                            code: 'course_key',
                            value: 'course-v1:edx+dummy+2015_T3'
                        },
                        {
                            name: 'credit_provider',
                            value: 'edx'
                        }
                    ];
                }

                return {
                    attribute_values: actualAttributes,
                    stockrecords: [
                        {
                            price_currency: 'USD',
                            product: 123,
                            partner_sku: '1234ABC',
                            partner: 1,
                            price_excl_tax: '10.00',
                            id: 123
                        }
                    ],
                    product_class: 'Seat',
                    title: 'Dummy title',
                    url: 'https://ecom.edx.org/api/v2/products/123/',
                    price: '10.00',
                    expires: null,
                    is_available_to_buy: true,
                    id: 123,
                    structure: 'child'
                };
            };

            createLine = function(product) {
                var actualProduct = product;
                if (typeof actualProduct === 'undefined') {
                    actualProduct = createProduct();
                }
                return {
                    status: 'Open',
                    unit_price_excl_tax: '10.00',
                    product: actualProduct,
                    line_price_excl_tax: '10.00',
                    description: 'dummy description',
                    title: 'dummy title',
                    quantity: 1
                };
            };

            createOrderResponse = function(lines) {
                var actualLines = lines;
                if (typeof actualLines === 'undefined') {
                    actualLines = [createLine()];
                }
                return {
                    status: 'Open',
                    billed_to: {
                        city: 'dummy city',
                        first_name: 'john',
                        last_name: 'doe',
                        country: 'AL',
                        line2: 'line2',
                        line1: 'line1',
                        state: '',
                        postcode: '12345'
                    },
                    lines: actualLines,
                    number: 'EDX-123456',
                    date_placed: '2016-01-01T01:01:01Z',
                    currency: 'USD',
                    total_excl_tax: '10.00'
                };
            };

            doCheckVerification = function(attributes, expected) {
                var view = createReceiptView(),
                    product = createProduct(attributes);
                expect(view.requiresVerification(product)).toBe(expected);
            };

            doCheckVerificationNagRendered = function(attributes, userVerified, expected, requestInThemedSite) {
                var view;
                data = createOrderResponse([createLine(createProduct(attributes))]);
                view = mockRender(true, userVerified, requestInThemedSite);
                if (expected) {
                    expect(view.$('.nav-wizard.is-ready').text()).toContain('Want to confirm your identity later');
                } else {
                    expect(view.$('.nav-wizard.is-ready').text()).toContain('Go to Dashboard');
                }
            };

            beforeEach(function() {
                var receiptFixture, providerFixture;
                // Stub analytics tracking
                window.analytics = jasmine.createSpyObj('analytics', ['page', 'track', 'trackLink']);

                loadFixtures('js/fixtures/commerce/checkout_receipt.html');

                receiptFixture = readFixtures('templates/commerce/receipt.underscore');
                providerFixture = readFixtures('templates/commerce/provider.underscore');
                appendSetFixtures(
                    '<script id="receipt-tpl" type="text/template" >' + receiptFixture + '</script>' +
                    '<script id="provider-tpl" type="text/template" >' + providerFixture + '</script>'
                );

                data = createOrderResponse();

                providerResponseData = {
                    id: 'edx',
                    display_name: 'edX',
                    url: 'http://www.edx.org',
                    status_url: 'http://www.edx.org/status',
                    description: 'Nothing',
                    enable_integration: false,
                    fulfillment_instructions: '',
                    thumbnail_url: 'http://edx.org/thumbnail.png'
                };

                courseResponseData = {
                    id: 'course-v1:edx+dummy+2015_T3',
                    name: 'receipt test',
                    category: 'course',
                    org: 'edx',
                    run: '2015_T2',
                    course: 'CS420',
                    uri: 'http://test.com/api/courses/v1/courses/course-v1:edx+dummy+2015_T3/',
                    image_url: '/test.jpg',
                    start: '2030-01-01T00:00:00Z',
                    end: null
                };
                userResponseData = {
                    username: 'user-1',
                    name: 'full name'
                };
            });

            it('sends analytic event when verified receipt is rendered', function() {
                mockRender(true, 'True');
                expect(window.analytics.track).toHaveBeenCalledWith(
                    'Completed Purchase',
                    {
                        orderId: 'EDX-123456',
                        total: '10.00',
                        currency: 'USD'
                    }
                );
            });

            it('sends analytic event when non verified receipt is rendered', function() {
                mockRender(true, 'False');
                expect(window.analytics.track).toHaveBeenCalledWith(
                    'Completed Purchase',
                    {
                        orderId: 'EDX-123456',
                        total: '10.00',
                        currency: 'USD'
                    }
                );
            });

            it('renders a receipt correctly with Ecommerce Order Number', function() {
                var view;

                view = mockRender(true, 'True');
                expect(view.$('.course_name_placeholder').text()).toContain('receipt test');
            });

            it('renders a receipt correctly with Ecommerce Basket Id', function() {
                var view;

                view = mockRender(false, 'True');
                expect(view.$('.course_name_placeholder').text()).toContain('receipt test');
            });

            it('requiresVerification returns true if product requires verification', function() {
                var expected = true,
                    attributes = [
                        {name: 'certificate_type', value: 'professional'},
                        {name: 'course_key', value: 'course-v1:OC+OC+2'},
                        {name: 'id_verification_required', value: true}
                    ];
                doCheckVerification(attributes, expected, 'False');
            });

            it('requiresVerification returns true if product requires verification, different order', function() {
                var expected = true,
                    attributes = [
                        {name: 'certificate_type', value: 'professional'},
                        {name: 'id_verification_required', value: true},
                        {name: 'course_key', value: 'course-v1:OC+OC+2'}
                    ];
                doCheckVerification(attributes, expected, 'False');
            });

            it('requiresVerification defaults to true', function() {
                var expected = true,
                    attributes = [
                        {name: 'certificate_type', value: 'professional'},
                        {name: 'course_key', value: 'course-v1:OC+OC+2'}
                    ];
                doCheckVerification(attributes, expected, 'False');
            });

            it('requiresVerification returns false for courses not requiring verification', function() {
                var expected = false,
                    attributes = [
                        {name: 'certificate_type', value: 'professional'},
                        {name: 'id_verification_required', value: false},
                        {name: 'course_key', value: 'course-v1:OC+OC+2'}
                    ];
                doCheckVerification(attributes, expected, 'False');
            });

            it('receipt view verification nag for not verified users in a verified course', function() {
                var attributes = [
                    {name: 'certificate_type', value: 'professional'},
                    {name: 'id_verification_required', value: true},
                    {name: 'course_key', value: 'course-v1:edx+dummy+2015_T3'},
                    {name: 'credit_provider', value: 'edx'}
                ];
                doCheckVerificationNagRendered(attributes, 'False', true, 'False');
            });

            it("receipt view doesn't show verification nag for a verified user in a verified course", function() {
                var attributes = [
                    {name: 'certificate_type', value: 'professional'},
                    {name: 'id_verification_required', value: true},
                    {name: 'course_key', value: 'course-v1:edx+dummy+2015_T3'},
                    {name: 'credit_provider', value: 'edx'}
                ];
                doCheckVerificationNagRendered(attributes, 'True', false, 'False');
            });

            it("receipt view doesn't show verification for a unverified user in a not verified course", function() {
                var attributes = [
                    {name: 'certificate_type', value: 'professional'},
                    {name: 'id_verification_required', value: false},
                    {name: 'course_key', value: 'course-v1:edx+dummy+2015_T3'},
                    {name: 'credit_provider', value: 'edx'}
                ];
                doCheckVerificationNagRendered(attributes, 'False', false, 'False');
            });

            it("receipt view doesn't show verification nag for a verified user in a not verified course", function() {
                var attributes = [
                    {name: 'certificate_type', value: 'professional'},
                    {name: 'id_verification_required', value: false},
                    {name: 'course_key', value: 'course-v1:edx+dummy+2015_T3'},
                    {name: 'credit_provider', value: 'edx'}
                ];
                doCheckVerificationNagRendered(attributes, 'True', false, 'False');
            });

            it("receipt view doesn't show verification nag for a not verified user in a verified" +
               ' course on themed site', function() {
                var attributes = [
                    {name: 'certificate_type', value: 'professional'},
                    {name: 'id_verification_required', value: true},
                    {name: 'course_key', value: 'course-v1:edx+dummy+2015_T3'},
                    {name: 'credit_provider', value: 'edx'}
                ];
                doCheckVerificationNagRendered(attributes, 'False', false, 'True');
            });
        });
    }
);
