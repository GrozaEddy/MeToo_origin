from requests import get, post, delete
import pprint


print('-' * 100)
pprint.pprint(delete('http://localhost:5000/api/feedback/1').json())
print('-' * 100)