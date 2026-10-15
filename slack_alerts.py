"""Slack side of Vigie: tells the program when a message concerns the user, and whether it has been read.

A message concerns the user when it is a direct message, or when it tags them personally (`<@id>`), in
a channel, a group conversation or a thread. Nothing else does: untagged messages, @here, @channel,
user-group mentions and the user's own messages stay silent.

Messages arrive in real time through Socket Mode, so no public server is needed. Whether a message has
been read comes from the conversation's last_read position.
"""

import logging
import threading
import time
from dataclasses import dataclass

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError  # noqa: F401 (also used by vigie.py)
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

log = logging.getLogger("vigie")

# A file sent in a DM, or a thread reply also posted to the channel, still concern the user.
ALERT_SUBTYPES = {None, "file_share", "thread_broadcast"}
DND_CACHE_SECONDS = 60


@dataclass(frozen=True)
class SlackMessage:
    channel: str
    ts: str
    author: str
    # "dm", "group-dm", "channel" or "private-channel"
    kind: str
    conversation: str
    in_thread: bool


def concerns_me(event, me, kind):
    """Whether a message event must ring: a direct message, or a personal tag; never the user's own."""
    if event.get("user") == me or event.get("subtype") not in ALERT_SUBTYPES:
        return False
    return kind == "dm" or f"<@{me}>" in (event.get("text") or "")


def dnd_active(info, now):
    """Whether Slack's "Do not disturb" is on right now, from a dnd.info answer."""
    if info.get("snooze_enabled") and info.get("snooze_endtime", 0) > now:
        return True
    start, end = info.get("next_dnd_start_ts", 0), info.get("next_dnd_end_ts", 0)
    return bool(info.get("dnd_enabled")) and start <= now < end


class SlackWatcher:
    """Listens to Slack for the user and hands the messages that concern them to on_message."""

    def __init__(self, app_token, user_token, on_message):
        self.web = WebClient(token=user_token)
        self.web.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=3))
        self.app_token = app_token
        self.on_message = on_message
        self.me = None
        self.team = None
        self.socket = None
        self.kinds = {}
        self.names = {}
        self.dnd = (0.0, {})
        self.lock = threading.Lock()

    # --- connection

    def start(self):
        """Connects; raises SlackApiError when a token is refused."""
        auth = self.web.auth_test()
        self.me, self.team = auth["user_id"], auth["team_id"]
        self.socket = SocketModeClient(app_token=self.app_token, web_client=self.web)
        self.socket.socket_mode_request_listeners.append(self.handle)
        self.socket.connect()
        log.info("slack: connected as %s", self.me)

    def stop(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def connected(self):
        return self.socket is not None and self.socket.is_connected()

    # --- incoming messages

    def handle(self, client: SocketModeClient, request: SocketModeRequest):
        client.send_socket_mode_response(SocketModeResponse(envelope_id=request.envelope_id))
        event = request.payload.get("event", {}) if request.type == "events_api" else {}
        if event.get("type") != "message":
            return
        try:
            kind = self.kind_of(event["channel"])
            if not concerns_me(event, self.me, kind):
                return
            message = SlackMessage(
                channel=event["channel"],
                ts=event["ts"],
                author=self.user_name(event.get("user")),
                kind=kind,
                conversation=self.conversation_name(event["channel"], kind),
                in_thread=bool(event.get("thread_ts")) and event.get("thread_ts") != event.get("ts"),
            )
        except Exception:
            log.exception("slack: could not read an incoming message")
            return
        log.info("slack: message for me (%s%s)", kind, ", thread" if message.in_thread else "")
        self.on_message(message)

    def info(self, channel):
        return self.web.conversations_info(channel=channel)["channel"]

    def kind_of(self, channel):
        if channel not in self.kinds:
            info = self.info(channel)
            if info.get("is_im"):
                kind = "dm"
            elif info.get("is_mpim"):
                kind = "group-dm"
            else:
                kind = "private-channel" if info.get("is_private") else "channel"
            self.kinds[channel] = (kind, info.get("name", ""))
        return self.kinds[channel][0]

    def conversation_name(self, channel, kind):
        if kind in ("channel", "private-channel"):
            return f"#{self.kinds[channel][1]}"
        return ""

    def user_name(self, user):
        if not user:
            return "?"
        if user not in self.names:
            try:
                profile = self.web.users_info(user=user)["user"]
                self.names[user] = profile.get("profile", {}).get("display_name") or profile.get("real_name") or user
            except SlackApiError:
                self.names[user] = user
        return self.names[user]

    # --- read state and "Do not disturb"

    def unseen(self, messages):
        """The messages not read yet; when Slack cannot tell, a message counts as unread."""
        positions = {}
        for channel in {message.channel for message in messages}:
            try:
                positions[channel] = self.info(channel).get("last_read")
            except Exception as exc:
                log.warning("slack: cannot tell whether %s was read: %r", channel, exc)
                positions[channel] = None
        return [
            message
            for message in messages
            if positions[message.channel] is None or float(positions[message.channel]) < float(message.ts)
        ]

    def do_not_disturb(self):
        with self.lock:
            checked_at, info = self.dnd
            if time.time() - checked_at > DND_CACHE_SECONDS:
                try:
                    info = self.web.dnd_info().data
                except Exception as exc:
                    log.warning("slack: dnd.info failed: %r", exc)
                    info = {}
                self.dnd = (time.time(), info)
        return dnd_active(info, time.time())

    def link(self, message):
        """Opens the conversation in the Slack application."""
        return f"slack://channel?team={self.team}&id={message.channel}"


def check_tokens(app_token, user_token):
    """Returns an error message, or None when both tokens work."""
    if not app_token.startswith("xapp-") or not user_token.startswith("xoxp-"):
        return "format"
    try:
        WebClient(token=user_token).auth_test()
    except SlackApiError:
        return "user"
    try:
        WebClient().apps_connections_open(app_token=app_token)
    except SlackApiError:
        return "app"
    return None
