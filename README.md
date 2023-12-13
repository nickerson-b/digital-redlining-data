# digital-redlining-data
Discussing, storing, and manipulating broadband data to explore digital redlining.

---

## File Structure
data_out: contains all files produced by the scrapers
1. Centurylink Data
  - test_2_data.csv: Final scraped centurylink data. Each row represents an address within a seattle block group, with the internal address information and broadband offers from centurylink. No headers. Column 1 is the GEOID of the block group, Column 2 is the address of the block group, formatted to match centurylink styling. Column 3 and 4 are json objects that contain the interal address information and broadband offer data respectively. The internal address datas contain information about the status of coverage, the closest wire center, the type of unit, and most importantly in some cases provides a link to centurylinks other service, quantum fiber. While many addresses have both traditional offers and a redirect link, there are a number of cases where the address request was unsuccessful, leading to there being no address or offer data. The requests  were likely redirected to the quantum fiber page for that address, which would result in no data because the scraper would view this as a failed request. Finally, the 'offersList' in the offers column consists of a list of offers, with most addresses that are covered having at least one. There is a lot of data here and I encourage anyone to dig in and find their own interesting information. The most obviously useful points of information are in the offersList where things like download and upload speed, type of technology, and cost data can be found. A small note on the cost data: I am unsure as to if there is a one-to-one correlation between the number listed as cost in this data and the prices advertised on the centurylink page.
  - centurylink_scraped.csv: First scrape. A lot of data is missing because this is the unfilled, uncleaned data.
  - cs_data_cleaned.csv: Cleaned and reformatted first scrape.

res: files required to run code in src

src: source code for scrapers
1. Centurylink scrapers
   - test_2.py: Logic to run the initial scrape
   - find_missing_offers_cl.py: Logic to run scrapes for data the first run missed.
   - century_link_scraper.py: package imported into test_2 and find_missing to make the requests to centurylink servers. The bulk of reusable code is here with the async request function that should only need to be modified slightly for use in other scrapers.
   - geoid_addresses, address_converter, bg_geoids: Files that are used minimally or not at all in the actual scraping process. They all serve different purposes in the goal of processing address information.
