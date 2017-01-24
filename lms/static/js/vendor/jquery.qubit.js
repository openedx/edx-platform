/*
** Checkboxes TreeView- jQuery
** https://github.com/aexmachina/jquery-qubit
**
** Copyright (c) 2014 Simon Wade
** The MIT License (MIT)
** https://github.com/aexmachina/jquery-qubit/blob/master/LICENSE.txt
**
*/

(function($) {
  $.fn.qubit = function(options) {
    return this.each(function() {
      var qubit = new Qubit(this, options);
    });
  };
  var Qubit = function(el) {
    var self = this;
    this.scope = $(el);
    this.scope.on('change', 'input[type=checkbox]', function(e) {
      if (!self.suspendListeners) {
        self.process(e.target);
      }
    });
    this.scope.find('input[type=checkbox]:checked').each(function() {
      self.process(this);
    });
  };
  Qubit.prototype = {
    itemSelector: 'li',
    process: function(checkbox) {
      var checkbox = $(checkbox),
          parentItems = checkbox.parentsUntil(this.scope, this.itemSelector);
      try {
        this.suspendListeners = true;
        // all children inherit my state
        parentItems.eq(0).find('input[type=checkbox]')
          .filter(checkbox.prop('checked') ? ':not(:checked)' : ':checked')
          .each(function() {
            if (!$(this).parent().hasClass('hidden')) {
              $(this).prop('checked', checkbox.prop('checked'));
            }
          })
          .trigger('change');
        this.processParents(checkbox);
      } finally {
        this.suspendListeners = false;
      }
    },
    processParents: function() {
      var self = this, changed = false;
      this.scope.find('input[type=checkbox]').each(function() {
        var $this = $(this),
            parent = $this.closest(self.itemSelector),
            children = parent.find('input[type=checkbox]').not($this),
            numChecked = children.filter(function() {
              return $(this).prop('checked') || $(this).prop('indeterminate');
            }).length;

        if (children.length) {
          if (numChecked == 0) {
            if (self.setChecked($this, false)) changed = true;
          } else if (numChecked == children.length) {
            if (self.setChecked($this, true)) changed = true;
          } else {
            if (self.setIndeterminate($this, true)) changed = true;
          }
        }
        else {
          if (self.setIndeterminate($this, false)) changed = true;
        }
      });
      if (changed) this.processParents();
    },
    setChecked: function(checkbox, value, event) {
      var changed = false;
      if (checkbox.prop('indeterminate')) {
        checkbox.prop('indeterminate', false);
        changed = true;
      }
      if (checkbox.prop('checked') != value) {
        checkbox.prop('checked', value).trigger('change');
        changed = true;
      }
      return changed;
    },
    setIndeterminate: function(checkbox, value) {
      if (value) {
        checkbox.prop('checked', false);
      }
      if (checkbox.prop('indeterminate') != value) {
        checkbox.prop('indeterminate', value);
        return true;
      }
    }
  };
}(jQuery));
