/*
Wrapper for React/Paragon accessible status bar
*/

import React from 'react';
import Websocket from 'react-websocket'
import Confetti from 'react-confetti'
import windowDimensions from 'react-window-dimensions';


class CompletionStatus extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            course_id: '',
            percent_complete: 100,
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

        if (result.percent_complete === 100) {
        }

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

        return (
            <div>
                <Websocket ref="socket" url={socketUrl}
                    onMessage={this.handleData.bind(this)} reconnect={true}/>
                <label>Completion: </label><progress max="100" value={this.state.percent_complete}></progress><span>{this.state.percent_complete}%</span>
                {this.state.percent_complete === 100 &&
                    <div style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%'}}>
                        <Confetti width={this.props.width} height={this.props.height}/>
                    </div>
                }
            </div>
        )
    }
}

CompletionStatus.propTypes = {
    socketPath: React.PropTypes.string
};

// windowSize is a HOC that sets props.windowHeight and props.windowWidth
const sizeAwareCompletionStatus = windowDimensions()(CompletionStatus);

export { sizeAwareCompletionStatus as CompletionStatus };