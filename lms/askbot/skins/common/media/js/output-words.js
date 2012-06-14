/*

   @desc Word checker
    Tests the JavaScript-side i18n translation arrays for completeness
    and generates an empty template containing all the keys 
    for new translations.
    
    Is included by output-words.html.
   
   @author      Pekka Gaiser <post@pekkagaiser.com>
   @package     Part of the ASKBOT project <www.askbot.org>
   @license     Published with NO WARRANTY WHATSOEVER
                under the same license as the Askbot project.
   @version     First release, May 7th 2010

*/


function output()
 {
  
  document.write("<div class='column'><h1>Translation check</h1><table class='languages'>");
   
  var allKeys = new Array();
  
  
  for (var key in i18n) 
      {
         if(!i18n.hasOwnProperty(key)) continue; 
	     
	     for (var word in i18n[key]) 
           {
             if(!i18n[key].hasOwnProperty(word)) continue;      
            
            if (jQuery.inArray(word, allKeys) == -1)
             allKeys.push(word); 
            
           }     
      }
      
      
  // Output all keys
    for (var key in allKeys.sort())
    { 
     
     document.write("<tr><td>");
     document.write(allKeys[key]); 
     document.write("</td><td>");    
        
     // Check word in all languages
      for (var language in i18n) 
      {
         if(!i18n.hasOwnProperty(language)) continue; 
         
         if ((!i18n[language][allKeys[key]]) || (i18n[language][allKeys[key]] == ""))
          document.write("<td class='language missing'>"+language+"</td>");             
          else
          document.write("<td class='language okay' title='"+escape(i18n[language][allKeys[key]])+"'>"+language+"</td>");
          
          escape(i18n[language][key])
           
      }
      
     document.write("</tr>"); 
     
    }  
     
   document.write("</table></div><div class='column'>"); 
   
   // Translation template
   
   document.write("<h1>Template for new translation</h1>");
   document.write("<textarea style='width: 100%; height: 600px'>");
   document.write("// Note that the words ending with '/' (e.g. 'questions/') are directory names\n");
   document.write("// And need to be identical with the directory names\n");
   document.write("// in the basic server-side translation\n\n");
   
   
   document.write("var i18nXY = {\n");
   
   // Output all words
    for (var key in allKeys.sort())
    { 
       
       document.write(" '"+allKeys[key]+"': '', \n");
    
    }
   
   document.write(" 'delete_this': ''\n}"); // To prevent trailing comma
   document.write("</textarea>");
   
   document.write("</div>");
        
      
  }
  
  
