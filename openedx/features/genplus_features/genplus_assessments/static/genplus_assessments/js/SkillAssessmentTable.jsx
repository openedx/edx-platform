import React from 'react';
import { connect } from 'react-redux';
import * as PropTypes from 'prop-types';
import { selectBlock } from 'BlockBrowser/data/actions/courseBlocks';
import {
    fetchCourseBlocks,
    fetchProgramSkillAssessmentMapping,
    addProgramSkillAssessmentMapping,
    updateMappingData
} from './data/actions/index';
import SkillAssessmentTableRows from "./SkillAssessmentTableRows"

class SkillAssessmentTable extends React.Component {
    constructor(props) {
      super(props);
      this.addTableRows = this.addTableRows.bind(this);
      this.deleteTableRows = this.deleteTableRows.bind(this);
      this.handleSelectIntro = this.handleSelectIntro.bind(this);
      this.handleSelectOutro = this.handleSelectOutro.bind(this);
      this.handleIntroToggleDropdown = this.handleIntroToggleDropdown.bind(this);
      this.handleOutroToggleDropdown = this.handleOutroToggleDropdown.bind(this);
      this.hideIntroDropdown = this.hideIntroDropdown.bind(this);
      this.hideOutroDropdown = this.hideOutroDropdown.bind(this);
      this.handleFormSubmit = this.handleFormSubmit.bind(this);
      this.handleSelectProgram = this.handleSelectProgram.bind(this);
      this.handleSelectSkill = this.handleSelectSkill.bind(this);
      this.handleProblemType = this.handleProblemType.bind(this);
      this.isSubmitting = this.isSubmitting.bind(this);
      this.state = {
        selectedProgram: '',
        isSubmitting: false
      };
    }

    addTableRows(){
        const rowsInput={
            question_number: this.props.mappingData.length + 1,
            start_unit: '',
            end_unit: '',
            start_unit_location: '',
            end_unit_location: '',
            skill: '',
            problem_type: '',
            showIntroDropdown: false,
            showOutroDropdown: false
        }
        this.props.updateMappingData([...this.props.mappingData, rowsInput])
    }

    deleteTableRows(index){
        const rows = [...this.props.mappingData];
        rows.splice(index, 1);
        rows.forEach((row, index) => {
          row.question_number = index + 1;
        })
        this.props.updateMappingData(rows);
    }

    isSubmitting(status) {
      this.setState((prevState) => ({
        ...prevState,
        isSubmitting: status
      }));
    }

    handleIntroToggleDropdown(index) {
        const rowsInput = [...this.props.mappingData];
        if(rowsInput[index]["start_unit"] === ""){
            return;
        }
        rowsInput[index]["showIntroDropdown"] = !rowsInput[index]["showIntroDropdown"];
        if(rowsInput[index]["showIntroDropdown"] === true){
            rowsInput[index]["showOutroDropdown"] = false;
            for(var i=0; i<this.props.mappingData.length; i++){
                if(i!==index){
                    rowsInput[i]["showIntroDropdown"] = false;
                    rowsInput[i]["showOutroDropdown"] = false;
                }
            }
        }
        this.props.fetchCourseBlocks(this.props.baseUrl, this.props.mappingData[index]['start_unit'], this.props.excludeBlockTypes);
        this.props.updateMappingData(rowsInput);
    }

    handleOutroToggleDropdown(index) {
        const rowsInput = [...this.props.mappingData];
        if(rowsInput[index]["end_unit"] === ""){
            return
        }
        rowsInput[index]["showOutroDropdown"] = !rowsInput[index]["showOutroDropdown"];
        if(rowsInput[index]["showOutroDropdown"] === true){
            rowsInput[index]["showIntroDropdown"] = false;
            for(var i=0; i<this.props.mappingData.length; i++){
                if(i!==index){
                    rowsInput[i]["showIntroDropdown"] = false;
                    rowsInput[i]["showOutroDropdown"] = false;
                }
            }
        }
        this.props.fetchCourseBlocks(this.props.baseUrl, this.props.mappingData[index]['end_unit'], this.props.excludeBlockTypes);
        this.props.updateMappingData(rowsInput);
    }

    hideIntroDropdown(index, blockId) {
        const rowsInput = [...this.props.mappingData];
        rowsInput[index]["start_unit_location"] = blockId;
        rowsInput[index]["showIntroDropdown"] = false;
        this.props.updateMappingData(rowsInput);
    }

    hideOutroDropdown(index, blockId) {
        const rowsInput = [...this.props.mappingData];
        rowsInput[index]["end_unit_location"] = blockId;
        rowsInput[index]["showOutroDropdown"] = false;
        this.props.updateMappingData(rowsInput);
    }

    handleSelectSkill(index, event){
        const rowsInput = [...this.props.mappingData];
        rowsInput[index]["skill"] = event.target.value;
        this.props.updateMappingData(rowsInput);
    }

    handleProblemType(index, event){
        const rowsInput = [...this.props.mappingData];
        rowsInput[index]["problem_type"] = event.target.value;
        this.props.updateMappingData(rowsInput);
    }

    handleSelectIntro(index, event){
        const rowsInput = [...this.props.mappingData];
        rowsInput[index]["start_unit"] = event.target.value;
        this.props.updateMappingData(rowsInput);
    }

    handleSelectOutro(index, event){
        const rowsInput = [...this.props.mappingData];
        rowsInput[index]["end_unit"] = event.target.value;
        this.props.updateMappingData(rowsInput);
    }

    handleFormSubmit(event){
        event.preventDefault();
        this.isSubmitting(true);
        const rowsInput = this.props.mappingData.map(({ showIntroDropdown, showOutroDropdown,...rest}) => ({...rest}));
        this.props.addProgramSkillAssessmentMapping(this.state.selectedProgram, rowsInput, this.isSubmitting);
    };

    handleSelectProgram(event){
        this.props.fetchProgramSkillAssessmentMapping(event.target.value);
        this.setState({
            selectedProgram: event.target.value
        });
    };

    render(){
        const { programsWithUnits, onSelectBlock, skills, problem_types } = this.props;
        return(
            <div>
                <div className="form-group">
                    <select
                        value={this.state.selectedProgram}
                        onChange={this.handleSelectProgram}
                        className="form-control"
                        id="select-program">
                        <option value="">Select Program</option>
                        {
                        Object.entries(programsWithUnits).map(([key, value], index) => (
                            <option key={index} value={key}>{key}</option>
                        ))
                        }
                    </select>
                </div>
                {
                  this.state.selectedProgram !== "" &&
                  <div className="skill-assessments">
                    {
                      this.state.isSubmitting &&
                      <div className="overlay-loader">
                        <span className="fa fa-refresh fa-spin"></span>
                      </div>
                    }
                    <table className="table table table-striped">
                        <thead>
                        <tr>
                            <th className="count">#</th>
                            <th className="intro">Intro</th>
                            <th className="outro">Outro</th>
                            <th className="type">Type</th>
                            <th className="skill">Skill</th>
                            <th className="actions">
                              <button className="btn btn-outline-success" onClick={this.addTableRows}>
                                <span className="fa fa-plus"></span>
                              </button>
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                            <SkillAssessmentTableRows
                                rowsData={this.props.mappingData}
                                deleteTableRows={this.deleteTableRows}
                                skills={skills}
                                problem_types={problem_types}
                                unitKeys={programsWithUnits[this.state.selectedProgram]}
                                handleSelectIntro={this.handleSelectIntro}
                                handleSelectOutro={this.handleSelectOutro}
                                handleSelectSkill={this.handleSelectSkill}
                                handleProblemType={this.handleProblemType}
                                handleIntroToggleDropdown={this.handleIntroToggleDropdown}
                                handleOutroToggleDropdown={this.handleOutroToggleDropdown}
                                hideIntroDropdown={this.hideIntroDropdown}
                                hideOutroDropdown={this.hideOutroDropdown}
                                onSelectBlock={onSelectBlock}
                            />
                        </tbody>
                    </table>
                  </div>
                }
                {
                    this.state.selectedProgram !== "" &&
                    <form onSubmit={this.handleFormSubmit}>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={this.state.isSubmitting}
                        >
                          {
                            this.state.isSubmitting ?
                            <span>Submitting... <span className="fa fa-refresh fa-spin"></span></span> :
                            "Submit"
                          }
                        </button>
                    </form>
                }
            </div>
        )
    }
}

SkillAssessmentTable.propTypes = {
    baseUrl: PropTypes.string.isRequired,
    excludeBlockTypes: PropTypes.arrayOf(PropTypes.string),
    fetchCourseBlocks: PropTypes.func.isRequired,
    onSelectBlock: PropTypes.func.isRequired,
};

SkillAssessmentTable.defaultProps = {
    excludeBlockTypes: null,
};

const mapStateToProps = state => ({
    mappingData: state.skillAssessment.mappingData
});

const mapDispatchToProps = dispatch => ({
    onSelectBlock: blockId => dispatch(selectBlock(blockId)),
    fetchCourseBlocks:
        (baseUrl, courseId, excludeBlockTypes) =>
        dispatch(fetchCourseBlocks(baseUrl, courseId, excludeBlockTypes)),
    fetchProgramSkillAssessmentMapping: (programSlug) => dispatch(fetchProgramSkillAssessmentMapping(programSlug)),
    addProgramSkillAssessmentMapping: (programSlug, mappingData, isSubmitting) => dispatch(addProgramSkillAssessmentMapping(programSlug, mappingData, isSubmitting)),
    updateMappingData: (mappingData) => dispatch(updateMappingData(mappingData)),
});


export default connect(mapStateToProps, mapDispatchToProps)(SkillAssessmentTable);
