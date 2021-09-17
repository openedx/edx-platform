import React from 'react';
import Spinner from '../../assets/spinner';

export default function Inbox({
    inboxList, lastInboxRef, inboxLoading, setSelectedInboxUser,
    selectedInboxUser,
}) {
    const handleInboxClick = (event) => {
        setSelectedInboxUser(event.currentTarget.dataset.user);
    }

    return (
        <div className="chat-sidebar">
            <div className="chat-sidebar-header">
                <div className="btn-box">
                    <strong className="text">Chats</strong>
                    <button className="btn btn-primary btn-lg start-new-msg-btn" data-toggle="modal" data-target="#messageModalCenter">
                        <span className="icon-plus">+</span>New Message
                    </button>
                </div>
                <div className="search-box">
                    <span className="fa fa-search"></span>
                    <input type="text" className="search-field" placeholder="Search Users" />
                    <span className="fa fa-times-circle"></span>
                </div>
            </div>
            <ul className="inbox-list">
                {
                    inboxLoading && (
                        <Spinner />
                    )
                }
                {
                    (!inboxList) ? <span>No conversation found!</span>: inboxList.map(
                        (inbox, index) => {
                            let setRef = (inboxList.length === index + 1 ) ? true : false;
                            let name = (selectedInboxUser === inbox.with_user) ? "inbox-message active" : "inbox-message";
                            const unreadClass = inbox.unread_count ? 'unread' : '';
                            return (
                                <li key={index} data-user={inbox.with_user} className={`${name} ${unreadClass}`} ref={setRef ? lastInboxRef : null} onClick={(e)=>handleInboxClick(e)}>
                                    <img src={inbox.with_user_img} alt={inbox.with_user} />
                                    <span className="img-placeholder" style={{background: '#a7f9e0'}}>TS</span>
                                    <div className="about">
                                        <div className="title">
                                            <span className="date">9:45 pm</span>
                                            <span className="name">{inbox.with_user}</span>
                                        </div>
                                        <div className="message">
                                            {inbox.last_message.length > 30 ? `${inbox.last_message.substring(0, 30)}...` : inbox.last_message}
                                        </div>
                                    </div>
                                    <span className="badge rounded-pill bg-danger unread-count">{inbox.unread_count ? inbox.unread_count : ''}</span>
                                </li>
                            )
                        }
                    )
                }
            </ul>
        </div>
    )
}
