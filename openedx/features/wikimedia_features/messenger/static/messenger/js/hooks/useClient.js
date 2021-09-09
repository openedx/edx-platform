import HttpClient from "../client";
import Cookies from "js-cookie";


export default function useClient() {
    const client = new HttpClient({
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken"),
        },
    });

    const notification = (func, msg) => {
        func(msg, { theme: "colored" });
    }

    return { client, notification };
}
