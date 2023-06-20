/* global gettext */
import * as React from 'react';

import SkillAssessmentTable from "./SkillAssessmentTable";

export default class Main extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <SkillAssessmentTable {...this.props}/>
    );
  }
}
