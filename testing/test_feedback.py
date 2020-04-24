from requests import get, post, delete
import pprint


print('-' * 100)
pprint.pprint(get('http://localhost:5000/api/feedback/1').json())
print('-' * 100)
pprint.pprint(get('http://localhost:5000/api/feedback').json())
print('-' * 100)