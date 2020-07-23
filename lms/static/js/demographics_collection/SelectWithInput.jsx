import React from 'react';

class SelectWithInput extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selected: this.props.selected,
    }
  }

  render() {
    return (
      <select value={this.state.selected} onChange={this.props.selectHandler}>
        {this.props.options}
      </select>
    )
  }
}