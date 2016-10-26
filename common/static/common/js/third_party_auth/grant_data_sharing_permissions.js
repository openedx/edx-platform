(function() {
    'use strict';

    $(document).ready(function() {
        $('#data-sharing').submit(function(event) {
            var $dataSharingConsentCheckbox = $('#register-data_sharing_consent');
            var warningMessage = $dataSharingConsentCheckbox.data('warningMessage');

            if (!$dataSharingConsentCheckbox.is(':checked') && warningMessage) {
                // eslint-disable-next-line no-alert
                if (!window.confirm(warningMessage)) {
                    event.preventDefault();
                }
            }
        });
    });
}).call(this);
