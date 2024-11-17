<!--
SPDX-FileCopyrightText: 2024 HarHarLinks <2803622+HarHarLinks@users.noreply.github.com>

SPDX-License-Identifier: MIT
-->

# I Don't Have Spotify Maubot [![Matrix](https://img.shields.io/matrix/maubot-idonthavespotify:matrix.org?logo=matrix&label=chat&server_fqdn=matrix.org&style=for-the-badge)](https://matrix.to/#/#maubot-idonthavespotify:matrix.org)

Find and convert Spotify links shared in [Matrix](https://matrix.org) chat rooms automatically to your preferred streaming service using [idonthavespotify](https://github.com/sjdonado/idonthavespotify) using this [Maubot](https://mau.bot) plugin.

## Installation

See <https://docs.mau.fi/maubot/usage/basic.html>.

The plugin supports one configuration option: `API`.
This URL will be called to resolve the Spotify link to other streaming services.
For maximum privacy, you can self-host idonthavespotify.

This version of maubot-idonthavespotify is tested to be compatible with idonthavespotify [v1.4.1](https://github.com/sjdonado/idonthavespotify/releases).

## Development

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

See also <https://docs.mau.fi/maubot/dev/getting-started.html>.
