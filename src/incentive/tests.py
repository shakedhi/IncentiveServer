# Create your tests here.

import urllib
import urllib2
import re
import cookielib
from django.test import TestCase


# do POST
url_2 = 'http://127.0.0.1:8000/incentives'
headers = {'Authorization': 'Token fd8dfa28ee89fea2413f3232fe3162423a4da594'}
values = dict(schemeID='1')
data = urllib.urlencode(values)
req = urllib2.Request(url_2, data, headers=headers)
rsp = urllib2.urlopen(req)
content = rsp.read()

# print result
pat = re.compile('Title:.*')
print pat.search(content).group()
