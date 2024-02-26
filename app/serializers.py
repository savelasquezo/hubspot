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
        full_name = obj.get('name', '')
        if full_name:
            names = full_name.split()
            return names[0] if names else ''
        return ''

    def get_lastname(self, obj):
        full_name = obj.get('name', '')
        if full_name:
            names = full_name.split()
            return ' '.join(names[1:]) if len(names) > 1 else ''
        return ''

    def get_location_id(self, obj):
        location_id = re.search(r'/(\d+)$', obj.get('location', {}).get('url', ''))
        return int(location_id.group(1)) if location_id else ''


class LocationSerializer(serializers.Serializer):
    location_id = serializers.IntegerField(source='id')
    name = serializers.CharField()
    location_type = serializers.CharField(source='type')
    dimension = serializers.CharField()
    creation_date = serializers.CharField(source='created')
