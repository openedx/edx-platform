jasmine.stubRequests = function () {
  spyOn($, 'ajax').andCallFake(function(settings){
    var match = settings.url.match(/\/transcripts\/(.+)$/);
    if (match) {
      var resp = {
          status: 'Success',
          subs: 'video_id'
        },
        action = match[1],
        dfd = jQuery.Deferred();

        switch (action) {
          case 'error':
            dfd.reject();
            break;
          case 'errorStatus':
            var r = $.extend(true, resp, { status: 'Error' });
            dfd.resolve(r);
            break;
          default:
            dfd.resolve(resp);
            break;
        }

      return dfd;

    } else {
      throw "External request attempted for "+ settings.url +", which is not defined.";
    }
  });
};
