var onVideoFail = function(e) {
  console.log('Failed to get camera access!', e);
};

// Returns true if we are capable of video capture (regardless of whether the
// user has given permission).
function initVideoCapture() {
  window.URL = window.URL || window.webkitURL;
  navigator.getUserMedia  = navigator.getUserMedia || navigator.webkitGetUserMedia ||
                            navigator.mozGetUserMedia || navigator.msGetUserMedia;
  return !(navigator.getUserMedia == undefined);
}

var submitToPaymentProcessing = function() {
  var contribution_input = $("input[name='contribution']:checked")
  var contribution = 0;
  if(contribution_input.attr('id') == 'contribution-other')
  {
      contribution = $("input[name='contribution-other-amt']").val();
  }
  else
  {
      contribution = contribution_input.val();
  }
  var course_id = $("input[name='course_id']").val();
  var xhr = $.post(
    "/verify_student/create_order",
    {
      "course_id" : course_id,
      "contribution": contribution
    },
    function(data) {
      for (prop in data) {
        $('<input>').attr({
            type: 'hidden',
            name: prop,
            value: data[prop]
        }).appendTo('#pay_form');
      }
    }
  )
  .done(function(data) {
    $("#pay_form").submit();
  })
  .fail(function(jqXhr,text_status, error_thrown) {
    alert(jqXhr.responseText);
  });
}

function doResetButton(resetButton, captureButton, approveButton, nextButton) {
  approveButton.removeClass('approved');
  nextButton.addClass('disabled');

  captureButton.show();
  resetButton.hide();
  approveButton.hide();
}

function doApproveButton(approveButton, nextButton) {
  approveButton.addClass('approved');
  nextButton.removeClass('disabled');
}

function doSnapshotButton(captureButton, resetButton, approveButton) {
  captureButton.hide();
  resetButton.show();
  approveButton.show();
}


function submitNameChange(event) {
  event.preventDefault();
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
  var nextButton = $("#" + name + "_next_button");
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
      image[0].src = flashCapture[0].snap();
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

    doResetButton(resetButton, captureButton, approveButton, nextButton);
    return false;
  }

  function approve() {
    doApproveButton(approveButton, nextButton)
    return false;
  }

  // Initialize state for this picture taker
  captureButton.show();
  resetButton.hide();
  approveButton.hide();
  nextButton.addClass('disabled');

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
      initSnapshotHandler(names, hasHtml5CameraSupport);
    }, onVideoFail);
  }
  else {
    initSnapshotHandler(names, hasHtml5CameraSupport);
  }

}

function objectTagForFlashCamera(name) {
  return '<object type="application/x-shockwave-flash" id="' +
         name + '" name="' + name + '" data=' +
         '"/static/js/verify_student/CameraCapture.swf"' +
          'width="500" height="375"><param name="quality" ' +
          'value="high"><param name="allowscriptaccess" ' +
          'value="sameDomain"></object>';
}

$(document).ready(function() {
  $(".carousel-nav").addClass('sr');
  $("#pay_button").click(submitToPaymentProcessing);
  // prevent browsers from keeping this button checked
  $("#confirm_pics_good").prop("checked", false)
  $("#confirm_pics_good").change(function() {
      $("#pay_button").toggleClass('disabled');
  });


  // add in handlers to add/remove the correct classes to the body
  // when moving between steps
  $('#face_next_button').click(function(){
      $('body').addClass('step-photos-id').removeClass('step-photos-cam')
  })

  $('#photo_id_next_button').click(function(){
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
  }

  initSnapshotHandler(["photo_id", "face"], hasHtml5CameraSupport);

});
