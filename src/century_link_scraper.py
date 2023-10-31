# import statements
import grequests
# import logging
import csv
from requests.adapters import HTTPAdapter, Retry
from random import sample
import json
import requests

# provides all functions needed to run the scraping tool given a list of addresses
class CenturyLinkScraper:
    # setup addresses, and proxies
    def __init__(self, addresses: list):
        self.addresses = addresses
        # Read endpoints as list
        self.endpoints = None
        with open('Endpoints.csv', 'r') as f:
            self.endpoints = list(csv.reader(f, delimiter=','))
        if not self.endpoints:
            raise Exception('Endpoints not read properly')
        else: 
            print('loaded endpoints')

    def exception_handler(self, request, exception):
        print("Request failed: ", request, exception)
        return -1
    
    def sort_enum(self, e):
        return e[0]
    
    def verify_responses(self, responses: list):
        response_bools = [responses[n].status_code == 200 for n in range(len(responses))] # list of bools for each status code
        non_200_count = sum(response_bools) - len(response_bools)
        if non_200_count != 0:
            codes = [responses[n].status_code for n in range(len(responses))]
            # first arg is the error message, next is the number of failed codes and last is the list of the codes
            raise ValueError("Some responses were not successful", non_200_count, codes)
    
    def get_auths(self, addresses_used: list):
        with requests.Session() as s:
            # create Retry
            retries = Retry(total=10, backoff_factor=1.2, status_forcelist=[500, 401, 403])
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
                    proxies={'https': sample(self.endpoints, 1)[0][0]}, 
                    session=s, 
                    cookies=cookies, 
                    headers=headers
                ) 
                for n in range(len(addresses_used))
            ]
            
            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(tasks, exception_handler=self.exception_handler):
                raw_responses.append((index, addresses_used[index], response))
            raw_responses.sort(key=self.sort_enum)

            # VALIDATE RESPONSES
            responses = [res[2] for res in raw_responses]
            try:
                self.verify_responses(responses)
            except ValueError as e:
                print(f'AUTH FAILED BECAUSE OF A REQUEST FAILURE, EXCEPTION RAISED: {e}')
                return None, None
            except Exception as e:
                print(f'AUTH FAILED, EXCEPTION RAISED: {e}')
                return None, None
            else: 
                response_content = [json.loads(res[2].content)['access_token']for res in raw_responses]
                auths = [(el[0], el[1], response_content[i]) for i, el in enumerate(raw_responses)]
                return auths, raw_responses  

    def check_adr(self, addresses_used: list, auths: list):
        with requests.Session() as s:
            # create Retry
            retries = Retry(total=10, backoff_factor=1, status_forcelist=[500, 401, 403])
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks
            target_url = 'https://api.lumen.com/Application/v4/DCEP-Consumer/identifyAddress'
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': sample(self.endpoints, 1)[0][0]},
                    session=s,
                    headers={'Authorization': 'Bearer ' + auth},# needs to be set with corresponding addr
                    json={'fullAddress': adr}# needs to be set with matching auth
                ) 
                for adr, auth in list(zip(addresses_used, auths))
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(tasks, exception_handler=self.exception_handler):
                raw_responses.append((index, addresses_used[index], auths[index], response))
            raw_responses.sort(key=self.sort_enum)
            
            # VALIDATE RESPONSES
            responses = [res[3] for res in raw_responses]
            try:
                self.verify_responses(responses)
            except ValueError as e:
                print(f'Address verification 1 failed with the following exception: {e}')
                response_content = []
                for res in responses:
                    if res.status_code != 200:
                        response_content.append({
                                'message':'Failed to get proper response from server while attempting to verify an initial address.',
                                'statusCode':res.status_code,
                                'fullResponse':res
                            })
                    else:
                        response_content.append(json.loads(res.content))
                verif_1 = [(el[0], el[1], el[2], response_content[i]) for i, el in enumerate(raw_responses)]
                return verif_1, raw_responses
            except Exception as e:
                print(f'Address verification 1 failed with the following exception: {e}')
                return None
            else: 
                response_content = [json.loads(res[3].content) for res in raw_responses]
                verif_1 = [(el[0], el[1], el[2], response_content[i]) for i, el in enumerate(raw_responses)]
                return verif_1, raw_responses
            
    def mdu_update(self, addresses_used: list, auths: list, mdu_list: list, adrs_response: list):

        with requests.Session() as s:
            # create Retry
            retries = Retry(total=10, backoff_factor=1, status_forcelist=[500, 401, 403])
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks
            target_url = 'https://api.lumen.com/Application/v4/DCEP-Consumer/identifyAddress'
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': sample(self.endpoints, 1)[0][0]},
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
            for index, response in grequests.imap_enumerated(tasks, exception_handler=self.exception_handler):
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)
            
            # VALIDATE RESPONSES
            responses = [res[1] for res in raw_responses]
            try:
                self.verify_responses(responses)
            except ValueError as e:
                print(f'While verifying the mdu responses the following error arose: {e}')
                for n, mdu in enumerate(mdu_list):
                    if mdu:
                        r = responses.pop(0)
                        code = r.status_code
                        if code != 200:
                            adrs_response[n] = {
                                'message':'Failed to get proper response from server while attempting to verify an MDU',
                                'statusCode':code,
                                'fullResponse':r
                            }
                        else:
                            adrs_response[n] = json.loads(r.content)
                return adrs_response, raw_responses
            except Exception as e:
                print(f'While verifying the mdu responses the following error arose: {e}')
                return -1
            else: 
                for n, mdu in enumerate(mdu_list):
                    if mdu:
                        adrs_response[n] = json.loads(responses.pop(0).content)
                return adrs_response, raw_responses

    def get_offers(self, addresses_used: list, auths: list, adrs_response: list, has_offers: list):
        with requests.Session() as s:
            # create Retry
            retries = Retry(total=10, backoff_factor=1, status_forcelist=[500, 401, 403])
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set up tasks
            target_url = 'https://api.centurylink.com/Application/v4/DCEP-Consumer/offer'
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': sample(self.endpoints, 1)[0][0]},
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
            for index, response in grequests.imap_enumerated(tasks, exception_handler=self.exception_handler):
                raw_responses.append((index, response))
            raw_responses.sort(key=self.sort_enum)
            
            # VALIDATE RESPONSES
            responses = [res[1] for res in raw_responses]
            try:
                self.verify_responses(responses)
            except ValueError as e:
                print(f'While collecting offers the following error arose: {e}')
                offers_list = []
                for status in has_offers:
                    r = responses.pop(0)
                    if status & (r.status_code == 200):
                        offers_list.append(json.loads(r.content))
                    elif r.status_code != 200:
                        offers_list.append("Request for offers failed with status {r.status_code}")
                    else:
                        offers_list.append(None)
                return offers_list, raw_responses
            except Exception as e:
                print(f'While collecting offers the following error arose: {e}')
                return None, None
            else: 
                offers_list = []
                for status in has_offers:
                    if status:
                        offers_list.append(json.loads(responses.pop(0).content))
                    else:
                        offers_list.append(None)
                return offers_list, raw_responses
    
    def run_scraper(self, i: int):
        # select the addresses we will be using (initially)
        adr_sample = sample(self.addresses, int(len(self.addresses) / 10))
        # adr_sample = self.addresses
        
        # get the authentication for each address
        auths, raw_1 = self.get_auths(addresses_used=adr_sample)
        if auths is None:
            print(f'Scraping failed')
            return -1
        else:
            print(f'Auths collected for {i}')
        # return auths, raw_responses
        just_auths = [el[2] for el in auths]
        # return just_auths

        # verify addresses for the first time
        verif_adr, raw_2 = self.check_adr(addresses_used=adr_sample, auths=just_auths)
        if verif_adr is None: 
            print('auth failed')
            return -1
        else:
            print(f'First adrs collected for {i}')
        # return verif_adr, raw_2
        just_adr_1 = [el[3] for el in verif_adr]
        is_mdu = ['mdu matches' in m['message'].lower() for m in just_adr_1]
        # return is_mdu, just_adr_1

        # update all mdu units with actual address data
        just_adr_2, raw_3 = self.mdu_update(addresses_used=adr_sample, auths=just_auths, mdu_list=is_mdu, adrs_response=just_adr_1)
        
        if just_adr_2 is None: 
            print('mdu update failed')
            return -1
        else:
            print(f'MDU\'s updated for {i}')
        # return verif_adr_2, raw_3

        # check for valid tags before getting offers
        has_offers = [(('green' in m['message'].lower()) | ('success' in m['message'].lower())) for m in just_adr_2]
        # collect offers for each address that has offers
        just_offers, raw_4 = self.get_offers(addresses_used=adr_sample, auths=just_auths, adrs_response=just_adr_2, has_offers=has_offers)
        if just_offers is None: 
            print('mdu update failed')
            return -1
        else:
            print(f'Offers collected for {i}')
        
        # uncleaned format with all address and offer data
        a = list(zip(adr_sample, just_adr_2, has_offers, just_offers))
        return a
