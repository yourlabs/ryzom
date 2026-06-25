# MR !68 — réponses aux commentaires de jpic

Brouillon des réponses à poster sur chaque commentaire de la MR. (Statut au
dernier passage : tous les points actionnables traités sauf l'UI edit/delete.)

---

## 1. `views.py:78` — « Ca serait sympa de l'envoyer en background avec celery »

Fait, mais **pas via Celery** finalement — et voici pourquoi. `sweep_stale_clients`
n'est appelé que depuis `ddp_poll`, donc **uniquement en mode poll**, où il n'y a
typiquement ni worker Celery ni broker. Un `.delay()` ne s'exécuterait donc jamais
(ou ferait planter le poll si le broker est injoignable).

À la place je l'ai sorti du chemin chaud en le **throttlant** : il ne touche la DB
qu'une fois par fenêtre `POLL_TTL` par process (`_last_sweep`) au lieu de chaque
poll. Un client stale n'a de toute façon besoin d'être réclamé qu'une fois son TTL
écoulé. Si tu préfères vraiment Celery pour les déploiements ws, je peux ajouter un
**beat périodique** en complément — dis-moi.

---

## 2. `ryzom.views.rst` — « Pourquoi t'as enlevé les docs d'API auto-générées ? »

Restaurées. 8 des 10 stubs supprimés pointaient en fait vers des modules qui ont
juste **déménagé** dans `ryzom_django_channels` (consumers, ddp, models, signals,
views, pubsub, methods, polling, facets). J'ai ajouté
`docs/source/ryzom_django_channels.rst` (directives `automodule`) et l'ai branché
dans le toctree. J'exclus `routing` car il importe `django.conf.urls.url`
(supprimé depuis Django 4) → il planterait à l'import : c'est un bug pré-existant,
séparé. Build sphinx clean (sans warnings).

---

## 3. `transpiler.py:691` — « `getattr(node, 'n', node.value)` ça fait presque pareil ? »

Corrigé : `return getattr(node, 'n', node.value)`. Tu as raison, et c'est même
plus correct : l'ancien `getattr(...) or node.value` jetait un `0`/`0.0`/`''`
pourtant légitime.

---

## 4. `transpiler.py:700` — « je prefererrais avoir un if self.in_str et un else »

Fait : `if self.in_str: return s` / `else: ...`.

---

## 5. `SOURCE.md` — « on peut les avoir en installant django-autocomplete-light, preferrable au vendoring »

Fait, et tu avais raison : le web component `autocomplete-light` est livré dans
**`django-autocomplete-light`** via l'app **`dal_alight`** (« alight » =
autocomplete-light). J'ai :
- retiré le vendoring (`git rm` des assets + `SOURCE.md`) ;
- ajouté `django-autocomplete-light` dans `setup.py` — **depuis PyPI**, pas
  l'install *editable* depuis l'USB (`/mnt/usb/...`) qui était précisément la cause
  du vendoring (chemin manquant → boot Django cassé) ;
- ajouté `dal_alight` à `INSTALLED_APPS` ;
- repointé les `Static()` vers `dal_alight/autocomplete-light.{css,js}`.

Le JS de DAL est un superset compatible (mêmes custom elements
`autocomplete-light` / `autocomplete-select(-input)`). `findstatic` + `check` OK.

---

## 6. `consumers.py:312` — subscriptions créées au render / GET non-safe (RFC 7231/9110)

Fait — et tu as raison sur les deux points (RFC + crawlers/GoogleBot). Petite
précision : le `recv_subscribe` côté ws était **déjà mort** (il référençait un champ
`parent` et un `exec_query` inexistants), donc c'était à refaire proprement, pas à
restaurer.

Nouveau fonctionnement :
- **Le GET ne crée rien** (ni `Client` ni `Subscription`). Il rend la première page
  en **lecture seule** (donc un crawler / client sans-JS voit le contenu) et émet
  des descripteurs `data-ryzom-subscribe` / `data-ryzom-register`.
- La création se fait sur **action client** : message `subscribe` sur le websocket,
  ou **premier poll en POST** (créer sur un POST = safe). Idempotent
  (`get_or_create`), donc reconnect/re-poll ne duplique rien.

Vérifié end-to-end (mode poll) : `GET` → **0 Client / 0 Subscription**, lignes
rendues ; premier `POST` → 1/1 avec la bonne fenêtre ; insert suivant livré au poll
GET. Côté ws : couvert par les tests `test_ws_connected` + `test_register_changed`.

Compromis connu (à arbitrer) : un changement qui arrive **entre** le rendu et le
subscribe n'est rattrapé qu'au prochain reload (on ne re-pousse pas le contenu
initial au subscribe, pour éviter un flicker). Corrigeable si tu veux que ce soit
hermétique.

---

## 7. `settings.py:139` — remettre `DB_HOST/DB_USER/DB_PASSWORD` à vide

Fait : `DB_HOST` / `DB_USER` / `DB_PASSWORD` (et `DB_PORT`) repassés à **vide** par
défaut → connexion socket local en tant que `$USER`, base `ryzom` (ton
`createuser -s $USER` + `createdb` « marche juste »). Le moteur reste **Postgres**
(requis pour `ArrayField`). CI inchangé (il set déjà les `DB_*`). J'ai mis à jour
`CLAUDE.md` et le skill `run-demo` en conséquence.

---

## 8. Commentaire général (capture d'écran) — retrouver la vue « riche »

Déjà en place :
- **Sorting au clic sur colonne** : fait (`ReactiveSort`, endpoint `sort/`).
- **Rows-per-page en material select** : fait (`MDCSelectOutlined`).
- **Filtre en formulaire material** : fait (`MDCTextFieldOutlined` / `MDCCheckbox`).

À faire (on s'y attaque ensuite) :
- **Bouton delete** (poubelle rouge) → formulaire en modale, clic-milieu = nouvel
  onglet (lien direct partageable).
- **Bouton edit** (stylo orange) → ModelForm d'update en modale, clic-milieu =
  nouvel onglet.
