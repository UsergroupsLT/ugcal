from __future__ import unicode_literals

import datetime
import httplib2
import json
import logging
import oauth2client
import os
import requests

from apiclient import discovery
from html2text import html2text

GROUPS = [
    'Technarium',
    'Vilnius-DevOps-Meetup',
    'Vilnius-Hadoop-Meetup',
    'Vilnius-js',
    'functional-vilnius',
    'vilnius-hack-and-tell',
    'vilniusphp',
    'vilniuspy',
    'vilniusrb',
    ]


try:
    import argparse
    flags = argparse.ArgumentParser(
        parents=[oauth2client.tools.argparser]).parse_args()
except ImportError:
    flags = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class Config:

    CLIENT_SECRET_FILE = 'client_secret.json'

    def __init__(self):
        config_file = file('config.json', 'r')
        self._config = json.loads(config_file.read())

    def get(self, key):
        """Retrieve custom value from config."""
        return self._config[key]

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

    SCOPES = 'https://www.googleapis.com/auth/calendar'

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

    def get_upcomig_events(self, limit=20):
        """Get upcoming calendar events.

        Creates a Google Calendar API service object and outputs a list of the
        next events on the user's calendar.
        """
        service = self._get_service()

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # noqa 'Z' indicates UTC time
        result = service.events().list(
            calendarId=self._config.get('calendar_id'),
            timeMin=now, maxResults=limit, singleEvents=True,
            orderBy='startTime').execute()
        return result.get('items', [])

    def insert_event(self, event):
        """Insert new event to calendar."""
        service = self._get_service()
        service.events().insert(
            calendarId=self._config.get('calendar_id'),
            body=event
        ).execute()


class UGCal(object):

    EVENT_DURATION_HOURS = 2

    def __init__(self):
        self.meetup_api = MeetupCom()
        self.gcal_api = GoogleCalendar()

    @classmethod
    def build_description(cls, meetup):
        """Build event description from meetup."""
        parts = [
            'RSVP: {}'.format(meetup['link']),
            html2text(meetup['description']),
        ]

        return "\n\n".join(parts)

    @classmethod
    def build_location(cls):
        """Build event location from meetup venue."""
        raise NotImplementedError

    @classmethod
    def build_date(cls, meetup, hours_offset=0):
        """Build date from start date on meetup object.

        If hours_offset is provided, it will be added to the date. This could
        be useful calculate event end time.
        """
        date = datetime.datetime.utcfromtimestamp(meetup['time']/1000)
        if hours_offset:
            date += datetime.timedelta(hours=hours_offset)

        date_string = date.strftime('%Y-%m-%dT%H:%M:%S')
        utc_offset = ('{!s}{!s}'.format(
                      ('-' if meetup['utc_offset'] < 0 else '+'),
                      datetime.datetime
                      .utcfromtimestamp(abs(meetup['utc_offset'])/1000)
                      .strftime('%H:%M')))

        return '{}{}'.format(date_string, utc_offset)

    @classmethod
    def build_event(cls, meetup):
        """Build event body from meetup.

        Build Google Calendar event body from Meetup.com meetup. Generate all
        required fields.
        """
        event = {
          'summary': meetup['name'],
          # 'location': '800 Howard St., San Francisco, CA 94103',
          'description': cls.build_description(meetup),
          'start': {
            'dateTime': cls.build_date(meetup),
            'timeZone': 'Europe/Vilnius',
          },
          'end': {
            'dateTime': cls.build_date(meetup, cls.EVENT_DURATION_HOURS),
            'timeZone': 'Europe/Vilnius',
          },
        }

        return event

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

                if meetup['name'] == event['summary']:
                    existing_events[link] = event
                    break

        return existing_events

    @classmethod
    def filter_for_creation(cls, meetups, existing_events):
        """Filter events which needs to be created."""
        return {meetup['link']: meetup for meetup in meetups
                if meetup['link'] not in existing_events}


def main():

    meetup_api = MeetupCom()
    meetups = meetup_api.get_upcomig_events()

    gcal_api = GoogleCalendar()
    gcal_events = gcal_api.get_upcomig_events()

    # STEP 1: Find events existing on calendar
    existing_events = UGCal.find_existing_events(meetups, gcal_events)
    to_create = UGCal.filter_for_creation(meetups, existing_events)  # noqa
    if to_create:
        logger.info("Found events to create: %d", len(to_create))
        for url in to_create:
            event = UGCal.build_event(to_create.get(url))
            logger.info("Creating event %s %s",
                        event['summary'], event['start']['dateTime'])
            gcal_api.insert_event(event)


if __name__ == "__main__":
    main()
