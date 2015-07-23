//use the !rel flag to load file relative to this module or to baseUrl
define(['image!./software_engineer.png!rel'], function(engineer){

    return {
        init : function(wrapper){
            engineer.style.display = 'block';
            wrapper.appendChild(engineer);
        }
    };

});
