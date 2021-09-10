import useClient from "./useClient";

import { toast } from 'react-toastify';

export default function useUserSearch(context) {
    const { client, notification } = useClient();

    const fetchUsers = async(query, setNewMessageUsers) => {
        try {
            if (query) {
                let users = (await client.get(`${context.USER_SEARCH_URL}?search=${query}`)).data;
                if (users) {
                    setNewMessageUsers(users.results.map((user)=>{
                        return {
                            id: user.username,
                            username: user.username
                        };
                    }));
                }
            }
        } catch (ex) {
            notification(toast.error, "Unable to search users.");
            console.error(ex);
        }
    }
    return { fetchUsers };
}
