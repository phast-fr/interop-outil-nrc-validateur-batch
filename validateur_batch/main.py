#!/usr/bin/env python3

import argparse
import os
import os.path as op
import pandas as pd

from validateur_batch import io
from validateur_batch.object import batch, server
from validateur_batch.control import editorial_check, format_check
from validateur_batch.phast import utils

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("endpoint", type=str, help="Endpoint du FTS à utiliser")
    cli.add_argument("snapshot", type=str,
                     help="Chemin vers la snapshot de l'édition FR")
    cli.add_argument("date", type=str, help="Date de publication de l'édition FR")
    cli.add_argument("output", type=str, help="Dossier où sauvegarder les rapports")
    cli.add_argument("--val", type=str,
                     help="Chemin vers le CSV des concepts non modifiés")
    cli.add_argument("--add", type=str,
                     help="Chemin vers le CSV de l'onglet 'Description Additions'")
    cli.add_argument("--chg", type=str,
                     help="Chemin vers le CSV de l'onglet 'Description Changes'")
    cli.add_argument("--rep", type=str,
                     help="Chemin vers le CSV de l'onglet 'Description Replacement'")
    cli.add_argument("--ina", type=str,
                     help="Chemin vers le CSV de l'onglet 'Description Inactivations'")
    cli.add_argument("--login", type=str,
                     help="Login pour accéder au FTS")
    cli.add_argument("--pwd", type=str,
                     help="Mot de passe pour accéder au FTS")
    cli.add_argument("--versioning", action="store_true",
                     help="Activer la gestion des versions SNOMED CT sur le FTS")
    args = cli.parse_args()

    #utils.generate_excel_from_report(op.join(args.output, "check_results.csv"), op.join(args.output, "check_results_condenses.xlsx"))

    # Initialisation de la classe de gestion du FTS
    fts = server.Server(args.endpoint, args.login, args.pwd, versioning=args.versioning)

    # Création de la liste des fichiers
    print("\n## Imports batch ##")
    print("Lecture des imports batch...", end="\r")
    input = zip(
        [args.val, args.add, args.chg, args.rep, args.ina],
        ["VAL", "ADD", "CHG", "REP", "INA"]
    )
    list_b = [batch.Batch(f, t) for f, t in input if f is not None]
    print("Lecture des imports batch - OK")

    # for b in list_b:
    #     b.df = b.df.loc[1710:1720] # TODO : à supprimer, juste pour les tests

    # Initialiser la preview de la snapshot de l'édition FR
    print("\n## Snapshot FR ##")
    preview = io.read_snapshot(args.snapshot, args.date, list_b)
    
    print("\n\n## Respect du format ##")
    for b in list_b:
        # Vérification du respect du format
        format_checks = b.check_format(fts)
        format_checks.to_csv(
            op.join(args.output, f"{b.type}_format_checks.csv"),
            sep=";",
            index=False
        )
        # Appliquer les changements des batchs sur `data`
        if b.type != "VAL":
            preview.set_index("id", inplace=True)
            preview = b.apply_modif(preview)
            preview.reset_index(inplace=True)

    # Ajouter les FSN de l'édition INT à la preview
    fsn = preview.loc[:, ["conceptId"]].drop_duplicates("conceptId", ignore_index=True)
    fsn.loc[:, "FSN"] = [fts.get_fsn(sctid) for sctid in fsn.loc[:, "conceptId"]]
    preview = pd.merge(preview, fsn, how="left", on="conceptId")
    preview["FSN_no_sem"] = preview["FSN"].str.replace(r'[\(\[].*[\)\]]$', "", regex=True)
    preview = preview[["id", "active", "_type_", "conceptId", "FSN", "FSN_no_sem", "term",
                       "caseSignificanceId", "acceptabilityId"]]

    # Vérification du respect des règles éditoriales
    print("\n## Respect des règles éditoriales ##")
    rules = pd.read_csv(os.path.join(os.path.dirname(__file__), "rules.csv"),  dtype={"en": "string", "fr": "string", "id": "string", "pt": "Int64", "syn": "Int64"}, sep=";")
    terminology_anatomica = pd.read_csv(os.path.join(os.path.dirname(__file__), "Terminologia Anatomica - ancienne VS nouvelle nomenclature - 012026.csv"), dtype=str, sep=";", encoding="latin-1")
    preview = editorial_check.run_editorial_check(preview, rules, terminology_anatomica, fts )
    
    # Vérification du respect 1 concept = 1 PT
    preview = format_check.check_pt(preview)
    # Sauvegarde du fichier
    filepath = op.join(args.output, "check_results.csv")
    preview.to_csv(filepath, sep=";", index=False)
    print(f"\nAnalyse terminée et sauvegardée : {filepath}")

    # Génération d'un fichier excel, condensé du résultat, pour intégration dans le fichier de travail
    print("\n## Génération du fichier Excel ##")
    utils.generate_excel_from_report(filepath, op.join(args.output, "check_results_condenses.xlsx"))


