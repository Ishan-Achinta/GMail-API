from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
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


def fetch_emails(count):
    # Fetch mails using GMail API
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
    else:
        print("Messages:")
        for message in messages[:count]:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            print("Message ID:", msg['id'])
            print("Snippet:", msg['snippet'])
            payload = msg['payload']
            headers = payload['headers']
            for header in headers:
                if header['name'] == 'From':
                    print("From:", header['value'])
                elif header['name'] == 'Subject':
                    print("Subject:", header['value'])
            store_email_in_database(msg)


def connect_to_postgresql():
    # Making connection to Emails Postgres table
    connection = pg8000.connect(user='ishan_user', password='123456', database='email_db_assignment', host='localhost', port=5432)
    return connection


def store_email_in_database(email_message):
    sender = ""
    subject = ""
    received_at = None
    snippet = ""
    message_id = email_message['id']
    
    payload = email_message['payload']
    headers = payload['headers']
    for header in headers:
        if header['name'] == 'From':
            sender = header['value']
        elif header['name'] == 'Subject':
            subject = header['value']
    
    snippet = email_message.get('snippet', "")

    if 'internalDate' in email_message and email_message['internalDate']:
        # Convert milliseconds since epoch to a datetime object
        received_at_timestamp = int(email_message['internalDate']) / 1000.0
        received_at = datetime.datetime.fromtimestamp(received_at_timestamp).strftime('%Y-%m-%d %H:%M:%S')

    connection = connect_to_postgresql()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO emails (message_id, sender, subject, received_at, snippet) VALUES (%s, %s, %s, %s, %s)", (message_id, sender, subject, received_at, snippet))
            connection.commit()
            print("Email stored successfully in PostgreSQL")
        except pg8000.DatabaseError as e:
            print(f"Error while inserting email into PostgreSQL: {e}")
        finally:
            connection.close()


if __name__ == '__main__':
    count_required = int(input("Enter the number of emails to be fetched: "))
    fetch_emails(count_required)