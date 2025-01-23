library(tidycensus)
library(tidyverse)
library(sf)

setwd(dir = "C:/Users/Cellar Door/Documents/2023 Digital Redlining/R Scripts/Tidycensus/")

census_api_key("e33daf8fcedf4e362f6b59f186da0bb0a4ffcce2")

# OPTIONAL: allows us to search through the ACS variables in order to determine which are needed
search_var <- load_variables(2021,"acs5", cache=TRUE)
view(search_var)

bb_race <- get_acs(geography="tract",
                state = "WA",
                county = c("King","Pierce","Spokane"),
                variables = c(
                  totalpop = "B02001_001",
                  c_bb_all = "B28008_004",
                  c_bb_wh = "B28009A_004",
                  c_bb_afam = "B28009B_004",
                  c_bb_amin = "B28009C_004",
                  c_bb_asian = "B28009D_004",
                  c_bb_nhpi = "B28009E_004",
                  c_bb_other = "B28009F_004",
                  c_bb_two = "B28009G_004",
                  c_bb_hisp = "B28009I_004"),
                geometry = TRUE,
                year = 2021)

view(bb_race)

# writes estimates to shapefile
bb_race_est = subset(bb_race, select = -c(moe))
bb_race_est_tidy <- pivot_wider(bb_race_est, names_from="variable", values_from=c("estimate"))
st_write(bb_race_est_tidy, "acs_bb_race_est.shp", append=FALSE)

# writes margin of error (moe) to separate shapefile
bb_race_moe = subset(bb_race, select = -c(estimate))
bb_race_moe_tidy <- pivot_wider(bb_race_moe, names_from="variable", values_from=c("moe"))
st_write(bb_race_est_tidy, "acs_bb_race_moe.shp", append=FALSE)