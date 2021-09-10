import React, {useState} from 'react';
import Multiselect from 'multiselect-react-dropdown';
import useUserSearch from '../hooks/useUserSearch';


export default function NewMessageModal({createGroupMessages, context}) {
    const [newMessageUsers, setNewMessageUsers] = useState([]);
    const [groupNewMessage, setGroupNewMessage ] = useState("");
    const [newMessageSelectedUsers, setNewMessageSelectedUsers] = useState([]);
    const {fetchUsers} = useUserSearch(context);

    const handleSearch = (query) => {
        fetchUsers(query, setNewMessageUsers);
    }

    const handleNewMessageBtnClick = (event) => {
        event.preventDefault();
        createGroupMessages(groupNewMessage, newMessageSelectedUsers);
    }

    return (
        <div>
            <div className="modal fade modal-update" id="messageModalCenter" tabIndex="-1" role="dialog" aria-labelledby="messageModalCenterTitle" aria-hidden="true">
                <div className="modal-dialog modal-dialog-centered modal-lg" role="document">
                    <div className="modal-content">
                        <form onSubmit={(e)=>handleNewMessageBtnClick(e)}>
                            <div className="modal-header">
                                <h5 className="modal-title" id="messageModalLongTitle">New Message</h5>
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div className="modal-body">
                                <label>Users</label>
                                <Multiselect
                                    options={newMessageUsers}
                                    displayValue="username"
                                    onSearch={(data)=>handleSearch(data)}
                                    selectedValues={newMessageSelectedUsers}
                                    onSelect={setNewMessageSelectedUsers}
                                />
                                <div className="form-group">
                                    <label htmlFor="group-message">Message</label>
                                    <textarea
                                        className="form-control"
                                        id="group-message"
                                        placeholder="Enter Message ..."
                                        required
                                        onChange={(e) => setGroupNewMessage(e.target.value)}
                                        value={groupNewMessage}
                                    >
                                    </textarea>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" data-dismiss="modal">Close</button>
                                <button type="submit" className="btn btn-primary">Send</button>
                            </div>
                    	</form>
                	</div>
                </div>
            </div>
        </div>
    );
}
