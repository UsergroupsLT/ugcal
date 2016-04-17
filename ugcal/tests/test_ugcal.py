from __future__ import absolute_import

import pytest
from ugcal import UGCal


@pytest.fixture
def php_meetup():
    return {
        'status': 'upcoming',
        'updated': 1457875805000,
        'group': {
            'who': 'PHPers',
            'name': 'Vilnius PHP Meetups',
            'join_mode': 'open',
            'created': 1416565027000,
            'lon': 25.270000457763672,
            'lat': 54.70000076293945,
            'urlname': 'vilniusphp',
            'id': 18204759
        },
        'name': 'VilniusPHP 0x29',
        'created': 1418629034000,
        'venue': {
            'city': 'Vilnius',
            'name': '\u0160MTP',
            'repinned': False,
            'lon': 25.294130325317383,
            'localized_country_name': 'Lithuania',
            'address_1': 'J. Galvyd\u017eio g. 5, Vilnius',
            'country': 'lt',
            'lat': 54.710880279541016,
            'id': 23491895
        },
        'utc_offset': 10800000,
        'visibility': 'public',
        'yes_rsvp_count': 5,
        'link': 'http://www.meetup.com/vilniusphp/events/228864161/',
        'time': 1460043000000,
        'duration': 9000000,
        'waitlist_count': 0,
        'id': 'gnbddlyvgbkb',
        'description': u"<p>Speakers: TBA</p> <p>Do you have what to share with community? Feel free to contact us and we'll register you as a speaker!</p> "  # noqa
    }


@pytest.fixture
def js_meetup():
    return {
        'status': 'upcoming',
        'updated': 1457875805000,
        'name': 'Vilnius JS',
        'created': 1418629034000,
        'utc_offset': 10800000,
        'visibility': 'public',
        'yes_rsvp_count': 5,
        'link': 'http://www.meetup.com/js_meetup/events/654321/',
        'time': 1460043000000,
        'duration': 9000000,
        'waitlist_count': 0,
        'id': 'gnbddlyvgbkb',
        'description': u"<p>Speakers: TBA</p> <p>Do you have what to share with community? Feel free to contact us and we'll register you as a speaker!</p> "  # noqa
    }


@pytest.fixture
def php_event():
    return {
        'created': '2015-07-29T19:21:09.000Z',
        'creator': {
             'displayName': 'Povilas Balzaravi\u010dius',
             'email': 'pavvka@gmail.com'
        },
        'description': 'Daugiau informacijos: http://www.vilniusphp.lt/\n\nRSVP: http://www.meetup.com/vilniusphp/events/228864161/',  # noqa
        'end': {
            'dateTime': '2016-04-07T21:00:00+03:00'
        },
        'etag': '"2915751232820000"',
        'hangoutLink':
        'https://plus.google.com/hangouts/_/calendar/bGhjdWE1cHFkcmhrYmg2amU4NTFjM21lZmdAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ.d425a6jmpbqunk8qadussb19bg',  # noqa
        'htmlLink': 'https://www.google.com/calendar/event?eid=ZDQyNWE2am1wYnF1bms4cWFkdXNzYjE5YmdfMjAxNjA0MDdUMTYwMDAwWiBsaGN1YTVwcWRyaGtiaDZqZTg1MWMzbWVmZ0Bn',  # noqa
        'iCalUID': 'd425a6jmpbqunk8qadussb19bg@google.com',
        'id': 'd425a6jmpbqunk8qadussb19bg_20160407T160000Z',
        'kind': 'calendar#event',
        'organizer': {
            'displayName': 'LTU Meetups - usergroups.lt',
            'email': 'lhcua5pqdrhkbh6je851c3mefg@group.calendar.google.com',
            'self': True
        },
        'originalStartTime': {
            'dateTime': '2016-04-07T19:00:00+03:00'
        },
        'recurringEventId': 'd425a6jmpbqunk8qadussb19bg',
        'reminders': {
            'useDefault': True
        },
        'sequence': 1,
        'start': {
            'dateTime': '2016-04-07T19:00:00+03:00'
        },
        'status': 'confirmed',
        'summary': 'Vilnius PHP',
        'updated': '2016-03-13T13:26:56.410Z'
    }


def test_existing_events_by_links(php_meetup, js_meetup):
    php_meetup['name'] = 'Vilnius PHP 123'
    php_meetup['link'] = 'http://www.meetup.com/php_meetup/events/123456/'

    php_event = {
        'id': 'qwerty',
        'summary': 'Some event',
        'start': {
            'dateTime': '2016-03-30 22:00'
        },
        'description': 'lorem ipsum http://www.meetup.com/php_meetup/events/123456/ somehting else.'  # noqa
    }
    ruby_event = {
        'id': 'azerty',
        'summary': 'Ruby',
        'start': {
            'dateTime': '2016-03-31 22:00'
        },
        'description': ''
    }

    meetups = [php_meetup, js_meetup]
    gcal_events = [php_event, ruby_event]

    result = UGCal.find_existing_events(meetups, gcal_events)
    assert {
        'http://www.meetup.com/php_meetup/events/123456/': php_event
    } == result


def test_existing_events_by_names(php_meetup, js_meetup, php_event):
    php_meetup['name'] = 'Vilnius PHP 123'

    other_php_event = {
        'id': 'qwerty',
        'summary': 'Moo Vilnius PHP Woo',
        'start': {
            'dateTime': '2016-04-07T19:00:00+03:00'
        }
    }
    ruby_event = {
        'id': 'azerty',
        'summary': 'Ruby',
        'start': {
            'dateTime': '2016-03-31 22:00'
        },
        'description': ''
    }

    meetups = [php_meetup, js_meetup]
    gcal_events = [other_php_event, php_event, ruby_event]

    result = UGCal.find_existing_events(meetups, gcal_events)
    assert 1 == len(result)
    assert php_meetup['link'] in result
    assert php_event == result[php_meetup['link']]


def test_existing_events_by_name_begining(php_meetup, php_event):
    php_event['summary'] = php_meetup['name'][:10]
    php_event['description'] = ''

    result = UGCal.find_existing_events([php_meetup], [php_event])
    assert 1 == len(result)
    assert php_meetup['link'] in result
    assert php_event == result[php_meetup['link']]


def test_filter_events_to_create():
    old_php_meetup = {
        'link': 'http://www.meetup.com/php_meetup/events/123456/'
    }
    new_php_meetup = {
        'link': 'http://www.meetup.com/php_meetup/events/987654/'
    }

    meetups = [old_php_meetup, new_php_meetup]
    existing = {
        'http://www.meetup.com/php_meetup/events/123456/': old_php_meetup
    }

    result = UGCal.filter_for_creation(meetups, existing)
    assert {
        'http://www.meetup.com/php_meetup/events/987654/': new_php_meetup
    } == result


def test_build_description(php_meetup):
    expect = """RSVP: http://www.meetup.com/vilniusphp/events/228864161/

Speakers: TBA

Do you have what to share with community? Feel free to contact us and we'll
register you as a speaker!

"""
    result = UGCal.build_description(php_meetup)
    assert expect == result


def test_build_date(php_meetup):
    start = UGCal.build_date(php_meetup)
    assert "2016-04-07T18:30:00+03:00" == start


def test_build_date_with_no_utc_offset(php_meetup):
    php_meetup['utc_offset'] = 0
    start = UGCal.build_date(php_meetup)
    assert "2016-04-07T15:30:00+00:00" == start


def test_build_date_with_negative_utc_offset(php_meetup):
    php_meetup['utc_offset'] = -7200000
    start = UGCal.build_date(php_meetup)
    assert "2016-04-07T13:30:00-02:00" == start


def test_build_date_with_positive_hours_offset(php_meetup):
    start = UGCal.build_date(php_meetup, 2)
    assert "2016-04-07T20:30:00+03:00" == start


def test_build_date_with_negative_hours_offset(php_meetup):
    start = UGCal.build_date(php_meetup, -2)
    assert "2016-04-07T16:30:00+03:00" == start


def test_build_event(php_meetup):
    event = UGCal.build_event(php_meetup)

    expected_description = """RSVP: http://www.meetup.com/vilniusphp/events/228864161/

Speakers: TBA

Do you have what to share with community? Feel free to contact us and we'll
register you as a speaker!

"""

    assert {
        'summary': 'VilniusPHP 0x29',
        'description': expected_description,
        'start': {
            'dateTime': '2016-04-07T18:30:00+03:00',
            'timeZone': 'Europe/Vilnius',
        },
        'end': {
            'dateTime': '2016-04-07T20:30:00+03:00',
            'timeZone': 'Europe/Vilnius',
        },
    } == event


def test_build_event_trimming(php_meetup):
    php_meetup['name'] = '  VilniusPHP 0x29   '
    event = UGCal.build_event(php_meetup)

    assert 'VilniusPHP 0x29' == event['summary']


def test_build_location_with_country(php_meetup):
    location = UGCal.build_location(php_meetup)
    assert '\u0160MTP, J. Galvyd\u017eio g. 5, Vilnius, Lithuania' == location


def test_build_location_plain(php_meetup):
    php_meetup['venue'].pop('localized_country_name')
    php_meetup['venue'].pop('name')
    php_meetup['venue']['address_1'] = 'J. Galvyd\u017eio g. 5'
    location = UGCal.build_location(php_meetup)
    assert 'J. Galvyd\u017eio g. 5, Vilnius' == location


def test_build_location_with_city(php_meetup):
    php_meetup['venue'].pop('localized_country_name')
    php_meetup['venue'].pop('name')
    location = UGCal.build_location(php_meetup)
    assert 'J. Galvyd\u017eio g. 5, Vilnius' == location


def test_build_location_with_city_and_different_case(php_meetup):
    php_meetup['venue'].pop('localized_country_name')
    php_meetup['venue'].pop('name')
    php_meetup['venue']['city'] = 'vilnius'
    location = UGCal.build_location(php_meetup)
    assert 'J. Galvyd\u017eio g. 5, Vilnius' == location


def test_build_location_with_no_name(php_meetup):
    php_meetup['venue'].pop('name')
    location = UGCal.build_location(php_meetup)
    assert 'J. Galvyd\u017eio g. 5, Vilnius, Lithuania' == location
