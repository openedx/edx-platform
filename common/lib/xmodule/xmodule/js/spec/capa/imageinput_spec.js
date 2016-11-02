/**
 * "Beware of bugs in the above code; I have only proved it correct, not tried
 * it."
 *
 * ~ Donald Knuth
 */

(function($, ImageInput, undefined) {
    describe('ImageInput', function() {
        var state;

        beforeEach(function() {
            var el;

            loadFixtures('imageinput.html');
            el = $('#imageinput_12345');

            el.append(createTestImage('cross_12345', 300, 400, 'red'));

            state = new ImageInput('12345');
        });

        it('initialization', function() {
            // Check that object's properties are present, and that the DOM
            // elements they reference exist.
            expect(state.el).toBeDefined();
            expect(state.el).toExist();

            expect(state.crossEl).toBeDefined();
            expect(state.crossEl).toExist();

            expect(state.inputEl).toBeDefined();
            expect(state.inputEl).toExist();

            expect(state.el).toHandle('click');
        });

        it('cross becomes visible after first click', function() {
            expect(state.crossEl.css('visibility')).toBe('hidden');

            state.el.click();

            expect(state.crossEl.css('visibility')).toBe('visible');
        });

        it('coordinates are updated [offsetX is set]', function() {
            var event, posX, posY, cssLeft, cssTop;

            // Set up of 'click' event.
            event = jQuery.Event(
                'click',
                {offsetX: 35.3, offsetY: 42.7}
            );

            // Calculating the expected coordinates.
            posX = event.offsetX;
            posY = event.offsetY;

            // Triggering 'click' event.
            jQuery(state.el).trigger(event);

            // Getting actual (new) coordinates, and testing them against the
            // expected.
            cssLeft = stripPx(state.crossEl.css('left'));
            cssTop = stripPx(state.crossEl.css('top'));

            expect(cssLeft).toBeCloseTo(posX - 15, 1);
            expect(cssTop).toBeCloseTo(posY - 15, 1);
            expect(state.inputEl.val()).toBe(
                '[' + Math.round(posX) + ',' + Math.round(posY) + ']'
            );
        });

        it('coordinates are updated [offsetX is NOT set]', function() {
            var offset = state.el.offset(),
                event, posX, posY, cssLeft, cssTop;

            // Set up of 'click' event.
            event = jQuery.Event(
                'click',
                {
                    offsetX: undefined, offsetY: undefined,
                    pageX: 35.3, pageY: 42.7
                }
            );

            // Calculating the expected coordinates.
            posX = event.pageX - offset.left;
            posY = event.pageY - offset.top;

            // Triggering 'click' event.
            jQuery(state.el).trigger(event);

            // Getting actual (new) coordinates, and testing them against the
            // expected.
            cssLeft = stripPx(state.crossEl.css('left'));
            cssTop = stripPx(state.crossEl.css('top'));

            expect(cssLeft).toBeCloseTo(posX - 15, 1);
            expect(cssTop).toBeCloseTo(posY - 15, 1);
            expect(state.inputEl.val()).toBe(
                '[' + Math.round(posX) + ',' + Math.round(posY) + ']'
            );
        });
    });

    // Instead of storing an image, and then including it in the template via
    // the <img /> tag, we will generate one on the fly.
    //
    // Create a simple image from a canvas. The canvas is filled by a colored
    // rectangle.
    function createTestImage(id, width, height, fillStyle) {
        var canvas, ctx, img;

        canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        ctx = canvas.getContext('2d');
        ctx.fillStyle = fillStyle;
        ctx.fillRect(0, 0, width, height);

        img = document.createElement('img');
        img.src = canvas.toDataURL('image/png');
        img.id = id;

        return img;
    }

    // Strip the trailing 'px' substring from a CSS string containing the
    // `left` and `top` properties of an element's style.
    function stripPx(str) {
        return str.substring(0, str.length - 2);
    }
}).call(this, window.jQuery, window.ImageInput);
