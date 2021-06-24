/* global gettext */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { InputText } from '@edx/paragon';
import actions from '../data/actions/actions';

export const CourseMaxTeamSize = ({ courseMaxTeamSize, onChange }) => (
  <section className="group-settings teams-max-size">
    <header>
      <h2 className="title-2">{gettext('Course Max Team Size')}</h2>
      <span className="tip">{gettext('Placeholder tip for Max Size')}</span>
    </header>
    <ol className="list-input">
      <li className="field text" id="field-course-max-team-size">
        <InputText
          label="Course Max Team Size"
          name="courseMaxTeamSize"
          value={courseMaxTeamSize}
          onChange={onChange}
        />
      </li>
    </ol>
  </section>
);

CourseMaxTeamSize.defaultProps = {
  courseMaxTeamSize: 0,
};

CourseMaxTeamSize.propTypes = {
  courseMaxTeamSize: PropTypes.number,
  onChange: PropTypes.func.isRequired,
};

const mapStateToProps = state => ({
  courseMaxTeamSize: state.courseMaxTeamSize,
});

const mapDispatchToProps = {
  onChange: actions.updateCourseMaxTeamSize,
};

export default connect(mapStateToProps, mapDispatchToProps)(CourseMaxTeamSize);

