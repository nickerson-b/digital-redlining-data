# module summary
# note: This module is functional for the purposes of the project
#       at its current stage, but will need to be improved
# The purpose of this module is to produce a list of geoids for a given
# city in Washington state. 
# CURRENT CITIES SUPPORTED: ['Seattle', 'Spokane', 'Tacoma']
# this module contains one class, GeoidCollector, with 1 method that should be accessed
# this module requires 2 external files of geometry from the census bureau

# import statements
import geopandas as gpd
import numpy as np
import csv

# THIS CODE SUCKS FIX IT LATER
# city: string that is the name of the city
#       First letter should be capital
class GeoidCollector:
    def __init__(self, city: str):
        self.city = city
        self.wa_places = gpd.read_file("tl_2020_53_place\\tl_2020_53_place.shp")
        self.wa_bgs = gpd.read_file("tl_2020_53_bg\\tl_2020_53_bg.shp")
        self.place_names = np.array(['Seattle', 'Spokane', 'Tacoma'])
        self.wa_places = self.wa_places[(self.wa_places['NAME'].isin(self.place_names))].reset_index()[['NAME', 'geometry']]

    # paired with find city
    # if city (geo1) contains or intersects bg (geo2), return true
    def in_or_inter(self, geo1, geo2):
        # for our purposes, geo1 is the city and geo2 is the block group
        return (geo1.contains(geo2) | geo1.intersects(geo2))

    # paired with find city
    # if geo1 (the city geo) contains geo2 (bg geo), return true
    def inside(self, geo1, geo2):
        return (geo1.contains(geo2))
    
    # paired with produce list
    # given a mode, returns the name of the city that a block group 
    # 0: contained within
    # 1: intersects or is inside
    def find_city(self, block_group, mode):
        # creates a filter array by checking if the passed block group  intersecting with or contained within
        # each city geometry
        filter = []
        if mode == 0:
            filter = np.array([self.inside(city, block_group) for city in self.wa_places['geometry'].values])
        if mode == 1:
            filter = np.array([self.in_or_inter(city, block_group) for city in self.wa_places['geometry'].values])
        city_that_block_group_is_in = np.array(self.place_names[filter])
        if city_that_block_group_is_in.size == 0:
            return 'Not found in city list'
        else:
            return city_that_block_group_is_in[0]
    
    # THIS IS THE ONLY FUNCTION ANYONE NEEDS TO USES
    # Returns a list of geoids for the chosen city
    # this all could definitely just be the function produce list but im extra
    def produce_list(self):
        # determine which block groups are WHOLLY CONTAINED in census defined city geography
        city_inside = [self.find_city(bg, 0) for bg in np.array(self.wa_bgs['geometry'].values)]
        # determine which block groups are WHOLLY CONTAINED and INTERSECTED BY the census defined city geography 
        city_intersects = [self.find_city(bg, 1) for bg in np.array(self.wa_bgs['geometry'].values)]

        # create new columns in df to track which intersect and which are contained
        self.wa_bgs['CITY_INSIDE'] = city_inside
        self.wa_bgs['CITY_INTERSECTS'] = city_intersects
        
        # for the purposes of this project, we will be considering block groups that
        # BOTH ARE CONTAINED AND INTERSECT as part of the city
        bg_codes = list(self.wa_bgs[(self.wa_bgs['CITY_INSIDE'] == self.city) | (self.wa_bgs['CITY_INTERSECTS'] == self.city)].reset_index().GEOID)
        return bg_codes
    