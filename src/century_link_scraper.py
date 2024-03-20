# import statements
from random import sample
import json
import os
import grequests
from requests.adapters import HTTPAdapter, Retry
import requests
from dotenv import load_dotenv

# when a request fails (including all retries), simply return -1 to show that it has failed
# out here because its breaking??
def exception_handler(request, exception):
    # print("Request failed: ", request, exception)
    return -1

# provides all functions needed to run the scraping tool given a list of addresses
class CenturyLinkScraper:
    # setup addresses, and proxies
    def __init__(self, addresses=None):
        self.addresses = addresses
        load_dotenv()
        # FOR ROTATING PROXY
        self.proxy_endpoint = os.environ.get("PROXY_ENDPOINT")  # Set proxy before use
        if self.proxy_endpoint is None:
            raise ValueError("No proxy endpoint found in .env. \
                             Please set a PROXY_ENDPOINT variable in a .env file with \
                             the proxy endpoint you will be using.")
        # retry codes, every code but 200 and 306 (unused, for skipping)
        self.status_list = list(x for x in requests.status_codes._codes if x not in [200])
    
    # sort an enumerated list by its first value
    # used to ensure all requests are returned in order
    def sort_enum(self, e):
        return e[0]
    
    # verifies that a list of responses contains only 200 codes
    # if the list contains only 200 codes, return true, if not false
    def verify_responses(self, responses: list):
        # list of bools for each status code
        response_bools = [responses[n].status_code == 200 for n in range(len(responses))] 
        non_200_count = sum(response_bools) - len(response_bools)
        if non_200_count != 0:
            codes = [responses[n].status_code for n in range(len(responses))]
            print("Some responses were not successful", non_200_count, codes)
            return False
        else:
            return True
    
    # request auth codes for a list of addresses
    # returns an indexed list of addressed and their auths, and a list of the raw responses
    def get_auths(self, addresses_used: list):
        with requests.Session() as s:
            # create retry function
            retries = Retry(total=4, backoff_factor=.9, 
                            status_forcelist=self.status_list, raise_on_status=True)
            # mount it to our session so each request will have the same retry function
            s.mount('https://', HTTPAdapter(max_retries=retries))
            
            # set up tasks
            target_url = 'https://shop.centurylink.com/uas/oauth'
            cookies = {}
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
            }
            tasks = [
                grequests.get(
                    url=target_url, 
                    proxies={'https': self.proxy_endpoint}, 
                    session=s, 
                    cookies=cookies, 
                    headers=headers
                ) 
                for n in range(len(addresses_used))
            ]
            
            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                                                        tasks, 
                                                        exception_handler=exception_handler,
                                                        size=40
                                                            ):
                # index for sorting, address, and then response which may be a full response or -1
                raw_responses.append((index, addresses_used[index], response))
            # pull out requests that failed and were caught
            failed_responses = [
                res for res in raw_responses if (res[2] == -1)
            ]
            # pull out requests that returned a code
            coded_responses = [
                        res for res in raw_responses if (res[2] != -1)
                    ]
            # if those codes aren't 200, set to -1 and if they are 200 get the token
            coded_responses = [
                [res[0], res[1], json.loads(res[2].content)['access_token']] 
                if res[2].status_code == 200 else [res[0], res[1], -1] for res in coded_responses
            ]
            # merge 2 lists
            responses = coded_responses + failed_responses
            # sort the list
            responses.sort(key=self.sort_enum)

            # raw_responses.sort(key=self.sort_enum)

            # # pull access token from valid responses
            # # exception handler ensures that only 200 responses will be non -1 in raw list
            # response_content = [
            #     (res[0], res[1], json.loads(res[2].content)['access_token']) 
            #     if (res[2] != -1 | res[2].status_code != 200) else (res[0], res[1], -1) for res in raw_responses
            # ]
            return responses, raw_responses

    # verifies that the address exists within the centurylink system and gets necessary data for 
    #   collecting offers
    # given a list of addresses and their corresponding auths
    # returns an indexed list of addresses with their auths and address data, 
    #   and a list of the raw responses
    def check_adr(self, addresses_used: list, auths: list):
        # auths: list same length as addresses_used, either 'access_token' or -1
        with requests.Session() as s:
            # create Retry
            retries = Retry(total=4, backoff_factor=2, 
                            status_forcelist=self.status_list, raise_on_status=True)
            # mount it to our session so each request will have the same retry function
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks, matching address to auths
            # if the auth failed, don't run that task
            target_url = 'https://api.lumen.com/Application/v4/DCEP-Consumer/identifyAddress'
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': self.proxy_endpoint},
                    session=s,
                    headers={'Authorization': 'Bearer ' + auth},
                    json={'fullAddress': adr}
                ) 
                # make a request to a safe location that will not force retry
                # else grequests.get('https://httpbin.org/status/306')
                for adr, auth in list(zip(addresses_used, auths)) if auth != -1
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                                                        tasks, 
                                                        exception_handler=exception_handler,
                                                        size=25
                                                            ):
                raw_responses.append((index, response))
            # sort responses
            raw_responses.sort(key=self.sort_enum)
            # get just responses
            responses = [res[1] for res in raw_responses]
            adrs_response = []
            # create the cleaned response list with [index, address, auth, content (or -1)]
            for n, auth in enumerate(auths):
                # if that auth was not -1 (and therefore a request was made)
                if auth != -1:
                    # get the response from that request
                    t = responses.pop(0)
                    # if that response failed
                    if t == -1:
                        adrs_response.append([n, addresses_used[n], auth, -1])
                    # if failed in a weird way
                    if t.status_code != 200:
                        adrs_response.append([n, addresses_used[n], auth, -1])
                    else: 
                        # otherwise the response was a success and we should load the data
                        adrs_response.append([n, addresses_used[n], auth, json.loads(t.content)])
                else:
                    # auth was -1 so no request was made and -1 should be listed
                    adrs_response.append([n, addresses_used[n], auth, -1])
            return adrs_response, raw_responses
            
            # pull address details from valid responses
            # exception handler ensures that only 200 responses will be non -1 in raw list

    # updates a given list of address data for MDU units
    # given a list of addresses and their corresponding auths/responses/address data
    # returns an updated list of address data   
    def mdu_update(self, addresses_used: list, auths: list, mdu_list: list, adrs_response: list):

        with requests.Session() as s:
            # create Retry
            retries = Retry(total=5, backoff_factor=2, 
                            status_forcelist=self.status_list, raise_on_status=True)
            # mount it to our session so each request will have the same retry function
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks, excluding ones not on list
            target_url = 'https://api.lumen.com/Application/v4/DCEP-Consumer/identifyAddress'
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': self.proxy_endpoint},
                    session=s,
                    headers={'Authorization': 'Bearer ' + auth},
                    json={
                        'addressId': old_res['addrValInfo']['addressId'],
                        'fullAddress': adr, 
                        'billingSource': old_res['addrValInfo']['billingSource'],
                        'unitNumber': old_res['addrValInfo']['mduInfo']['mduList'][0]['unitDescription'],
                        'geoSecUnitId': old_res['addrValInfo']['mduInfo']['mduList'][0]['geoSecUnitId']
                    }
                ) 
                for adr, auth, mdu, old_res in list(zip(addresses_used, auths, mdu_list, adrs_response)) if mdu
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                                                        tasks, 
                                                        exception_handler=exception_handler,
                                                        size=25
                                                            ):
                # index for sorting, address, and then response which may be a full response or -1
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)

            # replace old responses with updated ones
            # since we are modifying a list, we only need to do something if the case is met
            responses = [res[1] for res in raw_responses]
            # if the unit is mdu, then a request was made
            for n, mdu in enumerate(mdu_list):
                # if a request wasn't made, just go to next unit
                if mdu:
                    # unit is mdu, so a request was made. pop response
                    t = responses.pop(0)
                    # response failed and was caught, set to -1 (this will delete old addr data)
                    if t == -1:
                        adrs_response[n] = -1
                    # same as above, but failed in an unexpected way
                    if t.status_code != 200:
                        adrs_response[n] = -1
                    # response returned with code 200
                    else: 
                        adrs_response[n] = json.loads(t.content)
            return adrs_response, raw_responses

    # get internet plan offers from centurylink
    # given a list of addresses and their corresponding auths/address data/offer list
    # returns a list of offers
    def get_offers(self, addresses_used: list, auths: list, adrs_response: list, has_offers: list):

        with requests.Session() as s:
            # create Retry
            retries = Retry(total=5, backoff_factor=2, 
                            status_forcelist=self.status_list, raise_on_status=True)
            # mount it to our session so each request will have the same retry function
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks
            target_url = 'https://api.centurylink.com/Application/v4/DCEP-Consumer/offer'
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': self.proxy_endpoint},
                    session=s,
                    headers={'Authorization': 'Bearer ' + auth},
                    json={
                        'billingSource': address_info['addrValInfo']['billingSource'],
                        'addressId': address_info['addrValInfo']['addressId'],
                        'fullAddress': adr, 
                        'wireCenter': address_info['addrValInfo']['wireCenter'],
                        'unitNumber': address_info['unitNumber'],
                        'geoSecUnitId': address_info['geoSecUnitId']
                    }
                ) 
                for adr, auth, green, address_info in list(zip(addresses_used, auths, has_offers, adrs_response)) if green
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                                                        tasks, 
                                                        exception_handler=exception_handler,
                                                        size=25
                                                            ):
                # index for sorting, address, and then response which may be a full response or -1
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)
            # ordered response list by location in has_offers

            # parse offers
            # because we are constructing a new list we need to put something in for each address
            responses = [res[1] for res in raw_responses]
            offers_list = []
            # go through the list of bools for each address
            for green in has_offers:
                # if the address should have offers
                if green:
                    # grab the first response
                    t = responses.pop(0)
                    # if the request failed, put our fail placeholder
                    if t == -1:
                        offers_list.append(-1)
                    # if request failed, but in an unexpected way
                    if t.status_code != 200:
                        offers_list.append(-1)
                    # if the request didn't fail, put that data in!
                    else: 
                        offers_list.append(json.loads(t.content))
                # if the address should not have offers
                else: 
                    # put our fail placeholder
                    offers_list.append(-1)
            return offers_list, raw_responses
    
    # only method that should be called!
    # runs the scraper
    def run_scraper(self, i=0):
        # select the addresses we will be using (initially)
        adr_sample = sample(self.addresses, int(len(self.addresses) / 10))
        n_addrs = len(adr_sample)
        # if we have no addresses
        if len(self.addresses) == 0:
            print("---------------- Something went very wrong ----------------------")
            return [-1, -1, -1]
        # if our addresses are less than 10 and we don't have any sample
        if (n_addrs <= 1) & (len(self.addresses) <= 10):
            adr_sample = self.addresses
            n_addrs = len(adr_sample)
        # get the authentication for each address
        auths, raw_1 = self.get_auths(addresses_used=adr_sample)
        just_auths = [el[2] for el in auths]
        # auths: [index, addresses_used[index], 'access_token'/-1]
        # just_auths: ['access_token'/-1]

        # see how many auths failed
        n_failed_auths = sum([True if el == -1 else False for el in just_auths])
        print(f'FOR TESTING: FAILED_AUTHS = {n_failed_auths}')
        if n_failed_auths > 0:
            print(f'{n_failed_auths} out of {n_addrs} auths failed.')
        
        # verify addresses for the first time
        verif_adr, raw_2 = self.check_adr(addresses_used=adr_sample, auths=just_auths)
        just_adr_1 = [el[3] for el in verif_adr]
        # verif_adr: [index, address, 'auth'/-1, {adr_info}/-1]
        # just_adr_1: {adr_info}/-1
        
        # see how many verifications failed
        n_failed_verif_adr = sum([True if el == -1 else False for el in just_adr_1])
        print(f'FOR TESTING: failed_verif_adr = {n_failed_verif_adr}')

        # if the number of verifications that failed was higher than the number of auths that failed
        if n_failed_verif_adr - n_failed_auths > 0:
            # number of new failed requests // number of possible successes
            print(f'{n_failed_verif_adr - n_failed_auths} out of {n_addrs - n_failed_auths} verifications failed.')

        # see what units are mdu
        is_mdu = ['mdu matches' in m['message'].lower() if m != -1 else False for m in just_adr_1]
        n_is_mdu = sum(is_mdu)

        # update all mdu units with actual address data
        just_adr_2, raw_3 = self.mdu_update(addresses_used=adr_sample, auths=just_auths, mdu_list=is_mdu, adrs_response=just_adr_1)
        
        # see how many mdu verifications failed
        n_failed_verif_mdu = sum([True if el == -1 else False for el in just_adr_2])
        # if mdu request failed, then the sum of just_adr_2 will be higher than just_adr_1
        if n_failed_verif_mdu - n_failed_verif_adr > 0:
            # number of additional mdu failures // number of possible successes 
            print(f'{n_failed_verif_mdu - n_failed_verif_adr} out of {n_is_mdu} mdus failed.')

        # check for valid tags before getting offers
        # for t in just_adr_2:
        #     print(t)

        # list which addrs have offers to collect
        has_offers = [(('green' in m['message'].lower()) | ('success' in m['message'].lower())) if m != -1 else False for m in just_adr_2]
        
        # calculate stats
        n_has_offers = sum(has_offers)
        n_valid_responses = n_addrs - n_failed_verif_mdu
        n_non_green = n_valid_responses - n_has_offers
        print(f'Checking {n_has_offers} addresses out of {n_addrs} for offers. {n_non_green} units had non-green responses.')

        # collect offers for each address that has offers
        just_offers, raw_4 = self.get_offers(addresses_used=adr_sample, auths=just_auths, adrs_response=just_adr_2, has_offers=has_offers)

        # see how many offer requests failed, some number will have non green responses
        n_failed_offers = sum([True if el == -1 else False for el in just_offers])
        n_successful_offers = n_addrs - n_failed_offers
        # check if additionall offers failed
        if n_successful_offers < n_has_offers:
            # how many offer requests failed
            print(f'{n_has_offers - n_successful_offers} out of {n_has_offers} offer requests failed.')
        
        # uncleaned format with all address and offer data
        # [address used for request, data returned from that address, offers for that address]
        print(f"{n_successful_offers} offers collected for {n_addrs} addresses ({int(n_successful_offers / n_addrs * 100)}%)")
        print(len(adr_sample), len(just_adr_2), len(just_offers))
        a = list(zip(adr_sample, just_adr_2, just_offers))
        return a
