function initializeCourseSlider() {
    'use strict';
    var isMobileResolution = $(window).width() <= 767,
        sliderExists = $('.course-slider-xs').hasClass('slick-slider');
    $('.course-card').toggleClass('slidable', isMobileResolution);
    if (isMobileResolution) {    // Second condition will avoid the multiple calls from resize
        $('.copy-meta-mobile').show();
        $('.copy-meta').hide();
        if (!sliderExists) {
            $('.course-slider-xs').slick({
                arrows: false,
                centerMode: true,
                centerPadding: '40px',
                slidesToShow: 1
            });
        }
    } else {
        $('.copy-meta').show();
        $('.copy-meta-mobile').hide();
        if (sliderExists) {
            $('.course-slider-xs').slick('unslick');
            $('.course-slider-xs').html();
            $('.slick-arrow, .pageInfo').hide();
        }
    }
}

function paginate(page, size, total) {
    'use strict';
    var start = size * page,
        end = (start + size - 1) >= total ? total - 1 : (start + size - 1);
    $('.profile-item-desktop').each(function(index, item) {
        if (index >= start && index <= end) {
            $(item).css('display', 'block');
        } else {
            $(item).css('display', 'none');
        }
    });
    $('.pagination-start').text(start + 1);
    $('.pagination-end').text(end + 1);
}

$.fn.getFocusableChildren = function() {
    'use strict';
    return $(this)
        /* eslint max-len: 0 */
        .find('a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object:not([disabled]), embed, *[tabindex], *[contenteditable]')
        .filter(':visible');
};

$(document).ready(function() {
    'use strict';
    // Create MutationObserver which prevents the body of
    // the page from scrolling when a modal window is displayed
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if ($(mutation.target).css('display') === 'block') {
                $('body').css('overflow', 'hidden');
            } else {
                $('body').css('overflow', 'auto');
            }
        });
    });

    // Custom function showing current slide
    var $status = $('.pagingInfo');
    var $slickElement = $('.course-slider-xs');

    // Instructor pagination
    var page = 0,
        size = 4,
        total = parseInt($('.instructor-size').text(), 10),
        maxPages = Math.ceil(total / size) - 1;

    paginate(page, size, total);

    initializeCourseSlider();

    // In order to restrict focus, we added two pseudo <a> elements, one before the instructor modal and one after.
    // When reaching the first <a>, we focus the last element in the dialog.
    // If there is no focusable element, we focus the close button.
    // When focusing the last <a>, we focus the first control in the dialog.
    $('.focusKeeper:even').on('focus', function(event) {
        event.preventDefault();
        if ($(this).parent().find('.modal-body')
                            .getFocusableChildren().length) {
            $(this).parent().find('.modal-body')
                            .getFocusableChildren()
                            .filter(':last')
                            .focus();
        } else {
            $(this).parent().find('.modal_close a')
                            .focus();
        }
    });

    $('.focusKeeper:odd').on('focus', function(event) {
        event.preventDefault();
        $(this).parent().find('.modal_close a')
                        .focus();
    });

    $(window).resize(function() {
        initializeCourseSlider();
    });

    // Initialize instructor bio modals
    $('.instructor-image, .instructor-label').leanModal({closeButton: '.modal_close', top: '10%'});

    $('.modal').each(function(index, element) {
        observer.observe(element, {attributes: true, attributeFilter: ['style']});
    });

    $slickElement.on('init reInit afterChange', function(event, slick, currentSlide) {
        // currentSlide is undefined on init -- set it to 0 in this case (currentSlide is 0 based)
        var i = currentSlide || 1;
        $status.text(i + ' of ' + slick.slideCount);
    });

    // Initialize FAQ
    $('ul.faq-links-list li.item').click(function() {
        if ($(this).find('.answer').hasClass('hidden')) {
            $(this).find('.answer').removeClass('hidden');
            $(this).addClass('expanded');
        } else {
            $(this).find('.answer').addClass('hidden');
            $(this).removeClass('expanded');
        }
    });

    if (page < maxPages) {
        $('#pagination-next').addClass('active');
        $('#pagination-next > span.sr').attr('aria-hidden', 'false');
    }

    $('#pagination-next').click(function() {
        if (page === maxPages) {
            return false;
        }
        if (page + 1 === maxPages) {
            $(this).removeClass('active');
            $(this).children('span.sr').attr('aria-hidden', 'true');
        }
        page = page + 1;
        paginate(page, size, total);
        $('#pagination-previous').addClass('active');
        $('#pagination-previous > span.sr').attr('aria-hidden', 'false');
        return false;
    });

    $('#pagination-previous').click(function() {
        if (page === 0) {
            return false;
        }
        if (page - 1 === 0) {
            $(this).removeClass('active');
            $(this).children('span.sr').attr('aria-hidden', 'true');
        }
        page = page - 1;
        paginate(page, size, total);
        $('#pagination-next').addClass('active');
        $('#pagination-next > span.sr').attr('aria-hidden', 'false');
        return false;
    });

    $('#accordion-group').accordion({
        header: '> .accordion-item > .accordion-head',
        collapsible: true,
        active: false,
        heightStyle: 'content'
    });
});
