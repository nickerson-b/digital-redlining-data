library(tidycensus)
library(tidyverse)
library(sf)

# if desired, set working directory
# setwd(dir = "")

census_api_key("")

# OPTIONAL: allows us to search through the ACS variables in order to determine which are needed
# search_var <- load_variables(2021,"acs5/subject", cache=TRUE)
# view(search_var)

income <- get_acs(geography="tract",
                state = "WA",
                county = c("King","Pierce","Spokane"),
                variables = c(totali = "S1901_C01_001",
                              i_under10k = "S1901_C01_002",
                              i_10_15k = "S1901_C01_003",
                              i_15_25k = "S1901_C01_004",
                              i_25_35k = "S1901_C01_005",
                              i_35_50k = "S1901_C01_006",
                              i_50_75k = "S1901_C01_007",
                              i_75_100k = "S1901_C01_008",
                              i_100_150k = "S1901_C01_009",
                              i_150_200k = "S1901_C01_010",
                              i_over200k = "S1901_C01_011",
                              i_mean = "S1901_C01_012",
                              i_median = "S1901_C01_013"),
                geometry = TRUE,
                year = 2021)

income = subset(income, select = -c(moe))

income_tidy <- pivot_wider(income, names_from="variable", values_from=c("estimate"))

# PROBLEM: shapefile truncates field names, so they're no longer unique and they throw an error when exporting.
# need to rename fields or decide on a new file type
st_write(income_tidy, "acs_income.shp", append=FALSE)