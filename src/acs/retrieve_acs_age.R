library(tidycensus)
library(tidyverse)
library(sf)

# if desired, set working directory
# setwd(dir = "")

census_api_key("e33daf8fcedf4e362f6b59f186da0bb0a4ffcce2")

# OPTIONAL: allows us to search through the ACS variables in order to determine which are needed
# search_var <- load_variables(2021,"acs5/subject", cache=TRUE)
# view(search_var)

age <- get_acs(geography="tract",
                     state = "WA",
                     county = c("King","Pierce","Spokane"),
                     variables = c(
                       totalpop = "S0101_C01_001",
                       age_under5 = "S0101_C01_002",
                       age_5_9 = "S0101_C01_003",
                       age_10_14 = "S0101_C01_004",
                       age_15_19 = "S0101_C01_005",
                       age_20_24 = "S0101_C01_006",
                       age_25_29 = "S0101_C01_007",
                       age_30_34 = "S0101_C01_008",
                       age_35_39 = "S0101_C01_009",
                       age_40_44 = "S0101_C01_010",
                       age_45_49 = "S0101_C01_011",
                       age_50_54 = "S0101_C01_012",
                       age_55_59 = "S0101_C01_013",
                       age_60_64 = "S0101_C01_014",
                       age_65_69 = "S0101_C01_015",
                       age_70_74 = "S0101_C01_016",
                       age_75_80 = "S0101_C01_017",
                       age_80_84 = "S0101_C01_018",
                       age_over80 = "S0101_C01_019"
                     ),
                     geometry = TRUE,
                     year = 2021)

# write estimates to shapefile
age_est = subset(age, select = -c(moe))
age_est_tidy <- pivot_wider(age_est, names_from="variable", values_from=c("estimate"))
st_write(age_est_tidy, "acs_age_est.shp", append=FALSE)

# write margin of error (moe) to shapefile
age_moe = subset(age, select = -c(estimate))
age_moe_tidy <- pivot_wider(age_moe, names_from="variable", values_from=c("moe"))
st_write(age_moe_tidy, "acs_age_moe.shp", append=FALSE)