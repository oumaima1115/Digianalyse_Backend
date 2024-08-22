import requests

def api_besthashtag():
    country_codes = ['US', 'DE', 'GB', 'CA']
    days = [7, 30, 120]

    base_url = "https://trending-hashtags.p.rapidapi.com/api/trends/"
    headers = {
      "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
      "x-rapidapi-host": "trending-hashtags.p.rapidapi.com"
    }

    data_df = []

    for country in country_codes:
        for day in days:
            url = f"{base_url}{country}/{day}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                trends = response.json()
                for trend in trends:
                    trend_data = {
                        'video_views': int(trend.get('video_views', 0)),  # Ensure this is a number
                        'country_name': str(trend.get('country_name', '')),  # Ensure this is a string
                        'industry': trend.get('industry') if trend.get('industry') not in [None, "None"] else None,  # None or String
                        'hashtag': str(trend.get('hashtag', '')),  # Ensure this is a string
                        'publish_count': int(trend.get('publish_count', 0)),  # Ensure this is a number
                        'trend_type': str(trend.get('trend_type', '')),  # Ensure this is a string
                        'is_new': True if trend.get('is_new') == True else None  # True or None
                    }
                    data_df.append(trend_data)
            else:
                print(f"Failed to fetch data for {country} with period {day} days. Status code: {response.status_code}")

    return data_df