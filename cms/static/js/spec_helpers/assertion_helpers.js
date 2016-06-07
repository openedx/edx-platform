/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "common/js/components/views/feedback_notification", "common/js/components/views/feedback_prompt",
        "common/js/spec_helpers/template_helpers"],
    function($, NotificationView, Prompt, TemplateHelpers) {
        var installViewTemplates, createFeedbackSpy, verifyFeedbackShowing,
            verifyFeedbackHidden, createNotificationSpy, verifyNotificationShowing,
            verifyNotificationHidden, createPromptSpy, confirmPrompt, inlineEdit, verifyInlineEditChange,
            installMockAnalytics, removeMockAnalytics, verifyPromptShowing, verifyPromptHidden;

        assertDetailsView = function (view, text) {
            expect(view.$el).toContainText(text);
            expect(view.$el).toContainText('ID: 0');
            expect(view.$('.delete')).toExist();
        };

        assertControllerView = function (view, detailsView, editView) {
            // Details view by default
            expect(view.$(detailsView)).toExist();
            view.$('.action-edit .edit').click();
            expect(view.$(editView)).toExist();
            expect(view.$(detailsView)).not.toExist();
            view.$('.action-cancel').click();
            expect(view.$(detailsView)).toExist();
            expect(view.$(editView)).not.toExist();
        };

        assertAndDeleteItemError = function (that, url, promptText) {
            var requests = AjaxHelpers.requests(that),
                promptSpy = ViewHelpers.createPromptSpy(),
                notificationSpy = ViewHelpers.createNotificationSpy();

            clickDeleteItem(that, promptSpy, promptText);

            patchAndVerifyRequest(requests, url, notificationSpy);

            AjaxHelpers.respondToDelete(requests);
            ViewHelpers.verifyNotificationHidden(notificationSpy);
            expect($(SELECTORS.itemView)).not.toExist();
        };

        assertAndDeleteItemWithError = function (that, url, listItemView, promptText) {
            var requests = AjaxHelpers.requests(that),
                promptSpy = ViewHelpers.createPromptSpy(),
                notificationSpy = ViewHelpers.createNotificationSpy();

            clickDeleteItem(that, promptSpy, promptText);
            patchAndVerifyRequest(requests, url, notificationSpy);

            AjaxHelpers.respondWithError(requests);
            ViewHelpers.verifyNotificationShowing(notificationSpy, /Deleting/);
            expect($(listItemView)).toExist();
        };

        assertUnusedOptions = function (that) {
            that.model.set('usage', []);
            that.view.render();
            expect(that.view.$(SELECTORS.warningMessage)).not.toExist();
            expect(that.view.$(SELECTORS.warningIcon)).not.toExist();
        };

        assertCannotDeleteUsed = function (that, toolTipText, warningText){
            setUsageInfo(that.model);
            that.view.render();
            expect(that.view.$(SELECTORS.note)).toHaveAttr(
                'data-tooltip', toolTipText
            );
            expect(that.view.$(SELECTORS.warningMessage)).toContainText(warningText);
            expect(that.view.$(SELECTORS.warningIcon)).toExist();
            expect(that.view.$('.delete')).toHaveClass('is-disabled');
        };

        return {
            'installViewTemplates': installViewTemplates,
            'createNotificationSpy': createNotificationSpy,
            'verifyNotificationShowing': verifyNotificationShowing,
            'verifyNotificationHidden': verifyNotificationHidden,
            'confirmPrompt': confirmPrompt,
            'createPromptSpy': createPromptSpy,
            'verifyPromptShowing': verifyPromptShowing,
            'verifyPromptHidden': verifyPromptHidden,
            'inlineEdit': inlineEdit,
            'verifyInlineEditChange': verifyInlineEditChange,
            'installMockAnalytics': installMockAnalytics,
            'removeMockAnalytics': removeMockAnalytics
        };
    });
