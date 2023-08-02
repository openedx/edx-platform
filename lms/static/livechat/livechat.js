function getFormHTML() {
	const url = `${ this.host }/hf40-livechat/form.html`;
	
	return new Promise((resolve) => {
		const xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (this.readyState === 4 && this.status === 200) {
				resolve(this.responseText);
			}
		};
		xhttp.open('GET', url, true);
		xhttp.send();
	});
	// return $.get(url);
}


function callback(resolve) {

	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState === 4) {
			if (this.status === 200) {
				const json = JSON.parse(this.responseText);
				resolve(json[0].email);
				
			} else {
				resolve(null);
			}
		}
	};
	xhttp.open('GET', '/api/user/v1/accounts', true);
	xhttp.send();
	
}
function getEmail() {
	const mails=[]
	const mail=  new Promise(callback)  ;
	 mail.then((res)=>mails.push(res))
	 return mails
}


(  function(w, d, s, u) {
w.RocketChat = function(c) { w.RocketChat._.push(c) }; w.RocketChat._ = []; w.RocketChat.url = u;
var h = d.getElementsByTagName(s)[0], j = d.createElement(s);
j.async = true; j.src = 'https://test-xseries2.funix.edu.vn/livechat/rocketchat-livechat.min.js?_=201903270000';
h.parentNode.insertBefore(j, h);
})(window, document, 'script', 'https://test-xseries2.funix.edu.vn/livechat');
RocketChat(async function() {
	const email = await getEmail()
	this.registerGuest({
	token: email, // The token field is not required. If it is not passed, a new token will be generated
	name: email,
	email: email,
	
});
});
