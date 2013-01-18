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

CMS.HesitateEvent = function(executeOnTimeOut, jqueryEl, cancelSelector) {
	this.executeOnTimeOut = executeOnTimeOut;
	this.cancelSelector = cancelSelector;
	this.timeoutEventId = null;
	this.originalEvent = null;
}

CMS.HesitateEvent.DURATION = 400;

CMS.HesitateEvent.prototype.trigger = function(event) {
console.log('trigger');
	if (this.timeoutEventId === null) {
		this.timeoutEventId = window.setTimeout(this.fireEvent, CMS.HesitateEvent.DURATION);
		this.originalEvent = event;
		// is it wrong to bind to the below v $(event.currentTarget)?
		$(this.originalEvent.currentTarget).on(this.cancelSelector, this.untrigger);
	}
}

CMS.HesitateEvent.prototype.fireEvent = function(event) {
console.log('fire');
	this.timeoutEventId = null;
	$(this.originalEvent.currentTarget).off(this.cancelSelector, this.untrigger);
	this.executeOnTimeOut(this.originalEvent);
}

CMS.HesitateEvent.prototype.untrigger = function(event) {
console.log('untrigger');
	if (this.timeoutEventId) {
		window.clearTimeout(this.timeoutEventId);
		$(this.originalEvent.currentTarget).off(this.cancelSelector, this.untrigger);
	}
	this.timeoutEventId = null;
}