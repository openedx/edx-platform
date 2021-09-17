import React, { useState } from 'react';
import Spinner from '../../assets/spinner';

export default function Conversation({
    selectedInboxMessages,
    createMessage,
    messagesLoading,
    updateLastMessage,
    lastMessageRef,
    selectedInboxUser,
    isDrawerShown,
    setDrawerShown
}) {

    const [message, setMessage] = useState("");

    const handleSendMessageBtnClick = () => {
        createMessage(message, setMessage, updateLastMessage);
    }

    const handleInputChange = (e) => {
        setMessage(e.target.value);
        e.target.style.height = '5px';
        e.target.style.height = `${e.target.scrollHeight}px`;
    }

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>{selectedInboxUser}&nbsp;</h2>
                <button className="hamburger-menu" onClick={() => {setDrawerShown(!isDrawerShown)}}>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                </button>
            </div>
            <div className="chat">
                {selectedInboxMessages && !messagesLoading && selectedInboxMessages.map(
                    (message, index) => {
                        let setRef = (selectedInboxMessages.length === index + 1 ) ? true : false;
                        return (
                            <div className="chat-row" key={index} ref={setRef ? lastMessageRef : null}>
                                <img src={message.sender_img} alt={message.sender} />
                                <div className="chat-detail">
                                    <span className="msg-sender">{message.sender}</span>
                                    <span className="chat-time">{message.created}</span>
                                    <pre>{message.message}</pre>
                                </div>
                            </div>
                        )
                    }
                )}
                {
                    messagesLoading && (
                        <Spinner />
                    )
                }
            </div>
            <div className="new-message">
                <textarea
                    className="new-message-input"
                    value={message}
                    placeholder="Type your message..."
                    onChange={handleInputChange}
                ></textarea>
                <button
                    className="btn-primary"
                    onClick={handleSendMessageBtnClick}
                    disabled={!message.length}
                ><i className="fa fa-send"></i></button>
            </div>
        </div>
    )
}
