$(document).ready(function() {
    var orgs;
    $.ajax({
            url: "onboarding_survey/get_user_organizations", success: function (result) {
                full_result = result
                orgs = Object.keys(result)
            }
        });

    var waitForEl = function(selector, callback) {
      if (jQuery(selector).length) {
        callback();
      } else {
        setTimeout(function() {
          waitForEl(selector, callback);
        }, 100);
      }
    };

    waitForEl("#register-is_poc", function() {
        $('#register-is_poc').hide()
            $('.form-field.email-org_admin_email').hide();

            function hide_or_show_org_email_field(){

                    is_poc_value = $('#register-is_poc').find(":selected").val();

                    if (is_poc_value == '1'){
                        $('.form-field.email-org_admin_email').hide();
                    }
                    if (is_poc_value == '0') {
                        $('.form-field.email-org_admin_email').show();
                        $("#register-org_admin_email").val("")
                    }
            }

            $("#register-is_poc").change(hide_or_show_org_email_field);

            $("#register-organization_name").autocomplete({
                source: orgs, minLength: 3
            });

            $("#register-is_poc option").each(function() {
              //get values of all option
              var val = $(this).val();
              var text = $(this).text();

              //do magic create boxes like checkbox
              if(val == '1'){
                  $(".select-is_poc").append('<div class="selectbox" data-value="' + val + '"> ' +  text + '</div>');
              }
              else {
                  $(".select-is_poc").append('<div class="selectbox active" data-value="' + val + '"> ' +  text + '</div>');
              }


            });
            // Remove empty selectbox
            $('.selectbox[data-value=""]').remove();
            $('.selectbox:nth-child(2)').addClass('active');

            // Change select box on click
            $(".selectbox").click(function(e) {
              //remove selected from others
              $(".selectbox").removeClass("active");
              //do active to selected
              $(this).addClass("active");
              //get value
              var optVal = $(this).data("value");
                $("#register-is_poc").val(optVal + "");

                if (optVal == 1) {
                    $('.form-field.email-org_admin_email').hide();
                }
                else {
                    $('.form-field.email-org_admin_email').show();
                    $("#register-org_admin_email").val("")
                }
            });

            function revertRadioButtonToNo() {
                var optionValue = $("#register-is_poc").val();
                if (optionValue == '1'){
                    $(".selectbox").removeClass("active");
                    $(".selectbox[data-value='" + '0' + "']").addClass("active");
                    $('#register-is_poc').val('0');
                }
            }
            // Change select box on dropdown change
            $("#register-is_poc").change(function() {
              var optVal = $(this).val();
              $(".selectbox").removeClass("active");
              $(".selectbox[data-value='" + optVal + "']").addClass("active");
            });

            // Passwords should match.
            $('#register-password, #register-confirm_password').on('keyup', function () {

                if ($('#register-password').val() == $('#register-confirm_password').val()) {
                    $('.note').html('* Required field');
                    $('.action.action-primary.action-update.js-register.register-button').prop('disabled', false);
                } else {
                    $('.note').html('* Required field, Password does not match.');
                    $('.action.action-primary.action-update.js-register.register-button').prop('disabled', true);
                }
            });

            $("#register-organization_name").focusout(function () {

                if ($("#register-organization_name").val()) {
                    if (orgs.includes($("#register-organization_name").val()) && full_result[$("#register-organization_name").val()]) {
                        $(".form-field.select-is_poc").hide();
                        $(".form-field.email-org_admin_email").hide();
                        revertRadioButtonToNo()
                    } else {
                        $(".form-field.select-is_poc").show();
                        hide_or_show_org_email_field()
                    }
                } else {
                    $(".form-field.select-is_poc").hide();
                    $(".form-field.email-org_admin_email").hide();
                    revertRadioButtonToNo()

                }
            });
    });







});