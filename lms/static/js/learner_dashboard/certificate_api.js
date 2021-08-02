$(document).ready(() => {
  'use strict';

  const requestButtons = document.getElementsByClassName('request-cert');

  for (let i = 0; i < requestButtons.length; i++) {
    requestButtons[i].addEventListener('click', (event) => {
      event.preventDefault();
      const endpoint = !!event.target.dataset.endpoint && event.target.dataset.endpoint;
      $.ajax({
        type: 'POST',
        url: endpoint,
        dataType: 'text',
        success: () => {
          location.reload();
        },
        error: (jqXHR, textStatus, errorThrown) => {
          location.reload();
        },
      });
    });
  }
});
