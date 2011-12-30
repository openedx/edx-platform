from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import loader, Context
from django.db.models.fields.files import FieldFile
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required

from settings import *
from models import Article, ArticleAttachment, get_attachment_filepath
from views import not_found, check_permissions, get_url_path, fetch_from_url

import os
from simplewiki.settings import WIKI_ALLOW_ANON_ATTACHMENTS


def add_attachment(request, wiki_url):

    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err
    
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err
    
    if not WIKI_ALLOW_ATTACHMENTS or (not WIKI_ALLOW_ANON_ATTACHMENTS and request.user.is_anonymous()):
        return HttpResponseForbidden()

    if request.method == 'POST':
        if request.FILES.__contains__('attachment'):            
            attachment = ArticleAttachment()
            if not request.user.is_anonymous():
                attachment.uploaded_by = request.user
            attachment.article = article
 
            file = request.FILES['attachment']
            file_rel_path = get_attachment_filepath(attachment, file.name)
            chunk_size = request.upload_handlers[0].chunk_size

            filefield = FieldFile(attachment, attachment.file, file_rel_path)
            attachment.file = filefield
            
            file_path = WIKI_ATTACHMENTS_ROOT + attachment.file.name

            if not request.POST.__contains__('overwrite') and os.path.exists(file_path):
                c = Context({'overwrite_warning' : True,
                             'wiki_article': article,
                             'filename': file.name})
                t = loader.get_template('simplewiki_updateprogressbar.html')
                return HttpResponse(t.render(c))

            if file.size > WIKI_ATTACHMENTS_MAX:
                c = Context({'too_big' : True,
                             'max_size': WIKI_ATTACHMENTS_MAX,
                             'wiki_article': article,
                             'file': file})
                t = loader.get_template('simplewiki_updateprogressbar.html')
                return HttpResponse(t.render(c))
                
            def get_extension(fname):
                return attachment.file.name.split('.')[-2]
            if WIKI_ATTACHMENTS_ALLOWED_EXTENSIONS and not \
               get_extension(attachment.file.name) in WIKI_ATTACHMENTS_ALLOWED_EXTENSIONS:
                c = Context({'extension_err' : True,
                             'extensions': WIKI_ATTACHMENTS_ALLOWED_EXTENSIONS,
                             'wiki_article': article,
                             'file': file})
                t = loader.get_template('simplewiki_updateprogressbar.html')
                return HttpResponse(t.render(c))

            # Remove existing attachments
            # TODO: Move this until AFTER having removed file.
            # Current problem is that Django's FileField delete() method
            # automatically deletes files
            for a in article.attachments():
                if file_rel_path == a.file.name:
                    a.delete()
            def receive_file():
                destination = open(file_path, 'wb+')
                size = file.size
                cnt = 0
                c = Context({'started' : True,})
                t = loader.get_template('simplewiki_updateprogressbar.html')
                yield t.render(c)
                for chunk in file.chunks():
                    cnt += 1
                    destination.write(chunk)
                    c = Context({'progress_width' : (cnt*chunk_size) / size,
                                 'wiki_article': article,})
                    t = loader.get_template('simplewiki_updateprogressbar.html')
                    yield t.render(c)
                c = Context({'finished' : True,
                             'wiki_article': article,})
                t = loader.get_template('simplewiki_updateprogressbar.html')
                destination.close()
                attachment.save()
                yield t.render(c)

            return HttpResponse(receive_file())

    return HttpResponse('')

# Taken from http://www.djangosnippets.org/snippets/365/
def send_file(request, filepath):
    """                                                                         
    Send a file through Django without loading the whole file into              
    memory at once. The FileWrapper will turn the file object into an           
    iterator for chunks of 8KB.                                                 
    """
    filename =  filepath
    wrapper = FileWrapper(file(filename))
    response = HttpResponse(wrapper, content_type='text/plain')
    response['Content-Length'] = os.path.getsize(filename)
    return response

def view_attachment(request, wiki_url, file_name):
    
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err
    
    perm_err = check_permissions(request, article, check_read=True)
    if perm_err:
        return perm_err
    
    attachment = None
    for a in article.attachments():
        if get_attachment_filepath(a, file_name) == a.file.name:
            attachment = a
    
    if attachment:
        filepath = WIKI_ATTACHMENTS_ROOT + attachment.file.name
        if os.path.exists(filepath):
            return send_file(request, filepath)

    raise Http404()

####################
# LOGIN PROTECTION #
####################

if WIKI_REQUIRE_LOGIN_VIEW:
    view_attachment = login_required(view_attachment)
    
if WIKI_REQUIRE_LOGIN_EDIT or not WIKI_ALLOW_ANON_ATTACHMENTS:
    add_attachment  = login_required(add_attachment)
