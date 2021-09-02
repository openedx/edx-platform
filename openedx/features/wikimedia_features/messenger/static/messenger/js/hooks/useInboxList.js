import { useState, useEffect } from 'react';
import useClient from "./useClient"
import { ToastsStore } from "react-toasts";

export default function useInboxList(inboxPageNumber, setSelectedInboxUser, context) {
    const { client } = useClient()
    const [inboxList, setInboxList] = useState([]);
    const [inboxHasMore, setInboxHasMore] = useState(false);
    const [inboxLoading, setInboxLoading] = useState(false);

    const fetchInboxList = async() => {
        try {
            setInboxLoading(true);
            const inboxListData = (await client.get(`${context.INBOX_URL}?page=${inboxPageNumber}`)).data
            if (inboxListData) {
                setInboxList((previousList) => [...previousList, ...inboxListData.results]);
                setInboxHasMore(inboxPageNumber < inboxListData.num_pages)

                if (inboxPageNumber == 1 && inboxListData.results.length) {
                    setSelectedInboxUser(inboxListData.results[0].with_user)
                }
            }
            setInboxLoading(false);
        } catch (e) {
            console.error(e);
            ToastsStore.error("Unable to fetch all conversations.")
        }
    }

    useEffect(() => {
        fetchInboxList();
    }, [inboxPageNumber])

    return { inboxList, setInboxList, inboxLoading, inboxHasMore }
};
