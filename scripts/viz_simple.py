import os
import math
import csv
import json
import folium

from folium.plugins import HeatMap

with open('raw_data.json', 'r') as f:
    raw_data = json.load(f)

simple_data = list(map(
    lambda x: {
        'lat': x['latitude'],
        'lng': x['longitude'],
        'value': round(math.log10(x['current_tag_count']), 2)
    }, raw_data
))

simple_data = list(
    sorted(simple_data, key=lambda x: x['value'], reverse=True)
)
max_weight = max(
    list(map(lambda x: x['value'], simple_data))
)

hmap = folium.Map(location=[48.8, 2.35], zoom_start=6)

for i in range(1, int(max_weight + 1)):
    filtered_data = list(
        filter(lambda x: x['value'] >= i and x['value'] <= i + 1, simple_data)
    )

    latitudes = list(map(lambda x: x['lat'], filtered_data))
    longitudes = list(map(lambda x: x['lng'], filtered_data))
    weights = list(map(lambda x: x['value'], filtered_data))

    hm_wide = HeatMap(
        list(zip(latitudes, longitudes, weights)),
        min_opacity=0.2,
        max_val=max_weight,
        radius=max(1, i * 0.7), blur=1,
        max_zoom=1,
    )

    hmap.add_child(hm_wide)

hmap.save('visualizations/simple.html')