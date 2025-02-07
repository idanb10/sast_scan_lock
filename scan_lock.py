#scan_lock.py

from datetime import timedelta
import datetime
import yaml
import SAST_api
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='scan_lock.log', filemode='a')

with open('sast_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

SAST_username = config['SAST_username']
SAST_password = config['SAST_password']
SAST_server_name = config['SAST_server_name']

SAST_auth_url = f"{SAST_server_name}/CxRestAPI/auth/identity/connect/token"
SAST_api_url = f"{SAST_server_name}/CxRestAPI"

def prepare_for_data_retention(unlock_all=False, lock_interval='weekly'):
    add_log_separator(f"Starting preparation for data retention: unlock_all={unlock_all}, lock_interval={lock_interval}")

    logging.info(f"scan_lock.prepare_for_data_retention: Accessing projects for user '{SAST_username}'. Time interval={lock_interval}")
    print(f"Accessing projects for user '{SAST_username}'")
    
    access_token = SAST_api.SAST_get_access_token(SAST_username, SAST_password, SAST_auth_url)
    if not access_token:
        error_message = f"Failed to obtain access token for user {SAST_username}."
        print(error_message)
        return ""
    
    projects_and_ids = []
    projects = SAST_api.SAST_get_projects(access_token=access_token, SAST_api_url=SAST_api_url)
    if not projects:
        error_message = f"Failed to obtain projects for user '{SAST_username}'."
        print(error_message)
        logging.warning(f"scan_lock.prepare_for_data_retention: '{error_message}'")
        return ""

    for project in projects:
        print(project)
        projects_and_ids.append({project['name']: project['id']})
        
    logging.info(f"scan_lock.prepare_for_data_retention: Projects and their IDs:\n {projects_and_ids}")
    project_name_and_scan_ids = {}
    
    for project in projects_and_ids:
        project_name, project_id = next(iter(project.items()))
        print(f"Getting successful scans for project '{project_name}'")
        logging.info(f"scan_lock.prepare_for_data_retention: Getting successful scans for project '{project_name}'")
        scans = SAST_api.SAST_get_scans(project_id=project_id, access_token=access_token, SAST_api_url=SAST_api_url)
        successful_scans = [scan for scan in scans if scan['status']['name'] == 'Finished']
        logging.info(f"scan_lock.prepare_for_data_retention: Successful scans:\n {successful_scans}")

        scan_info = [{'id': scan['id'], 'dateAndTime': scan['dateAndTime']['startedOn']} for scan in successful_scans]
        project_name_and_scan_ids[project_name] = scan_info
        
    if not project_name_and_scan_ids:
        error_message = f"Failed to obtain scans for user '{SAST_username}'."
        print(error_message)
        logging.warning(f"scan_lock.prepare_for_data_retention: '{error_message}'")
        return ""
    
    logging.info(f"scan_lock.prepare_for_data_retention: Project names, their scan IDs and dates :\n{project_name_and_scan_ids}")
 
    
    for project_name, scans in project_name_and_scan_ids.items():
        print(f"{project_name}: {scans}")
    
    if unlock_all:
        print("About to unlock all scans...")
        unlock_all_scans(access_token=access_token, SAST_api_url=SAST_api_url, project_name_and_scan_ids=project_name_and_scan_ids)
    else:
        print(f"About to lock scans {lock_interval} for each project...")
        lock_scans_by_interval(access_token=access_token, SAST_api_url=SAST_api_url, project_name_and_scan_ids=project_name_and_scan_ids, interval=lock_interval)


def unlock_all_scans(access_token, SAST_api_url, project_name_and_scan_ids):
    logging.info(f"scan_lock.unlock_all_scans: Unlocking scans across all projects...")
    for project_name, scans in project_name_and_scan_ids.items():
        
        print(f"Unlocking scans for project '{project_name}':")
        logging.info(f"scan_lock.unlock_all_scans: Unlocking scans for project '{project_name}'")

        scan_ids = []
        for scan in scans:
            scan_ids.append(scan['id'])
        logging.info(f"{project_name=}, {scan_ids=}")
        
        for scan_id in scan_ids:
            logging.info(f"scan_lock.unlock_all_scans: Unlocking scan with id '{scan_id}'")
            print(f"Unlocking scan with id '{scan_id}'")

            SAST_api.SAST_unlock_scan_by_id(access_token=access_token, SAST_api_url=SAST_api_url, scan_id=scan_id)
    print("Finished unlocking scans across all projects.")
    logging.info(f"scan_lock.unlock_all_scans: Finished unlocking scans across all projects.")


def lock_scans_by_interval(access_token, SAST_api_url, project_name_and_scan_ids, interval='weekly'):
    for project_name, scans in project_name_and_scan_ids.items():
        print(f"Processing project: {project_name}")
        logging.info(f"scan_lock.lock_scans_by_interval: Processing project: {project_name}")
        
        sorted_scans = sorted(scans, key=lambda x: x['dateAndTime'])
        
        if not sorted_scans:
            print(f"No scans found for project {project_name}")
            logging.warning(f"scan_lock.lock_scans_by_interval: No scans found for project {project_name}")
            continue
        
        scans_to_lock = []
        try:
            current_interval_start = datetime.datetime.strptime(sorted_scans[0]['dateAndTime'], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            current_interval_start = datetime.datetime.strptime(sorted_scans[0]['dateAndTime'], "%Y-%m-%dT%H:%M:%S")

        for scan in sorted_scans:
            try:
                scan_date = datetime.datetime.strptime(scan['dateAndTime'], "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                scan_date = datetime.datetime.strptime(scan['dateAndTime'], "%Y-%m-%dT%H:%M:%S")
            
            scan_date_str = scan_date.strftime("%Y-%m-%d %H:%M:%S")
            current_interval_start_str = current_interval_start.strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"scan_lock.lock_scans_by_interval: Scan date: {scan_date_str}, Current interval start: {current_interval_start_str}")
                        
            if scan_date >= current_interval_start:
                scans_to_lock.append(scan)
                if interval == 'weekly':
                    current_interval_start = scan_date + timedelta(days=7)
                elif interval == 'daily':
                    current_interval_start = scan_date + timedelta(days=1)
                
        for scan in scans_to_lock:
            try:
                SAST_api.SAST_lock_scan_by_id(scan_id=scan['id'], access_token=access_token, SAST_api_url=SAST_api_url)
                print(f"Locked scan {scan['id']} for project '{project_name}'")
                logging.info(f"Locked scan {scan['id']} for project '{project_name}'")
            except Exception as e:
                print(f"Failed to lock scan {scan['id']} for project '{project_name}': {str(e)}")
                logging.warning(f"scan_lock.lock_scans_by_interval: Failed to lock scan {scan['id']} for project '{project_name}': {str(e)}")

    print("Finished locking scans for all projects")
    logging.info("scan_lock.lock_scans_by_interval: Finished locking scans for all projects")
    
    
def print_menu():
    print("""
            Welcome to the SAST Scan Management Tool!

            Please choose an option:
            1. Lock scans weekly for all projects
            2. Lock scans daily for each project
            3. Unlock all scans
            4. Exit

            Enter the number of your choice: """)
    
def add_log_separator(message=""):
    separator = "=" * 50
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"\n{separator}\n{timestamp} - {message}\n{separator}\n")
    
    
def get_user_choice():
    while True:
        try:
            choice = int(input())
            if 1 <= choice <= 4:
                return choice
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")
           
            
def main():
    while True:
        print_menu()
        choice = get_user_choice()
        
        if choice == 1:
            print("Locking scans weekly for each project...")
            prepare_for_data_retention(unlock_all=False, lock_interval='weekly')
        elif choice == 2:
            print("Locking scans daily for each project...")
            prepare_for_data_retention(unlock_all=False, lock_interval='daily')
        elif choice == 3:
            print("Unlocking all scans across all projects...")
            prepare_for_data_retention(unlock_all=True)
        elif choice == 4:
            print("Exiting the program. Goodbye!")
            sys.exit(0)
    

if __name__ == '__main__':
    main()
    prepare_for_data_retention(unlock_all=True)    
