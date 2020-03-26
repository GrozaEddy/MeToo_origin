from requests import get, post, delete
import pprint


print('-' * 100)
pprint.pprint(delete('http://localhost:5000/api/news/999').json())
print('-' * 100)
pprint.pprint(post('http://localhost:5000/api/news', json={'title': 'Заголовок'}).json())
print('-' * 100)
pprint.pprint(post('http://localhost:5000/api/news', json={'title': 'Заголовок', 'content': 'Текст новости',
                                                           'user_id': 1, 'is_private': False}).json())