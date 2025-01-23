library(tidycensus)
library(tidyverse)
library(sf)

# if desired, set working directory
# setwd(dir = "")

census_api_key("e33daf8fcedf4e362f6b59f186da0bb0a4ffcce2")

# OPTIONAL: allows us to search through the ACS variables in order to determine which are needed
# search_var <- load_variables(2021,"acs5", cache=TRUE)
# view(search_var)

race <- get_acs(geography="tract",
                state = "WA",
                county = c("King","Pierce","Spokane"),
                variables = c(
                  totalpop = "B02001_001",
                  white = "B02001_002",
                  black = "B02001_003",
                  amin = "B02001_004",
                  asian = "B02001_005",
                  nh_pi = "B02001_006",
                  other = "B02001_007",
                  two_plus = "B02001_008",
                  two_other = "B02001_009",
                  two_ex = "B02001_010"),
                geometry = TRUE,
                year = 2021)

# writes estimates to shapefile
race_est = subset(race, select = -c(moe))
race_est_tidy <- pivot_wider(race_est, names_from="variable", values_from=c("estimate"))
st_write(race_est_tidy, "acs_race_est.shp", append=FALSE)

# writes margin of error (moe) to separate shapefile
race_moe = subset(race, select = -c(estimate))
race_moe_tidy <- pivot_wider(race_moe, names_from="variable", values_from=c("moe"))
st_write(race_moe_tidy, "acs_race_moe.shp", append=FALSE)