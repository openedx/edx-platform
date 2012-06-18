$(document).ready(function(){
  $('section.main-content').children().hide();

  $(function(){
    $('.editable').inlineEdit();
    $('.editable-textarea').inlineEdit({control: 'textarea'});
  });

  var heighest = 0;
  $('.cal ol > li').each(function(){
    heighest = ($(this).height() > heighest) ? $(this).height() : heighest;

  });

  $('.cal ol > li').css('height',heighest + 'px');

  $('.add-new-section').click(function() {
    return false;
  });

  $('.new-week .close').click( function(){
    $(this).parents('.new-week').hide();
    $('p.add-new-week').show();
    return false;
  });

  $('.save-update').click(function(){
      $(this).parent().parent().hide();
      return false;
  });

  setHeight = function(){
    var windowHeight = $(this).height();
    var contentHeight = windowHeight - 29;

    $('section.main-content > section').css('min-height', contentHeight);
    $('body.content .cal').css('height', contentHeight);

    $('.edit-week').click( function() {
      $('body').addClass('content');
      $('body.content .cal').css('height', contentHeight);
      $('section.week-new').show();
      return false;
    });

    $('.cal ol li header h1 a').click( function() {
      $('body').addClass('content');
      $('body.content .cal').css('height', contentHeight);
      $('section.week-edit').show();
      return false;
    });

    $('a.sequence-edit').click(function(){
      $('body').addClass('content');
      $('body.content .cal').css('height', contentHeight);
      $('section.sequence-edit').show();
      return false;
    });
  }

  $(document).ready(setHeight);
  $(window).bind('resize', setHeight);

  $('.video-new a').click(function(){
    $('section.video-new').show();
    return false;
  });

  $('a.video-edit').click(function(){
    $('section.video-edit').show();
    return false;
  });

  $('.problem-new a').click(function(){
    $('section.problem-new').show();
    return false;
  });

  $('a.problem-edit').click(function(){
    $('section.problem-edit').show();
    return false;
  });

});

