define(['backbone', 'jquery', 'js/models/notification', 'js/views/notification', 'common/js/spec_helpers/template_helpers'],
    function(Backbone, $, NotificationModel, NotificationView, TemplateHelpers) {
        describe('NotificationView', function() {
            var createNotification, verifyTitle, verifyMessage, verifyDetails, verifyAction, notificationView;

            createNotification = function(modelVals) {
                var notificationModel = new NotificationModel(modelVals);
                notificationView = new NotificationView({
                    model: notificationModel
                });
                notificationView.render();
                return notificationView;
            };

            verifyTitle = function(expectedTitle) {
                expect(notificationView.$('.message-title').text().trim()).toBe(expectedTitle);
            };

            verifyMessage = function(expectedMessage) {
                expect(notificationView.$('.message-copy').text().trim()).toBe(expectedMessage);
            };

            verifyDetails = function(expectedDetails) {
                var details = notificationView.$('.summary-item');
                expect(details.length).toBe(expectedDetails.length);
                details.each(function(index) {
                    expect($(this).text().trim()).toBe(expectedDetails[index]);
                });
            };

            verifyAction = function(expectedActionText) {
                var actionButton = notificationView.$('.action-primary');
                if (expectedActionText) {
                    expect(actionButton.text().trim()).toBe(expectedActionText);
                }
                else {
                    expect(actionButton.length).toBe(0);
                }
            };

            beforeEach(function() {
                setFixtures('<div></div>');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/notification');
            });

            it('has default values', function() {
                createNotification({});
                expect(notificationView.$('div.message')).toHaveClass('message-confirmation');
                verifyTitle('');
                verifyDetails([]);
                verifyAction(null);
            });

            it('can use an error type', function() {
                createNotification({type: 'error'});
                expect(notificationView.$('div.message')).toHaveClass('message-error');
                expect(notificationView.$('div.message')).not.toHaveClass('message-confirmation');
            });

            it('can specify a title', function() {
                createNotification({title: 'notification title'});
                verifyTitle('notification title');
            });

            it('can specify a message', function() {
                createNotification({message: 'This is a dummy message'});
                verifyMessage('This is a dummy message');
            });

            it('can specify details', function() {
                var expectedDetails = ['detail 1', 'detail 2'];
                createNotification({details: expectedDetails});
                verifyDetails(expectedDetails);
            });

            it('shows an action button if text and callback are provided', function() {
                createNotification({actionText: 'action text', actionCallback: function() {}});
                verifyAction('action text');
            });

            it('shows an action button if only text is provided', function() {
                createNotification({actionText: 'action text'});
                verifyAction('action text');
            });

            it('does not show an action button if text is not provided', function() {
                createNotification({actionCallback: function() {}});
                verifyAction(null);
            });

            it('triggers the callback when the action button is clicked', function() {
                var actionCallback = jasmine.createSpy('Spy on callback');
                var view = createNotification({actionText: 'action text', actionCallback: actionCallback});
                notificationView.$('button.action-primary').click();
                expect(actionCallback).toHaveBeenCalledWith(view);
            });
        });
    });
