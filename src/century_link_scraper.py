# import statements
import grequests
# import logging
import csv
from requests.adapters import HTTPAdapter, Retry
from random import sample, randint
import json
import requests
import os

# provides all functions needed to run the scraping tool given a list of addresses
class CenturyLinkScraper:
    # setup addresses, and proxies
    def __init__(self, addresses: list):
        self.addresses = addresses
        # FOR STICKY SESSIONS
        # self.endpoints_path = 'digital-redlining-data/res/Endpoints.csv'
        # FOR ROTATING PROXY
        self.proxy_endpoint = 'https://customer-rnickben-cc-us-st-us_washington:6TBcLj4Ugh9M@pr.oxylabs.io:7777'
        # self.proxy_endpoint = 'https://customer-rnickben:6TBcLj4Ugh9M@us-pr.oxylabs.io:10000'
        # retry codes, every code but 200 and 306 (unused, for skipping)
        self.status_list = list(x for x in requests.status_codes._codes if x not in [200])

    # NOT USING STICKY SESSIONS ATM
    # return a random proxy from the endpoints file
    # credit for random file line reading: https://stackoverflow.com/a/56973905
    def get_next_proxy(self):
        file_size = os.path.getsize(self.endpoints_path)
        with open(self.endpoints_path, 'rb') as f:
            while True:
                pos = randint(0, file_size)
                if not pos:  # the first line is chosen
                    return f.readline().decode()  # return str
                f.seek(pos)  # seek to random position
                f.readline()  # skip possibly incomplete line
                line = f.readline()  # read next (full) line
                if line:
                    return line.decode()  
                # else: line is empty -> EOF -> try another position in next iteration

    # when a request fails (including all retries), simply return -1 to show that it has failed
    def exception_handler(self, request, exception):
        # print("Request failed: ", request, exception)
        return -1
    
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
            retries = Retry(total=8, backoff_factor=.8, 
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
                                                        exception_handler=self.exception_handler
                                                            ):
                # index for sorting, address, and then response which may be a full response or -1
                raw_responses.append((index, addresses_used[index], response))
            raw_responses.sort(key=self.sort_enum)

            # pull access token from valid responses
            # exception handler ensures that only 200 responses will be non -1 in raw list
            response_content = [
                (res[0], res[1], json.loads(res[2].content)['access_token']) 
                if res[2] != -1 else res for res in raw_responses
            ]
            return response_content, raw_responses

    # verifies that the address exists within the centurylink system and gets necessary data for 
    #   collecting offers
    # given a list of addresses and their corresponding auths
    # returns an indexed list of addresses with their auths and address data, 
    #   and a list of the raw responses
    def check_adr(self, addresses_used: list, auths: list):
        with requests.Session() as s:
            # create Retry
            retries = Retry(total=5, backoff_factor=1.2, 
                            status_forcelist=self.status_list, raise_on_status=True)
            # mount it to our session so each request will have the same retry function
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks, matching address to auths
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
                                                        exception_handler=self.exception_handler
                                                            ):
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)

            responses = [res[1] for res in raw_responses]
            adrs_response = []
            # for each auth
            for n, auth in enumerate(auths):
                # if that auth was not -1 (and therefore a request was made)
                if auth != -1:
                    # get the response from that request
                    t = responses.pop(0)
                    # if that response failed
                    if t == -1:
                        # then list that the response failed
                        adrs_response.append((n, addresses_used[n], auth, -1))
                    else: 
                        # otherwise the response was a success and we should load the data
                        adrs_response.append((n, addresses_used[n], auth, json.loads(t.content)))
                else:
                    # auth was -1 so no request was made and -1 should be listed
                    adrs_response.append((n, addresses_used[n], auth, -1))
            print(adrs_response)
            return adrs_response, raw_responses
            
            # pull address details from valid responses
            # exception handler ensures that only 200 responses will be non -1 in raw list

    # updates a given list of address data for MDU units
    # given a list of addresses and their corresponding auths/responses/address data
    # returns an updated list of address data   
    def mdu_update(self, addresses_used: list, auths: list, mdu_list: list, adrs_response: list):

        with requests.Session() as s:
            # create Retry
            retries = Retry(total=5, backoff_factor=1.2, 
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
                                                        exception_handler=self.exception_handler
                                                            ):
                # index for sorting, address, and then response which may be a full response or -1
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)

            # replace old responses with updated ones
            ## can do this for each instead of making async requests but they're fast ##
            # since we are modifying a list, we only need to do something if the case is met
            responses = [res[1] for res in raw_responses]
            for n, mdu in enumerate(mdu_list):
                if mdu:
                    t = responses.pop(0)
                    if t == -1:
                        adrs_response[n] = -1
                    else: 
                        adrs_response[n] = json.loads(t.content)
            return adrs_response, raw_responses

    # get internet plan offers from centurylink
    # given a list of addresses and their corresponding auths/address data/offer list
    # returns a list of offers
    def get_offers(self, addresses_used: list, auths: list, adrs_response: list, has_offers: list):

        with requests.Session() as s:
            # create Retry
            retries = Retry(total=5, backoff_factor=1.2, 
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
                                                        exception_handler=self.exception_handler
                                                            ):
                # index for sorting, address, and then response which may be a full response or -1
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)

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
    def run_scraper(self, i: int):
        # select the addresses we will be using (initially)
        adr_sample = sample(self.addresses, int(len(self.addresses) / 10))
        # adr_sample = self.addresses
        
        # get the authentication for each address
        auths, raw_1 = self.get_auths(addresses_used=adr_sample)
        just_auths = [el[2] for el in auths]
        # see how many auths failed
        failed_auths = sum([True if el == -1 else False for el in just_auths])
        if failed_auths > 0:
            # if len(adr_sample) - failed_auths == 0:
            #     return -1
            print(f'{failed_auths} out of {len(adr_sample)} auths failed.')
        
        # verify addresses for the first time
        verif_adr, raw_2 = self.check_adr(addresses_used=adr_sample, auths=just_auths)
        just_adr_1 = [el[3] for el in verif_adr]
        # see how many verifications failed
        failed_verif_adr = sum([True if el == -1 else False for el in just_adr_1])
        print(f"{failed_verif_adr}\n")
        print(f"{verif_adr}\n")
        print(f"{just_adr_1}\n")
        if failed_verif_adr - failed_auths > 0:
            # if len(adr_sample) - failed_verif_adr == 0:
            #     return -1
            print(f'{failed_verif_adr - failed_auths} out of {len(adr_sample) - failed_auths} verifications failed.')

        # check for MDUs
        is_mdu = ['mdu matches' in m['message'].lower() if m != -1 else False for m in just_adr_1]

        # update all mdu units with actual address data
        just_adr_2, raw_3 = self.mdu_update(addresses_used=adr_sample, auths=just_auths, mdu_list=is_mdu, adrs_response=just_adr_1)
        # see how many mdu verifications failed
        failed_verif_mdu = sum([True if el == -1 else False for el in just_adr_2])
        if failed_verif_mdu - failed_verif_adr > 0:
            # if len(adr_sample) - failed_verif_mdu == 0:
            #     return -1
            print(f'{failed_verif_mdu - failed_verif_adr} out of {len(adr_sample) - failed_verif_adr} verifications failed.')

        # check for valid tags before getting offers
        has_offers = [(('green' in m['message'].lower()) | ('success' in m['message'].lower())) if m != -1 else False for m in just_adr_2]
        print(f'Checking {sum(has_offers)} addresses out of {len(adr_sample)} for offers ({len(adr_sample) - (sum(has_offers) + failed_verif_mdu) } units had non-green responses).')
        
        # collect offers for each address that has offers
        just_offers, raw_4 = self.get_offers(addresses_used=adr_sample, auths=just_auths, adrs_response=just_adr_2, has_offers=has_offers)
        # see how many offer requests failed
        failed_offers = sum([True if el == -1 else False for el in just_offers])
        if failed_offers - failed_verif_mdu > 0:
            # if len(adr_sample) - failed_offers == 0:
            #     return -1
            print(f'{failed_offers - failed_verif_mdu} out of {len(adr_sample) - failed_verif_mdu} offer requests failed.')
        
        # uncleaned format with all address and offer data
        # [address used for request, data returned from that address, offers for that address]
        a = list(zip(adr_sample, just_adr_2, just_offers))
        return a
