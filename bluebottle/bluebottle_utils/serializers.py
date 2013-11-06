from django.core.exceptions import FieldError
from django.template.defaultfilters import truncatechars


from rest_framework import serializers
from taggit.managers import _TaggableManager


from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.bluebottle_utils.validators import validate_postal_code
from bluebottle.bluebottle_utils.models import Address

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    """ Used to strip HTML tags for meta fields (e.g. description) """
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


class AddressSerializer(serializers.ModelSerializer):

    def validate_postal_code(self, attrs, source):
        value = attrs[source]
        if value:
            country_code = ''
            if 'country' in attrs:
                country_code = attrs['country']
            elif self.object and self.object.country:
                country_code = self.object.country.alpha2_code

            if country_code:
                validate_postal_code(value, country_code)
        return attrs

    class Meta:
        model = Address
        fields = ('id', 'line1', 'line2', 'city', 'state', 'country', 'postal_code')



class MetaField(serializers.Field):
    """ 
    Serializer field which fills meta data based on model attributes
    Init with `field = None` to disable the field.

    Callables need to accept **kwargs, as the request is sent by default.

    Usage example:

    #models.py
    class Example(models.Model):
        title = models.CharField(max_length=50)

        def get_description(self, **kwargs):
            return self.title + ' (description)'

    
    # serializers.py
    class ExampleSerializer(serializers.ModelSerializer):

        meta_data = MetaField(
                title = 'title',
                description = 'get_description',
                keywords = None,
                image_source = None
            )

        class Meta:
            model = Example
            fields = ('title', 'meta_data')


    This returns API JSON as:

    json = {
        'title': 'Sample title',
        'meta_data': {
            'title': 'Sample title',
            'description': 'Sample title (description)',
            'keywords': null,
            'image': null
            }
        }
    }

    When image_source is provided, you get a JSON object with keys 'large',
    'small', 'full' and 'square'.

    Currently, images are only used for facebook

    # TODO: unittests

    """

    def __init__(self, title = 'title',
                description = 'description', keywords = 'tags',
                image_source = None, 
                *args, **kwargs):
        
        # default to None, return the default title/image if no explicit title/image were provided
        self.fb_title = kwargs.pop('fb_title', None)
        self.tweet = kwargs.pop('tweet', None)
        # TODO: add support for list of image sources -> multiple images

        self.title = title
        self.description = description
        self.keywords = keywords
        self.image_source = image_source

        super(MetaField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        """ Get the parts of the meta dict """

        # set defaults
        value = {
            'title': None,
            'fb_title': None,
            'tweet': None,
            'description': None,
            'image': None,
            'keywords': None,
        }

        # get the meta title from object callable or object property
        if self.title:
            title = self._get_callable(obj, self.title)
            if title is None:
                title = self._get_field(obj, self.title)
            value['title'] = title

        # try to get the facebook title
        if self.fb_title is not None:
            fb_title = self._get_callable(obj, self.fb_title)
            if fb_title is None:
                fb_title = self._get_field(obj, self.fb_title)
            value['fb_title'] = fb_title
        elif self.title:
            value['fb_title'] = value['title']

        if self.tweet is not None:
            tweet = self._get_callable(obj, self.tweet)
            if tweet is None:
                tweet = self._get_field(obj, self.tweet)
            value['tweet'] = tweet
        elif self.title:
            value['tweet'] = '{URL}'
                
        # get the meta description from object callable or object property
        if self.description:
            description = self._get_callable(obj, self.description)
            if description is None:
                description = self._get_field(obj, self.description)
                description = truncatechars(description, 200)
            value['description'] = description

        # keywords: either from object callable or property, if property,
        # check if we are referring to taggit tags.
        if self.keywords:
            keywords = self._get_callable(obj, self.keywords)
            if keywords is None:
                # Get the keywords
                keywords = self._get_field(obj, self.keywords)
                
                # usually tags as keywords
                if isinstance(keywords, _TaggableManager):
                    keywords = [tag.name.lower() for tag in keywords.all()]
                else:
                    # try to split the keywords
                    try:
                        keywords = keywords.lower().split()
                    except AttributeError:
                        keywords = ''
                value['keywords'] = ", ".join(keywords)
            else:
                value['keywords'] = keywords

        # special case with images, use the ImageSerializer to get cropped formats
        if self.image_source:
            image_source = self._get_callable(obj, self.image_source)
            if image_source is None:
                image_source = self._get_field(obj, self.image_source)


            serializer = ImageSerializer()
            serializer.context = self.context
            images = serializer.to_native(image_source)
            if images:
                # always take the full image for facebook, they consume it and
                # resize/store the images themselve
                value['image'] = images.get('full', None)

        return self.to_native(value)
    
    
    def _get_field(self, obj, field_name):
        """ Allow traversing the relations tree for fields """
        attrs = field_name.split('__')
        
        field = obj
        for attr in attrs:
            try:
                field = getattr(field, attr)
            except AttributeError:
                raise FieldError('Unknown field "%s" in "%s"' % (attr, field_name))
        return field

    def _get_callable(self, obj, attr):
        """ Check if the attr is callable, return its value if it is """
        try:
            _attr = getattr(obj, attr)
            if callable(_attr): 
                # return _attr() # Call it, and return the result
                return _attr(request=self.context['request'])
        except AttributeError: # not a model/object attribute
            pass
        return None