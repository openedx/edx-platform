# -*- coding: utf-8 -*-
from django.conf import settings as settings
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from mitxmako.shortcuts import render_to_response

from courseware.courses import get_opt_course_with_access
from courseware.access import has_access
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore

from models import Revision, Article, Namespace, CreateArticleForm, RevisionFormWithTitle, RevisionForm
import wiki_settings


def wiki_reverse(wiki_page, article=None, course=None, namespace=None, args=[], kwargs={}):
    kwargs = dict(kwargs)  # TODO: Figure out why if I don't do this kwargs sometimes contains {'article_path'}
    if not 'course_id' in kwargs and course:
        kwargs['course_id'] = course.id
    if not 'article_path' in kwargs and article:
        kwargs['article_path'] = article.get_path()
    if not 'namespace' in kwargs and namespace:
        kwargs['namespace'] = namespace
    return reverse(wiki_page, kwargs=kwargs, args=args)


def update_template_dictionary(dictionary, request=None, course=None, article=None, revision=None):
    if article:
        dictionary['wiki_article'] = article
        dictionary['wiki_title'] = article.title  # TODO: What is the title when viewing the article in a course?
        if not course and 'namespace' not in dictionary:
            dictionary['namespace'] = article.namespace.name

    if course:
        dictionary['course'] = course
        if 'namespace' not in dictionary:
            dictionary['namespace'] = course.wiki_namespace
    else:
        dictionary['course'] = None

    if revision:
        dictionary['wiki_article_revision'] = revision
        dictionary['wiki_current_revision_deleted'] = not (revision.deleted == 0)

    if request:
        dictionary.update(csrf(request))

    if request and course:
        dictionary['staff_access'] = has_access(request.user, course, 'staff')
    else:
        dictionary['staff_access'] = False

def view(request, article_path, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, article_path, course)
    if err:
        return err

    perm_err = check_permissions(request, article, course, check_read=True, check_deleted=True)
    if perm_err:
        return perm_err

    d = {}
    update_template_dictionary(d, request, course, article, article.current_revision)
    return render_to_response('simplewiki/simplewiki_view.html', d)


def view_revision(request, revision_number, article_path, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, article_path, course)
    if err:
        return err

    try:
        revision = Revision.objects.get(counter=int(revision_number), article=article)
    except:
        d = {'wiki_err_norevision': revision_number}
        update_template_dictionary(d, request, course, article)
        return render_to_response('simplewiki/simplewiki_error.html', d)

    perm_err = check_permissions(request, article, course, check_read=True, check_deleted=True, revision=revision)
    if perm_err:
        return perm_err

    d = {}
    update_template_dictionary(d, request, course, article, revision)

    return render_to_response('simplewiki/simplewiki_view.html', d)


def root_redirect(request, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    #TODO: Add a default namespace to settings.
    namespace = course.wiki_namespace if course else "edX"

    try:
        root = Article.get_root(namespace)
        return HttpResponseRedirect(reverse('wiki_view', kwargs={'course_id': course_id, 'article_path': root.get_path()}))
    except:
        # If the root is not found, we probably are loading this class for the first time
        # We should make sure the namespace exists so the root article can be created.
        Namespace.ensure_namespace(namespace)

        err = not_found(request, namespace + '/', course)
        return err


def create(request, article_path, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    article_path_components = article_path.split('/')

    # Ensure the namespace exists
    if not len(article_path_components) >= 1 or len(article_path_components[0]) == 0:
        d = {'wiki_err_no_namespace': True}
        update_template_dictionary(d, request, course)
        return render_to_response('simplewiki/simplewiki_error.html', d)

    namespace = None
    try:
        namespace = Namespace.objects.get(name__exact=article_path_components[0])
    except Namespace.DoesNotExist, ValueError:
        d = {'wiki_err_bad_namespace': True}
        update_template_dictionary(d, request, course)
        return render_to_response('simplewiki/simplewiki_error.html', d)

    # See if the article already exists
    article_slug = article_path_components[1] if len(article_path_components) >= 2 else ''
    #TODO: Make sure the slug only contains legal characters (which is already done a bit by the url regex)

    try:
        existing_article = Article.objects.get(namespace=namespace, slug__exact=article_slug)
        #It already exists, so we just redirect to view the article
        return HttpResponseRedirect(wiki_reverse("wiki_view", existing_article, course))
    except Article.DoesNotExist:
        #This is good. The article doesn't exist
        pass

    #TODO: Once we have permissions for namespaces, we should check for create permissions
    #check_permissions(request, #namespace#, check_locked=False, check_write=True, check_deleted=True)

    if request.method == 'POST':
        f = CreateArticleForm(request.POST)
        if f.is_valid():
            article = Article()
            article.slug = article_slug
            if not request.user.is_anonymous():
                article.created_by = request.user
            article.title = f.cleaned_data.get('title')
            article.namespace = namespace
            a = article.save()
            new_revision = f.save(commit=False)
            if not request.user.is_anonymous():
                new_revision.revision_user = request.user
            new_revision.article = article
            new_revision.save()

            return HttpResponseRedirect(wiki_reverse("wiki_view", article, course))
    else:
        f = CreateArticleForm(initial={'title': request.GET.get('wiki_article_name', article_slug),
                                       'contents': _('Headline\n===\n\n')})

    d = {'wiki_form': f, 'create_article': True, 'namespace': namespace.name}
    update_template_dictionary(d, request, course)

    return render_to_response('simplewiki/simplewiki_edit.html', d)


def edit(request, article_path, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, article_path, course)
    if err:
        return err

    # Check write permissions
    perm_err = check_permissions(request, article, course, check_write=True, check_locked=True, check_deleted=False)
    if perm_err:
        return perm_err

    if wiki_settings.WIKI_ALLOW_TITLE_EDIT:
        EditForm = RevisionFormWithTitle
    else:
        EditForm = RevisionForm

    if request.method == 'POST':
        f = EditForm(request.POST)
        if f.is_valid():
            new_revision = f.save(commit=False)
            new_revision.article = article

            if request.POST.__contains__('delete'):
                if (article.current_revision.deleted == 1):  # This article has already been deleted. Redirect
                    return HttpResponseRedirect(wiki_reverse('wiki_view', article, course))
                new_revision.contents = ""
                new_revision.deleted = 1
            elif not new_revision.get_diff():
                return HttpResponseRedirect(wiki_reverse('wiki_view', article, course))

            if not request.user.is_anonymous():
                new_revision.revision_user = request.user
            new_revision.save()
            if wiki_settings.WIKI_ALLOW_TITLE_EDIT:
                new_revision.article.title = f.cleaned_data['title']
                new_revision.article.save()
            return HttpResponseRedirect(wiki_reverse('wiki_view', article, course))
    else:
        startContents = article.current_revision.contents if (article.current_revision.deleted == 0) else 'Headline\n===\n\n'

        f = EditForm({'contents': startContents, 'title': article.title})

    d = {'wiki_form': f}
    update_template_dictionary(d, request, course, article)
    return render_to_response('simplewiki/simplewiki_edit.html', d)


def history(request, article_path, page=1, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, article_path, course)
    if err:
        return err

    perm_err = check_permissions(request, article, course, check_read=True, check_deleted=False)
    if perm_err:
        return perm_err

    page_size = 10

    if page == None:
        page = 1
    try:
        p = int(page)
    except ValueError:
        p = 1

    history = Revision.objects.filter(article__exact=article).order_by('-counter').select_related('previous_revision__counter', 'revision_user', 'wiki_article')

    if request.method == 'POST':
        if request.POST.__contains__('revision'):  # They selected a version, but they can be either deleting or changing the version
            perm_err = check_permissions(request, article, course, check_write=True, check_locked=True)
            if perm_err:
                return perm_err

            redirectURL = wiki_reverse('wiki_view', article, course)
            try:
                r = int(request.POST['revision'])
                revision = Revision.objects.get(id=r)
                if request.POST.__contains__('change'):
                    article.current_revision = revision
                    article.save()
                elif request.POST.__contains__('view'):
                    redirectURL = wiki_reverse('wiki_view_revision', course=course,
                                    kwargs={'revision_number': revision.counter, 'article_path': article.get_path()})
                #The rese of these are admin functions
                elif request.POST.__contains__('delete') and request.user.is_superuser:
                    if (revision.deleted == 0):
                         revision.adminSetDeleted(2)
                elif request.POST.__contains__('restore') and request.user.is_superuser:
                    if (revision.deleted == 2):
                        revision.adminSetDeleted(0)
                elif request.POST.__contains__('delete_all') and request.user.is_superuser:
                    Revision.objects.filter(article__exact=article, deleted=0).update(deleted=2)
                elif request.POST.__contains__('lock_article'):
                    article.locked = not article.locked
                    article.save()
            except Exception as e:
                print str(e)
                pass
            finally:
                return HttpResponseRedirect(redirectURL)
                #
                #
                # <input type="submit" name="delete" value="Delete revision"/>
                # <input type="submit" name="restore" value="Restore revision"/>
                # <input type="submit" name="delete_all" value="Delete all revisions">
                # %else:
                # <input type="submit" name="delete_article" value="Delete all revisions">
                #

    page_count = (history.count() + (page_size - 1)) / page_size
    if p > page_count:
        p = 1
    beginItem = (p - 1) * page_size

    next_page = p + 1 if page_count > p else None
    prev_page = p - 1 if p > 1 else None

    d = {'wiki_page': p,
            'wiki_next_page': next_page,
            'wiki_prev_page': prev_page,
            'wiki_history': history[beginItem:beginItem + page_size],
            'show_delete_revision': request.user.is_superuser}
    update_template_dictionary(d, request, course, article)

    return render_to_response('simplewiki/simplewiki_history.html', d)


def revision_feed(request, page=1, namespace=None, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    page_size = 10

    if page == None:
        page = 1
    try:
        p = int(page)
    except ValueError:
        p = 1

    history = Revision.objects.order_by('-revision_date').select_related('revision_user', 'article', 'previous_revision')

    page_count = (history.count() + (page_size - 1)) / page_size
    if p > page_count:
        p = 1
    beginItem = (p - 1) * page_size

    next_page = p + 1 if page_count > p else None
    prev_page = p - 1 if p > 1 else None

    d = {'wiki_page': p,
            'wiki_next_page': next_page,
            'wiki_prev_page': prev_page,
            'wiki_history': history[beginItem:beginItem + page_size],
            'show_delete_revision': request.user.is_superuser,
            'namespace': namespace}
    update_template_dictionary(d, request, course)

    return render_to_response('simplewiki/simplewiki_revision_feed.html', d)


def search_articles(request, namespace=None, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    # blampe: We should check for the presence of other popular django search
    # apps and use those if possible. Only fall back on this as a last resort.
    # Adding some context to results (eg where matches were) would also be nice.

    # todo: maybe do some perm checking here

    if request.method == 'GET':
        querystring = request.GET.get('value', '').strip()
    else:
        querystring = ""

    results = Article.objects.all()
    if namespace:
        results = results.filter(namespace__name__exact=namespace)

    if request.user.is_superuser:
        results = results.order_by('current_revision__deleted')
    else:
        results = results.filter(current_revision__deleted=0)

    if querystring:
        for queryword in querystring.split():
            # Basic negation is as fancy as we get right now
            if queryword[0] == '-' and len(queryword) > 1:
                results._search = lambda x: results.exclude(x)
                queryword = queryword[1:]
            else:
                results._search = lambda x: results.filter(x)

            results = results._search(Q(current_revision__contents__icontains=queryword) | \
                                      Q(title__icontains=queryword))

    results = results.select_related('current_revision__deleted', 'namespace')

    results = sorted(results, key=lambda article: (article.current_revision.deleted, article.get_path().lower()))

    if len(results) == 1 and querystring:
        return HttpResponseRedirect(wiki_reverse('wiki_view', article=results[0], course=course))
    else:
        d = {'wiki_search_results': results,
                'wiki_search_query': querystring,
                'namespace': namespace}
        update_template_dictionary(d, request, course)
        return render_to_response('simplewiki/simplewiki_searchresults.html', d)


def search_add_related(request, course_id, slug, namespace):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, slug, namespace if namespace else course_id)
    if err:
        return err

    perm_err = check_permissions(request, article, course, check_read=True)
    if perm_err:
        return perm_err

    search_string = request.GET.get('query', None)
    self_pk = request.GET.get('self', None)
    if search_string:
        results = []
        related = Article.objects.filter(title__istartswith=search_string)
        others = article.related.all()
        if self_pk:
            related = related.exclude(pk=self_pk)
        if others:
            related = related.exclude(related__in=others)
        related = related.order_by('title')[:10]
        for item in related:
            results.append({'id': str(item.id),
                            'value': item.title,
                            'info': item.get_url()})
    else:
        results = []

    json = simplejson.dumps({'results': results})
    return HttpResponse(json, mimetype='application/json')


def add_related(request, course_id, slug, namespace):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, slug, namespace if namespace else course_id)
    if err:
        return err

    perm_err = check_permissions(request, article, course, check_write=True, check_locked=True)
    if perm_err:
        return perm_err

    try:
        related_id = request.POST['id']
        rel = Article.objects.get(id=related_id)
        has_already = article.related.filter(id=related_id).count()
        if has_already == 0 and not rel == article:
            article.related.add(rel)
            article.save()
    except:
        pass
    finally:
        return HttpResponseRedirect(reverse('wiki_view', args=(article.get_url(),)))


def remove_related(request, course_id, namespace, slug, related_id):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    (article, err) = get_article(request, slug, namespace if namespace else course_id)

    if err:
        return err

    perm_err = check_permissions(request, article, course, check_write=True, check_locked=True)
    if perm_err:
        return perm_err

    try:
        rel_id = int(related_id)
        rel = Article.objects.get(id=rel_id)
        article.related.remove(rel)
        article.save()
    except:
        pass
    finally:
        return HttpResponseRedirect(reverse('wiki_view', args=(article.get_url(),)))


def random_article(request, course_id=None):
    course = get_opt_course_with_access(request.user, course_id, 'load')

    from random import randint
    num_arts = Article.objects.count()
    article = Article.objects.all()[randint(0, num_arts - 1)]
    return HttpResponseRedirect(wiki_reverse('wiki_view', article, course))


def not_found(request, article_path, course):
    """Generate a NOT FOUND message for some URL"""
    d = {'wiki_err_notfound': True,
         'article_path': article_path,
         'namespace': course.wiki_namespace}
    update_template_dictionary(d, request, course)
    return render_to_response('simplewiki/simplewiki_error.html', d)


def get_article(request, article_path, course):
    err = None
    article = None

    try:
        article = Article.get_article(article_path)
    except Article.DoesNotExist, ValueError:
        err = not_found(request, article_path, course)

    return (article, err)


def check_permissions(request, article, course, check_read=False, check_write=False, check_locked=False, check_deleted=False, revision=None):
    read_err = check_read and not article.can_read(request.user)

    write_err = check_write and not article.can_write(request.user)

    locked_err = check_locked and article.locked

    if revision is None:
        revision = article.current_revision
    deleted_err = check_deleted and not (revision.deleted == 0)
    if (request.user.is_superuser):
        deleted_err = False
        locked_err = False

    if read_err or write_err or locked_err or deleted_err:
        d = {'wiki_article': article,
                'wiki_err_noread': read_err,
                'wiki_err_nowrite': write_err,
                'wiki_err_locked': locked_err,
                'wiki_err_deleted': deleted_err, }
        update_template_dictionary(d, request, course)
        # TODO: Make this a little less jarring by just displaying an error
        #       on the current page? (no such redirect happens for an anon upload yet)
        # benjaoming: I think this is the nicest way of displaying an error, but
        # these errors shouldn't occur, but rather be prevented on the other pages.
        return render_to_response('simplewiki/simplewiki_error.html', d)
    else:
        return None

####################
# LOGIN PROTECTION #
####################


if wiki_settings.WIKI_REQUIRE_LOGIN_VIEW:
    view = login_required(view)
    history = login_required(history)
    search_articles = login_required(search_articles)
    root_redirect = login_required(root_redirect)
    revision_feed = login_required(revision_feed)
    random_article = login_required(random_article)
    search_add_related = login_required(search_add_related)
    not_found = login_required(not_found)
    view_revision = login_required(view_revision)

if wiki_settings.WIKI_REQUIRE_LOGIN_EDIT:
    create = login_required(create)
    edit = login_required(edit)
    add_related = login_required(add_related)
    remove_related = login_required(remove_related)

if wiki_settings.WIKI_CONTEXT_PREPROCESSORS:
    settings.TEMPLATE_CONTEXT_PROCESSORS += wiki_settings.WIKI_CONTEXT_PREPROCESSORS
