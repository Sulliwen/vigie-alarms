import re
import string
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest import mock

import icalendar

import slack_alerts
import texts
import vigie
import zoom_alerts
from vigie import Event, due_events, extract_events

ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//EN
BEGIN:VEVENT
UID:timed
SUMMARY:Point projet
LOCATION:Salle 2
DTSTART:20261013T120000Z
DTEND:20261013T130000Z
END:VEVENT
BEGIN:VEVENT
UID:allday
SUMMARY:Férié
DTSTART;VALUE=DATE:20261013
DTEND;VALUE=DATE:20261014
END:VEVENT
BEGIN:VEVENT
UID:cancelled
SUMMARY:Annulé
STATUS:CANCELLED
DTSTART:20261013T140000Z
DTEND:20261013T150000Z
END:VEVENT
BEGIN:VEVENT
UID:declined
SUMMARY:Refusé
DTSTART:20261013T160000Z
DTEND:20261013T170000Z
ATTENDEE;PARTSTAT=ACCEPTED:mailto:other@example.com
ATTENDEE;PARTSTAT=DECLINED:mailto:Me@Example.com
END:VEVENT
BEGIN:VEVENT
UID:accepted
SUMMARY:Accepté
DTSTART:20261013T180000Z
DURATION:PT30M
ATTENDEE;PARTSTAT=DECLINED:mailto:other@example.com
ATTENDEE;PARTSTAT=NEEDS-ACTION:mailto:me@example.com
END:VEVENT
BEGIN:VEVENT
UID:weekly
SUMMARY:Hebdo
DTSTART:20260901T090000Z
DTEND:20260901T093000Z
RRULE:FREQ=WEEKLY
END:VEVENT
END:VCALENDAR
"""

CALDAV = {"id": "a", "type": "caldav", "url": "https://example.com", "username": "AB12345", "calendars": ["url/mine"]}
FEED = {"id": "g", "type": "ics", "name": "Google"}
PROVIDER = {provider["key"]: provider for provider in texts.PROVIDERS}


def event(key, start):
    return Event(key, start, start + timedelta(hours=1), key, "", "cal")


def components(ics=ICS):
    return icalendar.Calendar.from_ical(ics).walk("VEVENT")


class ExtractEventsTest(unittest.TestCase):
    def setUp(self):
        self.events = {e.key.split("|")[0]: e for e in extract_events(components(), "Perso", {"me@example.com"})}

    def test_keeps_only_live_undeclined_events(self):
        self.assertEqual(set(self.events), {"timed", "accepted", "weekly", "allday"})

    def test_all_day_event_runs_from_local_midnight_to_midnight(self):
        allday = self.events["allday"]
        self.assertTrue(allday.all_day)
        self.assertFalse(self.events["timed"].all_day)
        self.assertEqual((allday.start.date().isoformat(), allday.start.hour), ("2026-10-13", 0))
        self.assertEqual(allday.end - allday.start, timedelta(days=1))

    def test_reads_fields_and_converts_to_local_time(self):
        timed = self.events["timed"]
        self.assertEqual((timed.summary, timed.location, timed.calendar), ("Point projet", "Salle 2", "Perso"))
        self.assertEqual(timed.start, datetime.fromisoformat("2026-10-13T12:00:00+00:00"))
        self.assertEqual(timed.start.utcoffset(), datetime.now().astimezone().utcoffset())
        self.assertEqual(self.events["accepted"].end - self.events["accepted"].start, timedelta(minutes=30))

    def test_appointments_marked_free_are_flagged(self):
        marked = ICS.replace("UID:timed", "UID:timed\nTRANSP:TRANSPARENT")
        events = {e.key.split("|")[0]: e for e in extract_events(components(marked), "Perso", set())}
        self.assertTrue(events["timed"].free)
        self.assertFalse(events["accepted"].free)

    def test_unanswered_invitations_are_flagged(self):
        self.assertTrue(self.events["accepted"].unanswered)
        self.assertFalse(self.events["timed"].unanswered)

    def test_key_changes_when_the_event_moves(self):
        moved = extract_events(components(ICS.replace("20261013T120000Z", "20261013T121500Z")), "Perso", set())
        self.assertNotEqual(moved[0].key, self.events["timed"].key)


class DueEventsTest(unittest.TestCase):
    now = datetime.fromisoformat("2026-10-13T12:00:00+00:00")
    lead = timedelta(minutes=10)
    grace = timedelta(minutes=5)

    def due(self, minutes_from_now, handled=()):
        events = [event("e", self.now + timedelta(minutes=minutes_from_now))]
        return bool(due_events(events, set(handled), self.now, self.lead, self.grace))

    def test_window(self):
        self.assertFalse(self.due(11))
        self.assertTrue(self.due(10))
        # Added at the last minute, or found after a wake-up.
        self.assertTrue(self.due(2))
        self.assertTrue(self.due(-4))
        self.assertFalse(self.due(-5))

    def test_handled_events_do_not_ring_again(self):
        self.assertFalse(self.due(5, handled=["e"]))

    def test_all_day_events_never_ring(self):
        start = self.now + timedelta(minutes=5)
        allday = Event("e", start, start + timedelta(days=1), "e", "", "cal", all_day=True)
        self.assertFalse(due_events([allday], set(), self.now, self.lead, self.grace))


class AgendaDaysTest(unittest.TestCase):
    def test_events_are_grouped_by_day_with_all_day_ones_first(self):
        monday = datetime(2026, 10, 12).astimezone()
        late = event("late", monday.replace(hour=16))
        early = event("early", monday.replace(hour=9))
        wednesday = event("wednesday", monday.replace(hour=10) + timedelta(days=2))
        trip = Event("trip", monday, monday + timedelta(days=2), "trip", "", "cal", all_day=True)
        outside = event("outside", monday + timedelta(days=3))
        agenda = vigie.agenda_days([late, wednesday, trip, early, outside], monday.date(), 3)
        self.assertEqual(
            [(day.isoformat(), [e.key for e in events]) for day, events in agenda],
            [
                ("2026-10-12", ["trip", "early", "late"]),
                ("2026-10-13", ["trip"]),
                ("2026-10-14", ["wednesday"]),
            ],
        )


class IconTest(unittest.TestCase):
    def test_portrait_with_and_without_status_dot(self):
        plain, ok, failing = vigie.make_icon(), vigie.make_icon(vigie.COLOR_OK), vigie.make_icon(vigie.COLOR_ERROR)
        self.assertEqual(plain.size, (256, 256))
        corner = (206, 206)
        self.assertEqual(ok.getpixel(corner)[:3], (0x2E, 0x7D, 0x32))
        self.assertEqual(failing.getpixel(corner)[:3], (0xC6, 0x28, 0x28))
        self.assertNotIn(plain.getpixel(corner)[:3], (ok.getpixel(corner)[:3], failing.getpixel(corner)[:3]))


class DevModeTest(unittest.TestCase):
    def watch(self, sources, edit):
        """Runs watch_sources until edit() has had time to be seen; returns how often it restarted."""
        restarts, calls = [], []

        def sleep(_):
            calls.append(1)
            if len(calls) == 1:
                edit()
            if restarts or len(calls) > 10:
                raise StopIteration

        with mock.patch("vigie.SOURCES", sources), mock.patch("vigie.time.sleep", side_effect=sleep):
            with self.assertRaises(StopIteration):
                vigie.watch_sources(lambda: restarts.append(1))
        return len(restarts)

    def test_restarts_when_a_source_changes_and_still_compiles(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "module.py"
            source.write_text("x = 1\n")
            def edit(text):
                def write():
                    source.write_text(text)
                    later = source.stat().st_mtime + 5
                    os.utime(source, (later, later))
                return write
            self.assertEqual(self.watch([source], edit("x = 2\n")), 1)
            self.assertEqual(self.watch([source], edit("x = (\n")), 0)


class SlackRulesTest(unittest.TestCase):
    me = "UME"

    def triggers(self, kind, name="", keywords=(), channels=(), **event):
        event = {"user": "UOTHER", "text": "hello", "ts": "2.0", **event}
        return set(slack_alerts.triggers_of(event, self.me, kind, name, keywords, channels))

    def test_each_trigger_is_recognised(self):
        self.assertEqual(self.triggers("dm"), {"dm"})
        self.assertEqual(self.triggers("dm", subtype="file_share"), {"dm"})
        self.assertEqual(self.triggers("group-dm"), {"group"})
        self.assertEqual(self.triggers("channel", text="<@UME> can you check?"), {"mention"})
        self.assertEqual(self.triggers("channel", text="<@UME>", thread_ts="1.0"), {"mention"})
        self.assertEqual(self.triggers("channel", thread_ts="1.0", parent_user_id="UME"), {"reply"})
        self.assertEqual(self.triggers("channel", thread_ts="1.0", parent_user_id="UOTHER"), set())
        self.assertEqual(self.triggers("channel", text="<!here> look"), {"broadcast"})
        self.assertEqual(self.triggers("private-channel", text="<!channel|channel>"), {"broadcast"})
        self.assertEqual(self.triggers("channel", text="<!subteam^S1> hi"), set())
        self.assertEqual(self.triggers("channel"), set())

    def test_keywords_are_whole_words_and_channels_ignore_the_hash(self):
        self.assertEqual(self.triggers("channel", text="Prod is down", keywords=["prod"]), {"keyword"})
        self.assertEqual(self.triggers("channel", text="product launch", keywords=["prod"]), set())
        self.assertEqual(self.triggers("channel", text="x", keywords=["", " "]), set())
        self.assertEqual(self.triggers("channel", name="Alertes-Prod", channels=["#alertes-prod"]), {"channel"})
        self.assertEqual(self.triggers("group-dm", name="", channels=["#alertes-prod"]), {"group"})

    def test_own_messages_edits_and_bots_never_match(self):
        self.assertEqual(self.triggers("dm", user="UME", text="<@UME>"), set())
        self.assertEqual(self.triggers("dm", subtype="message_changed"), set())
        self.assertEqual(self.triggers("dm", subtype="bot_message"), set())

    def test_vip_people_are_matched_by_any_name_in_any_word_order(self):
        names = ["Jakez", "Jakez Rolland"]
        event = {"user": "UJ", "text": "no tag"}
        self.assertTrue(slack_alerts.is_vip(event, self.me, ["Jakez", "Jakez Rolland", "jakez.rolland"], names))
        self.assertTrue(slack_alerts.is_vip(event, self.me, ["Rolland  Jakez"], names))
        self.assertFalse(slack_alerts.is_vip(event, self.me, ["Jakez Martin"], names))
        self.assertFalse(slack_alerts.is_vip(event, self.me, ["Jakez"], []))
        self.assertFalse(slack_alerts.is_vip({**event, "subtype": "message_changed"}, self.me, ["Jakez"], names))
        self.assertFalse(slack_alerts.is_vip({**event, "user": "UME"}, self.me, ["Jakez"], names))

    def test_a_vip_message_in_a_channel_is_passed_on_without_a_tag(self):
        received = []
        watcher = slack_alerts.SlackWatcher("xapp-1", "xoxp-1", on_message=received.append, vip_names=["Jakez Rolland"])
        watcher.me = "UME"
        watcher.kinds = {"C1": ("channel", "dev")}
        watcher.profiles = {"UJ": ["Rolland Jakez"], "UA": ["Ana"]}
        client = mock.Mock()
        for user in ("UJ", "UA"):
            payload = {"event": {"type": "message", "channel": "C1", "user": user, "text": "hello", "ts": "1.0"}}
            watcher.handle(client, mock.Mock(type="events_api", payload=payload, envelope_id="e"))
        (message,) = received
        self.assertTrue(message.vip)
        self.assertEqual((message.author, message.conversation), ("Rolland Jakez", "#dev"))

    def test_do_not_disturb(self):
        now = 1000
        self.assertFalse(slack_alerts.dnd_active({"dnd_enabled": True, "next_dnd_start_ts": 2000, "next_dnd_end_ts": 3000}, now))
        self.assertTrue(slack_alerts.dnd_active({"dnd_enabled": True, "next_dnd_start_ts": 900, "next_dnd_end_ts": 3000}, now))
        self.assertFalse(slack_alerts.dnd_active({"dnd_enabled": False, "next_dnd_start_ts": 900, "next_dnd_end_ts": 3000}, now))
        self.assertTrue(slack_alerts.dnd_active({"snooze_enabled": True, "snooze_endtime": 1500}, now))
        self.assertFalse(slack_alerts.dnd_active({"snooze_enabled": True, "snooze_endtime": 500}, now))

    def test_read_position_decides_what_is_unseen(self):
        watcher = slack_alerts.SlackWatcher("xapp-1", "xoxp-1", on_message=None)
        positions = {"D1": "200.0", "C1": None}
        watcher.info = lambda channel: {"last_read": positions[channel]}
        read = slack_alerts.SlackMessage("D1", "150.0", "Ana", "dm", "", False)
        unread = slack_alerts.SlackMessage("D1", "250.0", "Ana", "dm", "", False)
        unknown = slack_alerts.SlackMessage("C1", "100.0", "Ana", "channel", "#dev", True)
        self.assertEqual(watcher.unseen([read, unread, unknown]), [unread, unknown])


class ZoomRulesTest(unittest.TestCase):
    me = {"zid", "me@x.test", "mid"}

    def triggers(self, kind="channel", name="dev", keywords=(), channels=(), replies_to_me=False, **message):
        message = {"id": "m1", "sender": "ana@x.test", "message": "hello", "timestamp": 1, **message}
        return set(zoom_alerts.triggers_of(message, self.me, kind, name, keywords, channels, replies_to_me))

    def test_each_trigger_is_recognised(self):
        mention = {"at_type": zoom_alerts.AT_CONTACT, "at_contact": "ZID"}
        everyone = {"at_type": zoom_alerts.AT_ALL, "at_contact": ""}
        other = {"at_type": zoom_alerts.AT_CONTACT, "at_contact": "someone"}
        self.assertEqual(self.triggers("dm", "ana@x.test"), {"dm"})
        self.assertEqual(self.triggers(at_items=[mention]), {"mention"})
        self.assertEqual(self.triggers(at_items=[{"at_type": 1, "at_contact_member_id": "mid"}]), {"mention"})
        self.assertEqual(self.triggers(at_items=[other]), set())
        self.assertEqual(self.triggers(at_items=[everyone]), {"broadcast"})
        self.assertEqual(self.triggers(replies_to_me=True), {"reply"})
        self.assertEqual(self.triggers(message="Prod is down", keywords=["prod"]), {"keyword"})
        self.assertEqual(self.triggers(channels=["#Dev"]), {"channel"})
        self.assertEqual(self.triggers(channels=["*"]), {"channel"})
        self.assertEqual(self.triggers("dm", "ana@x.test", channels=["*"]), {"dm"})
        self.assertEqual(self.triggers(), set())

    def test_own_messages_never_match(self):
        self.assertEqual(self.triggers("dm", sender="ME@x.test"), set())
        self.assertEqual(self.triggers(send_member_id="mid", at_items=[{"at_type": 2}]), set())
        self.assertFalse(zoom_alerts.is_vip({"sender": "me@x.test", "sender_display_name": "Jakez"}, self.me, ["Jakez"]))

    def test_vip_people_are_matched_by_their_display_name(self):
        message = {"sender": "j@x.test", "sender_display_name": "Rolland Jakez"}
        self.assertTrue(zoom_alerts.is_vip(message, self.me, ["Jakez Rolland"]))
        self.assertFalse(zoom_alerts.is_vip(message, self.me, ["Jakez"]))

    def watcher(self, pages, **options):
        received = []
        watcher = zoom_alerts.ZoomWatcher("cid", "rt", save_token=None, on_message=received.append, **options)
        watcher.me = set(self.me)
        watcher.started_ms = 1000
        watcher.get = lambda path, **params: pages.pop(0) if path.endswith("/messages") else {"sender": "me@x.test"}
        return watcher, received

    def test_only_new_messages_are_handed_on_once(self):
        old = {"id": "a", "sender": "ana@x.test", "timestamp": 900, "message": "prod"}
        new = {"id": "b", "sender": "ana@x.test", "timestamp": 2000, "message": "prod"}
        newer = {"id": "c", "sender": "ana@x.test", "timestamp": 3000, "message": "prod"}
        watcher, received = self.watcher([{"messages": [new, old]}, {"messages": [newer, new]}], keywords=["prod"])
        watcher.read("channel", "C1", "dev")
        watcher.read("channel", "C1", "dev")
        self.assertEqual([message.id for message in received], ["b", "c"])
        self.assertEqual(watcher.read_up_to["C1"], 3000)

    def test_a_reply_to_one_of_my_messages_and_my_member_id_are_recognised(self):
        mine = {"id": "p", "sender": "me@x.test", "send_member_id": "mid2", "timestamp": 2000}
        reply = {"id": "r", "sender": "ana@x.test", "timestamp": 2001, "reply_main_message_id": "p",
                 "sender_display_name": "Ana"}
        watcher, received = self.watcher([{"messages": [reply, mine]}])
        watcher.read("channel", "C1", "dev")
        (message,) = received
        self.assertEqual((message.triggers, message.author, message.in_thread), ({"reply"}, "Ana", True))
        self.assertIn("mid2", watcher.me)


class VersionTest(unittest.TestCase):
    def test_version_is_major_minor_patch(self):
        self.assertRegex(vigie.__version__, r"^\d+\.\d+\.\d+$")


class IcsUrlTest(unittest.TestCase):
    def test_only_https_feeds_are_accepted(self):
        normalize = vigie.normalize_ics_url
        self.assertEqual(normalize(" https://x.test/basic.ics "), "https://x.test/basic.ics")
        self.assertEqual(normalize("webcal://x.test/basic.ics"), "https://x.test/basic.ics")
        for refused in ("file:///C:/secret.txt", "http://x.test/basic.ics", "basic.ics", ""):
            self.assertIsNone(normalize(refused))


class TextsTest(unittest.TestCase):
    def test_both_languages_say_the_same_things(self):
        french, english = texts.STRINGS["fr"], texts.STRINGS["en"]
        self.assertEqual(set(french), set(english))
        for key in french:
            fields = [{name for _, name, _, _ in string.Formatter().parse(text[key]) if name} for text in (french, english)]
            self.assertEqual(*fields, key)

    def test_every_provider_has_a_name_and_instructions(self):
        for provider in texts.PROVIDERS:
            for language in texts.STRINGS.values():
                self.assertTrue(language[f"provider_{provider['key']}"])
                self.assertTrue(language[f"help_{provider['key']}"])

    def test_french_addresses_the_user_formally(self):
        informal = re.compile(r"\b(tu|ton|ta|tes|toi)\b", re.IGNORECASE)
        self.assertEqual([key for key, text in texts.STRINGS["fr"].items() if informal.search(text)], [])

    def test_no_user_text_is_left_in_the_program(self):
        source = Path(vigie.__file__).read_text(encoding="utf-8")
        code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
        self.assertEqual(re.findall(r"[éèêàçùôî«»…]", code.replace('show="•"', "")), [])


class ConfigTest(unittest.TestCase):
    def test_older_files_keep_their_vip_people_and_get_the_new_triggers(self):
        stored = {"slack_vip_names": ["Jakez"], "slack_actions": {"dm": "sound"}}
        with mock.patch("vigie.load_json", return_value=stored):
            config = vigie.load_config()
        self.assertTrue(config["slack_vip_enabled"])
        self.assertEqual(config["slack_actions"]["dm"], "sound")
        self.assertEqual(config["slack_actions"]["mention"], "sound_alarm")
        with mock.patch("vigie.load_json", return_value={}):
            self.assertFalse(vigie.load_config()["slack_vip_enabled"])

    def test_older_files_get_the_zoom_triggers(self):
        with mock.patch("vigie.load_json", return_value={"zoom_actions": {"channel": "sound"}}):
            config = vigie.load_config()
        self.assertEqual(config["zoom_actions"]["channel"], "sound")
        self.assertEqual(config["zoom_actions"]["mention"], "sound")

    def test_forget_also_removes_the_slack_tokens(self):
        with (
            mock.patch("vigie.load_json", return_value={"accounts": [{"id": "a1"}]}),
            mock.patch("vigie.keyring") as keyring,
        ):
            vigie.forget()
        removed = {call.args[0] for call in keyring.delete_password.call_args_list}
        self.assertEqual(removed, {"vigie:a1", "vigie:slack:app", "vigie:slack:user", "vigie:zoom"})

    def test_default_accounts_are_not_shared_between_configurations(self):
        with mock.patch("vigie.load_json", return_value={}):
            vigie.load_config()["accounts"].append("x")
        self.assertEqual(vigie.DEFAULT_CONFIG["accounts"], [])


class AppTest(unittest.TestCase):
    """Drives the real windows, with the sound, the tray and the vault mocked out."""

    def setUp(self):
        for target in ("winsound.PlaySound", "keyring", "save_json", "pystray.Icon"):
            patcher = mock.patch(f"vigie.{target}")
            setattr(self, target.split(".")[-1], patcher.start())
            self.addCleanup(patcher.stop)
        self.keyring.get_password.return_value = "secret"
        with mock.patch("vigie.load_json", return_value={}):
            self.app = vigie.App()
        texts.set_language("fr")
        self.app.tray = mock.Mock()
        self.app.fetcher = mock.Mock()
        self.caldav, self.feed = dict(CALDAV), dict(FEED)
        self.app.config["accounts"] = [self.caldav]
        self.app.root.after = mock.Mock()
        self.addCleanup(self.app.root.destroy)
        self.now = datetime.now().astimezone()

    def tick(self):
        self.app.tick()
        self.app.root.update()

    # --- alarms

    def test_stop_silences_the_event_for_good(self):
        soon = event("soon", self.now + timedelta(minutes=4))
        self.app.on_events("a", [soon, event("later", self.now + timedelta(hours=3))])
        self.tick()
        self.assertEqual(list(self.app.windows), ["soon"])
        self.assertTrue(self.app.sound_playing)
        self.tick()
        self.assertEqual(len(self.app.windows), 1)

        self.app.windows["soon"].stop()
        self.tick()
        self.assertFalse(self.app.windows)
        self.assertFalse(self.app.sound_playing)
        self.assertIn("soon", self.app.acked)

    def test_snooze_rings_again_even_after_the_grace_period(self):
        started = event("started", self.now - timedelta(minutes=3))
        self.app.on_events("a", [started])
        self.tick()
        self.app.windows["started"].snooze()
        self.tick()
        self.assertFalse(self.app.windows)
        self.assertFalse(self.app.sound_playing)

        self.app.snoozed["started"] = (self.now - timedelta(seconds=1), started)
        self.app.on_events("a", [])
        self.tick()
        self.assertEqual(list(self.app.windows), ["started"])
        self.assertNotIn("started", self.app.acked)

    def test_cancelled_event_stops_ringing(self):
        self.app.on_events("a", [event("soon", self.now + timedelta(minutes=4))])
        self.tick()
        self.app.on_events("a", [])
        self.assertFalse(self.app.windows)
        self.assertFalse(self.app.sound_playing)

    def test_meeting_present_in_two_accounts_rings_once_and_survives_one_of_them(self):
        self.app.config["accounts"].append(self.feed)
        soon = event("soon", self.now + timedelta(minutes=4))
        self.app.on_events("a", [soon])
        self.app.on_events("g", [soon])
        self.tick()
        self.assertEqual(list(self.app.windows), ["soon"])
        # Removed from one calendar only: still a meeting.
        self.app.on_events("g", [])
        self.assertEqual(list(self.app.windows), ["soon"])

    # --- accounts

    def fetch_caldav(self, found):
        calendars = {}
        for url in ("url/mine", "url/colleague"):
            calendars[url] = (mock.Mock(**{"search.return_value": found}), url)
        discovery = vigie.Discovery(calendars, set(), "Me")
        fetcher = vigie.Fetcher(self.app)
        with mock.patch("vigie.discover", return_value=discovery):
            return fetcher.fetch(self.caldav, "secret"), calendars

    def test_only_the_chosen_calendars_are_read(self):
        found = [mock.Mock(icalendar_instance=icalendar.Calendar.from_ical(ICS))]
        events, calendars = self.fetch_caldav(found)
        self.assertEqual({e.calendar for e in events}, {"url/mine"})
        # Read from the start of today up to seven days ahead, for the agenda window.
        window = calendars["url/mine"][0].search.call_args.kwargs
        self.assertEqual((window["start"].hour, (window["end"] - window["start"]).days), (0, 7))
        calendars["url/colleague"][0].search.assert_not_called()

    def test_calendars_must_be_chosen_first_and_still_exist(self):
        for chosen in (None, ["url/deleted"]):
            self.caldav["calendars"] = chosen
            with self.assertRaises(vigie.CalendarsNeeded):
                self.fetch_caldav([])

    def test_ical_feed_expands_recurrences_and_spots_declined_invitations(self):
        fetcher = vigie.Fetcher(self.app)
        start = datetime(2026, 10, 13, 0, 0, tzinfo=timezone.utc)
        url = "https://calendar.test/ical/me%40example.com/private-abc/basic.ics"
        with mock.patch("vigie.download_ics", return_value=ICS.encode()) as download:
            events = fetcher.fetch_ics(self.feed, url, start, start + timedelta(days=7))
            fetcher.fetch_ics(self.feed, url, start, start + timedelta(days=7))
        self.assertEqual(download.call_count, 2)
        by_uid = {}
        for e in events:
            by_uid.setdefault(e.key.split("|")[0], []).append(e)
        self.assertEqual(set(by_uid), {"timed", "accepted", "weekly", "allday"})
        self.assertEqual(
            [e.start for e in by_uid["weekly"]], [datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)]
        )
        self.assertEqual(by_uid["weekly"][0].calendar, "Google")

    def test_first_choice_proposes_the_owner_calendar(self):
        self.caldav["calendars"] = None
        self.app.on_discovery("a", {"url/mine": "Me", "url/colleague": "Someone"}, "Me")
        self.app.ask_calendars("a")
        self.app.root.update()
        dialog = self.app.dialogs["calendars"]
        self.assertEqual({url: var.get() for url, var in dialog.choices.items()}, {"url/mine": True, "url/colleague": False})
        dialog.choices["url/mine"].set(False)
        dialog.submit()
        self.assertIn("calendars", self.app.dialogs)
        dialog.choices["url/colleague"].set(True)
        dialog.submit()
        self.assertEqual(self.caldav["calendars"], ["url/colleague"])
        self.assertNotIn("calendars", self.app.dialogs)
        self.app.fetcher.reset.assert_called()

    def test_refused_secret_reopens_the_matching_dialog(self):
        self.app.config["accounts"].append(self.feed)
        self.app.on_refused("g")
        self.app.root.update()
        self.assertIsInstance(self.app.dialogs["ics"], vigie.IcsDialog)
        self.app.dialogs["ics"].close()
        self.app.on_refused("a")
        self.app.root.update()
        self.assertIsInstance(self.app.dialogs["caldav"], vigie.CaldavDialog)
        self.assertNotIn("ics", self.app.dialogs)

    def test_adding_and_removing_an_ical_feed(self):
        self.app.show_accounts()
        self.app.edit_account(None, PROVIDER["google"])
        self.app.root.update()
        dialog = self.app.dialogs["ics"]
        self.assertEqual(dialog.label_entry.get(), "Google Agenda")
        dialog.url.insert(0, "file:///C:/secret.txt")
        dialog.submit()
        self.assertEqual(len(self.app.config["accounts"]), 1)

        dialog.tested(None, "Google", "https://calendar.test/basic.ics")
        added = self.app.config["accounts"][1]
        self.assertEqual((added["type"], added["provider"], added["name"]), ("ics", "google", "Google"))
        self.keyring.set_password.assert_called_once_with(
            f"vigie:{added['id']}", "secret", "https://calendar.test/basic.ics"
        )
        # The address is a secret: it must stay out of the configuration file.
        self.assertNotIn("calendar.test", str(self.save_json.call_args.args[1]))

        self.app.on_events(added["id"], [event("soon", self.now + timedelta(hours=1))])
        self.app.remove_account(added)
        self.assertEqual(self.app.config["accounts"], [self.caldav])
        self.assertFalse(self.app.events)
        self.keyring.delete_password.assert_called_once_with(f"vigie:{added['id']}", "secret")

    def test_first_launch_opens_the_accounts_window(self):
        self.app.config["accounts"] = []
        self.app.root.mainloop = mock.Mock()
        with mock.patch("vigie.autostart_command", return_value=vigie.launch_command()):
            self.app.run()
        self.assertIsInstance(self.app.dialogs["accounts"], vigie.AccountsDialog)

    def test_dropdown_offers_every_provider_and_prefills_its_server(self):
        self.app.show_accounts()
        accounts = self.app.dialogs["accounts"]
        self.assertEqual(len(accounts.provider.cget("values")), len(texts.PROVIDERS))
        accounts.provider.current(texts.PROVIDERS.index(PROVIDER["icloud"]))
        accounts.add()
        self.app.root.update()
        dialog = self.app.dialogs["caldav"]
        self.assertEqual(dialog.url.get(), "https://caldav.icloud.com")
        dialog.tested(None, "https://caldav.icloud.com", "me@icloud.com", "app-password")
        self.assertEqual(self.app.config["accounts"][1]["provider"], "icloud")

    def test_changing_language_translates_menus_and_windows(self):
        self.app.show_accounts()
        self.assertEqual(self.app.next_text(), "Aucun rendez-vous dans les 24 h")
        self.app.set_language("en")
        self.addCleanup(texts.set_language, "fr")
        self.assertEqual(self.app.next_text(), "No appointment in the next 24 h")
        self.assertEqual(self.app.config["language"], "en")
        self.assertFalse(self.app.dialogs)
        self.app.show_accounts()
        self.app.root.update()
        self.assertIn("Synced calendars", self.app.dialogs["accounts"].title())

    # --- settings

    def test_settings_are_applied_and_saved(self):
        self.app.show_settings()
        self.app.root.update()
        dialog = self.app.dialogs["settings"]
        self.assertIn(f"Vigie {vigie.__version__}", self.labels(dialog.footer))
        self.assertIn("Alarm 01", dialog.sound.cget("values"))
        self.assertEqual(dialog.sound.get(), "Alarm 01")
        dialog.lead = lambda: 15
        dialog.days = lambda: 3
        dialog.sound.set("Ring 02")
        dialog.silence.current(3)
        dialog.ignore_free.set(True)
        dialog.language.current(2)
        self.addCleanup(texts.set_language, "fr")
        with (
            mock.patch("vigie.autostart_command", return_value=None),
            mock.patch("vigie.set_autostart") as set_autostart,
        ):
            dialog.autostart.set(True)
            dialog.submit()
        config = self.app.config
        self.assertEqual(
            (config["lead_minutes"], config["agenda_days"], config["silence_after_minutes"], config["ignore_free"]),
            (15, 3, 5, True),
        )
        self.assertTrue(config["sound"].lower().endswith("ring02.wav"))
        self.assertEqual((config["language"], texts.language()), ("en", "en"))
        set_autostart.assert_called_once_with(True)
        self.assertNotIn("settings", self.app.dialogs)
        self.assertEqual(self.save_json.call_args.args[1]["lead_minutes"], 15)

    def test_out_of_range_numbers_are_brought_back(self):
        self.app.show_settings()
        dialog = self.app.dialogs["settings"]
        agenda = dialog.nametowidget(dialog.notebook.tabs()[1])
        entry = [
            control
            for cell in agenda.winfo_children()[0].winfo_children()
            for control in cell.winfo_children()
            if isinstance(control, vigie.tk.Spinbox)
        ][0]
        for typed, kept in (("999", 120), ("-3", 0), ("abc", 10), ("25", 25)):
            entry.delete(0, "end")
            entry.insert(0, typed)
            self.assertEqual(dialog.lead(), kept)

    def test_ring_mode_notifies_once_without_a_window(self):
        self.app.config["alert_mode"] = "ring"
        self.app.on_events("a", [event("soon", self.now + timedelta(minutes=4))])
        with mock.patch("vigie.play_once"):
            self.tick()
            self.tick()
        self.assertFalse(self.app.windows)
        self.assertFalse(self.app.sound_playing)
        self.app.tray.notify.assert_called_once()
        self.assertIn("soon", self.app.acked)

    def test_a_second_alert_when_the_appointment_starts(self):
        self.app.config["alert_at_start"] = True
        soon = event("soon", self.now + timedelta(minutes=4))
        self.app.on_events("a", [soon])
        self.tick()
        self.app.windows["soon"].stop()
        self.tick()
        self.assertFalse(self.app.windows)
        started = event("soon", self.now - timedelta(seconds=30))
        self.app.acked["soon"] = started.start.isoformat()
        self.app.on_events("a", [started])
        self.tick()
        self.assertEqual(list(self.app.windows), ["soon" + vigie.START_SUFFIX])

    def test_free_and_unanswered_appointments_can_stay_silent(self):
        free = vigie.replace(event("free", self.now), free=True)
        unanswered = vigie.replace(event("invite", self.now), unanswered=True)
        config = {**self.app.config, "ignore_free": True, "ignore_unanswered": True}
        self.assertEqual(vigie.ringable_events([free, unanswered], config), [])
        config.update(ignore_free=False, ignore_unanswered=False)
        self.assertEqual(vigie.ringable_events([free, unanswered], config), [free, unanswered])

    def test_sound_stops_by_itself_but_the_window_stays(self):
        self.app.config["silence_after_minutes"] = 2
        self.app.on_events("a", [event("soon", self.now + timedelta(minutes=4))])
        self.tick()
        self.assertTrue(self.app.sound_playing)
        self.app.ringing_since = self.now - timedelta(minutes=3)
        self.tick()
        self.assertFalse(self.app.sound_playing)
        self.assertEqual(list(self.app.windows), ["soon"])

    def test_free_appointments_ring_unless_told_otherwise(self):
        start = self.now + timedelta(minutes=4)
        free = Event("free", start, start + timedelta(hours=1), "FYI", "", "cal", free=True)
        self.app.config["ignore_free"] = True
        self.app.on_events("a", [free])
        self.tick()
        self.assertFalse(self.app.windows)
        self.app.config["ignore_free"] = False
        self.tick()
        self.assertEqual(list(self.app.windows), ["free"])

    def test_clicking_the_icon_opens_the_agenda_without_a_bold_menu_entry(self):
        default = [entry for entry in self.app.build_menu().items if entry.default]
        self.assertEqual([entry.visible for entry in default], [False])
        default[0](None)
        self.app.inbox.get_nowait()()
        self.assertIn("agenda", self.app.dialogs)

    # --- slack

    def slack_message(self, ts, kind="dm", author="Ana", triggers=("dm",)):
        conversation = "#dev" if "channel" in kind else ""
        return slack_alerts.SlackMessage(f"D{kind}", ts, author, kind, conversation, False, triggers=frozenset(triggers))

    def connect_slack(self, unseen):
        self.app.slack = mock.Mock(**{"unseen.side_effect": unseen, "do_not_disturb.return_value": False})
        self.app.slack.link.return_value = "slack://channel?team=T1&id=Ddm"
        self.app.background = lambda work, done: done(work())
        self.app.config["slack_delay_minutes"] = 5

    def test_one_alarm_for_the_messages_still_unread_after_the_delay(self):
        self.connect_slack(unseen=lambda messages: messages[1:])
        first = self.slack_message("100.0")
        second = self.slack_message("101.0", kind="channel", author="Yann", triggers=("mention",))
        with mock.patch("vigie.play_once") as play_once:
            self.app.on_slack_message(first)
            self.app.on_slack_message(second)
        self.assertEqual(play_once.call_count, 2)
        self.tick()
        self.assertFalse(self.app.windows)
        self.app.slack.unseen.assert_not_called()

        self.app.slack_group["deadline"] = self.now - timedelta(seconds=1)
        self.tick()
        self.app.slack.unseen.assert_called_once_with([first, second])
        (window,) = self.app.windows.values()
        self.assertIsInstance(window, vigie.SlackAlarmWindow)
        shown = self.labels(window)
        self.assertIn("1 message Slack non lu", shown)
        self.assertIn("Yann", shown)
        self.assertIn("#dev", shown)
        self.assertNotIn("Ana", shown)
        self.assertTrue(self.app.sound_playing)
        self.assertIsNone(self.app.slack_group)

        # Read meanwhile: the alarm closes by itself.
        self.app.slack.unseen.side_effect = lambda messages: []
        self.app.slack_recheck_at = 0
        self.tick()
        self.assertFalse(self.app.windows)
        self.assertFalse(self.app.sound_playing)

    def test_nothing_rings_when_everything_was_read_in_time(self):
        self.connect_slack(unseen=lambda messages: [])
        with mock.patch("vigie.play_once"):
            self.app.on_slack_message(self.slack_message("100.0"))
        self.app.slack_group["deadline"] = self.now - timedelta(seconds=1)
        self.tick()
        self.assertFalse(self.app.windows)

    def test_do_not_disturb_silences_slack(self):
        self.connect_slack(unseen=lambda messages: messages)
        self.app.slack.do_not_disturb.return_value = True
        self.app.slack_received(self.slack_message("100.0"))
        self.assertTrue(self.app.inbox.empty())

    def test_open_slack_goes_to_the_conversation(self):
        self.connect_slack(unseen=lambda messages: messages)
        self.app.ring_slack([self.slack_message("100.0")])
        (window,) = self.app.windows.values()
        with mock.patch("vigie.os.startfile") as startfile:
            window.open()
        startfile.assert_called_once_with("slack://channel?team=T1&id=Ddm")
        self.assertFalse(self.app.windows)
        # An appointment sync does not trip over the Slack window.
        self.app.ring_slack([self.slack_message("101.0")])
        self.app.on_events("a", [])
        self.assertEqual(len(self.app.windows), 1)

    def test_each_trigger_does_what_its_action_says(self):
        self.connect_slack(unseen=lambda messages: messages)
        self.app.config["slack_actions"] = {**self.app.config["slack_actions"], "group": "sound", "keyword": "alarm"}
        with mock.patch("vigie.play_once") as play_once:
            self.app.on_slack_message(self.slack_message("100.0", kind="group-dm", triggers=("group",)))
            self.assertEqual(play_once.call_count, 1)
            self.assertIsNone(self.app.slack_group)
            self.app.on_slack_message(self.slack_message("101.0", kind="channel", triggers=("keyword",)))
            self.assertEqual(play_once.call_count, 1)
            self.assertEqual(len(self.app.slack_group["messages"]), 1)
            self.app.on_slack_message(self.slack_message("102.0", kind="channel", triggers=("broadcast",)))
            # Several triggers: the strongest action wins.
            self.app.on_slack_message(self.slack_message("103.0", kind="group-dm", triggers=("group", "keyword")))
        self.assertEqual(play_once.call_count, 2)
        self.assertEqual([m.ts for m in self.app.slack_group["messages"]], ["101.0", "103.0"])

    def test_slack_stays_quiet_outside_the_alert_hours(self):
        config = {**self.app.config, "slack_hours_only": True, "slack_hours": [8, 19], "slack_weekdays_only": True}
        monday, saturday = datetime(2026, 10, 12), datetime(2026, 10, 17)
        self.assertTrue(vigie.hours_open(config, monday.replace(hour=8)))
        self.assertFalse(vigie.hours_open(config, monday.replace(hour=19)))
        self.assertFalse(vigie.hours_open(config, saturday.replace(hour=10)))
        self.assertTrue(vigie.hours_open({**config, "slack_hours": [22, 6]}, monday.replace(hour=2)))
        self.assertTrue(vigie.hours_open({**config, "slack_hours_only": False}, monday.replace(hour=23)))
        self.connect_slack(unseen=lambda messages: messages)
        self.app.config.update(slack_hours_only=True, slack_hours=[0, 0])
        self.app.slack_received(self.slack_message("100.0"))
        self.assertTrue(self.app.inbox.empty())

    def test_do_not_disturb_can_be_ignored(self):
        self.connect_slack(unseen=lambda messages: messages)
        self.app.slack.do_not_disturb.return_value = True
        self.app.config["slack_respect_dnd"] = False
        self.app.slack_received(self.slack_message("100.0"))
        self.assertFalse(self.app.inbox.empty())

    def test_a_slack_alarm_rings_with_its_own_sound(self):
        self.connect_slack(unseen=lambda messages: messages)
        self.app.config["slack_alarm_sound"] = __file__
        self.app.ring_slack([self.slack_message("100.0")])
        self.assertEqual(self.PlaySound.call_args.args[0], __file__)

    def test_no_vip_treatment_when_turned_off(self):
        self.connect_slack(unseen=lambda messages: messages)
        vip = slack_alerts.SlackMessage("Ddm", "100.0", "Jakez", "dm", "", False, vip=True, triggers=frozenset({"dm"}))
        with mock.patch("vigie.announce") as announce, mock.patch("vigie.play_once"):
            self.app.on_slack_message(vip)
        announce.assert_not_called()
        self.assertEqual(len(self.app.slack_group["messages"]), 1)

    def test_a_vip_message_is_announced_once_a_minute_and_never_rings(self):
        self.connect_slack(unseen=lambda messages: messages)
        self.app.config["slack_vip_enabled"] = True
        vip = slack_alerts.SlackMessage("Ddm", "100.0", "Jakez", "dm", "", False, vip=True)
        with mock.patch("vigie.announce") as announce, mock.patch("vigie.play_once") as play_once:
            self.app.on_slack_message(vip)
            self.app.on_slack_message(slack_alerts.SlackMessage("Ddm", "101.0", "Jakez", "dm", "", False, vip=True))
        announce.assert_called_once_with(self.app.config["slack_vip_sound"], "Message VIP", with_sound=True)
        play_once.assert_not_called()
        self.assertIsNone(self.app.slack_group)
        self.app.vip_announced["Jakez"] -= vigie.VIP_QUIET_SECONDS
        with mock.patch("vigie.announce") as announce:
            self.app.on_slack_message(vip)
        announce.assert_called_once()

    def test_saving_tokens_turns_slack_on(self):
        with mock.patch.object(self.app, "start_slack") as start_slack:
            self.app.save_slack_tokens("xapp-1", "xoxp-1")
        self.keyring.set_password.assert_any_call("vigie:slack:app", "secret", "xapp-1")
        self.keyring.set_password.assert_any_call("vigie:slack:user", "secret", "xoxp-1")
        self.assertTrue(self.app.config["slack_enabled"])
        start_slack.assert_called_once()

    def test_slack_settings_are_saved(self):
        self.app.show_settings()
        dialog = self.app.dialogs["settings"]
        dialog.slack_enabled.set(True)
        dialog.slack_delay = lambda: 3
        dialog.slack_vip.insert(0, "Jakez, Jakez Rolland ,")
        dialog.slack_vip_enabled.set(True)
        dialog.slack_actions["group"].current(vigie.SLACK_ACTIONS.index("sound"))
        dialog.slack_lists["channel"].insert(0, "#alertes-prod, dev")
        dialog.slack_lists["keyword"].insert(0, "urgent")
        dialog.alert_mode.set("ring")
        with (
            mock.patch("vigie.autostart_command", return_value=None),
            mock.patch.object(self.app, "start_slack"),
        ):
            dialog.submit()
        self.assertEqual((self.app.config["slack_enabled"], self.app.config["slack_delay_minutes"]), (True, 3))
        self.assertTrue(self.app.config["slack_sound"].lower().endswith(".wav"))
        self.assertEqual(self.app.config["slack_vip_names"], ["Jakez", "Jakez Rolland"])
        self.assertTrue(self.app.config["slack_vip_enabled"])
        self.assertIsNone(self.app.config["slack_vip_phrase"])
        self.assertEqual(self.app.config["slack_actions"]["group"], "sound")
        self.assertEqual(self.app.config["slack_actions"]["dm"], "sound_alarm")
        self.assertEqual(self.app.config["slack_channels"], ["alertes-prod", "dev"])
        self.assertEqual(self.app.config["slack_keywords"], ["urgent"])
        self.assertEqual(self.app.config["alert_mode"], "ring")
        self.assertTrue(self.app.config["slack_vip_sound"].lower().endswith(".wav"))

    # --- Zoom

    def test_zoom_settings_are_saved(self):
        self.app.show_settings()
        dialog = self.app.dialogs["settings"]
        dialog.zoom_enabled.set(True)
        dialog.zoom_actions["channel"].current(vigie.ZOOM_ACTIONS.index("sound"))
        dialog.zoom_lists["channel"].insert(0, "*")
        dialog.zoom_lists["dm"].insert(0, "Ana@X.test, ")
        with (
            mock.patch("vigie.autostart_command", return_value=None),
            mock.patch.object(self.app, "start_slack"),
            mock.patch.object(self.app, "start_zoom") as start_zoom,
        ):
            dialog.submit()
        start_zoom.assert_called_once()
        config = self.app.config
        self.assertTrue(config["zoom_enabled"])
        self.assertEqual((config["zoom_actions"]["channel"], config["zoom_actions"]["mention"]), ("sound", "sound"))
        self.assertEqual((config["zoom_channels"], config["zoom_contacts"]), (["*"], ["ana@x.test"]))
        self.assertEqual(config["zoom_hours"], [8, 19])

    def zoom_message(self, *triggers, vip=False):
        return zoom_alerts.ZoomMessage("m1", "Jakez", "channel", "dev", False, vip=vip, triggers=frozenset(triggers))

    def test_a_zoom_message_plays_its_sound_and_never_rings(self):
        self.app.config["zoom_actions"] = {**self.app.config["zoom_actions"], "channel": "sound"}
        with mock.patch("vigie.play_once") as play_once:
            self.app.on_zoom_message(self.zoom_message("keyword"))
            play_once.assert_not_called()
            self.app.on_zoom_message(self.zoom_message("channel", "keyword"))
        play_once.assert_called_once_with(self.app.config["zoom_sound"])
        self.assertFalse(self.app.windows)

    def test_zoom_vip_messages_are_announced_like_slack_ones(self):
        self.app.config["slack_vip_enabled"] = True
        with mock.patch("vigie.announce") as announce, mock.patch("vigie.play_once") as play_once:
            self.app.on_zoom_message(self.zoom_message(vip=True))
        announce.assert_called_once_with(self.app.config["slack_vip_sound"], "Message VIP", with_sound=True)
        play_once.assert_not_called()

    def test_zoom_stays_silent_outside_its_hours(self):
        self.app.config.update(zoom_hours_only=True, zoom_hours=[0, 0])
        self.app.zoom_received(self.zoom_message("dm"))
        self.assertTrue(self.app.inbox.empty())

    def test_a_refused_zoom_authorization_asks_for_a_new_one(self):
        self.app.zoom = mock.Mock()
        self.app.zoom.thread.is_alive.return_value = False
        self.app.zoom_state = "connected"
        self.app.zoom_tick()
        self.assertEqual((self.app.zoom, self.app.zoom_state), (None, "no_tokens"))

    # --- agenda

    def labels(self, widget):
        found = [widget.cget("text")] if isinstance(widget, vigie.tk.Label) else []
        for child in widget.winfo_children():
            found.extend(self.labels(child))
        return found

    def test_agenda_lists_every_calendar_by_day_in_the_chosen_language(self):
        self.app.config["accounts"].append(self.feed)
        self.app.on_discovery("a", {"url/mine": "Perso"}, "Me")
        noon = self.now.replace(hour=12, minute=0, second=0, microsecond=0)
        self.app.on_events("a", [Event("work", noon, noon + timedelta(hours=1), "Point projet", "Salle 2", "Perso")])
        holiday = noon.replace(hour=0) + timedelta(days=1)
        self.app.on_events("g", [Event("off", holiday, holiday + timedelta(days=1), "Férié", "", "Google", all_day=True)])
        self.assertEqual(self.app.watched_calendars(), ["Perso", "Google"])

        self.app.show_agenda()
        self.app.show_agenda()
        self.app.root.update()
        window = self.app.dialogs["agenda"]
        shown = self.labels(window.days)
        self.assertEqual(sum(text.startswith(("Aujourd'hui", "Demain")) for text in shown), 2)
        self.assertEqual(shown.count("Rien de prévu"), self.app.config["agenda_days"] - 2)
        for expected in ("Point projet", "Salle 2  ·  Perso", "Férié", "Journée", "12:00", "13:00"):
            self.assertIn(expected, shown)
        self.assertEqual(self.labels(window.legend), ["Perso", "Google"])

        # A sync redraws the open window.
        self.app.on_events("a", [])
        self.assertNotIn("Point projet", self.labels(window.days))
        self.app.set_language("en")
        self.addCleanup(texts.set_language, "fr")
        self.assertNotIn("agenda", self.app.dialogs)
        self.app.show_agenda()
        self.assertIn("All day", self.labels(self.app.dialogs["agenda"].days))

    def test_agenda_without_any_account_offers_to_add_one(self):
        self.app.config["accounts"] = []
        self.app.show_agenda()
        self.assertEqual(self.labels(self.app.dialogs["agenda"].days), ["Ajoutez un agenda pour voir vos rendez-vous ici."])

    # --- health

    def test_health_turns_red_as_soon_as_one_account_goes_stale(self):
        self.app.config["accounts"].append(self.feed)
        self.app.on_events("a", [])
        self.tick()
        self.assertFalse(self.app.healthy)
        self.app.on_events("g", [])
        self.tick()
        self.assertTrue(self.app.healthy)
        self.assertTrue(self.app.status_text().startswith("Dernière synchro"))

        self.app.last_sync["g"] = self.now - timedelta(minutes=10)
        self.tick()
        self.tick()
        self.assertFalse(self.app.healthy)
        self.app.tray.notify.assert_called_once()
        self.assertIn("Google", self.app.tray.notify.call_args.args[0])

    def test_a_calendar_just_added_is_not_reported_as_broken(self):
        self.app.on_events("a", [])
        self.tick()
        self.app.save_ics_account(None, PROVIDER["google"], "Google", "https://calendar.test/basic.ics")
        added = self.app.config["accounts"][1]
        self.tick()
        # Red until its first sync, but no warning yet.
        self.assertFalse(self.app.healthy)
        self.app.tray.notify.assert_not_called()
        self.app.on_events(added["id"], [])
        self.tick()
        self.assertTrue(self.app.healthy)

        # It only becomes a warning when the first sync never comes.
        del self.app.last_sync[added["id"]]
        self.app.watched_since[added["id"]] = self.now - timedelta(minutes=10)
        self.tick()
        self.app.tray.notify.assert_called_once()

    def test_no_sync_since_startup_ends_up_reported(self):
        self.tick()
        self.app.tray.notify.assert_not_called()
        self.app.started = self.now - timedelta(minutes=10)
        self.tick()
        self.app.tray.notify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
