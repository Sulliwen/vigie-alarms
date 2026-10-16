"""Zoom Team Chat side of Vigie: tells the program which triggers a new message matches.

The triggers (TRIGGERS) are a direct message from a listed contact, an @me mention, a reply to one of
the user's messages, @all, a keyword, or a message in a watched channel. The user's own messages never
match. VIP people are apart, as for Slack: every message they post is passed on.

Zoom pushes nothing to a desktop program and its "recent conversations" list stays empty on some
accounts, so the watcher reads the user's channels (and the listed contacts) one by one every
POLL_SECONDS. The API does not tell whether a message was read: Zoom alerts are sounds, never alarms.

The app is a "user-managed" Zoom app with Public Client OAuth: the user authorizes it once in the
browser (PKCE, answer on a loopback address), then a refresh token, renewed at every use, keeps it going.
"""

import base64
import hashlib
import html
import http.server
import json
import logging
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone

from slack_alerts import channel_key, has_keyword, name_key

log = logging.getLogger("vigie")

AUTHORIZE_URL = "https://zoom.us/oauth/authorize"
TOKEN_URL = "https://zoom.us/oauth/token"
API = "https://api.zoom.us/v2"
REDIRECT_PORT = 8765
REDIRECT = f"http://127.0.0.1:{REDIRECT_PORT}/callback"
AUTHORIZE_SECONDS = 300
POLL_SECONDS = 30
CHANNELS_SECONDS = 600
# At least this long between two calls: Zoom limits the calls per second.
CALL_GAP = 1.0
TRIGGERS = ("dm", "mention", "reply", "broadcast", "keyword", "channel")
# at_items[].at_type
AT_CONTACT, AT_ALL = 1, 2


class ZoomAuthError(Exception):
    """Zoom refuses the authorization (revoked, expired, or wrong client id)."""


class RateLimited(Exception):
    pass


@dataclass(frozen=True)
class ZoomMessage:
    id: str
    author: str
    # "dm" or "channel"
    kind: str
    conversation: str
    in_thread: bool
    vip: bool = False
    triggers: frozenset = frozenset()


def triggers_of(message, me, kind, channel_name="", keywords=(), channels=(), replies_to_me=False):
    """The triggers a message matches; none for the user's own messages.

    me: the user's identifiers (lower case): Zoom id, email and member id.
    """
    if (message.get("sender") or "").lower() in me or message.get("send_member_id") in me:
        return frozenset()
    mentioned = {
        item.get("at_type"): item
        for item in message.get("at_items") or []
        if item.get("at_type") == AT_ALL
        or (item.get("at_contact") or "").lower() in me
        or item.get("at_contact_member_id") in me
    }
    watched = {channel_key(name) for name in channels if name.strip()}
    found = {
        "dm": kind == "dm",
        "mention": AT_CONTACT in mentioned,
        "reply": replies_to_me,
        "broadcast": AT_ALL in mentioned,
        "keyword": has_keyword(message.get("message") or "", keywords),
        "channel": kind == "channel" and ("*" in watched or channel_key(channel_name) in watched),
    }
    return frozenset(trigger for trigger, matched in found.items() if matched)


def is_vip(message, me, vip_names):
    if (message.get("sender") or "").lower() in me:
        return False
    wanted = {name_key(name) for name in vip_names if name.strip()}
    return name_key(message.get("sender_display_name") or "") in wanted


# --- authorization ----------------------------------------------------------


def token_request(fields):
    request = urllib.request.Request(TOKEN_URL, data=urllib.parse.urlencode(fields).encode(), method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 401):
            raise ZoomAuthError(exc.read().decode(errors="replace")[:200]) from exc
        raise


def authorize(client_id, done_text, open_browser=webbrowser.open, timeout=AUTHORIZE_SECONDS):
    """Has the user authorize the app in the browser, which then shows done_text; returns the refresh
    token. Raises ZoomAuthError."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    answer = {}

    class Callback(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if query.get("state", [""])[0] == state:
                answer.update({key: values[0] for key, values in query.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<!doctype html><meta charset=utf-8><p>{html.escape(done_text)}</p>".encode())

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", REDIRECT_PORT), Callback)
    server.timeout = 1
    try:
        open_browser(AUTHORIZE_URL + "?" + urllib.parse.urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }))
        deadline = time.time() + timeout
        while not answer and time.time() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if "code" not in answer:
        raise ZoomAuthError(answer.get("error", "timeout"))
    tokens = token_request({
        "grant_type": "authorization_code",
        "code": answer["code"],
        "redirect_uri": REDIRECT,
        "code_verifier": verifier,
        "client_id": client_id,
    })
    return tokens["refresh_token"]


# --- watching ---------------------------------------------------------------


class ZoomWatcher:
    """Reads the user's Zoom channels and listed contacts, and hands the new messages that concern them
    to on_message. save_token(refresh_token) keeps the refresh token Zoom renews at every use."""

    def __init__(self, client_id, refresh_token, save_token, on_message,
                 vip_names=(), keywords=(), channels=(), contacts=()):
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.save_token = save_token
        self.on_message = on_message
        self.vip_names = list(vip_names)
        self.keywords = list(keywords)
        self.channels = list(channels)
        self.contacts = [contact.strip().lower() for contact in contacts if contact.strip()]
        self.access_token = None
        self.expires_at = 0.0
        self.me = set()
        # [(kind, id, name)], refreshed every CHANNELS_SECONDS
        self.conversations = []
        self.listed_at = 0.0
        # Per conversation: the newest timestamp read (ms) and the ids already seen at that time.
        self.read_up_to = {}
        self.seen = {}
        self.parents = {}
        self.healthy = False
        self.last_call = 0.0
        self.stopped = threading.Event()
        self.thread = None

    # --- connection

    def start(self):
        """Connects; raises ZoomAuthError when Zoom refuses the authorization."""
        self.renew()
        profile = self.get("/users/me")
        self.me = {value.lower() for value in (profile.get("id"), profile.get("email")) if value}
        self.started_ms = int(time.time() * 1000)
        self.list_conversations()
        self.healthy = True
        log.info("zoom: connected, watching %d conversation(s)", len(self.conversations))
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped.set()

    def connected(self):
        return self.healthy and not self.stopped.is_set()

    def renew(self):
        tokens = token_request({
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
        })
        self.refresh_token = tokens["refresh_token"]
        self.save_token(self.refresh_token)
        self.access_token = tokens["access_token"]
        self.expires_at = time.time() + tokens.get("expires_in", 3600) - 60

    def get(self, path, **params):
        if time.time() >= self.expires_at:
            self.renew()
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        for attempt in (1, 2):
            time.sleep(max(0.0, self.last_call + CALL_GAP - time.time()))
            self.last_call = time.time()
            request = urllib.request.Request(url)
            request.add_header("Authorization", f"Bearer {self.access_token}")
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                if exc.code == 401 and attempt == 1:
                    self.renew()
                    continue
                if exc.code == 429:
                    raise RateLimited() from exc
                raise
        return {}

    # --- polling

    def run(self):
        while not self.stopped.wait(POLL_SECONDS):
            try:
                if time.time() - self.listed_at >= CHANNELS_SECONDS:
                    self.list_conversations()
                for conversation in self.conversations:
                    if self.stopped.is_set():
                        return
                    self.read(*conversation)
                if not self.healthy:
                    log.info("zoom: reconnected")
                self.healthy = True
            except RateLimited:
                log.info("zoom: rate limited, waiting for the next round")
            except ZoomAuthError as exc:
                log.warning("zoom: authorization refused: %s", exc)
                self.healthy = False
                return
            except Exception as exc:
                if self.healthy:
                    log.warning("zoom: cannot read the messages: %r", exc)
                self.healthy = False

    def list_conversations(self):
        channels = self.get("/chat/users/me/channels", page_size=50).get("channels", [])
        self.conversations = [("channel", channel["id"], channel.get("name", "")) for channel in channels]
        self.conversations += [("dm", contact, contact) for contact in self.contacts]
        self.listed_at = time.time()

    def read(self, kind, target, name):
        """Hands on the messages of one conversation posted since the last read."""
        since_ms = self.read_up_to.get(target, self.started_ms)
        since = datetime.fromtimestamp(since_ms / 1000 - 60, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        where = {"to_channel": target} if kind == "channel" else {"to_contact": target}
        messages = self.get("/chat/users/me/messages", page_size=50, **{"from": since}, **where).get("messages", [])
        seen = self.seen.setdefault(target, set())
        fresh = sorted(
            (m for m in messages if m.get("timestamp", 0) >= since_ms and m.get("id") not in seen),
            key=lambda m: m.get("timestamp", 0),
        )
        for message in fresh:
            if (message.get("sender") or "").lower() in self.me:
                # The user's own messages tell their member id, used by mentions, and answer replies.
                if message.get("send_member_id"):
                    self.me.add(message["send_member_id"])
                self.parents[message["id"]] = True
            # Rate limited here, the message is read again at the next round.
            self.hand_on(message, kind, target, name)
            stamp = message.get("timestamp", since_ms)
            if stamp > self.read_up_to.get(target, since_ms):
                self.read_up_to[target] = stamp
                seen.clear()
            seen.add(message["id"])

    def hand_on(self, message, kind, target, name):
        try:
            parent = message.get("reply_main_message_id")
            vip = bool(self.vip_names) and is_vip(message, self.me, self.vip_names)
            triggers = triggers_of(
                message, self.me, kind, name, self.keywords, self.channels,
                replies_to_me=bool(parent) and self.written_by_me(parent, kind, target),
            )
            if not vip and not triggers:
                return
            found = ZoomMessage(
                id=message["id"],
                author=message.get("sender_display_name") or message.get("sender") or "?",
                kind=kind,
                conversation=name,
                in_thread=bool(parent),
                vip=vip,
                triggers=triggers,
            )
        except RateLimited:
            raise
        except Exception:
            log.exception("zoom: could not read a message")
            return
        self.on_message(found)

    def written_by_me(self, message_id, kind, target):
        if message_id not in self.parents:
            where = {"to_channel": target} if kind == "channel" else {"to_contact": target}
            try:
                sender = self.get(f"/chat/users/me/messages/{message_id}", **where).get("sender") or ""
            except urllib.error.HTTPError:
                sender = ""
            self.parents[message_id] = sender.lower() in self.me
        return self.parents[message_id]
