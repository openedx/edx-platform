import React from 'react';
import TableRows from "./TableRows"

export default class AddDeleteTableRows extends React.Component {
    constructor(props) {
      super(props);
      this.addTableRows = this.addTableRows.bind(this);
      this.deleteTableRows = this.deleteTableRows.bind(this);
      this.handleSelectIntro = this.handleSelectIntro.bind(this);
      this.handleSelectOutro = this.handleSelectOutro.bind(this);
      this.state = {
        rowsData: []
      };
    }


    addTableRows(){
        const rowsInput={
            selectedIntro:'',
            selectedOutro:''
        }
        this.setState({ rowsData: [...this.state.rowsData, rowsInput]})
    }
    deleteTableRows(index){
        const rows = [...this.state.rowsData];
        rows.splice(index, 1);
        this.setState({rowsData: rows});
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

    render(){
        return(
            <div className="container">
                <div className="row">
                    <div className="col-sm-8">
                    <table className="table">
                        <thead>
                        <tr>
                            <th>Intro Unit</th>
                            <th>Outro Unit</th>
                            <th><button className="btn btn-outline-success" onClick={this.addTableRows} >+</button></th>
                        </tr>
                        </thead>
                    <tbody>
                    <TableRows
                        rowsData={this.state.rowsData}
                        deleteTableRows={this.deleteTableRows}
                        unitKeys={this.props.unitKeys}
                        handleSelectIntro={this.handleSelectIntro}
                        handleSelectOutro={this.handleSelectOutro}
                    />
                    </tbody>
                    </table>
                    </div>
                    <div className="col-sm-4">
                    </div>
                </div>
            </div>
        )
    }
}
