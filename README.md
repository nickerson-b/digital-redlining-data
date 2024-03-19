# digital-redlining-data
## An exploration of digital redlining in the Seattle area
*Created and maintained by Benjamin Nickerson in association with the Technology and Social Change lab (TASCHA) at the University of Washington, Seattle.*  

---

## Overview & Goals
This repository stores the work done by TASCHA exploring how digital redlining impacts areas across the Seattle area. This project primarily seeks to understand how to cost of broadband services change from block to block. Internet Service Providers (ISPs) don't typically make pricing details publicly accessible, and datasets compiled and maintained by the FCC do not contain pricing information. Additionally, the FCCs new mapping project has been criticized for its bias towards ISPs and is suspected to be inaccurate in many cases. As such, we have sought to collect and aggregate samples of ISP data for Seattle area addresses with the hope that this will both provide great insight into aspects of the digital divide in Seattle, as well as provide a launching point for anyone else looking to investigate this issue further.

The earlier work contained here explores the use of Census maps and geographies in defining areas of study, and the use of Census data in determining demographic information. This stage also explores the tools and methods for finding valid addresses to analyze. More recent efforts have been put towards collecting and analyzing data from the ISPs. While work continues on the collection of this data, resources are also being put towards the analysis of the data collected so far. 

---

## File Structure
*Purpose and contents of each folder. Note that while the structure of the repository mimics the layout of a traditional python project, since there is no central product or package being delivered, the contents of each folder are not what they might normally be.*

- data_out: Data produced by scrapers and processors. Currently contains centurylink data, quantum fiber data, and the full Lumen dataset. 
- doc: Logs, profiles, and (currently missing) analysis and documentation of process.
- res: Necessary data for running the scrapers, non-ISP data. Largely addresses, Census data and geographies for mapping.
- src: Python scripts used to scrape and curate data.
- test: Jupyter files for testing and limited analysis. These are primarily for "messing around" and are not necessarily useful scripts, and will not exist here permanently. 
- tools: Short, useful scripts (often Jupyter files) for manipulating data, or other similar processes.

---

## Details on important files
data_out: contains all files produced by the scrapers
1. Centurylink Data
  - test_2_data.csv: Final scraped centurylink data. Each row represents an address within a seattle block group, with the internal address information and broadband offers from centurylink. No headers. Column 1 is the GEOID of the block group, Column 2 is the address of the block group, formatted to match centurylink styling. Column 3 and 4 are json objects that contain the internal address information and broadband offer data respectively. The internal address data contains information about the status of coverage, the closest wire center, the type of unit, and most importantly in some cases provides a link to centurylink's other service, quantum fiber. While many addresses have both traditional offers and a redirect link, there are a number of cases where the address request was unsuccessful, leading to there being no address or offer data. The requests were likely redirected to the quantum fiber page for that address, which would result in no data because the scraper would view this as a failed request. Finally, the 'offersList' in the offers column consists of a list of offers, with most addresses that are covered having at least one. There is a lot of data here and I encourage anyone to dig in and find their own interesting information. The most obviously useful points of information are in the offersList where things like download and upload speed, type of technology, and cost data can be found. A small note on the cost data: I am unsure as to if there is a one-to-one correlation between the number listed as cost in this data and the prices advertised on the centurylink page.
  - centurylink_scraped.csv: First scrape. A lot of data is missing because this is the unfilled, uncleaned data.
  - cs_data_cleaned.csv: Cleaned and reformatted first scrape.

res: files required to run code in src

src: source code for scrapers
1. Centurylink scrapers
  - test_2.py: Logic to run the initial scrape
  - find_missing_offers_cl.py: Logic to run scrapes for data the first run missed.
  - century_link_scraper.py: package imported into test_2 and find_missing to make the requests to centurylink servers. The bulk of reusable code is here with the async request function that should only need to be modified slightly for use in other scrapers.
  - geoid_addresses, address_converter, bg_geoids: Files that are used minimally or not at all in the actual scraping process. They all serve different purposes in the goal of processing address information.
