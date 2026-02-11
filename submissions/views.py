import json
import logging
import os
import subprocess
from functools import wraps

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Submission, Image, Link
from django.forms.models import ModelForm, inlineformset_factory
from django.forms.utils import ErrorList
from django import forms
from django.utils import timezone
from django.contrib import messages
from extra_views import InlineFormSet
from extra_views.advanced import UpdateWithInlinesView
from PIL import Image as PILImage
from PIL.ImageOps import exif_transpose

logger = logging.getLogger(__name__)


MAX_DIMENSION = 2000
JPEG_QUALITY = 85


def compress_image(image_path):
    """Auto-orient, resize if >2000px on any side, and save as JPEG (or PNG if transparent)."""
    try:
        img = PILImage.open(image_path)

        # Auto-orient based on EXIF rotation
        img = exif_transpose(img)

        # Resize if either dimension exceeds MAX_DIMENSION
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), PILImage.LANCZOS)

        # Keep PNG for images with transparency, convert everything else to JPEG
        has_transparency = img.mode in ('RGBA', 'LA') or (
            img.mode == 'P' and 'transparency' in img.info
        )

        if has_transparency:
            img.save(image_path, format='PNG', optimize=True)
        else:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(image_path, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    except Exception:
        logger.exception("Failed to compress image: %s", image_path)


def send_submission_notification(submission):
    """Send email notification about a new submission via sendmail command."""
    from mysite.context_processors import get_site_config

    to_email = get_site_config('NOTIFICATION_EMAIL', '')
    if not to_email:
        return

    from_email = get_site_config('NOTIFICATION_FROM', to_email)
    sendmail_cmd = get_site_config('SENDMAIL_COMMAND', '/usr/sbin/sendmail')

    subject = "New submission from %s" % (submission.name or 'Anonymous')
    admin_url = "https://%s/admin/submissions/submission/%s/change/" % (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost',
        submission.pk,
    )

    body = "New submission received.\n\nFrom: %s\n\nView in admin: %s\n" % (
        submission.name or 'Anonymous',
        admin_url,
    )

    email_message = "From: %s\nTo: %s\nSubject: %s\nContent-Type: text/plain; charset=utf-8\n\n%s" % (
        from_email, to_email, subject, body,
    )

    try:
        proc = subprocess.run(
            [sendmail_cmd, '-t'],
            input=email_message.encode('utf-8'),
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            logger.error("sendmail failed (exit %d): %s", proc.returncode, proc.stderr.decode('utf-8', errors='replace'))
    except Exception:
        logger.exception("Failed to send submission notification email")


def submission_password_required(view_func):
    """Decorator that requires submission password to access a view."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.session.get('submission_unlocked'):
            return HttpResponseRedirect(reverse('submission-password') + '?next=' + request.path)
        return view_func(request, *args, **kwargs)
    return wrapped


class SubmissionPasswordRequiredMixin:
    """Mixin for class-based views that require submission password."""
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('submission_unlocked'):
            return HttpResponseRedirect(reverse('submission-password') + '?next=' + request.path)
        return super().dispatch(request, *args, **kwargs)


def submission_password(request):
    """View to enter the submission password."""
    error = None
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password == settings.SUBMISSION_PASSWORD:
            request.session['submission_unlocked'] = True
            next_url = request.GET.get('next', reverse('submit'))
            return HttpResponseRedirect(next_url)
        else:
            error = 'Incorrect password'

    return render(request, 'submissions/password.html', {'error': error})

class LinkInline(InlineFormSet):
    model = Link
    fields = ['link', 'description']
    extra = 1
    can_delete = False  # Hide delete checkboxes - empty links are auto-deleted

    def get_queryset(self):
        # Delete any links with empty link field when loading
        qs = super().get_queryset()
        qs.filter(link='').delete()
        return qs

class SubmissionForm(ModelForm):
    class Meta:
        model = Submission
        widgets={'message': forms.Textarea(attrs={'rows':2, 'cols':15}),
                 'text': forms.Textarea(attrs={'rows':4, 'cols':15})}
        fields = ['text','message','name','email',]

    def save(self, commit=True):
        x = super(SubmissionForm, self).save(commit=False)
        if 'send' in self.data:
            x.submitted_at = timezone.now()
        if commit:
            x.save()
        return x

    def clean_name(self):
        data = self.cleaned_data
        if 'send' in self.data:
            if not data.get('name', None):
                raise forms.ValidationError('Name needed for submission!')
        return data.get('name', None)

    def clean_text(self):
        data = self.cleaned_data
        if 'send' in self.data:
            if not data.get('text', None) and not self.instance.current_files:
                raise forms.ValidationError('Text or Pictures needed for submission!')
        return data.get('text', None)



class SubmissionListView(ListView):
    paginate_by = 10

    def get_queryset(self):
        from mysite.context_processors import get_site_config
        if get_site_config('REQUIRE_APPROVAL', False):
            return Submission.objects.filter(accepted_at__isnull=False).order_by('-accepted_at')
        else:
            return Submission.objects.filter(submitted_at__isnull=False).order_by('-submitted_at')

class SubmissionUpdateView(SubmissionPasswordRequiredMixin, UpdateWithInlinesView):
    model = Submission
    form_class = SubmissionForm
    inlines = [LinkInline]
    success_url = '/'

    def get_queryset(self):
        base_qs = super(SubmissionUpdateView, self).get_queryset()

        sid = self.request.session.get('submission_id',None)
        if not sid:
            sid = Submission.objects.create().pk
        self.request.session['submission_id'] = sid
        return base_qs.filter(pk=sid, accepted_at__isnull=True)

    def forms_valid(self, form, inlines):
        if 'send' in self.request.POST:
            self.object = form.save()
            for formset in inlines:
                formset.save()
            # Validate required fields
            if not self.object.name:
                error = form._errors.setdefault('name', ErrorList())
                error.append('Name is required!')
                return self.forms_invalid(form, inlines)
            if not self.object.text and not self.object.current_files:
                error = form._errors.setdefault('text', ErrorList())
                error.append('Please upload images or add text to submit.')
                return self.forms_invalid(form, inlines)
            # Mark as submitted
            self.object.submitted_at = timezone.now()
            self.object.save()
            # Send notification email
            send_submission_notification(self.object)
            # Clear session so user can make another submission
            if 'submission_id' in self.request.session:
                del self.request.session['submission_id']
            return HttpResponseRedirect('/')

        response = super(SubmissionUpdateView, self).forms_valid(form, inlines)
        # Clean up empty links
        self.object.link_set.filter(link='').delete()
        return response


@submission_password_required
def submission(request):
    sid = request.session.get('submission_id', None)
    existing = None
    if sid:
        existing = Submission.objects.filter(pk=sid, submitted_at__isnull=True).first()
    if not existing:
        existing = Submission.objects.create()
        request.session['submission_id'] = existing.pk
    return HttpResponseRedirect(existing.get_absolute_url())

class ImageCreateView(SubmissionPasswordRequiredMixin, CreateView):
    model = Image
    fields = ['file']

    def form_valid(self, form):
        sub = Submission.objects.get(pk=self.kwargs['pk'], submitted_at__isnull=True)
        form.instance.submission = sub
        form.instance.order = sub.image_set.count()
        self.object = form.save()
        compress_image(self.object.file.path)
        data = {'status': 'success', 'removeLink': reverse('jfu-delete', kwargs={'pk': self.object.pk}), 'imageId': self.object.pk}
        response = JsonResponse(data)
        return response

    def form_invalid(self, form):
        return HttpResponse('Not an Image', status=500)

@submission_password_required
def delete_image(request, pk):
    success = True
    try:
        instance = Image.objects.get( pk = pk )
        if request.session['submission_id']==instance.submission.pk:
            os.unlink( instance.file.path )
            instance.delete()
        else:
            success = False
    except Image.DoesNotExist:
        success = False

    return HttpResponse(  'ok, gone' )


@submission_password_required
def delete_submission(request, pk):
    """Delete a submission if it belongs to the current session."""
    try:
        submission = Submission.objects.get(pk=pk)
        if request.session.get('submission_id') == submission.pk:
            # Delete associated images
            for image in submission.image_set.all():
                try:
                    os.unlink(image.file.path)
                except:
                    pass
            submission.delete()
            # Clear session
            del request.session['submission_id']
    except Submission.DoesNotExist:
        pass
    return HttpResponseRedirect('/')


@submission_password_required
def reorder_images(request, pk):
    """Reorder images for a submission via JSON array of image IDs."""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
    if request.session.get('submission_id') != pk:
        return HttpResponse('Forbidden', status=403)
    try:
        image_ids = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse('Invalid JSON', status=400)
    submission = Submission.objects.get(pk=pk)
    for order, image_id in enumerate(image_ids):
        submission.image_set.filter(pk=image_id).update(order=order)
    return JsonResponse({'status': 'ok'})


def LinkView(InlineFormSetView):
    model = Submission
    inlines = [LinkInline]
