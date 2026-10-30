"""Everything the user reads, in French and in English, and the calendar providers on offer."""

import ctypes

LANGUAGES = {"fr": "Français", "en": "English"}

# kind "caldav": server + login + password; kind "ics": one secret address per calendar.
# The name and the instructions of each provider are the strings provider_<key> and help_<key>.
PROVIDERS = [
    {"key": "infomaniak", "kind": "caldav", "url": "https://sync.infomaniak.com"},
    {"key": "google", "kind": "ics"},
    {"key": "outlook", "kind": "ics"},
    {"key": "icloud", "kind": "caldav", "url": "https://caldav.icloud.com"},
    {"key": "yahoo", "kind": "caldav", "url": "https://caldav.calendar.yahoo.com"},
    {"key": "fastmail", "kind": "caldav", "url": "https://caldav.fastmail.com/dav/"},
    {"key": "nextcloud", "kind": "caldav", "url": "https://"},
    {"key": "caldav", "kind": "caldav", "url": "https://"},
    {"key": "ics", "kind": "ics"},
]

STRINGS = {
    "fr": {
        # Providers
        "provider_infomaniak": "Infomaniak (kSuite, Kalendar)",
        "provider_google": "Google Agenda",
        "provider_outlook": "Outlook / Microsoft 365",
        "provider_icloud": "Apple iCloud",
        "provider_yahoo": "Yahoo",
        "provider_fastmail": "Fastmail",
        "provider_nextcloud": "Nextcloud",
        "provider_caldav": "Autre serveur CalDAV",
        "provider_ics": "Autre adresse iCal (.ics)",
        "help_infomaniak": (
            "Saisissez votre identifiant de synchronisation (du type AB12345) et un mot de passe "
            "d'application. Les deux se trouvent sur config.infomaniak.com : « Mes Contacts & Agendas » → "
            "« Synchronisation manuelle »."
        ),
        "help_google": (
            "Collez l'adresse secrète de l'agenda. Dans Google Agenda : Paramètres → votre agenda → "
            "« Intégrer l'agenda » → « Adresse secrète au format iCal ». Cette adresse donne accès en "
            "lecture à l'agenda : ne la partagez pas."
        ),
        "help_outlook": (
            "Collez le lien ICS de l'agenda publié. Dans Outlook sur le web : Paramètres → Calendrier → "
            "Calendriers partagés → « Publier un calendrier », choisissez l'agenda et « Peut afficher tous "
            "les détails », puis copiez le lien ICS. Toute personne possédant ce lien peut lire l'agenda : "
            "ne le partagez pas."
        ),
        "help_icloud": (
            "Identifiant : l'adresse e-mail de votre compte Apple. Mot de passe : un mot de passe pour "
            "application, à créer sur account.apple.com (« Connexion et sécurité » → « Mots de passe pour "
            "applications »). La validation en deux étapes doit être activée."
        ),
        "help_yahoo": (
            "Identifiant : votre adresse Yahoo. Mot de passe : un mot de passe d'application, à créer dans "
            "les réglages de sécurité de votre compte Yahoo (« Générer un mot de passe d'application »)."
        ),
        "help_fastmail": (
            "Identifiant : votre adresse Fastmail. Mot de passe : un mot de passe d'application donnant "
            "accès à « Calendars (CalDAV) », à créer dans Settings → Privacy & Security → Integrations."
        ),
        "help_nextcloud": (
            "Serveur : l'adresse de votre Nextcloud suivie de /remote.php/dav, par exemple "
            "https://cloud.exemple.fr/remote.php/dav. Identifiant : votre nom d'utilisateur. Mot de passe : "
            "un mot de passe d'application, à créer dans Paramètres → Sécurité."
        ),
        "help_caldav": (
            "Saisissez l'adresse CalDAV du serveur, votre identifiant et votre mot de passe (de préférence "
            "un mot de passe d'application)."
        ),
        "help_ics": (
            "Collez l'adresse iCal (.ics) de l'agenda, commençant par https://. Si elle est privée, elle "
            "donne accès en lecture à l'agenda : ne la partagez pas."
        ),
        # Settings windows
        "title_accounts": "Agendas synchronisés",
        "title_calendars": "Agendas surveillés",
        "accounts_intro": "Ajoutez des agendas à synchroniser",
        "no_account": "Aucun agenda pour l'instant.",
        "add_calendar": "Ajouter un agenda :",
        "add": "Ajouter…",
        "close": "Fermer",
        "remove": "Supprimer",
        "edit": "Modifier…",
        "calendars_button": "Agendas…",
        "remove_question": "Supprimer « {name} » ? Ses rendez-vous ne sonneront plus.",
        "server": "Serveur",
        "username": "Identifiant",
        "app_password": "Mot de passe d'application",
        "calendar_name": "Nom de l'agenda",
        "ics_address": "Adresse iCal",
        "test_and_save": "Tester et enregistrer",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "testing": "Test de la connexion…",
        "refused_input": "Refusé par le serveur : vérifiez votre saisie.",
        "connection_failed": "Connexion impossible : {error}",
        "three_required": "Les trois champs sont obligatoires.",
        "no_calendar_found": "Connexion réussie, mais aucun agenda trouvé.",
        "ics_invalid": "Il faut un nom et une adresse commençant par https://.",
        "not_ical": "Cette adresse ne renvoie pas un agenda au format iCal.",
        "choose_calendars": "{name}\nCochez les agendas dont les rendez-vous doivent sonner.",
        "at_least_one": "Cochez au moins un agenda.",
        "refused_caldav": (
            "{name} : le serveur refuse le mot de passe enregistré (révoqué ou expiré). Les alarmes de ce "
            "compte sont suspendues tant qu'il n'est pas remplacé."
        ),
        "refused_ics": (
            "{name} : le serveur refuse l'adresse iCal enregistrée (réinitialisée ou supprimée). Les alarmes "
            "de cet agenda sont suspendues tant qu'elle n'est pas remplacée."
        ),
        # Settings
        "title_settings": "Paramètres",
        "settings_intro": "Options générales, alertes des rendez-vous et des messageries",
        "tab_general": "Général",
        "tab_agenda": "Agenda",
        "tab_slack": "Slack",
        "tab_messaging": "Messageries",
        "section_interface": "Interface",
        "section_startup": "Démarrage",
        "section_alert_mode": "Type d'alerte",
        "alert_mode_alarm": "Alarme : une fenêtre et la sonnerie en boucle, jusqu'à « Arrêter » ou « Rappel »",
        "alert_mode_ring": "Sonnerie : un son et une notification Windows, sans fenêtre",
        "section_triggers": "Déclenchement",
        "lead_label": "Prévenir",
        "unit_minutes_before": "minutes avant le début",
        "alert_at_start": "Prévenir aussi au début du rendez-vous",
        "late_grace_label": "Rendez-vous découvert en retard",
        "unit_minutes_after": "minutes après le début, au plus",
        "ignore_unanswered": "Ignorer les invitations auxquelles vous n'avez pas répondu",
        "section_sound": "Son",
        "section_display": "Affichage et synchronisation",
        "ring_notification": "{time} · {location}",
        "section_connection": "Connexion",
        "section_slack_triggers": "Déclencheurs",
        "slack_action_header": "Action",
        "slack_action_none": "Rien",
        "slack_action_sound": "Son",
        "slack_action_alarm": "Alarme si non lu",
        "slack_action_sound_alarm": "Son + alarme si non lu",
        "slack_trigger_dm": "Message privé",
        "slack_trigger_mention": "Mention @moi",
        "slack_trigger_reply": "Réponse à vos messages (fil)",
        "slack_trigger_group": "Conversation de groupe",
        "slack_trigger_broadcast": "@here, @channel",
        "slack_trigger_keyword": "Mots-clés",
        "slack_trigger_channel": "Canaux suivis",
        "slack_triggers_hint": (
            "Mention @moi : dans un canal, un groupe ou un fil. Conversation de groupe et canaux suivis : tous "
            "leurs messages. Listes séparées par des virgules. Si un message correspond à plusieurs lignes, "
            "l'action la plus forte s'applique."
        ),
        "section_slack_alarm": "Son et alarme",
        "slack_alarm_sound_label": "Sonnerie de l'alarme",
        "section_slack_when": "Quand",
        "slack_respect_dnd": "Respecter le « Ne pas déranger » de Slack",
        "slack_hours_from": "Seulement de",
        "slack_hours_to": "h à",
        "slack_hours_unit": "h",
        "slack_weekdays_only": "Seulement du lundi au vendredi",
        "section_vip": "Personnes VIP",
        "slack_vip_enable": "Annoncer les messages des personnes VIP",
        "slack_vip_voice_label": "Puis une voix dit",
        "snooze_label": "Durée d'un rappel",
        "unit_minutes": "minutes",
        "sound_label": "Sonnerie",
        "sound_preview": "Écouter",
        "sound_browse": "Parcourir…",
        "wav_files": "Fichiers audio WAV",
        "silence_label": "Couper le son après",
        "never": "Jamais",
        "minutes_value": "{minutes} min",
        "ignore_free": "Ignorer les rendez-vous marqués « Disponible »",
        "slack_status_label": "État",
        "slack_tokens_button": "Jetons Slack…",
        "slack_enable": "Activer les alertes Slack",
        "slack_delay_label": "Alarme si non lu après",
        "slack_sound_label": "Son à la réception",
        "slack_vip_label": "Noms",
        "slack_vip_hint": (
            "Noms séparés par des virgules. Tous leurs messages sont annoncés, même sans tag, jamais par une alarme ; "
            "ils passent avant les déclencheurs."
        ),
        "slack_vip_sound_label": "Son",
        "slack_vip_voice": "Message VIP",
        "agenda_days_label": "Jours affichés",
        "unit_days": "jours",
        "show_all_day": "Afficher les événements « toute la journée »",
        "language": "Langue",
        "language_auto": "Celle de Windows",
        "poll_label": "Relire les agendas toutes les",
        "autostart": "Lancer au démarrage de Windows",
        # Slack
        "slack_status_off": "désactivé",
        "slack_status_no_tokens": "jetons à saisir",
        "slack_status_connecting": "connexion…",
        "slack_status_connected": "connecté",
        "slack_status_disconnected": "non connecté",
        "slack_menu_status": "Slack : {state}",
        "slack_tokens_title": "Jetons Slack",
        "slack_tokens_help": (
            "Les deux jetons de votre application Slack « Vigie », sur api.slack.com/apps. App-Level Token : "
            "« Basic Information » → « App-Level Tokens ». User OAuth Token : « OAuth & Permissions »."
        ),
        "app_token": "App-Level Token (xapp-…)",
        "user_token": "User OAuth Token (xoxp-…)",
        "slack_error_format": "Le premier jeton doit commencer par xapp-, le second par xoxp-.",
        "slack_error_user": "Slack refuse le User OAuth Token.",
        "slack_error_app": "Slack refuse l'App-Level Token (permission connections:write ?).",
        "slack_alarm_title": "Slack",
        "slack_unread_one": "1 message Slack non lu",
        "slack_unread_many": "{count} messages Slack non lus",
        "slack_unread_since": "Toujours pas lu après {minutes} min",
        "slack_dm": "Message privé",
        "slack_group": "Conversation de groupe",
        "slack_thread": "dans un fil",
        "open_slack": "Ouvrir Slack",
        # Zoom
        "tab_zoom": "Zoom",
        "zoom_enable": "Activer les alertes Zoom",
        "zoom_connect_button": "Connecter Zoom…",
        "zoom_trigger_dm": "Messages privés de",
        "zoom_trigger_mention": "Mention @moi",
        "zoom_trigger_reply": "Réponse à vos messages",
        "zoom_trigger_broadcast": "@all",
        "zoom_trigger_keyword": "Mots-clés",
        "zoom_trigger_channel": "Canaux suivis",
        "zoom_triggers_hint": (
            "Messages privés : adresses e-mail des contacts, séparées par des virgules. Canaux suivis : leurs noms, "
            "ou * pour tous. Zoom ne dit pas si un message a été lu : pas d'alarme, seulement un son, environ "
            "30 secondes après le message."
        ),
        "vip_intro": "Valable pour toutes les messageries : Slack, Zoom, Mail.",
        "zoom_menu_status": "Zoom : {state}",
        "zoom_connect_title": "Connecter Zoom",
        "zoom_connect_help": (
            "Le Public Client ID de votre application Zoom « Vigie » (marketplace.zoom.us, page Basic Information, "
            "« Use Public Client OAuth » activé, adresse de redirection {redirect}). Le navigateur s'ouvre ensuite "
            "pour que vous autorisiez l'application."
        ),
        "zoom_client_id": "Public Client ID",
        "zoom_connect_submit": "Se connecter",
        "zoom_client_id_missing": "Saisissez le Public Client ID.",
        "zoom_waiting": "Autorisez l'application dans le navigateur (5 minutes au plus)…",
        "zoom_error": "Zoom refuse l'autorisation : {error}",
        "zoom_done_page": "Vigie est connectée à Zoom. Vous pouvez fermer cet onglet.",
        # Mail
        "tab_mail": "Mail",
        "mail_enable": "Activer les alertes mail",
        "mail_say_sender": "Annoncer l'expéditeur (voix et notification)",
        "mail_from": "Mail de {name}",
        "mail_from_many": "{count} mails de {names}",
        "mail_no_subject": "(sans objet)",
        "mail_account_button": "Compte mail…",
        "mail_status_no_account": "compte à saisir",
        "mail_trigger_all": "Tout nouveau mail",
        "mail_trigger_vip": "Mail d'une personne VIP",
        "mail_trigger_keyword": "Mots-clés dans le sujet",
        "mail_triggers_hint": (
            "Seule la boîte de réception est lue, environ 30 secondes après l'arrivée du mail, sans jamais marquer "
            "un mail comme lu. Une personne VIP (reconnue à son nom ou à son adresse) est toujours annoncée par la "
            "voix ; cette ligne dit seulement ce qui s'y ajoute."
        ),
        "mail_menu_status": "Mail : {state}",
        "mail_account_title": "Compte mail",
        "mail_account_help": (
            "Votre adresse et votre mot de passe mail (IMAP). Si la double authentification est active sur votre "
            "compte Infomaniak, créez un mot de passe d'application. Le mot de passe reste dans le Gestionnaire "
            "d'identifications de Windows."
        ),
        "mail_host": "Serveur IMAP",
        "mail_username": "Adresse",
        "mail_password": "Mot de passe",
        "mail_error_missing": "Saisissez le serveur, l'adresse et le mot de passe.",
        "mail_error_refused": "Le serveur refuse cette adresse ou ce mot de passe.",
        "mail_alarm_title": "Mail",
        "mail_unread_one": "1 mail non lu",
        "mail_unread_many": "{count} mails non lus",
        "open_mail": "Ouvrir la messagerie",
        # Account states
        "synced_at": "Synchronisé à {time}",
        "failing": "En échec : {error}",
        "refused_short": "refusé par le serveur",
        "none_chosen": "Aucun agenda choisi",
        "waiting": "En attente de synchronisation",
        # Alarm
        "alarm_title": "Rendez-vous",
        "in_minutes": "Rendez-vous dans {minutes} min",
        "now": "Rendez-vous maintenant",
        "started_since": "Rendez-vous commencé depuis {minutes} min",
        "stop": "Arrêter",
        "snooze": "Rappel {minutes} min",
        "untitled": "(sans titre)",
        "test_event": "Test de l'alarme",
        "test_calendar": "Test",
        # Agenda
        "agenda_title": "Agenda",
        "agenda_subtitle": "Les {days} prochains jours",
        "today": "Aujourd'hui",
        "tomorrow": "Demain",
        "nothing_planned": "Rien de prévu",
        "all_day": "Journée",
        "ongoing": "en cours",
        "in_min": "dans {minutes} min",
        "in_hours": "dans {hours} h",
        "agenda_no_account": "Ajoutez un agenda pour voir vos rendez-vous ici.",
        # Tray
        "menu_agenda": "Agenda",
        "not_configured": "Aucun agenda configuré",
        "account_state": "{name} : {state}",
        "last_sync": "Dernière synchro : {time}",
        "no_upcoming": "Aucun rendez-vous dans les 24 h",
        "next_event": "Prochain : {time} {title}",
        "sync_now": "Synchroniser maintenant",
        "test_alarm": "Tester l'alarme",
        "menu_accounts": "Agendas synchronisés…",
        "menu_settings": "Paramètres…",
        "menu_dashboard": "Tableau de bord",
        "dashboard_title": "Tableau de bord",
        "section_state": "État",
        "section_next": "Prochaine alerte de rendez-vous",
        "section_history": "Dernières alertes",
        "no_upcoming_alert": "Aucun rendez-vous à venir dans les jours affichés",
        "next_alert": "{day}{time} {title} · alerte à {alert}",
        "history_empty": "Aucune alerte depuis le démarrage de Vigie à {time}.",
        "history_alarm": "alarme",
        "history_ring": "sonnerie",
        "history_sound": "son",
        "history_sound_wait": "son, alarme si non lu dans {minutes} min",
        "history_wait": "alarme si non lu dans {minutes} min",
        "history_vip": "annonce VIP",
        "history_read": "lu à temps, pas d'alarme",
        "history_read_count": "{count} message(s) lu(s) avant le délai",
        "history_quiet_hours": "ignoré : hors horaires",
        "history_dnd": "ignoré : Ne pas déranger",
        "open_log": "Ouvrir le journal",
        "quit": "Quitter",
        "stale_notification": "Agenda non synchronisé ({names}) : les alarmes ne sont plus fiables.",
    },
    "en": {
        # Providers
        "provider_infomaniak": "Infomaniak (kSuite, Kalendar)",
        "provider_google": "Google Calendar",
        "provider_outlook": "Outlook / Microsoft 365",
        "provider_icloud": "Apple iCloud",
        "provider_yahoo": "Yahoo",
        "provider_fastmail": "Fastmail",
        "provider_nextcloud": "Nextcloud",
        "provider_caldav": "Other CalDAV server",
        "provider_ics": "Other iCal address (.ics)",
        "help_infomaniak": (
            "Enter your synchronisation username (like AB12345) and an application password. Both are "
            "shown on config.infomaniak.com: “My Contacts & Calendars” → “Manual synchronisation”."
        ),
        "help_google": (
            "Paste the secret address of the calendar. In Google Calendar: Settings → your calendar → "
            "“Integrate calendar” → “Secret address in iCal format”. This address gives read access to "
            "the calendar: do not share it."
        ),
        "help_outlook": (
            "Paste the ICS link of the published calendar. In Outlook on the web: Settings → Calendar → "
            "Shared calendars → “Publish a calendar”, choose the calendar and “Can view all details”, "
            "then copy the ICS link. Anyone holding this link can read the calendar: do not share it."
        ),
        "help_icloud": (
            "Username: the email address of your Apple Account. Password: an app-specific password, "
            "created on account.apple.com (“Sign-In and Security” → “App-Specific Passwords”). "
            "Two-factor authentication must be turned on."
        ),
        "help_yahoo": (
            "Username: your Yahoo address. Password: an app password, created in the security settings "
            "of your Yahoo account (“Generate app password”)."
        ),
        "help_fastmail": (
            "Username: your Fastmail address. Password: an app password with access to “Calendars "
            "(CalDAV)”, created in Settings → Privacy & Security → Integrations."
        ),
        "help_nextcloud": (
            "Server: the address of your Nextcloud followed by /remote.php/dav, for example "
            "https://cloud.example.com/remote.php/dav. Username: your user name. Password: an app "
            "password, created in Settings → Security."
        ),
        "help_caldav": (
            "Enter the CalDAV address of the server, your username and your password (preferably an "
            "application password)."
        ),
        "help_ics": (
            "Paste the iCal (.ics) address of the calendar, starting with https://. If it is private, it "
            "gives read access to the calendar: do not share it."
        ),
        # Settings windows
        "title_accounts": "Synced calendars",
        "title_calendars": "Watched calendars",
        "accounts_intro": "Add calendars to sync",
        "no_account": "No calendar yet.",
        "add_calendar": "Add a calendar:",
        "add": "Add…",
        "close": "Close",
        "remove": "Remove",
        "edit": "Edit…",
        "calendars_button": "Calendars…",
        "remove_question": "Remove “{name}”? Its events will no longer ring.",
        "server": "Server",
        "username": "Username",
        "app_password": "Application password",
        "calendar_name": "Calendar name",
        "ics_address": "iCal address",
        "test_and_save": "Test and save",
        "save": "Save",
        "cancel": "Cancel",
        "testing": "Testing the connection…",
        "refused_input": "Refused by the server: check what you entered.",
        "connection_failed": "Connection failed: {error}",
        "three_required": "All three fields are required.",
        "no_calendar_found": "Connection succeeded, but no calendar was found.",
        "ics_invalid": "A name and an address starting with https:// are required.",
        "not_ical": "This address does not return a calendar in iCal format.",
        "choose_calendars": "{name}\nTick the calendars whose events must ring.",
        "at_least_one": "Tick at least one calendar.",
        "refused_caldav": (
            "{name}: the server refuses the saved password (revoked or expired). The alarms of this "
            "account are suspended until it is replaced."
        ),
        "refused_ics": (
            "{name}: the server refuses the saved iCal address (reset or deleted). The alarms of this "
            "calendar are suspended until it is replaced."
        ),
        # Settings
        "title_settings": "Settings",
        "settings_intro": "General options, appointment and messaging alerts",
        "tab_general": "General",
        "tab_agenda": "Agenda",
        "tab_slack": "Slack",
        "tab_messaging": "Messaging",
        "section_interface": "Interface",
        "section_startup": "Startup",
        "section_alert_mode": "Alert type",
        "alert_mode_alarm": "Alarm: a window and a looping sound, until “Stop” or “Snooze”",
        "alert_mode_ring": "Ring: one sound and a Windows notification, no window",
        "section_triggers": "Triggers",
        "lead_label": "Alert",
        "unit_minutes_before": "minutes before the start",
        "alert_at_start": "Also alert when the appointment starts",
        "late_grace_label": "Appointment found late",
        "unit_minutes_after": "minutes after the start, at most",
        "ignore_unanswered": "Ignore the invitations you have not answered",
        "section_sound": "Sound",
        "section_display": "Display and sync",
        "ring_notification": "{time} · {location}",
        "section_connection": "Connection",
        "section_slack_triggers": "Triggers",
        "slack_action_header": "Action",
        "slack_action_none": "Nothing",
        "slack_action_sound": "Sound",
        "slack_action_alarm": "Alarm if unread",
        "slack_action_sound_alarm": "Sound + alarm if unread",
        "slack_trigger_dm": "Direct message",
        "slack_trigger_mention": "@me mention",
        "slack_trigger_reply": "Reply to your messages (thread)",
        "slack_trigger_group": "Group conversation",
        "slack_trigger_broadcast": "@here, @channel",
        "slack_trigger_keyword": "Keywords",
        "slack_trigger_channel": "Watched channels",
        "slack_triggers_hint": (
            "@me mention: in a channel, a group or a thread. Group conversation and watched channels: every "
            "message. Lists separated by commas. When a message matches several rows, the strongest action applies."
        ),
        "section_slack_alarm": "Sound and alarm",
        "slack_alarm_sound_label": "Alarm sound",
        "section_slack_when": "When",
        "slack_respect_dnd": "Follow Slack's “Do not disturb”",
        "slack_hours_from": "Only from",
        "slack_hours_to": "to",
        "slack_hours_unit": "o'clock",
        "slack_weekdays_only": "Only Monday to Friday",
        "section_vip": "VIP people",
        "slack_vip_enable": "Announce the messages of VIP people",
        "slack_vip_voice_label": "Then a voice says",
        "snooze_label": "Length of a snooze",
        "unit_minutes": "minutes",
        "sound_label": "Alarm sound",
        "sound_preview": "Listen",
        "sound_browse": "Browse…",
        "wav_files": "WAV audio files",
        "silence_label": "Silence the sound after",
        "never": "Never",
        "minutes_value": "{minutes} min",
        "ignore_free": "Ignore the appointments marked “Free”",
        "slack_status_label": "Status",
        "slack_tokens_button": "Slack tokens…",
        "slack_enable": "Turn Slack alerts on",
        "slack_delay_label": "Alarm if unread after",
        "slack_sound_label": "Sound on arrival",
        "slack_vip_label": "Names",
        "slack_vip_hint": (
            "Names separated by commas. All their messages are announced, even untagged, never by an alarm; "
            "they come before the triggers."
        ),
        "slack_vip_sound_label": "Sound",
        "slack_vip_voice": "VIP message",
        "agenda_days_label": "Days shown",
        "unit_days": "days",
        "show_all_day": "Show all-day events",
        "language": "Language",
        "language_auto": "Same as Windows",
        "poll_label": "Read the calendars again every",
        "autostart": "Start with Windows",
        # Slack
        "slack_status_off": "off",
        "slack_status_no_tokens": "tokens needed",
        "slack_status_connecting": "connecting…",
        "slack_status_connected": "connected",
        "slack_status_disconnected": "not connected",
        "slack_menu_status": "Slack: {state}",
        "slack_tokens_title": "Slack tokens",
        "slack_tokens_help": (
            "The two tokens of your Slack app “Vigie”, on api.slack.com/apps. App-Level Token: “Basic "
            "Information” → “App-Level Tokens”. User OAuth Token: “OAuth & Permissions”."
        ),
        "app_token": "App-Level Token (xapp-…)",
        "user_token": "User OAuth Token (xoxp-…)",
        "slack_error_format": "The first token must start with xapp-, the second with xoxp-.",
        "slack_error_user": "Slack refuses the User OAuth Token.",
        "slack_error_app": "Slack refuses the App-Level Token (connections:write permission?).",
        "slack_alarm_title": "Slack",
        "slack_unread_one": "1 unread Slack message",
        "slack_unread_many": "{count} unread Slack messages",
        "slack_unread_since": "Still unread after {minutes} min",
        "slack_dm": "Direct message",
        "slack_group": "Group conversation",
        "slack_thread": "in a thread",
        "open_slack": "Open Slack",
        # Zoom
        "tab_zoom": "Zoom",
        "zoom_enable": "Turn Zoom alerts on",
        "zoom_connect_button": "Connect Zoom…",
        "zoom_trigger_dm": "Direct messages from",
        "zoom_trigger_mention": "@me mention",
        "zoom_trigger_reply": "Reply to your messages",
        "zoom_trigger_broadcast": "@all",
        "zoom_trigger_keyword": "Keywords",
        "zoom_trigger_channel": "Watched channels",
        "zoom_triggers_hint": (
            "Direct messages: email addresses of the contacts, separated by commas. Watched channels: their names, "
            "or * for all. Zoom does not tell whether a message was read: no alarm, only a sound, about 30 seconds "
            "after the message."
        ),
        "vip_intro": "For every messaging tool: Slack, Zoom, Mail.",
        "zoom_menu_status": "Zoom: {state}",
        "zoom_connect_title": "Connect Zoom",
        "zoom_connect_help": (
            "The Public Client ID of your Zoom app “Vigie” (marketplace.zoom.us, Basic Information page, “Use "
            "Public Client OAuth” on, redirect URL {redirect}). The browser then opens for you to authorize the app."
        ),
        "zoom_client_id": "Public Client ID",
        "zoom_connect_submit": "Connect",
        "zoom_client_id_missing": "Enter the Public Client ID.",
        "zoom_waiting": "Authorize the app in the browser (5 minutes at most)…",
        "zoom_error": "Zoom refuses the authorization: {error}",
        "zoom_done_page": "Vigie is connected to Zoom. You can close this tab.",
        # Mail
        "tab_mail": "Mail",
        "mail_enable": "Turn mail alerts on",
        "mail_say_sender": "Announce the sender (voice and notification)",
        "mail_from": "Mail from {name}",
        "mail_from_many": "{count} messages from {names}",
        "mail_no_subject": "(no subject)",
        "mail_account_button": "Mail account…",
        "mail_status_no_account": "account to enter",
        "mail_trigger_all": "Any new message",
        "mail_trigger_vip": "Message from a VIP person",
        "mail_trigger_keyword": "Keywords in the subject",
        "mail_triggers_hint": (
            "Only the inbox is read, about 30 seconds after a message arrives, and no message is ever marked as "
            "read. A VIP person (recognised by name or address) is always announced by the voice; this row only "
            "says what is added to it."
        ),
        "mail_menu_status": "Mail: {state}",
        "mail_account_title": "Mail account",
        "mail_account_help": (
            "Your mail address and password (IMAP). If two-factor authentication is on for your Infomaniak account, "
            "create an app password. The password stays in the Windows Credential Manager."
        ),
        "mail_host": "IMAP server",
        "mail_username": "Address",
        "mail_password": "Password",
        "mail_error_missing": "Enter the server, the address and the password.",
        "mail_error_refused": "The server refuses this address or password.",
        "mail_alarm_title": "Mail",
        "mail_unread_one": "1 unread message",
        "mail_unread_many": "{count} unread messages",
        "open_mail": "Open the mailbox",
        # Account states
        "synced_at": "Synced at {time}",
        "failing": "Failing: {error}",
        "refused_short": "refused by the server",
        "none_chosen": "No calendar chosen",
        "waiting": "Waiting for the first sync",
        # Alarm
        "alarm_title": "Appointment",
        "in_minutes": "Appointment in {minutes} min",
        "now": "Appointment now",
        "started_since": "Appointment started {minutes} min ago",
        "stop": "Stop",
        "snooze": "Snooze {minutes} min",
        "untitled": "(no title)",
        "test_event": "Alarm test",
        "test_calendar": "Test",
        # Agenda
        "agenda_title": "Agenda",
        "agenda_subtitle": "The next {days} days",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "nothing_planned": "Nothing planned",
        "all_day": "All day",
        "ongoing": "now",
        "in_min": "in {minutes} min",
        "in_hours": "in {hours} h",
        "agenda_no_account": "Add a calendar to see your appointments here.",
        # Tray
        "menu_agenda": "Agenda",
        "not_configured": "No calendar configured",
        "account_state": "{name}: {state}",
        "last_sync": "Last sync: {time}",
        "no_upcoming": "No appointment in the next 24 h",
        "next_event": "Next: {time} {title}",
        "sync_now": "Sync now",
        "test_alarm": "Test the alarm",
        "menu_accounts": "Synced calendars…",
        "menu_settings": "Settings…",
        "menu_dashboard": "Dashboard",
        "dashboard_title": "Dashboard",
        "section_state": "Status",
        "section_next": "Next appointment alert",
        "section_history": "Latest alerts",
        "no_upcoming_alert": "No upcoming appointment in the days shown",
        "next_alert": "{day}{time} {title} · alert at {alert}",
        "history_empty": "No alert since Vigie started at {time}.",
        "history_alarm": "alarm",
        "history_ring": "ring",
        "history_sound": "sound",
        "history_sound_wait": "sound, alarm if unread in {minutes} min",
        "history_wait": "alarm if unread in {minutes} min",
        "history_vip": "VIP announcement",
        "history_read": "read in time, no alarm",
        "history_read_count": "{count} message(s) read before the delay",
        "history_quiet_hours": "ignored: outside hours",
        "history_dnd": "ignored: Do not disturb",
        "open_log": "Open the log",
        "quit": "Quit",
        "stale_notification": "Calendar not synced ({names}): the alarms can no longer be trusted.",
    },
}

# Written out here: the day names of the system follow its regional format, not the chosen language.
DATES = {
    "fr": {
        "days": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
        "months": [
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre",
        ],
        "format": "{day} {number} {month}",
    },
    "en": {
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "months": [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        "format": "{day}, {month} {number}",
    },
}

_language = "en"


def detect_language():
    """French on a French Windows, English everywhere else."""
    try:
        primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
    except (AttributeError, OSError):
        return "en"
    return "fr" if primary == 0x0C else "en"


def set_language(code):
    global _language
    _language = code if code in STRINGS else detect_language()


def language():
    return _language


def t(key, **values):
    return STRINGS[_language][key].format(**values)


def day_name(date):
    """"mardi 13 octobre" or "Tuesday, October 13"."""
    dates = DATES[_language]
    return dates["format"].format(day=dates["days"][date.weekday()], number=date.day, month=dates["months"][date.month - 1])
