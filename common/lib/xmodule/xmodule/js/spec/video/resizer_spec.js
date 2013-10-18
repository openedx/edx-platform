(function (requirejs, require, define) {

require(
['video/00_resizer.js'],
function (Resizer) {

    describe('Resizer', function () {
        var html = [
                '<div class="rszr-wrapper" style="width:200px; height: 200px;">',
                    '<div class="rszr-el" style="width:100px; height: 150px;">',
                        'Content',
                    '</div>',
                '</div>'
            ].join(''),
            config, container, element;

        beforeEach(function () {
            setFixtures(html);

            container = $('.rszr-wrapper');
            element = $('.rszr-el');
            config = {
                container: container,
                element: element
            };
        });

        it('When Initialize without required parameters, log message is shown',
            function () {
                spyOn(console, 'log');

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

    });
});


}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
