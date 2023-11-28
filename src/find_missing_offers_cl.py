# import statements
# from geoid_addresses import *
# from address_converter import *
# from bg_geoids import *
from century_link_scraper import *
from ast import literal_eval
import numpy as np
import pandas as pd
import csv
import time

# given a row from a df, validate that data
def bad_data(row: list) -> bool:
    # print(row)
    bad = True
    if (row['coverage_response'] == -1):
        return bad
    # check if coverage request had internal error
    if (row['coverage_response']['status'] != 0):
        return bad
    # if coverage request has passed both of these tests, then we are assuming the info is accurate
    
    # Check if offer request failed
    # if (row['offers'] == -1) & ('out of region' in row['coverage_response']['message'].lower()):
    #     return bad
    if row['offers'] == -1:
        return bad
    if (row['offers']['offersList'] is None):
        return bad
    return not (bad)

# given a dataframe, return two lists of the rows with valid and invalid responses
# returns (good, bad)
def split_good_bad(rows: pd.DataFrame) -> tuple:
    to_be_fixed = []
    good_to_go = []
    for i in rows.index:
        row = rows.loc[i]
        if bad_data(row):
            to_be_fixed.append(row.to_list())
        else:
            good_to_go.append(row.to_list())
    return good_to_go, to_be_fixed

# given a df of all bad rows
# return a df of all good rows
def fix_rows(rows):
    # we know we have a list of bad requests
    # frame them for easier user
    rows_df = pd.DataFrame(rows, columns=['gid_code', 'address', 'coverage_response', 'offers', 'num_runs'])

    # make our scraper
    sc = CenturyLinkScraper(rows_df['address'].tolist())

    # run the scraper for the bad requests
    res =  sc.run_scraper(0)

    # frame the results
    res_df = pd.DataFrame(res, columns=['address', 'coverage_response', 'offers'])

    # update our rows
    rows_df.update(res_df)

    # update the number of times each call has been made, adding 3 if the response was successful but the overall call was not so it only goes one additional times
    rows_df['num_runs'] = rows_df.apply(lambda x: x['num_runs'] + 3 if (x['coverage_response']!=-1) else x['num_runs'] + 1, axis=1)

    # split into successful and failed calls
    good_to_go, maybe_to_be_fixed = split_good_bad(rows_df)

    # move any run too many times to good
    to_be_fixed = []
    for item in maybe_to_be_fixed:
        if item[4] >=5:
            good_to_go.append(item)
        else:
            to_be_fixed.append(item)

    # base case: rows are all good!
    if len(to_be_fixed) <= 0:
        return good_to_go
    # recursive case: rows are not all good
    else:
        return fix_rows(to_be_fixed) + good_to_go
    

# given a block group
# return a filled block group
def fill_data(rows: pd.DataFrame) -> pd.DataFrame:
    # split good and bad rows
    good_to_go, to_be_fixed = split_good_bad(rows)
    # return recursive function call
    return fix_rows(to_be_fixed) + good_to_go
    # return to_be_fixed + good_to_go
    # return fix_rows(to_be_fixed)

# fill in missing spots in our data
# by redoing failed requests
def main(g):
    # read in full dataset
    # each block group will be split off and filled in
    # this is a resource intensive approach requiring the entire dataset to be held in memory with its converted formatting
    # but it is simple and easier to read so this is how it will be done at this moment
    full_data = pd.read_csv('../data_out/cs_data_cleaned.csv', converters={'coverage_response': literal_eval, 'offers': literal_eval})
    full_data = full_data.reset_index().drop(columns=['run_num', 'index'])

    # list all unique bg codes
    bgs = set(full_data['gid_code'].values)
    
    # open our target file
    with open('../data_out/test_2_data.csv', 'a', newline='') as outfile:
        write_out = csv.writer(outfile)
        # select code, select rows with code, call the update function, passing the rows, write out
        g=g
        for code in bgs:
            # where the code matches, convert those rows to a new dataframe
            rows = pd.DataFrame(full_data.iloc[full_data[full_data['gid_code'] == code].index].values, columns=full_data.columns)

            # add column to track run number
            rows['num_runs'] = 0

            # run recursive scraper
            new_data = fill_data(rows)

            # clean data slightly
            new_df = pd.DataFrame(new_data, columns=['bg', 'address', 'coverage_response', 'offers', 'runs']).drop(columns=['runs']).replace(-1, None)
            
            # write the newly updated data
            write_out.writerows(new_df.values)


if __name__ == '__main__':
    main(g=0)