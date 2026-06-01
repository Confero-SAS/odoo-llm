# ODK Quote Generator

**Module Odoo 19 — Générateur de devis automatique ODK**

Auteur : ODK / Groupe Confero — Direction des Opérations
Licence : OPL-1
Version : 19.0.2.0.7

---

## 1. Présentation

Ce module ajoute à Odoo 19 un générateur de devis dédié à l'activité ODK
(éditeur du logiciel de facturation). Il s'appuie sur deux catalogues
tarifaires configurables (Packs Factures + Abonnement ODK) et permet aux
commerciaux de produire un devis chiffré en quelques clics, directement
intégré au pipeline `sale.order`, à la fiche contact (`res.partner`) et à
l'opportunité (`crm.lead`).

### Catalogues V1

| Catalogue | Paliers | Offres | Engagements | Particularités |
|-----------|---------|--------|-------------|----------------|
| Packs Factures (V4) | S / M / L / XL / XXL (5) | Offre 1 spot 0,22 € — Offre 2 bundle + PA spot 0,28 € | 12 / 24 / 36 mois | Plancher 0,18 € HT/facture |
| Abonnement ODK (V1) | XS / S / M / L / XL / XXL (6) | Avec PA ODK — Avec PA tierce surchargée | 12 / 24 / 36 mois | 8 fonctionnalités, dépassements caisses (+4 €/mois) et transactions (+0,008 €/tx) |

### Fonctionnalités

- **Devis mixte** : un même devis peut combiner une offre Packs Factures
  **et** une offre Abonnement ODK. Le wizard propose deux sections
  activables indépendamment (cases *Inclure Packs Factures* / *Inclure
  Abonnement ODK*), chacune avec sa grille, son engagement et son aperçu.
- Grilles tarifaires partagées multi-sociétés, reconfigurables sans code.
- Wizard de saisie : nombre de magasins / caisses / volume → devis généré.
- Devis injecté dans `sale.order` et rattaché à `res.partner` + `crm.lead`.
- **Rapport PDF au look « one-pager »** ODK (NAVY #1F3864 / ORANGE #ED7D31) :
  en-tête blanc à liseré orange + logo, badge de mise en avant, titres
  soulignés, tables à en-tête NAVY, pied de page gris confidentiel. Affiche
  les conditions des deux sections pour un devis mixte.
- Gestion fine des droits via 4 groupes métier.
- Détection automatique des devis hors-grille (prix override) ligne à ligne,
  avec workflow de validation par un manager.

---

## 2. Architecture du module

```
odk_quote_generator/
├── __manifest__.py
├── README.md
├── data/
│   ├── odk_catalogs.xml          # Catalogues Packs + Abonnement
│   ├── odk_packs_factures.xml    # Grille V4 Packs Factures
│   └── odk_abonnement.xml        # Grille V1 Abonnement ODK
├── models/
│   ├── odk_pricing_catalog.py    # Catalogue tarifaire
│   ├── odk_pricing_grid.py       # Grille (catalogue x offre)
│   ├── odk_pricing_tier.py       # Palier tarifaire + moteur de calcul
│   ├── sale_order.py             # Champs ODK sur le devis
│   ├── sale_order_line.py        # Champs ODK sur la ligne
│   ├── res_partner.py            # Smart button devis ODK
│   └── crm_lead.py               # Smart button devis ODK
├── reports/
│   ├── odk_quote_report.xml      # Paperformat + ir.actions.report
│   └── odk_quote_report_templates.xml  # 3 templates QWeb
├── security/
│   ├── odk_security.xml          # 4 groupes + hiérarchie implied_ids
│   └── ir.model.access.csv       # ACL des 4 modèles
├── static/description/
│   ├── icon.png
│   └── logo_odk.png
├── views/
│   ├── odk_pricing_views.xml     # Catalogue / grille / palier
│   ├── sale_order_views.xml      # Onglet ODK + colonnes + filtres
│   ├── res_partner_views.xml     # Smart button
│   ├── crm_lead_views.xml        # Smart button
│   └── odk_menus.xml             # Menu racine ODK Devis
└── wizards/
    ├── quote_generator_wizard.py
    └── quote_generator_wizard_views.xml
```

---

## 3. Groupes de sécurité

| Groupe technique | Rôle métier | Droits |
|------------------|-------------|--------|
| `group_odk_commercial` | Commercial ODK | Crée et modifie ses devis dans la grille, déclenche le wizard. |
| `group_odk_sales_manager` | Manager Commercial ODK | Valide les devis hors-grille (override prix). Hérite de `commercial`. |
| `group_odk_pricing_admin` | Admin Tarifaire ODK | Gère catalogues, grilles, paliers. Hérite de `sales_manager`. |
| `group_odk_direction` | Direction ODK | Consultation transverse en lecture seule. Hérite de `commercial`. |

La hiérarchie est implémentée via `implied_ids` : un Admin Tarifaire
hérite automatiquement des droits Manager et Commercial.

---

## 4. Installation locale (test)

### Prérequis

- Odoo 19 community ou enterprise
- Python 3.11+
- PostgreSQL 14+

### Étapes

```bash
# 1. Cloner le module dans le dossier addons custom
cd /opt/odoo/custom-addons
git clone <repo> odk_quote_generator

# 2. Mettre à jour la liste des modules
./odoo-bin -c odoo.conf -u base --stop-after-init

# 3. Installer le module
./odoo-bin -c odoo.conf -i odk_quote_generator --stop-after-init

# 4. Démarrer Odoo
./odoo-bin -c odoo.conf
```

### Assignation des groupes (premier démarrage)

1. Se connecter en administrateur.
2. **Paramètres › Utilisateurs et sociétés › Utilisateurs**.
3. Pour chaque utilisateur ODK, dans l'onglet **Droits d'accès**, cocher
   le bon groupe sous la catégorie **Sales › ODK Devis**.

---

## 5. Déploiement sur odoo.sh

### 5.1 Pré-requis odoo.sh

- Projet odoo.sh actif (version Odoo 19) avec accès admin.
- Dépôt Git connecté (GitHub / GitLab / Bitbucket).
- Branche cible : `staging` pour validation, `production` après recette.

### 5.2 Procédure de déploiement

#### Étape 1 — Ajout du module au dépôt

```bash
# Sur votre poste local
git clone <url-du-depot-odoo-sh>
cd <repo>

# Copier le module dans le dépôt
cp -r /chemin/vers/odk_quote_generator ./

# Vérifier la structure
ls odk_quote_generator/__manifest__.py

# Commit + push sur la branche staging
git checkout staging
git add odk_quote_generator/
git commit -m "Ajout module odk_quote_generator v19.0.1.0.0"
git push origin staging
```

#### Étape 2 — Build automatique sur odoo.sh

1. Le push déclenche un **build** automatique sur la branche `staging`.
2. Dans l'interface odoo.sh, surveiller l'onglet **Builds** → statut doit
   passer à **Updating**.
3. Une fois le build vert, ouvrir l'instance staging.

#### Étape 3 — Installation du module

Sur l'instance staging :

1. **Apps** → mode développeur activé → **Mettre à jour la liste des modules**.
2. Rechercher *ODK - Générateur de Devis Automatique*.
3. Cliquer **Installer**. L'installation charge automatiquement :
   - Les 4 groupes de sécurité et les ACL.
   - Les 2 catalogues tarifaires + les grilles + les paliers.
   - Les vues, menus, wizard et rapport PDF.

#### Étape 4 — Recette utilisateur sur staging

Voir checklist § 6 ci-dessous.

#### Étape 5 — Promotion en production

1. Sur odoo.sh, ouvrir la branche `staging`.
2. Cliquer **Merge in production** (ou faire un PR `staging → production`).
3. Le build production se lance automatiquement.
4. Vérifier l'absence d'erreur dans **Logs › install.log**.
5. Sur la production, **Apps › Mettre à jour la liste › Installer** le
   module (si pas encore installé) ou **Mettre à jour** (sinon).

### 5.3 Mises à jour ultérieures

Pour toute évolution (nouveau palier, nouvelle offre, correctif) :

```bash
# Bump la version dans __manifest__.py (ex: 19.0.1.0.1)
# Commit + push sur staging
git push origin staging
# Sur staging : Apps › <module> › Mettre à jour
# Recette → merge en production
```

> **Important** : pour que les modifications de données XML
> (`data/odk_*.xml`) soient rejouées, il faut systématiquement
> **Mettre à jour** le module (et non simplement redémarrer).

---

## 6. Checklist de recette

À exécuter sur staging avant promotion en production.

### Sécurité
- [ ] Un utilisateur avec le seul groupe **Commercial** voit le menu *ODK
      Devis* et peut ouvrir *Configuration* en **lecture seule** (il consulte
      catalogues / grilles / paliers mais les boutons *Créer* / *Modifier* y
      sont absents).
- [ ] Un utilisateur **Manager** voit le bouton **Valider hors-grille** sur
      un devis ODK dont le prix a été overridé.
- [ ] Un utilisateur **Admin Tarifaire** voit dans *ODK Devis ›
      Configuration › Grilles tarifaires* le bouton **Créer** et peut ajouter
      un nouveau palier (les autres rôles ne le peuvent pas).
- [ ] Un utilisateur **Direction** voit le smart button *Devis ODK* sur la
      fiche contact, mais ne peut rien modifier.

### Fonctionnel — Packs Factures
- [ ] Ouvrir le wizard, sélectionner un client, catalogue **Packs
      Factures**, grille **Offre 1**, engagement **24 mois**, volume
      annuel **120 000**. Le palier doit être détecté automatiquement et
      le prix unitaire affiché en aperçu.
- [ ] Cliquer **Générer le devis** → un `sale.order` est créé avec une
      ligne forfait et le champ `odk_is_quote` à vrai.
- [ ] Imprimer **Devis ODK** depuis le devis → le PDF s'ouvre aux couleurs
      ODK avec le bloc *Conditions tarifaires ODK*.

### Fonctionnel — Abonnement
- [ ] Wizard, catalogue **Abonnement ODK**, **Offre PA ODK**, engagement
      **36 mois**, **15 magasins**, **45 caisses**, **800 000 tx**.
- [ ] L'aperçu doit afficher : base mensuelle, éventuel dépassement
      caisses, éventuel dépassement transactions, total mensuel.
- [ ] Le devis généré comporte 1 à 3 lignes selon les dépassements.

### Hors-grille / validation
- [ ] Modifier manuellement le `price_unit` d'une ligne pour qu'il
      diverge du `odk_expected_unit_price`. La bannière *Hors-grille* doit
      apparaître.
- [ ] Connecté en **Manager**, cliquer **Valider hors-grille** → bannière
      verte avec date et utilisateur.

### Rapport PDF
- [ ] Logo ODK présent en en-tête, bandeau NAVY + liseré ORANGE.
- [ ] Pied de page avec nom de société, TVA, pagination, site web.
- [ ] Bloc *Conditions tarifaires ODK* visible avec catalogue / grille /
      palier / engagement.
- [ ] Si devis hors-grille validé, badge orange *Hors-grille validé par
      … le …* visible.

### Pipeline
- [ ] Sur la fiche **Contact**, smart button *Devis ODK* affiche le bon
      compteur et ouvre la liste filtrée.
- [ ] Idem sur la fiche **Opportunité** (CRM).
- [ ] Dans la liste des devis, les filtres *Devis ODK*, *Hors-grille*,
      *Hors-grille validé* fonctionnent.

---

## 7. Configuration tarifaire

### Ajouter un nouveau palier

1. **ODK Devis › Configuration › Grilles tarifaires** → ouvrir la grille
   concernée.
2. Dans l'onglet **Paliers**, cliquer **Ajouter une ligne**.
3. Renseigner code, libellé, bornes volumétriques (ou nombre de
   magasins/caisses pour le catalogue Abonnement), prix unitaire ou
   forfait mensuel, inclus, surcharges.
4. Enregistrer. Le palier est immédiatement disponible dans le wizard.

### Créer une nouvelle offre

1. **ODK Devis › Configuration › Grilles tarifaires** → **Créer**.
2. Sélectionner le catalogue parent, nommer la grille, choisir le type
   (volume / network), définir l'éventuel plancher tarifaire.
3. Ajouter les paliers comme ci-dessus.

### Ajouter un catalogue (nouveau produit ODK)

1. **ODK Devis › Configuration › Catalogues tarifaires** → **Créer**.
2. Définir code, nom, type (`volume` ou `network`), produit Odoo associé.
3. Créer ensuite une ou plusieurs grilles rattachées.

---

## 8. Dépannage

| Symptôme | Cause probable | Résolution |
|----------|----------------|------------|
| Le menu *ODK Devis* n'apparaît pas après installation | Utilisateur sans groupe ODK | Assigner au moins `group_odk_commercial` via *Paramètres › Utilisateurs*. |
| Wizard : *Aucun palier trouvé* | Volume / magasins hors bornes de tous les paliers | Vérifier la grille ; ajouter un palier couvrant la plage. |
| PDF généré sans couleurs | Asset CSS non chargé | Mettre à jour le module (le CSS `static/src/css/odk_report.css` est injecté dans le bundle `web.report_assets_common` à l'install/upgrade). |
| Bannière *Hors-grille* toujours présente après validation | Le prix a été remodifié après validation | La validation est révoquée automatiquement à chaque changement de `price_unit`. Faire revalider par un manager. |
| Smart button *Devis ODK* à 0 sur un contact qui a des devis | Les devis n'ont pas `odk_is_quote=True` (créés avant install, ou hors wizard) | Le filtre se base sur ce flag ; soit re-générer via wizard, soit mettre à jour manuellement le champ. |
| Erreur *External ID not found: odk_quote_generator.xxx* au démarrage | Ordre de chargement du `__manifest__.py` cassé | Restaurer l'ordre : security → data → views (menus parents avant sub-menus) → wizards → reports. |

### Logs odoo.sh

```bash
# Sur odoo.sh, onglet Logs de la branche concernée :
- install.log     # Erreurs d'installation / mise à jour
- odoo.log        # Logs runtime (recherche "odk_quote_generator")
```

---

## 9. Pistes d'évolution (à arbitrer)

Aucune évolution post-V1 n'est engagée à ce stade. Pistes possibles
soumises à arbitrage du Product Owner :

- Module sœur `odk_contract_generator` pour générer le contrat PDF
  signable à partir du devis accepté.
- Tableau de bord Direction (mix produit, taux d'override, marge par
  commercial).

---

## 10. Contact

- **Maintainer** : ODK — Direction des Opérations
- **Contact projet** : Eloi Lamort de Gail — elg@confero.fr
- **Siège ODK** : 17 rue Tiphaine, 75015 Paris
- **Documentation Odoo 19** : https://www.odoo.com/documentation/19.0/
