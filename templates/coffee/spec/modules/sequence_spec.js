(function() {

  describe('Sequence', function() {
    beforeEach(function() {
      window.MathJax = {
        Hub: {
          Queue: function() {}
        }
      };
      spyOn(Logger, 'log');
      loadFixtures('sequence.html');
      return this.items = $.parseJSON(readFixtures('items.json'));
    });
    describe('constructor', function() {
      beforeEach(function() {
        return this.sequence = new Sequence('1', this.items, 1);
      });
      it('set the element', function() {
        return expect(this.sequence.element).toEqual($('#sequence_1'));
      });
      it('build the navigation', function() {
        var classes, elements, titles;
        classes = $('#sequence-list li>a').map(function() {
          return $(this).attr('class');
        }).get();
        elements = $('#sequence-list li>a').map(function() {
          return $(this).attr('data-element');
        }).get();
        titles = $('#sequence-list li>a>p').map(function() {
          return $(this).html();
        }).get();
        expect(classes).toEqual(['seq_video_active', 'seq_video_inactive', 'seq_problem_inactive']);
        expect(elements).toEqual(['1', '2', '3']);
        return expect(titles).toEqual(['Video 1', 'Video 2', 'Sample Problem']);
      });
      it('bind the page events', function() {
        expect(this.sequence.element).toHandleWith('contentChanged', this.sequence.toggleArrows);
        return expect($('#sequence-list a')).toHandleWith('click', this.sequence.goto);
      });
      return it('render the active sequence content', function() {
        return expect($('#seq_content').html()).toEqual('Video 1');
      });
    });
    describe('toggleArrows', function() {
      beforeEach(function() {
        return this.sequence = new Sequence('1', this.items, 1);
      });
      describe('when the first tab is active', function() {
        beforeEach(function() {
          this.sequence.position = 1;
          return this.sequence.toggleArrows();
        });
        it('disable the previous button', function() {
          return expect($('.sequence-nav-buttons .prev a')).toHaveClass('disabled');
        });
        return it('enable the next button', function() {
          expect($('.sequence-nav-buttons .next a')).not.toHaveClass('disabled');
          return expect($('.sequence-nav-buttons .next a')).toHandleWith('click', this.sequence.next);
        });
      });
      describe('when the middle tab is active', function() {
        beforeEach(function() {
          this.sequence.position = 2;
          return this.sequence.toggleArrows();
        });
        it('enable the previous button', function() {
          expect($('.sequence-nav-buttons .prev a')).not.toHaveClass('disabled');
          return expect($('.sequence-nav-buttons .prev a')).toHandleWith('click', this.sequence.previous);
        });
        return it('enable the next button', function() {
          expect($('.sequence-nav-buttons .next a')).not.toHaveClass('disabled');
          return expect($('.sequence-nav-buttons .next a')).toHandleWith('click', this.sequence.next);
        });
      });
      return describe('when the last tab is active', function() {
        beforeEach(function() {
          this.sequence.position = 3;
          return this.sequence.toggleArrows();
        });
        it('enable the previous button', function() {
          expect($('.sequence-nav-buttons .prev a')).not.toHaveClass('disabled');
          return expect($('.sequence-nav-buttons .prev a')).toHandleWith('click', this.sequence.previous);
        });
        return it('disable the next button', function() {
          return expect($('.sequence-nav-buttons .next a')).toHaveClass('disabled');
        });
      });
    });
    describe('render', function() {
      beforeEach(function() {
        spyOn($, 'postWithPrefix');
        this.sequence = new Sequence('1', this.items);
        return spyOnEvent(this.sequence.element, 'contentChanged');
      });
      describe('with a different position than the current one', function() {
        beforeEach(function() {
          return this.sequence.render(1);
        });
        describe('with no previous position', function() {
          return it('does not save the new position', function() {
            return expect($.postWithPrefix).not.toHaveBeenCalled();
          });
        });
        describe('with previous position', function() {
          beforeEach(function() {
            this.sequence.position = 2;
            return this.sequence.render(1);
          });
          it('mark the previous tab as visited', function() {
            return expect($('[data-element="2"]')).toHaveClass('seq_video_visited');
          });
          return it('save the new position', function() {
            return expect($.postWithPrefix).toHaveBeenCalledWith('/modx/sequential/1/goto_position', {
              position: 1
            });
          });
        });
        it('mark new tab as active', function() {
          return expect($('[data-element="1"]')).toHaveClass('seq_video_active');
        });
        it('render the new content', function() {
          return expect($('#seq_content').html()).toEqual('Video 1');
        });
        it('update the position', function() {
          return expect(this.sequence.position).toEqual(1);
        });
        return it('trigger contentChanged event', function() {
          return expect('contentChanged').toHaveBeenTriggeredOn(this.sequence.element);
        });
      });
      return describe('with the same position as the current one', function() {
        return it('should not trigger contentChanged event', function() {
          this.sequence.position = 2;
          this.sequence.render(2);
          return expect('contentChanged').not.toHaveBeenTriggeredOn(this.sequence.element);
        });
      });
    });
    describe('goto', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.sequence = new Sequence('1', this.items, 2);
        return $('[data-element="3"]').click();
      });
      it('log the sequence goto event', function() {
        return expect(Logger.log).toHaveBeenCalledWith('seq_goto', {
          old: 2,
          "new": 3,
          id: '1'
        });
      });
      return it('call render on the right sequence', function() {
        return expect($('#seq_content').html()).toEqual('Sample Problem');
      });
    });
    describe('next', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.sequence = new Sequence('1', this.items, 2);
        return $('.sequence-nav-buttons .next a').click();
      });
      it('log the next sequence event', function() {
        return expect(Logger.log).toHaveBeenCalledWith('seq_next', {
          old: 2,
          "new": 3,
          id: '1'
        });
      });
      return it('call render on the next sequence', function() {
        return expect($('#seq_content').html()).toEqual('Sample Problem');
      });
    });
    describe('previous', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.sequence = new Sequence('1', this.items, 2);
        return $('.sequence-nav-buttons .prev a').click();
      });
      it('log the previous sequence event', function() {
        return expect(Logger.log).toHaveBeenCalledWith('seq_prev', {
          old: 2,
          "new": 1,
          id: '1'
        });
      });
      return it('call render on the previous sequence', function() {
        return expect($('#seq_content').html()).toEqual('Video 1');
      });
    });
    return describe('link_for', function() {
      return it('return a link for specific position', function() {
        var sequence;
        sequence = new Sequence('1', this.items, 2);
        return expect(sequence.link_for(2)).toBe('[data-element="2"]');
      });
    });
  });

}).call(this);
