define(['js/dashboard/dropdown', 'jquery.simulate'],
    function() {
        'use strict';
        var keys = $.simulate.keyCode,
            toggleButtonSelector = '#actions-dropdown-link-2',
            dropdownSelector = '#actions-dropdown-2',
            dropdownItemSelector = '#actions-dropdown-2 li a',
            clickToggleButton = function() {
                $(toggleButtonSelector).click();
            },
            verifyDropdownVisible = function() {
                expect($(dropdownSelector)).toBeVisible();
            },
            verifyDropdownNotVisible = function() {
                expect($(dropdownSelector)).not.toBeVisible();
            },
            waitForElementToBeFocused = function(element, desc) {
                // This is being used instead of toBeFocused which is flaky
                waitsFor(
                    function () {
                        return element === document.activeElement;
                    },
                    desc + ' element to have focus',
                    500
                );
            },
            openDropDownMenu = function() {
                verifyDropdownNotVisible();
                clickToggleButton();
                verifyDropdownVisible();
            },
            keydown = function(keyInfo) {
                $(document.activeElement).simulate("keydown", keyInfo);
            };

        describe("edx.dashboard.dropdown.toggleCourseActionsDropdownMenu", function() {

            beforeEach(function() {
                loadFixtures('js/fixtures/dashboard/dashboard.html');
                window.edx.dashboard.dropdown.bindToggleButtons();
            });

            it("Clicking the .action-more button toggles the menu", function() {
                verifyDropdownNotVisible();
                clickToggleButton();
                verifyDropdownVisible();
                clickToggleButton();
                verifyDropdownNotVisible();
            });
            it("ESCAPE will close dropdown and return focus to the button", function() {
                openDropDownMenu();
                keydown({ keyCode: keys.ESCAPE });
                verifyDropdownNotVisible();
                waitForElementToBeFocused($(toggleButtonSelector)[0], "button");
            });
            it("SPACE will close dropdown and return focus to the button", function() {
                openDropDownMenu();
                keydown({ keyCode: keys.SPACE });
                verifyDropdownNotVisible();
                waitForElementToBeFocused($(toggleButtonSelector)[0], "button");
            });

            describe("Focus is trapped when navigating with", function() {
                it("TAB key", function() {
                    openDropDownMenu();
                    keydown({ keyCode: keys.TAB });
                    waitForElementToBeFocused($(dropdownItemSelector)[0], "first");
                });
                it("DOWN key", function() {
                    openDropDownMenu();
                    keydown({ keyCode: keys.DOWN });
                    waitForElementToBeFocused($(dropdownItemSelector)[0], "first");
                });
                it("TAB key + SHIFT key", function() {
                    openDropDownMenu();
                    keydown({ keyCode: keys.TAB, shiftKey: true });
                    waitForElementToBeFocused($(dropdownItemSelector)[1], "last");
                });
                it("UP key", function() {
                    openDropDownMenu();
                    keydown({ keyCode: keys.UP });
                    waitForElementToBeFocused($(dropdownItemSelector)[1], "last");
                });
            });
        });
    }
);
