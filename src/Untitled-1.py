# import statements
import grequests
import csv
from requests.adapters import HTTPAdapter, Retry
from random import sample, randint
import json
import requests
import os
import time

# print(f'current time is : {time.strftime("%H:%M:%S", time.localtime())}')
# n = 40546832
# t = 8
# inputNumber = format(10.65432465424635753,'.2f')
# print(f"This is a string with other {n} values {t} that need to stay {inputNumber}")
status_forcelist = list(x for x in requests.status_codes._codes if x not in [200, 306])
print(status_forcelist)

# just_auths = ['akaldafkl', 18, 'FUCK', (1, 2, 3), -1, "200", -1]

# failed_auths = sum( [True if el == -1 else False for el in just_auths] )

# print(failed_auths)