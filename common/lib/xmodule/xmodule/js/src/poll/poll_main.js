// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function(requirejs, require, define) {

  // Even though it is not explicitly in this module, we have to specify
  // 'GeneralMethods' as a dependency. It expands some of the core JS objects
  // with additional useful methods that are used in other modules.
  define("PollMain", ["logme"], function(logme) {

    function PollMain(element) {
      logme(element);
      // alert("PollJSConstructor");

      this.reinitialize(element);
    }

    PollMain.prototype.submit_answer = function (event, _this) {
      // alert('answer');
      _this.status_item = $(event.target).parent().parent().find(
                                           'input:checked').val();
      _this.data = {
        'answer': _this.status_item
      };
      logme( "" + _this.ajax_url + "/submit_answer");
      $.postWithPrefix(
        "" + _this.ajax_url + "/submit_answer",
        _this.data,
        function(response) {
          if (response.success) {
            // alert("Success");
            _this.element.find(".hidden").attr('style',
               'display: block !important; visibility: visible; border: 1px solid green;');
          } else {
            // alert("No success");
            _this.element.find(".hidden").attr('style',
               'display: block !important; visibility: visible; border: 1px solid red;');
          }
        }
      );
    };

    PollMain.prototype.reinitialize = function (element) {
      var _this = this;
      // alert('Reinit');
      this.element = element;
      this.id = element.data("id");
      this.ajax_url = element.data("ajax-url");
      this.state = element.data("state");
      this.answer_button = element.find(".submit-button");
      this.answer_button.click(function (event) {
        // logme('123');
        _this.submit_answer(event, _this);
      });
    };
    return PollMain;
  });
// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));

