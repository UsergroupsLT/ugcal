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

    def get_upcomig_events(self):
        """Return upcoming events map of all groups.

        Result: {url: event}
        """
        groups = self.get_groups()
        result = []
        for group in groups:
            if 'next_event' in group:
                event = self.get_results('{!s}/events/{!s}'.format(
                    group['urlname'], group['next_event']['id']))
                result.append(event)

        return result


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
            else:  # Needed only for compatability with Python 2.6
                credentials = oauth2client.tools.run(flow, store)
            print 'Storing credentials to ' + credential_path
        return credentials

    def _get_service(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        return service

    def get_upcomig_events(self):
        """Shows basic usage of the Google Calendar API.

        Creates a Google Calendar API service object and outputs a list of the
        next 10 events on the user's calendar.
        """
        service = self._get_service()

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # noqa 'Z' indicates UTC time
        result = service.events().list(
            calendarId=self._config.get('calendar_id'),
            timeMin=now, maxResults=20, singleEvents=True,
            orderBy='startTime').execute()
        return result.get('items', [])


class UGCal(object):

    def __init__(self):
        self.meetup_api = MeetupCom()
        self.gcal_api = GoogleCalendar()

    def _build_description(self):
        pass

    @classmethod
    def find_existing_events(cls, meetups, gcal_events):
        """Find meetups existing on Google Calendar."""
        existing_events = {}
        for meetup in meetups:
            for event in gcal_events:
                link = meetup['link']
                if 'description' in event and link in event['description']:
                    existing_events[link] = event
                    break

        return existing_events


def main():

    meetup_api = MeetupCom()
    meetups = meetup_api.get_upcomig_events()
    meetups_map = {meetup['link']: meetup for meetup in meetups}

    gcal_api = GoogleCalendar()
    gcal_events = gcal_api.get_upcomig_events()

    # STEP 1: Find events existing on calendar
    existing_events = {}
    events_by_name = {}
    for meetup in meetups:
        for event in gcal_events:
            link = meetup['link']
            if 'description' in event and link in event['description']:
                existing_events[link] = event
                break
            #
            # if 'summary' in event and meetup['name'] == event['summary']:
            #     events_by_name[link] = event

    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    main()
