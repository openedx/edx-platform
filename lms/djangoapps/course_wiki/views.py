import logging
import re

from django.shortcuts import redirect
from wiki.core.exceptions import NoRootURL
from wiki.models import URLPath, Article

from courseware.courses import check_course

log = logging.getLogger(__name__)

def root_create(request):
    
    """
    In the edX wiki, we don't show the root_create view. Instead, we
    just create the root automatically if it doesn't exist.
    """
    root = get_or_create_root()
    return redirect('wiki:get', path=root.path)


def course_wiki_redirect(request, course_id):
    """
    This redirects to whatever page on the wiki that the course designates
    as it's home page. A course's wiki must be an article on the root (for
    example, "/6.002x") to keep things simple.
    """
    course = check_course(request.user, course_id)
    
    course_slug = course.wiki_slug
    valid_slug = True
    #TODO: Make sure this is a legal slug. No "/"'s
    if not course_slug:
        log.exception("This course is improperly configured. The slug cannot be empty.")
        valid_slug = False
    if re.match('^[-\w\.]+$', course_slug) == None:
        log.exception("This course is improperly configured. The slug can only contain letters, numbers, periods or hyphens.")
        valid_slug = False
    
    if not valid_slug:
        return redirect("wiki:get", path="")
                
    try:
        urlpath = URLPath.get_by_path(course_slug, select_related=True)
        
        results = list( Article.objects.filter( id = urlpath.article.id ) )
        if results:
            article = results[0]
        else:
            article = None
    
    except (NoRootURL, URLPath.DoesNotExist):
        # We will create it in the next block
        urlpath = None
        article = None
        
    if not article:
        # create it
        root = get_or_create_root()
        
        if urlpath:
            # Somehow we got a urlpath without an article. Just delete it and
            # recerate it.
            urlpath.delete()
        
        urlpath = URLPath.create_article(
            root,
            course_slug,
            title=course.title,
            content="This is the wiki for " + course.title + ".",
            user_message="Course page automatically created.",
            user=None,
            ip_address=None,
            article_kwargs={'owner': None,
                            'group': None,
                            'group_read': True,
                            'group_write': True,
                            'other_read': True,
                            'other_write': True,
                            })
        
    return redirect("wiki:get", path=urlpath.path)
    

def get_or_create_root():
    """
    Returns the root article, or creates it if it doesn't exist.
    """
    try:
        root = URLPath.root()
        if not root.article:
            root.delete()
            raise NoRootURL
        return root
    except NoRootURL:
        pass
    
    starting_content = "\n".join((
    "Welcome to the edX Wiki",
    "===",
    "Visit a course wiki to add an article."))
    
    root = URLPath.create_root(title="edX Wiki",
                        content=starting_content)
    return root
    
