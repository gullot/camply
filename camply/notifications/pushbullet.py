"""
Push Notifications via Pushbullet
"""

import logging
from abc import ABC
from datetime import datetime
from typing import List

import requests

from camply.config import CampsiteContainerFields, PushbulletConfig
from camply.containers import AvailableCampsite
from camply.notifications.base_notifications import BaseNotifications

logger = logging.getLogger(__name__)


class PushbulletNotifications(BaseNotifications, ABC):
    """
    Push Notifications via PushBullet
    """

    def __init__(self):
        if any([PushbulletConfig.API_TOKEN is None, PushbulletConfig.API_TOKEN == ""]):
            warning_message = (
                "Pushbullet is not configured properly. To send Pushbullet messages "
                "make sure to run `camply configure` or set the "
                "proper environment variable: `PUSHBULLET_API_TOKEN`."
            )
            logger.error(warning_message)
            raise EnvironmentError(warning_message)

    def __repr__(self):
        """
        String Representation
        """
        return "<PushbulletNotifications>"

    @staticmethod
    def send_message(message: str, **kwargs) -> requests.Response:
        """
        Send a message via PushBullet - if environment variables are configured

        Parameters
        ----------
        message: str

        Returns
        -------
        requests.Response
        """
        pushbullet_headers = PushbulletConfig.API_HEADERS.copy()
        pushbullet_headers.update({"Access-Token": PushbulletConfig.API_TOKEN})
        message_type = kwargs.pop("type", "note")
        message_title = kwargs.pop("title", "Camply Notification")
        message_json = dict(
            type=message_type, title=message_title, body=message, **kwargs
        )
        logger.debug(message_json)
        response = requests.post(
            url=PushbulletConfig.PUSHBULLET_API_ENDPOINT,
            headers=pushbullet_headers,
            json=message_json,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as he:
            logger.warning(
                "Notifications weren't able to be sent to Pushbullet. "
                "Your configuration might be incorrect."
            )
            raise ConnectionError(response.text) from he
        return response

    @staticmethod
    def send_campsites(campsites: List[AvailableCampsite], **kwargs):
        """
        Send a message with a campsite object

        Parameters
        ----------
        campsites: AvailableCampsite
        """
        for campsite in campsites:
            fields = list()
            for key, value in campsite.dict().items():
                if key == CampsiteContainerFields.BOOKING_URL:
                    key = "booking_link"
                elif key in [
                    CampsiteContainerFields.BOOKING_DATE,
                    CampsiteContainerFields.BOOKING_END_DATE,
                ]:
                    value: datetime = value.strftime("%Y-%m-%d")
                formatted_key = key.replace("_", " ").title()
                fields.append(f"{formatted_key}: {value}")
            composed_message = "\n".join(fields)
            message_title = (
                f"{campsite.recreation_area} | {campsite.facility_name} | "
                f"{campsite.booking_date.strftime('%Y-%m-%d')}"
            )
            PushbulletNotifications.send_message(
                message=composed_message, title=message_title, type="note"
            )
