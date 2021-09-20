import React, { useState } from 'react';
import Spinner from '../../assets/spinner';

export default function Conversation({
    selectedInboxMessages,
    createMessage,
    messagesLoading,
    updateLastMessage,
    lastMessageRef,
    selectedInboxUser
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
            </div>
            <div className="chat">
                {selectedInboxMessages && !messagesLoading && selectedInboxMessages.map(
                    (message, index) => {
                        let setRef = (selectedInboxMessages.length === index + 1 ) ? true : false;
                        const hasProfileImage = message.sender_img.indexOf('default_50') === -1;
                        const profileName = `${message.sender[0]}${message.sender.split(' ')[1] ? message.sender.split(' ')[1][0] : message.sender[1]}`;
                        return (
                            <div className="chat-row" key={index} ref={setRef ? lastMessageRef : null}>
                                {
                                    hasProfileImage
                                    ? (<img src={message.sender_img} alt={message.sender} />)
                                    : (<span className="img-placeholder" style={{background: '#a7f9e0'}}>{profileName}</span>)
                                }
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
