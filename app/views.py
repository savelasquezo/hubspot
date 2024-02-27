import os, ramapi, hubspot, re
from ramapi import *

from django.conf import settings
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, PublicObjectSearchRequest, SimplePublicObjectInputForCreate, SimplePublicObjectInput, ApiException
from hubspot.crm.associations.v4 import BatchInputPublicDefaultAssociationMultiPost, ApiException

from app.serializers import CharacterSerializer, LocationSerializer

HUBSOPT_SOURCE_KEY = settings.HUBSOPT_SOURCE_KEY
HUBSOPT_MIRROR_KEY = settings.HUBSOPT_MIRROR_KEY

class requestHS(generics.GenericAPIView):
    """
    Generic API view for handling requests related to characters and locations.

    Methods:
    - getClients: Fetches client information from HubSpot using the provided access token.
    - getCompanies: Fetches company information from HubSpot using the provided access token.
    - makeAssociations: Creates associations between clients and companies based on matching location IDs.
    """
    def getClients(self, access_token):
        """
        Fetches client information from HubSpot using the provided access token.

        :param access_token: HubSpot access token for authentication.
        :type access_token: str
        :return: List of dictionaries containing client information.
        :rtype: list
        """
        try:
            client = hubspot.Client.create(access_token=access_token)

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


    def getCompanies(self, access_token):
        """
        Fetches company information from HubSpot using the provided access token.

        :param access_token: HubSpot access token for authentication.
        :type access_token: str
        :return: List of dictionaries containing company information.
        :rtype: list
        """
        try:
            client = hubspot.Client.create(access_token=access_token)

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


    def makeAssociations(self, access_token):
        """
        Creates associations between clients and companies based on matching location IDs.

        :param access_token: HubSpot access token for authentication.
        :type access_token: str
        :return: None
        """
        data_clients = self.getClients(access_token=access_token)
        dict_clients = [
            {
                'client': client['id'],
                'location_id': client['properties'].get('location_id', None),
            }
            for client in data_clients
        ]

        data_companies = self.getCompanies(access_token=access_token)
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
        try:
            client = hubspot.Client.create(access_token=access_token)
            for batch in batchLocations:
                batch_input_public_default_association_multi_post = BatchInputPublicDefaultAssociationMultiPost(
                    inputs=batch
                )
                client.crm.associations.v4.batch_api.create_default(
                    from_object_type="contacts",
                    to_object_type="companies",
                    batch_input_public_default_association_multi_post=batch_input_public_default_association_multi_post
                )            

        except Exception as e:
            date = timezone.now().strftime("%Y-%m-%d %H:%M")
            with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
                f.write("fetchClients {} --> Error: {}\n".format(date, str(e)))


class requestRM(generics.GenericAPIView):
    """
    Generic API view for handling requests related to characters and locations.

    Methods:
    - isPrime: Checks if a number is prime.
    - get_characters: Retrieves characters from the RAM API, filtering prime IDs.
    - get_locations: Retrieves locations associated with prime ID characters.
    """
    def isPrime(self, n):
        """
        Check if a number is prime n (int).
        Returns:
        - bool: True if the number is prime, False otherwise.
        """
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    def get_characters(self):
        """
        Retrieves characters from the RAM API, filtering by prime IDs.

        :return: List of characters with prime IDs.
        :rtype: list
        """
        characters, page = [], 1
        while True:
            characters_data = ramapi.Character.get_page(page)
            characters.extend(characters_data['results'])
            if not characters_data['info']['next']:
                break
            page += 1
        data = [character for character in characters if self.isPrime(character['id'])]
        return data

    def get_locations(self):
        """
        Retrieves locations associated with prime ID characters.

        :return: List of locations.
        :rtype: list
        """
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
    """
    API view for handling requests related to contacts.

    Attributes:
    - permission_classes: List of permission classes, allowing any user to access.
    - serializer_class: Serializer class for character information.
    """
    permission_classes = [AllowAny]
    serializer_class = CharacterSerializer

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create batches of contacts in HubSpot.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :return: Response indicating the success or failure of the batch creation.
        :rtype: rest_framework.response.Response
        """
        try:
            data = self.get_characters()

            size = 50
            batchCharacters = [data[i:i+size] for i in range(0, len(data), size)]

            client = hubspot.Client.create(access_token=HUBSOPT_SOURCE_KEY)
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
    """
    API view for handling requests related to companies.

    Attributes:
    - permission_classes: List of permission classes, allowing any user to access.
    - serializer_class: Serializer class for location information.
    """
    permission_classes = [AllowAny]
    serializer_class = LocationSerializer

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create batches of companies in HubSpot.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :return: Response indicating the success or failure of the batch creation.
        :rtype: rest_framework.response.Response
        """
        try:
            data = self.get_locations()

            size = 50
            batchLocations = [data[i:i+size] for i in range(0, len(data), size)]

            client = hubspot.Client.create(access_token=HUBSOPT_SOURCE_KEY)
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



        

class mirrorHubspotContacts(generics.GenericAPIView):
    """
    API view for mirroring HubSpot contacts.

    Attributes:
    - permission_classes: List of permission classes, allowing any user to access.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to mirror HubSpot contacts.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :return: Response indicating the success or failure of the operation.
        :rtype: rest_framework.response.Response
        """
        hubspot_secret = request.headers.get('HubSpotSecret')

        if not hubspot_secret:
            return Response({'error': 'HubSpotSecret not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hubspot_secret != HUBSOPT_SOURCE_KEY:
            return Response({'error': 'Authentication failed: X-HubSpot-Secret mismatch.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            client = hubspot.Client.create(access_token=HUBSOPT_MIRROR_KEY)
            
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




class mirrorHubspotCompanies(generics.GenericAPIView):
    """
    API view for mirroring HubSpot companies.

    Attributes:
    - permission_classes: List of permission classes, allowing any user to access.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to mirror HubSpot companies.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :return: Response indicating the success or failure of the operation.
        :rtype: rest_framework.response.Response
        """
        hubspot_secret = request.headers.get('HubSpotSecret')

        if not hubspot_secret:
            return Response({'error': 'HubSpotSecret not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hubspot_secret != HUBSOPT_SOURCE_KEY:
            return Response({'error': 'Authentication failed: X-HubSpot-Secret mismatch.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            client = hubspot.Client.create(access_token=HUBSOPT_MIRROR_KEY)
            
            data = request.data
            locationID = data.get('location_id', '')

            properties = {
                "location_id": data.get('location_id', ''),
                "name": data.get('name', ''),
                "location_type": data.get('location_type', ''),
                "dimension": data.get('dimension', ''),
                "creation_date": data.get('creation_date', '')
            }


            public_object_search_request = PublicObjectSearchRequest(properties=["hs_object_id"], filter_groups=[{"filters":[{"propertyName":"location_id","value":locationID,"operator":"EQ"}]}],limit=1)
            response = client.crm.companies.search_api.do_search(public_object_search_request=public_object_search_request)
            if response.total > 0:
                companyID = response.results[0].properties.get('hs_object_id', None)
                simple_public_object_input = SimplePublicObjectInput(properties=properties)
                client.crm.companies.basic_api.update(company_id=companyID, simple_public_object_input=simple_public_object_input)
                return Response({'succes': 'The company has been update.'}, status=status.HTTP_201_CREATED)

            simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=properties)
            client.crm.companies.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
            return Response({'succes': 'The company has been created.'}, status=status.HTTP_200_OK)

        except ApiException as e:
            return Response({'error': 'Failed to update/created company.'}, status=status.HTTP_403_FORBIDDEN)


class mirrorHubspotAssociations(requestHS):
    """
    API view for mirroring HubSpot associations.

    Attributes:
    - permission_classes: List of permission classes, allowing any user to access.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create batches of associations in HubSpot.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :return: Response indicating the success or failure of the batch creation.
        :rtype: rest_framework.response.Response
        """
        try:
            self.makeAssociations(access_token=HUBSOPT_MIRROR_KEY)
            return Response({'succes': 'The batches of associations have been created.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            date = timezone.now().strftime("%Y-%m-%d %H:%M")
            with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
                f.write("requestAssociations {} --> Error: {}\n".format(date, str(e)))
            return Response({'error': 'Error fetching associations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class requestAssociations(requestHS):
    """
    API view for handling requests to create batches of associations in HubSpot.

    Attributes:
    - permission_classes: List of permission classes, allowing any user to access.
    """


    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create batches of associations in HubSpot.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :return: Response indicating the success or failure of the batch creation.
        :rtype: rest_framework.response.Response
        """
        try:
            self.makeAssociations(access_token=HUBSOPT_SOURCE_KEY)
            return Response({'succes': 'The batches of associations have been created.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            date = timezone.now().strftime("%Y-%m-%d %H:%M")
            with open(os.path.join(settings.BASE_DIR, 'logs/core.log'), 'a') as f:
                f.write("requestAssociations {} --> Error: {}\n".format(date, str(e)))
            return Response({'error': 'Error fetching associations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)