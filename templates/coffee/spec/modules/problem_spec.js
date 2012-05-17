(function() {

  describe('Problem', function() {
    beforeEach(function() {
      window.MathJax = {
        Hub: {
          Queue: function() {}
        }
      };
      window.update_schematics = function() {};
      loadFixtures('problem.html');
      spyOn(Logger, 'log');
      return spyOn($.fn, 'load').andCallFake(function(url, callback) {
        $(this).html(readFixtures('problem_content.html'));
        return callback();
      });
    });
    describe('constructor', function() {
      beforeEach(function() {
        return this.problem = new Problem(1, '/problem/url/');
      });
      it('set the element', function() {
        return expect(this.problem.element).toBe('#problem_1');
      });
      it('set the content url', function() {
        return expect(this.problem.content_url).toEqual('/problem/url/problem_get?id=1');
      });
      return it('render the content', function() {
        return expect($.fn.load).toHaveBeenCalledWith(this.problem.content_url, this.problem.bind);
      });
    });
    describe('bind', function() {
      beforeEach(function() {
        spyOn(MathJax.Hub, 'Queue');
        spyOn(window, 'update_schematics');
        return this.problem = new Problem(1, '/problem/url/');
      });
      it('set mathjax typeset', function() {
        return expect(MathJax.Hub.Queue).toHaveBeenCalled();
      });
      it('update schematics', function() {
        return expect(window.update_schematics).toHaveBeenCalled();
      });
      it('bind answer refresh on button click', function() {
        return expect($('section.action input:button')).toHandleWith('click', this.problem.refreshAnswers);
      });
      it('bind the check button', function() {
        return expect($('section.action input.check')).toHandleWith('click', this.problem.check);
      });
      it('bind the reset button', function() {
        return expect($('section.action input.reset')).toHandleWith('click', this.problem.reset);
      });
      it('bind the show button', function() {
        return expect($('section.action input.show')).toHandleWith('click', this.problem.show);
      });
      return it('bind the save button', function() {
        return expect($('section.action input.save')).toHandleWith('click', this.problem.save);
      });
    });
    describe('render', function() {
      beforeEach(function() {
        this.problem = new Problem(1, '/problem/url/');
        this.bind = this.problem.bind;
        return spyOn(this.problem, 'bind');
      });
      describe('with content given', function() {
        beforeEach(function() {
          return this.problem.render('Hello World');
        });
        it('render the content', function() {
          return expect(this.problem.element.html()).toEqual('Hello World');
        });
        return it('re-bind the content', function() {
          return expect(this.problem.bind).toHaveBeenCalled();
        });
      });
      return describe('with no content given', function() {
        return it('load the content via ajax', function() {
          return expect($.fn.load).toHaveBeenCalledWith(this.problem.content_url, this.bind);
        });
      });
    });
    describe('check', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.problem = new Problem(1, '/problem/url/');
        return this.problem.answers = 'foo=1&bar=2';
      });
      it('log the problem_check event', function() {
        this.problem.check();
        return expect(Logger.log).toHaveBeenCalledWith('problem_check', 'foo=1&bar=2');
      });
      it('submit the answer for check', function() {
        spyOn($, 'postWithPrefix');
        this.problem.check();
        return expect($.postWithPrefix).toHaveBeenCalledWith('/modx/problem/1/problem_check', 'foo=1&bar=2', jasmine.any(Function));
      });
      describe('when the response is correct', function() {
        return it('call render with returned content', function() {
          spyOn($, 'postWithPrefix').andCallFake(function(url, answers, callback) {
            return callback({
              success: 'correct',
              contents: 'Correct!'
            });
          });
          this.problem.check();
          return expect(this.problem.element.html()).toEqual('Correct!');
        });
      });
      describe('when the response is incorrect', function() {
        return it('call render with returned content', function() {
          spyOn($, 'postWithPrefix').andCallFake(function(url, answers, callback) {
            return callback({
              success: 'incorrect',
              contents: 'Correct!'
            });
          });
          this.problem.check();
          return expect(this.problem.element.html()).toEqual('Correct!');
        });
      });
      return describe('when the response is undetermined', function() {
        return it('alert the response', function() {
          spyOn(window, 'alert');
          spyOn($, 'postWithPrefix').andCallFake(function(url, answers, callback) {
            return callback({
              success: 'Number Only!'
            });
          });
          this.problem.check();
          return expect(window.alert).toHaveBeenCalledWith('Number Only!');
        });
      });
    });
    describe('reset', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        return this.problem = new Problem(1, '/problem/url/');
      });
      it('log the problem_reset event', function() {
        this.problem.answers = 'foo=1&bar=2';
        this.problem.reset();
        return expect(Logger.log).toHaveBeenCalledWith('problem_reset', 'foo=1&bar=2');
      });
      it('POST to the problem reset page', function() {
        spyOn($, 'postWithPrefix');
        this.problem.reset();
        return expect($.postWithPrefix).toHaveBeenCalledWith('/modx/problem/1/problem_reset', {
          id: 1
        }, jasmine.any(Function));
      });
      return it('render the returned content', function() {
        spyOn($, 'postWithPrefix').andCallFake(function(url, answers, callback) {
          return callback("Reset!");
        });
        this.problem.reset();
        return expect(this.problem.element.html()).toEqual('Reset!');
      });
    });
    describe('show', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.problem = new Problem(1, '/problem/url/');
        return this.problem.element.prepend('<div id="answer_1_1" /><div id="answer_1_2" />');
      });
      describe('when the answer has not yet shown', function() {
        beforeEach(function() {
          return this.problem.element.removeClass('showed');
        });
        it('log the problem_show event', function() {
          this.problem.show();
          return expect(Logger.log).toHaveBeenCalledWith('problem_show', {
            problem: 1
          });
        });
        it('fetch the answers', function() {
          spyOn($, 'postWithPrefix');
          this.problem.show();
          return expect($.postWithPrefix).toHaveBeenCalledWith('/modx/problem/1/problem_show', jasmine.any(Function));
        });
        it('show the answers', function() {
          spyOn($, 'postWithPrefix').andCallFake(function(url, callback) {
            return callback({
              '1_1': 'One',
              '1_2': 'Two'
            });
          });
          this.problem.show();
          expect($('#answer_1_1')).toHaveHtml('One');
          return expect($('#answer_1_2')).toHaveHtml('Two');
        });
        it('toggle the show answer button', function() {
          spyOn($, 'postWithPrefix').andCallFake(function(url, callback) {
            return callback({});
          });
          this.problem.show();
          return expect($('.show')).toHaveValue('Hide Answer');
        });
        it('add the showed class to element', function() {
          spyOn($, 'postWithPrefix').andCallFake(function(url, callback) {
            return callback({});
          });
          this.problem.show();
          return expect(this.problem.element).toHaveClass('showed');
        });
        return describe('multiple choice question', function() {
          beforeEach(function() {
            return this.problem.element.prepend('<label for="input_1_1_1"><input type="checkbox" name="input_1_1" id="input_1_1_1" value="1"> One</label>\n<label for="input_1_1_2"><input type="checkbox" name="input_1_1" id="input_1_1_2" value="2"> Two</label>\n<label for="input_1_1_3"><input type="checkbox" name="input_1_1" id="input_1_1_3" value="3"> Three</label>\n<label for="input_1_2_1"><input type="radio" name="input_1_2" id="input_1_2_1" value="1"> Other</label>');
          });
          return it('set the correct_answer attribute on the choice', function() {
            spyOn($, 'postWithPrefix').andCallFake(function(url, callback) {
              return callback({
                '1_1': [2, 3]
              });
            });
            this.problem.show();
            expect($('label[for="input_1_1_1"]')).not.toHaveAttr('correct_answer', 'true');
            expect($('label[for="input_1_1_2"]')).toHaveAttr('correct_answer', 'true');
            expect($('label[for="input_1_1_3"]')).toHaveAttr('correct_answer', 'true');
            return expect($('label[for="input_1_2_1"]')).not.toHaveAttr('correct_answer', 'true');
          });
        });
      });
      return describe('when the answers are alreay shown', function() {
        beforeEach(function() {
          this.problem.element.addClass('showed');
          this.problem.element.prepend('<label for="input_1_1_1" correct_answer="true">\n  <input type="checkbox" name="input_1_1" id="input_1_1_1" value="1" />\n  One\n</label>');
          $('#answer_1_1').html('One');
          return $('#answer_1_2').html('Two');
        });
        it('hide the answers', function() {
          this.problem.show();
          expect($('#answer_1_1')).toHaveHtml('');
          expect($('#answer_1_2')).toHaveHtml('');
          return expect($('label[for="input_1_1_1"]')).not.toHaveAttr('correct_answer');
        });
        it('toggle the show answer button', function() {
          this.problem.show();
          return expect($('.show')).toHaveValue('Show Answer');
        });
        return it('remove the showed class from element', function() {
          this.problem.show();
          return expect(this.problem.element).not.toHaveClass('showed');
        });
      });
    });
    describe('save', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.problem = new Problem(1, '/problem/url/');
        return this.problem.answers = 'foo=1&bar=2';
      });
      it('log the problem_save event', function() {
        this.problem.save();
        return expect(Logger.log).toHaveBeenCalledWith('problem_save', 'foo=1&bar=2');
      });
      it('POST to save problem', function() {
        spyOn($, 'postWithPrefix');
        this.problem.save();
        return expect($.postWithPrefix).toHaveBeenCalledWith('/modx/problem/1/problem_save', 'foo=1&bar=2', jasmine.any(Function));
      });
      return it('alert to the user', function() {
        spyOn(window, 'alert');
        spyOn($, 'postWithPrefix').andCallFake(function(url, answers, callback) {
          return callback({
            success: 'OK'
          });
        });
        this.problem.save();
        return expect(window.alert).toHaveBeenCalledWith('Saved');
      });
    });
    return describe('refreshAnswers', function() {
      beforeEach(function() {
        this.problem = new Problem(1, '/problem/url/');
        this.problem.element.html('<textarea class="CodeMirror" />\n<input id="input_1_1" name="input_1_1" class="schematic" value="one" />\n<input id="input_1_2" name="input_1_2" value="two" />\n<input id="input_bogus_3" name="input_bogus_3" value="three" />');
        this.stubSchematic = {
          update_value: jasmine.createSpy('schematic')
        };
        this.stubCodeMirror = {
          save: jasmine.createSpy('CodeMirror')
        };
        $('input.schematic').get(0).schematic = this.stubSchematic;
        return $('textarea.CodeMirror').get(0).CodeMirror = this.stubCodeMirror;
      });
      it('update each schematic', function() {
        this.problem.refreshAnswers();
        return expect(this.stubSchematic.update_value).toHaveBeenCalled();
      });
      it('update each code block', function() {
        this.problem.refreshAnswers();
        return expect(this.stubCodeMirror.save).toHaveBeenCalled();
      });
      return it('serialize all answers', function() {
        this.problem.refreshAnswers();
        return expect(this.problem.answers).toEqual("input_1_1=one&input_1_2=two");
      });
    });
  });

}).call(this);
