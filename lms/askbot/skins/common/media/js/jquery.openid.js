/*
openid login boxes
*/
var providers_large = {
    google: {
        name: 'Google',
        url: 'https://www.google.com/accounts/o8/id'
    },
    yahoo: {
        name: 'Yahoo',      
        url: 'http://yahoo.com/'
    },    
    aol: {
        name: 'AOL',     
        label: 'Enter your AOL screenname.',
        url: 'http://openid.aol.com/{username}'
    },
    openid: {
        name: 'OpenID',     
        label: 'Enter your OpenID.',
        url: 'http://'
    }
};
var providers_small = {
    myopenid: {
        name: 'MyOpenID',
        label: 'Enter your MyOpenID username.',
        url: 'http://{username}.myopenid.com/'
    },
    livejournal: {
        name: 'LiveJournal',
        label: 'Enter your Livejournal username.',
        url: 'http://{username}.livejournal.com/'
    },
    flickr: {
        name: 'Flickr',        
        label: 'Enter your Flickr username.',
        url: 'http://flickr.com/{username}/'
    },
    technorati: {
        name: 'Technorati',
        label: 'Enter your Technorati username.',
        url: 'http://technorati.com/people/technorati/{username}/'
    },
    wordpress: {
        name: 'Wordpress',
        label: 'Enter your Wordpress.com username.',
        url: 'http://{username}.wordpress.com/'
    },
    blogger: {
        name: 'Blogger',
        label: 'Your Blogger account',
        url: 'http://{username}.blogspot.com/'
    },
    verisign: {
        name: 'Verisign',
        label: 'Your Verisign username',
        url: 'http://{username}.pip.verisignlabs.com/'
    },
    vidoop: {
        name: 'Vidoop',
        label: 'Your Vidoop username',
        url: 'http://{username}.myvidoop.com/'
    },
    verisign: {
        name: 'Verisign',
        label: 'Your Verisign username',
        url: 'http://{username}.pip.verisignlabs.com/'
    },
    claimid: {
        name: 'ClaimID',
        label: 'Your ClaimID username',
        url: 'http://claimid.com/{username}'
    }
};
var providers = $.extend({}, providers_large, providers_small);

var openid = {

	cookie_expires: 6*30,	// 6 months.
	cookie_name: 'openid_provider',
	cookie_path: '/',
	
	img_path: '/media/images/openid/',
	
	input_id: null,
	provider_url: null,
	
    init: function(input_id) {

        var openid_btns = $('#openid_btns');
        this.input_id = input_id;
        
        $('#openid_choice').show();
        //$('#openid_input_area').empty();
        
        // add box for each provider
        for (id in providers_large) {
           	openid_btns.append(this.getBoxHTML(providers_large[id], 'large', '.gif'));
        }
        if (providers_small) {
        	openid_btns.append('<br/>');
	        for (id in providers_small) {       
	           	openid_btns.append(this.getBoxHTML(providers_small[id], 'small', '.ico'));
	        }
        }

        var box_id = this.readCookie();
        if (box_id) {
        	this.signin(box_id, true);
        }  
    },
    getBoxHTML: function(provider, box_size, image_ext) {
            
        var box_id = provider["name"].toLowerCase();
        return '<a title="'+provider["name"]+'" href="javascript: openid.signin(\''+ box_id +'\');"' +
        		' style="background: #FFF url(' + this.img_path + box_id + image_ext+') no-repeat center center" ' + 'class="' + box_id + ' openid_' + box_size + '_btn"></a>';    
    
    },
    /* Provider image click */
    signin: function(box_id, onload) {
    	var provider = providers[box_id];
  		if (! provider) {
  			return;
  		}
		this.highlight(box_id);
		this.setCookie(box_id);
		
        $('#'+this.input_id).val(provider['url']);
        var input = $('#'+this.input_id);
        if(document.selection){
            var r = document.all.openid_url.createTextRange();
            var res = r.findText("{username}");
            if(res)
                r.select();
            
        }
        else {
            var text  = input.val();
            var searchText = "{username}";
            var posStart = text.indexOf(searchText);
            if(posStart > -1){
                input.focus();
                document.getElementById(this.input_id).setSelectionRange(posStart, posStart + searchText.length);
            }
        } 
    },

    highlight: function (box_id) {
    	// remove previous highlight.
    	var highlight = $('#openid_highlight');
    	if (highlight) {
    		highlight.replaceWith($('#openid_highlight a')[0]);
    	}
    	// add new highlight.
    	$('.'+box_id).wrap('<div id="openid_highlight"></div>');
    },
        
    setCookie: function (value) {
		var date = new Date();
		date.setTime(date.getTime()+(this.cookie_expires*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
		document.cookie = this.cookie_name+"="+value+expires+"; path=" + this.cookie_path;
    },
        
    readCookie: function () {
		var nameEQ = this.cookie_name + "=";
		var ca = document.cookie.split(';');
		for(var i=0;i < ca.length;i++) {
			var c = ca[i];
			while (c.charAt(0)==' ') c = c.substring(1,c.length);
			if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
		}
		return null;
    }
};
