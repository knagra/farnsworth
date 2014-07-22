'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Search indexes for the threads app.
'''

from haystack import indexes

from base.models import UserProfile
from utils.variables import ANONYMOUS_USERNAME

class UserProfileIndex(indexes.SearchIndex, indexes.Indexable):
    ''' Index for UserProfiles. '''
    text = indexes.EdgeNgramField(document=True, use_template=True)
    user = indexes.EdgeNgramField(model_attr='user', boost=1.125)
    exact_user = indexes.CharField(model_attr='user', faceted=True)
    former_houses = indexes.EdgeNgramField(model_attr='former_houses', null=True)
    status = indexes.EdgeNgramField(model_attr='status')
    exact_status = indexes.CharField(model_attr='status', faceted=True)

    def get_model(self):
        return UserProfile

    def prepare(self, obj):
        data = super(UserProfileIndex, self).prepare(obj)
        data['boost'] = 1.125
        return data

    def index_queryset(self, using=None):
        return self.get_model().objects.all().exclude(user__username=ANONYMOUS_USERNAME)
