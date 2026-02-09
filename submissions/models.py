from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import micawber

class Submission(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(User, null=True, blank=True, related_name='accepted_submissions', on_delete=models.SET_NULL)
    message = models.TextField(blank=True, null=True, verbose_name='Private message to family (optional, not public)')
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Name (required)')
    email = models.CharField(max_length=200, blank=True, null=True, verbose_name='Email (optional, not public)')

    text = models.TextField(blank=True, verbose_name='Story or memory you\'d like to share(required if no pictures)')

    def get_absolute_url(self):
        return reverse('submission-edit', kwargs={'pk': self.id})

    @property
    def current_files(self):
        return [x for x in self.image_set.all() if x.file]

    def __str__(self):
        return 'Submission by %s (%s)' % (self.name, (self.text or '')[:20])

class Image(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    file = models.ImageField()

class Link(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    link = models.CharField(max_length=255, verbose_name="URL (video, social media, photo album, article)")
    description = models.CharField(max_length=255, null=True, blank=True, verbose_name="Caption (optional)")

    embed = models.TextField(null=True,blank=True)

    def save(self, *args, **kwargs):
        providers = micawber.bootstrap_basic()
        try:
            self.embed = providers.request(self.link)['html']
        except micawber.ProviderException as e:
            self.embed = None
        super(Link, self).save(*args, **kwargs)

