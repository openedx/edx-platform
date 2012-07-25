import difflib
import os

from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from markdown import markdown

from wiki_settings import *
from util.cache import cache


class ShouldHaveExactlyOneRootSlug(Exception):
    pass


class Namespace(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name=_('namespace'))
    # TODO: We may want to add permissions, etc later

    @classmethod
    def ensure_namespace(cls, name):
        try:
            namespace = Namespace.objects.get(name__exact=name)
        except Namespace.DoesNotExist:
            new_namespace = Namespace(name=name)
            new_namespace.save()


class Article(models.Model):
    """Wiki article referring to Revision model for actual content.
       'slug' and 'title' field should be maintained centrally, since users
       aren't allowed to change them, anyways.
    """

    title = models.CharField(max_length=512, verbose_name=_('Article title'),
                             blank=False)
    slug = models.SlugField(max_length=100, verbose_name=_('slug'),
                            help_text=_('Letters, numbers, underscore and hyphen.'),
                            blank=True)
    namespace = models.ForeignKey(Namespace, verbose_name=_('Namespace'))
    created_by = models.ForeignKey(User, verbose_name=_('Created by'), blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=1)
    modified_on = models.DateTimeField(auto_now_add=1)
    locked = models.BooleanField(default=False, verbose_name=_('Locked for editing'))
    permissions = models.ForeignKey('Permission', verbose_name=_('Permissions'),
                                    blank=True, null=True,
                                    help_text=_('Permission group'))
    current_revision = models.OneToOneField('Revision', related_name='current_rev',
                                            blank=True, null=True, editable=True)
    related = models.ManyToManyField('self', verbose_name=_('Related articles'), symmetrical=True,
                                     help_text=_('Sets a symmetrical relation other articles'),
                                     blank=True, null=True)

    def attachments(self):
        return ArticleAttachment.objects.filter(article__exact=self)

    def get_path(self):
        return self.namespace.name + "/" + self.slug

    @classmethod
    def get_article(cls, article_path):
        """
        Given an article_path like namespace/slug, this returns the article. It may raise
        a Article.DoesNotExist if no matching article is found or ValueError if the
        article_path is not constructed properly.
        """
        #TODO: Verify the path, throw a meaningful error?
        namespace, slug = article_path.split("/")
        return Article.objects.get(slug__exact=slug, namespace__name__exact=namespace)

    @classmethod
    def get_root(cls, namespace):
        """Return the root article, which should ALWAYS exist..
        except the very first time the wiki is loaded, in which
        case the user is prompted to create this article."""
        try:
            return Article.objects.filter(slug__exact="", namespace__name__exact=namespace)[0]
        except:
            raise ShouldHaveExactlyOneRootSlug()

    # @classmethod
    # def get_url_reverse(cls, path, article, return_list=[]):
    #     """Lookup a URL and return the corresponding set of articles
    #     in the path."""
    #     if path == []:
    #         return return_list + [article]
    #     # Lookup next child in path
    #     try:
    #         a = Article.objects.get(parent__exact = article, slug__exact=str(path[0]))
    #         return cls.get_url_reverse(path[1:], a, return_list+[article])
    #     except Exception, e:
    #         return None

    def can_read(self, user):
        """ Check read permissions and return True/False."""
        if user.is_superuser:
            return True
        if self.permissions:
            perms = self.permissions.can_read.all()
            return perms.count() == 0 or (user in perms)
        else:
            # TODO: We can inherit namespace permissions here
            return True

    def can_write(self, user):
        """ Check write permissions and return True/False."""
        if user.is_superuser:
            return True
        if self.permissions:
            perms = self.permissions.can_write.all()
            return perms.count() == 0 or (user in perms)
        else:
            # TODO: We can inherit namespace permissions here
            return True

    def can_write_l(self, user):
        """Check write permissions and locked status"""
        if user.is_superuser:
            return True
        return not self.locked and self.can_write(user)

    def can_attach(self, user):
        return self.can_write_l(user) and (WIKI_ALLOW_ANON_ATTACHMENTS or not user.is_anonymous())

    def __unicode__(self):
        if self.slug == '':
            return unicode(_('Root article'))
        else:
            return self.slug

    class Meta:
        unique_together = (('slug', 'namespace'),)
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')


def get_attachment_filepath(instance, filename):
    """Store file, appending new extension for added security"""
    dir_ = WIKI_ATTACHMENTS + instance.article.get_url()
    dir_ = '/'.join(filter(lambda x: x != '', dir_.split('/')))
    if not os.path.exists(WIKI_ATTACHMENTS_ROOT + dir_):
        os.makedirs(WIKI_ATTACHMENTS_ROOT + dir_)
    return dir_ + '/' + filename + '.upload'


class ArticleAttachment(models.Model):
    article = models.ForeignKey(Article, verbose_name=_('Article'))
    file = models.FileField(max_length=255, upload_to=get_attachment_filepath, verbose_name=_('Attachment'))
    uploaded_by = models.ForeignKey(User, blank=True, verbose_name=_('Uploaded by'), null=True)
    uploaded_on = models.DateTimeField(auto_now_add=True, verbose_name=_('Upload date'))

    def download_url(self):
        return reverse('wiki_view_attachment', args=(self.article.get_url(), self.filename()))

    def filename(self):
        return '.'.join(self.file.name.split('/')[-1].split('.')[:-1])

    def get_size(self):
        try:
            size = self.file.size
        except OSError:
            size = 0
        return size

    def filename(self):
        return '.'.join(self.file.name.split('/')[-1].split('.')[:-1])

    def is_image(self):
        fname = self.filename().split('.')
        if len(fname) > 1 and fname[-1].lower() in WIKI_IMAGE_EXTENSIONS:
            return True
        return False

    def get_thumb(self):
        return self.get_thumb_impl(*WIKI_IMAGE_THUMB_SIZE)

    def get_thumb_small(self):
        return self.get_thumb_impl(*WIKI_IMAGE_THUMB_SIZE_SMALL)

    def mk_thumbs(self):
        self.mk_thumb(*WIKI_IMAGE_THUMB_SIZE, **{'force': True})
        self.mk_thumb(*WIKI_IMAGE_THUMB_SIZE_SMALL, **{'force': True})

    def mk_thumb(self, width, height, force=False):
        """Requires Python Imaging Library (PIL)"""
        if not self.get_size():
            return False

        if not self.is_image():
            return False

        base_path = os.path.dirname(self.file.path)
        orig_name = self.filename().split('.')
        thumb_filename = "%s__thumb__%d_%d.%s" % ('.'.join(orig_name[:-1]), width, height, orig_name[-1])
        thumb_filepath = "%s%s%s" % (base_path, os.sep, thumb_filename)

        if force or not os.path.exists(thumb_filepath):
            try:
                import Image
                img = Image.open(self.file.path)
                img.thumbnail((width, height), Image.ANTIALIAS)
                img.save(thumb_filepath)
            except IOError:
                return False

        return True

    def get_thumb_impl(self, width, height):
        """Requires Python Imaging Library (PIL)"""

        if not self.get_size():
            return False

        if not self.is_image():
            return False

        self.mk_thumb(width, height)

        orig_name = self.filename().split('.')
        thumb_filename = "%s__thumb__%d_%d.%s" % ('.'.join(orig_name[:-1]), width, height, orig_name[-1])
        thumb_url = settings.MEDIA_URL + WIKI_ATTACHMENTS + self.article.get_url() + '/' + thumb_filename

        return thumb_url

    def __unicode__(self):
        return self.filename()


class Revision(models.Model):

    article = models.ForeignKey(Article, verbose_name=_('Article'))
    revision_text = models.CharField(max_length=255, blank=True, null=True,
                                     verbose_name=_('Description of change'))
    revision_user = models.ForeignKey(User, verbose_name=_('Modified by'),
                                      blank=True, null=True, related_name='wiki_revision_user')
    revision_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Revision date'))
    contents = models.TextField(verbose_name=_('Contents (Use MarkDown format)'))
    contents_parsed = models.TextField(editable=False, blank=True, null=True)
    counter = models.IntegerField(verbose_name=_('Revision#'), default=1, editable=False)
    previous_revision = models.ForeignKey('self', blank=True, null=True, editable=False)

    # Deleted has three values. 0 is normal, non-deleted. 1 is if it was deleted by a normal user. It should
    # be a NEW revision, so that it appears in the history. 2 is a special flag that can be applied or removed
    # from a normal revision. It means it has been admin-deleted, and can only been seen by an admin. It doesn't
    # show up in the history.
    deleted = models.IntegerField(verbose_name=_('Deleted group'), default=0)

    def get_user(self):
        return self.revision_user if self.revision_user else _('Anonymous')

    # Called after the deleted fied has been changed (between 0 and 2). This bypasses the normal checks put in
    # save that update the revision or reject the save if contents haven't changed
    def adminSetDeleted(self, deleted):
        self.deleted = deleted
        super(Revision, self).save()

    def save(self, **kwargs):
        # Check if contents have changed... if not, silently ignore save
        if self.article and self.article.current_revision:
            if self.deleted == 0 and self.article.current_revision.contents == self.contents:
                return
            else:
                import datetime
                self.article.modified_on = datetime.datetime.now()
                self.article.save()

        # Increment counter according to previous revision
        previous_revision = Revision.objects.filter(article=self.article).order_by('-counter')
        if previous_revision.count() > 0:
            if previous_revision.count() > previous_revision[0].counter:
                self.counter = previous_revision.count() + 1
            else:
                self.counter = previous_revision[0].counter + 1
        else:
            self.counter = 1
        if (self.article.current_revision and self.article.current_revision.deleted == 0):
            self.previous_revision = self.article.current_revision

        # Create pre-parsed contents - no need to parse on-the-fly
        ext = WIKI_MARKDOWN_EXTENSIONS
        ext += ["wikipath(default_namespace=%s)" % self.article.namespace.name]
        self.contents_parsed = markdown(self.contents,
                                        extensions=ext,
                                        safe_mode='escape',)
        super(Revision, self).save(**kwargs)

    def delete(self, **kwargs):
        """If a current revision is deleted, then regress to the previous
        revision or insert a stub, if no other revisions are available"""
        article = self.article
        if article.current_revision == self:
            prev_revision = Revision.objects.filter(article__exact=article,
                                                    pk__not=self.pk).order_by('-counter')
            if prev_revision:
                article.current_revision = prev_revision[0]
                article.save()
            else:
                r = Revision(article=article,
                             revision_user=article.created_by)
                r.contents = unicode(_('Auto-generated stub'))
                r.revision_text = unicode(_('Auto-generated stub'))
                r.save()
                article.current_revision = r
                article.save()
        super(Revision, self).delete(**kwargs)

    def get_diff(self):
        if (self.deleted == 1):
            yield "Article Deletion"
            return

        if self.previous_revision:
            previous = self.previous_revision.contents.splitlines(1)
        else:
            previous = []

        # Todo: difflib.HtmlDiff would look pretty for our history pages!
        diff = difflib.unified_diff(previous, self.contents.splitlines(1))
        # let's skip the preamble
        diff.next(); diff.next(); diff.next()

        for d in diff:
            yield d

    def __unicode__(self):
        return "r%d" % self.counter

    class Meta:
        verbose_name = _('article revision')
        verbose_name_plural = _('article revisions')


class Permission(models.Model):
    permission_name = models.CharField(max_length=255, verbose_name=_('Permission name'))
    can_write = models.ManyToManyField(User, blank=True, null=True, related_name='write',
                                       help_text=_('Select none to grant anonymous access.'))
    can_read = models.ManyToManyField(User, blank=True, null=True, related_name='read',
                                       help_text=_('Select none to grant anonymous access.'))

    def __unicode__(self):
        return self.permission_name

    class Meta:
        verbose_name = _('Article permission')
        verbose_name_plural = _('Article permissions')


class RevisionForm(forms.ModelForm):
    contents = forms.CharField(label=_('Contents'), widget=forms.Textarea(attrs={'rows': 8, 'cols': 50}))

    class Meta:
        model = Revision
        fields = ['contents', 'revision_text']


class RevisionFormWithTitle(forms.ModelForm):
    title = forms.CharField(label=_('Title'))

    class Meta:
        model = Revision
        fields = ['title', 'contents', 'revision_text']


class CreateArticleForm(RevisionForm):
    title = forms.CharField(label=_('Title'))

    class Meta:
        model = Revision
        fields = ['title', 'contents', ]


def set_revision(sender, *args, **kwargs):
    """Signal handler to ensure that a new revision is always chosen as the
    current revision - automatically. It simplifies stuff greatly. Also
    stores previous revision for diff-purposes"""
    instance = kwargs['instance']
    created = kwargs['created']
    if created and instance.article:
        instance.article.current_revision = instance
        instance.article.save()

signals.post_save.connect(set_revision, Revision)
