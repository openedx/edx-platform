/*
Wrapper for React/Paragon accessible status bar
*/

import React from 'react';
import Websocket from 'react-websocket'

export class CompletionStatus extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            course_id: '',
            percent_complete: 0,
        };

        // TODO: do we need to send anything?
        this.sendSocketMessage = this.sendSocketMessage.bind(this);
    }

    componentDidMount() {}

    componentWillUnmount() {
        this.serverRequest.abort();
    }

    handleData(data) {
        //receives messages from the connected websocket
        let result = JSON.parse(data);

        // we've received an updated completion status event
        this.setState(result);
    }

    sendSocketMessage(message){
        // sends message to channels back-end
       const socket = this.refs.socket;
       socket.state.ws.send(JSON.stringify(message))
    }

    render() {
        const socketUrl = `ws://${window.location.host}/${this.props.socketPath}/`;
        const barStyle = {
            width: this.state.percent_complete
        };
        return (
            <div className="row">
                <Websocket ref="socket" url={socketUrl}
                    onMessage={this.handleData.bind(this)} reconnect={true}/>
                <div className="progress">
                    <div className="progress-bar" role="progressbar" style={barStyle} aria-valuenow="{this.state.percent_complete}" aria-valuemin="0" aria-valuemax="100">{this.state.percent_complete}%</div>
                </div>
            </div>
        )
    }
}

CompletionStatus.propTypes = {
    socketPath: React.PropTypes.string
};