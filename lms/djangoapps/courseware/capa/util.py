def contextualize_text(text, context): # private
    ''' Takes a string with variables. E.g. $a+$b. 
    Does a substitution of those variables from the context '''
    if not text: return text
    for key in sorted(context, lambda x,y:cmp(len(y),len(x))):
        text=text.replace('$'+key, str(context[key]))
    return text
