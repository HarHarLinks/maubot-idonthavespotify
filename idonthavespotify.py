# SPDX-FileCopyrightText: 2024 HarHarLinks <2803622+HarHarLinks@users.noreply.github.com>
#
# SPDX-License-Identifier: MIT

import re
from typing import Dict, Type, Union

import aiohttp
from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.types import MessageType, EventType
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

# https://open.spotify.com/album/6D2bGAKmIYtMQtL14c4vAb
# https://open.spotify.com/intl-de/album/6D2bGAKmIYtMQtL14c4vAb
# https://open.spotify.com/artist/3eCpCUtYdBCM1twAb4mk8I
# https://open.spotify.com/track/1FwhTB4R0lOWII5tc6cl9P
SPOTIFY_PATTERN = r"https?://(?:open|play)\.spotify\.com/(?:intl-[a-z]{2}/)?(?:track|album|artist|playlist)/([A-Za-z0-9]+)"
# https://geo.music.apple.com/de/album/the-matrix-the-complete-score/1574417068?app=music&ls=1
# https://music.apple.com/de/album/the-matrix-the-complete-score/1574417068
# https://music.apple.com/de/artist/don-davis/875136
# https://music.apple.com/de/song/logos-the-matrix-main-title/1574417069
APPLE_PATTERN = r"https?://(?:geo\.)?music\.apple\.com/(?:[a-z]{2})/(?:song|album|artist)/([A-Za-z0-9-]+)/([0-9]+)"
# https://www.deezer.com/de/album/243158702
# https://www.deezer.com/de/artist/1530
DEEZER_PATTERN = r"https?://www.deezer.com/(?:[a-z]{2}/)(?:album|artist)/([0-9]+)"
# https://soundcloud.com/don-davis-official/sets/the-matrix-the-complete-score
# https://soundcloud.com/don-davis-official
# https://soundcloud.com/don-davis-official/logos-the-matrix-main-title?in=don-davis-official/sets/the-matrix-the-complete-score
SOUNDCLOUD_PATTERN = r"https?://soundcloud\.com/(?:(?:[A-Za-z0-9-]+)/(?:sets/)?)?([A-Za-z0-9-]+)"
# https://tidal.com/browse/album/190433454
# https://tidal.com/browse/artist/3569622
# https://tidal.com/browse/track/190433467
TIDAL_PATTERN = r"https?://tidal.com/browse/(?:track|album|artist)/([0-9]+)"
# https://music.youtube.com/playlist?list=OLAK5uy_llz2tuxTrSyEzBo0KrNsYUucJM38Gy40w
# https://music.youtube.com/watch?v=dzEtP6fpbOo&list=OLAK5uy_llz2tuxTrSyEzBo0KrNsYUucJM38Gy40w
# https://www.youtube.com/watch?v=qLY1f_sy1aU&list=OLAK5uy_mXG-qOUammaM8mfq60ZO8Kan1xvfSwUBM
# https://youtube.com/watch?v=qLY1f_sy1aU&list=OLAK5uy_mXG-qOUammaM8mfq60ZO8Kan1xvfSwUBM
# https://youtu.be/qLY1f_sy1aU?si=ZSxexr5C4jzTc14x
# https://music.youtube.com/channel/UCpw8T1E5f_ZiQjZCJ0rMdyg
# https://music.youtube.com/playlist?list=OLAK5uy_llz2tuxTrSyEzBo0KrNsYUucJM38Gy40w
YOUTUBE_PATTERN = r"https?://(?:(?:(?:music|www)\.)?youtube\.com|youtu\.be)/.+"

PATTERNS = {
    "spotify": SPOTIFY_PATTERN,
    "apple": APPLE_PATTERN,
    "deezer": DEEZER_PATTERN,
    "soundcloud": SOUNDCLOUD_PATTERN,
    "tidal": TIDAL_PATTERN,
    "youtube": YOUTUBE_PATTERN
}


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("API")
        helper.copy("services")


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

            match = None
            for service in self.config["services"]:
                self.log.debug(f"checking {service} match")
                pattern = PATTERNS.get(service)
                if pattern is None:
                    continue
                match = re.search(pattern, message)
                if match is not None:
                    break

            if match:
                spotify_url = match.group(0)
                self.log.info(f"extracted url {spotify_url}")
                not_spotify = await self.transform_link(spotify_url)
                self.log.debug(f"api returned {not_spotify}")
                formatted_message = format_message(not_spotify)
                self.log.debug(f"sending response {formatted_message}")

                if not_spotify:
                    await evt.reply(formatted_message)
                else:
                    await evt.reply("Sorry, I couldn't process the Spotify link.")

    async def transform_link(self, spotify_url) -> Union[Dict, None]:
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
