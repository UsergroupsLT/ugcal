from __future__ import unicode_literals

import datetime
import httplib2
import json
import os
import requests

import oauth2client
from apiclient import discovery

GROUPS = [
    # 'Technarium',
    # 'Vilnius-DevOps-Meetup',
    # 'Vilnius-Hadoop-Meetup',
    # 'Vilnius-js',
    # 'functional-vilnius',
    # 'vilnius-hack-and-tell',
    'vilniusphp',
    # 'vilniuspy',
    # 'vilniusrb',
    ]


try:
    import argparse
    flags = argparse.ArgumentParser(
        parents=[oauth2client.tools.argparser]).parse_args()
except ImportError:
    flags = None


class Config:

    CLIENT_SECRET_FILE = 'client_secret.json'

    def __init__(self):
        config_file = file(self.CLIENT_SECRET_FILE, 'r')
        self._config = json.loads(config_file.read())

    def get(self, key):
        """Retrieve custom value from config."""
        return self._config['other'][key]

    def get_secret_file(self):
        return self.CLIENT_SECRET_FILE


class MeetupCom:
    """Meetup.com API client."""
    def __init__(self):
        self._config = Config()

    def get_groups(self):
        """Retrieve list of groups."""
        return [self.get_results(name) for name in GROUPS]

    def get_results(self, endpoint, params={}):
        params['key'] = self._config.get('meetup_api_key')
        url = "http://api.meetup.com/" + endpoint
        request = requests.get(url, params=params)
        data = request.json()
        return data


class GoogleCalendar:
    """Google Calendar API client."""

    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

    def __init__(self):
        self._config = Config()

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'gcal-usergroups-lt.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = oauth2client.client.flow_from_clientsecrets(
                self._config.get_secret_file(), self.SCOPES)
            flow.user_agent = 'Usergroups.lt Calendar updater'
            if flags:
                credentials = oauth2client.tools.run_flow(flow, store, flags)
            else: # Needed only for compatability with Python 2.6
                credentials = oauth2client.tools.run(flow, store)
            print 'Storing credentials to ' + credential_path
        return credentials

    def run(self):
        """Shows basic usage of the Google Calendar API.

        Creates a Google Calendar API service object and outputs a list of the
        next 10 events on the user's calendar.
        """
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # noqa 'Z' indicates UTC time
        print 'Getting the upcoming 10 events'
        eventsResult = service.events().list(
            calendarId=self._config.get('calendar_id'),
            timeMin=now, maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            print 'No upcoming events found.'
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print start, event['summary']


def main():
    meetup_api = MeetupCom()
    gcal_api = GoogleCalendar()

    groups = meetup_api.get_groups()
    for group in groups:

        print group['name'], group['link']
        if 'next_event' in group:
            event = meetup_api.get_results('{!s}/events/{!s}'.format(
                group['urlname'], group['next_event']['id']))
            print event

    gcal_api.run()


if __name__ == "__main__":
    main()
