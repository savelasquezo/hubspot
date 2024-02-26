import os, ramapi, csv, hubspot, json, re, hashlib
from ramapi import *
from pprint import pprint

from django.conf import settings
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response

from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, BatchReadInputSimplePublicObjectId, ApiException
from hubspot.crm.associations.v4 import BatchInputPublicDefaultAssociationMultiPost, ApiException

from app.serializers import CharacterSerializer, LocationSerializer

def isPrime(n):
    """
    Check if a number is prime n (int).
    Returns:
    - bool: True if the number is prime, False otherwise.
    """
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def getClients():
    try:
        client = hubspot.Client.create(access_token="pat-na1-4de0014b-a034-43c6-aee2-b9261311121c")

        clients_data, after = [], None
        while True:
            response = client.crm.contacts.basic_api.get_page(
                properties=[
                    "character_id",
                    "firstname",
                    "lastname",
                    "status_character",
                    "character_species",
                    "character_gender",
                    "location_id"
                ], 
                limit=100, archived=False, after=after
            )
            
            for result in response.results:
                client_info = {
                    'id': result.id,
                    'properties': result.properties,
                }
                clients_data.append(client_info)

            if response.paging and response.paging.next:
                after = response.paging.next.after
            else:
                break

        return clients_data

    except Exception as e:
        date = timezone.now().strftime("%Y-%m-%d %H:%M")
        with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
            f.write("fetchClients {} --> Error: {}\n".format(date, str(e)))


def getCompanies():
    try:
        client = hubspot.Client.create(access_token="pat-na1-4de0014b-a034-43c6-aee2-b9261311121c")

        data, after = [], None
        while True:
            response = client.crm.companies.basic_api.get_page(
                properties=[
                    "location_id",
                    "name",
                    "location_type",
                    "dimension",
                    "creation_date"
                ], 
                limit=100, archived=False, after=after
            )
            
            for result in response.results:
                client_info = {
                    'id': result.id,
                    'properties': result.properties,
                }
                data.append(client_info)

            if response.paging and response.paging.next:
                after = response.paging.next.after
            else:
                break

        return data

    except Exception as e:
        date = timezone.now().strftime("%Y-%m-%d %H:%M")
        with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
            f.write("fetchClients {} --> Error: {}\n".format(date, str(e)))


class requestRM(generics.GenericAPIView):

    def get_characters(self):
        characters, page = [], 1
        while True:
            characters_data = ramapi.Character.get_page(page)
            characters.extend(characters_data['results'])
            if not characters_data['info']['next']:
                break
            page += 1
        data = [character for character in characters if isPrime(character['id'])]
        return data

    def get_locations(self):
        characters = self.get_characters()
        idLocations = []
        for item in characters:
            match = re.search(r'/(\d+)$', item['location']['url'])
            if match:
                idLocations.append(int(match.group(1)))
        idLocations = sorted(set(idLocations))
        data = ramapi.Location.get(idLocations)
        return data

class requestContacts(requestRM):
    permission_classes = [AllowAny]
    serializer_class = CharacterSerializer

    def post(self, request, *args, **kwargs):
        try:
            data = self.get_characters()

            size = 50
            batchCharacters = [data[i:i+size] for i in range(0, len(data), size)]

            client = hubspot.Client.create(access_token="pat-na1-4de0014b-a034-43c6-aee2-b9261311121c")
            for batch in batchCharacters:
                serializer = self.serializer_class(batch, many=True)
                dataInput = [{"properties": item} for item in serializer.data]

                batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(
                    inputs=dataInput
                )

                client.crm.contacts.batch_api.create(
                    batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create
                )

            return Response({'succes': 'The batches of clients have been created.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            date = timezone.now().strftime("%Y-%m-%d %H:%M")
            with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
                f.write("requestCharacters {} --> Error: {}\n".format(date, str(e)))
            return Response({'error': 'Error fetching characters.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class requestCompanies(requestRM):
    permission_classes = [AllowAny]
    serializer_class = LocationSerializer

    def post(self, request, *args, **kwargs):
        try:
            data = self.get_locations()

            size = 50
            batchLocations = [data[i:i+size] for i in range(0, len(data), size)]

            client = hubspot.Client.create(access_token="pat-na1-4de0014b-a034-43c6-aee2-b9261311121c")
            for batch in batchLocations:
                serializer = self.serializer_class(batch, many=True)
                dataInput = [{"properties": item} for item in serializer.data]

                batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(
                    inputs=dataInput
                )

                client.crm.companies.batch_api.create(
                    batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create
                )

            return Response({'succes': 'The batches of companies have been created.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            date = timezone.now().strftime("%Y-%m-%d %H:%M")
            with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
                f.write("requestLocations {} --> Error: {}\n".format(date, str(e)))
            return Response({'error': 'Error fetching locations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class requestAssociations(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        try:

            data_clients = getClients()
            dict_clients = [
                {
                    'client': client['id'],
                    'location_id': client['properties'].get('location_id', None),
                }
                for client in data_clients
            ]

            data_companies = getCompanies()
            dict_companies = [
                {
                    'companie': client['id'],
                    'location_id': client['properties'].get('location_id', None),
                }
                for client in data_companies
            ]

            associations = {}
            for d1 in dict_clients:
                for d2 in dict_companies:
                    if d1["location_id"] == d2["location_id"]:
                        associations[d1["client"]] = d2["companie"]


            data = []
            for key, value in associations.items():
                elemento_transformado = {"from": {"id": key},"to": {"id": value}}
                data.append(elemento_transformado)


            batch = 50
            batchLocations = [data[i:i+batch] for i in range(0, len(data), batch)]

            client = hubspot.Client.create(access_token="pat-na1-4de0014b-a034-43c6-aee2-b9261311121c")
            for batch in batchLocations:
                batch_input_public_default_association_multi_post = BatchInputPublicDefaultAssociationMultiPost(
                    inputs=batch
                )
                client.crm.associations.v4.batch_api.create_default(
                    from_object_type="contacts",
                    to_object_type="companies",
                    batch_input_public_default_association_multi_post=batch_input_public_default_association_multi_post
                )
            
            return Response({'succes': 'The batches of associations have been created.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            date = timezone.now().strftime("%Y-%m-%d %H:%M")
            with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
                f.write("requestAssociations {} --> Error: {}\n".format(date, str(e)))
            return Response({'error': 'Error fetching associations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class requestHubspot(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        hubspot_secret = request.headers.get('XHubSpotSecret')

        if not hubspot_secret:
            return Response({'error': 'XHubSpotSecret not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hubspot_secret == "54b655d0-f1dd-436b-8dfb-9dccadd79a8a":
            pprint(request.data)
            return Response({'succes': 'The batches of contacts have been update.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Authentication failed: X-HubSpot-Secret mismatch.'}, status=status.HTTP_401_UNAUTHORIZED)
