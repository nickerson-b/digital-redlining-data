library(tidycensus)
library(tidyverse)
library(sf)

# if desired, set working directory
# setwd(dir = "")

census_api_key("e33daf8fcedf4e362f6b59f186da0bb0a4ffcce2")

# OPTIONAL: allows us to search through the ACS variables in order to determine which are needed
search_var <- load_variables(2021,"acs5", cache=TRUE)
view(search_var)

broadband_income <- get_acs(geography="tract",
                     state = "WA",
                     county = c("King","Pierce","Spokane"),
                     variables = c(has_bb="B28002_004",
                                   bb_10k = "B28004_004",
                                   bb_10_19k= "B28004_008",
                                   bb_20_34k= "B28004_012",
                                   bb_35_49k= "B28004_016",
                                   bb_50_74k= "B28004_020",
                                   bb_75k = "B28004_024"
                     ),
                     geometry = TRUE,
                     year = 2021)

# write estimates to shapefile
broadband_income_est = subset(broadband_income, select = -c(moe))
broadband_income_tidy <- pivot_wider(broadband_income_est, names_from="variable", values_from=c("estimate"))
st_write(broadband_income_tidy, "acs_broadband_income_est.shp", append=FALSE)

# write margin of error (moe) to separate shapefile
broadband_income_moe = subset(broadband_income, select = -c(estimate))
broadband_income_moe_tidy <- pivot_wider(broadband_income_moe, names_from="variable", values_from=c("moe"))
st_write(broadband_income_moe_tidy, "acs_broadband_income_moe.shp", append=FALSE)