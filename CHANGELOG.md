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

- Le portrait de Vigie remplace l'icône du calendrier : programme, fenêtres et
  zone de notification. Une pastille verte ou rouge dans le coin indique si les
  agendas se synchronisent.

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
