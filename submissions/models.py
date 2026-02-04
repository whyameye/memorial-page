from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import micawber

class Submission(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(User, null=True, blank=True, related_name='accepted_submissions', on_delete=models.SET_NULL)
    message = models.TextField(blank=True, null=True, help_text='If you\'d like, leave a private message to partner and family (not public)')
    name = models.CharField(max_length=200,blank=True, null=True,
            help_text="<b>Name, Location</b> would be ideal")
    email = models.CharField(max_length=200,blank=True, null=True, help_text="Give us a way to contact you (not public)")

    text = models.TextField(blank=True, help_text='A story about how he touched your life, or anything else you want to share. <small>(markdown formatting available)</small>')

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
    link = models.CharField(max_length=255, verbose_name="URL", help_text="Any link: video, social media, photo album, article")
    description = models.CharField(max_length=255, null=True, blank=True, verbose_name="Caption", help_text="Optional caption for this link")

    embed = models.TextField(null=True,blank=True)

    def save(self, *args, **kwargs):
        providers = micawber.bootstrap_basic()
        try:
            self.embed = providers.request(self.link)['html']
        except micawber.ProviderException as e:
            self.embed = None
        super(Link, self).save(*args, **kwargs)

