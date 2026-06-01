# Cahier des charges — Module `odk_quote_generator`

**Demandeur** : Eloi Lamort de Gail — Directeur des Opérations, ODK / Groupe Confero
**Date de la demande** : Mai 2026
**Version du document** : 1.0
**Statut** : Spécifications validées — développement livré

---

## 1. Contexte et objectif

ODK, filiale du Groupe Confero, édite un logiciel de facturation
commercialisé sous deux formats : **Packs Factures** (consommation
volumétrique) et **Abonnement ODK** (forfait réseau). La force de vente
doit pouvoir produire rapidement des devis chiffrés conformes à la
politique tarifaire, sans risque d'erreur de saisie.

L'objectif est de **développer un module Odoo 19 natif** qui automatise
la génération de ces devis depuis les CRM/Sales du SI ODK, déployé sur
la plateforme **odoo.sh** déjà utilisée par le Groupe.

---

## 2. Périmètre fonctionnel

### 2.1 Inclus dans la V1
- Saisie guidée par wizard pour les deux catalogues (Packs Factures + Abonnement ODK).
- Sélection automatique du palier tarifaire en fonction des variables (volume, magasins, caisses, transactions).
- Calcul automatique du prix unitaire et des éventuels dépassements / surcharges.
- Génération d'un devis (`sale.order`) rattaché au contact et à l'opportunité.
- Édition d'un PDF aux couleurs ODK.
- Gestion des devis hors-grille avec workflow de validation manager.
- Reconfiguration des grilles tarifaires sans modification de code.
- Reporting transverse pour la Direction (lecture seule).

### 2.2 Hors périmètre V1 (pistes d'évolution à arbitrer)
- Génération du contrat signable à partir du devis accepté.
- Tableau de bord Direction avec analyse mix produit / marge.

> Aucune évolution post-V1 n'a été engagée à ce stade ; les pistes
> ci-dessus sont des suggestions soumises à arbitrage du Product Owner.

---

## 3. Exigences fonctionnelles

### 3.1 Catalogues tarifaires

**Catalogue Packs Factures (V4)**
- 5 paliers volumétriques : S / M / L / XL / XXL.
- 2 offres : Offre 1 (spot 0,22 €) / Offre 2 (bundle + PA spot 0,28 €).
- Engagements : 12 / 24 / 36 mois.
- Plancher tarifaire : 0,18 € HT / facture.

**Catalogue Abonnement ODK (V1)**
- 6 paliers réseau : XS / S / M / L / XL / XXL.
- 2 offres : avec PA ODK / avec PA tierce surchargée.
- Engagements : 12 / 24 / 36 mois.
- 8 fonctionnalités incluses.
- Dépassements : caisses (+4 €/mois/caisse au-delà du forfait) et transactions (+0,008 €/tx au-delà du forfait).

**Exigences communes**
- Les grilles doivent être **modifiables via l'interface Odoo** par un Admin Tarifaire, sans intervention développeur.
- L'ajout d'une nouvelle offre ou d'un nouveau catalogue (futur produit ODK) doit être possible sans modification de code.

### 3.2 Workflow commercial

1. Le commercial ouvre le wizard depuis le menu **ODK Devis › Nouveau devis**.
2. Il sélectionne le client (et éventuellement l'opportunité CRM rattachée).
3. Il choisit le catalogue, l'offre (grille) et la durée d'engagement.
4. Il renseigne les variables métier (volume annuel pour Packs, ou nombre de magasins / caisses / transactions pour Abonnement).
5. Le système affiche un **aperçu temps réel** : palier détecté, prix unitaire, base mensuelle, dépassements éventuels, total.
6. Le commercial valide → un devis est créé dans le pipeline `sale.order`, rattaché au contact et à l'opportunité.
7. Il peut imprimer le **PDF Devis ODK** depuis le bouton standard *Imprimer*.

### 3.3 Gestion du hors-grille

- Si un commercial modifie manuellement le `price_unit` d'une ligne et qu'il diverge du prix attendu issu de la grille, le devis bascule en statut **hors-grille**.
- Une **bannière d'alerte** apparaît en tête du devis.
- Un **Manager Commercial** peut valider le hors-grille (bouton dédié). La validation est tracée (utilisateur + date).
- Toute modification ultérieure du prix **révoque automatiquement** la validation.
- Le badge *Hors-grille validé par X le Y* apparaît sur le PDF.

### 3.4 Rapport PDF

- Format A4 portrait, marges 28/18/10/10 mm.
- En-tête : bandeau NAVY (#1F3864) avec liseré ORANGE (#ED7D31), logo ODK, raison sociale, tagline.
- Corps : titre *Devis Commercial* + numéro, bloc client, bloc références, bloc *Conditions tarifaires ODK* (catalogue / grille / palier / engagement / variables saisies), tableau des lignes avec totaux HT / TVA / TTC, badge de validation hors-grille si applicable, conditions particulières, mention légale.
- Pied de page : bandeau NAVY avec liseré ORANGE, raison sociale, n° TVA, pagination, site web.
- Police : Arial.
- Palette : exclusivement NAVY #1F3864 et ORANGE #ED7D31 sur fond clair (#F5F8FC, #F8FAFD, #FFFAF5).

---

## 4. Exigences techniques

### 4.1 Plateforme
- **Odoo 19** (community ou enterprise), déployé sur **odoo.sh**.
- Multi-sociétés : les grilles tarifaires sont partagées entre les sociétés du Groupe Confero.
- Compatible avec le module standard `sale_management` et `crm`.

### 4.2 Architecture
- Module Odoo natif respectant les conventions officielles (manifest, structure de dossiers, hooks).
- Pas de dépendance externe non standard.
- Pas de modification de code core Odoo (extensions via `_inherit` uniquement).
- Données initiales chargées via XML avec `noupdate="1"` sur les enregistrements critiques.
- Vues étendues via xpath (pas de remplacement complet).

### 4.3 Intégration SI
- Devis créés dans le pipeline `sale.order` standard (visibles dans les rapports natifs de vente).
- Rattachement automatique à `res.partner` (smart button compteur de devis ODK).
- Rattachement automatique à `crm.lead` quand le devis est issu d'une opportunité.
- Réutilisation de la TVA et de la devise paramétrées sur la société Odoo.

### 4.4 Performance
- Aperçu du wizard temps réel via `@api.onchange` (pas de rechargement).
- Calcul des dépassements en Python (pas de DAX / requête lourde).

---

## 5. Exigences de sécurité

### 5.1 Groupes utilisateurs (4)

| Groupe | Rôle métier | Périmètre |
|--------|-------------|-----------|
| Commercial ODK | Force de vente | Créer et modifier ses propres devis dans la grille. Pas d'accès configuration. |
| Manager Commercial ODK | Manager des équipes vente | Hérite de Commercial. Peut valider les devis hors-grille. |
| Admin Tarifaire ODK | Pricing manager | Hérite de Manager. Peut créer / modifier catalogues, grilles, paliers. |
| Direction ODK | Comité de direction | Hérite de Commercial. Lecture seule transverse + accès reporting. |

### 5.2 Contrôle d'accès
- ACL fines via `ir.model.access.csv` sur chacun des 4 modèles métier (catalogue, grille, palier, wizard).
- Hiérarchie implicite via `implied_ids` pour limiter la maintenance.
- Menus Configuration restreints au seul groupe Admin Tarifaire.

### 5.3 Traçabilité
- Tous les devis hors-grille validés enregistrent : utilisateur validateur + date + utilisateur d'origine.
- Modification du prix après validation → révocation automatique tracée.

---

## 6. Exigences de design (charte graphique ODK)

- **Couleur primaire** : NAVY #1F3864 (titres, en-têtes, fonds de table).
- **Couleur secondaire** : ORANGE #ED7D31 (accents, liserés, badges, numéro de document).
- **Police** : Arial (compatible PDF rendu via wkhtmltopdf / Odoo).
- **Logo** : logo ODK officiel intégré dans le module (`static/description/logo_odk.png`).
- **Pas d'utilisation** de couleurs hors charte sur les éléments décoratifs.

---

## 7. Livrables attendus

| Livrable | Format | Statut |
|----------|--------|--------|
| Module Odoo `odk_quote_generator` | Code source Python + XML | Livré |
| Données initiales V1 (2 catalogues + grilles + paliers) | XML | Livré |
| Rapport PDF aux couleurs ODK | Template QWeb + CSS | Livré |
| README + guide de déploiement odoo.sh | Markdown | Livré |
| Changelog | Markdown | Livré |
| Checklist de recette utilisateur | Section README | Livré |
| Cahier des charges (ce document) | Markdown | Livré |

---

## 8. Critères d'acceptation

Le module est considéré conforme si :

1. ✅ Installation réussie sur odoo.sh staging sans erreur de log.
2. ✅ Les 4 groupes sont créés et assignables aux utilisateurs.
3. ✅ Le wizard génère un devis Packs Factures et un devis Abonnement avec les bons montants (validés contre le simulateur Excel ODK).
4. ✅ Le PDF respecte la charte graphique ODK (NAVY / ORANGE + logo).
5. ✅ Le workflow hors-grille est fonctionnel (alerte + validation + révocation).
6. ✅ Les smart buttons sur contact et opportunité affichent le bon compteur de devis ODK.
7. ✅ Un Admin Tarifaire peut ajouter un nouveau palier sans modification de code.
8. ✅ La checklist de recette du README est entièrement validée sur staging avant promotion en production.

---

## 9. Planning de déploiement

| Phase | Activité | Durée indicative |
|-------|----------|------------------|
| Phase 1 | Développement + tests unitaires | Réalisé |
| Phase 2 | Push sur dépôt Git odoo.sh → build staging | 1 jour |
| Phase 3 | Recette utilisateur sur staging | 2 à 5 jours |
| Phase 4 | Promotion en production + assignation des groupes | 1 jour |
| Phase 5 | Formation commerciaux (30 min) | 1 jour |

---

## 10. Contacts projet

- **Demandeur / Product Owner** : Eloi Lamort de Gail — elg@confero.fr
- **Direction Groupe** : Marc Lamort de Gail — mlg@confero.fr
- **Siège ODK** : 17 rue Tiphaine, 75015 Paris
- **Plateforme cible** : odoo.sh — Odoo 19

---

*Fin du cahier des charges.*
