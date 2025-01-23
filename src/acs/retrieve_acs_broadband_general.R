library(tidycensus)
library(tidyverse)
library(sf)

# if desired, set working directory
# setwd(dir = "")

census_api_key("e33daf8fcedf4e362f6b59f186da0bb0a4ffcce2")

# OPTIONAL: allows us to search through the ACS variables in order to determine which are needed
# search_var <- load_variables(2021,"acs5", cache=TRUE)
# view(search_var)

broadband <- get_acs(geography="tract",
               state = "WA",
               county = c("King","Pierce","Spokane"),
               variables = c(totalpop="B28002_001",
                             any_int="B28002_002",
                             dial_up="B28002_003",
                             any_bb="B28002_004",
                             no_int="B28002_013",
                             has_comp="B28003_002",
                             no_comp="B28003_006"
                             
               ),
               geometry = TRUE,
               year = 2021)

# write estimates to shapefile
broadband_est = subset(broadband, select = -c(moe))
broadband_est_tidy <- pivot_wider(broadband_est, names_from="variable", values_from=c("estimate"))
st_write(broadband_est_tidy, "acs_broadband_est.shp", append=FALSE)

# write margin of error (moe) to separate shapefile
broadband_moe = subset(broadband, select = -c(estimate))
broadband_moe_tidy <- pivot_wider(broadband_moe, names_from="variable", values_from=c("moe"))
st_write(broadband_moe_tidy, "acs_broadband_moe.shp", append=FALSE)