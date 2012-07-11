/**
 * Search Engine Keyword Highlight (http://fucoder.com/code/se-hilite/)
 *
 * This module can be imported by any HTML page, and it would analyse the
 * referrer for search engine keywords, and then highlight those keywords on
 * the page, by wrapping them around <span class="hilite">...</span> tags.
 * Document can then define styles else where to provide visual feedbacks.
 *
 * Usage:
 *
 *   In HTML. Add the following line towards the end of the document.
 *
 *     <script type="text/javascript" src="se_hilite.js"></script>
 *
 *   In CSS, define the following style:
 *
 *     .hilite { background-color: #ff0; }
 *
 *   If Hilite.style_name_suffix is true, then define the follow styles:
 *
 *     .hilite1 { background-color: #ff0; }
 *     .hilite2 { background-color: #f0f; }
 *     .hilite3 { background-color: #0ff; }
 *     .hilite4 ...
 *
 * @author Scott Yang <http://scott.yang.id.au/>
 * @version 1.5
 */

// Configuration:
Hilite = {
    /**
     * Element ID to be highlighted. If set, then only content inside this DOM
     * element will be highlighted, otherwise everything inside document.body
     * will be searched.
     */
    elementid: 'content',
    
    /**
     * Whether we are matching an exact word. For example, searching for
     * "highlight" will only match "highlight" but not "highlighting" if exact
     * is set to true.
     */
    exact: true,

    /**
     * Maximum number of DOM nodes to test, before handing the control back to
     * the GUI thread. This prevents locking up the UI when parsing and
     * replacing inside a large document.
     */
    max_nodes: 1000,

    /**
     * Whether to automatically hilite a section of the HTML document, by
     * binding the "Hilite.hilite()" to window.onload() event. If this
     * attribute is set to false, you can still manually trigger the hilite by
     * calling Hilite.hilite() in Javascript after document has been fully
     * loaded.
     */
    onload: true,

    /**
     * Name of the style to be used. Default to 'hilite'.
     */
    style_name: 'hilite',
    
    /**
     * Whether to use different style names for different search keywords by
     * appending a number starting from 1, i.e. hilite1, hilite2, etc.
     */
    style_name_suffix: true,

    /**
     * Set it to override the document.referrer string. Used for debugging
     * only.
     */
    debug_referrer: ''
};

Hilite.search_engines = [
    ['google\\.', 'q'],                             // Google
    ['search\\.yahoo\\.', 'p'],                     // Yahoo
    ['search\\.msn\\.', 'q'],                       // MSN
    ['search\\.live\\.', 'query'],                  // MSN Live
    ['search\\.aol\\.', 'userQuery'],               // AOL
    ['ask\\.com', 'q'],                             // Ask.com
    ['altavista\\.', 'q'],                          // AltaVista
    ['feedster\\.', 'q'],                           // Feedster
    ['search\\.lycos\\.', 'q'],                     // Lycos
    ['alltheweb\\.', 'q'],                          // AllTheWeb
    ['technorati\\.com/search/([^\\?/]+)', 1],      // Technorati
    ['dogpile\\.com/info\\.dogpl/search/web/([^\\?/]+)', 1, true] // DogPile
];

/**
 * Decode the referrer string and return a list of search keywords.
 */
Hilite.decodeReferrer = function(referrer) {
    var query = null;
    var regex = new RegExp('');

    for (var i = 0; i < Hilite.search_engines.length; i ++) {
        var se = Hilite.search_engines[i];
        regex.compile('^http://(www\\.)?' + se[0], 'i');
        var match = referrer.match(regex);
        if (match) {
            var result;
            if (isNaN(se[1])) {
                result = Hilite.decodeReferrerQS(referrer, se[1]);
            } else {
                result = match[se[1] + 1];
            }
            if (result) {
                result = decodeURIComponent(result);
                // XXX: DogPile's URI requires decoding twice.
                if (se.length > 2 && se[2])
                    result = decodeURIComponent(result);
                result = result.replace(/\'|"/g, '');
                result = result.split(/[\s,\+\.]+/);
                return result;
            }
            break;
        }
    }
    return null;
};

Hilite.decodeReferrerQS = function(referrer, match) {
    var idx = referrer.indexOf('?');
    var idx2;
    if (idx >= 0) {
        var qs = new String(referrer.substring(idx + 1));
        idx  = 0;
        idx2 = 0;
        while ((idx >= 0) && ((idx2 = qs.indexOf('=', idx)) >= 0)) {
            var key, val;
            key = qs.substring(idx, idx2);
            idx = qs.indexOf('&', idx2) + 1;
            if (key == match) {
                if (idx <= 0) {
                    return qs.substring(idx2+1);
                } else {
                    return qs.substring(idx2+1, idx - 1);
                }
            }
            else if (idx <=0) {
                return null;
            }
        }
    }
    return null;
};

/**
 * Highlight a DOM element with a list of keywords.
 */
Hilite.hiliteElement = function(elm, query) {
    if (!query || elm.childNodes.length == 0)
	return;

    var qre = new Array();
    for (var i = 0; i < query.length; i ++) {
        query[i] = query[i].toLowerCase();
        if (Hilite.exact)
            qre.push('\\b'+query[i]+'\\b');
        else
            qre.push(query[i]);
    }

    qre = new RegExp(qre.join("|"), "i");

    var stylemapper = {};
    for (var i = 0; i < query.length; i ++) {
        if (Hilite.style_name_suffix)
            stylemapper[query[i]] = Hilite.style_name+(i+1);
        else
            stylemapper[query[i]] = Hilite.style_name;
    }

    var textproc = function(node) {
        var match = qre.exec(node.data);
        if (match) {
            var val = match[0];
            var k = '';
            var node2 = node.splitText(match.index);
            var node3 = node2.splitText(val.length);
            var span = node.ownerDocument.createElement('SPAN');
            node.parentNode.replaceChild(span, node2);
            span.className = stylemapper[val.toLowerCase()];
            span.appendChild(node2);
            return span;
        } else {
            return node;
        }
    };
    Hilite.walkElements(elm.childNodes[0], 1, textproc);
};

/**
 * Highlight a HTML document using keywords extracted from document.referrer.
 * This is the main function to be called to perform search engine highlight
 * on a document.
 *
 * Currently it would check for DOM element 'content', element 'container' and
 * then document.body in that order, so it only highlights appropriate section
 * on WordPress and Movable Type pages.
 */
Hilite.hilite = function() {
    // If 'debug_referrer' then we will use that as our referrer string
    // instead.
    var q = Hilite.debug_referrer ? Hilite.debug_referrer : document.referrer;
    var e = null;
    q = Hilite.decodeReferrer(q);
    if (q && ((Hilite.elementid && 
               (e = document.getElementById(Hilite.elementid))) || 
              (e = document.body)))
    {
	Hilite.hiliteElement(e, q);
    }
};

Hilite.walkElements = function(node, depth, textproc) {
    var skipre = /^(script|style|textarea)/i;
    var count = 0;
    while (node && depth > 0) {
        count ++;
        if (count >= Hilite.max_nodes) {
            var handler = function() {
                Hilite.walkElements(node, depth, textproc);
            };
            setTimeout(handler, 50);
            return;
        }

        if (node.nodeType == 1) { // ELEMENT_NODE
            if (!skipre.test(node.tagName) && node.childNodes.length > 0) {
                node = node.childNodes[0];
                depth ++;
                continue;
            }
        } else if (node.nodeType == 3) { // TEXT_NODE
            node = textproc(node);
        }

        if (node.nextSibling) {
            node = node.nextSibling;
        } else {
            while (depth > 0) {
                node = node.parentNode;
                depth --;
                if (node.nextSibling) {
                    node = node.nextSibling;
                    break;
                }
            }
        }
    }
};

// Trigger the highlight using the onload handler.
if (Hilite.onload) {
    if (window.attachEvent) {
        window.attachEvent('onload', Hilite.hilite);
    } else if (window.addEventListener) {
        window.addEventListener('load', Hilite.hilite, false);
    } else {
        var __onload = window.onload;
        window.onload = function() {
            Hilite.hilite();
            __onload();
        };
    }
}
