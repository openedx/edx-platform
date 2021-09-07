import { useEffect } from 'react'
import { ToastsStore } from "react-toasts";
import useClient from "./useClient"


export default function useCreateUpdateMessages(
    inboxList, setInboxList, selectedInboxUser, setSelectedInboxMessages, context) {
    const { client } = useClient()
    let currentInbox = {}

    const createMessage = async(message, setMessage, updateLastMessage) => {
        try {
            const createdMessage = (await client.post(context.MESSAGE_URL, {
                receiver: selectedInboxUser,
                message: message
            })).data
            if (createdMessage) {
                setSelectedInboxMessages((prevMsgs) => [createdMessage, ...prevMsgs]);
                setMessage("")
                updateLastMessage(message)
            }
            ToastsStore.success("Message has been sent.")
        } catch (e) {
            console.error(e);
            ToastsStore.error("Unable to send your message, please try again!")
        }
    }

    const createGroupMessages = async(message, users) => {
        try {
            const UpdatedInbox = (await client.post(context.BULK_MESSAGE_URL, {
                receivers: users.map((user) => user.id),
                message: message
            })).data

            updateInboxList(UpdatedInbox);
            updateOpenedConversation(message, users);
            ToastsStore.success("Message has been sent.")
        } catch (e) {
            console.error(e);
            ToastsStore.error("Unable to send your message, please try again!")
        }
    }

    const updateInboxList = (UpdatedInbox ) => {
        let newlyCreatedInbox = []
        let newList = inboxList.map((inbox) => inbox)
        UpdatedInbox.forEach((newInbox) => {
            let existingInbox = inboxList.find((inbox) => inbox.id === newInbox.id)
            if (existingInbox) {
                newList = newList.map((inbox) => {
                    return inbox.id == newInbox.id ? newInbox : inbox;
                })
            } else {
                newlyCreatedInbox.push(newInbox)
            }
        })

        if (newlyCreatedInbox) {
            newList = [...newlyCreatedInbox, ...newList]
        }
        setInboxList(newList);
    }

    const updateOpenedConversation = (message, users) => {
        let isConversationOpened = users.some((user) => user.username == selectedInboxUser)
        if (isConversationOpened) {
            setSelectedInboxMessages((prevMsgs) => {
                return [{
                    sender: context.LOGIN_USER,
                    sender_img: context.LOGIN_USER_IMG,
                    created: "now",
                    message
                }, ...prevMsgs, ]
            })
        }
    }

    const updateUnreadCount = async(inboxId) => {
        try {
            let updatedInbox = (await client.patch(`${context.INBOX_URL}${inboxId}/`, {
                unread_count: 0
            })).data;
            if (updatedInbox) {
                setInboxList((previousList) => {
                    return previousList.map((inbox) => {
                        return (inbox.id === updatedInbox.id ? updatedInbox : inbox)
                    })
                });
            }
        } catch (ex) {
            ToastsStore.error('Failed: Failure while updating .');
            console.error(ex)
        }
    }

    const updateLastMessage = (message) => {
        currentInbox = inboxList.find((inbox) => inbox.with_user == selectedInboxUser)
        if (currentInbox) {
            currentInbox.last_message = message.length > 30 ? `${message.substring(0, 30)}...`: message;
            setInboxList((previousList) => {
                return previousList.map((inbox) => {
                    return (inbox.id === currentInbox.id ? currentInbox : inbox)
                })
            });
        }
    }

    useEffect(() => {
        currentInbox = inboxList.find((inbox) => inbox.with_user == selectedInboxUser)
        if (currentInbox && currentInbox.unread_count) {
            setTimeout(() => { updateUnreadCount(currentInbox.id) }, 3000);

        }
    }, [selectedInboxUser])

    return { updateLastMessage, createGroupMessages, createMessage, updateUnreadCount }
}
