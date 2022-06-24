/* global gettext */
import React from 'react';

const RecommendationsPanel = (props) => {
  return (
    <div className="p-4 panel-background">
      <div className="recommend-heading mb-4">{gettext('Recommendations for you')}</div>
      <div className="course-card box-shadow-down-1 bg-white mb-3">
        <div className="box-shadow-down-1 image-box">
          <img
            className="panel-course-img"
            src="https://source.unsplash.com/lQGJCMY5qcM"
            alt="course image"
          />
        </div>
        <div className="course-title pl-3">The Chemistry of Life</div>
      </div>
      <div className="course-card box-shadow-down-1 bg-white mb-3">
        <div className="box-shadow-down-1 image-box">
          <img
            className="panel-course-img"
            src="https://source.unsplash.com/KltoLK6Mk-g"
            alt="course image"
          />
        </div>
        <div className="course-title pl-3">Drug Discovery & Medicinal Chemistry</div>
      </div>
      <div className="course-card box-shadow-down-1 bg-white mb-3">
        <div className="box-shadow-down-1 image-box">
          <img
            className="panel-course-img"
            src="https://source.unsplash.com/_BJVJ4WcV1M"
            alt="course image"
          />
        </div>
        <div className="course-title pl-3">From Fossil Resources to Biomass: A Chemistry Perspective</div>
      </div>
      <div className="course-card box-shadow-down-1 bg-white mb-3">
        <div className="box-shadow-down-1 image-box">
          <img
            className="panel-course-img"
            src="https://source.unsplash.com/NKhckz9B78c"
            alt="course image"
          />
        </div>
        <div className="course-title pl-3">Digital Biomaterials</div>
      </div>
      <div className="course-card box-shadow-down-1 bg-white mb-3">
        <div className="box-shadow-down-1 image-box">
          <img
            className="panel-course-img"
            src="https://source.unsplash.com/x649mR6yBIs"
            alt="course image"
          />
        </div>
        <div className="course-title pl-3">Basic Steps in Magnetic Resonance</div>
      </div>
      <div className="d-flex justify-content-center">
        <a href={props.exploreCoursesUrl}
           className="panel-explore-courses justify-content-center align-items-center">
          {gettext('Explore courses')}
          <span className="icon fa fa-search search-icon" aria-hidden="true"/>
        </a>
      </div>
    </div>
  );
}

export {RecommendationsPanel};
