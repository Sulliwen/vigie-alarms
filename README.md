# Vigie — une alarme avant chaque rendez-vous

*[English version](README.en.md)*

Vigie reprend [Calendar Alarm](https://github.com/Sulliwen/calendar-alarm),
qui reste disponible seul, et y ajoutera les alertes Slack.

Petit programme Windows qui tourne en arrière-plan et sonne **10 minutes avant
chaque rendez-vous** de vos agendas (Infomaniak, Google, Outlook, iCloud…), que
le rendez-vous porte un rappel ou non et quel que soit son créateur. Une
fenêtre passe au premier plan avec le titre du rendez-vous et deux boutons :
**Arrêter** et **Rappel 5 min**.

Les agendas sont relus toutes les minutes : un rendez-vous ajouté à la dernière
minute sonne dès qu'il est découvert.

## Installation

1. Lancez `Vigie-Setup-<version>.exe` (aucun droit administrateur
   requis). Le fichier n'étant pas signé, Windows affiche un avertissement
   SmartScreen : « Informations complémentaires » → « Exécuter quand même ».
2. À la fin de l'installation, la fenêtre **« Agendas synchronisés »**
   s'ouvre.
   Choisissez votre fournisseur dans la liste déroulante, cliquez sur
   « Ajouter… » et suivez les indications affichées. Recommencez pour chaque
   agenda à surveiller.

Le programme s'inscrit lui-même au démarrage de Windows. Un **clic** sur
l'icône de la zone de notification ouvre le **Tableau de bord** : l'état de
chaque agenda et de chaque messagerie (pastille verte, rouge ou grise), la
prochaine alerte de rendez-vous, et les dernières alertes depuis le démarrage
de Vigie (heure, source, message, ce qui a été fait : son, alarme, annonce VIP,
lu à temps, ignoré hors horaires…). Son en-tête mène aux autres écrans :
l'**Agenda** (tous les rendez-vous des 7 prochains jours, regroupés par jour),
les agendas synchronisés, les paramètres et le journal ; en bas, « Synchroniser
maintenant ». Le clic droit sur l'icône donne aussi ces écrans, ainsi que
« Tester l'alarme » et « Quitter ». Le programme
existe en français et en anglais.

## Agendas pris en charge

| Fournisseur | Ce qu'il faut saisir |
| --- | --- |
| Infomaniak (kSuite, Kalendar) | Identifiant de synchronisation et mot de passe d'application, affichés sur <https://config.infomaniak.com> (« Mes Contacts & Agendas » → « Synchronisation manuelle ») |
| Google Agenda | L'adresse secrète de l'agenda : Paramètres → votre agenda → « Intégrer l'agenda » → « Adresse secrète au format iCal » |
| Outlook / Microsoft 365 | Le lien ICS de l'agenda publié : Outlook sur le web → Paramètres → Calendrier → Calendriers partagés → « Publier un calendrier » |
| Apple iCloud | Adresse du compte Apple et mot de passe pour application (account.apple.com) |
| Yahoo, Fastmail | Adresse du compte et mot de passe d'application |
| Nextcloud | Adresse du serveur suivie de `/remote.php/dav`, nom d'utilisateur et mot de passe d'application |
| Autre serveur CalDAV | Adresse CalDAV, identifiant et mot de passe |
| Autre adresse iCal (.ics) | Une adresse `https://` renvoyant un agenda au format iCal |

Pour un compte CalDAV (Infomaniak, iCloud, Yahoo, Fastmail, Nextcloud), le
programme demande ensuite quels agendas du compte surveiller : le vôtre est
proposé par défaut, les agendas partagés des collègues et des salles ne le
sont pas. Pour Google et Outlook, il faut une adresse par agenda.

Une adresse secrète donne accès en lecture à tout l'agenda : elle est conservée
comme un mot de passe, ne la partagez pas.

Un rendez-vous présent dans deux agendas (invitation reçue sur les deux) ne
sonne qu'une fois.

## Alertes Slack

Vigie peut aussi surveiller Slack. Chaque **déclencheur** a son action, au choix
« Rien », « Son », « Alarme si non lu » ou « Son + alarme si non lu » :

| Déclencheur | Par défaut |
| --- | --- |
| Message privé | Son + alarme si non lu |
| Mention @moi (canal, groupe ou fil) | Son + alarme si non lu |
| Réponse à l'un de vos messages, dans un fil | Rien |
| Tout message d'une conversation de groupe | Rien |
| `@here`, `@channel` | Rien |
| Mots-clés (mots entiers, sans tenir compte des majuscules) | Rien |
| Canaux suivis : tous leurs messages | Rien |

Si un message correspond à plusieurs déclencheurs, l'action la plus forte
s'applique. Vos propres messages, les modifications et les robots ne déclenchent
jamais rien.

- **Son** : un son court à l'arrivée du message.
- **Alarme si non lu** : si un message n'est toujours pas lu 5 minutes après le
  premier d'une série, **une seule alarme** liste les messages non lus, avec
  « Ouvrir Slack ». Elle a sa propre sonnerie et se ferme d'elle-même dès qu'ils
  sont lus.
- **Quand** : silence pendant le « Ne pas déranger » de Slack (désactivable), et
  au choix seulement entre deux heures et seulement du lundi au vendredi.

**Personnes VIP** (Paramètres → Messageries → Personnes VIP, communes à Slack
et Zoom ; décochée, aucun traitement VIP) : tous leurs messages sont annoncés, partout où vous êtes
membre, même sans tag. Un son, puis une voix dit la phrase choisie (« Message
VIP » par défaut). Il n'y a jamais d'alarme pour eux, et une série de messages
n'est annoncée qu'une fois par minute. Le nom est comparé sans tenir compte des
majuscules ni de l'ordre des mots (« Jakez Rolland » reconnaît aussi « Rolland
Jakez »).

Mise en place, une fois : sur <https://api.slack.com/apps>, « Create New App » →
« From a manifest », choisir l'espace de travail et coller :

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

Puis « Basic Information » → « App-Level Tokens » → générer un jeton avec la
permission `connections:write`, et « Install App » → « Install to Workspace ».
Dans Vigie : Paramètres → Messageries → Slack → « Jetons Slack… », y coller les deux jetons
(`xapp-…` et `xoxp-…`).

## Alertes Zoom

Vigie peut aussi surveiller Zoom Team Chat, avec un **son** par déclencheur :

| Déclencheur | Par défaut |
| --- | --- |
| Messages privés des contacts listés (adresses e-mail) | Son |
| Mention @moi | Son |
| Réponse à l'un de vos messages | Rien |
| `@all` | Rien |
| Mots-clés (mots entiers, sans tenir compte des majuscules) | Rien |
| Canaux suivis (leurs noms, ou `*` pour tous) : tous leurs messages | Rien |

Différences avec Slack :

- **Pas d'alarme si non lu** : l'API de Zoom ne dit pas si un message a été lu.
- **Environ 30 secondes de délai** : Zoom n'envoie rien en direct à un
  programme de bureau, et sa liste des « conversations récentes » reste vide sur
  certains comptes. Vigie relit donc chacun de vos canaux toutes les
  30 secondes, en espaçant les appels d'au moins une seconde pour respecter la
  limite de Zoom. Les messages privés ne sont lus que pour les contacts listés.
- **Personnes VIP** : la même liste que pour Slack ; leurs messages Zoom sont
  annoncés de la même façon (un son, puis la voix).
- **Horaires** et jours d'alerte propres à Zoom.

Mise en place, une fois : sur <https://marketplace.zoom.us>, « Develop » →
« Build App » → « General App » :

1. « Basic Information » : **User-managed**, activer **Use Public Client
   OAuth**, mettre `http://127.0.0.1:8765/callback` comme « OAuth Redirect URL »
   et dans l'« OAuth Allow List ».
2. « Scopes », uniquement en lecture : `team_chat:read:list_user_channels`,
   `team_chat:read:list_user_messages`, `team_chat:read:user_message` et
   `user:read:user`.

Dans Vigie : Paramètres → Messageries → Zoom → « Connecter Zoom… », y coller le **Public
Client ID**, puis autoriser l'application dans le navigateur. Le jeton est
conservé dans le Gestionnaire d'identifications Windows et renouvelé tout seul.

## Comportement

- Sonnerie en boucle jusqu'à un clic. Fermer la fenêtre par la croix vaut
  « Rappel », pas « Arrêter ».
- Un rendez-vous découvert à moins de 10 minutes, ou commencé depuis moins de
  5 minutes (sortie de veille), sonne immédiatement.
- Ne sonnent pas : les événements « toute la journée » (affichés dans
  l'Agenda), les rendez-vous annulés et les invitations refusées.
- Icône verte : tous les comptes se synchronisent. Icône rouge et
  notification : un compte n'a plus de synchronisation réussie depuis
  5 minutes, ses alarmes ne sont plus fiables.
- Mots de passe et adresses iCal sont conservés dans le Gestionnaire
  d'identifications Windows. Si un serveur en refuse un, le programme le
  redemande.

Désinstallation : « Applications installées » de Windows. Elle retire aussi
les réglages et les mots de passe enregistrés.

Limites : Windows uniquement ; le PC doit être allumé, session ouverte. Pour
les agendas lus par une adresse iCal (Google, Outlook), le délai d'apparition
d'un nouveau rendez-vous dépend du fournisseur.

## Paramètres

Clic droit sur l'icône → « Paramètres… » :

- **Général** : langue, lancement au démarrage de Windows.
- **Agenda** (rendez-vous seulement) :
  - type d'alerte : **alarme** (fenêtre et sonnerie en boucle) ou **sonnerie**
    (un son et une notification Windows, sans fenêtre) ;
  - déclenchement : délai avant le rendez-vous, deuxième alerte au début du
    rendez-vous, retard toléré pour un rendez-vous découvert tard, rendez-vous
    « Disponible » et invitations sans réponse à ignorer ;
  - son : sonnerie (celles de Windows ou un fichier `.wav`), durée d'un rappel,
    arrêt automatique du son (la fenêtre reste affichée) ;
  - affichage et synchronisation : jours affichés, événements « toute la
    journée », fréquence de relecture des agendas.
- **Messageries** : une liste à gauche (une pastille verte, rouge ou grise
  indique si l'outil est connecté, en échec ou désactivé), les réglages de
  l'outil choisi à droite :
  - **Slack** : connexion, déclencheurs, son et alarme, horaires (voir
    [Alertes Slack](#alertes-slack)) ;
  - **Zoom** : connexion, déclencheurs, son, horaires (voir
    [Alertes Zoom](#alertes-zoom)) ;
  - **Personnes VIP**, communes à toutes les messageries.

Les réglages sont enregistrés dans `%LOCALAPPDATA%\vigie\config.json`.
`my_emails` (adresses servant à reconnaître vos invitations) ne se change que
dans ce fichier. Le journal est dans le même
dossier (`vigie.log`).

## Depuis les sources

Python 3.12 ou plus récent, installé côté Windows.

Pendant le développement, `dev.ps1` lance Vigie directement depuis le code, sans
compiler ni installer ; elle redémarre d'elle-même à chaque modification de
`vigie.py` ou `texts.py`.

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1        # lancement depuis le code, redémarrage automatique
powershell -ExecutionPolicy Bypass -File install.ps1    # venv, dépendances, lancement
.venv\Scripts\python.exe -m unittest                    # tests
powershell -ExecutionPolicy Bypass -File build.ps1      # produit l'installeur dans dist\ (Inno Setup 6 requis)
powershell -ExecutionPolicy Bypass -File uninstall.ps1  # arrêt et retrait du démarrage
```

Tous les textes affichés sont dans `texts.py`, en français et en anglais.
