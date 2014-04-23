// A file for JS workarounds for CSS3 features that are not
// supported in older browsers

var pointerEventsNone = function (selector, supportedStyles) {
	// Check to see if the brower supports 'pointer-events' css rule.
	// If it doesn't, use javascript to stop the link from working
	// when clicked.
	$(selector).click(function (event) {
		if (!('pointerEvents' in supportedStyles)) {
			event.preventDefault();
		};
	});
};

$(function () {
	pointerEventsNone('.is-disabled', document.body.styles);
});
