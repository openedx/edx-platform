var setupFullScreenModal = function() {
    // Setup full screen image modal.
    // Executed from HTMLModule in display.js.
    $('a.modal-content').each(function() {
        var smallImageObject = $(this).children();
        var largeImageSRC = $(this).attr('href');

        // if contents of zoomable link is image and large image link exists: setup modal
        if (smallImageObject.is('img') && largeImageSRC) {
            var data = {
                smallHTML: $(this).html(),
                largeALT: smallImageObject.attr('alt'),
                largeSRC: largeImageSRC
            };
            var html = _.template($('#image-modal-tpl').text())(data);
            // xss-lint: disable=javascript-jquery-insertion
            $(this).replaceWith(html);
        }
    });
    $('.wrapper-modal-image .image-wrapper img').each(function() {
        var draggie = new Draggabilly(this, {containment: true});
        draggie.disable();
        $(this).closest('.image-modal').data('draggie', draggie);
    });

    // Opening and closing image modal on clicks
    $('.wrapper-modal-image .image-link').click(function() {
        $(this).siblings('.image-modal').addClass('image-is-fit-to-screen');
        $('body').css('overflow', 'hidden');
    });

    // variable to detect when modal is being "hovered".
    // Done this way as jquery doesn't support the :hover psudo-selector as expected.
    var imageModalImageHover = false;
    $('.wrapper-modal-image .image-content img, .wrapper-modal-image .image-content .image-controls').hover(function() {
        imageModalImageHover = true;
    }, function() {
        imageModalImageHover = false;
    });

    // prevent image control button links from scrolling
    $('.modal-ui-icon').click(function(event) {
        event.preventDefault();
    });

    // Define function to close modal
    function closeModal(imageModal) {
        imageModal.removeClass('image-is-fit-to-screen').removeClass('image-is-zoomed');
        $('.wrapper-modal-image .image-content .image-controls .modal-ui-icon.action-zoom-in').removeClass('is-disabled').attr('aria-disabled', false);
        $('.wrapper-modal-image .image-content .image-controls .modal-ui-icon.action-zoom-out').addClass('is-disabled').attr('aria-disabled', true);
        var currentDraggie = imageModal.data('draggie');
        currentDraggie.disable();
        $('body').css('overflow', 'auto');
    }

    // Click outside of modal to close it.
    $('.wrapper-modal-image .image-modal').click(function() {
        if (!imageModalImageHover) {
            closeModal($(this));
        }
    });

    // Click close icon to close modal.
    $('.wrapper-modal-image .image-content .action-remove').click(function() {
        closeModal($(this).closest('.image-modal'));
    });

    // zooming image in modal and allow it to be dragged
    // Make sure it always starts zero position for below calcs to work
    $('.wrapper-modal-image .image-content .image-controls .modal-ui-icon').click(function() {
        if (!$(this).hasClass('is-disabled')) {
            var mask = $(this).closest('.image-content');

            var imageModal = $(this).closest('.image-modal');
            var img = imageModal.find('img');
            var currentDraggie = imageModal.data('draggie');

            if ($(this).hasClass('action-zoom-in')) {
                imageModal.removeClass('image-is-fit-to-screen').addClass('image-is-zoomed');

                var imgWidth = img.width();
                var imgHeight = img.height();

                var imgContainerOffsetLeft = imgWidth - mask.width();
                var imgContainerOffsetTop = imgHeight - mask.height();
                var imgContainerWidth = imgWidth + imgContainerOffsetLeft;
                var imgContainerHeight = imgHeight + imgContainerOffsetTop;

                // Set the width and height of the image's container so that the dimensions are equal to the image dimensions + view area dimensions to limit dragging
                // Set image container top and left to center image at load.
                img.parent().css({
                    left: -imgContainerOffsetLeft,
                    top: -imgContainerOffsetTop,
                    width: imgContainerWidth,
                    height: imgContainerHeight
                });
                img.css({top: imgContainerOffsetTop / 2, left: imgContainerOffsetLeft / 2});

                currentDraggie.enable();
            } else if ($(this).hasClass('action-zoom-out')) {
                imageModal.removeClass('image-is-zoomed').addClass('image-is-fit-to-screen');

                currentDraggie.disable();
            }

            $('.wrapper-modal-image .image-content .image-controls .modal-ui-icon').toggleClass('is-disabled').attr('aria-disabled', $(this).hasClass('is-disabled'));
        }
    });
};
