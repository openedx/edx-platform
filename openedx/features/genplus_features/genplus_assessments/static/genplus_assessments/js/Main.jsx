/* global gettext */
import * as React from 'react';

import SkillAssessmentTable from "./SkillAssessmentTable";

export default class Main extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div>
        <header className="mast">
          <h1 className="page-header">{"Skill Assessment Admin"}</h1>
        </header>
        <SkillAssessmentTable {...this.props}/>
      </div>
    );
  }
}
