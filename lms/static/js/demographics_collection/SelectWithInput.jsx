import React from 'react';

// eslint-disable-next-line import/prefer-default-export, react/function-component-definition
export const SelectWithInput = (props) => {
    const {
        selectName,
        selectId,
        selectValue,
        options,
        inputName,
        inputId,
        inputType,
        inputValue,
        selectOnChange,
        inputOnChange,
        showInput,
        inputOnBlur,
        labelText,
        disabled,
    } = props;
    return (
        <div className="d-flex flex-column pb-3">
            <label htmlFor={selectName}>{labelText}</label>
            <select
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus
                className="form-control"
                name={selectName}
                id={selectId}
                onChange={selectOnChange}
                value={selectValue}
                disabled={disabled}
            >
                {options}
            </select>
            {showInput
        && (
            <input
                className="form-control"
                aria-label={`${selectName} description field`}
                type={inputType}
                name={inputName}
                id={inputId}
                onChange={inputOnChange}
                onBlur={inputOnBlur}
                value={inputValue}
                disabled={disabled}
                maxLength={255}
            />
        )}
        </div>
    );
};
