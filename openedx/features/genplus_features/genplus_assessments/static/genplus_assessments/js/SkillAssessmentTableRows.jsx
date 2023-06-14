import React from 'react';
import { Button } from '@edx/paragon';
import BlockBrowserContainer from 'BlockBrowser/components/BlockBrowser/BlockBrowserContainer';

function SkillAssessmentTableRows(props) {
    const {
        rowsData,
        deleteTableRows,
        unitKeys,
        handleSelectIntro,
        handleSelectOutro,
        handleIntroToggleDropdown,
        handleOutroToggleDropdown,
        hideIntroDropdown,
        hideOutroDropdown,
        onSelectBlock
    } = props;
    return(
        rowsData.map((data, index)=>{
            const {
                selectedIntro,
                selectedOutro,
                selectedIntroBlock,
                selectedOutroBlock,
                showIntroDropdown,
                showOutroDropdown
            } = data;
            return(
                <tr key={index}>
                <td>
                    <select
                    value={selectedIntro}
                    onChange={(event) => handleSelectIntro(index, event)}
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
                    <Button onClick={()=>handleIntroToggleDropdown(index)} label={gettext('Select Intro Problem')} />
                    <span>{selectedIntroBlock}</span>
                    {
                        showIntroDropdown && selectedIntro !== "" &&
                        <BlockBrowserContainer
                        onSelectBlock={(blockId) => {
                            onSelectBlock(blockId);
                            hideIntroDropdown(index, blockId);
                        }}
                        />
                    }
                </div>
                </td>
                <td>
                    <select
                        value={selectedOutro}
                        onChange={(event) => handleSelectOutro(index, event)}
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
                    <Button onClick={()=>handleOutroToggleDropdown(index)} label={gettext('Select Outro Problem')} />
                    <span>{selectedOutroBlock}</span>
                    {
                        showOutroDropdown && selectedOutro !== "" &&
                        <BlockBrowserContainer
                        onSelectBlock={(blockId) => {
                            onSelectBlock(blockId);
                            hideOutroDropdown(index, blockId);
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
export default SkillAssessmentTableRows;
