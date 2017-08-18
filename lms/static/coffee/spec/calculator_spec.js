describe('Calculator', function() {

  const KEY = {
    TAB   : 9,
    ENTER : 13,
    ALT   : 18,
    ESC   : 27,
    SPACE : 32,
    LEFT  : 37,
    UP    : 38,
    RIGHT : 39,
    DOWN  : 40
  };

  beforeEach(function() {
    loadFixtures('coffee/fixtures/calculator.html');
    this.calculator = new Calculator;
  });

  describe('bind', function() {
    it('bind the calculator button', function() {
      expect($('.calc')).toHandleWith('click', this.calculator.toggle);
    });

    it('bind key up on calculator', function() {
      expect($('#calculator_wrapper')).toHandle('keyup', this.calculator.handleKeyUpOnHint);
    });

    it('bind the help button', () =>
      // This events is bind by $.click()
      expect($('#calculator_hint')).toHandle('click')
    );

    it('bind the calculator submit', function() {
      expect($('form#calculator')).toHandleWith('submit', this.calculator.calculate);
    });

    xit('prevent default behavior on form submit', function() {
      jasmine.stubRequests();
      $('form#calculator').submit(function(e) {
        expect(e.isDefaultPrevented()).toBeTruthy();
        return e.preventDefault();
      });
      return $('form#calculator').submit();
    });
  });

  describe('toggle', function() {
    it('focuses the input when toggled', function(done){

      const self = this;
      const focus = function(){
        const deferred = $.Deferred();

        // Since the focus is called asynchronously, we need to
        // wait until focus() is called.
        spyOn($.fn, 'focus').and.callFake(elementName => deferred.resolve());

        self.calculator.toggle(jQuery.Event("click"));

      	return deferred.promise();
      };

      focus().then(
        () => expect($('#calculator_wrapper #calculator_input').focus).toHaveBeenCalled()).always(done);
    });

    it('toggle the close button on the calculator button', function() {
      this.calculator.toggle(jQuery.Event("click"));
      expect($('.calc')).toHaveClass('closed');

      this.calculator.toggle(jQuery.Event("click"));
      expect($('.calc')).not.toHaveClass('closed');
    });
  });

  describe('showHint', () =>
    it('show the help overlay', function() {
      this.calculator.showHint();
      expect($('.help')).toHaveClass('shown');
      expect($('.help')).toHaveAttr('aria-hidden', 'false');
    })
  );


  describe('hideHint', () =>
    it('show the help overlay', function() {
      this.calculator.hideHint();
      expect($('.help')).not.toHaveClass('shown');
      expect($('.help')).toHaveAttr('aria-hidden', 'true');
    })
  );

  describe('handleClickOnHintButton', () =>
    it('on click hint button hint popup becomes visible ', function() {
      const e = jQuery.Event('click');
      $('#calculator_hint').trigger(e);
      expect($('.help')).toHaveClass('shown');
    })
  );

  describe('handleClickOnDocument', () =>
    it('on click out of the hint popup it becomes hidden', function() {
      this.calculator.showHint();
      const e = jQuery.Event('click');
      $(document).trigger(e);
      expect($('.help')).not.toHaveClass('shown');
    })
  );

  describe('handleClickOnHintPopup', () =>
    it('on click of hint popup it remains visible', function() {
      this.calculator.showHint();
      const e = jQuery.Event('click');
      $('#calculator_input_help').trigger(e);
      expect($('.help')).toHaveClass('shown');
    })
  );

  describe('selectHint', function() {
    it('select correct hint item', function() {
      spyOn($.fn, 'focus');
      const element = $('.hint-item').eq(1);
      this.calculator.selectHint(element);

      expect(element.focus).toHaveBeenCalled();
      expect(this.calculator.activeHint).toEqual(element);
      expect(this.calculator.hintPopup).toHaveAttr('data-calculator-hint', element.attr('id'));
    });

    it('select the first hint if argument element is not passed', function() {
          this.calculator.selectHint();
          expect(this.calculator.activeHint.attr('id')).toEqual($('.hint-item').first().attr('id'));
    });

    it('select the first hint if argument element is empty', function() {
          this.calculator.selectHint([]);
          expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').first().attr('id'));
    });
  });

  describe('prevHint', function() {

    it('Prev hint item is selected', function() {
      this.calculator.activeHint = $('.hint-item').eq(1);
      this.calculator.prevHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(0).attr('id'));
    });

    it('if this was the second item, select the first one', function() {
      this.calculator.activeHint = $('.hint-item').eq(1);
      this.calculator.prevHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(0).attr('id'));
    });

    it('if this was the first item, select the last one', function() {
      this.calculator.activeHint = $('.hint-item').eq(0);
      this.calculator.prevHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(2).attr('id'));
    });

    it('if this was the last item, select the second last', function() {
      this.calculator.activeHint = $('.hint-item').eq(2);
      this.calculator.prevHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(1).attr('id'));
    });
  });

  describe('nextHint', function() {

    it('if this was the first item, select the second one', function() {
      this.calculator.activeHint = $('.hint-item').eq(0);
      this.calculator.nextHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(1).attr('id'));
    });

    it('If this was the second item, select the last one', function() {
      this.calculator.activeHint = $('.hint-item').eq(1);
      this.calculator.nextHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(2).attr('id'));
    });

    it('If this was the last item, select the first one', function() {
      this.calculator.activeHint = $('.hint-item').eq(2);
      this.calculator.nextHint();

      expect(this.calculator.activeHint.attr('id')).toBe($('.hint-item').eq(0).attr('id'));
    });
  });

  describe('handleKeyDown', function() {
    const assertHintIsHidden = function(calc, key) {
      spyOn(calc, 'hideHint');
      calc.showHint();
      const e = jQuery.Event('keydown', { keyCode: key });
      const value = calc.handleKeyDown(e);

      expect(calc.hideHint).toHaveBeenCalled;
      expect(value).toBeFalsy();
      expect(e.isDefaultPrevented()).toBeTruthy();
    };

    const assertHintIsVisible = function(calc, key) {
      spyOn(calc, 'showHint');
      spyOn($.fn, 'focus');
      const e = jQuery.Event('keydown', { keyCode: key });
      const value = calc.handleKeyDown(e);

      expect(calc.showHint).toHaveBeenCalled;
      expect(value).toBeFalsy();
      expect(e.isDefaultPrevented()).toBeTruthy();
      expect(calc.activeHint.focus).toHaveBeenCalled();
    };

    const assertNothingHappens = function(calc, key) {
      spyOn(calc, 'showHint');
      const e = jQuery.Event('keydown', { keyCode: key });
      const value = calc.handleKeyDown(e);

      expect(calc.showHint).not.toHaveBeenCalled;
      expect(value).toBeTruthy();
      expect(e.isDefaultPrevented()).toBeFalsy();
    };

    it('hint popup becomes hidden on press ENTER', function() {
      assertHintIsHidden(this.calculator, KEY.ENTER);
    });

    it('hint popup becomes visible on press ENTER', function() {
      assertHintIsVisible(this.calculator, KEY.ENTER);
    });

    it('hint popup becomes hidden on press SPACE', function() {
      assertHintIsHidden(this.calculator, KEY.SPACE);
    });

    it('hint popup becomes visible on press SPACE', function() {
      assertHintIsVisible(this.calculator, KEY.SPACE);
    });

    it('Nothing happens on press ALT', function() {
      assertNothingHappens(this.calculator, KEY.ALT);
    });

    it('Nothing happens on press any other button', function() {
      assertNothingHappens(this.calculator, KEY.DOWN);
    });
  });

  describe('handleKeyDownOnHint', () =>
    it('Navigation works in proper way', function() {
      const calc = this.calculator;

      const eventToShowHint = jQuery.Event('keydown', { keyCode: KEY.ENTER } );
      $('#calculator_hint').trigger(eventToShowHint);

      spyOn(calc, 'hideHint');
      spyOn(calc, 'prevHint');
      spyOn(calc, 'nextHint');
      spyOn($.fn, 'focus');

      const cases = {
        left: {
          event: {
            keyCode: KEY.LEFT,
            shiftKey: false
          },
          returnedValue: false,
          called: {
            'prevHint': calc
          },
          isPropagationStopped: true
        },

        leftWithShift: {
          returnedValue: true,
          event: {
            keyCode: KEY.LEFT,
            shiftKey: true
          },
          not_called: {
            'prevHint': calc
          }
        },

        up: {
          event: {
            keyCode: KEY.UP,
            shiftKey: false
          },
          returnedValue: false,
          called: {
            'prevHint': calc
          },
          isPropagationStopped: true
        },

        upWithShift: {
          returnedValue: true,
          event: {
            keyCode: KEY.UP,
            shiftKey: true
          },
          not_called: {
            'prevHint': calc
          }
        },

        right: {
          event: {
            keyCode: KEY.RIGHT,
            shiftKey: false
          },
          returnedValue: false,
          called: {
            'nextHint': calc
          },
          isPropagationStopped: true
        },

        rightWithShift: {
          returnedValue: true,
          event: {
            keyCode: KEY.RIGHT,
            shiftKey: true
          },
          not_called: {
            'nextHint': calc
          }
        },

        down: {
          event: {
            keyCode: KEY.DOWN,
            shiftKey: false
          },
          returnedValue: false,
          called: {
            'nextHint': calc
          },
          isPropagationStopped: true
        },

        downWithShift: {
          returnedValue: true,
          event: {
            keyCode: KEY.DOWN,
            shiftKey: true
          },
          not_called: {
            'nextHint': calc
          }
        },

        esc: {
          returnedValue: false,
          event: {
            keyCode: KEY.ESC,
            shiftKey: false
          },
          called: {
            'hideHint': calc,
            'focus': $.fn
          },
          isPropagationStopped: true
        },

        alt: {
          returnedValue: true,
          event: {
            which: KEY.ALT
          },
          not_called: {
            'hideHint': calc,
            'nextHint': calc,
            'prevHint': calc
          }
        }
      };

      $.each(cases, function(key, data) {
        calc.hideHint.calls.reset();
        calc.prevHint.calls.reset();
        calc.nextHint.calls.reset();
        $.fn.focus.calls.reset();

        const e = jQuery.Event('keydown', data.event || {});
        const value = calc.handleKeyDownOnHint(e);

        if (data.called) {
          $.each(data.called, (method, obj) => expect(obj[method]).toHaveBeenCalled());
        }

        if (data.not_called) {
          $.each(data.not_called, (method, obj) => expect(obj[method]).not.toHaveBeenCalled());
        }

        if (data.isPropagationStopped) {
          expect(e.isPropagationStopped()).toBeTruthy();
        } else {
          expect(e.isPropagationStopped()).toBeFalsy();
        }

        expect(value).toBe(data.returnedValue);
      });
    })
  );

  describe('calculate', function() {
    beforeEach(function() {
      $('#calculator_input').val('1+2');
      spyOn($, 'getWithPrefix').and.callFake((url, data, callback) => callback({ result: 3 }));
      this.calculator.calculate();
    });

    it('send data to /calculate', () =>
      expect($.getWithPrefix).toHaveBeenCalledWith('/calculate',
        {equation: '1+2'}
      , jasmine.any(Function))
    );

    it('update the calculator output', () => expect($('#calculator_output').val()).toEqual('3'));
  });
});
