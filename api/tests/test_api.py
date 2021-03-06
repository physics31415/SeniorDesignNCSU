import http.client
import json
import os
import sqlalchemy
import sys 
import time
import unittest, urllib
import flask

from flask import Flask, request, Response
from flask_testing import TestCase

sys.path.append('..')

from app import application
import db
import models
import api

from db import engine


"""
How to Get Coverage
python -m coverage run <file>
python -m coverage report
python -m coverage html (outputs coverage stats in html files for each file covered)

"""


class TestAPI(TestCase):
    """
    Class Tests API
    """ 

    TOKEN = None

    def create_app(self):
        """
        Creates app for testing
        """
        return application 


    def addUser(self):   
        headers = {'Content-type': 'application/json'}
        
        data = {
            "username": "ndseamon",
            "email": "ndseamon@gmail.com",
            "password": "password",
            "secret_code": "SeniorDesignS2020"
        }

        json_data = json.dumps(data)
        self.client().post('/createAccount', headers=headers, data=json_data)


    def login(self):
        headers = {'Content-type': 'application/json'}

        body = {
            "username": "ndseamon",
            "password": "password"
        }

        json_data = json.dumps(body)
        response =  self.client().post('/login', headers=headers, data=json_data)
        token =  response.json['token']

        return token


    def setUp(self):
        """
        Deletes and recreates new blank tables so that testing is idempotent
        Creates a user and logs the user in to generate session token
        """
        self.app = self.create_app()
        self.client = self.app.test_client

        time.sleep(.01)
        models.Base.metadata.drop_all(engine)

        time.sleep(.01)
        models.Base.metadata.create_all(engine)

        time.sleep(.01)
        self.addUser()

        time.sleep(.01)
        self.TOKEN = self.login()

    
    def post(self, endpoint, body):
        headers = {'Content-type': 'application/json', 'Authorization': "Bearer " + self.TOKEN}
        return self.client().post(endpoint, headers=headers, data=body)


    def requestWithQueryParams(self, endpoint, method, query_params=None):
        """
        Method used to cut down on duplicated code. Takes parameters to make request 
        and returns the http response. Includes Auth

        :param: body of request
        :param: string value of endpoint to use
        :param: query param (list of tuples)
        :return: http response object
        """
        if query_params:
            endpoint = endpoint + "?"
            for item in query_params:
                endpoint = endpoint + item[0] + "=" + item[1] + "&"

        headers = {'Content-type': 'application/json', 'Authorization': "Bearer " + self.TOKEN}

        if method == "DELETE":
            return self.client().delete(endpoint, headers=headers)
        elif method == "GET":
            return self.client().get(endpoint, headers=headers)


"""
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
This section tests raw text entry posts, delete and get functions
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""
class TestRawPostAndGetRaw(TestAPI):
    """
    Test raw entries
    """
    
    VALID_RAW_BODY = {
        
        "raw_text": "I love Merck", 
        "time": "2020-26-02 15:34:00", 
        "source": "TWITTER",
        "lat": "56.3304",
        "lon": "130.3221",
        "author": "Donald Trump"
    }

    VALID_RAW_BODY_TWO = {
        "raw_text": "I hate Merck becuase they kill babies 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "56.3304",
        "lon": "130.3221",
        "author": "Andrew Goncharov",
    }

    VALID_RAW_BODY_THREE = {
        "raw_text": "I hate Merck becuase they give babies autism with their vaccines 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "26.39",
        "lon": "129.19",
        "author": "Nathan Seamon"
    }

    RETURN_BODY_TWO = {
        'author': 'Andrew Goncharov', 
        'emojis': False, 
        'id': 2, 
        'lat': 56.3304, 
        'lon': 130.3221, 
        'processed': False, 
        'raw_text': 'I hate Merck becuase they kill babies 😠',
        'source': 'TWITTER', 
        'time': '2020-01-03 03:33:21'
    }

    def testPostRawTextEntryValid(self):
        """ 
        Test valid raw text entry post 
        """
        response =  self.post('/rawTextEntry', json.dumps(self.VALID_RAW_BODY))

        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)


    def testPostRawTextEntryDuplicate(self):
        """ 
        Test duplicate raw entry failure 
        """

        # first post
        response = self.post('/rawTextEntry', json.dumps(self.VALID_RAW_BODY))
        
        # first post sanity check
        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)
        
        # second post
        response = self.post('/rawTextEntry', json.dumps(self.VALID_RAW_BODY))
        
        # second post failure verification
        self.assertEqual(response.json, "Text entry with time and text already exists")
        self.assertEqual(400, response.status_code)


    def testPostRawInvalidDatetime(self):
        """
        Tests raw text entry post with invlaid time
        """
        
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-36-02 5:34:0", 
            "source": "TWITTER",
            "lat": "56.3304",
            "lon": "130.3221",
            "author": "Donald Trump"
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, 'Invalid time format, must be YYYY-DD-MM HH:MM:SS')
        self.assertEqual(400, response.status_code)


    def testPostRawNoAuthor(self):
        """
        Tests valid raw text entry post with a bad url
        """
        
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lat": "56.3304",
            "lon": "130.3221",
            "url": "bad url"
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Invalud url. Must start with http or https")
        self.assertEqual(400, response.status_code)

    def testPostRawNoAuthor(self):
        """
        Tests valid raw text entry post with out author
        """
        
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lat": "56.3304",
            "lon": "130.3221",
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)


    def testInvalidLatLon(self):
        """
        Tests invalid lats and lons
        """
        
        # missing lon
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lat": "56.3304",
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Missing parameter lon")
        self.assertEqual(400, response.status_code)

        # missing lat
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lon": "130.3221",
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Missing parameter lat")
        self.assertEqual(400, response.status_code)

        # out of range longitudue
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lon": "190.3221",
            "lat": "20"
        }
        
        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Longitude must be between -180 and 180")
        self.assertEqual(400, response.status_code)


        # out of range latitude
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lon": "160.3221",
            "lat": "200"
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Latitude must be between -90 and 90")
        self.assertEqual(400, response.status_code)


    def testPostRawInvalidSource(self):
        """
        Tests valid raw text entry post with invalid source
        """
        
        body = {
            "raw_text": "I love Merck", 
            "time": "2020-26-02 15:34:00", 
            "source": "The guy on the corner",
            "lat": "56.3304",
            "lon": "130.3221",
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Invalid source")
        self.assertEqual(400, response.status_code)


    def testPostRawMissingText(self):
        """
        Tests valid raw text entry post without raw text
        """
        
        body = {
            "time": "2020-26-02 15:34:00", 
            "source": "TWITTER",
            "lat": "56.3304",
            "lon": "130.3221",
        }

        response = self.post("rawTextEntry", json.dumps(body))
        
        self.assertEqual(response.json, "Missing parameter raw_text")
        self.assertEqual(400, response.status_code)


    def testPostNoBody(self):
        """
        Tests a post without a body
        """
        response = self.post("rawTextEntry", None)
        
        # import pdb; pdb.set_trace()
        # self.assertEqual(response.json, "Missing request body")
        self.assertEqual(400, response.status_code)


    def testPostNoAuth(self):
        """
        Tests a post without auth
        """
        headers = {'Content-type': 'application/json',}
        response =  self.client().post("rawTextEntry", headers=headers, data=json.dumps(self.VALID_RAW_BODY))
        self.assertEqual(response.json['message'], "Token is missing")
        self.assertEqual(401, response.status_code)
        

    def testGetRawText(self):
        """
        Tests a posting and retriving raw text entries
        """

        #first post
        response = self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY))
        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)
 

        #second post
        response = self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY_TWO))
        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)


        #third post
        response = self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY_THREE))
        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)
        

        #test getting all
        response = self.requestWithQueryParams("/rawTextEntries", "GET")

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.json))
        self.assertEqual(self.RETURN_BODY_TWO, response.json[1])

        #test min
        response = self.requestWithQueryParams("/rawTextEntries","GET", query_params=[('min', '2')])

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(self.RETURN_BODY_TWO, response.json[0])

        #test max
        response = self.requestWithQueryParams("/rawTextEntries", "GET", query_params=[('max', '2')])

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(self.RETURN_BODY_TWO, response.json[1])

        #test max and min
        response = self.requestWithQueryParams("/rawTextEntries", "GET", query_params=[('max', '2'), ('min', '2')])

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertEqual(self.RETURN_BODY_TWO, response.json[0])

        #test getting invalid range
        response = self.requestWithQueryParams("/rawTextEntries", "GET", query_params=[("min", "3"), ("max", "1")])
        
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json, "Min must be less than max")



    def testGetRawTextNoAuth(self):
        """
        Tests get method without auth
        """

        #first post
        response = self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY))
        self.assertEqual(response.json, "Raw entry successfully added")
        self.assertEqual(200, response.status_code)
    
        
        headers = {'Content-type': 'application/json'}

        response =  self.client().get("rawTextEntries", headers=headers)
        self.assertEqual(401, response.status_code)


    def testDeleteRawText(self):
        """
        Tests a posting and retriving raw text entries
        """

        #first post
        self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY))

        #second post
        self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY_TWO))

        #third post
        self.post("rawTextEntry", json.dumps(self.VALID_RAW_BODY_THREE))
 
        #delete 3
        resp = self.requestWithQueryParams( "/deleteRawTextEntry", "DELETE", query_params=[("id", "3")])

        self.assertEqual(200, resp.status_code)


        #test getting all with 3 deleted
        response = self.requestWithQueryParams("/rawTextEntries", "GET")

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(self.RETURN_BODY_TWO, response.json[1])


        #delete 1
        self.requestWithQueryParams( "/deleteRawTextEntry", "DELETE", query_params=[("id", "1")])

        #test getting all with 1 deleted
        response = self.requestWithQueryParams("/rawTextEntries", "GET")

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertEqual(self.RETURN_BODY_TWO, response.json[0])


        #delete 2
        self.requestWithQueryParams( "/deleteRawTextEntry", "DELETE", query_params=[("id", "2")])

        #test getting all with 1 deleted
        response = self.requestWithQueryParams("/rawTextEntries", "GET")

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.json))


"""
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
This section tests instant processing 
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""
class TestInstantProcessing(TestAPI):
    
    RAW_TEXT_BODY_THREAT = {
           
        "raw_text": "I hate Merck becuase they kill babies 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "47.1",
        "lon": "8.5",
        "author": "Andrew Goncharov"
    }

    RAW_TEXT_BODY_KW_THREAT = {

        "raw_text": "I hate Nasonex becuase it makes babies high 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "47.1",
        "lon": "8.5",
        "author": "Andrew Goncharov"
    }
    

    RAW_TEXT_BODY_OUT_OF_RANGE = {
           
        "raw_text": "I hate Merck becuase they kill babies 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "56.3304",
        "lon": "130.3221",
        "author": "Andrew Goncharov"
    }

    RAW_TEXT_BODY_NONTHREAT = {
           
        "raw_text": "I love Merck and their COVID-19 vaccine", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "47.1",
        "lon": "8.5",
        "author": "Andrew Goncharov"
    }

    RAW_TEXT_BODY_UNRELATED_THREAT = {
        "raw_text": "I hate Corona, its a shitty beer", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "47.1",
        "lon": "8.5",
        "author": "Andrew Goncharov"
    }

    OUT_OF_RANGE_RESP = { "message": "Not in range of a facility" }

    UNRELATED_KEY_WORD_RESP = { "message": "Not related to Merck or its interests" }

    THREAT_RESPONSE_VALID = {
        'id': 1,
        'raw': {
            'author': 'Andrew Goncharov', 
            'lat': 47.1, 
            'lon': 8.5, 
            'raw_text': 
            'I hate Merck becuase they kill babies 😠', 
            'source': 'TWITTER', 
            'time': '2020-01-03 03:33:21',
            'url': None
            }, 
        'threat_type': 'NEGATIVE', 
        'time': '2020-05-03 20:50:47'
    }

    THREAT_RESPONSE_KW_VALID = {
        'id': 1,
        'raw': {
            'author': 'Andrew Goncharov', 
            'lat': 47.1, 
            'lon': 8.5, 
            'raw_text': 
            'I hate Nasonex becuase it makes babies high 😠', 
            'source': 'TWITTER', 
            'time': '2020-01-03 03:33:21',
            'url': None
            }, 
        'threat_type': 'NEGATIVE', 
        'time': '2020-05-03 20:50:47'
    }


    def testValidInstantProcessingOutOfRange(self):
        """
        Tests valid instant processing out of range
        """
        response = self.post("instantProcessing", json.dumps(self.RAW_TEXT_BODY_OUT_OF_RANGE))
 
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.OUT_OF_RANGE_RESP, response.json)
    

    def testValidInstantProcessingThreat(self):
        """
        Tests valid instant processing of a threat
        """
        response = self.post("instantProcessing", json.dumps(self.RAW_TEXT_BODY_THREAT))
        self.assertEqual(200, response.status_code)

        self.assertEqual(self.THREAT_RESPONSE_VALID['id'], response.json['id'])
        self.assertEqual(self.THREAT_RESPONSE_VALID['raw'], response.json['raw'])
        self.assertEqual(self.THREAT_RESPONSE_VALID['threat_type'], response.json['threat_type'])
    

    def testValidInstantProcessingThreatKW(self):
        """
        Tests valid threat with Merck product
        """
        response = self.post("instantProcessing", json.dumps(self.RAW_TEXT_BODY_KW_THREAT))
        self.assertEqual(200, response.status_code)

        self.assertEqual(self.THREAT_RESPONSE_KW_VALID['id'], response.json['id'])
        self.assertEqual(self.THREAT_RESPONSE_KW_VALID['raw'], response.json['raw'])
        self.assertEqual(self.THREAT_RESPONSE_KW_VALID['threat_type'], response.json['threat_type'])


    def testValidInstantProcessingNonThreat(self):
        """
        Tests valid instant processing of a nonthreat
        """
        response = self.post("instantProcessing", json.dumps(self.RAW_TEXT_BODY_NONTHREAT))
        self.assertEqual(200, response.status_code)

        self.assertEqual({'message': 'Nonnegative sentiment'}, response.json)


    def testValidInstantProcessingUnrelatedThreat(self):
        """
        Tests valid instant processing of an unrelated threat
        """
        response = self.post("instantProcessing", json.dumps(self.RAW_TEXT_BODY_UNRELATED_THREAT))
        self.assertEqual(200, response.status_code)

        self.assertEqual(self.UNRELATED_KEY_WORD_RESP, response.json)


    def testInstantProcessingThreatNoAuth(self):
        """
        Tests instant processing with no auth
        """
        headers = {'Content-type': 'application/json',}
        response =  self.client().post("instantProcessing", headers=headers, data=json.dumps(self.RAW_TEXT_BODY_THREAT))
        self.assertEqual(401, response.status_code)


"""
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
This section tests the health status endpoint
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""
class TestHealthStatus(TestAPI):
    """
    Test health status
    """

    def testValidHealthStatus(self):
        """
        Tests valid instant processing of a nonthreat
        """
        response = self.requestWithQueryParams("/healthstatus",  "GET")
        self.assertEqual(200, response.status_code)

        self.assertEqual({"db_status": "Healthy"}, response.json)



"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
This section tests processed text entry posts, delete and get functions
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""
class TestProccessedEntries(TestAPI):
    """
    Test processed entries
    """
    
    VALID_RAW_BODY_TWO = {  
        "raw_text": "I love Merck", 
        "time": "2020-26-02 15:34:00", 
        "source": "TWITTER",
        "lat": "56.3304",
        "lon": "130.3221",
        "author": "Donald Trump"
    }

    VALID_RAW_BODY_ONE = {
        "raw_text": "I hate Merck becuase they kill babies 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "56.3304",
        "lon": "130.3221",
        "author": "Andrew Goncharov",
        "url": "http://whitehouse.gov"
    }

    VALID_RAW_BODY_THREE = {
        "raw_text": "I hate Merck becuase they give babies autism with their vaccines 😠", 
        "time": "2020-01-03 03:33:21", 
        "source": "TWITTER",
        "lat": "26.39",
        "lon": "129.19",
        "author": "Nathan Seamon"
    }

    VALID_PROCESSED_BODY_ONE_RESPONSE = {
        'id': 1,
        'raw': {
            'author': 'Andrew Goncharov', 
            'lat': 56.3304, 
            'lon': 130.3221, 
            'raw_text': 
            'I hate Merck becuase they kill babies 😠', 
            'source': 'TWITTER', 
            'time': '2020-01-03 03:33:21',
            "url": "http://whitehouse.gov"
            }, 
        'threat_type': 'NEGATIVE', 
        'time': '2020-05-03 20:50:47'
    }

    VALID_PROCESSED_BODY_ONE_POST = {
        'time': '2020-05-03 20:50:47',
        'raw': 1,
        'threat_type': 'NEGATIVE'
    }

    VALID_PROCESSED_BODY_TWO_POST = {
        'time': '2020-04-03 10:03:02',
        'raw': 2,
        'threat_type': 'NEGATIVE'
    }

    VALID_PROCESSED_BODY_THREE_POST = {
        'time': '2020-02-04 11:03:02',
        'raw': 3,
        'threat_type': 'NEGATIVE'
    }


    def testPostProcessedTextEntryValid(self):
        """ 
        Test valid processed text entry post 
        """
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_ONE))
        response = self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_ONE_POST))
    
        self.assertEqual('Processed entry successfully added', response.json)
        self.assertEqual(200, response.status_code)


    def testPostProcessedTextEntryBadSource(self):
        """ 
        Test invalid processed text entry post. Missing source
        """
        response = self.post("/processedTextEntry", self.VALID_PROCESSED_BODY_ONE_POST)
  
        # self.assertEqual('Source ID does not exist', response.json)
        self.assertEqual(400, response.status_code)

    
    def testGetProcessedTextEntryValid(self):
        """ 
        Test get processed text entry  
        """
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_ONE))
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_TWO))
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_THREE))

        self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_ONE_POST))
        self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_TWO_POST))
        self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_THREE_POST))
        
        #test getting all
        response = self.requestWithQueryParams("/processedTextEntries", "GET")
        
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.json))
        self.assertEqual(self.VALID_PROCESSED_BODY_ONE_RESPONSE, response.json[0])

        #test max
        response = self.requestWithQueryParams("/processedTextEntries", "GET", query_params=[("max", "2")])
        
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(response.json[1]['id'], 2)

        #test getting min
        response = self.requestWithQueryParams("/processedTextEntries", "GET", query_params=[("min", "2")])
        
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(response.json[0]['id'], 2)

        #test getting min and max
        response = self.requestWithQueryParams("/processedTextEntries", "GET", query_params=[("min", "2"), ("max", "2")])
        
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json))
        self.assertEqual(response.json[0]['id'], 2)

        #test getting invalid range
        response = self.requestWithQueryParams("/processedTextEntries", "GET", query_params=[("min", "3"), ("max", "1")])
        
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json, "Min must be less than max")



    def testDeleteProcessedTextEntry(self):
        """ 
        Test get processed text entry  
        """
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_ONE))
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_TWO))
        self.post("/rawTextEntry", json.dumps(self.VALID_RAW_BODY_THREE))

        self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_ONE_POST))
        self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_TWO_POST))
        self.post("/processedTextEntry", json.dumps(self.VALID_PROCESSED_BODY_THREE_POST))

        
        # delete two
        self.requestWithQueryParams( "/deleteProcessedTextEntry", "DELETE", query_params=[("id", "2")])

        #test getting all with 2 deleted
        response = self.requestWithQueryParams("/processedTextEntries", "GET")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(3, response.json[1]['id'])


        #test getting all raw with one entry deleted
        response = self.requestWithQueryParams("/rawTextEntries", "GET")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))
        self.assertEqual(3, response.json[1]['id'])


class TestCSV(TestAPI):
    """
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    This section tests csv upload
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    """

    def testUploadValidCSV(self):
        """
        Test valid csv file upload. Includes duplicate entries and optional
        paramaters
        """
        file_test =  open("test.csv", "rb")
        headers = {'Content-type': 'multipart/form-data', 'Authorization': "Bearer " + self.TOKEN}
        response = self.client().post("/csv", data={'file': file_test}, headers=headers)
        self.assertEqual(200, response.status_code)
        
        # This tests that all raw entries were added with the exception of the duplicate entry.
        # It includes variations of option author, url, and time parameters
        response = self.requestWithQueryParams("/rawTextEntries", "GET")
        self.assertEqual(8, len(response.json))

        #this tests that 3 of the entries were marked as threats
        response = self.requestWithQueryParams("/processedTextEntries", "GET")
        self.assertEqual(7, len(response.json))


if __name__ == '__main__':
    unittest.main()
