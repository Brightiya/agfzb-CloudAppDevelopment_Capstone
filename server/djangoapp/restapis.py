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

def get_request(url, **params):
    try:
        if not 'api_key' in params:
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'})
        else:
            api_key = params['api_key']
            del params['api_key']
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
                                    auth=HTTPBasicAuth('apikey', api_key))
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
        dealers = json_result["body"]

        dealer_doc = dealers[0]
        dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"],
                               id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                               full_name=dealer_doc["full_name"],

                               st=dealer_doc["st"], zip=dealer_doc["zip"])
        return dealer_obj


def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("id")
    if id:
        json_result = get_request(url, id=id)
    else:
        json_result = get_request(url)
    # print(json_result)
    if json_result:
        reviews = json_result["body"]["data"]["docs"]
        for dealer_review in reviews:
            review_obj = DealerReview(dealership=dealer_review["dealership"],
                                      name=dealer_review["name"],
                                      purchase=dealer_review["purchase"],
                                      review=dealer_review["review"])
            if "id" in dealer_review:
                review_obj.id = dealer_review["id"]
            if "purchase_date" in dealer_review:
                review_obj.purchase_date = dealer_review["purchase_date"]
            if "car_make" in dealer_review:
                review_obj.car_make = dealer_review["car_make"]
            if "car_model" in dealer_review:
                review_obj.car_model = dealer_review["car_model"]
            if "car_year" in dealer_review:
                review_obj.car_year = dealer_review["car_year"]

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
    url = "https://dd5dab06-83d7-4e3f-bdd3-fba01337ae7c-bluemix.cloudantnosqldb.appdomain.cloud"
    api_key = "E2SRo-xKOn_MHYPXHVWiP6ckeM-IZsrGdK-CGiRcX8II"
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2021-08-01', authenticator=authenticator)
    natural_language_understanding.set_service_url(url)
    response = natural_language_understanding.analyze(text=text + "hello hello hello", features=Features(
        sentiment=SentimentOptions(targets=[text + "hello hello hello"]))).get_result()
    label = json.dumps(response, indent=2)
    label = response['sentiment']['document']['label']

    return label
