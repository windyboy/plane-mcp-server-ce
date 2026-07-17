# CE_COMPAT.md — Compatibilité MCP ↔ Plane Community Edition

> Dossier de suivi : état de chaque outil MCP testé contre l'instance
> **Plane CE self-hosted** locale (`../stack/`), et ce qui reste à corriger.
> Objectif : **toute fonctionnalité disponible dans Plane CE doit être
> exploitable via le MCP.** Les fonctions purement Cloud sont hors périmètre
> (mais doivent échouer proprement, pas avec un 404 cryptique).
>
> Méthodo : harnais `tests/harness_probe.py` (pilote le MCP stdio en in-memory)
> + relevé des routes réelles CE via `docker compose exec api` sur
> `plane/api/urls/*.py`. Dernier run : **2026-07-17**, instance CE `stable`,
> workspace `optimis-test`, projet `OPTIM`.

## Cause racine dominante

Le `plane-sdk` officiel cible des **endpoints Cloud** que la CE n'enregistre
pas sous `/api/v1`. Trois familles :

1. **Endpoints `*-lite`** (`projects-lite`, `project-members-lite`,
   `members-lite`, `cycles` lite, `modules` lite) → **404 sur CE**. La variante
   pleine (`projects/`, `members/`, `cycles/`, `modules/`) renvoie **200**.
   *(Régression introduite en amont par leur PR #162 ; cf. issues #169/#170/#172.)*
2. **Variantes de chemin** : CE expose `work-items/{id}/relations/` mais le SDK
   appelle l'ancien `issues/{id}/issue-relation/`.
3. **Bugs de modèles Pydantic** dans le SDK : le endpoint répond 200 mais le
   parsing casse (`epoch` int vs float, `assignees` UUID vs `UserLite`,
   `sequence_id` str vs int).

## Endpoints CE réels (relevés depuis `plane/api/urls/`)

Présents sous `/api/v1/` : `projects/`, `projects/{id}/`, `.../members/`,
`.../project-members/`, `.../summary/`, `.../estimates/`, `.../cycles/`
(+ archive, cycle-issues, transfer-issues, archived-cycles), `.../modules/`
(+ module-issues, archive, archived-modules), `.../labels/`, `.../states/`,
`.../intake-issues/`, `.../issues/` **et** `.../work-items/` (alias) avec
sous-ressources `activities/`, `comments/`, `links/`, `issue-attachments/`
(alias `attachments/`), et **`relations/` uniquement sous `work-items/`**.
Workspace : `members/`, `issues/search/` (alias `work-items/search/`),
`issues/{proj}-{seq}/`. User : `users/me/`.

**Absents de `/api/v1` sur cette CE** (→ 404) : `features`, `roles`,
`initiatives`, `milestones`, `work-item relation-definitions`, `count`,
`worklogs` / `total-worklogs`, `archived-issues`, `pages`, `issue-types`
(work-item-types), `work-item property values`.

---

## Matrice de résultats (run 2026-07-17)

### ✅ Fonctionnent tel quel (15)
`get_me`, `get_pql_reference`, `search_work_items`, `retrieve_project`,
`list_labels`, `retrieve_label`, `list_states`, `retrieve_state`,
`list_work_items`, `retrieve_work_item`*, `list_intake_work_items`,
`list_work_item_properties`†, `list_work_item_comments`,
`list_work_item_links`, `list_work_item_attachments`.

> \* `retrieve_work_item` OK tant que l'item n'a **pas** d'assignee/label
>    (sinon crash de validation, cf. BUG-2).
> † `list_work_item_properties` renvoie OK — **à revérifier** (aucune route
>    property côté CE ; possiblement réponse vide/silencieuse).

### 🔧 Category 1 — Corrigeables (CE a l'endpoint, mauvaise variante)
| Outil MCP | Le SDK appelle | CE fournit (200) | Correctif |
|-----------|----------------|------------------|-----------|
| `list_projects` | `projects-lite` | `projects/` | fallback lite→full |
| `get_workspace_members` | `members-lite` | `members/` | fallback lite→full |
| `get_project_members` | `project-members-lite` | `project-members/` | fallback lite→full |
| `list_cycles` | `cycles` (lite) | `cycles/` | fallback lite→full |
| `list_modules` | `modules` (lite) | `modules/` | fallback lite→full |
| `list_work_item_relations` | `issues/{id}/issue-relation/` | `work-items/{id}/relations/` | changement de chemin |

### 🐛 Category 3 — Endpoint OK, modèle SDK cassé
| Outil MCP | Bug | Correctif |
|-----------|-----|-----------|
| `list_work_item_activities` | `results.*.epoch` : API renvoie un float, modèle typé `int` | `epoch: int` → `float`/`int\|float` |
| `retrieve_work_item` (avec assignees) | `assignees`/`labels` : UUID nus vs `UserLite`/`Label` | élargir le modèle **ou** `expand=assignees,labels` |
| `search_work_items` | `sequence_id: str` alors que l'API renvoie un int (n'apparaît qu'avec des résultats réels) | `sequence_id: int\|str` |

### 🚫 Category 2 — Absent de la CE `/api/v1` (dégrader proprement)
`get_features`, `update_workspace_features`, `update_project_features`,
`list_roles`/`retrieve_role`, `list_initiatives` (+ tous outils initiative),
`list_milestones` (+ tous outils milestone), `count_work_items`,
`list_work_item_relation_definitions` (+ CRUD définitions),
`work_logs` (list/create/update/delete), `get_project_worklog_summary`
(chemin `total-worklogs` absent — mais `summary/` existe, non wrappé),
`list_archived_work_items` (route `archived-issues` absente),
outils **pages** (non sous `/api/v1`, cf. issue #163 : essayer `/api/...`),
outils **work-item-types** (`issue-types` absent de `/api/v1`),
lecture/écriture **work-item property values**.

> Pour Category 2 : au lieu d'un 404 brut, renvoyer une erreur claire
> « non disponible sur Plane self-hosted / CE » (pattern décorateur, cf.
> upstream PR #161). Réévaluer au cas par cas si un chemin CE alternatif
> existe (pages, work-item-types, estimates avec données).

---

## Plan d'action (priorisé)

- [ ] **P1 — Fallback lite→full** (`lite_or_fallback` helper). Corrige d'un
      coup `list_projects`, `get_workspace_members`, `get_project_members`,
      `list_cycles`, `list_modules`. *Inspiré de la PR upstream #173, étendue
      aux 2 outils members.* Impact max / risque min.
- [ ] **P2 — Relations** : router `list_work_item_relations` (et create/remove)
      vers `work-items/{id}/relations/`.
- [ ] **P3 — Bugs modèles** : `epoch` (activities), `assignees/labels`
      (retrieve_work_item), `sequence_id` (search). Patch modèle SDK ou
      normalisation côté outil.
- [ ] **P4 — Dégradation propre** pour Category 2 (décorateur
      « not-available-on-CE » façon PR #161, généralisé).
- [ ] **P5 — Investiguer chemins alternatifs CE** : pages (`/api/...`),
      work-item-types, estimates, worklogs. Confirmer présents/absents.
- [ ] **P6 — Emprunts upstream** (voir dossier ci-dessous) : `PLANE_MCP_MODULES`
      (PR #81, filtrage d'outils), `advanced_search` (PR #88), auto-expand
      assignees (PR #80), normalisation params JSON-string (PR #76),
      host/port + /healthz (PR #137).

## Emprunts upstream repérés (à réimplémenter dans le fork)

Le fork est déjà sur la base **Python `plane_mcp/`** (post-rewrite PR #54) →
les PRs Python sont directement transposables ; les vieilles PRs TypeScript
(#35/#37/#43) ne le sont pas.

| PR upstream | Apport | Priorité |
|-------------|--------|----------|
| **#173** `refract99` | fallback lite→full 404 (`lite_or_fallback`) | **P1** |
| **#161** `HellCatVN` | décorateur « milestones indispo self-hosted » | P4 |
| **#81** `enesdemir` | `PLANE_MCP_MODULES` : limite les outils chargés (clients qui refusent 139 outils) | P6 |
| **#88** `lifeiscontent` | `advanced_search_work_items` (filtres structurés) | P6 |
| **#80** `Quentin-M` | auto-expand `assignees` (évite les UUID nus → mitige BUG-2) | P3/P6 |
| **#76** `ej31` | normalise params list passés en string JSON | P6 |
| **#137** `Maziak2520` | host/port via env + `/healthz` (self-hosting HTTP) | P6 |
| **#117** `151813125` | lecture des valeurs de propriétés work-item | P5/P6 |
| **#62** `1nk1` | outils pages list/search/update/delete (à combiner avec fix chemin pages) | P5 |

Issues de fond côté CE : #169/#170/#172 (lite 404), #98 (assignees), #136
(search `q`→`search`), #163 (pages `/api/v1`), #131 (PAT HTTP sans OAuth),
#102/#29 (trop d'outils).
