import os
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
from datetime import datetime
from django.contrib import messages
from extra_views import InlineFormSet
from extra_views.advanced import UpdateWithInlinesView


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
    fields=['link','description']

class SubmissionForm(ModelForm):
    class Meta:
        model = Submission
        widgets={'message': forms.Textarea(attrs={'rows':2, 'cols':15}),
                 'text': forms.Textarea(attrs={'rows':4, 'cols':15})}
        fields = ['text','message','name','email',]

    def save(self, commit=True):
        x = super(SubmissionForm, self).save(commit=False)
        if 'send' in self.data:
            x.submitted_at = datetime.now()
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

    def get_queryset(self):
        base_qs = super(SubmissionUpdateView, self).get_queryset()

        sid = self.request.session.get('submission_id',None)
        if not sid:
            sid = Submission.objects.create().pk
        self.request.session['submission_id'] = sid
        return base_qs.filter(pk=sid, accepted_at__isnull=True)

    def form_valid(self, form):
        if 'send' in self.request.POST:
            self.object = form.save()
            if self.object.name:
                self.object.submitted_at = datetime.now()
            self.object.save()
            if self.object.name and (self.object.text or self.object.current_files):
                messages.success(self.request, 'Thank you. A moderator will publish your submission as soon as possible!')
                return HttpResponseRedirect('/')
            else:
                error = form._errors.setdefault('name', ErrorList())
                error.append('Needed for submission!')
                if not self.object.name and not self.object.current_files:
                    error = form._errors.setdefault('text', ErrorList())
                    error.append('Please upload Images or add Text to submit.')
                return super(SubmissionUpdateView, self).form_invalid(form)


        return super(SubmissionUpdateView, self).form_valid(form)


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
        form.instance.submission = Submission.objects.get(pk=self.kwargs['pk'], submitted_at__isnull=True)
        self.object = form.save()
        data = {'status': 'success', 'removeLink': reverse('jfu-delete', kwargs={'pk': self.object.pk})}
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
            messages.success(request, 'Your submission has been deleted.')
    except Submission.DoesNotExist:
        pass
    return HttpResponseRedirect('/')


def LinkView(InlineFormSetView):
    model = Submission
    inlines = [LinkInline]
