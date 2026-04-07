# Validateur d'imports batch dans l'Authoring Platform

## À propos du projet
Ce projet a pour objectif de valider le format d'un ensemble de fichiers détaillant une liste de concepts à ne pas modifier et une liste de modifications correspondant aux fichiers d'import batch de l'Authoring Platform. Le validateur doit être utilisé avant tout import batch dans l'édition française.

## Prérequis
- Accès à un serveur FHIR contenant l'édition internationale (version du projet)
- Accès au dernier RF2 de l'édition nationale (dernière version publiée)
- Recommandé : accès au dernier RF2 de l'édition internationale
- Recommandé : fichier de définition du périmètre de travail

## Installation du projet
```shell
# Exemple avec le gestionnaire d'environnement venv
python3 -m venv ~/chemin_vers_environnement/mon_environnement
source ~/chemin_vers_environnement/mon_environnement/bin/activate

# Récupérer le projet
git clone git@github.com:ansforge/interop-outil-nrc-validateur-batch.git
cd ./interop-outil-nrc-validateur-batch/
python3 -m pip install -e .
```

## Utilisation du projet
Le projet nécessite plusieurs données en entrée :
- [**OBLIGATOIRE**] Endpoint d'un serveur FHIR contenant l'édition internationale de référence pour le projet
- [**OBLIGATOIRE**] Snapshot de la dernière release de l'édition française
- [**OBLIGATOIRE**] Date de publication de la dernière release de l'édition française
- [**OBLIGATOIRE**] Dossier de sauvegarde du fichier de résultats
- [*OPTIONNEL*] `--val` : Chemin du fichier des concepts sans modification
- [*OPTIONNEL*] `--add` : Chemin du fichier des descriptions à ajouter
- [*OPTIONNEL*] `--chg` : Chemin du fichier des métadonnées de descriptions à modifier
- [*OPTIONNEL*] `--rep` : Chemin du fichier des descriptions à remplacer par une nouvelle traduction
- [*OPTIONNEL*] `--ina` : Chemin du fichier des descriptions à inactiver
- [*OPTIONNEL*] `--login` : Login pour accéder au FTS
- [*OPTIONNEL*] `--pwd` : Mot de passe pour accéder au FTS
- [*OPTIONNEL*] `--international` : Chemin vers les RF2 de l'édition internationale (alternative à la récupération via le FTS)
- [*OPTIONNEL*] `--cache` : Chemin vers le répertoire de cache (défaut : `./cache`)
- [*OPTIONNEL*] `--scope` : Chemin vers le fichier JSON définissant le périmètre d'analyse

```shell
./validateur_batch/main.py "endpoint_FTS" "chemin_vers_release_fr/Snapshot/" "YYYYMMDD" "dossier_sauvegarde" --val "chemin_fichier_concept_sans_modification" --add "chemin_fichier_descriptions_à_ajouter" --chg "chemin_fichier_metadonnees_à_modifier" --rep "chemin_fichier_descriptions_à_remplacer" --ina "chemin_fichier_descriptions_à_inactiver" --login "login" --pwd "mot_de_passe" --international "chemin_vers_rf2_international" --cache "chemin_vers_cache" --scope "scope.json"
```

## Fichiers RF2
- Téléchargement de la dernière version de l'édition française SNOMED CT : https://smt.esante.gouv.fr/terminologie-snomed-ct-fr/
- Téléchargement de la dernière version de l'édition internationale SNOMED CT : https://smt.esante.gouv.fr/terminologie-snomed-ct/

Attention pour le moment l'outil attend :
* le chemin vers le sous-répertoire "Snapshot" pour l'édition nationale française (deuxième paramètre positionnel)
* le chemin vers le répertoire racine de l'édition internationale, contenant le fichier `release_package_information.json` (paramètre --international)

## Cache
Le chargement des fichiers RF2 de l'édition internationale est long. Lors de la première exécution, les données utiles sont stockées dans des
fichiers parquet dans le répertoire de cache (par défaut `./cache`). À l'exécution suivante, ces fichiers sont chargés, évitant la lecture des fichiers RF2.

## Fichier de scope
Le fichier de scope permet de définir le périmètre d'analyse, c'est-à-dire les concepts SNOMED CT sur lesquels les vérifications seront effectuées. Sans ce fichier, le périmètre est déduit des concepts présents dans les fichiers CSV de transformation.

Le fichier est au format JSON et contient un tableau de sections. Chaque section est un objet avec deux attributs :

- `name` : nom de la section (utilisé dans les rapports de résultats)
- `ecl` : expression ECL définissant les concepts de la section (évaluée via le FTS)

```json
[
  {
    "name": "Structure corporelle",
    "ecl": "<< 123037004 |Body structure (body structure)|"
  }
]
```

## Fichiers d'entrée valides
Ce projet peut valider jusqu'à 5 fichiers différents dans le cadre d'une tâche de traduction ou révision de traductions. Tous ces fichiers sont à mettre au format CSV.

### Concepts sans modification
Le chemin vers ce fichier est passé par l'argument ```--val```. Les colonnes attendues sont :
```python
["Concept ID", "FSN"]
```

### Descriptions à ajouter
Ce fichier correspond à l'onglet **Description Additions** du template d'import batch de SNOMED International.

Le chemin vers ce fichier est passé par l'argument ```--add```. Les colonnes attendues sont :
```python
["Concept ID", "GB/US FSN Term (For reference only)", "Preferred Term (For reference only)", "Translated Term", "Language Code", "Case significance", "Type", "Language reference set", "Acceptability"]
```

### Métadonnées de descriptions à modifier
Ce fichier correspond à l'onglet **Description Changes** du template d'import batch de SNOMED International.

Le chemin vers ce fichier est passé par l'argument ```--chg```. Les colonnes attendues sont :
```python
["Description ID", "Preferred Term (For reference only)", "Term (For reference only)", "Case significance", "Type", "Language reference set", "Acceptability"]
```

### Descriptions à remplacer par une nouvelle traduction
Ce fichier correspond à l'onglet **Description Replacements** du template d'import batch de SNOMED International.

Le chemin vers ce fichier est passé par l'argument ```--rep```. Les colonnes attendues sont :
```python
["Concept ID", "Description ID", "Preferred Term (For reference only)", "Term (For reference only)", "Inactivation Reason", "Association Target ID1", "Association Target ID2", "Association Target ID3", "Association Target ID4", "New Replacement Description ID", "Replacement term (For reference only)", "New Translated Term", "Language Code", "Case significance", "Type", "Language reference set", "Acceptability"]
```

### Descriptions à inactiver
Ce fichier correspond à l'onglet **Description Inactivations** du template d'import batch de SNOMED International.

Le chemin vers ce fichier est passé par l'argument ```--ina```. Les colonnes attendues sont :
```python
["Description ID Or Term", "Language Code (require if the term is specified)", "Concept ID (Optional)", "Preferred Term (For reference only)", "Term (For reference only)", "Inactivation Reason", "Association Target ID1", "Association Target ID2", "Association Target ID3", "Association Target ID4"]
```

## Règles implémentées
Les tableaux ci-dessous indiquent les [règles éditoriales de l'édition française SNOMED CT](https://ansforge.github.io/interop-nrc-guide-editorial-snomed-edition-fr/) qui sont implémentées et vérifiées par cet outil.

### Règles génériques
#### Abréviations, acronymes et sigles (ab)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ab1                  |            ❌            |
| ab2                  |            ❌            |
| ab3                  |            ❌            |

#### Articles (ab)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ar1                  |            ❌            |
| ar2                  |            ✅            |
| ar3                  |            ❌            |
| ar4-FR               |            ✅            |
| ar6                  |            ✅            |
| ar7                  |            ❌            |

#### Caractères séparateurs ou de ponctuation (se)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| se1                  |            ❌            |
| se2                  |            ✅            |
| se3                  |            ✅            |
| se4                  |            ✅            |
| se5                  |            ❌            |
| se6                  |            ❌            |
| se7                  |            ❌            |
| se8                  |            ❌            |
| se9                  |            ❌            |
| se10                 |            ✅            |
| se11                 |            ❌            |

#### Lettres grecques (gr)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| gr1                  |            🟡           |

#### Lettres ligaturées (ll)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ll1                  |            ❌           |

#### Noms propres (np)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| np1                  |            ❌           |

#### Rectification orthographiques de 1990 (or)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| or2                  |            ❌            |
| or3                  |            ❌            |
| or4                  |            ✅            |
| or5                  |            ❌            |
| or6                  |            ❌            |

#### Style général et syntaxe (ss)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ss1                  |            🟡            |
| ss2                  |            ❌            |
| ss3                  |            ❌            |
| ss4                  |            ❌            |
| ss5                  |            ❌            |
| ss6                  |            ❌            |
| ss7                  |            ❌            |

#### Symboles scientifiques, chiffres et nombres (sc)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| sc1                  |            ❌            |
| sc2                  |            ❌            |
| sc3                  |            ❌            |
| sc4                  |            ❌            |
| sc5                  |            ❌            |
| sc6                  |            ❌            |
| sc7                  |            ❌            |
| sc8                  |            ❌            |

#### Temps des verbes (tv)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| tv1                  |            ❌            |
| tv2                  |            ❌            |
| tv3                  |            ❌            |
| tv4                  |            ❌            |

#### Unités de mesure (um)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| um1                  |            ❌            |
| um2                  |            ❌            |
| um3                  |            ❌            |
| um4                  |            ❌            |
| um5                  |            ❌            |
| um6                  |            ❌            |
| um7                  |            ❌            |
| um8                  |            ❌            |

### Règles spécifiques aux hiérarchies
#### Constatation clinique - Sous-hiérarchie constatation (co)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| co2                  |            ✅            |
| co5                  |            ❌            |
| co6-FR               |            ✅            |

#### Constatation clinique - Sous-hiérarchie maladie (pa)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| pa2                  |            ❌            |
| pa3                  |            ✅            |
| pa3.1                |            ✅            |
| pa4                  |            ✅            |
| pa5                  |            ❌            |
| pa6                  |            ✅            |
| pa7                  |            ✅            |
| pa8                  |            ✅            |
| pa9                  |            ✅            |
| pa10                 |            ❌            |
| pa11                 |            ❌            |

#### Échantillon (ec)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ec2                  |            ✅            |
| ec4                  |            ✅            |
| ec5                  |            ❌            |
| ec6                  |            ❌            |

#### Environnement ou lieu géographique - Sous-hiérarchie environnement (en)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| en1-FR               |            ❌            |
| en2-FR               |            ❌            |
| en3-FR               |            ❌            |
| en4                  |            ❌            |
| en5                  |            ❌            |
| en6-FR               |            ❌            |

#### Environnement ou lieu géographique - Sous-hiérarchie région géographique et/ou politique du monde (ge)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ge1                  |            ❌            |
| ge2                  |            ❌            |

#### Objet physique (sb)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| sb1                  |            ✅            |
| sb2                  |            ✅            |
| sb3                  |            ✅            |

#### Organisme (ho)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| ho1                  |            ❌            |
| ho3                  |            ❌            |
| ho4                  |            ❌            |
| ho5                  |            ❌            |
| ho6                  |            ❌            |
| ho7                  |            ❌            |
| ho8                  |            ❌            |
| ho9                  |            ❌            |
| ho10                 |            ❌            |
| ho11                 |            ❌            |

#### Procédure (pr)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| pr2                  |            ✅            |
| pr3                  |            ✅            |
| pr4                  |            ✅            |
| pr5                  |            ❌            |
| pr6                  |            ❌            |
| pr7                  |            ❌            |
| pr8                  |            ❌            |
| pr9                  |            ✅            |
| pr10                 |            ✅            |
| pr12                 |            ✅            |
| pr13                 |            ✅            |
| pr14                 |            ✅            |
| pr15-FR              |            ✅            |

#### Produit pharmaceutique ou biologique (me)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| me1                  |            ✅            |
| me2-FR               |            ✅            |
| me3                  |            ✅            |
| me4                  |            ✅            |

#### Situation avec contexte explicite (hs)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| hs1                  |            ✅            |

#### Structure corporelle (bs)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| bs2                  |            ✅            |
| bs3                  |            ✅            |
| bs4                  |            ✅            |
| bs5                  |            ✅            |
| bs6                  |            ✅            |
| bs7                  |            ✅            |
| bs8                  |            ✅            |
| bs9                  |            ✅            |
| bs10-FR              |            ✅            |
| bs11-FR              |            ✅            |
| bs12                 |            ✅            |
| bs13                 |            ✅            |

#### Substance (su)
| Identifiant de règle | Statut d'implémentation |
| -------------------- | :---------------------: |
| su1-FR               |            ✅            |
| su2-FR               |            ❌            |
| su3-FR               |            ✅            |
| su4-FR               |            ❌            |
| su5-FR               |            ❌            |
| su6-FR               |            ❌            |
| su7-FR               |            ❌            |
| su8-FR               |            ✅            |

## Licence
Sous licence MIT, voir le fichier `LICENSE` pour plus d'informations.