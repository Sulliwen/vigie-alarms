# Journal des modifications

Les versions suivent le [versionnage sémantique](https://semver.org/lang/fr/) :
`MAJEURE.MINEURE.CORRECTIF`.

- **CORRECTIF** (1.0.x) : correction d'un défaut, sans nouveauté.
- **MINEURE** (1.x.0) : nouvelle fonctionnalité ; la mise à jour garde les réglages.
- **MAJEURE** (x.0.0) : changement qui ne permet pas de garder les réglages
  existants.

Le numéro est défini à un seul endroit, `__version__` dans `vigie.py`.
Il est repris par l'installeur et affiché en bas de la fenêtre « Paramètres ».

## En cours (non publié)

Le numéro reste 1.0.0 tant que la version finale n'est pas validée.

- Lancement au démarrage de Windows sans fenêtre de terminal, même après un
  lancement manuel depuis un terminal.
- Le portrait de Vigie remplace l'icône du calendrier : programme, fenêtres et
  zone de notification. Une pastille verte ou rouge dans le coin indique si les
  agendas se synchronisent.

- Alertes Slack : son à chaque message privé ou tag personnel, puis une seule
  alarme pour les messages encore non lus après 5 minutes ; respect du « Ne pas
  déranger » de Slack ; réglages dans Paramètres → Slack.
- Personnes VIP sur Slack : tous leurs messages, même sans tag, sont annoncés
  par un son puis une voix « Message VIP », sans alarme.
- Paramètres en trois onglets : Général, Agenda (rendez-vous seulement) et
  Slack (Slack seulement).
- Agenda : choix entre alarme (fenêtre) et sonnerie (son et notification),
  deuxième alerte au début du rendez-vous, retard toléré réglable, invitations
  sans réponse à ignorer.
- Slack : une action par déclencheur (rien, son, alarme si non lu, ou les
  deux) pour les messages privés, les mentions, les réponses à vos messages,
  les conversations de groupe, `@here`/`@channel`, des mots-clés et des canaux
  suivis ; sonnerie d'alarme et coupure du son propres à Slack ; horaires et
  jours d'alerte ; « Ne pas déranger » désactivable ; section VIP dépliable,
  désactivable, avec phrase et voix au choix.
- Alertes Zoom Team Chat : un son pour les mentions, les réponses à vos
  messages, `@all`, des mots-clés, des canaux suivis et les messages privés de
  contacts choisis ; personnes VIP partagées avec Slack ; onglet Zoom dans les
  Paramètres, connexion par le navigateur. Pas d'alarme si non lu (Zoom ne le
  dit pas), environ 30 secondes de délai.
- Paramètres : Slack, Zoom et les futures messageries regroupés dans un onglet
  « Messageries » (liste à gauche avec l'état de chaque outil) ; les personnes
  VIP y ont leur propre entrée, commune à toutes les messageries.
- Tableau de bord au clic sur l'icône (à la place de l'Agenda) : état des
  agendas et des messageries, prochaine alerte de rendez-vous, dernières
  alertes avec ce qui a été fait, y compris les messages Slack lus avant le
  délai et ceux ignorés hors horaires ou en « Ne pas déranger ».
- Mode développement (`dev.ps1`) : lancement depuis le code, redémarrage
  automatique à chaque modification.

## 1.0.0 — 2026-10-13

Première version de Vigie, reprise de Calendar Alarm 1.0.0 sous son propre nom.
Vigie s'installe à côté de Calendar Alarm sans le remplacer.

- Alarme avant chaque rendez-vous, avec ou sans rappel, quel que soit son
  créateur : fenêtre au premier plan, sonnerie en boucle, « Arrêter » ou
  « Rappel ».
- Agendas Infomaniak, Google, Outlook / Microsoft 365, iCloud, Yahoo, Fastmail,
  Nextcloud, et tout serveur CalDAV ou adresse iCal.
- Fenêtre « Agenda » : les rendez-vous des prochains jours, tous agendas
  confondus.
- Paramètres : délai, durée du rappel, sonnerie, coupure automatique du son,
  jours affichés, langue, démarrage avec Windows.
- Français et anglais.
- Installeur Windows par utilisateur, sans droits administrateur.
