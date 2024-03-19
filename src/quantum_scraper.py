"""Module providing a QuantumScraper class and necessary functions.
Runs the scraper if run as main.
"""

# import statements
import time
import csv
import os.path
import logging
import grequests
from requests.adapters import HTTPAdapter, Retry
from lxml import etree
import requests


class QuantumScraper:
    """Class that uses out folder and proxy to scrape quantum pages"""

    def __init__(self, outfolder: str = 'out', run_num: int = 0) -> None:
        # init logging
        logging.basicConfig(filename='../doc/quantum_scraper.log', encoding='utf-8',
                            level=logging.DEBUG)
        print(f'{time.strftime("%H:%M:%S", time.localtime())}: initializing scraper.')
        logging.info('%s: initializing scraper.', time.strftime("%H:%M:%S", time.localtime()))

        # init proxy, outfolder, and 'globals'
        self.outfolder = outfolder
        self.p = 'https://customer-rnickben:6TBcLj4Ugh9M@us-pr.oxylabs.io:10000'  # Set proxy before use
        self.status_list = list(x for x in requests.status_codes._codes
                                if x not in [200, 301, 302, 307, 308])
        self.run_num = run_num

    def get_dwsid(self, n: int = 1) -> list:
        """
        Asynchronously request dwsids from quantum
        :param n: number of dwsids to request
        :type n: int
        :returns: n dwsids as a list of strings or None if failed
        :rtype: list
        """
        # set session
        with requests.Session() as s:
            retries = Retry(total=4, backoff_factor=.2,
                            status_forcelist=self.status_list, raise_on_status=True)
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set loop
            target_url = 'https://www.quantumfiber.com/'
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            }
            tasks = [
                grequests.get(
                    url=target_url,
                    proxies={'https': self.p},
                    session=s,
                    headers=headers
                )
                for _ in range(n)
            ]

            # execute tasks
            raw_responses = []
            for response in grequests.imap(
                tasks,
                exception_handler=exception_handler,
                size=10
            ):
                raw_responses.append(response)

        # process responses
        cleaned_responses = []
        for res in raw_responses:
            if res != -1:
                cleaned_responses.append(res.cookies.get_dict()['dwsid'])
            else:
                cleaned_responses.append(None)
        return cleaned_responses

    def get_csrf(self, dwsids: list) -> list:
        """
        Asynchronously request a csrf code for each dwsid code given
        :param dwsids: list of dwsid codes to generate an associating csrf for
        :type dwsids: list
        :returns: list of csrfs in the same order as the list of dwsids given
        :rtype: list 
        """
        # set session
        with requests.Session() as s:
            retries = Retry(total=4, backoff_factor=.2, status_forcelist=self.status_list,
                            raise_on_status=True, raise_on_redirect=False)
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set loop
            target_url = 'https://www.quantumfiber.com/shop/smartNidSpeeds'
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            tasks = [
                grequests.get(
                    url=target_url,
                    proxies={'https': self.p},
                    session=s,
                    headers=headers,
                    cookies={'dwsid': dwsid},
                    # allow_redirects=True
                )
                if dwsid is not None
                else grequests.get('https://httpbin.org/status/404')
                for dwsid in dwsids
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                tasks,
                exception_handler=exception_handler,
                size=10
            ):
                raw_responses.append((index, response))
            raw_responses.sort()  # sorts default ascending, which is desired

        # process responses, res[0] is just index
        cleaned_responses = []
        for res in raw_responses:
            if (res[1] != -1) and (res[1].status_code == 200):
                cleaned_responses.append(self.extract_csrf(res[1]))
            else:
                cleaned_responses.append(None)
        return cleaned_responses

    def adr_conf(self, adrs: list, dwsids: list, csrfs: list) -> list:
        """
        Asynchronously request quantum to tie address data to given sessions
        :param adrs: list of addresses to request data for
        :type adrs: list
        :param dwsids: list of dwsid codes representing a session, paired with
            a csrf at the same index in param csrfs
        :type dwsids: list
        :param csrfs: list of csrf codes representing a session, paired with a 
            dwsid at the same index in param dwsids
        :type csrfs: list
        :returns: list of responses from quantum
        """
        # set session
        with requests.Session() as s:
            retries = Retry(total=4, backoff_factor=.3,
                            status_forcelist=self.status_list, raise_on_status=True)
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set loop
            target_url = (
                'https://www.quantumfiber.com/on/demandware.store/Sites-QFCC-Site/'
                'default/AddressChecker-GetServiceability'
            )
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            tasks = [
                grequests.post(
                    url=target_url,
                    proxies={'https': self.p},
                    session=s,
                    headers=headers,
                    cookies={'dwsid': dwsid},
                    data={'dwfrm_addressChecker_o2check': adr,
                          'dwfrm_addressChecker_centurylinkExisting': 'false', 'csrf_token': csrf}
                )
                if ((dwsid is not None) and (csrf is not None))
                else grequests.get('https://httpbin.org/status/404')
                for adr, dwsid, csrf in list(zip(adrs, dwsids, csrfs))
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                tasks,
                exception_handler=exception_handler,
                size=10
            ):
                raw_responses.append((index, response))
            raw_responses.sort()  # sorts default ascending, which is desired

        # process responses
        cleaned_responses = []
        for res in raw_responses:
            if res[1] != -1:
                cleaned_responses.append(res[1])
            else:
                cleaned_responses.append(None)
        return cleaned_responses

    def save_page(self, dwsids: list, adrs: list) -> None:
        """
        Asynchronously request page with offer data for the given session
        Saves this page to the scrapers outfolder
        """
        # set session
        with requests.Session() as s:
            retries = Retry(
                total=4,
                backoff_factor=.3,
                status_forcelist=self.status_list,
                raise_on_status=True,
                raise_on_redirect=False
            )
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # set loop
            target_url = 'https://www.quantumfiber.com/shop/smartNidSpeeds'
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            tasks = [
                grequests.get(
                    url=target_url,
                    proxies={'https': self.p},
                    session=s,
                    headers=headers,
                    cookies={'dwsid': dwsid}
                )
                if dwsid is not None
                else grequests.get('https://httpbin.org/status/404')
                for dwsid in dwsids
            ]

            # execute tasks
            raw_responses = []
            for index, response in grequests.imap_enumerated(
                tasks,
                exception_handler=exception_handler,
                size=10
            ):
                raw_responses.append((index, response))
            raw_responses.sort()  # sorts default ascending, which is desired

        # process responses
        for res in raw_responses:
            if (res[1] != -1) and (res[1].status_code == 200):
                with open(os.path.join(self.outfolder, adrs[res[0]]+'.txt'), \
                          'w', encoding='utf8') as out:
                    out.write(res[1].text)
            else:
                with open(os.path.join(self.outfolder, adrs[res[0]]+'.txt'), \
                          'w', encoding='utf8') as out:
                    out.write("None")

    def extract_csrf(self, response):
        """
        Extracts csrf tag from given html response
        """
        g = response.iter_content(decode_unicode=True)
        line = []
        for item in g:
            if item == '\n':
                line = ''.join(line)
                if 'csrf' in line:
                    break
                line = []
            else:
                line.append(item)

        tree = etree.HTML(line)
        csrf = tree.find(".//input").get('value')
        return csrf

    def scrape(self, addresses: list) -> None:
        """runs scraper"""

        # set timer
        # start = time.perf_counter() # not used
        print(f'{time.strftime("%H:%M:%S", time.localtime())}: Scraper started.')
        logging.info('%s: Scraper started.', time.strftime(
            "%H:%M:%S", time.localtime()))

        # in batches, do following:
        # get ids
        # get csrfs
        # call data to sessions
        # save pages
        run_num = self.run_num
        for adr_chunk in chunker(addresses, 10):
            # start run
            print(
                f'{time.strftime("%H:%M:%S", time.localtime())}: Run {run_num} with '
                f'{len(adr_chunk)} addresses START.'
            )
            logging.info('%s: Run %s with %s addresses START.', time.strftime(
                "%H:%M:%S", time.localtime()), run_num, len(adr_chunk))

            # get session ids
            print(f'{time.strftime("%H:%M:%S", time.localtime())}:     requesting dwsids...')
            logging.info('%s:     requesting dwsids...',
                         time.strftime("%H:%M:%S", time.localtime()))
            dwsids = self.get_dwsid(len(adr_chunk))

            # get security code
            print(f'{time.strftime("%H:%M:%S", time.localtime())}:     requesting csrfs...')
            logging.info('%s:     requesting csrfs...',
                         time.strftime("%H:%M:%S", time.localtime()))
            csrfs = self.get_csrf(dwsids)

            # join the address to the session
            print(f'{time.strftime("%H:%M:%S", time.localtime())}:     joining session...')
            logging.info('%s:     joining session...',
                         time.strftime("%H:%M:%S", time.localtime()))
            # unsure what to do with responses?
            adrs_responses = self.adr_conf(adr_chunk, dwsids, csrfs)

            # doc the response
            for i, res in enumerate(adrs_responses):
                if res is None:
                    print(f'{time.strftime("%H:%M:%S", time.localtime())}:     WARN: No response'
                          f' from {adr_chunk[i]}')
                    logging.warning('%s:     no response from %s', time.strftime(
                        "%H:%M:%S", time.localtime()), adr_chunk[i])
                if 'action' in res and res['action'] != 'AddressChecker-GetServiceability':
                    print(f'{time.strftime("%H:%M:%S", time.localtime())}:     WARN: unexpected'
                          f' response from {adr_chunk[i]}\n{res}')
                    logging.warning('%s:     unexpected response from %s\n%s', time.strftime(
                        "%H:%M:%S", time.localtime()), adr_chunk[i], res)

            # save joined sessions
            print(f'{time.strftime("%H:%M:%S", time.localtime())}:     saving pages...')
            logging.info('%s:     saving pages...',
                         time.strftime("%H:%M:%S", time.localtime()))
            self.save_page(dwsids, adr_chunk)

            print(f'{time.strftime("%H:%M:%S", time.localtime())}: Run {run_num} with '
                  f'{len(adr_chunk)} addresses COMPLETE.')
            logging.info('%s: Run %s with %s addresses COMPLETE.', time.strftime(
                "%H:%M:%S", time.localtime()), run_num, len(adr_chunk))
            # count run
            run_num += 1


def chunker(seq, size):
    """
    CREDIT: https://stackoverflow.com/a/434328
    """
    return list(seq[pos:pos + size] for pos in range(0, len(seq), size))


def exception_handler(request, exception):
    """ Handle failed requests
    when a request fails (including all retries), simply return -1 to show that it has failed
    """
    # print([resp.url for resp in request.history])
    print(f'Failed request: {exception}\nStatus code: {request}')
    return -1


if __name__ == "__main__":
    # get addresses
    all_addresses = []
    with open('../res/adrs_for_quantum.csv', encoding='utf-8') as a:
        a = csv.reader(a)
        for ad in a:
            all_addresses.append(ad[0])
    print(f'got some addresses! \n{all_addresses[:10]}')
    # init scraper
    q = QuantumScraper(outfolder='../data_out/new_quantum_run')
    q.scrape(all_addresses)