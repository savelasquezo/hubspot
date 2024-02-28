
# Hubspot Test 

Hubspot test is developed in order to validate technical knowledge in backend development and integration with the hubspot platform


## Overview

The HubspotTest provides a simple basis for the Migration and Integration of data in this case obtained from the RAMAPI APP, which allows integration with Hubspot services.



## Installation Locally (Only Migrations)

Clone hubspot repository form github and move to folder of the proyect

```bash
  $ git clone git@github.com:savelasquezo/hubspot.git
  $ cd hubspot
```

Create a virtual environment, activate said environment and install the libraries and dependencies of the project.

```bash
  $ python3 -m venv venv
  $ source venv/bin/activate
  $ pip install -r requirements.txt
```

Run the django service; remember to keep this window active

```bash
  $ python3 manage.py runserver
```


## Usage

In this application we will use Postman to run the different endpoints and execute the migrations. The integrations will be automatic. We will list the different endpoints and their purpose


### Source Platform

Migrate character with prime id from ramapi to hubspot as contacts and if the companies already exist, create the appropriate associations
```bash
POST https://hubspot-d04aa4727870.herokuapp.com/app/request-contacts/
```

Migrate the locations associated with the prime characters from ramapi to hubspot as companies and if the contacts already exist, create the appropriate associations
```bash
POST https://hubspot-d04aa4727870.herokuapp.com/app/request-companies/
```

Manually create associations between contacts and companies; It is only optional if you want to rectify the associations.
```bash
POST https://hubspot-d04aa4727870.herokuapp.com/app/request-associations/
```

### Mirror Platform

Manually create associations between contacts and companies; Once the update process is finished, it is recommended to execute it.
```bash
POST https://hubspot-d04aa4727870.herokuapp.com/app/mirror-hubspot-associations/
```


## Environment Variables

For your convenience, the .env file has been added so you do not need to define additional environment variables. Although it is recognized that it is not a good practice





## Thanks for All!
### Simon Velasquez Ortiz - Fuzer Developer!


