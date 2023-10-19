const sequenceId = document.querySelector('.xblock-editor').getAttribute('data-locator')
const subTextElement = document.querySelector('#sub-text')
const btnSubmit = document.querySelector('#sub-text-submit')
const btnSave = document.querySelector('.action-save')
const inputTimeUnit = document.querySelector('.time_unit')
const titleModal = document.querySelector('#modal-window-title')
const title = titleModal.textContent.trim()

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

async function getDataInputTime (){
    const url = '/api/course_unit_time/' + sequenceId
    try {
        const data = await fetchData(url)

        inputTimeUnit.value = data.total
    } catch (error) {
        console.log(error)
    } 
}
getDataInputTime()

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
        if (textareaValue.length > 0){
            const response = await fetch('/api/set_sub_text', {
                method : 'POST',
                headers: {
                'Content-Type': 'application/json',
                 'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ subtext: textareaValue  , suquence_id: sequenceId , courseId:courseId , title:title}) 
            })
        }

        if(inputTimeUnit.value.length > 0){
            const response_time_unit = await fetch('/api/set_course_unit_time' ,{
                method : 'POST',
                headers: {
                'Content-Type': 'application/json',
                 'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ total: inputTimeUnit.value  , suquence_id: sequenceId , courseId:courseId , title:title}) 
            })
        }
        
        
    }
    catch(error){
        console.log(error)
    }
   
})