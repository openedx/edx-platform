// @ts-check
import {
    html,
    useFields,
    registerPreactXBlock,
} from 'xblock2-client-v0';

function HTMLBlock(props) {
    const {
        data,
    } = useFields(props);

    return html`
        <div dangerouslySetInnerHTML=${{__html: data}}></div>
    `;
}

registerPreactXBlock(HTMLBlock, 'html', {shadow: false});
