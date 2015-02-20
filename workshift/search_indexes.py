"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

Search indexes for the workshift app.
"""

from haystack import indexes
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    WorkshiftProfile, RegularWorkshift, WorkshiftInstance


class SemesterIndex(indexes.ModelSearchIndex, indexes.Indexable):
    """ Index for semesters. """
    season = indexes.EdgeNgramField(model_attr='season', boost=2)
    year = indexes.EdgeNgramField(model_attr='year', boost=2)
    class Meta:
        model = Semester
        fields = (
            "start_date",
            "end_date",
        )

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class WorkshiftPoolIndex(indexes.ModelSearchIndex, indexes.Indexable):
    """ Index for workshift pools. """
    class Meta:
        model = WorkshiftPool
        fields = (
            "title",
            "semester",
        )

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class WorkshiftTypeIndex(indexes.ModelSearchIndex, indexes.Indexable):
    """ Index for workshift types. """
    class Meta:
        model = WorkshiftType
        fields = (
            "title",
            "description",
            "quick_tips",
        )

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class WorkshiftProfileIndex(indexes.ModelSearchIndex, indexes.Indexable):
    """ Index for workshift profiles. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    user = indexes.EdgeNgramField(model_attr='user', boost=1.5)
    exact_user = indexes.CharField(model_attr='user', faceted=True)
    class Meta:
        model = WorkshiftProfile
        fields = (
            "semester",
        )

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class RegularWorkshiftIndex(indexes.ModelSearchIndex, indexes.Indexable):
    """ Index for a regular workshift. """
    class Meta:
        model = RegularWorkshift
        fields = (
            "workshift_type",
            "pool",
            "addendum",
        )

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(pool__semester__current=True)


class WorkshiftInstanceIndex(indexes.ModelSearchIndex, indexes.Indexable):
    """ Index for a workshift instance. """
    class Meta:
        model = WorkshiftInstance
        fields = (
            "date",
            "workshifter",
            "logs",
            "pool",
            "title",
            "description",
        )

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(semester__current=True)
