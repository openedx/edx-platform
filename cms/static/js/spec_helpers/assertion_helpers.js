/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
// eslint-disable-next-line no-undef
define(['jquery', 'common/js/components/views/feedback_notification', 'common/js/components/views/feedback_prompt',
    'common/js/spec_helpers/template_helpers'],
// eslint-disable-next-line no-unused-vars
function($, NotificationView, Prompt, TemplateHelpers) {
    /* eslint-disable-next-line no-unused-vars, no-var */
    var installViewTemplates, createFeedbackSpy, verifyFeedbackShowing,
        // eslint-disable-next-line no-unused-vars
        verifyFeedbackHidden, createNotificationSpy, verifyNotificationShowing,
        verifyNotificationHidden, createPromptSpy, confirmPrompt, inlineEdit, verifyInlineEditChange,
        installMockAnalytics, removeMockAnalytics, verifyPromptShowing, verifyPromptHidden;

    // eslint-disable-next-line no-undef
    assertDetailsView = function(view, text) {
        expect(view.$el).toContainText(text);
        expect(view.$el).toContainText('ID: 0');
        expect(view.$('.delete')).toExist();
    };

    // eslint-disable-next-line no-undef
    assertControllerView = function(view, detailsView, editView) {
        // Details view by default
        expect(view.$(detailsView)).toExist();
        view.$('.action-edit .edit').click();
        expect(view.$(editView)).toExist();
        expect(view.$(detailsView)).not.toExist();
        view.$('.action-cancel').click();
        expect(view.$(detailsView)).toExist();
        expect(view.$(editView)).not.toExist();
    };

    // eslint-disable-next-line no-undef
    assertAndDeleteItemError = function(that, url, promptText) {
        /* eslint-disable-next-line no-undef, no-var */
        var requests = AjaxHelpers.requests(that),
            // eslint-disable-next-line no-undef
            promptSpy = ViewHelpers.createPromptSpy(),
            // eslint-disable-next-line no-undef
            notificationSpy = ViewHelpers.createNotificationSpy();

        // eslint-disable-next-line no-undef
        clickDeleteItem(that, promptSpy, promptText);

        // eslint-disable-next-line no-undef
        patchAndVerifyRequest(requests, url, notificationSpy);

        // eslint-disable-next-line no-undef
        AjaxHelpers.respondToDelete(requests);
        // eslint-disable-next-line no-undef
        ViewHelpers.verifyNotificationHidden(notificationSpy);
        // eslint-disable-next-line no-undef
        expect($(SELECTORS.itemView)).not.toExist();
    };

    // eslint-disable-next-line no-undef
    assertAndDeleteItemWithError = function(that, url, listItemView, promptText) {
        /* eslint-disable-next-line no-undef, no-var */
        var requests = AjaxHelpers.requests(that),
            // eslint-disable-next-line no-undef
            promptSpy = ViewHelpers.createPromptSpy(),
            // eslint-disable-next-line no-undef
            notificationSpy = ViewHelpers.createNotificationSpy();

        // eslint-disable-next-line no-undef
        clickDeleteItem(that, promptSpy, promptText);
        // eslint-disable-next-line no-undef
        patchAndVerifyRequest(requests, url, notificationSpy);

        // eslint-disable-next-line no-undef
        AjaxHelpers.respondWithError(requests);
        // eslint-disable-next-line no-undef
        ViewHelpers.verifyNotificationShowing(notificationSpy, /Deleting/);
        expect($(listItemView)).toExist();
    };

    // eslint-disable-next-line no-undef
    assertUnusedOptions = function(that) {
        that.model.set('usage', []);
        that.view.render();
        // eslint-disable-next-line no-undef
        expect(that.view.$(SELECTORS.warningMessage)).not.toExist();
        // eslint-disable-next-line no-undef
        expect(that.view.$(SELECTORS.warningIcon)).not.toExist();
    };

    // eslint-disable-next-line no-undef
    assertCannotDeleteUsed = function(that, toolTipText, warningText) {
        // eslint-disable-next-line no-undef
        setUsageInfo(that.model);
        that.view.render();
        // eslint-disable-next-line no-undef
        expect(that.view.$(SELECTORS.note)).toHaveAttr(
            'data-tooltip', toolTipText
        );
        // eslint-disable-next-line no-undef
        expect(that.view.$(SELECTORS.warningMessage)).toContainText(warningText);
        // eslint-disable-next-line no-undef
        expect(that.view.$(SELECTORS.warningIcon)).toExist();
        expect(that.view.$('.delete')).toHaveClass('is-disabled');
    };

    return {
        installViewTemplates: installViewTemplates,
        createNotificationSpy: createNotificationSpy,
        verifyNotificationShowing: verifyNotificationShowing,
        verifyNotificationHidden: verifyNotificationHidden,
        confirmPrompt: confirmPrompt,
        createPromptSpy: createPromptSpy,
        verifyPromptShowing: verifyPromptShowing,
        verifyPromptHidden: verifyPromptHidden,
        inlineEdit: inlineEdit,
        verifyInlineEditChange: verifyInlineEditChange,
        installMockAnalytics: installMockAnalytics,
        removeMockAnalytics: removeMockAnalytics
    };
});
