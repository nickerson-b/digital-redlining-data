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
### Datasets (/data_out):
CenturyLink Data:
- centurylink_scraped.csv: Results of the first CenturyLinkScraper runs. Unfiltered, unedited data for each of the addresses sampled for the Seattle area (10% by block group).
- cs_data_cleaned.csv: An intermediary view of the CenturyLink data, put in a more proper csv format.
- cl_data.csv: Broadband offers for a stratified sample of seattle addresses. Around 3000 addresses were automatically redirected to their Quantum Fiber pages, and the scraper was unable to capture this. Any row with missing data in both the third and fourth (verification response and offer response) columns is likely to have been redirected. The columns for this data are Block Group Geoid, Address, Address verification response, and Offer response. These columns are expanded in cl_data_price_speed.csv.
- cl_data_price_speed.csv: The price and speed of broadband offers for a stratified sample of Seattle area addresses from CenturyLink. In progress, to be added soon.

Quantum Data:
- quantum_pages.csv: Broadband offers from Quantum Fiber for a number of addresses in the Seattle area. These addresses specifically are the addresses that were automatically redirected during use of the CenturyLink scraper.
- quantum_pages_all.csv: Broadband offers from Quantum Fiber for a stratified (10% by block group) sample of addresses in the Seattle area. Not currently complete.
- quantum_pages directory: Contains the html (as txt) for each of the addresses that had given redirect failures to the CenturyLink scraper. 
- new_quantum_run directory: Contains the html (as txt) for reach address that was scraped by the CenturyLink scraper. Not fully collected yet, in progress. 

### Scrips and packages (/src):
Quantum Data Collection:
- quantum_scraper.py: This file contains the QuantumScraper class which takes a list of addresses and collects the offers page for quantum fiber. The whole page for each address is downloaded, as opposed to simple json like with the CenturyLinkScraper. As such, an additional script is needed to process these pages. Use of the QuantumScraper can be found in quantum_scraper.py file directly, and processing of the pages can be found in the process_quantum_pages.py.
- process_quantum_pages.py: This file contains a script that processes pages collected by the quantum scraper, extracting information about broadband offers and processing them into a csv file.

Century Link Data Collection:
- century_link_scraper.py: This file contains the CenturyLinkScraper class, which takes a list of addresses and collects the centurylink offers for those addresses. This code was written closer to the start of the project and will be updated to match python style guides and best practices. An example of the scraper being used can be found in both run_cl_scraper.py and find_missing_offers_cl.py.
- run_cl_scraper.py: This file contains a script that uses the CenturyLinkScraper with information from the various address collecting and transforming packages.
- find_missing_offers_cl.py: This file contains a script that will use the CenturyLinkScraper and a partially filled dataset to finish collecting the data.

Address Collection and Manipulation:
- address_converter.py: This file contains a class, AddressConverter, which currents is capable of converting a given address (collected from the BigLocalNews United States Place Sampler) into a format usable in centurylink requests.
- bg_geoids.py: This file contains a class, GeoidCollector, which returns the list of block group geoids for a given city using census data. Current it can do this for Seattle, Tacoma, and Spokane. This code is old and is not worth updating as it has served its purpose.
- geoid_addresses.py: This file contains a number of functions helpful in collecting addresses from the BigLocalNews United States Place Sampler. 

ACS:
- Created by Teddy Davenport. These scripts were created in order to automatically retrieve GIS data from the US Census' American Community Survey.

### test, tools, res, and doc
Breakdown coming soon.
