import requests
import json
# import related models here
from .models import CarDealer, DealerReview
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
from requests.auth import HTTPBasicAuth
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import time

# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))

import requests
import json
from .models import CarDealer
from requests.auth import HTTPBasicAuth


def get_request(url, **params):
    try:
        if not 'api_key' in params:
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'})
        else:
            api_key = params['api_key']
            del params['api_key']
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
                                    auth=HTTPBasicAuth('apikey', "mpOtbGnGrNyOoiUVUx1cu3-Y-e03cacKvdIXBbtG-_Sv"))
        status_code = response.status_code
        # print(f"{url} with status {status_code}")
        json_data = json.loads(response.text)
        # print("res: ", json_data, response, params,status_code)
        return json_data
    except requests.exceptions.RequestException as e:
        print("Network exception occurred: {}".format(str(e)))
        return None


def post_request(url, payload, **kwargs):
    print(kwargs)
    print("POST to {} ".format(url))
    print(payload)
    response = requests.post(url, params=kwargs, json=payload)
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data


# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list

def get_dealers_from_cf(url, **params):
    results = []
    json_result = get_request(url, **params)

    dealers = json_result
    for dealer in dealers:
        dealer_doc = dealer
        dealer_obj = CarDealer(
            address=dealer_doc.get("address"),
            city=dealer_doc.get("city"),
            full_name=dealer_doc.get("full_name"),
            id=dealer_doc.get("id"),
            lat=dealer_doc.get("lat"),
            long=dealer_doc.get("long"),
            short_name=dealer_doc.get("short_name"),
            st=dealer_doc.get("st"),
            state=dealer_doc.get("state"),
            zip=dealer_doc.get("zip"))

        results.append(dealer_obj)

    return results


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def get_dealer_by_id_from_cf(url, id):

    json_result = get_request(url, id=id)
    print('json_result from line 54', json_result)

    if json_result:

        dealers = json_result

        dealer_doc = dealers[0]
        dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"],
                               id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                               full_name=dealer_doc["full_name"],

                               st=dealer_doc["st"], zip=dealer_doc["zip"], short_name=dealer_doc["short_name"],
                               state=dealer_doc["state"])
        return dealer_obj


def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("id")
    if id:
        json_result = get_request(url, id=id)
    else:
        json_result = get_request(url)
    print(json_result, "96")
    if json_result:
        if isinstance(json_result, list):  # Check if json_result is a list
            reviews = json_result
        else:
            reviews = json_result["data"]["docs"]

        # Check if 'reviews' is a list of one dictionary
        if isinstance(reviews, list) and len(reviews) == 1 and isinstance(reviews[0], dict):
            reviews = reviews[0]

        for dealer_review in reviews:
            print("dealer_review--------------------", dealer_review)  # Print dealer_review
            if isinstance(dealer_review, str):  # Check if dealer_review is a string
                try:
                    dealer_review = json.loads(dealer_review)
                except json.JSONDecodeError:
                    continue  # Skip this iteration if the JSON decoding fails

            review_obj = DealerReview(
                dealership=dealer_review.get("dealership"),
                name=dealer_review.get("name"),
                purchase=dealer_review.get("purchase"),
                review=dealer_review.get("review"),
                purchase_date=dealer_review.get("purchase_date"),
                car_make=dealer_review.get("car_make"),
                car_model=dealer_review.get("car_model"),
                car_year=dealer_review.get("car_year"),
                id=dealer_review.get("id"), sentiment=dealer_review.get("sentiment"))

            sentiment = analyze_review_sentiments(review_obj.review)
            print(sentiment)
            review_obj.sentiment = sentiment
            results.append(review_obj)

    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative


def analyze_review_sentiments(text):
    url = ("https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/7db77c2a-3329-43a4-ba57"
           "-1a02b2c23a87")
    api_key = "mpOtbGnGrNyOoiUVUx1cu3-Y-e03cacKvdIXBbtG-_Sv"
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2021-08-01', authenticator=authenticator)
    natural_language_understanding.set_service_url(url)
    response = natural_language_understanding.analyze(text=text + "hello hello hello", features=Features(
        sentiment=SentimentOptions(targets=[text + "hello hello hello"]))).get_result()
    label = json.dumps(response, indent=2)
    label = response['sentiment']['document']['label']

    return label
