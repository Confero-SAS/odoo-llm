# Matrice ACL — odk_quote_generator

Référence interne pour les tâches #19 et #21. Les lignes correspondantes
seront ajoutées à `ir.model.access.csv` au fur et à mesure que les modèles
sont créés.

## Groupes (définis dans `odk_security.xml`)

| ID externe                        | Libellé                              | Hérite de                              |
|-----------------------------------|--------------------------------------|----------------------------------------|
| `group_odk_direction`             | Direction (lecture seule)            | —                                      |
| `group_odk_commercial`            | Commercial                           | `group_odk_direction` + Sales / CRM    |
| `group_odk_sales_manager`         | Manager Commercial                   | `group_odk_commercial` + Sales Manager |
| `group_odk_pricing_admin`         | Admin Tarifaire                      | `group_odk_sales_manager`              |

## Matrice cible (R = read, W = write, C = create, U = unlink)

| Modèle                    | Direction | Commercial | Manager  | Admin tarifaire |
|---------------------------|:---------:|:----------:|:--------:|:---------------:|
| `odk.pricing.catalog`     |     R     |     R      |    R     |    R W C U      |
| `odk.pricing.grid`        |     R     |     R      |    R     |    R W C U      |
| `odk.pricing.tier`        |     R     |     R      |    R     |    R W C U      |
| `sale.order` (devis ODK)  |     R     |   R W C    | R W C U  |    R W C U      |
| `crm.lead` (opportunité)  |     R     |   R W C    | R W C U  |    R W C U      |
| `res.partner`             |     R     |   R W C    | R W C    |    R W C U      |

## Convention XML ID

```
access_<model_underscored>_<group_suffix>
```

Exemple :

```csv
access_odk_pricing_grid_admin,odk.pricing.grid admin,model_odk_pricing_grid,group_odk_pricing_admin,1,1,1,1
access_odk_pricing_grid_commercial,odk.pricing.grid commercial,model_odk_pricing_grid,group_odk_commercial,1,0,0,0
access_odk_pricing_grid_direction,odk.pricing.grid direction,model_odk_pricing_grid,group_odk_direction,1,0,0,0
```

## Règles d'enregistrement (record rules) à implémenter

1. **Grilles tarifaires partagées multi-sociétés**
   - Modèle : `odk.pricing.grid`, `odk.pricing.tier`, `odk.pricing.catalog`
   - Domaine : `[('company_id', 'in', [False] + company_ids)]`
   - But : les grilles avec `company_id = False` sont visibles par toutes les filiales.

2. **Devis ODK cloisonnés par société**
   - Modèle : `sale.order` (filtré sur les devis générés par le module)
   - Domaine : `[('company_id', 'in', company_ids)]`
   - But : un commercial ne voit que les devis de sa(ses) société(s) courante(s).

3. **Override hors-grille réservé au Manager**
   - À implémenter en logique Python (champ `is_off_grid` + contrainte) plutôt
     qu'en record rule, car la restriction porte sur une transition d'état.
