import React, { useState } from 'react'

export default function Conversation({
    selectedInboxMessages,
    createMessage,
    messagesLoading,
    updateLastMessage,
    lastMessageRef,
    selectedInboxUser
}) {

    const [message, setMessage] = useState("")

    const handleSendMessageBtnClick = () => {
        createMessage(message, setMessage, updateLastMessage);
    }

    return (
        <div className="chat-container">
            <div className="selected-user">{selectedInboxUser}</div>
            <div className="chat">
                {selectedInboxMessages && selectedInboxMessages.map(
                    (message, index) => {
                        let setRef = (selectedInboxMessages.length === index + 1 ) ? true : false;
                        return (
                            <div className="chat-div" key={index} ref={setRef ? lastMessageRef : null}>
                                <img src={message.sender_img} alt={message.sender} />
                                <div className="chat-div-detail">
                                    <span className="msg-sender">{message.sender}</span>
                                    <span className="chat-time">{message.created}</span>
                                    <h2>{message.message}</h2>
                                </div>
                            </div>
                        )
                    }
                )}
                <div className="loading">{messagesLoading && "Loading conversation.."}</div>
            </div>
            <div className="new-message">
                <textarea className="new-message-input" value={message} onChange={(e) => setMessage(e.target.value)}></textarea>
                <button className="btn-primary" onClick={handleSendMessageBtnClick}><i className="fa fa-send"></i></button>
            </div>
        </div>
    )
}
