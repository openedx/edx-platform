const sequenceId = document.querySelector('.xblock-editor').getAttribute('data-locator')
const subTextElement = document.querySelector('#sub-text')
const btnSubmit = document.querySelector('#sub-text-submit')
const btnSave = document.querySelector('.action-save')


const fetchData = async (url)=>{
    try {
        const response = await fetch (url)
        if(!response.ok){
            throw new Error('error')
        }
        const data =await response.json()
       
        return data
    } catch (error) {
        console.log(error)
    }
}




async function getDataSubText() {
    const url_sub_text = '/api/sub_text/' + sequenceId
    try {
      const dataSubText = await fetchData(url_sub_text);
     
      subTextElement.value = dataSubText.sub_text
    } catch (error) {
      
      console.error(error);
    }
  }
  
getDataSubText();



function getCookie(cookieName) {
const name = cookieName + "=";
const decodedCookie = decodeURIComponent(document.cookie);
const cookieArray = decodedCookie.split(';');
for (let i = 0; i < cookieArray.length; i++) {
    let cookie = cookieArray[i];
    while (cookie.charAt(0) === ' ') {
    cookie = cookie.substring(1);
    }
    if (cookie.indexOf(name) === 0) {
    return cookie.substring(name.length, cookie.length);
    }
}
return null; 
}



btnSave.addEventListener('click', async (e) =>{
    
     try{
        const csrftoken = getCookie('csrftoken')
        const textareaValue = subTextElement.value
        const url = window.location.href
        const parts = url.split('/')
        const courseId = parts[parts.length -1]
        const response = await fetch('/api/set_sub_text', {
            method : 'POST',
            headers: {
            'Content-Type': 'application/json',
             'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ subtext: textareaValue  , suquence_id: sequenceId , courseId:courseId}) 
        })

      
    }
    catch(error){
        console.log(error)
    }
   
})