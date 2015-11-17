$(document).ready(function () {
  // define variables for code legibility
  var toggleActionElements = $('.toggle-visibility-button');

  var _changeToggleActionText = function(targetElement, actionElement){
    var show_text = actionElement.data('show');
    var hide_text = actionElement.data('hide');

    if( targetElement.is(":visible")){
      if(hide_text){
        actionElement.html(actionElement.data('hide'));
      } else {
        actionElement.hide();
      }
    } else {
      if(show_text){
        actionElement.html(actionElement.data('show'));
      }
    }
  };

  $.each(toggleActionElements, function(i, elem){
    var toggleActionElement = $(elem);
    var toggleTargetElement = toggleActionElement.siblings('.toggle-visibility-element');

    _changeToggleActionText(toggleTargetElement, toggleActionElement);

    toggleActionElement.on('click', function(event){
      event.preventDefault();
      toggleTargetElement.toggleClass('hidden');
      _changeToggleActionText(toggleTargetElement, toggleActionElement);
    });
  });
});