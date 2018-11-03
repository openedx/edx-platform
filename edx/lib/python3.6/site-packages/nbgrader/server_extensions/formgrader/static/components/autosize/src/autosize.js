function assign(ta, {setOverflowX = true, setOverflowY = true} = {}) {
	if (!ta || !ta.nodeName || ta.nodeName !== 'TEXTAREA' || ta.hasAttribute('data-autosize-on')) return;

	let heightOffset = null;
	let overflowY = 'hidden';

	function init() {
		const style = window.getComputedStyle(ta, null);

		if (style.resize === 'vertical') {
			ta.style.resize = 'none';
		} else if (style.resize === 'both') {
			ta.style.resize = 'horizontal';
		}

		if (style.boxSizing === 'content-box') {
			heightOffset = -(parseFloat(style.paddingTop)+parseFloat(style.paddingBottom));
		} else {
			heightOffset = parseFloat(style.borderTopWidth)+parseFloat(style.borderBottomWidth);
		}

		update();
	}

	function changeOverflow(value) {
		{
			// Chrome/Safari-specific fix:
			// When the textarea y-overflow is hidden, Chrome/Safari do not reflow the text to account for the space
			// made available by removing the scrollbar. The following forces the necessary text reflow.
			const width = ta.style.width;
			ta.style.width = '0px';
			// Force reflow:
			/* jshint ignore:start */
			ta.offsetWidth;
			/* jshint ignore:end */
			ta.style.width = width;
		}

		overflowY = value;

		if (setOverflowY) {
			ta.style.overflowY = value;
		}

		resize();
	}

	function resize() {
		const htmlTop = window.pageYOffset;
		const bodyTop = document.body.scrollTop;
		const originalHeight = ta.style.height;

		ta.style.height = 'auto';

		let endHeight = ta.scrollHeight+heightOffset;

		if (ta.scrollHeight === 0) {
			// If the scrollHeight is 0, then the element probably has display:none or is detached from the DOM.
			ta.style.height = originalHeight;
			return;
		}

		ta.style.height = endHeight+'px';

		// prevents scroll-position jumping
		document.documentElement.scrollTop = htmlTop;
		document.body.scrollTop = bodyTop;
	}

	function update() {
		const startHeight = ta.style.height;
		
		resize();

		const style = window.getComputedStyle(ta, null);

		if (style.height !== ta.style.height) {
			if (overflowY !== 'visible') {
				changeOverflow('visible');
			}
		} else {
			if (overflowY !== 'hidden') {
				changeOverflow('hidden');
			}
		}

		if (startHeight !== ta.style.height) {
			const evt = document.createEvent('Event');
			evt.initEvent('autosize:resized', true, false);
			ta.dispatchEvent(evt);
		}
	}

	const destroy = style => {
		window.removeEventListener('resize', update);
		ta.removeEventListener('input', update);
		ta.removeEventListener('keyup', update);
		ta.removeAttribute('data-autosize-on');
		ta.removeEventListener('autosize:destroy', destroy);

		Object.keys(style).forEach(key => {
			ta.style[key] = style[key];
		});
	}.bind(ta, {
		height: ta.style.height,
		resize: ta.style.resize,
		overflowY: ta.style.overflowY,
		overflowX: ta.style.overflowX,
		wordWrap: ta.style.wordWrap,
	});

	ta.addEventListener('autosize:destroy', destroy);

	// IE9 does not fire onpropertychange or oninput for deletions,
	// so binding to onkeyup to catch most of those events.
	// There is no way that I know of to detect something like 'cut' in IE9.
	if ('onpropertychange' in ta && 'oninput' in ta) {
		ta.addEventListener('keyup', update);
	}

	window.addEventListener('resize', update);
	ta.addEventListener('input', update);
	ta.addEventListener('autosize:update', update);
	ta.setAttribute('data-autosize-on', true);

	if (setOverflowY) {
		ta.style.overflowY = 'hidden';
	}
	if (setOverflowX) {
		ta.style.overflowX = 'hidden';
		ta.style.wordWrap = 'break-word';
	}

	init();
}

function destroy(ta) {
	if (!(ta && ta.nodeName && ta.nodeName === 'TEXTAREA')) return;
	const evt = document.createEvent('Event');
	evt.initEvent('autosize:destroy', true, false);
	ta.dispatchEvent(evt);
}

function update(ta) {
	if (!(ta && ta.nodeName && ta.nodeName === 'TEXTAREA')) return;
	const evt = document.createEvent('Event');
	evt.initEvent('autosize:update', true, false);
	ta.dispatchEvent(evt);
}

let autosize = null;

// Do nothing in Node.js environment and IE8 (or lower)
if (typeof window === 'undefined' || typeof window.getComputedStyle !== 'function') {
	autosize = el => el;
	autosize.destroy = el => el;
	autosize.update = el => el;
} else {
	autosize = (el, options) => {
		if (el) {
			Array.prototype.forEach.call(el.length ? el : [el], x => assign(x, options));
		}
		return el;
	};
	autosize.destroy = el => {
		if (el) {
			Array.prototype.forEach.call(el.length ? el : [el], destroy);
		}
		return el;
	};
	autosize.update = el => {
		if (el) {
			Array.prototype.forEach.call(el.length ? el : [el], update);
		}
		return el;
	};
}

export default autosize;
