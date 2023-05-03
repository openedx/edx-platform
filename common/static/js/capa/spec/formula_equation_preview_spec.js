describe('escapeSelector', function() {
    'use strict';
    var escapeSelector = window.escapeSelector;

    it('correctly escapes css', function() {
        // tests borrowed from
        // https://github.com/jquery/jquery/blob/3edfa1bcdc50bca41ac58b2642b12f3feee03a3b/test/unit/selector.js#L2030
        expect(escapeSelector('-')).toEqual('\\-');
        expect(escapeSelector('-a')).toEqual('-a');
        expect(escapeSelector('--')).toEqual('--');
        expect(escapeSelector('--a')).toEqual('--a');
        expect(escapeSelector('\uFFFD')).toEqual('\uFFFD');
        expect(escapeSelector('\uFFFDb')).toEqual('\uFFFDb');
        expect(escapeSelector('a\uFFFDb')).toEqual('a\uFFFDb');
        expect(escapeSelector('1a')).toEqual('\\31 a');
        expect(escapeSelector('a\0b')).toEqual('a\uFFFDb');
        expect(escapeSelector('a3b')).toEqual('a3b');
        expect(escapeSelector('-4a')).toEqual('-\\34 a');
        expect(escapeSelector('\x01\x02\x1E\x1F')).toEqual('\\1 \\2 \\1e \\1f ');

        // This is the important one; xblocks and course ids often contain invalid characters, so if these aren't
        // escaped when embedding/searching xblock IDs using css selectors, bad things happen.
        expect(escapeSelector('course-v1:edX+DemoX+Demo_Course')).toEqual('course-v1\\:edX\\+DemoX\\+Demo_Course');
        expect(escapeSelector('block-v1:edX+DemoX+Demo_Course+type@sequential+block')).toEqual(
            'block-v1\\:edX\\+DemoX\\+Demo_Course\\+type\\@sequential\\+block'
        );
    });
});

describe('Formula Equation Preview', function() {
    'use strict';
    var formulaEquationPreview = window.formulaEquationPreview;
    beforeEach(function() {
        // Simulate an environment conducive to a FormulaEquationInput
        var $fixture = this.$fixture = $('\
<section class="problems-wrapper" data-url="THE_URL">\
  <section class="formulaequationinput">\
    <div class="INITIAL_STATUS" id="status_THE_ID">\
      <input type="text" id="input_THE_ID" data-input-id="THE_ID"\
          value="PREFILLED_VALUE"/>\
      <p class="status">INITIAL_STATUS</p>\
      <div id="input_THE_ID_preview" class="equation">\
        \[\]\
        <img class="loading" style="visibility:hidden"/>\
      </div>\
    </div>\
  </section>\
</section>');

        // Modify $ for the test to search the fixture.
        var old$find = this.old$find = $.find;
        $.find = function() {
            // Given the default context, swap it out for the fixture.
            if (arguments[1] == document) {
                arguments[1] = $fixture[0];
            }

            // Call old function.
            return old$find.apply(this, arguments);
        };
        $.find.matchesSelector = old$find.matchesSelector;

        this.oldDGEBI = document.getElementById;
        document.getElementById = function(id) {
            return $('*#' + id)[0] || null;
        };

        // Catch the AJAX requests
        var ajaxTimes = this.ajaxTimes = [];
        this.oldProblem = window.Problem;

        window.Problem = {};
        window.Problem.inputAjax = jasmine.createSpy('Problem.inputAjax')
            .and.callFake(function() {
                ajaxTimes.push(Date.now());
            });

        // Spy on MathJax
        this.jax = 'OUTPUT_JAX';
        this.oldMathJax = window.MathJax;

        window.MathJax = {Hub: {}};
        window.MathJax.Hub.getAllJax = jasmine.createSpy('MathJax.Hub.getAllJax')
            .and.returnValue([this.jax]);
        window.MathJax.Hub.Queue = function(callback) {
            if (typeof (callback) === 'function') {
                callback();
            }
        };
        spyOn(window.MathJax.Hub, 'Queue').and.callThrough();
        window.MathJax.Hub.Startup = jasmine.createSpy('MathJax.Hub.Startup');
        window.MathJax.Hub.Startup.signal = jasmine.createSpy('MathJax.Hub.Startup.signal');
        window.MathJax.Hub.Startup.signal.Interest = function(callback) {
            callback('End');
        };
    });

    it('(the test) is able to swap out the behavior of $', function() {
        // This was a pain to write, make sure it doesn't get screwed up.

        // Find the element using DOM methods.
        var legitInput = this.$fixture[0].getElementsByTagName('input')[0];

        // Use the (modified) jQuery.
        var $jqueryInput = $('.formulaequationinput input');
        var $byIdInput = $('#input_THE_ID');

        expect($jqueryInput[0]).toEqual(legitInput);
        expect($byIdInput[0]).toEqual(legitInput);
    });

    describe('Ajax requests', function() {
        beforeEach(function(done) {
            // This is common to all tests on ajax requests.
            formulaEquationPreview.enable();

            // This part may be asynchronous, so wait.
            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(done);
        });

        it('has an initial request with the correct parameters', function() {
            expect(window.Problem.inputAjax.calls.count()).toEqual(1);

            // Use `.toEqual` rather than `.toHaveBeenCalledWith`
            // since it supports `jasmine.any`.
            expect(window.Problem.inputAjax.calls.mostRecent().args).toEqual([
                'THE_URL',
                'THE_ID',
                'preview_formcalc',
                {formula: 'PREFILLED_VALUE',
                    request_start: jasmine.any(Number)},
                jasmine.any(Function)
            ]);
        });

        it('does not request again if the initial request has already been made', function(done) {
            expect(window.Problem.inputAjax.calls.count()).toEqual(1);

            // Reset the spy in order to check calls again.
            window.Problem.inputAjax.calls.reset();

            // Enabling the formulaEquationPreview again to see if this will
            // reinitialize input request once again.
            formulaEquationPreview.enable();

            // This part may be asynchronous, so wait.
            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() === 0;
            }).then(function() {
                // Expect window.Problem.inputAjax was not called as input request was
                // initialized before.
                expect(window.Problem.inputAjax).not.toHaveBeenCalled();
            }).always(done);
        });

        it('makes a request on user input', function(done) {
            window.Problem.inputAjax.calls.reset();
            $('#input_THE_ID').val('user_input').trigger('input');

            // This part is probably asynchronous
            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(function() {
                expect(window.Problem.inputAjax.calls.mostRecent().args[3].formula).toEqual('user_input');
            }).always(done);
        });

        it("isn't requested for empty input", function(done) {
            window.Problem.inputAjax.calls.reset();

            // When we make an input of '',
            $('#input_THE_ID').val('').trigger('input');

            // Either it makes a request or jumps straight into displaying ''.
            jasmine.waitUntil(function() {
                // (Short circuit if `inputAjax` is indeed called)
                return window.Problem.inputAjax.calls.count() > 0 ||
                    window.MathJax.Hub.Queue.calls.count() > 0;
            }).then(function() {
                // Expect the request not to have been called.
                expect(window.Problem.inputAjax).not.toHaveBeenCalled();
            }).always(done);
        });

        it('limits the number of requests per second', function(done) {
            var minDelay = formulaEquationPreview.minDelay;
            var end = Date.now() + minDelay * 1.1;

            var $input = $('#input_THE_ID');
            var value;
            function inputAnother(iter) {
                value = 'math input ' + iter;
                $input.val(value).trigger('input');
            }

            var self = this;
            var iter = 0;
            jasmine.waitUntil(function() {
                inputAnother(iter++);
                return Date.now() > end;  // Stop when we get to `end`.
            }).then(function() {
                jasmine.waitUntil(function() {
                    return window.Problem.inputAjax.calls.count() > 0 &&
                        window.Problem.inputAjax.calls.mostRecent().args[3].formula === value;
                }).then(_.bind(function() {
                    // There should be 2 or 3 calls (depending on leading edge).
                    expect(window.Problem.inputAjax.calls.count()).not.toBeGreaterThan(3);

                    // The calls should happen approximately `minDelay` apart.
                    for (var i = 1; i < this.ajaxTimes.length; i ++) {
                        var diff = this.ajaxTimes[i] - this.ajaxTimes[i - 1];
                        expect(diff).toBeGreaterThan(minDelay - 10);
                    }
                }, self)).then(function() {
                    done();
                });
            });
        });
    });

    describe('Visible results (icon and mathjax)', function() {
        it('displays a loading icon when requests are open', function(done) {
            var $img = $('img.loading');
            expect($img.css('visibility')).toEqual('hidden');
            formulaEquationPreview.enable();
            expect($img.css('visibility')).toEqual('visible');

            // This part could be asynchronous
            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(function() {
                expect($img.css('visibility')).toEqual('visible');

                // Reset and send another request.
                $img.css('visibility', 'hidden');
                $('#input_THE_ID').val('different').trigger('input');

                expect($img.css('visibility')).toEqual('visible');
            }).then(function() {
                return jasmine.waitUntil(function() {
                    var args = window.Problem.inputAjax.calls.mostRecent().args;
                    return args[3].formula === 'different';
                }).then(done);
            });
        });

        it('updates MathJax and loading icon on callback', function(done) {
            formulaEquationPreview.enable();

            var jax = this.jax;

            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(function() {
                var args = window.Problem.inputAjax.calls.mostRecent().args;
                var callback = args[4];
                callback({
                    preview: 'THE_FORMULA',
                    request_start: args[3].request_start
                });

                // The only request returned--it should hide the loading icon.
                expect($('img.loading').css('visibility')).toEqual('hidden');

                // We should look in the preview div for the MathJax.
                var previewDiv = $('#input_THE_ID_preview')[0];
                expect(window.MathJax.Hub.getAllJax).toHaveBeenCalledWith(previewDiv);

                // Refresh the MathJax.
                expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Text', jax, 'THE_FORMULA']
                );
            }).always(done);
        });

        it('finds alternatives if MathJax hasn\'t finished loading', function(done) {
            formulaEquationPreview.enable();
            $('#input_THE_ID').val('user_input').trigger('input');

            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(function() {
                var args = window.Problem.inputAjax.calls.mostRecent().args;
                var callback = args[4];

                // Cannot find MathJax.
                window.MathJax.Hub.getAllJax.and.returnValue([]);
                spyOn(console, 'log');

                callback({
                    preview: 'THE_FORMULA',
                    request_start: args[3].request_start
                });

                // Tests.
                expect(console.log).toHaveBeenCalled();

                // We should look in the preview div for the MathJax.
                var previewElement = $('#input_THE_ID_preview')[0];
                expect(previewElement.firstChild.data).toEqual('\\(THE_FORMULA\\)');

                // Refresh the MathJax.
                expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Typeset', jasmine.any(Object), jasmine.any(Element)]
                );
            }).always(done);
        });

        it('displays errors from the server well', function(done) {
            var $img = $('img.loading');
            var jax = this.jax;

            formulaEquationPreview.enable();
            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(function() {
                var args = window.Problem.inputAjax.calls.mostRecent().args;
                var callback = args[4];
                callback({
                    error: 'OOPSIE',
                    request_start: args[3].request_start
                });
                expect(window.MathJax.Hub.Queue).not.toHaveBeenCalled();
                expect($img.css('visibility')).toEqual('visible');
            }).then(function() {
                jasmine.waitUntil(function() {
                    return window.MathJax.Hub.Queue.calls.count() > 0;
                }).then(function() {
                    // Refresh the MathJax.
                    expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                        ['Text', jax, '\\text{OOPSIE}']
                    );
                    expect($img.css('visibility')).toEqual('hidden');
                }).then(done);
            });
        });
    });

    describe('Multiple callbacks', function() {
        beforeEach(function(done) {
            formulaEquationPreview.enable();

            var self = this;
            jasmine.waitUntil(function() {
                return window.Problem.inputAjax.calls.count() > 0;
            }).then(function() {
                $('#input_THE_ID').val('different').trigger('input');
                jasmine.waitUntil(function() {
                    return window.Problem.inputAjax.calls.count() > 1;
                }).then(_.bind(function() {
                    var args0 = window.Problem.inputAjax.calls.argsFor(0);
                    var args1 = window.Problem.inputAjax.calls.argsFor(1);
                    var response0 = {
                        preview: 'THE_FORMULA_0',
                        request_start: args0[3].request_start
                    };
                    var response1 = {
                        preview: 'THE_FORMULA_1',
                        request_start: args1[3].request_start
                    };

                    this.callbacks = [args0[4], args0[4]];
                    this.responses = [response0, response1];
                }, self)).then(done);
            });
        });

        it('updates requests sequentially', function() {
            var $img = $('img.loading');

            expect($img.css('visibility')).toEqual('visible');

            this.callbacks[0](this.responses[0]);
            expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_0']
            );
            expect($img.css('visibility')).toEqual('visible');

            this.callbacks[1](this.responses[1]);
            expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1']
            );
            expect($img.css('visibility')).toEqual('hidden');
        });

        it("doesn't display outdated information", function() {
            var $img = $('img.loading');

            expect($img.css('visibility')).toEqual('visible');

            // Switch the order (1 returns before 0)
            this.callbacks[1](this.responses[1]);
            expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1']
            );
            expect($img.css('visibility')).toEqual('hidden');

            window.MathJax.Hub.Queue.calls.reset();
            this.callbacks[0](this.responses[0]);
            expect(window.MathJax.Hub.Queue).not.toHaveBeenCalled();
            expect($img.css('visibility')).toEqual('hidden');
        });

        it("doesn't show an error if the responses are close together", function(done) {
            this.callbacks[0]({
                error: 'OOPSIE',
                request_start: this.responses[0].request_start
            });
            expect(window.MathJax.Hub.Queue).not.toHaveBeenCalled();

            // Error message waiting to be displayed
            this.callbacks[1](this.responses[1]);
            expect(window.MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1']
            );

            // Make sure that it doesn't indeed show up later
            window.MathJax.Hub.Queue.calls.reset();
            jasmine.waitUntil(function() {
                return formulaEquationPreview.errorDelay * 1.1;
            }).then(function() {
                expect(window.MathJax.Hub.Queue).not.toHaveBeenCalled();
            }).then(done);
        });
    });

    afterEach(function() {
        // Return jQuery
        $.find = this.old$find;
        document.getElementById = this.oldDGEBI;

        // Return Problem
        window.Problem = this.oldProblem;
        if (window.Problem === undefined) {
            delete window.Problem;
        }

        // Return MathJax
        window.MathJax = this.oldMathJax;
        if (window.MathJax === undefined) {
            delete window.MathJax;
        }
    });
});
