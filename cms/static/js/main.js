$(document).ready(function(){
  $('section.main-content').children().hide();

  $(function(){
    $('.editable').inlineEdit();
    $('.editable-textarea').inlineEdit({control: 'textarea'});
  });

  // $("a[rel*=leanModal]").leanModal();

  // $(".remove").click(function(){
  //   $(this).parents('li').hide();
  // });

  // $("#show-sidebar").click(function(){
  //   $("#video-selector").toggleClass('hidden');
  //   return false;
  // });

  // $('.use-video').click(function() {
  //   var used = $('#used');
  //   if (used.is(':visible')) {
  //     used.hide().show('slow');
  //   }
  //   used.show();
  //   $('.no-video').hide();
  // });

  // $('.remove-video').click(function() {
  //   $('#used').hide();
  //   $('.no-video').show();
  // });

  // $('#new-upload').click(function() {
  //   $('.selected-files').toggle();
  //   return false;
  // });

  // /* $('.block').append('<a href=\"#\" class=\"delete\">&#10005;<\/a>'); */

  // $('a.delete').click(function() {
  //   $(this).parents('.block').hide();
  // });

  // $('.speed-list > li').hover(function(){
  //   $(this).children('.tooltip').toggle();
  // });

  // $('.delete-speed').click(function(){
  //   $(this).parents('li.speed').hide();
  //   return false;
  // });

  // $('.edit-captions').click(function(){
  //   var parentVid = $(this).parents('div');
  //   parentVid.siblings('div.caption-box').toggle();
  //   return false;
  // });

  // $('.close-box').click(function(){
  //   $(this).parents('.caption-box').hide();
  //   return false;
  // });

  // $('ul.dropdown').hide();
  // $('li.questions').click(function() {
  //   $('ul.dropdown').toggle();
  //   return false;
  // });

  // $('#mchoice').click(function(){
  //   $('div.used').append($('<div class="block question">').load("/widgets/multi-choice.html"));
  //   return false;
  // });

  // $('#text').click(function(){
  //   $('div.used').append($('<div class="block text">').load("/widgets/text.html"));
  //   return false;
  // });

  // $('#numerical').click(function(){
  //   $('div.used').append($('<div class="block question">').load("/widgets/text-question.html"));
  //   return false;
  // });

  // $('#equation').click(function(){
  //   $('div.used').append($('<div class="block latex">').load("/widgets/latex-equation.html"));
  //   return false;
  // });

  // $('#script').click(function(){
  //   $('div.used').append($('<div class="block code">').load("/widgets/script-widget.html"));
  //   return false;
  // });

  // $("#mark").markItUp(myWikiSettings);


  var heighest = 0;
  $('.cal ol > li').each(function(){
    heighest = ($(this).height() > heighest) ? $(this).height() : heighest;

  });

  $('.cal ol > li').css('height',heighest + 'px');

  $('.new-week').hide();
  $('.add-new-week').click(function() {
    $(this).hide();
    $('.new-week').show();
    return false;
  });

  $('.new-week .close').click( function(){
    $(this).parents('.new-week').hide();
    $('p.add-new-week').show();
    return false;
  });

  var windowHeight = $(window).resize().height();

  $('.sidebar').css('height', windowHeight);

  $('.edit-week').click( function() {
    $('body').addClass('content');
    $('body.content .cal').css('height', windowHeight);
    $('section.week-new').show();
    return false;
  });

  $('.cal ol li header h1 a').click( function() {
    $('body').addClass('content');
    $('body.content .cal').css('height', windowHeight);
    $('section.week-edit').show();
    return false;
  });


  $('.video-new a').click(function(){
      $('section.video-new').show();
      return false;
  });

  $('.video-edit a').click(function(){
      $('section.video-edit').show();
      return false;
  });

  $('.problem-new a').click(function(){
      $('section.problem-new').show();
      return false;
  });

  $('.problem-edit a').click(function(){
      $('section.problem-edit').show();
      return false;
  });
});

