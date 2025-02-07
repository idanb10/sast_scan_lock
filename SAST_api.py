#SAST_api.py

import requests
import logging

def SAST_get_access_token(SAST_username, SAST_password, SAST_auth_url):
    try:
        logging.info(f"SAST_api.SAST_get_access_token: Attempting to obtain access token for user '{SAST_username}'")
        payload = {
            'scope': 'access_control_api sast_api',
            'client_id': 'resource_owner_sast_client',
            'grant_type': 'password',
            'client_secret': '014DF517-39D1-4453-B7B3-9930C563627C',
            'username': SAST_username,
            'password': SAST_password
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(SAST_auth_url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        access_token = response.json()['access_token']
        logging.info("SAST_api.SAST_get_access_token: Access token obtained.")
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f"SAST_api.SAST_get_access_token: Failed to obtain access token for user '{SAST_username}'")
        #print(f"Exception: get SAST access token failed: {e}")
        return ""

def SAST_get_projects(access_token, SAST_api_url):
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        url = f'{SAST_api_url}/projects'

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        #print(f"Exception: SAST_get_projects: {e}")
        return ""
    
def SAST_get_project_ID(access_token, project_name, SAST_api_url):
    try:
        projects = SAST_get_projects(access_token, SAST_api_url)
        projId = next((project['id'] for project in projects if project['name'] == project_name), 0)
    except Exception as e:
        #print(f"Exception: SAST_get_project_ID: {e}")
        return ""
    return projId


def SAST_lock_scan_by_id(access_token, SAST_api_url, scan_id):
    url = f"{SAST_api_url}/sast/lockScan"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'id': scan_id
    }
    
    response = requests.put(url=url, headers=headers, params=payload)
    logging.info(f"SAST_api.SAST_lock_scan_by_id : Lock scan response.json : {response.json()}")
    return response.json()

def SAST_unlock_scan_by_id(access_token, SAST_api_url, scan_id):
    url = f"{SAST_api_url}/sast/unLockScan"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'id': scan_id
    }
    
    response = requests.put(url=url, headers=headers, params=payload)
    logging.info(f"SAST_api.SAST_unlock_scan_by_id : Unlock scan response.json : {response.json()}")
    return response.json()

    
def SAST_get_scans(access_token, SAST_api_url, project_id):
    
    url = f"{SAST_api_url}/sast/scans?projectId={project_id}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    
    return response.json()
