import React from 'react';

export default function Inbox({
    inboxList, lastInboxRef, inboxLoading, setSelectedInboxUser,
    selectedInboxUser,
}) {
    const handleInboxClick = (event) => {
        setSelectedInboxUser(event.currentTarget.dataset.user);
    }

    return (
        <div className="inbox-container">
            <div className="start-new-msg-div">
                <button className="btn btn-primary btn-lg start-new-msg-btn" data-toggle="modal" data-target="#messageModalCenter">
                    + New Message
                </button>
            </div>

            <ul className="inbox-list">
                {
                    (!inboxList) ? <span>No conversation found!</span>: inboxList.map(
                        (inbox, index) => {
                            let setRef = (inboxList.length === index + 1 ) ? true : false;
                            let name = (selectedInboxUser === inbox.with_user) ? "inbox-message active" : "inbox-message";
                            return (
                                <li key={index} data-user={inbox.with_user} className={name} ref={setRef ? lastInboxRef : null} onClick={(e)=>handleInboxClick(e)}>
                                    <img src={inbox.with_user_img} alt={inbox.with_user} />
                                    <div className="about">
                                        <div className="name">
                                            {inbox.with_user}
                                        </div>
                                        <div className="status">
                                            {inbox.last_message.length > 30 ? `${inbox.last_message.substring(0, 30)}...` : inbox.last_message}
                                        </div>
                                    </div>
                                    <span className="badge rounded-pill bg-danger unread-count">{inbox.unread_count ? inbox.unread_count : ""}</span>
                                </li>
                            )
                        }
                    )
                }
                <div className="loading">{inboxLoading && "Loading List..."}</div>
            </ul>
        </div>
    )
}
