(function (requirejs, require, define) {

require(
['video/00_resizer.js'],
function (Resizer) {

    describe('Resizer', function () {
        var html = [
                '<div ' +
                    'class="rszr-wrapper" ' +
                    'style="width:200px; height: 200px;"' +
                '>',
                    '<div ' +
                        'class="rszr-el" ' +
                        'style="width:100px; height: 150px;"' +
                    '>',
                        'Content',
                    '</div>',
                '</div>'
            ].join(''),
            config, container, element, originalConsoleLog;

        beforeEach(function () {
            setFixtures(html);

            container = $('.rszr-wrapper');
            element = $('.rszr-el');
            config = {
                container: container,
                element: element
            };

            originalConsoleLog = window.console.log;
            spyOn(console, 'log');
        });

        afterEach(function () {
            window.console.log = originalConsoleLog;
        });

        it('When Initialize without required parameters, log message is shown',
            function () {
                new Resizer({ });
                expect(console.log).toHaveBeenCalled();
            }
        );

        it('`alignByWidthOnly` works correctly', function () {
            var resizer = new Resizer(config).alignByWidthOnly(),
                expectedWidth = container.width(),
                realWidth = element.width();

            expect(realWidth).toBe(expectedWidth);
        });

        it('`alignByHeightOnly` works correctly', function () {
            var resizer = new Resizer(config).alignByHeightOnly(),
                expectedHeight = container.height(),
                realHeight = element.height(),
                realWidth;

            expect(realHeight).toBe(expectedHeight);
        });

        it('`align` works correctly', function () {
            var resizer = new Resizer(config).align(),
                expectedHeight = container.height(),
                realHeight = element.height(),
                expectedWidth = 50;

            // containerRatio >= elementRatio
            expect(realHeight).toBe(expectedHeight);

            // containerRatio < elementRatio
            container.width(expectedWidth);
            resizer.align();
            realWidth = element.width();

            expect(realWidth).toBe(expectedWidth);

        });

        it('`setMode` works correctly', function () {
            var resizer = new Resizer(config).setMode('height'),
                expectedHeight = container.height(),
                realHeight = element.height(),
                expectedWidth = 50;

            // containerRatio >= elementRatio
            expect(realHeight).toBe(expectedHeight);

            // containerRatio < elementRatio
            container.width(expectedWidth);
            resizer.setMode('width');
            realWidth = element.width();

            expect(realWidth).toBe(expectedWidth);
        });

        describe('Callbacks', function () {
            var resizer,
                spiesList = [];

            beforeEach(function () {
                var spiesCount = _.range(3);

                spiesList = $.map(spiesCount, function() {
                    return jasmine.createSpy();
                });

                resizer = new Resizer(config);
            });


            it('callbacks are called', function () {
                $.each(spiesList, function(index, spy) {
                    resizer.callbacks.add(spy);
                });

                resizer.align();

                $.each(spiesList, function(index, spy) {
                    expect(spy).toHaveBeenCalled();
                });
            });

            it('callback called just once', function () {
                resizer.callbacks.once(spiesList[0]);

                resizer
                    .align()
                    .alignByHeightOnly();

                expect(spiesList[0].calls.length).toEqual(1);
            });

            it('All callbacks are removed', function () {
                $.each(spiesList, function(index, spy) {
                    resizer.callbacks.add(spy);
                });

                resizer.callbacks.removeAll();
                resizer.align();

                $.each(spiesList, function(index, spy) {
                    expect(spy).not.toHaveBeenCalled();
                });
            });

            it('Specific callback is removed', function () {
                $.each(spiesList, function(index, spy) {
                    resizer.callbacks.add(spy);
                });

                resizer.callbacks.remove(spiesList[1]);
                resizer.align();

                expect(spiesList[1]).not.toHaveBeenCalled();
            });

            it('Error message is shown when wrong argument type is passed', function () {
                var methods = ['add', 'once'],
                    errorMessage = '[Video info]: TypeError: Argument is not a function.',
                    arg = {};

                spyOn(console, 'error');

                $.each(methods, function(index, methodName) {
                     resizer.callbacks[methodName](arg);
                     expect(console.error).toHaveBeenCalledWith(errorMessage);
                     //reset spy
                     console.log.reset();
                });

            });

        });
    });
});


}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
