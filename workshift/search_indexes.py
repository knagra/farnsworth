"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

Search indexes for the workshift app.
"""

from haystack import indexes
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    WorkshiftProfile, RegularWorkshift, WorkshiftInstance

class SemesterIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for semesters. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    season = indexes.EdgeNgramField(model_attr='season', boost=2)
    year = indexes.EdgeNgramField(model_attr='year', boost=2)
    start_date = indexes.DateField(model_attr='start_date')
    end_date = indexes.DateField(model_attr='end_date')

    def get_model(self):
        return Semester

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class WorkshiftPoolIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for workshift pools. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    title = indexes.EdgeNgramField(model_attr='title')
    semester = indexes.EdgeNgramField(model_attr='semester')

    def get_model(self):
        return WorkshiftPool

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class WorkshiftTypeIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for workshift types. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    title = indexes.EdgeNgramField(model_attr='title')
    description = indexes.EdgeNgramField(model_attr='description', null=True)
    quick_tips = indexes.EdgeNgramField(model_attr='quick_tips', null=True)

    def get_model(self):
        return WorkshiftType

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class WorkshiftProfileIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for workshift profiles. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    user = indexes.EdgeNgramField(model_attr='user', boost=1.5)
    exact_user = indexes.CharField(model_attr='user', faceted=True)
    semester = indexes.EdgeNgramField(model_attr='semester')

    def get_model(self):
        return WorkshiftProfile

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class RegularWorkshiftIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for a regular workshift. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
    workshift_type = indexes.EdgeNgramField(model_attr='workshift_type')
    pool = indexes.EdgeNgramField(model_attr='pool')
    addendum = indexes.EdgeNgramField(model_attr='addendum', null=True)

    def get_model(self):
        return RegularWorkshift

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(pool__semester__current=True)

class WorkshiftInstanceIndex(indexes.SearchIndex, indexes.Indexable):
    """ Index for a workshift instance. """
    text = indexes.EdgeNgramField(document=True, use_template=True)
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
        return WorkshiftInstance

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(semester__current=True)
