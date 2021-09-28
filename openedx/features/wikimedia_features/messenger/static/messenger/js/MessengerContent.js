import React, { useState } from 'react';
import { ToastContainer } from 'react-toastify';

import useInboxList from './hooks/useInboxList';
import useSelectedInbox from './hooks/useSelectedInbox';
import useCreateUpdateMessages from './hooks/useCreateUpdateMessages';
import useScrollObserver from './hooks/useScrollObserver';

import Inbox from "./components/Inbox/index";
import Conversation from "./components/Conversation/index";
import NewMessageModal from './components/newMessageModal';


export default function MessengerContent({ context }) {
    const [inboxPageNumber, setInboxPageNumber] = useState(1);
    const [messagesPageNumber, setMessagesPageNumber] = useState(1);
    const [isDrawerShown, setDrawerShown] = useState(false);
    const [searchInbox, setSearchInbox] = useState("");

    const {
        selectedInboxUser,
        setSelectedInboxUser,
        selectedInboxMessages,
        setSelectedInboxMessages,
        messagesLoading,
        messagesHasMore,
        loggedinUser
    } = useSelectedInbox(messagesPageNumber, setMessagesPageNumber, context);

    const {
        inboxList,
        setInboxList,
        inboxLoading,
        inboxHasMore
    } = useInboxList(inboxPageNumber, setSelectedInboxUser, context, setInboxPageNumber, searchInbox);

    const {
        updateLastMessage,
        createGroupMessages,
        createMessage,
    } = useCreateUpdateMessages(inboxList, setInboxList, selectedInboxUser, setSelectedInboxMessages, context);


    const {
        lastInboxRef,
        lastMessageRef
    } = useScrollObserver(
        setInboxPageNumber, inboxLoading, inboxHasMore,
        setMessagesPageNumber, messagesLoading, messagesHasMore
    );

    return (
        <div className={isDrawerShown ? 'chat-sidebar-open': ''}>
            <div className="messenger main-container">
                <Inbox
                    setSelectedInboxUser = { setSelectedInboxUser }
                    inboxList = { inboxList }
                    lastInboxRef = { lastInboxRef }
                    inboxLoading = { inboxLoading }
                    selectedInboxUser = { selectedInboxUser }
                    isDrawerShown = { isDrawerShown }
                    setDrawerShown = { setDrawerShown }
                    searchInbox = { searchInbox }
                    setSearchInbox = { setSearchInbox }
                />
                <Conversation
                    createMessage = { createMessage }
                    selectedInboxMessages = { selectedInboxMessages }
                    messagesLoading = { messagesLoading }
                    updateLastMessage = { updateLastMessage }
                    lastMessageRef = { lastMessageRef }
                    selectedInboxUser = { selectedInboxUser }
                    loggedinUser = { loggedinUser }
                />
                <div
                    className="chat-overlay"
                    onClick={() => setDrawerShown(!isDrawerShown)}
                ></div>
            </div>
            <NewMessageModal
                createGroupMessages = { createGroupMessages }
                context = { context }
            />
            <ToastContainer />
        </div>
    )
}
