import {
    Component,
    render,
    html,
    useReducer,
    useEffect,
    useState,
    registerPreactXBlock,
} from 'xblock2-client-v0';

console.log("✅ Initializing...");

function HTMLBlock(props) {
    const [count, add] = useReducer((a, b) => a + b, 0);

    return html`
        <p>
            This XBlock has no isolation from the parent page.
            It is on the same domain (${document.domain}), can access cookies, and is affected by the CSS/JS of the LMS.
        </p>
        <button onClick=${() => add(-1)}>Decrement</button>
        <input readonly size="4" value=${count} />
        <button onClick=${() => add(1)}>Increment</button>
        <br/>
        <p>Here is <a href="#"> a link </a>.</p>
        <p><code><pre>${JSON.stringify(props, undefined, 2)}</pre></code></p>
    `;
}

registerPreactXBlock(HTMLBlock, 'html', {shadow: false});
