describe('JS bridge for communication between native mobile apps and the xblock', function() {
    beforeEach(function() {
    // Mock objects for IOS and Android bridges
        window.webkit = {
            messageHandlers: {
                IOSBridge: {
                    postMessage: jasmine.createSpy('postMessage')
                }
            }
        };
        window.AndroidBridge = {
            postMessage: jasmine.createSpy('postMessage')
        };
    });

    describe('sendMessageToIOS', function() {
        it('should call postMessage on IOSBridge with the correct message', function() {
            const message = JSON.stringify({answer: 'test'});
            sendMessageToIOS(message);
            expect(window.webkit.messageHandlers.IOSBridge.postMessage).toHaveBeenCalledWith(message);
        });
    });

    describe('sendMessageToAndroid', function() {
        it('should call postMessage on AndroidBridge with the correct message', function() {
            const message = JSON.stringify({answer: 'test'});
            sendMessageToAndroid(message);
            expect(window.AndroidBridge.postMessage).toHaveBeenCalledWith(message);
        });
    });

    describe('markProblemCompleted', function() {
        it('should correctly parse the message and update the DOM elements', function() {
            const message = JSON.stringify({
                data: 'input1=answer1&input2=answer2'
            });
            const problemContainer = $('<div class="xblock-student_view">'
        + '<div class="submit-attempt-container">'
        + '<button class="submit"></button>'
        + '</div>'
        + '<div class="notification-gentle-alert">'
        + '<div class="notification-message"></div>'
        + '</div>'
        + '<input id="input1">'
        + '<input id="input2">'
        + '<input id="answer1">'
        + '<input id="answer2">'
        + '</div>');
            $('body').append(problemContainer);

            markProblemCompleted(message);

            expect(problemContainer.find('.submit-attempt-container .submit').attr('disabled')).toBe('disabled');
            expect(problemContainer.find('.notification-gentle-alert .notification-message').html()).toBe('Answer submitted.');
            expect(problemContainer.find('.notification-gentle-alert').css('display')).not.toBe('none');
            expect(problemContainer.find('#input1').val()).toBe('answer1');
            expect(problemContainer.find('#input2').val()).toBe('answer2');
            expect(problemContainer.find('#answer1').prop('disabled')).toBe(true);
            expect(problemContainer.find('#answer2').prop('disabled')).toBe(true);

            problemContainer.remove();
        });
    });

    describe('$.ajax', function() {
        beforeEach(function() {
            spyOn($, 'ajax').and.callThrough();
        });

        it('should intercept the request to problem_check and send data to the native apps', function() {
            const ajaxOptions = {
                url: 'http://example.com/handler/xmodule_handler/problem_check',
                data: {answer: 'test'}
            };

            $.ajax(ajaxOptions);

            expect(window.webkit.messageHandlers.IOSBridge.postMessage).toHaveBeenCalledWith(JSON.stringify(ajaxOptions));
            expect(window.AndroidBridge.postMessage).toHaveBeenCalledWith(JSON.stringify(ajaxOptions));
        });

        it('should call the original $.ajax function', function() {
            const ajaxOptions = {
                url: 'http://example.com/handler/xmodule_handler/problem_check',
                data: {answer: 'test'}
            };

            const originalAjax = spyOn($, 'ajax').and.callFake(function(options) {
                return originalAjax.and.callThrough().call(this, options);
            });

            $.ajax(ajaxOptions);

            expect(originalAjax).toHaveBeenCalledWith(ajaxOptions);
        });
    });
});
