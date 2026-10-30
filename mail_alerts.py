"""Mail side of Vigie: tells the program about the new messages of an IMAP inbox, and whether they were read.

The triggers (TRIGGERS) are any new message, a message from a VIP person, or a keyword in the subject.
What each one does (nothing, a sound, an alarm) is the program's business. The user's own messages and
messages already read elsewhere never match.

The watcher reads the inbox every POLL_SECONDS over one connection. The mailbox is opened read-only and
the headers are fetched with BODY.PEEK: Vigie never marks a message as read. Only messages arriving after
the connection are handed on, so that the existing inbox stays silent.
"""

import imaplib
import logging
import re
import threading
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr

from slack_alerts import has_keyword, name_key

log = logging.getLogger("vigie")

DEFAULT_HOST = "mail.infomaniak.com"
PORT = 993
INBOX = "INBOX"
POLL_SECONDS = 30
TIMEOUT_SECONDS = 20
TRIGGERS = ("all", "vip", "keyword")
FETCH_NEW = "(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])"
SEEN = "\\Seen"


class MailAuthError(Exception):
    """The server refuses the address or the password."""


@dataclass(frozen=True)
class MailMessage:
    uid: int
    author: str
    subject: str
    vip: bool = False
    triggers: frozenset = frozenset()


def decoded(value):
    """A header as plain text on one line; an unknown encoding is left as it came."""
    try:
        value = str(make_header(decode_header(value)))
    except (LookupError, UnicodeError, ValueError):
        pass
    return " ".join(value.split())


def parse_fetch(data):
    """[(uid, flags, header bytes)] from what imaplib returns for a FETCH.

    A message is a tuple (start, literal) followed by the end of its line, or a line alone when nothing
    was asked as a literal. Lines without a UID are the server's unrequested flag updates.
    """
    entries = []
    for item in data:
        if item is None:
            continue
        line, literal = item if isinstance(item, tuple) else (item, b"")
        if re.match(rb"\d+ \(", line):
            entries.append([line, literal])
        elif entries:
            entries[-1][0] += line
    found = []
    for line, literal in entries:
        uid, flags = re.search(rb"\bUID (\d+)", line), re.search(rb"\bFLAGS \(([^)]*)\)", line)
        if uid:
            found.append((int(uid.group(1)), flags.group(1).decode(errors="replace") if flags else "", literal))
    return found


def parse_status(line):
    """(uid validity, next uid) from a STATUS answer."""
    text = line.decode(errors="replace")
    return int(re.search(r"UIDVALIDITY (\d+)", text).group(1)), int(re.search(r"UIDNEXT (\d+)", text).group(1))


def read_headers(header):
    """(display name, lower-case address, subject) of a message."""
    message = message_from_bytes(header)
    name, address = parseaddr(message.get("From", ""))
    return decoded(name), address.lower(), decoded(message.get("Subject", ""))


def triggers_of(name, address, subject, me, vip_names=(), keywords=()):
    """The triggers a message matches; none for the user's own messages."""
    if address == me:
        return frozenset()
    wanted = {name_key(vip) for vip in vip_names if vip.strip()}
    found = {
        "all": True,
        "vip": bool(wanted) and (name_key(name) in wanted or name_key(address) in wanted),
        "keyword": has_keyword(subject, keywords),
    }
    return frozenset(trigger for trigger, matched in found.items() if matched)


def connect(host, username, password):
    """A logged-in connection. Raises MailAuthError, or OSError when the server cannot be reached."""
    connection = imaplib.IMAP4_SSL(host, PORT, timeout=TIMEOUT_SECONDS)
    try:
        connection.login(username, password)
    except imaplib.IMAP4.abort:
        # The connection broke during the login: nothing was refused.
        raise
    except imaplib.IMAP4.error as exc:
        try:
            connection.shutdown()
        except OSError:
            pass
        raise MailAuthError(str(exc)) from exc
    return connection


def check_account(host, username, password):
    """Raises MailAuthError or OSError when this account cannot be read."""
    connection = connect(host, username, password)
    try:
        connection.select(INBOX, readonly=True)
    finally:
        connection.logout()


class MailWatcher:
    """Reads the inbox and hands the new messages to on_message."""

    def __init__(self, host, username, password, on_message, vip_names=(), keywords=()):
        self.host = host
        self.username = username
        self.password = password
        self.me = username.strip().lower()
        self.on_message = on_message
        self.vip_names = list(vip_names)
        self.keywords = list(keywords)
        self.connection = None
        # Kept over a reconnection, so that a message arriving during a network loss still alerts.
        self.validity = None
        self.next_uid = None
        self.healthy = False
        # imaplib is not thread-safe: the watcher's thread and unseen() share the connection.
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        self.thread = None

    def start(self):
        """Connects; raises MailAuthError when the server refuses the account."""
        with self.lock:
            self.open()
        self.healthy = True
        log.info("mail: connected")
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped.set()

    def connected(self):
        return self.healthy and not self.stopped.is_set()

    def open(self):
        self.connection = connect(self.host, self.username, self.password)
        status, lines = self.connection.status(INBOX, "(UIDVALIDITY UIDNEXT)")
        if status != "OK":
            raise imaplib.IMAP4.error(f"STATUS: {status}")
        validity, next_uid = parse_status(lines[0])
        # A new validity renumbers the mailbox: the position kept no longer means anything.
        if validity != self.validity:
            self.validity, self.next_uid = validity, next_uid
        status, _ = self.connection.select(INBOX, readonly=True)
        if status != "OK":
            raise imaplib.IMAP4.error(f"SELECT: {status}")

    def close(self):
        connection, self.connection = self.connection, None
        if connection is not None:
            try:
                connection.logout()
            except (imaplib.IMAP4.error, OSError):
                pass

    def run(self):
        try:
            while not self.stopped.wait(POLL_SECONDS):
                try:
                    with self.lock:
                        if self.connection is None:
                            self.open()
                        fresh = self.read_new()
                    if not self.healthy:
                        log.info("mail: reconnected")
                    self.healthy = True
                    for message in fresh:
                        self.on_message(message)
                except MailAuthError as exc:
                    log.warning("mail: account refused: %s", exc)
                    self.healthy = False
                    return
                except Exception as exc:
                    if self.healthy:
                        log.warning("mail: cannot read the inbox: %r", exc)
                    self.healthy = False
                    with self.lock:
                        self.close()
        finally:
            with self.lock:
                self.close()

    def read_new(self):
        """The messages that arrived since the last read and concern the user."""
        status, data = self.connection.uid("SEARCH", None, f"UID {self.next_uid}:*")
        if status != "OK":
            raise imaplib.IMAP4.error(f"SEARCH: {status}")
        # "n:*" always answers the newest message, even an older one.
        uids = sorted(uid for uid in map(int, (data[0] or b"").split()) if uid >= self.next_uid)
        if not uids:
            return []
        status, data = self.connection.uid("FETCH", ",".join(map(str, uids)), FETCH_NEW)
        if status != "OK":
            raise imaplib.IMAP4.error(f"FETCH: {status}")
        self.next_uid = uids[-1] + 1
        return [message for message in map(self.message, parse_fetch(data)) if message is not None]

    def message(self, entry):
        uid, flags, header = entry
        try:
            if SEEN in flags:
                return None
            name, address, subject = read_headers(header)
            triggers = triggers_of(name, address, subject, self.me, self.vip_names, self.keywords)
            if not triggers:
                return None
            return MailMessage(uid, name or address or "?", subject, "vip" in triggers, triggers)
        except Exception:
            log.exception("mail: could not read a message")
            return None

    def unseen(self, messages):
        """The messages not read yet; when the server cannot tell, a message counts as unread.
        A message gone from the inbox has been dealt with."""
        uids = ",".join(str(message.uid) for message in messages)
        try:
            with self.lock:
                if self.connection is None:
                    return list(messages)
                status, data = self.connection.uid("FETCH", uids, "(UID FLAGS)")
            if status != "OK":
                raise imaplib.IMAP4.error(f"FETCH: {status}")
        except (imaplib.IMAP4.error, OSError) as exc:
            log.warning("mail: cannot tell whether messages were read: %r", exc)
            return list(messages)
        unread = {uid for uid, flags, _ in parse_fetch(data) if SEEN not in flags}
        return [message for message in messages if message.uid in unread]
