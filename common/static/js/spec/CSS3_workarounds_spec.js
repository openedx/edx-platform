describe("CSS3 workarounds", function() {
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
			// mock document.body.style so it does not include 'pointerEvents'
			var mockBodyStyle = {},
			    bodyStyleKeys = Object.keys(document.body.style);
			for (var index = 0; index < bodyStyleKeys.length; index++) {
				var key = bodyStyleKeys[index];
				if (key !== "pointerEvents") {
					mockBodyStyle[key] = document.body.style[key];
				};
			};

			pointerEventsNone(".is-disabled", mockBodyStyle);
			spyOnEvent(".is-disabled", "click");
			$(".is-disabled").click();
			expect("click").toHaveBeenPreventedOn(".is-disabled");
		});
	});
});
