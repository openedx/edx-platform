import logging
import os

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.decorators import login_required
from edxmako.shortcuts import render_to_response

from wand.image import Image
from .utils import generate_certificate

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def issue(request):
    course_id = request.POST['certificate_course_id']

    if request.session.get('course_pass_%s' % course_id):
        user = request.user

        return render_to_response('edraak_certificates/issue.html', {'user': user,
                                                                     'course_id': course_id})
    else:
        return redirect(reverse('dashboard'))


@login_required
def download(request, course_id):
    if request.session.get('course_pass_%s' % course_id):
        pdf_file = generate_certificate(request, course_id)
        wrapper = FileWrapper(pdf_file)

        # `application/octet-stream` is to force download
        response = HttpResponse(wrapper, content_type='application/octet-stream')

        response['Content-Length'] = os.path.getsize(pdf_file.name)
        response['Content-Disposition'] = "attachment; filename=Edraak-Certificate.pdf"

        return response
    else:
        return redirect(reverse('dashboard'))


@login_required
def preview(request, course_id):
    if request.session.get('course_pass_%s' % course_id):
        pdf_file = generate_certificate(request, course_id)
        image_file = NamedTemporaryFile(suffix='-cert.png')

        with Image(filename=pdf_file.name) as img:
            with img.clone() as i:
                i.resize(445, 315)
                i.save(filename=image_file.name)

        wrapper = FileWrapper(image_file)
        response = HttpResponse(wrapper, content_type='image/png')
        response['Content-Length'] = os.path.getsize(image_file.name)

        return response
    else:
        return redirect(reverse('dashboard'))