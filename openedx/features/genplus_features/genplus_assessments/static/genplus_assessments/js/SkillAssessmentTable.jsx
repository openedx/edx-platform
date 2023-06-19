import React from 'react';
import { connect } from 'react-redux';
import * as PropTypes from 'prop-types';
import { selectBlock } from 'BlockBrowser/data/actions/courseBlocks';
import {
    fetchCourseBlocks,
    fetchProgramSkillAssessmentMapping,
    addProgramSkillAssessmentMapping
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
      this.state = {
        selectedProgram: '',
        rowsData: []
      };
    }

    addTableRows(){
        const rowsInput={
            selectedIntro:'',
            selectedOutro:'',
            selectedIntroBlock:'',
            selectedOutroBlock:'',
            showIntroDropdown: false,
            showOutroDropdown: false
        }
        this.setState({ rowsData: [...this.state.rowsData, rowsInput]})
    }

    deleteTableRows(index){
        const rows = [...this.state.rowsData];
        rows.splice(index, 1);
        this.setState({rowsData: rows});
    }

    handleIntroToggleDropdown(index) {
        const rowsInput = [...this.state.rowsData];
        if(rowsInput[index]["selectedIntro"] === ""){
            return;
        }
        rowsInput[index]["showIntroDropdown"] = !rowsInput[index]["showIntroDropdown"];
        if(rowsInput[index]["showIntroDropdown"] === true){
            rowsInput[index]["showOutroDropdown"] = false;
            for(var i=0; i<this.state.rowsData.length; i++){
                if(i!==index){
                    rowsInput[i]["showIntroDropdown"] = false;
                    rowsInput[i]["showOutroDropdown"] = false;
                }
            }
        }
        this.props.fetchCourseBlocks(this.props.baseUrl, this.state.rowsData[index]['selectedIntro'], this.props.excludeBlockTypes);
        this.setState({rowsData: rowsInput});
    }

    handleOutroToggleDropdown(index) {
        const rowsInput = [...this.state.rowsData];
        if(rowsInput[index]["selectedOutro"] === ""){
            return
        }
        rowsInput[index]["showOutroDropdown"] = !rowsInput[index]["showOutroDropdown"];
        if(rowsInput[index]["showOutroDropdown"] === true){
            rowsInput[index]["showIntroDropdown"] = false;
            for(var i=0; i<this.state.rowsData.length; i++){
                if(i!==index){
                    rowsInput[i]["showIntroDropdown"] = false;
                    rowsInput[i]["showOutroDropdown"] = false;
                }
            }
        }
        this.props.fetchCourseBlocks(this.props.baseUrl, this.state.rowsData[index]['selectedOutro'], this.props.excludeBlockTypes);
        this.setState({rowsData: rowsInput});
    }

    hideIntroDropdown(index, blockId) {
        const rowsInput = [...this.state.rowsData];
        rowsInput[index]["selectedIntroBlock"] = blockId;
        rowsInput[index]["showIntroDropdown"] = false;
        this.setState({rowsData: rowsInput});
    }

    hideOutroDropdown(index, blockId) {
        const rowsInput = [...this.state.rowsData];
        rowsInput[index]["selectedOutroBlock"] = blockId;
        rowsInput[index]["showOutroDropdown"] = false;
        this.setState({rowsData: rowsInput});
    }

    handleSelectIntro(index, event){
        const rowsInput = [...this.state.rowsData];
        rowsInput[index]["selectedIntro"] = event.target.value;
        this.setState({rowsData: rowsInput});
    }

    handleSelectOutro(index, event){
        const rowsInput = [...this.state.rowsData];
        rowsInput[index]["selectedOutro"] = event.target.value;
        this.setState({rowsData: rowsInput});
    }

    handleFormSubmit(event){
        event.preventDefault();
        this.props.addProgramSkillAssessmentMapping(this.state.selectedProgram, this.state.rowsData);
    };

    handleSelectProgram(event){
        this.props.fetchProgramSkillAssessmentMapping(event.target.value);
        this.setState({
            selectedProgram: event.target.value
        });
    };

    render(){
        const { programsWithUnits, onSelectBlock } = this.props;
        return(
            <div>
                <header className="mast">
                  <h1 className="page-header">{"Add/Update Skill Assessment"}</h1>
                </header>
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
                    <table className="table table-striped">
                        <thead>
                        <tr>
                            <th>Intro</th>
                            <th>Outro</th>
                            <th className="actions">
                              <button className="btn btn-outline-success" onClick={this.addTableRows}>
                                <span className="fa fa-plus"></span>
                              </button>
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                            <SkillAssessmentTableRows
                                rowsData={this.state.rowsData}
                                deleteTableRows={this.deleteTableRows}
                                unitKeys={programsWithUnits[this.state.selectedProgram]}
                                handleSelectIntro={this.handleSelectIntro}
                                handleSelectOutro={this.handleSelectOutro}
                                handleIntroToggleDropdown={this.handleIntroToggleDropdown}
                                handleOutroToggleDropdown={this.handleOutroToggleDropdown}
                                hideIntroDropdown={this.hideIntroDropdown}
                                hideOutroDropdown={this.hideOutroDropdown}
                                onSelectBlock={onSelectBlock}
                            />
                        </tbody>
                    </table>
                }
                {
                    this.state.selectedProgram !== "" &&
                    <form onSubmit={this.handleFormSubmit}>
                        <button
                            type="submit"
                            className="btn btn-primary"
                        >
                            Submit
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
    mapping: state.mapping
});


const mapDispatchToProps = dispatch => ({
    onSelectBlock: blockId => dispatch(selectBlock(blockId)),
    fetchCourseBlocks:
        (baseUrl, courseId, excludeBlockTypes) =>
        dispatch(fetchCourseBlocks(baseUrl, courseId, excludeBlockTypes)),
    fetchProgramSkillAssessmentMapping: program_slug => (fetchProgramSkillAssessmentMapping(program_slug)),
    addProgramSkillAssessmentMapping: (program_slug, mapping_data) => (addProgramSkillAssessmentMapping(program_slug, mapping_data))
});


export default connect(mapStateToProps, mapDispatchToProps)(SkillAssessmentTable);
