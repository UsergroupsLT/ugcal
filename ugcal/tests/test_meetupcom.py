from __future__ import absolute_import

import pytest
import responses
from mock import patch

from ugcal import MeetupCom
from ugcal.ugcal import CredentialsThrottled


@responses.activate
@patch('time.sleep', return_value=None)
def test_get_results_with_repeated_calls(mock_sleep):

    response = {'errors': [{
        "code": "throttled",
        "message": "Credentials have been throttled"
    }]}

    url = 'http://api.meetup.com/whatever'
    responses.add(responses.GET, url,
                  json=response, status=429)

    with pytest.raises(CredentialsThrottled):
        meetup = MeetupCom({})
        result = meetup._get_results('whatever')

        assert meetup.REQUEST_RETRIES > 0
        assert meetup.REQUEST_RETRIES == len(responses.calls)
        assert result == response
