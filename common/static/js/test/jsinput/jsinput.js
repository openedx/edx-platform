describe("jsinput test", function () {

  beforeEach(function () {
    $('#fixture').remove();
    $.ajax({
      async: false,
      url: 'mainfixture.html',
      success: function(data) {
        $('body').append($(data));
      }
    });
  });

  it("")
}
        )
