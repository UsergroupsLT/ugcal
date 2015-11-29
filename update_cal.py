from __future__ import unicode_literals

import json
import requests

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


class Config:

    CLIENT_SECRET_FILE = 'client_secret.json'

    def __init__(self):
        config_file = file(self.CLIENT_SECRET_FILE, 'r')
        self._config = json.loads(config_file.read())

    def get(self, key):
        """Retrieve custom value from config."""
        return self._config['other'][key]


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
        # print url
        request = requests.get(url, params=params)
        data = request.json()
        return data


def main():
    meetup_api = MeetupCom()
    groups = meetup_api.get_groups()

    for group in groups:
        print group['name'], group['link']
        if 'next_event' in group:
            event = meetup_api.get_results('{!s}/events/{!s}'.format(
                group['urlname'], group['next_event']['id']))
            print event


if __name__ == "__main__":
    main()
