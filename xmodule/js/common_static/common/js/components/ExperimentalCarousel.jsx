import React from 'react';
import Slider from 'react-slick';
import classNames from 'classnames';
import PropTypes from 'prop-types';

/** Experimental Carousel as part of https://openedx.atlassian.net/browse/LEARNER-3583 **/

function NextArrow(props) {
  const {currentSlide, slideCount, onClick, displayedSlides} = props;
  const showArrow = slideCount - currentSlide > displayedSlides;
  const opts = {
    className: classNames('js-carousel-nav', 'carousel-arrow', 'next', 'btn btn-secondary', {'active': showArrow}),
    onClick
  };

  if (!showArrow) {
    opts.disabled = 'disabled';
  }

  return (
    <button {...opts}>
        <span>Next </span>
        <span className="icon fa fa-chevron-right" aria-hidden="true"></span>
        <span className="sr">{ 'Scroll carousel forwards' }</span>
    </button>
  );
}

function PrevArrow(props) {
  const {currentSlide, onClick} = props;
  const showArrow = currentSlide > 0;
  const opts = {
    className: classNames('js-carousel-nav', 'carousel-arrow', 'prev', 'btn btn-secondary', {'active': showArrow}),
    onClick
  };

  if (!showArrow) {
    opts.disabled = 'disabled';
  }

    return (
        <button {...opts} >
          <span className="icon fa fa-chevron-left" aria-hidden="true"></span>
          <span> Prev</span>
          <span className="sr">{ 'Scroll carousel backwards' }</span>
        </button>
    );
}

export default class ExperimentalCarousel extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      // Default to undefined to not focus on page load
      activeIndex: undefined,
    };

    this.carousels = [];

    this.afterChange = this.afterChange.bind(this);
    this.getCarouselContent = this.getCarouselContent.bind(this);
  }

  afterChange(activeIndex) {
    this.setState({ activeIndex });
  }

  componentDidUpdate() {
    const { activeIndex } = this.state;

    if (!isNaN(activeIndex)) {
      this.carousels[activeIndex].focus();
    }
  }

  getCarouselContent() {
    return this.props.slides.map((slide, i) => {
      const firstIndex = this.state.activeIndex || 0;
      const lastIndex = firstIndex + this.props.slides.length;
      const tabIndex = (firstIndex <= i && i < lastIndex) ? undefined : '-1';
      const carouselLinkProps = {
        ref: (item) => {
          this.carousels[i] = item;
        },
        tabIndex: tabIndex,
        className: 'carousel-item'
      }

      return (
          <div {...carouselLinkProps}>
            { slide }
          </div>
        );
    });
  }

  render() {
    const carouselSettings = {
      accessibility: true,
      dots: true,
      infinite: false,
      speed: 500,
      className: 'carousel-wrapper',
      nextArrow: <NextArrow displayedSlides={1} />,
      prevArrow: <PrevArrow />,
      afterChange: this.afterChange,
      slidesToShow: 1,
      slidesToScroll: 1,
      initialSlide: 0,
    };

    return (
      <Slider {...carouselSettings} >
          {this.getCarouselContent()}
      </Slider>
    );
  }
}

ExperimentalCarousel.propTypes = {
  slides: PropTypes.array.isRequired
};