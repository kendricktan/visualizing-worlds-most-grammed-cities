from mypy_extensions import TypedDict
from typing import NewType, Optional, Tuple, Union, List

Latitude = NewType('Latitude', float)
Longitude = NewType('Longitude', float)
GeoLocation = Tuple[Latitude, Longitude]

QueryType = NewType('QueryType', str)
INSTA_USER = QueryType('User')
INSTA_LOCATION = QueryType('Location')

### Raw Types (straight from Instagram) ###

RawInstagramEdgesNodeText = TypedDict(
    'RawInstagramEdgesNodeText',
    {
        'text': str
    }
)

RawInstagramEdgesNode = TypedDict(
    'RawInstagramEdgesNode',
    {
        'node': RawInstagramEdgesNodeText
    }
)

RawInstagramEdges = TypedDict(
    'RawInstagramEdges',
    {
        'edges': List[RawInstagramEdgesNode]
    }
)

RawInstagramEdgeCount = TypedDict(
    'RawInstagramEdgeCount',
    {
        'count': int
    }
)

RawInstagramPostOwner = TypedDict(
    'RawInstagramPostOwner',
    {
        'id': str
    }
)

RawInstagramNode = TypedDict(
    'RawInstagramNode',
    {
        'id': str,
        'edge_media_to_caption': RawInstagramEdges,
        'shortcode': str,
        'edge_media_to_comment': RawInstagramEdgeCount,
        'dimensions': dict,  # Don't really care
        'display_url': str,
        'edge_liked_by': RawInstagramEdgeCount,
        'owner': RawInstagramPostOwner,
        'thumbnail_src': str,
        'thumbnail_resources': List[dict],
        'is_video': bool
    }
)

RawInstagramPostsNode = TypedDict(
    'RawInstagramPostsNode',
    {
        'node': RawInstagramNode
    }
)

RawInstagramPosts = TypedDict(
    'RawInstagramPosts',
    {
        'total_media_count': int,
        'top_posts': List[RawInstagramPostsNode],
        'recent_posts': List[RawInstagramPostsNode]
    }
)

RawInstagramLocationQuery = TypedDict(
    'RawInstagramLocationQuery',
    {
        'posts': RawInstagramPosts,
        'success': bool
    }
)

RawInstagramLocation = TypedDict(
    'RawInstagramLocation',
    {
        'pk': str,
        'name': str,
        'address': str,
        'city': str,
        'short_name': str,
        'lng': float,
        'lat': float,
        'external_source': str,
        'facebook_places_id': str
    }
)

RawInstagramLocationSearch = TypedDict(
    'RawInstagramLocationSearch',
    {
        'location': RawInstagramLocation,
        'posts': RawInstagramPosts,
        'success': bool
    }
)


## Standardized Types (after xforming) ###


InstagramPost = TypedDict(
    'InstagramPost',
    {
        'display_url': str,
        'thumbnail_url': str,
        'caption': str,
        'instagram_id': str,
        'shortcode': str,
        'taken_at_timestamp': int
    }
)

InstagramPosts = TypedDict(
    'InstagramPosts',
    {
        'total_media_count': int,
        'recent_posts': List[InstagramPost],
        'top_posts': List[InstagramPost]
    }
)

InstagramLocationSearch = TypedDict(
    'InstagramLocationSearch',
    {
        'location': RawInstagramLocation,
        'posts': InstagramPosts,
        'success': bool
    }
)