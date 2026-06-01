# Changelog — odk_quote_generator

Toutes les évolutions notables du module sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [19.0.2.0.7] — 2026-06-01

### Modifié
- **Incrément de version pour forcer la mise à jour du module sur odoo.sh** :
  aucune modification fonctionnelle. Sur les instances staging odoo.sh, le
  bouton *Mettre à jour* de l'interface Apps peut être ignoré (le module
  n'est pas réellement re-upgradé). Un changement de numéro de version est
  détecté par le build odoo.sh, qui exécute alors un vrai `-u` rejouant les
  fichiers de données (menus, vues, ACL). Cette version sert de déclencheur
  fiable pour appliquer les correctifs déjà livrés (≥ 19.0.2.0.4 : menu
  *Configuration*, bouton *Nouveau* sur les grilles, mise en page du devis PDF).

## [19.0.2.0.6] — 2026-06-01

### Modifié
- **Écart libellé/valeur trop large dans le bloc « Nos références » du devis
  PDF** : la table méta était en `width: 100 %` avec une colonne de libellés
  forcée à `width: 40 %`, ce qui poussait les valeurs loin à droite. La table
  passe en largeur automatique (`width: auto`) et la colonne libellé s'ajuste
  au contenu (`white-space: nowrap` + petit `padding-right`). Les valeurs sont
  désormais collées à leurs libellés. Correctif appliqué à l'identique dans le
  `<style>` inline du template et dans `static/src/css/odk_report.css`.

## [19.0.2.0.5] — 2026-06-01

### Modifié
- **Mise en page de l'en-tête du devis PDF** :
  - Bloc **« Nos références »** (date, validité, commercial, réf. client)
    désormais aligné **à gauche**.
  - Bloc **« Client »** désormais aligné **à droite**.
  - **En-tête** : suppression du nom de société « ODK » en texte (le logo
    présent à droite le rend redondant). La signature d'activité
    (« Opérateur de dématérialisation… ») est conservée.

## [19.0.2.0.4] — 2026-06-01

### Corrigé
- **Interface d'administration tarifaire introuvable** : le module exposait
  deux menus contradictoires. Le menu réel contenant les écrans
  Catalogues / Grilles / Paliers s'appelait « Catalogues tarifaires », tandis
  qu'un menu **« Configuration » vide** (sans action ni sous-menu) était
  automatiquement **masqué par Odoo**. Le README documentait pourtant le
  chemin « Configuration › Grilles tarifaires », d'où l'impression d'absence
  d'interface admin. Le menu réel est désormais renommé **« Configuration »**
  (sous-menus *Catalogues tarifaires*, *Grilles tarifaires*, *Paliers*) et le
  placeholder vide a été supprimé. Le chemin du README correspond maintenant
  à l'interface réelle.

> Rappel droits : le menu **Configuration** est visible par les 4 rôles (via
> la hiérarchie `implied_ids`), mais seul l'**Admin Tarifaire ODK**
> (`group_odk_pricing_admin`) peut **créer / modifier** catalogues, grilles
> et paliers. Les autres rôles y accèdent en lecture seule.

## [19.0.2.0.3] — 2026-06-01

### Corrigé
- **Symbole € et séparateurs de milliers en charabia** (`10Â 258,33Â â‚¬`) :
  la déclaration UTF-8 n'étant pas honorée par le moteur PDF de l'instance,
  l'affichage des nombres est désormais rendu **insensible à l'encodage**.
  Tous les montants et entiers du rapport sont formatés en **ASCII pur** —
  espace normale comme séparateur de milliers, virgule décimale, et suffixe
  **« EUR »** à la place du caractère €. Plus aucun caractère non-ASCII dans
  les valeurs numériques, donc plus de charabia quel que soit le moteur.
- **Doublon « 36 mois mois »** : le champ d'engagement est une liste de choix
  dont le libellé contient déjà « mois » ; le mot « mois » ajouté en dur après
  le champ a été retiré (sections Packs Factures et Abonnement ODK).

## [19.0.2.0.2] — 2026-06-01

### Corrigé
- **Corps du devis non stylisé à l'impression PDF** : sous wkhtmltopdf, le
  corps du rapport ne recevait pas systématiquement le bundle d'assets
  `web.report_assets_common` (seuls l'en-tête et le pied de page, rendus
  comme documents séparés, le recevaient — d'où le liseré orange visible
  mais le corps en texte brut). Le CSS de la charte ODK est désormais
  **intégré en dur** dans le template QWeb (balises `<style>` inline pour le
  corps, l'en-tête et le pied de page), ce qui garantit le rendu NAVY/ORANGE
  indépendamment du bundle. Le bundle d'assets est conservé en complément.
- **Encodage UTF-8 (€ et accents)** : ajout de
  `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>`
  dans le corps, l'en-tête et le pied de page pour corriger l'affichage du
  symbole € (rendu « â‚¬ ») et des caractères accentués.
- **Slogan société erroné** : la mention « Logiciel d'édition de factures —
  Éditeur ODK » (fausse) est remplacée par le bon descriptif d'activité :
  « Opérateur de dématérialisation de données de caisse et e-reporting de
  transaction. »

## [19.0.2.0.1] — 2026-06-01

### Modifié
- **Badge de mise en avant du PDF aligné sur le one-pager** : le bloc
  « Total mensuel HT » passe d'un fond orange clair à texte NAVY à un fond
  **NAVY plein avec chiffre blanc** et label orange, reprenant fidèlement le
  bloc de mise en avant (type « Jusqu'à -18% ») des one-pagers Packs Factures.

## [19.0.2.0.0] — 2026-06-01

Version majeure : devis mixtes et refonte du rapport PDF.

### Ajouté
- **Devis mixte (Packs Factures + Abonnement dans un même devis)** : le
  wizard de génération propose désormais deux sections activables
  indépendamment via les cases *Inclure Packs Factures* et *Inclure
  Abonnement ODK*. Chaque section possède sa propre grille, son
  engagement, ses variables d'entrée et son aperçu temps réel. La
  génération produit **une seule** `sale.order` regroupant les lignes des
  deux offres, avec un récapitulatif du total mensuel combiné.
- Champs de provenance Abonnement sur `sale.order` (`odk_ab_catalog_id`,
  `odk_ab_grid_id`, `odk_ab_tier_id`, `odk_ab_engagement_months`) et
  drapeau `odk_is_mixed`, en complément des champs Packs historiques.
- Onglet ODK du devis scindé en deux sections de provenance (Packs /
  Abonnement), affichées selon les offres présentes sur le devis.

### Modifié
- **Refonte du rapport PDF au look « one-pager »** : en-tête blanc à
  liseré orange (logo à droite), badge de mise en avant du total mensuel
  HT, titres de section soulignés en orange, tables de conditions à
  colonnes label NAVY sur fond gris, pied de page gris avec mention
  *Document commercial — confidentiel* et pagination. Le bloc *Conditions
  tarifaires ODK* affiche les deux sections (Packs et Abonnement) pour un
  devis mixte.
- **Contrôle hors-grille et plancher tarifaire refactorés ligne à ligne** :
  la grille de référence est désormais celle du palier porté par chaque
  ligne (`line.odk_tier_id.grid_id`), ce qui permet à un devis mixte de
  faire coexister deux grilles avec des planchers distincts.

### Corrigé
- **Double imbrication `web.html_container`** dans le layout externe du
  rapport (`odk_external_layout`) : le conteneur HTML est désormais fourni
  une seule fois par le template principal, le layout externe ne définit
  plus que l'en-tête, le pied de page et le point d'insertion du contenu.

## [19.0.1.0.3] — 2026-06-01

### Corrigé
- **Incompatibilité Odoo 19 bloquant l'installation (assets de rapport)** :
  le template `odk_report_assets_styles` héritait `web.report_assets_common`
  pour injecter le CSS du rapport. En Odoo 19, ce nom n'est plus un template
  QWeb héritable mais un bundle d'assets — l'héritage échouait avec
  `External ID not found: web.report_assets_common`. Le CSS a été déplacé
  dans `static/src/css/odk_report.css` et déclaré via la clé `assets` du
  manifeste (bundle `web.report_assets_common`). Aucun changement visuel :
  même charte NAVY #1F3864 / ORANGE #ED7D31.

## [19.0.1.0.2] — 2026-06-01

### Corrigé
- Correctif d'empaquetage de la 19.0.1.0.1 : le record
  `res.groups.privilege` référençait par erreur sa propre ID via un champ
  `privilege_id` inexistant (`External ID not found: privilege_odk_quote`).
  Le privilège se rattache désormais correctement à la catégorie de module
  via `category_id` → `module_category_odk_quote`. Les 4 groupes conservent
  `privilege_id` → `privilege_odk_quote`.

## [19.0.1.0.1] — 2026-06-01

Version issue de l'audit de code et de sécurité (revue 5 axes + ANSSI).
Voir `output/securite-anssi-2026-05-25.md` pour le détail des constats.

### Corrigé
- **Incompatibilité Odoo 19 bloquant l'installation** : le champ
  `category_id` a été retiré de `res.groups` en Odoo 19. Les 4 groupes
  ODK utilisent désormais `privilege_id` (nouveau modèle
  `res.groups.privilege`), lequel porte le rattachement à la catégorie
  de module. Sans ce correctif, l'import du module échouait avec
  `ValueError: Invalid field 'category_id' in 'res.groups'`.
- Bannières « hors-grille » (avertissement / succès) rendues mutuellement
  exclusives : conditions `invisible` corrigées pour ne plus afficher les
  deux bandeaux simultanément.
- Alignement du wizard volumétrique (Packs Factures) sur une facturation
  mensuelle cohérente avec l'aperçu (volume annuel ÷ 12).

### Sécurité
- **Cloisonnement multi-sociétés** : 3 `ir.rule` globales ajoutées sur
  `odk.pricing.catalog`, `odk.pricing.grid` et `odk.pricing.tier`
  (partage si `company_id = False`, sinon restriction à la société).
- **Confidentialité commerciale** : `ir.rule` restreignant le Commercial
  à ses propres devis ODK ; Manager / Admin voient tous les devis ODK de
  leur société.
- Correction de la hiérarchie `implied_ids` ; la Direction obtient
  l'accès transverse en lecture via
  `sales_team.group_sale_salesman_all_leads`.
- **Plancher tarifaire administrable** : contrôle bloquant à la
  confirmation du devis (`action_confirm` et validation hors-grille)
  s'appuyant sur la variable `odk.pricing.grid.floor_price` configurée
  par l'Admin Tarifaire — aucune valeur en dur.
- **Traçabilité (ANSSI domaine 12)** : héritage `mail.thread` +
  `mail.activity.mixin` et `tracking=True` sur les catalogues, grilles et
  paliers ; `<chatter/>` ajouté aux formulaires correspondants.

### Modifié
- Comparaison plancher / prix via `float_compare` (précision monétaire)
  au lieu d'une tolérance magique `0.0001`.
- Boutons intelligents *Devis ODK* (`res.partner`, `crm.lead`) basés sur
  `search_count` plutôt que sur le chargement complet du recordset.
- `index=True` ajouté sur les champs ODK filtrables de `sale.order`
  (`odk_grid_id`, `odk_tier_id`, `odk_engagement_months`,
  `odk_is_off_grid`, `odk_is_validated`).
- Mixin de devis ODK fusionné dans le modèle `sale.order` principal.

### Notes techniques
- `_sql_constraints` (format liste) conservé : fonctionnel en Odoo 19,
  migration vers `models.Constraint` possible dans une version ultérieure
  (non bloquant).

## [19.0.1.0.0] — 2026-05-25

### Ajouté
- Première version du module pour Odoo 19.
- Catalogues V1 :
  - **Packs Factures (V4)** — 5 paliers (S/M/L/XL/XXL), 2 offres,
    engagements 12/24/36 mois, plancher 0,18 € HT/facture.
  - **Abonnement ODK (V1)** — 6 paliers réseau (XS/S/M/L/XL/XXL),
    2 offres (PA ODK / PA tierce), 8 fonctionnalités, dépassements
    caisses (+4 €/mois) et transactions (+0,008 €/tx).
- Modèles tarifaires : `odk.pricing.catalog`, `odk.pricing.grid`,
  `odk.pricing.tier` avec moteur de calcul intégré.
- Extension `sale.order` : champs ODK, smart bannières hors-grille,
  workflow de validation manager.
- Extension `sale.order.line` : prix attendu + palier de référence.
- Extensions `res.partner` et `crm.lead` : smart buttons *Devis ODK*.
- Wizard `odk.quote.generator.wizard` : génération en 3 étapes avec
  aperçu temps réel.
- Rapport PDF *Devis ODK* aux couleurs ODK (NAVY #1F3864 / ORANGE
  #ED7D31) avec logo, format A4 dédié, bandeau d'en-tête, pied de page
  paginé, bloc *Conditions tarifaires ODK*, badge de validation
  hors-grille.
- Sécurité : 4 groupes (`commercial`, `sales_manager`,
  `pricing_admin`, `direction`) avec hiérarchie `implied_ids` et ACL
  fines par modèle.
- Menus dédiés *ODK Devis* (Devis / Catalogues tarifaires /
  Configuration).
- README + guide de déploiement odoo.sh + checklist de recette.

### Notes techniques
- Compatible Odoo 19.0 community et enterprise.
- Dépendances : `base`, `mail`, `product`, `sale_management`, `crm`.
- Multi-sociétés : compatible (les grilles sont partagées entre
  sociétés du groupe).
