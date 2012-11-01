
    show: function() {
      Logger.log('sa_show', {
        problem: _this.id
      });
      return $.postWithPrefix("" + _this.url + "/sa_show", function(response) {
        var answers;
        answers = response.answers;
        return _this.el.addClass('showed');
      });
    }

    save: function() {
      Logger.log('sa_save', _this.answers);
      return $.postWithPrefix("" + _this.url + "/sa_save", _this.answers, function(response) {
        if (response.success) {
          return _this.$('p.rubric').replace(response.rubric);
        }
      });
    }
