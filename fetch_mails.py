from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
import json
import os.path
import pg8000
import pickle


# Defining the scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly', 
    'https://www.googleapis.com/auth/gmail.modify'
]
PATH = "/Users/ishanachinta/Documents/Personnel/Resume and hiring/Happy Fox Assignment/"


def authenticate():
    # Load or create credentials
    creds = None
    if os.path.exists(PATH + 'token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no credentials available, redirect to OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                PATH + 'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(PATH + 'token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def connect_to_postgresql():
    # Making connection to Emails Postgres table
    connection = pg8000.connect(user='ishan_user', password='123456', database='email_db_assignment', host='localhost', port=5432)
    return connection


def fetch_emails():
    # Fetch all Emails from Postgres
    connection = connect_to_postgresql()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM emails")
            emails = cursor.fetchall()
            return emails
        except pg8000.DatabaseError as e:
            print(f"Error while fetching emails from PostgreSQL: {e}")
        finally:
            connection.close()


def load_rules_from_json(filename):
    # Loading rules from Rules JSON file
    try:
        with open(filename, 'r') as file:
            rules = json.load(file)
        return rules
    except FileNotFoundError:
        print(f"Error: JSON file '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON file '{filename}' is not valid JSON.")
        return None


def apply_rule(rule, email):
    # Check if all conditions must match or any condition must match
    if rule['predicate'] == "All":
        conditions_met = all(check_condition(condition, email) for condition in rule['conditions'])
    elif rule['predicate'] == "Any":
        conditions_met = any(check_condition(condition, email) for condition in rule['conditions'])

    # Perform actions if conditions are met
    if conditions_met:
        perform_actions(rule['actions'], email)


def check_condition(condition, email):
    field = condition['field']
    predicate = condition['predicate']
    value = condition['value']
    field_mapping = {
        "id": 0,
        "message_id": 1,
        "sender": 2,
        "subject": 3,
        "received_at": 4,
        "snippet": 5,
    }

    # Get the index of the specified field from the email
    email_value = email[field_mapping.get(field)]

    # Convert the value to datetime if the field is a date/time field
    if isinstance(email_value, datetime.datetime) and predicate in ['less_than', 'greater_than']:
        value = datetime.datetime.strptime(value, '%Y-%m-%d')

    # Check if the condition is satisfied
    if predicate == "contains":
        return value.lower() in email_value.lower()
    elif predicate == "does_not_contain":
        return value.lower() not in email_value.lower()
    elif predicate == "equals":
        return email_value.lower() == value.lower()
    elif predicate == "does_not_equal":
        return email_value.lower() != value.lower()
    elif predicate == "less_than":
        return email_value < value
    elif predicate == "greater_than":
        return email_value > value


def perform_actions(actions, email_id):
    credentials = authenticate()
    service = build('gmail', 'v1', credentials=credentials)
    email_id = email_id[1]
    for action in actions:
        if action['action'] == 'mark_as_read':
            # Mark email as read
            service.users().messages().modify(userId='me', id=email_id, body={'removeLabelIds': ['UNREAD']}).execute()
            print(f"Marked email with ID {email_id} as read.")
        elif action['action'] == 'mark_as_unread':
            # Mark email as unread
            service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['UNREAD']}).execute()
            print(f"Marked email with ID {email_id} as unread.")
        elif action['action'] == 'move_message':
            # Move email to a specific label (folder)
            destination_folder = action['destination_folder']
            try:
                label_id = next(label['id'] for label in service.users().labels().list(userId='me').execute()['labels'] if label['name'] == destination_folder)
                service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}).execute()
                print(f"Moved email with ID {email_id} to folder: {destination_folder}.")
            except StopIteration:
                print(f"Label '{destination_folder}' not found.")


if __name__ == "__main__":
    # Fetch emails from PostgreSQL
    emails = fetch_emails()
    if emails:
        print("Fetched {} emails from the Emails database.".format(len(emails)))
    else:
        print("No emails found in the database.")

    # Load rules from JSON file
    rules = load_rules_from_json('rules.json')
    if rules:
        print("Loaded {} rules from JSON file.".format(len(rules['rules'])))
        print("Applying rules to fetched emails...")
        for email in emails:
            for rule in rules['rules']:
                apply_rule(rule, email)
    else:
        print("Failed to load rules.")
    print("--END--")
