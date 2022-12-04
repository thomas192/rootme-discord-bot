from requests import get
from dotenv import load_dotenv
from utils import load_from_json, write_to_json
import os


load_dotenv()
BASE_URL = 'https://api.www.root-me.org'
USER_AGENT = 'curl/7.68.0'
COOKIES = {'api_key': '' + os.getenv('ROOTME_TOKEN')}


# Retrieves fresh user data from API
def get_user_data(uid: int) -> str:
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    r = get(f'{BASE_URL}/auteurs/{uid}', headers=headers, cookies=COOKIES)
    return r.json()


# Retrieves newly obtained flags for a user
def get_new_flags(uid: int) -> list:
    print('get_new_flags()')
    old = load_from_json(f'profiles/{uid}.json')
    new = get_user_data(uid)
    # If user did not flag new challenges, return
    if len(old['validations']) == len(new['validations']):
        return []
    # Store flags
    data = [chall for chall in new['validations'] if chall not in old['validations']]
    # Update user data
    write_to_json(f'profiles/{uid}.json', new)
    return data


# Retrieves info about a challenge
def retrieve_challenge(challenge) -> str:
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    r = get(f"{BASE_URL}/challenges/{challenge}", headers=headers, cookies=COOKIES)
    return r.json()
