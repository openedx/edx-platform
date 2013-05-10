/*
 * Create a HesitateEvent and assign it as the event to execute:
 *   $(el).on('mouseEnter', CMS.HesitateEvent( expand, 'mouseLeave').trigger);
 *   It calls the executeOnTimeOut function with the event.currentTarget after the configurable timeout IFF the cancelSelector event
 *   did not occur on the event.currentTarget.
 *
 *   More specifically, when trigger is called (triggered by the event you bound it to), it starts a timer
 *   which the cancelSelector event will cancel or if the timer finished, it executes the executeOnTimeOut function
 *   passing it the original event (whose currentTarget s/b the specific ele). It never accumulates events; however, it doesn't hurt for your
 *   code to minimize invocations of trigger by binding to mouseEnter v mouseOver and such.
 *
 *   NOTE: if something outside of this wants to cancel the event, invoke cachedhesitation.untrigger(null | anything);
 */

CMS.HesitateEvent = function(executeOnTimeOut, cancelSelector, onlyOnce) {
	this.executeOnTimeOut = executeOnTimeOut;
	this.cancelSelector = cancelSelector;
	this.timeoutEventId = null;
	this.originalEvent = null;
	this.onlyOnce = (onlyOnce === true);
};

CMS.HesitateEvent.DURATION = 800;

CMS.HesitateEvent.prototype.trigger = function(event) {
	if (event.data.timeoutEventId == null) {
		event.data.timeoutEventId = window.setTimeout(
				function() { event.data.fireEvent(event); },
				CMS.HesitateEvent.DURATION);
		event.data.originalEvent = event;
		$(event.data.originalEvent.delegateTarget).on(event.data.cancelSelector, event.data, event.data.untrigger);
	}
};

CMS.HesitateEvent.prototype.fireEvent = function(event) {
	event.data.timeoutEventId = null;
	$(event.data.originalEvent.delegateTarget).off(event.data.cancelSelector, event.data.untrigger);
	if (event.data.onlyOnce) $(event.data.originalEvent.delegateTarget).off(event.data.originalEvent.type, event.data.trigger);
	event.data.executeOnTimeOut(event.data.originalEvent);
};

CMS.HesitateEvent.prototype.untrigger = function(event) {
	if (event.data.timeoutEventId) {
		window.clearTimeout(event.data.timeoutEventId);
		$(event.data.originalEvent.delegateTarget).off(event.data.cancelSelector, event.data.untrigger);
	}
	event.data.timeoutEventId = null;
};
