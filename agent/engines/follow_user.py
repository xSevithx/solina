import requests

def get_user_id(auth, username):
    url = f'https://api.twitter.com/2/users/by/username/{username}'
    params = {
        'user.fields': 'id,username',
    }
    response = requests.get(url, auth=auth, params=params)
    if response.status_code == 200:
        user_data = response.json()
        return user_data['data']['id']
    else:
        print(f'Error fetching user ID: {response.status_code} - {response.text}')
        return None
    
def follow_user(auth, source_user_id, target_user_id):
    url = f'https://api.twitter.com/2/users/{source_user_id}/following'
    json_data = {
        'target_user_id': target_user_id,
    }
    response = requests.post(url, auth=auth, json=json_data)
    if response.status_code in [200, 201]:
        print(f'Successfully followed user ID {target_user_id}')
        return True
    else:
        print(f'Error: {response.status_code} - {response.text}')
        return False
    
def follow_by_username(auth, my_user_id, username):
    
    target = get_user_id(auth, username=username)
    if target:
        follow_user(auth, my_user_id, target)
    