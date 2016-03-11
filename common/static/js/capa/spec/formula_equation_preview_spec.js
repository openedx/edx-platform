var waitForInputAjax = function (conditionalFn) {
    var deferred = $.Deferred(),
        timeout;

    var fn = function fn() {
        if (conditionalFn()) {
            timeout && clearTimeout(timeout);
            deferred.resolve();
        } else {
            timeout = setTimeout(fn, 50);
        }
    };

    fn();
    return deferred.promise();
};

describe("Formula Equation Preview", function () {
    beforeEach(function () {
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
        $.find = function () {
            // Given the default context, swap it out for the fixture.
            if (arguments[1] == document) {
                arguments[1] = $fixture[0];
            }

            // Call old function.
            return old$find.apply(this, arguments);
        };
        $.find.matchesSelector = old$find.matchesSelector;

        this.oldDGEBI = document.getElementById;
        document.getElementById = function (id) {
            return $("*#" + id)[0] || null;
        };

        // Catch the AJAX requests
        var ajaxTimes = this.ajaxTimes = [];
        this.oldProblem = window.Problem;

        window.Problem = {};
        Problem.inputAjax = jasmine.createSpy(Problem, 'inputAjax')
            .and.callFake(function () {
                ajaxTimes.push(Date.now());
            });

        // Spy on MathJax
        this.jax = 'OUTPUT_JAX';
        this.oldMathJax = window.MathJax;

        window.MathJax = {Hub: {}};
        MathJax.Hub.getAllJax = jasmine.createSpy('MathJax.Hub.getAllJax')
            .and.returnValue([this.jax]);
        MathJax.Hub.Queue = function (callback) {
            if (typeof (callback) == 'function') {
                callback();
            }
        };
        spyOn(MathJax.Hub, 'Queue').and.callThrough();
        MathJax.Hub.Startup = jasmine.createSpy('MathJax.Hub.Startup');
        MathJax.Hub.Startup.signal = jasmine.createSpy('MathJax.Hub.Startup.signal');
        MathJax.Hub.Startup.signal.Interest = function (callback) {
            callback('End');
        };

        oldJasmineDEFAULT_TIMEOUT_INTERVAL = jasmine.DEFAULT_TIMEOUT_INTERVAL;
        jasmine.DEFAULT_TIMEOUT_INTERVAL = 15000;
    });

    it('(the test) is able to swap out the behavior of $', function () {
        // This was a pain to write, make sure it doesn't get screwed up.

        // Find the element using DOM methods.
        var legitInput = this.$fixture[0].getElementsByTagName("input")[0];

        // Use the (modified) jQuery.
        var jqueryInput = $('.formulaequationinput input');
        var byIdInput = $("#input_THE_ID");

        expect(jqueryInput[0]).toEqual(legitInput);
        expect(byIdInput[0]).toEqual(legitInput);
    });

    describe('Ajax requests', function () {
        beforeEach(function (done) {
            // This is common to all tests on ajax requests.
            formulaEquationPreview.enable();

            // This part may be asynchronous, so wait.
            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                done();
            });
        });

        it('has an initial request with the correct parameters', function () {
            expect(Problem.inputAjax.calls.count()).toEqual(1);

            // Use `.toEqual` rather than `.toHaveBeenCalledWith`
            // since it supports `jasmine.any`.
            expect(Problem.inputAjax.calls.mostRecent().args).toEqual([
                "THE_URL",
                "THE_ID",
                "preview_formcalc",
                {formula: "PREFILLED_VALUE",
                 request_start: jasmine.any(Number)},
                jasmine.any(Function)
            ]);
        });

        it('makes a request on user input', function (done) {
            Problem.inputAjax.calls.reset();
            $('#input_THE_ID').val('user_input').trigger('input');

            // This part is probably asynchronous
            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                expect(Problem.inputAjax.calls.mostRecent().args[3].formula).toEqual('user_input');
            }).always(done);
        });

        it("isn't requested for empty input", function (done) {
            Problem.inputAjax.calls.reset();

            // When we make an input of '',
            $('#input_THE_ID').val('').trigger('input');

            // Either it makes a request or jumps straight into displaying ''.
            waitForInputAjax(function () {
                // (Short circuit if `inputAjax` is indeed called)
                return Problem.inputAjax.calls.count() > 0 ||
                    MathJax.Hub.Queue.calls.count() > 0;
            }).then(function () {
                // Expect the request not to have been called.
                expect(Problem.inputAjax).not.toHaveBeenCalled();
            }).always(done);
        });

        it('limits the number of requests per second', function (done) {
            var minDelay = formulaEquationPreview.minDelay;
            var end = Date.now() + minDelay * 1.1;

            var $input = $('#input_THE_ID');
            var value;
            function inputAnother(iter) {
                value = "math input " + iter;
                $input.val(value).trigger('input');
            }

            waitForInputAjax((function () {
                var iter = 0;
                return function () {
                    inputAnother(iter++);
                    return Date.now() > end;  // Stop when we get to `end`.
                };
            }())).then(function () {
                return waitForInputAjax(function () {
                    return Problem.inputAjax.calls.count() > 0 &&
                        Problem.inputAjax.calls.mostRecent().args[3].formula == value;
                });
            }).then(_.bind(function () {
                // There should be 2 or 3 calls (depending on leading edge).
                expect(Problem.inputAjax.calls.count()).not.toBeGreaterThan(3);

                // The calls should happen approximately `minDelay` apart.
                for (var i =1; i < this.ajaxTimes.length; i ++) {
                    var diff = this.ajaxTimes[i] - this.ajaxTimes[i - 1];
                    expect(diff).toBeGreaterThan(minDelay - 10);
                }
            }, this)).always(done);
        });
    });

    describe("Visible results (icon and mathjax)", function () {
        it('displays a loading icon when requests are open', function (done) {
            var $img = $("img.loading");
            expect($img.css('visibility')).toEqual('hidden');
            formulaEquationPreview.enable();
            expect($img.css('visibility')).toEqual('visible');

            // This part could be asynchronous
            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                expect($img.css('visibility')).toEqual('visible');

                // Reset and send another request.
                $img.css('visibility', 'hidden');
                $("#input_THE_ID").val("different").trigger('input');

                expect($img.css('visibility')).toEqual('visible');
            }).then(function () {
                return waitForInputAjax(function () {
                    var args = Problem.inputAjax.calls.mostRecent().args;
                    return args[3].formula == "different";
                });
            }).then(done);
        });

        it('updates MathJax and loading icon on callback', function (done) {
            formulaEquationPreview.enable();

            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                var args = Problem.inputAjax.calls.mostRecent().args;
                var callback = args[4];
                callback({
                    preview: 'THE_FORMULA',
                    request_start: args[3].request_start
                });

                // The only request returned--it should hide the loading icon.
                expect($("img.loading").css('visibility')).toEqual('hidden');

                // We should look in the preview div for the MathJax.
                var previewDiv = $("#input_THE_ID_preview")[0];
                expect(MathJax.Hub.getAllJax).toHaveBeenCalledWith(previewDiv);

                // Refresh the MathJax.
                expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Text', this.jax, 'THE_FORMULA']
                );
            }).always(done);
        });

        it('finds alternatives if MathJax hasn\'t finished loading', function (done) {
            formulaEquationPreview.enable();
            $('#input_THE_ID').val('user_input').trigger('input');

            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                var args = Problem.inputAjax.calls.mostRecent().args;
                var callback = args[4];

                // Cannot find MathJax.
                MathJax.Hub.getAllJax.and.returnValue([]);
                spyOn(console, 'log');

                callback({
                    preview: 'THE_FORMULA',
                    request_start: args[3].request_start
                });

                // Tests.
                expect(console.log).toHaveBeenCalled();

                // We should look in the preview div for the MathJax.
                var previewElement = $("#input_THE_ID_preview")[0];
                expect(previewElement.firstChild.data).toEqual("\\(THE_FORMULA\\)");

                // Refresh the MathJax.
                expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Typeset', jasmine.any(Object), jasmine.any(Element)]
                );
            }).always(done);
        });

        it('displays errors from the server well', function (done) {
            var $img = $("img.loading");
            formulaEquationPreview.enable();
            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                var args = Problem.inputAjax.calls.mostRecent().args;
                var callback = args[4];
                callback({
                    error: 'OOPSIE',
                    request_start: args[3].request_start
                });
                expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
                expect($img.css('visibility')).toEqual('visible');
            }).then(function () {
                return waitForInputAjax(function () {
                    return MathJax.Hub.Queue.wasCalled;
                });
            }).then(function () {
                // Refresh the MathJax.
                expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Text', this.jax, '\\text{OOPSIE}']
                );
                expect($img.css('visibility')).toEqual('hidden');
            }).then(done);
        });
    });

    describe('Multiple callbacks', function () {
        beforeEach(function (done) {
            formulaEquationPreview.enable();

            waitForInputAjax(function () {
                return Problem.inputAjax.calls.count() > 0;
            }).then(function () {
                $('#input_THE_ID').val('different').trigger('input');
            }).then(function () {
                return waitForInputAjax(function () {
                    return Problem.inputAjax.calls.count() > 1;
                });
            }).then(_.bind(function () {
                var args0 = Problem.inputAjax.calls.argsFor(0);
                var args1 = Problem.inputAjax.calls.argsFor(1);
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
            }, this)).then(function () {
                done();
            });
        });

        it('updates requests sequentially', function () {
            var $img = $("img.loading");

            expect($img.css('visibility')).toEqual('visible');

            this.callbacks[0](this.responses[0]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_0']
            );
            expect($img.css('visibility')).toEqual('visible');

            this.callbacks[1](this.responses[1]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1']
            );
            expect($img.css('visibility')).toEqual('hidden');
        });

        it("doesn't display outdated information", function () {
            var $img = $("img.loading");

            expect($img.css('visibility')).toEqual('visible');

            // Switch the order (1 returns before 0)
            this.callbacks[1](this.responses[1]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1']
            );
            expect($img.css('visibility')).toEqual('hidden');

            MathJax.Hub.Queue.calls.reset();
            this.callbacks[0](this.responses[0]);
            expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
            expect($img.css('visibility')).toEqual('hidden');
        });

        it("doesn't show an error if the responses are close together", function (done) {
            this.callbacks[0]({
                error: 'OOPSIE',
                request_start: this.responses[0].request_start
            });
            expect(MathJax.Hub.Queue).not.toHaveBeenCalled();

            // Error message waiting to be displayed
            this.callbacks[1](this.responses[1]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1']
            );

            // Make sure that it doesn't indeed show up later
            MathJax.Hub.Queue.calls.reset();
            waitForInputAjax(function () {
                return formulaEquationPreview.errorDelay * 1.1;
            }).then(function () {
                expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
            }).then(done);
        });
    });

    afterEach(function () {
        // Return jQuery
        $.find = this.old$find;
        document.getElementById = this.oldDGEBI;

        // Return Problem
        Problem = this.oldProblem;
        if (Problem === undefined) {
            delete Problem;
        }

        // Return MathJax
        MathJax = this.oldMathJax;
        if (MathJax === undefined) {
            delete MathJax;
        }

        jasmine.DEFAULT_TIMEOUT_INTERVAL = oldJasmineDEFAULT_TIMEOUT_INTERVAL;
    });
});
