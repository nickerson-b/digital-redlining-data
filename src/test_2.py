# import statements
from geoid_addresses import *
from address_converter import *
# from bg_geoids import *
from century_link_scraper import *
import numpy as np
import pandas as pd
from csv import writer
import time


def main(rerun, s_num):
    # set up time checks
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
    # # 530330053041??
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

    # Work of collecting addresses and storing them by block groups done already
    # load in csv consisting of all addresses for all (workable) washington block groups
    adrs_expanded = pd.read_csv('digital-redlining-data/res/addresses_converted_cl.csv', dtype={'addresses':'object'})
    # clean data for json formatting
    adr_dicts = [json.loads(adr.replace("'", '"')) for adr in adrs_expanded.addresses]
    adrs_expanded['addresses'] = adr_dicts

    # convert all addresses to cl format
    cl_convr = AddressConverter('cl')
    adrs_expanded['cl_addresses'] = cl_convr.list_converter(list(adrs_expanded['addresses']))

    # time check
    c2 = time.perf_counter()
    print(f"{ format((c2-start),'.2f') } sec to prepare addresses")
 
    # get all the gid codes
    bg_codes = np.unique(adrs_expanded.bg_geoid.values)
    # set the codes to be only rerun block groups if necessary
    if rerun:
        bg_codes = pd.read_csv('rerun_codes.csv', header=None).transpose()[0].values
    # in case code is interrupted, set this index to restart at that position
    start_num = s_num
    bg_codes = bg_codes[start_num:]

    # go through each bg code with index for debugging
    for i, code in enumerate(bg_codes):
        # time for start of one block group run
        c3 = time.perf_counter()

        # Select all addresses affiliated with the current bg
        bg = adrs_expanded[adrs_expanded['bg_geoid'] == code]
        bg_adrs = list(bg['cl_addresses'])

        # set up scraper with the list of addresses
        scrp = CenturyLinkScraper(bg_adrs)

        # run the scraper
        print(f'START scraping run {i + start_num}, with bg {code} at {time.strftime("%H:%M:%S", time.localtime())}')
        data = scrp.run_scraper(i + start_num)
        
        # check that the data we want is returned
        # IF we aren't zipping an empty list (which we should never do anymore)
        # then this will never be none.
        if not data or data is None:
            # scrape_success[i + start_num] = False
            print(f"run {i + start_num} failed, skipping\n")
            d = list((i + start_num, code, -1))
            with open('digital-redlining-data/data_out/centurylink_scraped.csv', 'a') as f:
                writer_obj = writer(f)
                writer_obj.writerow(d)
            
            # save to two locations
            with open('t.csv', 'a') as f:
                writer_obj = writer(f)
                writer_obj.writerow(d)

            # output runtime stats
            c4 = time.perf_counter()
            print(f'FINISH scraping run {i + start_num}, with bg {code} at {time.strftime("%H:%M:%S", time.localtime())}')
            print(f"Completed in { format(( (c4-c3) / 60 ),'.2f') } min\n")
        # save the data collected
        else:
            # save the run number, the block group number, and all returned data
            d = list((i + start_num, code, data))
            with open('digital-redlining-data/data_out/centurylink_scraped.csv', 'a') as f:
                writer_obj = writer(f)
                writer_obj.writerow(d)
            
            # save to two locations
            with open('t.csv', 'a') as f:
                writer_obj = writer(f)
                writer_obj.writerow(d)

            # output runtime stats
            c4 = time.perf_counter()
            print(f'FINISH scraping run {i + start_num}, with bg {code} at {time.strftime("%H:%M:%S", time.localtime())}')
            print(f"Completed in { format(( (c4-c3) / 60 ),'.2f') } min\n")

    # From here, we should go through each block group again (maybe recursively?)
    # and check for missed addresses. Try each one again, then maybe try new addresses?
    '''
    read in bg from file [run num, bg code, [address, address data, offers]]
        fully re-run each with missing address data (maybe 3 times or until data is sent back)
        rerun just getting offers for those with addresses but no offers (maybe 3 time or until data is sent back)





    if has no offer, but auth succeeded, simply try again and if no response keep data
    if missing offer:
        did auth fail?
        if yes, retry auth
            Did second auth fail?
            if no, collect data
                if collection fails again, move to next step
            if yes, get new address (that hasn't been chosen)
                try scrape again

    for bg in bg list:
        async method queue
        for address in bg:
            if address has no offer:
                call async method that will do all the logic 
        execute async methods

    async get missed offers method(address):
        How many times have we tried this particular address?
            Has this address been failing auths?
                If yes, get new address and try this again

    [bg code, address, ]
    async get missed offers method(address):

    '''


if __name__ == '__main__':
    t = main(rerun=False, s_num=480)
    
'''

{'status': 1, 'message': 'Address_Validation_Service_Error. Service Unavailable', 'addrValInfo': {'result': '', 'billingSource': '', 'fullAddress': '527 N  84TH ST SEATTLE WA 98103 USA', 'addressId': None, 'mduInfo': {'mduList': None}, 'wireCenter': '', 'nearMatchAddress': None, 'nearMatchList': None, 'exactMatchAddress': None, 'companyOwnerId': None}, 'loopQualInfo': None, 'leadIndicator': None, 'leadIndicatorStatus': None, 'addressId': None, 'unitNumber': None, 'geoSecUnitId': None, 'googleInfo': None, 'biwfInfo': None, 'below940': False, 'existingService': False, 'expectedCompDate': None, 'lnppiMainDecision': None}

Team Booth 131 E

'''

