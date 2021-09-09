import React from "react";
import ReactDOM from "react-dom";

import MessengerContent from "./MessengerContent";

export class Messenger {
    constructor(context) {
        ReactDOM.render(<MessengerContent context={context} />, document.getElementById("root"));
    }
}
