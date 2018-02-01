/*
Wrapper for React/Paragon accessible status bar
*/

import React from 'react';
import Websocket from 'react-websocket'
import Confetti from 'react-confetti'
import windowDimensions from 'react-window-dimensions';
import Modal from 'react-modal';


class CompletionStatus extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            course_id: this.props.course_id || '',
            percent_complete: this.props.percentComplete || 0,
            modalIsOpen: false,
        };

        this.sendSocketMessage = this.sendSocketMessage.bind(this);
        this.openModal = this.openModal.bind(this);
        this.closeModal = this.closeModal.bind(this);
    }

    componentDidMount() {
    }

    componentWillUnmount() {
        this.serverRequest.abort();
    }

    handleData(data) {
        //receives messages from the connected websocket
        let result = JSON.parse(data);

        if (result.percent_complete === 100) {
            this.openModal();
        }

        // we've received an updated completion status event
        this.setState(result);
    }

    sendSocketMessage(message){
        // sends message to channels back-end
       const socket = this.refs.socket;
       socket.state.ws.send(JSON.stringify(message))
    }

    openModal() {
        this.setState({modalIsOpen: true});
    }

    closeModal() {
        this.setState({modalIsOpen: false});
    }

    render() {
        const socketUrl = `ws://${window.location.host}/${this.props.socketPath}/`;
        const isComplete = this.state.percent_complete === 100;

        return (
            <div>
                <Websocket ref="socket" url={socketUrl}
                    onMessage={this.handleData.bind(this)} reconnect={true}/>
                <label>Completion: </label><progress max="100" value={this.state.percent_complete}></progress><span>{this.state.percent_complete}%</span>
                {isComplete &&
                    <div style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%'}}>
                        <Confetti width={this.props.width} height={this.props.height}/>
                    </div>
                }
                <Modal isOpen={this.state.modalIsOpen}
                            style={{
                                overlay: {
                                  position: 'fixed',
                                  top: 0,
                                  left: 0,
                                  right: 0,
                                  bottom: 0,
                                  backgroundColor: 'rgba(0, 0, 0, 0.5)'
                                },
                                content: {
                                    position: 'absolute',
                                    top: '25%',
                                    bottom: '-25%',
                                    left: '25%',
                                    right: '-25%',
                                    maxHeight: '300px',
                                    maxWidth: '600px',
                                    border: '1px solid #ccc',
                                    background: '#fff',
                                    overflow: 'auto',
                                    WebkitOverflowScrolling: 'touch',
                                    borderRadius: '4px',
                                    outline: 'none',
                                    padding: '20px'
                                }

                            }}
                >
                    <h2>Congratulations!</h2>
                    <p>You've done it! You've finished the course.</p>
                    <p>Continue your lifetime of learning by exploring new courses.
                    Here are a few we think you might like:</p>
                    <ul>
                        <li><a href="#">Linear Algebra - Foundations to Frontiers</a></li>
                        <li><a href="#">Essential Mathematics for Artificial Intelligence</a></li>
                        <li><a href="#">Foundations of Data Structures</a></li>
                    </ul>
                    <button onClick={this.closeModal} style={{float: 'right'}}>OK</button>
                </Modal>
            </div>
        )
    }
}

CompletionStatus.propTypes = {
    socketPath: React.PropTypes.string,
    percentComplete: React.PropTypes.number
};

// windowSize is a HOC that sets props.windowHeight and props.windowWidth
const sizeAwareCompletionStatus = windowDimensions()(CompletionStatus);

export { sizeAwareCompletionStatus as CompletionStatus };