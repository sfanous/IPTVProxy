import logging.handlers
import warnings
from datetime import datetime

import pytz
from cerberus import Validator

from .configuration import IPTVProxyConfiguration

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class IPTVProxyCerberusValidator(Validator):
    def _validate_is_channel_number_valid(self, other, field, value):
        if other not in self.document:
            return False

        try:
            provider = IPTVProxyConfiguration.get_provider(self.document[other].lower())

            if not provider['epg'].is_channel_number_in_epg(value):
                self._error(field, 'must be between {0:02} and {1:02}'.format(
                    *provider['epg'].get_channel_numbers_range()))
        except KeyError:
            return False

    def _validate_is_end_date_time_after_start_date_time(self, other, field, value):
        if other not in self.document:
            return False

        end_date_time_in_utc = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
        start_date_time_in_utc = datetime.strptime(self.document[other], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
        if end_date_time_in_utc <= start_date_time_in_utc:
            self._error(field, 'must be later than start_date_time_in_utc')

    def _validate_is_end_date_time_in_the_future(self, is_end_date_time_in_the_future, field, value):
        end_date_time_in_utc = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
        if is_end_date_time_in_the_future and datetime.now(pytz.utc) > end_date_time_in_utc:
            self._error(field, 'must be later than now')

    def _validate_is_provider_valid(self, is_provider_valid, field, value):
        if is_provider_valid:
            try:
                IPTVProxyConfiguration.get_provider(value.lower())
            except KeyError:
                self._error(field, 'must be a valid provider')

    # noinspection PyMethodMayBeStatic
    def _validate_type_datetime_string(self, value):
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

            return True
        except (TypeError, ValueError):
            return False
