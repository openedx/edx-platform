import React from 'react';
import BlockBrowserContainer from 'BlockBrowser/components/BlockBrowser/BlockBrowserContainer';

function TableRows(props) {
    const {
        rowsData,
        deleteTableRows,
        unitKeys,
        showDropdown,
        handleSelectIntro,
        handleSelectOutro,
        handleToggleDropdown,
        hideDropdown
    } = props;
    return(
        rowsData.map((data, index)=>{
            const {selectedIntro, selectedOutro} = data;
            return(
                <tr key={index}>
                <td>
                    <select
                    value={selectedIntro}
                    onChange={handleSelectIntro}
                    className="form-control"
                    id={"select-intro-" + index}
                    >
                    <option value="">Select Intro Unit</option>
                    {
                        unitKeys.map((unitKey, index) => (
                            <option key={index} value={unitKey}>{unitKey}</option>
                        ))
                    }
                    </select>
                </td>
                <td>
                <div className="problem-browser">
                    <Button onClick={handleToggleDropdown} label={gettext('Select Intro Problem')} />
                    <span>Intro</span>
                    {
                        showDropdown &&
                        <BlockBrowserContainer
                        onSelectBlock={(blockId) => {
                            hideDropdown();
                            onSelectBlock(blockId);
                        }}
                        />
                    }
                </div>
                </td>
                <td>
                    <select
                        value={selectedOutro}
                        onChange={handleSelectOutro}
                        className="form-control"
                        id={"select-outro-" + index}
                        >
                        <option value="">Select Outro Unit</option>
                        {
                            unitKeys.map((unitKey, index) => (
                                <option key={index} value={unitKey}>{unitKey}</option>
                            ))
                        }
                    </select>
                </td>
                <td>
                <div className="problem-browser">
                    <Button onClick={handleToggleDropdown} label={gettext('Select Outro Problem')} />
                    <span>Outro</span>
                    {
                        showDropdown &&
                        <BlockBrowserContainer
                        onSelectBlock={(blockId) => {
                            hideDropdown();
                            onSelectBlock(blockId);
                        }}
                        />
                    }
                </div>
                </td>
                <td><button className="btn btn-outline-danger" onClick={()=>(deleteTableRows(index))}>x</button></td>
            </tr>
            )
        })

    )

}
export default TableRows;
