import re
from rest_framework import serializers

class CharacterSerializer(serializers.Serializer):
    character_id = serializers.IntegerField(source='id')
    firstname = serializers.SerializerMethodField()
    lastname = serializers.SerializerMethodField()
    status_character = serializers.CharField(source='status')
    character_species = serializers.CharField(source='species')
    character_gender = serializers.CharField(source='gender')
    location_id = serializers.SerializerMethodField()

    def get_firstname(self, obj):
        """
        Retrieves the first name from an object containing a 'name' field.

        :param obj: Object containing name information.
        :type obj: dict
        :return: Extracted first name.
        :rtype: str
        """
        full_name = obj.get('name', '')
        if full_name:
            names = full_name.split()
            return names[0] if names else ''
        return ''

    def get_lastname(self, obj):
        """
        Retrieves the last name from an object containing a 'name' field.

        :param obj: Object containing name information.
        :type obj: dict
        :return: Extracted last name.
        :rtype: str
        """
        full_name = obj.get('name', '')
        if full_name:
            names = full_name.split()
            return ' '.join(names[1:]) if len(names) > 1 else ''
        return ''

    def get_location_id(self, obj):
        """
        Retrieves the location ID from an object containing a 'location' field with a URL.

        :param obj: Object containing location information.
        :type obj: dict
        :return: Extracted location ID.
        :rtype: int or str (in case ID is not found)
        """
        location_id = re.search(r'/(\d+)$', obj.get('location', {}).get('url', ''))
        return int(location_id.group(1)) if location_id else ''


class LocationSerializer(serializers.Serializer):
    location_id = serializers.IntegerField(source='id')
    name = serializers.CharField()
    location_type = serializers.CharField(source='type')
    dimension = serializers.CharField()
    creation_date = serializers.CharField(source='created')
