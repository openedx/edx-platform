$(document).ready(function() {

    function hideEmail(){
        $("label[for='id_org_admin_email']").hide();
        $("#id_org_admin_email").hide();
    }

    function showEmail(){
        $("label[for='id_org_admin_email']").show();
        $("#id_org_admin_email").show();
    }

    function hidePOC(){
        $("label[for='id_is_poc_0']").hide();
        $("#id_is_poc").hide();
    }

    function showPOC(){
        $("label[for='id_is_poc_0']").show();
        $("#id_is_poc").show();
    }

    function hideOrShowOrgEmailField(){

            reg_update_poc_radio = $('input[name=is_poc]:checked').val();

            if (reg_update_poc_radio == '1'){
                hideEmail();
            }
            if (reg_update_poc_radio == '0') {
                showEmail();
            }
    }

    hideOrShowOrgEmailField();

    $("#id_is_poc").change(hideOrShowOrgEmailField);

    var org_url = $('#reg-update-form').data('org-url');

    $.ajax({
            url: org_url, success: function (result) {
                full_result = result
                orgs = Object.keys(result)
                $("#id_organization_name").autocomplete({
                    source: orgs, minLength: 3
                });
            }
        });

    function revertRadioButtonToNo() {
                $('[name="is_poc"][value="0"]').prop('checked', true);
            }

    $("#id_organization_name").focusout(function () {

                if ($("#id_organization_name").val()) {
                    if (orgs.includes($("#id_organization_name").val()) && full_result[$("#id_organization_name").val()]) {
                        hideEmail();
                        hidePOC();
                        revertRadioButtonToNo()
                    } else {
                        showPOC();
                        hideOrShowOrgEmailField();
                    }
                } else {
                    hideEmail();
                    hidePOC();
                    revertRadioButtonToNo()
                }
            });

});
