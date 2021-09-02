import { ToastsStore } from "react-toasts";
import useClient from "./useClient"

export default function useUserSearch(context) {
    const { client } = useClient()

    const fetchUsers = async(query, setNewMessageUsers) => {
        try {
            if (query) {
                let users = (await client.get(`${context.USER_SEARCH_URL}?search=${query}`)).data;
                if (users) {
                    setNewMessageUsers(users.results.map((user)=>{
                        return {
                            id: user.username,
                            username: user.username
                        }
                    }));
                }
            }
        } catch (ex) {
            ToastsStore.error('Failed to fetch users.');
            console.error(ex)
        }
    }
    return { fetchUsers }
}
