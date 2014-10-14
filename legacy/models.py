"""
Project: Farnsworth

Author: Karandeep Singh Nagra

Legacy Kingman site data.
"""


from django.db import models


class TeacherRequest(models.Model):
    """
    A request from the previous Kingman website.
    """
    request_type = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="The request type for this request."
    )
    teacher_key = models.CharField(
        max_length=24,
        null=True,
        blank=True,
        help_text="Legacy primary key based on datetime."
    )
    timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when this request was posted."
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The name given by the user who posted this request."
    )
    body = models.TextField(
        null=True,
        blank=True,
        help_text="The body of this request."
    )

    def __unicode__(self):
        return self.teacher_key

    class Meta:
        ordering = ['-timestamp']


class TeacherResponse(models.Model):
    """
    A response to a request from the previous Kingman website.
    """
    request = models.ForeignKey(
        TeacherRequest,
        help_text="The request to which this is a response."
    )
    timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when this response was posted."
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The name given by the user who posted this request."
    )
    body = models.TextField(
        null=True,
        blank=True,
        help_text="The body of this response."
    )

    def __unicode__(self):
        return "{key} - {name}".format(
            key=self.request.teacher_key,
            name=self.name
        )

    class Meta:
        ordering = ['timestamp']


class TeacherNote(models.Model):
    """
    A note posted for public consumption.
    """
    timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when this note was posted."
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The name given by the user who posted this request."
    )
    body = models.TextField(
        null=True,
        blank=True,
        help_text="The body of this note."
    )

    def __unicode__(self):
        return "{time} - {name}".format(
            time=self.timestamp,
            name=self.name
        )

    class Meta:
        ordering = ['-timestamp']


class TeacherEvent(models.Model):
    """
    An event posted on the legacy Kingman website.
    """
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of this event."
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The title of this event."
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="The description of this event."
    )

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-date']
