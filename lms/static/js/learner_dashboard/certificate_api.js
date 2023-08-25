// eslint-disable-next-line no-undef
$(document).ready(() => {
    'use strict';

    const requestButtons = document.getElementsByClassName('request-cert');

    for (let i = 0; i < requestButtons.length; i++) {
        // eslint-disable-next-line no-loop-func
        requestButtons[i].addEventListener('click', (event) => {
            event.preventDefault();
            const endpoint = !!event.target.dataset.endpoint && event.target.dataset.endpoint;
            // eslint-disable-next-line no-undef
            $.ajax({
                type: 'POST',
                url: endpoint,
                dataType: 'text',
                success: () => {
                    // eslint-disable-next-line no-restricted-globals
                    location.reload();
                },
                // eslint-disable-next-line no-unused-vars
                error: (jqXHR, textStatus, errorThrown) => {
                    // eslint-disable-next-line no-restricted-globals
                    location.reload();
                },
            });
        });
    }
});
