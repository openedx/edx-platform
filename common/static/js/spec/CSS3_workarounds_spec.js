describe("CSS3 workarounds", function() {
	'use strict';
	var pointerEventsNone = window.pointerEventsNone;
	describe("pointer-events", function() {
		beforeEach(function() {
			var html = "<a href='#' class='is-disabled'>What wondrous life in this I lead</a>";
			setFixtures(html);
		});

		it("should not prevent default when pointerEvents is supported", function() {
			// In case this test suite is being run in a browser where
			// 'pointerEvents' is not supported, mock out document.body.style
			// so that it includes 'pointerEvents'
			var mockBodyStyle = document.body.style;
			if (!("pointerEvents" in mockBodyStyle)) {
				mockBodyStyle["pointerEvents"] = "";
			};

			pointerEventsNone(".is-disabled", mockBodyStyle);
			spyOnEvent(".is-disabled", "click");
			$(".is-disabled").click();
			expect("click").not.toHaveBeenPreventedOn(".is-disabled");
		});

		it("should prevent default when pointerEvents is not Supported", function() {
			pointerEventsNone(".is-disabled", {});
			spyOnEvent(".is-disabled", "click");
			$(".is-disabled").click();
			expect("click").toHaveBeenPreventedOn(".is-disabled");
		});
	});
});
