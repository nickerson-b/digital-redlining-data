# import statements
import grequests
import requests
from requests.adapters import HTTPAdapter 
from requests.packages.urllib3.util.retry import Retry
import json

# if exceptions become an issue, expand more on this
def exception_handler(request, exception):
    print("Request failed: ", request)
    
# verify that all requests have returned with a successful status code
def verify_responses(responses: list):
    f = [responses[n].status_code == 200 for n in range(len(responses))]
    if (sum(f) - len(f)) != 0:
        raise Exception("Some gid requests failed.")

# sort the outcomes of async requests for gid codes
def sort_gids_async(e):
    return e[0]

# given a list of geoids, return a list of gids in the same order as the geoids
def get_gid_from_geoid(geoids: list):
    # create auto closing session
    with requests.Session() as s:
        # create retry function
        retries = Retry(total=10, backoff_factor=1, status_forcelist=[500])
        # mount adapter
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        # create async tasks
        tasks = [grequests.get(url='https://usps.biglocalnews.org/api/search', session=s, params={'q':geoid,'limit':'10'}, headers={'accept': 'application/json'}) for geoid in geoids]
        # execute tasks with index so they can be sorted and used in order later with their geoid codes
        raw_responses = []
        for index, response in grequests.imap_enumerated(tasks, exception_handler=exception_handler):
            raw_responses.append((index, response))
        # sort
        raw_responses.sort(key=sort_gids_async)
        # extract the response from the raw responses
        responses = [raw_responses[n][1] for n in range(len(raw_responses))]
        # checks responses are all code 200
        try:
            verify_responses(responses=responses)
        except Exception as e:
            print(e)
            return -1
        # all responses are valid, safe to extract the list of gid codes
        else:
            return [str(json.loads(response.content)['results'][0]['gid']) for response in responses]

# given a list of geoids and matching gids
# in json format, return 100% of addresses in each block group
def get_bg_addresses(geoids, gids):
    # zip ids so they can be used in list comprehension
    ids = list(zip(geoids, gids))

    # self closing session for automatic retries
    with requests.Session() as s:
        # def retry function params
        retries = Retry(total=10, backoff_factor=1, status_forcelist=[500])

        # mount adapter
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))

        # make list of tasks
        tasks = [grequests.post('https://usps.biglocalnews.org/api/sample', session=s, headers={'accept': 'application/json','Content-Type': 'application/json',}, json={'custom_bounds': {},'shape_bounds': {'kind': 'bg','gid': id[1],'name': id[0],},'unit': 'pct','n': 100,}) for id in ids]
        
        # collect and enumerate responses to track ids easily
        raw_responses = []
        for index, response in grequests.imap_enumerated(tasks, exception_handler=exception_handler):
            raw_responses.append((ids[index][0], response))
        
        # pull just the responses, as a list (like <Response [200]>, ...)
        # if the whole response failed, then will be none and this will error
        responses = [raw_responses[n][1] for n in range(len(raw_responses))]
        
        try:
            # check that all response codes are 200
            # IN FUTURE: If not 200, change proxies and try again
            verify_responses(responses=responses)
        except Exception as e:
            # should catch if something breaks in the verification process
            print(f"Responses Not Valid: {e}")
            return -1
        else:
            # return the bg code, the gid code, and the content of the response
            t = [(raw_responses[ind][0], json.loads(res.content)['addresses']) for ind, res in enumerate(responses)]
            return t
    