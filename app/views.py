import os, ramapi, csv, hubspot, json, re, hashlib
from ramapi import *
from pprint import pprint

from django.conf import settings
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, PublicObjectSearchRequest, SimplePublicObjectInputForCreate, SimplePublicObjectInput, ApiException
from hubspot.crm.associations.v4 import BatchInputPublicDefaultAssociationMultiPost, ApiException
from hubspot.crm.contacts.exceptions import NotFoundException

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
        

class mirrorHubspotContacts(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        hubspot_secret = request.headers.get('HubSpotSecret')

        if not hubspot_secret:
            return Response({'error': 'HubSpotSecret not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hubspot_secret != "pat-na1-4de0014b-a034-43c6-aee2-b9261311121c":
            return Response({'error': 'Authentication failed: X-HubSpot-Secret mismatch.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            client = hubspot.Client.create(access_token="pat-na1-5db5fd91-2648-49cb-8a58-3299a4bc6a61")
            
            data = request.data
            characterID = data.get('character_id', '')

            properties = {
                "character_id": data.get('character_id', ''),
                "firstname": data.get('firstname', ''),
                "lastname": data.get('lastname', ''),
                "status_character": data.get('status_character', ''),
                "character_species": data.get('character_species', ''),
                "character_gender": data.get('character_gender', ''),
                "location_id": data.get('location_id', '')
            }


            public_object_search_request = PublicObjectSearchRequest(properties=["hs_object_id"], filter_groups=[{"filters":[{"propertyName":"character_id","value":characterID,"operator":"EQ"}]}],limit=1)
            response = client.crm.contacts.search_api.do_search(public_object_search_request=public_object_search_request)
            pprint(f'response-------------------{response}')
            if response.total > 0:
                contactID = response.results[0].properties.get('hs_object_id', None)
                simple_public_object_input = SimplePublicObjectInput(properties=properties)
                client.crm.contacts.basic_api.update(contact_id=contactID, simple_public_object_input=simple_public_object_input)
                return Response({'succes': 'The contact has been update.'}, status=status.HTTP_201_CREATED)

            simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=properties)
            client.crm.contacts.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
            return Response({'succes': 'The contact has been created.'}, status=status.HTTP_200_OK)

        except ApiException as e:
            return Response({'error': 'Failed to update/created client.'}, status=status.HTTP_403_FORBIDDEN)


        



public_object_search_request = PublicObjectSearchRequest(query="string", limit=0, after="string", sorts=["string"], properties=["string"], filter_groups=[{"filters":[{"highValue":"string","propertyName":"string","values":["string"],"value":"string","operator":"EQ"}]}])

















class mirrorHubspotCompanies(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        print("ENTRO AL ENDPOINT mirrorHubspotContacts XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        hubspot_secret = request.headers.get('HubSpotSecret')

        if not hubspot_secret:
            return Response({'error': 'HubSpotSecret not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hubspot_secret != "pat-na1-4de0014b-a034-43c6-aee2-b9261311121c":
            return Response({'error': 'Authentication failed: X-HubSpot-Secret mismatch.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            client = hubspot.Client.create(access_token="pat-na1-5db5fd91-2648-49cb-8a58-3299a4bc6a61")
            
            data = request.data
            contactId = data.get('hs_object_id', '')
            print(f'contactId_-------------------------{contactId}')
            properties = {
                "character_id": data.get('character_id', ''),
                "firstname": data.get('firstname', ''),
                "lastname": data.get('lastname', ''),
                "status_character": data.get('status_character', ''),
                "character_species": data.get('character_species', ''),
                "character_gender": data.get('character_gender', ''),
                "location_id": data.get('location_id', ''),
            }
            print("PROPIEDADES PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")
            pprint(properties)

            response = client.crm.contacts.basic_api.get_by_id(contact_id=contactId, archived=False)
            if response.status == 200:
                simple_public_object_input = SimplePublicObjectInput(properties=properties)
                client.crm.contacts.basic_api.update(contact_id=contactId, simple_public_object_input=simple_public_object_input)
                return Response({'succes': 'The contact has been update.'}, status=status.HTTP_201_CREATED)

        except NotFoundException:
            simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=properties)
            client.crm.contacts.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
            return Response({'succes': 'The contact has been created.'}, status=status.HTTP_200_OK)

        except ApiException as e:
            return Response({'error': 'Failed to update/created client.'}, status=status.HTTP_403_FORBIDDEN)



