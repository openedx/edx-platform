import { useState, useEffect } from 'react';

import useClient from "./useClient";


export default function useSelectedInbox(messagesPageNumber, setMessagesPageNumber, context) {
    const { client, notification } = useClient();
    const [selectedInboxUser, setSelectedInboxUser] = useState("");
    const [selectedInboxMessages, setSelectedInboxMessages] = useState([]);
    const [messagesLoading, setMessagesLoading] = useState(false);
    const [messagesHasMore, setMessagesHasMore] = useState(false);

    const fetchSelectedInboxMessages = async(is_new_user, pageNumber) => {
        try {
            setMessagesLoading(true);
            const inboxMessages = (
                await client.get(
                    `${context.CONVERSATION_URL}?page=${pageNumber}&with_user=${selectedInboxUser}`
                )
            ).data;
            if (inboxMessages) {
                if (is_new_user) {
                    setSelectedInboxMessages(inboxMessages.results);
                } else {
                    setSelectedInboxMessages((previousList) => [...previousList, ...inboxMessages.results]);
                }
                setMessagesHasMore(pageNumber < inboxMessages.num_pages);
            }
            setMessagesLoading(false);
        } catch (e) {
            notification(toast.error, `Unable to load conversation of user: ${selectedInboxUser}.`);
            console.error(e);
        }
    }

    useEffect(() => {
        if (selectedInboxUser) {
            setMessagesPageNumber(1);
            fetchSelectedInboxMessages(true, 1);
        }
    }, [selectedInboxUser]);

    useEffect(() => {
        if (selectedInboxUser && messagesPageNumber > 1) {
            fetchSelectedInboxMessages(false, messagesPageNumber);
        }
    }, [messagesPageNumber]);

    return {
        selectedInboxUser,
        setSelectedInboxUser,
        selectedInboxMessages,
        setSelectedInboxMessages,
        messagesLoading,
        messagesHasMore
    };
}
