# SPDX-FileCopyrightText: 2024 HarHarLinks <2803622+HarHarLinks@users.noreply.github.com>
#
# SPDX-License-Identifier: MIT

import re
from typing import Dict, Type

import aiohttp
from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.types import MessageType, EventType
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

SPOTIFY_PATTERN = r"https?://(?:open|play)\.spotify\.com/(?:track|album|playlist)/([A-Za-z0-9]+)"


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("API")


def format_message(api_response: Dict) -> str:
    """
    example API response:

    {
      "id" : "b3Blbi5zcG90aWZ5LmNvbS9hbGJ1bS83M29JSzRISEJWYU40V05FOGYzSmVhP3NpPVZ5Rzd0cVRoUllhTEt1bnhRX1N0cWc%3D",
      "type" : "album",
      "title" : "Feathergun",
      "description" : "Rishloo · Album · 2009 · 11 songs",
      "image" : "https://i.scdn.co/image/ab67616d0000b2733c64c336ac47c4fb8a4a6e41",
      "source" : "https://open.spotify.com/album/73oIK4HHBVaN4WNE8f3Jea?si=VyG7tqThRYaLKunxQ_Stqg",
      "universalLink" : "https://bit.donado.co/ih46A",
      "links" : [ {
        "type" : "youTube",
        "url" : "https://music.youtube.com/browse/MPREb_RwfcqHJcPLw",
        "isVerified" : true
      }, {
        "type" : "appleMusic",
        "url" : "https://music.apple.com/ca/album/feathergun/348336795",
        "isVerified" : true
      }, {
        "type" : "soundCloud",
        "url" : "https://soundcloud.com/rishloo/sets/feathergun",
        "isVerified" : true
      }, {
        "type" : "tidal",
        "url" : "https://listen.tidal.com/search?q=Feathergun+Rishloo"
      } ]
    }
    """
    formatted_message = f"{api_response.get('title', 'unknown title')} by {api_response.get('description', 'unknown description')}"
    if api_response.get("universalLink") is not None:
        formatted_message = f"[{formatted_message}]({api_response['universalLink']})"
    if api_response.get("image") is not None:
        # include hidden link to image which will cause a link preview in some clients that loads the image
        formatted_message += f"[]({api_response['image']})"
    formatted_message += "\n"
    for link in api_response.get("links", []):
        if link.get("url") is not None:
            formatted_message += f"- {'✅' if link.get('isVerified', False) else '❓'} [{link.get('type', 'unknown')}]({link['url']})\n"

    return formatted_message


class IDontHaveSpotifyPlugin(Plugin):
    async def start(self) -> None:
        self.config.load_and_update()

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, evt: MessageEvent) -> None:
        self.log.debug(f"received event {evt}")
        if evt.content.msgtype == MessageType.TEXT:
            message = evt.content.body
            self.log.debug(f"message is {message}")
            match = re.search(SPOTIFY_PATTERN, message)

            if match:
                spotify_url = match.group(0)
                self.log.info(f"extracted spotify url {spotify_url}")
                not_spotify = await self.transform_link(spotify_url)
                self.log.debug(f"api returned {not_spotify}")
                formatted_message = format_message(not_spotify)
                self.log.debug(f"sending response {formatted_message}")

                if not_spotify:
                    await evt.reply(formatted_message)
                else:
                    await evt.reply("Sorry, I couldn't process the Spotify link.")

    async def transform_link(self, spotify_url) -> Dict:
        api_url = self.config["API"]
        data = {"link": spotify_url, "adapters[]": ["spotify"]}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, data=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Error: Unable to process the request (Status code: {response.status})")
                        return None
        except Exception as e:
            self.log.warning(f"Error making API request: {e}")
            return None
