"""
Sole purpose of this function is to extract data from instagram's API
"""

import json

from mypy_extensions import TypedDict

from qinstagram.utils import haversine_distance
from qinstagram.transforms import standardize_instagram_posts
from qinstagram.instagram import Instagram
from qinstagram.types import (
    INSTA_LOCATION,
    INSTA_USER,
    QueryType,
    GeoLocation,
    InstagramPosts,
    RawInstagramPosts,
    RawInstagramLocation,
    RawInstagramLocationSearch,
    RawInstagramLocationQuery
)


""" Helper functions (to determine if success or not) """


def instagram_search_location(location_name: str, geolocation: GeoLocation, count: int = 1) -> RawInstagramLocationSearch:
    """
    Queries instagram location and returns GraphQL dump

    Params:
        location_name:  Name of location
        geolocation:    (Lat, Lng) of the location
        count:          How many posts to scrape from location
    """

    instagram = Instagram(INSTA_LOCATION)

    try:
        # return json
        ret_json = {}

        # Get base location data
        location_data = instagram.search_location(location_name, geolocation)

        # No such place
        if location_data['location'] is None:
            return {'success': False}

        location_query_id = None

        # Sometimes page does not exist on insta, need to use fb
        if location_data['location']['pk'] != '0':
            location_query_id = location_data['location']['pk']
        else:
            location_query_id = location_data['location']['facebook_places_id']

        location_insta_data = instagram.query(
            location_query_id,
            count=count
        )

        ret_json['location'] = location_data['location']
        ret_json['posts'] = location_insta_data

    except Exception:
        return {'success': False}

    # TODO: Perform ML on posts?
    # Or compose functions in cloud function API...
    ret_json['success'] = True

    return ret_json


def instagram_query_location(location_id: str, count: int) -> RawInstagramLocationQuery:
    """
    Queries instagram location and returns GraphQL dump

    Params:
        location_id:  id of location
        count:          How many posts to scrape from location
    """

    instagram = Instagram(INSTA_LOCATION)

    try:
        # return json
        ret_json = {}

        location_insta_data = instagram.query(
            location_id,
            count=count
        )

        ret_json['posts'] = location_insta_data

    except Exception:
        return {'success': False}


    ret_json['success'] = True
    return ret_json


""" Request Handlers (used to xform data to a standard format) """


def search_location(request_json) -> TypedDict(
        'QueryLocation',
        {
            'location': RawInstagramLocation,
            'posts': InstagramPosts,
            'success': bool
        }
    ):
    """
    Searches for location name etc
    """

    # Make sure payload is correct
    location_name = request_json.get('location_name', None)
    latitude = request_json.get('latitude', None)
    longitude = request_json.get('longitude', None)
    count = request_json.get('count', 1)

    try:
        latitude = float(latitude)
        longitude = float(longitude)

    except:
        latitude = None
        longitude = None

    if location_name is None or latitude is None or longitude is None:
        response = {'error': 'invalid search_location payload'}
        return response, 400

    # Query instagram
    ret: RawInstagramLocationSearch = instagram_search_location(
        location_name, (latitude, longitude), count
    )
    
    if ret['success']:
        # ret['posts']: RawInstagramPosts
        ret['posts']: InstagramPosts = standardize_instagram_posts(ret['posts'])
    return ret, 200 if ret['success'] else 404


def query_location(request_json) -> TypedDict(
        'QueryLocation',
        {
            'posts': InstagramPosts,
            'success': bool
        }
    ):
    # Make sure payload is correct
    location_id = request_json.get('location_id', None)
    count = request_json.get('count', 32)

    try:
        count = int(count)
    except:
        count = 32

    if location_id is None:
        response = {'error': 'invalid query_location payload'}
        return response, 400

    # Query instagram
    ret: RawInstagramLocationQuery = instagram_query_location(location_id, count)
    
    if ret['success']:
        # ret['posts']: RawInstagramPosts
        ret['posts']: InstagramPosts = standardize_instagram_posts(ret['posts'])
    return ret, 200 if ret['success'] else 404


""" Lambda main function logic """


def lambda_main_function(event, context):
    """
    LAMBDA_PROXY is gonna format the request so the
    parameter `event` is going to be in this format:

    {
        "resource": "Resource path",
        "path": "Path parameter",
        "httpMethod": "Incoming request's method name"
        "headers": {Incoming request headers}
        "queryStringParameters": {query string parameters }
        "pathParameters":  {path parameters}
        "stageVariables": {Applicable stage variables}
        "requestContext": {Request context, including authorizer-returned key-value pairs}
        "body": "A JSON string of the request payload."
        "isBase64Encoded": "A boolean flag to indicate if the applicable request payload is Base64-encode"
    }
    """
    try:
        body_json = json.loads(event['body'])
        req_action = body_json.get('action', None)

    except:
        req_action = None

    # TODO: Change this so only grammable is allowed
    cors_headers = {
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        }
    }

    if req_action is None:
        return {
            "statusCode": 400,
            **cors_headers,
            "body": json.dumps({'error': 'invalid payload'})
        }

    # Mutation :(
    body_ret, status_code = None, None

    # Search by location name
    if req_action == 'search_location':
        body_ret, status_code = search_location(body_json)

    # Query location information
    # (Get back photos etc)
    if req_action == 'query_location':
        body_ret, status_code = query_location(body_json)

    # Preview location
    # Search by location name
    if req_action == 'preview_location':
        body_ret, status_code = query_location({**body_json, 'count': 0})

    # Body ret is dict if success
    if type(body_ret) is dict:
        return {
            'statusCode': status_code,
            **cors_headers,
            'body': json.dumps(body_ret)
        }

    return {
        "statusCode": 400,
        **cors_headers,
        "body": json.dumps({'error': 'invalid action'})
    }


if __name__ == '__main__':
    pass
    # ret, status_code = query_location({'location_id': '769182129910072'})
    # print(json.dumps(ret))
    ret, status_code = search_location({
        'location_name': 'Afghanistan Qal‘ah-ye Kūf',
        'latitude': -33.8900694,
        'longitude': 151.2719358,
    })
    # print(haversine_distance(34.044151, -118.26537, 34.05049, -118.24406))
    # {
    #     "action": "search_location",
    #     "location_name": "redbird",
    #     "latitude": 34.044151,
    #     "longitude": -118.24406,
    # }
    # {
    #     "action": "query_location",
    #     "location_id": "1223657931030868"
    # }
