# import statements
from geoid_addresses import *
from address_converter import *
# from bg_geoids import *
from century_link_scraper import *
import numpy as np
import pandas as pd
from csv import writer
import time


def main(rerun):
    start = time.perf_counter()
    # ##### Code under here disabled for debugging purposes
    # # get geoids for seattle
    # seattle_collector = GeoidCollector('Seattle')
    
    # # list of block group geoids
    # seattle_bg_geoids = seattle_collector.produce_list()
    # print(seattle_bg_geoids[1:10])
    # c1 = time.perf_counter()
    # print(f"{c1-start} seconds to collect block group geoids")
    
    # # get gid codes for each block group so that we can sample them with usps
    # seattle_bg_gids = get_gid_from_geoid(seattle_bg_geoids)
    
    # # make sure results are returned properly
    # if seattle_bg_gids == -1:
    #     raise Exception("Failed to get gids")
    # print(seattle_bg_gids[1:10])
    # c2 = time.perf_counter()
    # print(f"{c2-c1} seconds to collect block group geoids")

    # # get addresses from ids
    # addresses = get_bg_addresses(geoids=seattle_bg_geoids, gids=seattle_bg_gids)

    # # create data frame for addresses
    # adrs = pd.DataFrame(addresses)
    # adrs = adrs.rename({0: 'bg_geoid', 1: 'addresses'}, axis='columns')
    # adrs_expanded = adrs.explode(column='addresses')

    # # clean data
    # # NOTE: block group 530359901000 and 530339901000 are block groups with 0 residents and oddly no geography on the census website
    # # they are removed from consideration with the first dropna call.
    # # additionally, block group 530330242002 had a number of addresses that were missing values.
    # # 72 of those are removed with the second dropna call
    # def dict_has_none(d):
    #     if None in d['properties'].values():
    #         return None
    #     return d
    # adrs_expanded = adrs_expanded.dropna()
    # adrs_expanded['addresses'] = [dict_has_none(d) for d in adrs_expanded['addresses']]
    # adrs_expanded = adrs_expanded.dropna()
    # adrs_expanded.to_csv('addresses_converted_cl.csv', index_label='idx')

    adrs_expanded = pd.read_csv('addresses_converted_cl.csv', dtype={'addresses':'object'})
    adr_dicts = [json.loads(adr.replace("'", '"')) for adr in adrs_expanded.addresses]
    adrs_expanded['addresses'] = adr_dicts

    # convert addresses to cl format
    cl_convr = AddressConverter('cl')
    
    adrs_expanded['cl_addresses'] = cl_convr.list_converter(list(adrs_expanded['addresses']))
    c2 = time.perf_counter()
    print(f"{c2-start} seconds to prepare addreses")

    # collecting addresses 
    # get all the gid codes
    bg_codes = np.unique(adrs_expanded.bg_geoid.values)
    start_num = 48
    bg_codes = bg_codes[start_num:]
    if rerun:
        bg_codes = pd.read_csv('rerun_codes.csv', header=None).transpose()[0].values
    bg_codes = bg_codes[start_num:]
    # final data from the scraping
    trial_data = []
    # scrape_success = [True] * len(bg_codes)
    # go through each code with index for debugging
    for i, code in enumerate(bg_codes):
        c3 = time.perf_counter()
        # Select all addresses affiliated with the current code
        bg = adrs_expanded[adrs_expanded['bg_geoid'] == code]
        bg_adrs = list(bg['cl_addresses'])

        # set up scraper with the list of addresses
        scrp = CenturyLinkScraper(bg_adrs)

        # run the scraper ( all logic handled in package )
        print(f'scraping: {i + start_num}, bg: {code}')
        data = scrp.run_scraper(i + start_num)
        if not data or data is None:
            # scrape_success[i + start_num] = False
            print(f"run {i + start_num} failed, skipping")
        else:
            # save data
            trial_data.append((i + start_num, code, data))
            d = list((i + start_num, code, data))
            print(f"bg {i + start_num}: saviang {code}")
            with open('test_2_data.csv', 'a') as f:
                writer_obj = writer(f)
                writer_obj.writerow(d)
            c4 = time.perf_counter()
            print(f"Completed in {((c4-c3) / 60)} min")
    return trial_data

if __name__ == '__main__':
    t = main(rerun=True)
    