var onVideoFail = function(e) {
  if(e == 'NO_DEVICES_FOUND') {
      $('#no-webcam').show();
      $('#face_capture_button').hide();
      $('#photo_id_capture_button').hide();
  }
  else {
    console.log('Failed to get camera access!', e);
  }
};

// Returns true if we are capable of video capture (regardless of whether the
// user has given permission).
function initVideoCapture() {
  window.URL = window.URL || window.webkitURL;
  navigator.getUserMedia  = navigator.getUserMedia || navigator.webkitGetUserMedia ||
                            navigator.mozGetUserMedia || navigator.msGetUserMedia;
  return !(navigator.getUserMedia == undefined);
}

var submitReverificationPhotos = function() {
    // add photos to the form
    $('<input>').attr({
        type: 'hidden',
        name: 'face_image',
        value: $("#face_image")[0].src,
    }).appendTo("#reverify_form");
    $('<input>').attr({
        type: 'hidden',
        name: 'photo_id_image',
        value: $("#photo_id_image")[0].src,
    }).appendTo("#reverify_form");

    $("#reverify_form").submit();

}

var submitMidcourseReverificationPhotos = function() {
  $('<input>').attr({
      type: 'hidden',
      name: 'face_image',
      value: $("#face_image")[0].src,
  }).appendTo("#reverify_form");
  $("#reverify_form").submit();
}

function showSubmissionError() {
    if (xhr.status == 400) {
        $('#order-error .copy p').html(xhr.responseText);
    }
    $('#order-error').show();
    $("html, body").animate({ scrollTop: 0 });
}

function submitForm(data) {
    for (prop in data) {
    $('<input>').attr({
        type: 'hidden',
        name: prop,
        value: data[prop]
    }).appendTo('#pay_form');
    }
    $("#pay_form").submit();
}

function refereshPageMessage() {
    $('#photo-error').show();
    $("html, body").animate({ scrollTop: 0 });
}

var submitToPaymentProcessing = function() {
  var contribution_input = $("input[name='contribution']:checked")
  var contribution = 0;
  if(contribution_input.attr('id') == 'contribution-other') {
      contribution = $("input[name='contribution-other-amt']").val();
  }
  else {
      contribution = contribution_input.val();
  }
  var course_id = $("input[name='course_id']").val();
  $.ajax({
    url: "/verify_student/create_order",
    type: 'POST',
    data: {
      "course_id" : course_id,
      "contribution": contribution,
      "face_image" : $("#face_image")[0].src,
      "photo_id_image" : $("#photo_id_image")[0].src
    },
    success:function(data) {
      if (data.success) {
        submitForm(data);
      } else {
        refereshPageMessage();
      }
    },
    error:function(xhr,status,error) {
      showSubmissionError()
    }
  });
}

function doResetButton(resetButton, captureButton, approveButton, nextButtonNav, nextLink) {
  approveButton.removeClass('approved');
  nextButtonNav.addClass('is-not-ready');
  nextLink.attr('href', "#");

  captureButton.show();
  resetButton.hide();
  approveButton.hide();
}

function doApproveButton(approveButton, nextButtonNav, nextLink) {
  nextButtonNav.removeClass('is-not-ready');
  approveButton.addClass('approved');
  nextLink.attr('href', "#next");
}

function doSnapshotButton(captureButton, resetButton, approveButton) {
  captureButton.hide();
  resetButton.show();
  approveButton.show();
}

function submitNameChange(event) {
  event.preventDefault();
  $("#lean_overlay").fadeOut(200);
  $("#edit-name").css({ 'display' : 'none' });
  var full_name = $('input[name="name"]').val();
  var xhr = $.post(
    "/change_name",
    {
      "new_name" : full_name,
      "rationale": "Want to match ID for ID Verified Certificates."
    },
    function(data) {
        $('#full-name').html(full_name);
    }
  )
  .fail(function(jqXhr,text_status, error_thrown) {
    $('.message-copy').html(jqXhr.responseText);
  });

}

function initSnapshotHandler(names, hasHtml5CameraSupport) {
  var name = names.pop();
  if (name == undefined) {
    return;
  }

  var video = $('#' + name + '_video');
  var canvas = $('#' + name + '_canvas');
  var image = $('#' + name + "_image");
  var captureButton = $("#" + name + "_capture_button");
  var resetButton = $("#" + name + "_reset_button");
  var approveButton = $("#" + name + "_approve_button");
  var nextButtonNav = $("#" + name + "_next_button_nav");
  var nextLink = $("#" + name + "_next_link");
  var flashCapture = $("#" + name + "_flash");

  var ctx = null;
  if (hasHtml5CameraSupport) {
    ctx = canvas[0].getContext('2d');
  }

  var localMediaStream = null;

  function snapshot(event) {
    if (hasHtml5CameraSupport) {
      if (localMediaStream) {
        ctx.drawImage(video[0], 0, 0);
        image[0].src = canvas[0].toDataURL('image/png');
      }
      else {
        return false;
      }
      video[0].pause();
    }
    else {
      if (flashCapture[0].cameraAuthorized()) {
        image[0].src = flashCapture[0].snap();
      }
      else {
        return false;
      }
    }

    doSnapshotButton(captureButton, resetButton, approveButton);
    return false;
  }

  function reset() {
    image[0].src = "";

    if (hasHtml5CameraSupport) {
      video[0].play();
    }
    else {
      flashCapture[0].reset();
    }

    doResetButton(resetButton, captureButton, approveButton, nextButtonNav, nextLink);
    return false;
  }

  function approve() {
    doApproveButton(approveButton, nextButtonNav, nextLink)
    return false;
  }

  // Initialize state for this picture taker
  captureButton.show();
  resetButton.hide();
  approveButton.hide();
  nextButtonNav.addClass('is-not-ready');
  nextLink.attr('href', "#");

  // Connect event handlers...
  video.click(snapshot);
  captureButton.click(snapshot);
  resetButton.click(reset);
  approveButton.click(approve);

  // If it's flash-based, we can just immediate initialize the next one.
  // If it's HTML5 based, we have to do it in the callback from getUserMedia
  // so that Firefox doesn't eat the second request.
  if (hasHtml5CameraSupport) {
    navigator.getUserMedia({video: true}, function(stream) {
      video[0].src = window.URL.createObjectURL(stream);
      localMediaStream = stream;

      // We do this in a recursive call on success because Firefox seems to
      // simply eat the request if you stack up two on top of each other before
      // the user has a chance to approve the first one.
      //
      // This appears to be necessary for older versions of Firefox (before 28).
      // For more info, see https://github.com/edx/edx-platform/pull/3053
      initSnapshotHandler(names, hasHtml5CameraSupport);
    }, onVideoFail);
  }
  else {
    initSnapshotHandler(names, hasHtml5CameraSupport);
  }

}

function browserHasFlash() {
  var hasFlash = false;
  try {
      var fo = new ActiveXObject('ShockwaveFlash.ShockwaveFlash');
      if(fo) hasFlash = true;
  } catch(e) {
      if(navigator.mimeTypes["application/x-shockwave-flash"] != undefined) hasFlash = true;
  }
  return hasFlash;
}

function objectTagForFlashCamera(name) {
  // detect whether or not flash is available
  if(browserHasFlash()) {
      // I manually update this to have ?v={2,3,4, etc} to avoid caching of flash
      // objects on local dev.
      return '<object type="application/x-shockwave-flash" id="' +
             name + '" name="' + name + '" data=' +
             '"/static/js/verify_student/CameraCapture.swf?v=3"' +
              'width="500" height="375"><param name="quality" ' +
              'value="high"><param name="allowscriptaccess" ' +
              'value="sameDomain"></object>';
  }
  else {
      // display a message informing the user to install flash
      $('#no-flash').show();
  }
}

function waitForFlashLoad(func, flash_object) {
    if(!flash_object.hasOwnProperty('percentLoaded') || flash_object.percentLoaded() < 100){
        setTimeout(function() {
            waitForFlashLoad(func, flash_object);
        },
        50);
    }
    else {
        func(flash_object);
    }
}

$(document).ready(function() {
  $(".carousel-nav").addClass('sr');
  $("#pay_button").click(function(){
      analytics.pageview("Payment Form");
      submitToPaymentProcessing();
  });

  $("#reverify_button").click(function() {
      submitReverificationPhotos();
  });

  $("#midcourse_reverify_button").click(function() {
      submitMidcourseReverificationPhotos();
  });

  // prevent browsers from keeping this button checked
  $("#confirm_pics_good").prop("checked", false)
  $("#confirm_pics_good").change(function() {
      $("#pay_button").toggleClass('disabled');
      $("#reverify_button").toggleClass('disabled');
      $("#midcourse_reverify_button").toggleClass('disabled');
  });


  // add in handlers to add/remove the correct classes to the body
  // when moving between steps
  $('#face_next_link').click(function(){
      analytics.pageview("Capture ID Photo");
      $('#photo-error').hide();
      $('body').addClass('step-photos-id').removeClass('step-photos-cam')
  })

  $('#photo_id_next_link').click(function(){
      analytics.pageview("Review Photos");
      $('body').addClass('step-review').removeClass('step-photos-id')
  })

  // set up edit information dialog
  $('#edit-name div[role="alert"]').hide();
  $('#edit-name .action-save').click(submitNameChange);

  var hasHtml5CameraSupport = initVideoCapture();

  // If HTML5 WebRTC capture is not supported, we initialize jpegcam
  if (!hasHtml5CameraSupport) {
    $("#face_capture_div").html(objectTagForFlashCamera("face_flash"));
    $("#photo_id_capture_div").html(objectTagForFlashCamera("photo_id_flash"));
    // wait for the flash object to be loaded and then check for a camera
    if(browserHasFlash()) {
        waitForFlashLoad(function(flash_object) {
            if(!flash_object.hasOwnProperty('hasCamera')){
                onVideoFail('NO_DEVICES_FOUND');
            }
        }, $('#face_flash')[0]);
    }
  }

  analytics.pageview("Capture Face Photo");
  initSnapshotHandler(["photo_id", "face"], hasHtml5CameraSupport);

  $('a[rel="external"]').attr({
    title: gettext('This link will open in a new browser window/tab'),
    target: '_blank'
  });

});
