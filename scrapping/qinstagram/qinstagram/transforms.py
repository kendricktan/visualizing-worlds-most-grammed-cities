"""
Transforms the data from scrapped instagram api to a standard format
"""

from typing import List
from qinstagram.types import (
    RawInstagramPostsNode,
    RawInstagramPosts,
    InstagramPost,
    InstagramPosts
)


def standardize_instagram_post_data(post_data: RawInstagramPostsNode) -> InstagramPost:
    """
    Standardized InstagramPost data (singular)
    """
    node_data = post_data['node']

    display_url = node_data['display_url']
    try:
        caption = node_data['edge_media_to_caption']['edges'][0]['node']['text']
    except:
        caption = ''
    instagram_id = node_data['id']
    shortcode = node_data['shortcode']
    thumbnail_url = node_data['thumbnail_src']
    taken_at_timestamp = node_data['taken_at_timestamp']

    return {
        'display_url': display_url,
        'thumbnail_url': thumbnail_url,
        # Datastore stores max 1500 bytes (~187 characters)
        'caption': caption[:180],
        'instagram_id': instagram_id,
        'shortcode': shortcode,
        'taken_at_timestamp': taken_at_timestamp
    }


def standardize_instagram_posts(insta_data: RawInstagramPosts) -> InstagramPosts:
    """
    Standardized InstagramPosts data (plural)
    """
    recent_posts: List[InstagramPost] = list(
        map(standardize_instagram_post_data, insta_data['recent_posts'])
    )

    top_posts: List[InstagramPost] = list(
        map(standardize_instagram_post_data, insta_data['top_posts'])
    )

    return {
        'total_media_count': insta_data['total_media_count'],
        'recent_posts': recent_posts,
        'top_posts': top_posts
    }
