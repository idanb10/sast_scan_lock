# Checkmarx SAST Scan Lock Manager

This program manages the locking and unlocking of Checkmarx SAST scans for multiple projects. It allows you to automatically lock one scan per day/week for each project, starting from the earliest scan, or unlock all scans.

## Prerequisites

- Python 3.x
- Valid Checkmarx SAST credentials
- Required Python packages

## Usage


1. Clone this repository to your local machine:
```git clone https://github.com/idanb10/sast_scan_lock```
2. Navigate into the folder.
```cd sast_scan_lock```

3. Install the required packages:
```pip install -r requirements.txt```

4. Fill in your Checkmarx SAST credentials in the sast_config.yaml file

5. Run the program from the command line:
```python sast_lock.py```