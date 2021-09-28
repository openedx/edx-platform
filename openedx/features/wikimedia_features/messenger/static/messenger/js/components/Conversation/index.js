import React, { useState } from 'react';
import Spinner from '../../assets/spinner';

export default function Conversation({
    selectedInboxMessages,
    createMessage,
    messagesLoading,
    updateLastMessage,
    lastMessageRef,
    selectedInboxUser,
    loggedinUser
}) {

    const [message, setMessage] = useState('');
    const [isReplying, setReplying] = useState(false);

    const handleSendMessageBtnClick = () => {
        createMessage(message, setMessage, updateLastMessage, setReplying);
    }

    const handleInputChange = (e) => {
        setMessage(e.target.value);
        e.target.style.height = '5px';
        e.target.style.height = `${e.target.scrollHeight}px`;
    }

    const handleCancelReply = (e) => {
        setReplying(false);
        setMessage('');
    }

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>Inbox / {selectedInboxUser}&nbsp;</h2>
            </div>
            <div className="chat">
                {
                    isReplying && (
                        <div className="chat-row">
                            {
                                loggedinUser.hasProfileImage ? (
                                    <img src={loggedinUser.profileImage} alt={loggedinUser.name} />
                                ) : (
                                    <span className="img-placeholder" style={{background: '#a7f9e0'}}>{loggedinUser.profileName}</span>
                                )
                            }
                            <div className="chat-detail">
                                <div className="new-message">
                                    <textarea
                                        className="new-message-input"
                                        value={message}
                                        placeholder="Type your message..."
                                        onChange={handleInputChange}
                                    ></textarea>
                                    <div className="btn-box">
                                        <button
                                            className="btn btn-primary"
                                            onClick={handleSendMessageBtnClick}
                                            disabled={!message.length}
                                        >Send</button>
                                        <button
                                            className="btn btn-default"
                                            onClick={(e) => handleCancelReply(e)}
                                        >Cancel</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                }
                {
                    selectedInboxMessages.length > 0 && !messagesLoading && !isReplying && (
                        <div className="chat-reply">
                            <button
                                className="btn btn-default"
                                onClick={(e) => setReplying(true)}
                            >Reply</button>
                        </div>
                    )
                }
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
        </div>
    )
}
