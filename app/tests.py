import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from app.views import requestRM

class RequestRMTest(TestCase):

    def setUp(self):
        self.view = requestRM()

    def test_isPrime(self):
        primes = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        for number in range(1, 100):
            expected_result = number in primes
            self.assertEqual(self.view.isPrime(number), expected_result)
        
        print("isPrime: All tests passed successfully!")

    @patch('app.views.ramapi.Character.get_page')
    def test_get_characters(self, mock_get_page):
        mock_get_page.return_value = {
            'info': {
                'count': 2,
                'pages': 1,
                'next': None,
                'prev': None
            },
            'results': [
                {'id': 1, 'name': 'Rick Sanchez'},
                {'id': 2, 'name': 'Morty Smith'},
            ]
        }
        result = self.view.get_characters()
        self.assertEqual(result, [{'id': 1, 'name': 'Rick Sanchez'}, {'id': 2, 'name': 'Morty Smith'}])
        print("getCharacters: All tests passed successfully!")


    @patch('app.views.requestRM.get_characters')
    @patch('app.views.ramapi.Location.get')
    def test_get_locations(self, mock_get_characters, mock_location_get):
        # Simulamos la respuesta de get_characters
        mock_get_characters.return_value = {
            'info': {
                'count': 3,
                'pages': 1,
                'next': None,
                'prev': None
            },
            'results': [
                {'location': {'url': 'https://rickandmortyapi.com/api/location/1'}},
                {'location': {'url': 'https://rickandmortyapi.com/api/location/2'}},
                {'location': {'url': 'https://rickandmortyapi.com/api/location/3'}},
            ]
        }

        # Simulamos la respuesta de Location.get con datos más realistas
        mock_location_get.return_value = {
            'info': {
                'count': 3,
                'pages': 1,
                'next': None,
                'prev': None
            },
            'results': [
                {'id': 1, 'name': 'Location 1', 'type': 'Planet', 'dimension': 'Dimension C-137', 'url': 'https://rickandmortyapi.com/api/location/1'},
                {'id': 2, 'name': 'Location 2', 'type': 'Cluster', 'dimension': 'unknown', 'url': 'https://rickandmortyapi.com/api/location/2'},
                {'id': 3, 'name': 'Location 3', 'type': 'Unknown', 'dimension': 'Dimension XYZ', 'url': 'https://rickandmortyapi.com/api/location/3'},
            ]
        }

        result = self.view.get_locations()

        expected_result = [
            {'id': 1, 'name': 'Location 1', 'type': 'Planet', 'dimension': 'Dimension C-137'},
            {'id': 2, 'name': 'Location 2', 'type': 'Cluster', 'dimension': 'unknown'},
            {'id': 3, 'name': 'Location 3', 'type': 'Unknown', 'dimension': 'Dimension XYZ'},
        ]

        self.assertEqual(result, expected_result, 'Test failed for get_locations')

        # También podrías verificar si las funciones mock fueron llamadas correctamente
        mock_get_characters.assert_called_once()
        mock_location_get.assert_called_with([1, 2, 3])

        print("test_get_locations: All tests passed successfully!")


if __name__ == '__main__':
    unittest.main()