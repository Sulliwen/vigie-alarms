# Vigie — an alarm before every appointment

*[Version française](README.md)*

Vigie builds on [Calendar Alarm](https://github.com/Sulliwen/calendar-alarm),
which remains available on its own, and will add Slack alerts to it.

A small Windows program that runs in the background and rings **10 minutes
before every appointment** of your calendars (Infomaniak, Google, Outlook,
iCloud…), whether or not the appointment carries a reminder and whoever created
it. A window comes to the front with the title of the appointment and two
buttons: **Stop** and **Snooze 5 min**.

Calendars are read again every minute: an appointment added at the last minute
rings as soon as it is found.

## Installation

1. Run `Vigie-Setup-<version>.exe` (no administrator rights needed).
   The file is not signed, so Windows shows a SmartScreen warning: “More
   info” → “Run anyway”.
2. When the installation ends, the **“Synced calendars”** window opens.
   Pick your provider in the drop-down list, click “Add…” and follow the
   instructions shown. Repeat for every calendar to watch.

The program registers itself to start with Windows. A **click** on the icon in
the notification area opens the **Dashboard**: the state of every calendar and
messaging tool (green, red or grey dot), the next appointment alert, and the
latest alerts since Vigie started (time, source, message, what was done: sound,
alarm, VIP announcement, read in time, ignored outside hours…). Its header
leads to the other screens: the **Agenda** (every appointment of the next
7 days, grouped by day), the synced calendars, the settings and the log; at the
bottom, “Sync now”. A right-click on the icon also gives these screens, plus
“Test the alarm” and “Quit”. The program exists in French and
in English.

## Supported calendars

| Provider | What to enter |
| --- | --- |
| Infomaniak (kSuite, Kalendar) | Synchronisation username and application password, shown on <https://config.infomaniak.com> (“My Contacts & Calendars” → “Manual synchronisation”) |
| Google Calendar | The secret address of the calendar: Settings → your calendar → “Integrate calendar” → “Secret address in iCal format” |
| Outlook / Microsoft 365 | The ICS link of the published calendar: Outlook on the web → Settings → Calendar → Shared calendars → “Publish a calendar” |
| Apple iCloud | Apple Account address and app-specific password (account.apple.com) |
| Yahoo, Fastmail | Account address and app password |
| Nextcloud | Server address followed by `/remote.php/dav`, user name and app password |
| Other CalDAV server | CalDAV address, username and password |
| Other iCal address (.ics) | An `https://` address returning a calendar in iCal format |

For a CalDAV account (Infomaniak, iCloud, Yahoo, Fastmail, Nextcloud), the
program then asks which calendars of the account to watch: yours is proposed by
default, the shared calendars of colleagues and rooms are not. Google and
Outlook need one address per calendar.

A secret address gives read access to the whole calendar: it is stored like a
password, do not share it.

An appointment present in two calendars (an invitation received on both) rings
only once.

## Slack alerts

Vigie can also watch Slack. Each **trigger** has its action: “Nothing”,
“Sound”, “Alarm if unread” or “Sound + alarm if unread”:

| Trigger | Default |
| --- | --- |
| Direct message | Sound + alarm if unread |
| @me mention (channel, group or thread) | Sound + alarm if unread |
| Reply to one of your messages, in a thread | Nothing |
| Any message of a group conversation | Nothing |
| `@here`, `@channel` | Nothing |
| Keywords (whole words, regardless of case) | Nothing |
| Watched channels: every message | Nothing |

When a message matches several triggers, the strongest action applies. Your own
messages, edits and bots never trigger anything.

- **Sound**: a short sound when the message arrives.
- **Alarm if unread**: if a message is still unread 5 minutes after the first
  one of a series, **a single alarm** lists the unread messages, with “Open
  Slack”. It has its own sound and closes by itself as soon as they are read.
- **When**: silent during Slack's “Do not disturb” (can be turned off), and if
  you wish only between two hours and only Monday to Friday.

**VIP people** (Settings → Messaging → VIP people, shared by Slack and Zoom;
unticked, no VIP treatment at all): all their messages are announced, wherever you are a member, even without
a tag. A sound, then a voice says the chosen phrase (“VIP message” by default).
They never trigger an alarm, and a series of messages is announced once a
minute. Names are compared regardless of case and word order (“Jakez Rolland”
also matches “Rolland Jakez”).

Setting up, once: on <https://api.slack.com/apps>, “Create New App” → “From a
manifest”, choose the workspace and paste:

```yaml
display_information:
  name: Vigie
  description: Alerte locale pour mes messages privés et mes mentions
oauth_config:
  scopes:
    user: [channels:history, groups:history, im:history, mpim:history,
           channels:read, groups:read, im:read, mpim:read,
           users:read, dnd:read]
settings:
  event_subscriptions:
    user_events: [message.channels, message.groups, message.im, message.mpim]
  socket_mode_enabled: true
  token_rotation_enabled: false
```

Then “Basic Information” → “App-Level Tokens” → generate a token with the
`connections:write` permission, and “Install App” → “Install to Workspace”. In
Vigie: Settings → Messaging → Slack → “Slack tokens…”, paste both tokens (`xapp-…` and
`xoxp-…`).

## Zoom alerts

Vigie can also watch Zoom Team Chat, with a **sound** per trigger:

| Trigger | Default |
| --- | --- |
| Direct messages from the listed contacts (email addresses) | Sound |
| @me mention | Sound |
| Reply to one of your messages | Nothing |
| `@all` | Nothing |
| Keywords (whole words, case ignored) | Nothing |
| Watched channels (their names, or `*` for all): every message | Nothing |

Differences with Slack:

- **No alarm if unread**: Zoom's API does not tell whether a message was read.
- **About 30 seconds of delay**: Zoom pushes nothing to a desktop program, and
  its "recent conversations" list stays empty on some accounts. Vigie reads each
  of your channels every 30 seconds instead, at least one second apart to stay
  within Zoom's limit. Direct messages are read for the listed contacts only.
- **VIP people**: the same list as for Slack; their Zoom messages are announced
  the same way (a sound, then the voice).
- **Hours** and alert days of its own.

Setting up, once: on <https://marketplace.zoom.us>, “Develop” → “Build App” →
“General App”:

1. “Basic Information”: **User-managed**, turn **Use Public Client OAuth** on,
   put `http://127.0.0.1:8765/callback` as “OAuth Redirect URL” and in the
   “OAuth Allow List”.
2. “Scopes”, read-only: `team_chat:read:list_user_channels`,
   `team_chat:read:list_user_messages`, `team_chat:read:user_message` and
   `user:read:user`.

In Vigie: Settings → Messaging → Zoom → “Connect Zoom…”, paste the **Public Client ID**,
then authorize the app in the browser. The token is kept in the Windows
Credential Manager and renewed on its own.

## Behaviour

- The alarm loops until you click. Closing the window with the cross means
  “Snooze”, not “Stop”.
- An appointment found less than 10 minutes ahead, or started less than
  5 minutes ago (waking from sleep), rings immediately.
- These do not ring: all-day events (shown in the Agenda), cancelled
  appointments and declined invitations.
- Green icon: every account is syncing. Red icon and a notification: an account
  has had no successful sync for 5 minutes, its alarms can no longer be
  trusted.
- Passwords and iCal addresses are stored in the Windows Credential Manager.
  If a server refuses one, the program asks for it again.

Uninstalling: “Installed apps” in Windows. It also removes the settings and the
saved passwords.

Limits: Windows only; the PC must be on, with the session open. For calendars
read through an iCal address (Google, Outlook), how quickly a new appointment
shows up depends on the provider.

## Settings

Right-click on the icon → “Settings…”:

- **General**: language, starting with Windows.
- **Agenda** (appointments only):
  - alert type: **alarm** (a window and a looping sound) or **ring** (one sound
    and a Windows notification, no window);
  - triggers: delay before the appointment, a second alert when it starts, how
    late an appointment found late may still alert, “Free” appointments and
    unanswered invitations to ignore;
  - sound: alarm sound (those of Windows or a `.wav` file), length of a snooze,
    automatic silence (the window stays);
  - display and sync: days shown, all-day events, how often calendars are read
    again.
- **Messaging**: a list on the left (a green, red or grey dot tells whether the
  tool is connected, failing or off), the settings of the chosen tool on the
  right:
  - **Slack**: connection, triggers, sound and alarm, hours (see
    [Slack alerts](#slack-alerts));
  - **Zoom**: connection, triggers, sound, hours (see [Zoom alerts](#zoom-alerts));
  - **VIP people**, shared by every messaging tool.

Settings are saved in `%LOCALAPPDATA%\vigie\config.json`. `my_emails`
(addresses used to recognise your invitations) can only be changed in that
file. The log is in the same folder
(`vigie.log`).

## From the sources

Python 3.12 or later, installed on Windows.

During development, `dev.ps1` runs Vigie straight from the sources, with no build
and no installation; it restarts by itself whenever `vigie.py` or `texts.py`
change.

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1        # run from the sources, automatic restart
powershell -ExecutionPolicy Bypass -File install.ps1    # venv, dependencies, launch
.venv\Scripts\python.exe -m unittest                    # tests
powershell -ExecutionPolicy Bypass -File build.ps1      # builds the installer in dist\ (requires Inno Setup 6)
powershell -ExecutionPolicy Bypass -File uninstall.ps1  # stops the program and removes it from startup
```

Every displayed text lives in `texts.py`, in French and in English.
