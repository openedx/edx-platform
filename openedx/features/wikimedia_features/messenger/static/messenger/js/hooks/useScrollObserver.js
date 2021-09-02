import { useRef, useCallback } from 'react'

export default function useScrollObserver(
    setInboxPageNumber, inboxLoading, inboxHasMore,
    setMessagesPageNumber, messagesLoading, messagesHasMore
) {

    const messageObserver = useRef()
    const InboxListObserver = useRef()

    const lastMessageRef = useCallback(
        (node) => {
            if (messagesLoading) return
            if (messageObserver.current) messageObserver.current.disconnect();
            messageObserver.current = new IntersectionObserver(entries => {
                if (entries[0].isIntersecting && messagesHasMore) {
                    setMessagesPageNumber(prevPageNumber => prevPageNumber + 1)
                }
            })
            if (node) messageObserver.current.observe(node)
        }, [messagesLoading, messagesHasMore]
    )

    const lastInboxRef = useCallback(
        (node) => {
            if (inboxLoading) return
            if (InboxListObserver.current) InboxListObserver.current.disconnect();
            InboxListObserver.current = new IntersectionObserver(entries => {
                if (entries[0].isIntersecting && inboxHasMore) {
                    setInboxPageNumber(prevPageNumber => prevPageNumber + 1)
                }
            })
            if (node) InboxListObserver.current.observe(node)
        }, [inboxLoading, inboxHasMore]
    )

    return { lastMessageRef, lastInboxRef }
}
