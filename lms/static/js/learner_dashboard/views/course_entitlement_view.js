/* globals gettext */

import 'bootstrap';

import Backbone from 'backbone';
import moment from 'moment';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import EntitlementModel from '../models/course_entitlement_model';
import CourseCardModel from '../models/course_card_model';

import pageTpl from '../../../templates/learner_dashboard/course_entitlement.underscore';
import verificationPopoverTpl from '../../../templates/learner_dashboard/verification_popover.underscore';

class CourseEntitlementView extends Backbone.View {
    constructor(options) {
        const defaults = {
            events: {
                'change .session-select': 'updateEnrollBtn',
                'click .enroll-btn': 'handleEnrollChange',
                'keydown .final-confirmation-btn': 'handleVerificationPopoverA11y',
                'click .popover-dismiss': 'hideDialog',
            },
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(pageTpl);
        this.verificationTpl = HtmlUtils.template(verificationPopoverTpl);

        // Set up models and reload view on change
        this.courseCardModel = options.courseCardModel || new CourseCardModel();
        this.enrollModel = options.enrollModel;
        this.entitlementModel = new EntitlementModel({
            availableSessions: this.formatDates(JSON.parse(options.availableSessions)),
            entitlementUUID: options.entitlementUUID,
            currentSessionId: options.currentSessionId,
            expiredAt: options.expiredAt,
            expiresAtDate: CourseCardModel.formatDate(
                new moment().utc().add(options.daysUntilExpiration, 'days'), // eslint-disable-line new-cap
            ),
            courseName: options.courseName,
        });
        this.listenTo(this.entitlementModel, 'change', this.render);

        // Grab URLs that handle changing of enrollment and entering a newly selected session.
        this.enrollUrl = options.enrollUrl;
        this.courseHomeUrl = options.courseHomeUrl;

        // Grab elements from the parent card that work with this view
        this.$parentEl = options.$parentEl; // Containing course card (must be a backbone view root el)
        this.$enterCourseBtn = $(options.enterCourseBtn); // Button link to course home page
        this.$courseCardMessages = $(options.courseCardMessages); // Additional session messages
        this.$courseTitleLink = $(options.courseTitleLink); // Title link to course home page
        this.$courseImageLink = $(options.courseImageLink); // Image link to course home page
        this.$policyMsg = $(options.policyMsg); // Message for policy information

        // Bind action elements with associated events to objects outside this view
        this.$dateDisplayField = this.$parentEl ? this.$parentEl.find(options.dateDisplayField) :
            $(options.dateDisplayField); // Displays current session dates
        this.$triggerOpenBtn = this.$parentEl ? this.$parentEl.find(options.triggerOpenBtn) :
            $(options.triggerOpenBtn); // Opens/closes session selection view
        this.$triggerOpenBtn.on('click', this.toggleSessionSelectionPanel.bind(this));

        this.render(options);
        this.postRender();
    }

    render() {
        HtmlUtils.setHtml(this.$el, this.tpl(this.entitlementModel.toJSON()));
        this.delegateEvents();
        this.updateEnrollBtn();
        return this;
    }

    postRender() {
    // Close any visible popovers on click-away
        $(document).on('click', (e) => {
            if (this.$('.popover:visible').length &&
          !($(e.target).closest('.enroll-btn-initial, .popover').length)) {
                this.hideDialog(this.$('.enroll-btn-initial'));
            }
        });

        // Initialize focus to cancel button on popover load
        $(document).on('shown.bs.popover', () => {
            this.$('.final-confirmation-btn:first').focus();
        });
    }

    handleEnrollChange() {
    /*
    Handles enrolling in a course, unenrolling in a session and changing session.
    The new session id is stored as a data attribute on the option in the session-select element.
    */
        // Do not allow for enrollment when button is disabled
        const prevSession = this.entitlementModel.get('currentSessionId');
        if (this.$('.enroll-btn-initial').hasClass('disabled')) return;

        // Grab the id for the desired session, a leave session event will return null
        this.currentSessionSelection = this.$('.session-select')
            .find('option:selected').data('session_id');
        const isLeavingSession = !this.currentSessionSelection;

        // Display the indicator icon
        HtmlUtils.setHtml(this.$dateDisplayField,
            HtmlUtils.HTML('<span class="fa fa-spinner fa-spin" aria-hidden="true"></span>'),
        );

        $.ajax({
            type: isLeavingSession ? 'DELETE' : 'POST',
            url: this.enrollUrl,
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify({
                course_run_id: this.currentSessionSelection,
            }),
            statusCode: {
                201: this.enrollSuccess.bind(this, prevSession, this.currentSessionSelection),
                204: this.unenrollSuccess.bind(this, prevSession),
            },
            error: this.enrollError.bind(this),
        });
    }

    enrollSuccess(prevSession, newSession) {
    /*
    Update external elements on the course card to represent the now available course session.

    1) Show the change session toggle button.
    2) Add the new session's dates to the date field on the main course card.
    3) Hide the 'View Course' button to the course card.
    */
        const successIconEl = '<span class="fa fa-check" aria-hidden="true"></span>';
        const eventPage = this.$parentEl ? 'program-details' : 'course-dashboard';
        const eventAction = prevSession ? 'switch' : 'new';

        // Emit analytics event to track user leaving current session
        this.trackSessionChange(eventPage, eventAction, prevSession);

        // With a containing backbone view, we can simply re-render the parent card
        if (this.$parentEl &&
        this.courseCardModel.get('course_run_key') !== this.currentSessionSelection) {
            this.courseCardModel.updateCourseRun(this.currentSessionSelection);
            return;
        }

        // Update the model with the new session Id
        this.entitlementModel.set({ currentSessionId: this.currentSessionSelection });

        // Allow user to change session
        this.$triggerOpenBtn.removeClass('hidden');

        // Display a success indicator
        HtmlUtils.setHtml(this.$dateDisplayField,
            HtmlUtils.joinHtml(
                HtmlUtils.HTML(successIconEl),
                this.getAvailableSessionWithId(newSession).session_dates,
            ),
        );

        // Ensure the view course button links to new session home page and place focus there
        this.$enterCourseBtn
            .attr('href', this.formatCourseHomeUrl(newSession))
            .removeClass('hidden')
            .focus();
        this.toggleSessionSelectionPanel();
    }

    unenrollSuccess(prevSession) {
    /*
    Update external elements on the course card to represent the unenrolled state.

    1) Hide the change session button and the date field.
    2) Hide the 'View Course' button.
    3) Remove the messages associated with the enrolled state.
    4) Remove the link from the course card image and title.
    */
        // Emit analytics event to track user leaving current session
        const eventPage = this.$parentEl ? 'program-details' : 'course-dashboard';
        this.trackSessionChange(eventPage, 'leave', prevSession);

        // With a containing backbone view, we can simply re-render the parent card
        if (this.$parentEl) {
            this.courseCardModel.setUnselected();
            return;
        }

        // Update the model with the new session Id;
        this.entitlementModel.set({ currentSessionId: this.currentSessionSelection });

        // Reset the card contents to the unenrolled state
        this.$triggerOpenBtn.addClass('hidden');
        this.$enterCourseBtn.addClass('hidden');
        // Remove all message except for related programs, which should always be shown
        // (Even other messages might need to be shown again in future: LEARNER-3523.)
        this.$courseCardMessages.filter(':not(.message-related-programs)').remove();
        this.$policyMsg.remove();
        this.$('.enroll-btn-initial').focus();
        HtmlUtils.setHtml(
            this.$dateDisplayField,
            HtmlUtils.joinHtml(
                HtmlUtils.HTML('<span class="icon fa fa-warning" aria-hidden="true"></span>'),
                HtmlUtils.HTML(gettext('You must select a session to access the course.')),
            ),
        );

        // Remove links to previously enrolled sessions
        this.$courseImageLink.replaceWith( // xss-lint: disable=javascript-jquery-insertion
            HtmlUtils.joinHtml(
                HtmlUtils.HTML('<div class="'),
                this.$courseImageLink.attr('class'),
                HtmlUtils.HTML('" tabindex="-1">'),
                HtmlUtils.HTML(this.$courseImageLink.html()),
                HtmlUtils.HTML('</div>'),
            ).text,
        );
        this.$courseTitleLink.replaceWith( // xss-lint: disable=javascript-jquery-insertion
            HtmlUtils.joinHtml(
                HtmlUtils.HTML('<span>'),
                this.$courseTitleLink.text(),
                HtmlUtils.HTML('</span>'),
            ).text,
        );
    }

    enrollError() {
    // Display a success indicator
        const errorMsgEl = HtmlUtils.joinHtml(
            HtmlUtils.HTML('<span class="enroll-error">'),
            gettext('There was an error. Please reload the page and try again.'),
            HtmlUtils.HTML('</spandiv>'),
        ).text;

        this.$dateDisplayField
            .find('.fa.fa-spin')
            .removeClass('fa-spin fa-spinner')
            .addClass('fa-close');

        this.$dateDisplayField.append(errorMsgEl);
        this.hideDialog(this.$('.enroll-btn-initial'));
    }

    updateEnrollBtn() {
    /*
    This function is invoked on load, on opening the view and on changing the option on the session
    selection dropdown. It plays three roles:
    1) Enables and disables enroll button
    2) Changes text to describe the action taken
    3) Formats the confirmation popover to allow for two step authentication
    */
        let enrollText;
        const currentSessionId = this.entitlementModel.get('currentSessionId');
        const newSessionId = this.$('.session-select').find('option:selected').data('session_id');
        const enrollBtnInitial = this.$('.enroll-btn-initial');

        // Disable the button if the user is already enrolled in that session.
        if (currentSessionId === newSessionId) {
            enrollBtnInitial.addClass('disabled');
            this.removeDialog(enrollBtnInitial);
            return;
        }
        enrollBtnInitial.removeClass('disabled');

        // Update button text specifying if the user is initially enrolling,
        // changing or leaving a session.
        if (newSessionId) {
            enrollText = currentSessionId ? gettext('Change Session') : gettext('Select Session');
        } else {
            enrollText = gettext('Leave Current Session');
        }
        enrollBtnInitial.text(enrollText);
        this.initializeVerificationDialog(enrollBtnInitial);
    }

    toggleSessionSelectionPanel() {
    /*
    Opens and closes the session selection panel.
    */
        this.$el.toggleClass('hidden');
        if (!this.$el.hasClass('hidden')) {
            // Set focus to the session selection for a11y purposes
            this.$('.session-select').focus();
            this.hideDialog(this.$('.enroll-btn-initial'));
        }
        this.updateEnrollBtn();
    }

    initializeVerificationDialog(invokingElement) {
    /*
    Instantiates an instance of the Bootstrap v4 dialog modal and attaches it to the
    passed in element.

    This dialog acts as the second step in verifying the user's action to select, change
    or leave an available course session.
    */
        let confirmationMsgTitle;
        let confirmationMsgBody;
        const currentSessionId = this.entitlementModel.get('currentSessionId');
        const newSessionId = this.$('.session-select').find('option:selected').data('session_id');

        // Update the button popover text to enable two step authentication.
        if (newSessionId) {
            confirmationMsgTitle = !currentSessionId ?
                gettext('Are you sure you want to select this session?') :
                gettext('Are you sure you want to change to a different session?');
            confirmationMsgBody = !currentSessionId ? '' :
                gettext('Any course progress or grades from your current session will be lost.');
        } else {
            confirmationMsgTitle = gettext('Are you sure that you want to leave this session?');
            confirmationMsgBody = gettext('Any course progress or grades from your current session will be lost.'); // eslint-disable-line max-len
        }

        // Re-initialize the popover
        invokingElement.popover({
            placement: 'bottom',
            container: this.$el,
            html: true,
            trigger: 'click',
            content: this.verificationTpl({
                confirmationMsgTitle,
                confirmationMsgBody,
            }).text,
        });
    }

    removeDialog(el) {
    /* Removes the Bootstrap v4 dialog modal from the update session enrollment button. */
        const $el = el instanceof jQuery ? el : this.$('.enroll-btn-initial');
        if (this.$('popover').length) {
            $el.popover('dispose');
        }
    }

    hideDialog(el, returnFocus) {
    /* Hides the modal if it is visible without removing it from the DOM. */
        const $el = el instanceof jQuery ? el : this.$('.enroll-btn-initial');
        if (this.$('.popover:visible').length) {
            $el.popover('hide');
            if (returnFocus) {
                $el.focus();
            }
        }
    }

    handleVerificationPopoverA11y(e) {
    /* Ensure that the second step verification popover is treated as an a11y compliant dialog */
        let $nextButton;
        const $verificationOption = $(e.target);
        const openButton = $(e.target).closest('.course-entitlement-selection-container')
            .find('.enroll-btn-initial');
        if (e.key === 'Tab') {
            e.preventDefault();
            $nextButton = $verificationOption.is(':first-child') ?
                $verificationOption.next('.final-confirmation-btn') :
                $verificationOption.prev('.final-confirmation-btn');
            $nextButton.focus();
        } else if (e.key === 'Escape') {
            this.hideDialog(openButton);
            openButton.focus();
        }
    }

    formatCourseHomeUrl(sessionKey) {
    /*
    Takes the base course home URL and updates it with the new session id, leveraging the
    the fact that all course keys contain a '+' symbol.
    */
        const oldSessionKey = this.courseHomeUrl.split('/')
            .filter(
                urlParam => urlParam.indexOf('+') > 0,
            )[0];
        return this.courseHomeUrl.replace(oldSessionKey, sessionKey);
    }

    formatDates(sessionData) {
    /*
    Takes a data object containing the upcoming available sessions for an entitlement and returns
    the object with a session_dates attribute representing a formatted date string that highlights
    the start and end dates of the particular session.
    */
        // Set the date format string to the user's selected language
        moment.locale(document.documentElement.lang);
        const dateFormat = moment.localeData().longDateFormat('L').indexOf('DD') >
      moment.localeData().longDateFormat('L').indexOf('MM') ? 'MMMM D, YYYY' : 'D MMMM, YYYY';

        sessionData.forEach((session) => {
            Object.assign(session, {
                enrollment_end: CourseEntitlementView.formatDate(session.enrollment_end, dateFormat),
                session_id: session.session_id ? session.session_id : session.key,
                session_dates: this.courseCardModel.formatDateString({
                    start_date: CourseEntitlementView.formatDate(session.start, dateFormat),
                    advertised_start: session.advertised_start,
                    end_date: CourseEntitlementView.formatDate(session.end, dateFormat),
                    pacing_type: session.pacing_type,
                }),
            });
        });

        return sessionData;
    }

    static formatDate(date, dateFormat) {
        return date ? moment((new Date(date))).format(dateFormat) : '';
    }

    getAvailableSessionWithId(sessionId) {
    /* Returns an available session given a sessionId */
        return this.entitlementModel.get('availableSessions').find(session => session.session_id === sessionId);
    }

    trackSessionChange(eventPage, action, prevSession) {
        const eventName = `${eventPage}.${action}-session`;

        window.analytics.track(eventName, {
            fromCourseRun: prevSession,
            toCourseRun: this.entitlementModel.get('currentSessionId'),
        });
    }
}

export default CourseEntitlementView;
