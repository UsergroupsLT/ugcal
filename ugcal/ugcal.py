from __future__ import unicode_literals

import argparse
import datetime
import httplib2
import json
import logging
import oauth2client
import os
import requests
import time

from apiclient import discovery
from dateutil import parser
from html2text import html2text

GROUPS = [
    'CodeforVilnius',
    'Data-Science-Vilnius',
    'Docker-Vilnius',
    'functional-vilnius',
    'Lithuania-Bitcoin-Meetup-Group',
    'Technarium',
    'vilnius-backend',
    'Vilnius-Clojure',
    'Vilnius-DevOps-Meetup',
    'Vilnius-Golang',
    'vilnius-hack-and-tell',
    'Vilnius-Hadoop-Meetup',
    'Vilnius-js',
    'Vilnius-MongoDB-User-Group',
    'VilniusML',
    'vilniusphp',
    'vilniuspy',
    'vilniusrb',
    'Wix-com-tech-talks-in-Vilnius',
    ]


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

    DAYS_FORECAST = 30

    """Meetup.com API client."""
    def __init__(self):
        self._config = Config()

    def get_groups(self):
        """Retrieve list of groups."""
        return [self._get_results(name) for name in GROUPS]

    def _get_results(self, endpoint, params={}):
        params['key'] = self._config.get('meetup_api_key')
        url = "http://api.meetup.com/" + endpoint
        request = requests.get(url, params=params)
        logger.info("MeetupCom REQUEST: %s", url)
        data = request.json()
        if 'errors' in data and len(data['errors']):
            logger.error(url, params)
        return data

    def get_events(self, group, limit=10):
        """Return events list of Meetup group."""
        return self._get_results(
            '{!s}/events'.format(group['urlname']), {'page': limit})

    def get_upcomig_meetups(self):
        """Return upcoming meetups map of all groups."""
        groups = self.get_groups()
        result = []
        for group in groups:
            result += self.get_events(group)

        max_date = (datetime.datetime.utcnow() +
                    datetime.timedelta(days=self.DAYS_FORECAST))
        max_time = int(time.mktime(max_date.timetuple())) * 1000

        return filter(lambda meetup: meetup['time'] <= max_time, result)


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
            credentials = oauth2client.tools.run(flow, store)
            print 'Storing credentials to ' + credential_path
        return credentials

    def _get_service(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        return service

    def get_upcomig_events(self, limit=50):
        """Get upcoming calendar events.

        Creates a Google Calendar API service object and outputs a list of the
        next events on the user's calendar.
        """
        service = self._get_service()

        now = datetime.datetime.utcnow()
        today = '{!s}T00:00:00Z'.format(now.date().isoformat())
        result = service.events().list(
            calendarId=self._config.get('calendar_id'),
            timeMin=today, maxResults=limit, singleEvents=True,
            orderBy='startTime').execute()
        return result.get('items', [])

    def insert_event(self, event):
        """Insert new event to calendar."""
        logger.info("Creating event %s %s",
                    event['summary'], event['start']['dateTime'])
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
            'RSVP: {}'.format(meetup.get('link')),
        ]
        if meetup.get('description'):
            parts.append(html2text(meetup.get('description')))

        return "\n\n".join(filter(None, parts))

    @classmethod
    def build_date(cls, meetup, hours_offset=0):
        """Build date from start date on meetup object.

        If hours_offset is provided, it will be added to the date. This could
        be useful calculate event end time.
        """
        date = datetime.datetime.utcfromtimestamp(meetup['time']/1000)
        date += datetime.timedelta(minutes=meetup['utc_offset']/1000/60)
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
    def build_location(cls, meetup):
        """Build event location string."""

        address = meetup['venue']['address_1']
        parts = [address]

        if 'name' in meetup['venue']:
            parts.insert(0, meetup['venue']['name'])

        if meetup['venue']['city'].lower() not in address.lower():
            parts.append(meetup['venue']['city'])

        if 'localized_country_name' in meetup['venue']:
            parts.append(meetup['venue']['localized_country_name'])

        return ', '.join(parts)

    @classmethod
    def build_event(cls, meetup):
        """Build event body from meetup.

        Build Google Calendar event body from Meetup.com meetup. Generate all
        required fields.
        """
        event = {
          'summary': meetup['name'].strip(),
          # 'location': '800 Howard St., San Francisco, CA 94103',
          'description': cls.build_description(meetup),
          'start': {
            'dateTime': cls.build_date(meetup),
            'timeZone': 'Europe/Vilnius',
          },
          'end': {
            'dateTime': cls.build_date(meetup, cls.EVENT_DURATION_HOURS),
            'timeZone': 'Europe/Vilnius',
          }
        }

        return event

    @classmethod
    def find_existing_events(cls, meetups, gcal_events):
        """Find meetups existing on Google Calendar."""

        known_event_dates = {}

        def get_event_start_date(event):
            if event['id'] in known_event_dates:
                return known_event_dates[event['id']]

            date_string = (event['start']['dateTime'] if 'dateTime' in
                           event['start'] else event['start']['date'])

            date = parser.parse(date_string).date()
            known_event_dates[event['id']] = date
            return date

        existing_events = {}
        for meetup in meetups:
            meetup_start = parser.parse(cls.build_date(meetup)).date()
            for event in gcal_events:
                link = meetup['link']
                if 'description' in event and link in event['description']:
                    existing_events[link] = event
                    break

                event_start = get_event_start_date(event)
                if meetup_start == event_start:
                    if meetup['name'] == event['summary']:
                        existing_events[link] = event
                        break

                    if (meetup['name'] ==
                            event['summary'][:len(meetup['name'])] or
                            event['summary'] ==
                            meetup['name'][:len(event['summary'])]):
                        existing_events[link] = event
                        break

        return existing_events

    @classmethod
    def filter_for_creation(cls, meetups, existing_events):
        """Filter events which needs to be created."""
        return {meetup['link']: meetup for meetup in meetups
                if meetup['link'] not in existing_events}

    def syncronize(self, dry_run=False):
        """Syncronize google calendar with meetup.com"""

        if dry_run:
            print '*' * 60
            print 'DRY RUN MODE ENABLED'
            print '*' * 60

        meetups = self.meetup_api.get_upcomig_meetups()
        gcal_events = self.gcal_api.get_upcomig_events()

        # STEP 1: Find events existing on calendar
        existing_events = self.find_existing_events(meetups, gcal_events)
        to_create = self.filter_for_creation(meetups, existing_events)
        if to_create:
            logger.info("Found events to create: %d", len(to_create))
            for url in to_create:
                event = UGCal.build_event(to_create.get(url))
                if not dry_run:
                    self.gcal_api.insert_event(event)
                else:
                    print 'Event to create: {!s} ({!s})'.format(
                        event['summary'], event['start']['dateTime'])
        else:
            logger.info('No events to create')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true',
                        help='Do not create or update records.')
    args = parser.parse_args()

    ugcal = UGCal()
    ugcal.syncronize(args.dry_run)

if __name__ == "__main__":
    main()
