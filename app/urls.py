from django.urls import path
import app.views as view

urlpatterns = [
    path('request-contacts/', view.requestContacts.as_view(), name='request-contacts'),
    path('request-companies/', view.requestCompanies.as_view(), name='request-companies'),
    path('request-associations/', view.requestAssociations.as_view(), name='request-associations'),

    path('request-hubspot/', view.requestHubspot.as_view(), name='request-hubspot'),
]