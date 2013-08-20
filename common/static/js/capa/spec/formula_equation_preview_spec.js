function callPeriodicallyUntil(block, delay, condition, i) {  // i is optional
    i = i || 0;
    block(i);
    waits(delay);
    runs(function () {
        if (!condition()) {
            callPeriodicallyUntil(block, delay, condition, i + 1);
        }
    });
}

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
        }
        $.find.matchesSelector = old$find.matchesSelector;

        this.oldDGEBI = document.getElementById;
        document.getElementById = function (id) {
            return $("*#" + id)[0] || null;
        };

        // Catch the AJAX requests
        var ajaxTimes = this.ajaxTimes = [];
        this.oldProblem = window.Problem;

        window.Problem = {};
        Problem.inputAjax = jasmine.createSpy('Problem.inputAjax')
            .andCallFake(function () {
                ajaxTimes.push(Date.now());
            });

        // Spy on MathJax
        this.jax = 'OUTPUT_JAX';
        this.oldMathJax = window.MathJax;

        window.MathJax = {Hub: {}};
        MathJax.Hub.getAllJax = jasmine.createSpy('MathJax.Hub.getAllJax')
            .andReturn([this.jax]);
        MathJax.Hub.Queue = jasmine.createSpy('MathJax.Hub.Queue');
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
        beforeEach(function () {
            // This is common to all tests on ajax requests.
            formulaEquationPreview.enable();

            // This part may be asynchronous, so wait.
            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            }, "AJAX never called initially", 1000);
        });

        it('has an initial request with the correct parameters', function () {
            expect(Problem.inputAjax.callCount).toEqual(1);

            // Use `.toEqual` rather than `.toHaveBeenCalledWith`
            // since it supports `jasmine.any`.
            expect(Problem.inputAjax.mostRecentCall.args).toEqual([
                "THE_URL",
                "THE_ID",
                "preview_formcalc",
                {formula: "PREFILLED_VALUE",
                 request_start: jasmine.any(Number)},
                jasmine.any(Function)
            ]);
        });

        it('makes a request on user input', function () {
            Problem.inputAjax.reset();
            $('#input_THE_ID').val('user_input').trigger('input');

            // This part is probably asynchronous
            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            }, "AJAX never called on user input", 1000);

            runs(function () {
                expect(Problem.inputAjax.mostRecentCall.args[3].formula
                      ).toEqual('user_input');
            });
        });

        it("isn't requested for empty input", function () {
            Problem.inputAjax.reset();

            // When we make an input of '',
            $('#input_THE_ID').val('').trigger('input');

            // Either it makes a request or jumps straight into displaying ''.
            waitsFor(function () {
                // (Short circuit if `inputAjax` is indeed called)
                return Problem.inputAjax.wasCalled || 
                    MathJax.Hub.Queue.wasCalled;
            }, "AJAX never called on user input", 1000);

            runs(function () {
                // Expect the request not to have been called.
                expect(Problem.inputAjax).not.toHaveBeenCalled();
            });
        });

        it('limits the number of requests per second', function () {
            var minDelay = formulaEquationPreview.minDelay;
            var end = Date.now() + minDelay * 1.1;
            var step = 10;  // ms

            var $input = $('#input_THE_ID');
            var value;
            function inputAnother(iter) {
                value = "math input " + iter;
                $input.val(value).trigger('input');
            }

            callPeriodicallyUntil(inputAnother, step, function () {
                return Date.now() > end;  // Stop when we get to `end`.
            });

            waitsFor(function () {
                return Problem.inputAjax.wasCalled &&
                    Problem.inputAjax.mostRecentCall.args[3].formula == value;
            }, "AJAX never called with final value from input", 1000);

            runs(function () {
                // There should be 2 or 3 calls (depending on leading edge).
                expect(Problem.inputAjax.callCount).not.toBeGreaterThan(3);

                // The calls should happen approximately `minDelay` apart.
                for (var i =1; i < this.ajaxTimes.length; i ++) {
                    var diff = this.ajaxTimes[i] - this.ajaxTimes[i - 1];
                    expect(diff).toBeGreaterThan(minDelay - 10);
                }
            });
        });
    });

    describe("Visible results (icon and mathjax)", function () {
        it('displays a loading icon when requests are open', function () {
            var $img = $("img.loading");
            expect($img.css('visibility')).toEqual('hidden');
            formulaEquationPreview.enable();
            expect($img.css('visibility')).toEqual('visible');

            // This part could be asynchronous
            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            }, "AJAX never called initially", 1000);

            runs(function () {
                expect($img.css('visibility')).toEqual('visible');

                // Reset and send another request.
                $img.css('visibility', 'hidden');
                $("#input_THE_ID").val("different").trigger('input');

                expect($img.css('visibility')).toEqual('visible');
            });

            // Don't let it fail later.
            waitsFor(function () {
                var args = Problem.inputAjax.mostRecentCall.args;
                return args[3].formula == "different";
            });
        });

        it('updates MathJax and loading icon on callback', function () {
            formulaEquationPreview.enable();
            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            }, "AJAX never called initially", 1000);

            runs(function () {
                var args = Problem.inputAjax.mostRecentCall.args;
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
                    ['Text', this.jax, 'THE_FORMULA'],
                    ['Reprocess', this.jax]
                );
            });
        });

        it('finds alternatives if MathJax hasn\'t finished loading', function () {
            formulaEquationPreview.enable();
            $('#input_THE_ID').val('user_input').trigger('input');

            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            }, "AJAX never called initially", 1000);

            runs(function () {
                var args = Problem.inputAjax.mostRecentCall.args;
                var callback = args[4];

                // Cannot find MathJax.
                MathJax.Hub.getAllJax.andReturn([]);
                spyOn(console, 'warn');

                callback({
                    preview: 'THE_FORMULA',
                    request_start: args[3].request_start
                });

                // Tests.
                expect(console.warn).toHaveBeenCalled();

                // We should look in the preview div for the MathJax.
                var previewElement = $("#input_THE_ID_preview")[0];
                expect(previewElement.firstChild.data).toEqual("\\[THE_FORMULA\\]");

                // Refresh the MathJax.
                expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Typeset', jasmine.any(Object), jasmine.any(Element)]
                );
            });
        });

        it('displays errors from the server well', function () {
            var $img = $("img.loading");
            formulaEquationPreview.enable();
            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            }, "AJAX never called initially", 1000);

            runs(function () {
                var args = Problem.inputAjax.mostRecentCall.args;
                var callback = args[4];
                callback({
                    error: 'OOPSIE',
                    request_start: args[3].request_start
                });
                expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
                expect($img.css('visibility')).toEqual('visible');
            });

            var errorDelay = formulaEquationPreview.errorDelay * 1.1;
            waitsFor(function () {
                return MathJax.Hub.Queue.wasCalled;
            }, "Error message never displayed", 2000);

            runs(function () {
                // Refresh the MathJax.
                expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                    ['Text', this.jax, '\\text{OOPSIE}'],
                    ['Reprocess', this.jax]
                );
                expect($img.css('visibility')).toEqual('hidden');
            });
        });
    });

    describe('Multiple callbacks', function () {
        beforeEach(function () {
            formulaEquationPreview.enable();

            waitsFor(function () {
                return Problem.inputAjax.wasCalled;
            });

            runs(function () {
                $('#input_THE_ID').val('different').trigger('input');
            });

            waitsFor(function () {
                return Problem.inputAjax.callCount > 1;
            });

            runs(function () {
                var args = Problem.inputAjax.argsForCall;
                var response0 = {
                    preview: 'THE_FORMULA_0',
                    request_start: args[0][3].request_start
                };
                var response1 = {
                    preview: 'THE_FORMULA_1',
                    request_start: args[1][3].request_start
                };

                this.callbacks = [args[0][4], args[1][4]];
                this.responses = [response0, response1];
            });
        });

        it('updates requests sequentially', function () {
            var $img = $("img.loading");

            expect($img.css('visibility')).toEqual('visible');

            this.callbacks[0](this.responses[0]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_0'],
                ['Reprocess', this.jax]
            );
            expect($img.css('visibility')).toEqual('visible');

            this.callbacks[1](this.responses[1]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1'],
                ['Reprocess', this.jax]
            );
            expect($img.css('visibility')).toEqual('hidden')
        });

        it("doesn't display outdated information", function () {
            var $img = $("img.loading");

            expect($img.css('visibility')).toEqual('visible');

            // Switch the order (1 returns before 0)
            this.callbacks[1](this.responses[1]);
            expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                ['Text', this.jax, 'THE_FORMULA_1'],
                ['Reprocess', this.jax]
            );
            expect($img.css('visibility')).toEqual('hidden')

            MathJax.Hub.Queue.reset();
            this.callbacks[0](this.responses[0]);
            expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
            expect($img.css('visibility')).toEqual('hidden')
        });

        it("doesn't show an error if the responses are close together",
           function () {
               this.callbacks[0]({
                   error: 'OOPSIE',
                   request_start: this.responses[0].request_start
               });
               expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
               // Error message waiting to be displayed

               this.callbacks[1](this.responses[1]);
               expect(MathJax.Hub.Queue).toHaveBeenCalledWith(
                   ['Text', this.jax, 'THE_FORMULA_1'],
                   ['Reprocess', this.jax]
               );

               // Make sure that it doesn't indeed show up later
               MathJax.Hub.Queue.reset();
               var errorDelay = formulaEquationPreview.errorDelay * 1.1;
               waits(errorDelay);

               runs(function () {
                   expect(MathJax.Hub.Queue).not.toHaveBeenCalled();
               })
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
    });
});
