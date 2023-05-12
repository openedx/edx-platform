/* eslint-disable-next-line no-unused-vars, no-var */
var DialogTabControls = (function() {
    'use strict';

    // eslint-disable-next-line no-var
    var focusableChildren,
        numElements,
        currentIndex,
        focusableElementSelectors = 'a, input[type=text], input[type=submit], select, textarea, button',
        setCurrentIndex = function(currentElement) {
            // eslint-disable-next-line no-var
            var elementIndex = focusableChildren.index(currentElement);
            if (elementIndex >= 0) {
                currentIndex = elementIndex;
            }
        },
        initializeTabKeyValues = function(elementName, $closeButton) {
            focusableChildren = $(elementName).find(focusableElementSelectors);
            if ($closeButton) {
                focusableChildren = focusableChildren.add($closeButton);
            }
            numElements = focusableChildren.length;
            currentIndex = 0;
            focusableChildren[currentIndex].focus();
            focusableChildren.on('click', function() {
                setCurrentIndex(this);
            });
        },
        focusElement = function() {
            // eslint-disable-next-line no-var
            var focusableElement = focusableChildren[currentIndex];
            if (focusableElement) {
                focusableElement.focus();
            }
        },
        focusPrevious = function() {
            currentIndex--;
            if (currentIndex < 0) {
                currentIndex = numElements - 1;
            }

            focusElement();
        },
        focusNext = function() {
            currentIndex++;
            if (currentIndex >= numElements) {
                currentIndex = 0;
            }

            focusElement();
        },
        setKeydownListener = function($element, $closeButton) {
            $element.on('keydown', function(e) {
                // eslint-disable-next-line no-var
                var keyCode = e.keyCode || e.which,
                    escapeKeyCode = 27,
                    tabKeyCode = 9;
                if (keyCode === escapeKeyCode) {
                    e.preventDefault();
                    if ($closeButton) {
                        $closeButton.click();
                    }
                }
                if (keyCode === tabKeyCode && e.shiftKey) {
                    e.preventDefault();
                    focusPrevious();
                } else if (keyCode === tabKeyCode) {
                    e.preventDefault();
                    focusNext();
                }
            });
        };

    return {
        initializeTabKeyValues: initializeTabKeyValues,
        setKeydownListener: setKeydownListener
    };
}());
