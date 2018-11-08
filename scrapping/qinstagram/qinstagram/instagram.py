"""
Instagram Scrapper
"""

import hashlib
import re
import json
import requests 

from mypy_extensions import TypedDict
from typing import Union
from urllib.parse import urlencode, quote_plus

from qinstagram.utils import haversine_distance
from qinstagram.types import (
    INSTA_LOCATION,
    INSTA_USER,
    QueryType,
    GeoLocation,
    RawInstagramLocation
)

class Instagram:
    """
    Class to get instagram's page (e.g. location or user)
    """
    _location_search_url = 'https://www.instagram.com/web/search/topsearch/?context=blended&query={}'
    _hashtag_explore_url = 'https://www.instagram.com/explore/tags/{}'

    _query_urls = {}
    _query_urls[INSTA_LOCATION] = dict(
        base_url='https://www.instagram.com/explore/locations/{}',
        container_url='https://www.instagram.com/static/bundles/base/LocationPageContainer.js/{}.js'
    )
    _query_urls[INSTA_USER] = dict(
        base_url='https://www.instagram.com/{}',
        container_url='https://www.instagram.com/static/bundles/base/ProfilePageContainer.js/{}.js'
    )

    _query_regex = {}
    _query_regex[INSTA_LOCATION] = dict(
        container_re=r"<link rel=\"preload\" href=\"/static/bundles/base/LocationPageContainer.js/(.+).js\" as=\"script\"",
        hash_re=r"locationPosts.byLocationId.get\(t\).pagination},queryId:\"(\w+)\",queryParams:"
    )
    _query_regex[INSTA_USER] = dict(
        container_re=r"<link rel=\"preload\" href=\"/static/bundles/base/ProfilePageContainer.js/(.+).js\" as=\"script\"",
        hash_re=r"void 0===r\?void 0:r.pagination},queryId:\"(\w+)\",queryParams:"
    )

    _query_base_headers = {
        'Accept': '*/*',
        'Host': 'www.instagram.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
    }

    _graphql_keys = {}
    _graphql_keys[INSTA_LOCATION] = dict(
        type='location',
        page='LocationsPage',
        media='edge_location_to_media',
        top_posts='edge_location_to_top_posts'
    )
    _graphql_keys[INSTA_USER] = dict(
        type='user',
        page='ProfilePage',
        media='edge_owner_to_timeline_media'
    )

    def __init__(self, queryType: QueryType):
        self._base_url = self._query_urls[queryType]['base_url']
        self._container_url = self._query_urls[queryType]['container_url']

        self._container_re = self._query_regex[queryType]['container_re']
        self._hash_re = self._query_regex[queryType]['hash_re']

        self._graphql_vals = self._graphql_keys[queryType]

    @staticmethod
    def get_insta_window_json(page_html: str):
        """
        Converts initial window request to JSON data
        """
        gmaps_json_blob = re.findall(
            r"window._sharedData\s=\s(.+);</script>", page_html)[0]
        return json.loads(gmaps_json_blob)

    def extract_window_data(self, window_data_json):
        """
        Extracts key components to query next page
        """
        graphql_json = window_data_json['entry_data'][self._graphql_vals['page']
                                                      ][0]['graphql'][self._graphql_vals['type']]

        csrf_token = window_data_json['config']['csrf_token']
        profile_id = graphql_json['id']
        rhx_gis = window_data_json['rhx_gis']
        end_cursor = graphql_json[self._graphql_vals['media']]['page_info'].get(
            'end_cursor', None
        )
        total_media_count = graphql_json[self._graphql_vals['media']]['count']
        has_next_page = graphql_json[self._graphql_vals['media']]['page_info'].get(
            'has_next_page', False
        )
        edges_json = graphql_json[self._graphql_vals['media']]['edges']

        top_posts_json = {'top_posts': []}
        if 'top_posts' in self._graphql_vals:
            top_posts_json['top_posts'] = graphql_json[self._graphql_vals['top_posts']]['edges']

        return {
            'csrf_token': csrf_token,
            'profile_id': profile_id,
            'rhx_gis': rhx_gis,
            'end_cursor': end_cursor,
            'has_next_page': has_next_page,
            'edges': edges_json,
            'total_media_count': total_media_count,
            **top_posts_json
        }

    @staticmethod
    def compute_gis(rhx_gis, query_params):
        """
        Compute Instagram GIS Header
        """
        bs = str.encode('{}:{}'.format(rhx_gis, query_params))
        return hashlib.md5(bs).hexdigest()

    def get_insta_query_hash(self, page_html: str):
        """
        Gets query hash from initial json loaded from window (for graph ql)
        """
        containerId = re.findall(self._container_re, page_html)[0]
        r = requests.get(self._container_url.format(containerId))
        query_hash = re.findall(self._hash_re, r.text)[0]
        return query_hash

    def query(self, query_id: Union[str, int], count: int = 32):
        """
        Queries graphql and returns formatted graphql dump

        Params:
            query_id: Instagram id (places will be an id, users will be username)
            count: How many posts to scrap
        """
        r = requests.get(self._base_url.format(query_id),
                         headers=self._query_base_headers)

        # Extract HTML from page
        page_html = r.text

        # Extract JSON blob from HTML page
        window_data_json = self.get_insta_window_json(page_html)

        # Extract query_hash and session from raw HTML data and JSON blob
        query_hash = self.get_insta_query_hash(page_html)
        session_json = self.extract_window_data(window_data_json)

        # Initial list of edges (our data)
        edges_list = session_json['edges']
        top_posts = session_json['top_posts']
        total_media_count = session_json['total_media_count']

        # Check if has next page
        has_next_page = session_json['has_next_page']
        end_cursor = session_json['end_cursor']

        # Used to query graphql
        while has_next_page and (len(edges_list) + len(top_posts)) <= count and has_next_page is not None:
            # Query variables is formatted specifically to calculate header
            # X-Instagram-GIS: <md5-hash of query_variables_str>
            query_variables = {
                'id': '{}'.format(session_json['profile_id']),
                'first': 64,
                'after': end_cursor
            }
            query_variables_str = json.dumps(
                query_variables, separators=(',', ':'))

            # Construct headers and request
            req_headers = {
                'X-Instagram-GIS': self.compute_gis(session_json['rhx_gis'], query_variables_str),
                'Cookie': 'csrftoken={}'.format(session_json['csrf_token']),
                **self._query_base_headers
            }
            req_url = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}'.format(
                query_hash,
                quote_plus(query_variables_str)
            )
            req = requests.get(req_url, headers=req_headers)

            # Extract edge json
            cur_media_json = req.json(
            )['data'][self._graphql_vals['type']][self._graphql_vals['media']]

            # Get page edges (our data)
            cur_edges = cur_media_json['edges']

            # Get next page info
            has_next_page = cur_media_json['page_info'].get(
                'has_next_page', False)
            end_cursor = cur_media_json['page_info'].get('page_cursor', None)

            edges_list.extend(cur_edges)

        return {
            'total_media_count': total_media_count,
            'top_posts': top_posts,
            'recent_posts': edges_list
        }

    def search_location(self,
                        location_name: str,
                        geolocation: GeoLocation) -> TypedDict('search_location',
                                                               {
                                                                   'location': RawInstagramLocation
                                                               }
                                                               ):
        """
        Uses instagram's websearch API to search for a location and returns graph QL dump
        for specific location

        Params:
            location_name: Name of location (restaurant / business)
            count: number of posts to scrap
            geolocation: Filters out places that aren't close by to the geolocation
                         (used to differenciate between multiple businesses that have similar names)
        """
        # Payload to query instagram websearch api
        web_search_payload = location_name.replace(' ', '+')

        r = requests.get(
            self._location_search_url.format(web_search_payload),
            headers=self._query_base_headers
        )
        ret_json = r.json()

        if len(ret_json['places']) > 0:
            for i in range(len(ret_json['places'])):

                # Make sure it has a valid instagram pk
                if ret_json['places'][i]['place']['location']['pk'] == '0':
                    continue

                # Check distance, make sure its the same place (3300m wiggle room)
                cur_insta_location = ret_json['places'][i]['place']['location']
                if haversine_distance(geolocation[0], geolocation[1], cur_insta_location['lat'], cur_insta_location['lng']) > 3.3:
                    print(haversine_distance(geolocation[0], geolocation[1], cur_insta_location['lat'], cur_insta_location['lng']))
                    continue

                return {
                    'location': ret_json['places'][i]['place']['location']
                }

        return {
            'location': None
        }
