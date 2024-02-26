from django.urls import path
import app.views as view

urlpatterns = [
    path('request-contacts/', view.requestContacts.as_view(), name='request-contacts'),
    path('request-companies/', view.requestCompanies.as_view(), name='request-companies'),
    path('request-associations/', view.requestAssociations.as_view(), name='request-associations'),

    path('mirror-hubspot-contacts/', view.mirrorHubspotContacts.as_view(), name='mirror-hubspot-contacts'),
    path('mirror-hubspot-companies/', view.mirrorHubspotCompanies.as_view(), name='mirror-hubspot-companies'),
]