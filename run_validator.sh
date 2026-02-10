#!/bin/bash

NOW=`date '+%F_%Hh%M'`;
CTRL_ROOT_DIR="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/06 - Production/fichiers test livraison/contrôles"
PHAST_SOURCE_PATH="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/06 - Production/fichiers test livraison/Workbook v2 PHAST 202602101900.xlsx"
SIMED_SOURCE_PATH="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/06 - Production/fichiers test livraison/Fichiers SIMED modifiés/SIMED_Lot1_Perim_Int_2026-02-03_13h45_modifPHAST.xlsx"
SIMED_LOT2_SOURCE_PATH="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/06 - Production/fichiers test livraison/Simulation livraison SIMED perimetre post intermediaire.xlsx"
TRANFORMATION_TOOL_DIR="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/09 - Outils de production/Outil transformation des données/Debug"
TEMPLATE_PATH="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/05 - Suivi processus qualité/Formats de livraison/ms-translations-template_current.xlsx"
CACHE_PATH="/mnt/c/Users/Pierre-OlivierGRÉGOI/OneDrive - phastservices/SIMED/Marché ANS SNOMED-CT partagé SIMED-PHAST/06 - Production/valuesets/2026-02-05/all_batches_2026-02-05.csv"
PER_CONCEPT_RESULTS_FILENAME="check_results_condenses.xlsx"

PHAST_SOURCE_PATH_W=`wslpath -w "${PHAST_SOURCE_PATH}"`
SIMED_SOURCE_PATH_W=`wslpath -w "${SIMED_SOURCE_PATH}"`
SIMED_LOT2_SOURCE_PATH_W=`wslpath -w "${SIMED_LOT2_SOURCE_PATH}"`
TRANSFORMATION_OUTPUT_DIR_W=`wslpath -w "${TRANSFORMATION_OUTPUT_DIR}"`
TEMPLATE_PATH_W=`wslpath -w "${TEMPLATE_PATH}"`

echo "Chemin du fichier source PHAST dans windows : ${PHAST_SOURCE_PATH_W}"
echo "Chemin du fichier source SIMED dans windows : ${SIMED_SOURCE_PATH_W}"
echo "Chemin du fichier template dans windows : ${TEMPLATE_PATH_W}"

# Création du dossier de contrôle
CTRL_CURR_DIR="${CTRL_ROOT_DIR}/${NOW}"
printf "Création du dossier de contrôle : ${CTRL_CURR_DIR}\n"
mkdir -p "${CTRL_CURR_DIR}"

# Copie des fichiers sources
printf "\n#############################################################################\n"
printf "Copie des fichiers sources dans le dossier de contrôle...\n"
SOURCES_DIR="${CTRL_CURR_DIR}/01 - Sources"
mkdir -p "${SOURCES_DIR}"
cp "${PHAST_SOURCE_PATH}" "${SOURCES_DIR}/"
cp "${SIMED_SOURCE_PATH}" "${SOURCES_DIR}/"
cp "${SIMED_LOT2_SOURCE_PATH}" "${SOURCES_DIR}/"
printf "Fichiers sources copiés dans : ${SOURCES_DIR} : \n"
ls -l "${SOURCES_DIR}"

# Filtre sur les données intermédiaires
# printf "\n#############################################################################\n"
# printf "Filtrage des données intermédiaires et copie des résultats dans le dossier de contrôle...\n"
# INTERMEDIATE_DIR="${CTRL_CURR_DIR}/02 - Fitrage Intermédiaire"
# mkdir -p "${INTERMEDIATE_DIR}"
# uv run tools/filter_excel_by_value.py "${PHAST_SOURCE_PATH}" "${PHAST_INTERMEDIATE_OUTPUT}"
# cp "${PHAST_INTERMEDIATE_OUTPUT}" "${INTERMEDIATE_DIR}/"
# printf "Données intermédiaires filtrées copiées dans : ${INTERMEDIATE_DIR} : \n"
# ls -l "${INTERMEDIATE_DIR}"

# Copie des résultats de l'outil de transformation
printf "\n#############################################################################\n"
printf "Exécution de l'outil de transformation et copie des résultats dans le dossier de contrôle...\n"
TRANSFORMATION_DIR="${CTRL_CURR_DIR}/03 - Transformation"
TRANSFORMATION_DIR_W=`wslpath -w "${TRANSFORMATION_DIR}"`
TRANSFORMATION_TOOL_CPY_DIR="${CTRL_CURR_DIR}/05 - Outil de transformation"
mkdir -p "${TRANSFORMATION_DIR}"
mkdir -p "${TRANSFORMATION_TOOL_CPY_DIR}"
cp "${TRANFORMATION_TOOL_DIR}/"* "${TRANSFORMATION_TOOL_CPY_DIR}/"
xmlstarlet ed -u "configuration/appSettings/add[@key='InputFilePath1']/@value" -v "${PHAST_SOURCE_PATH_W}" \
    -u "configuration/appSettings/add[@key='InputFilePath2']/@value" -v "${SIMED_SOURCE_PATH_W}" \
    -u "configuration/appSettings/add[@key='InputFilePath3']/@value" -v "${SIMED_LOT2_SOURCE_PATH_W}" \
    -u "configuration/appSettings/add[@key='OutputDirectory']/@value" -v "${TRANSFORMATION_DIR_W}" \
    -u "configuration/appSettings/add[@key='TemplateOutputFilePath']/@value" -v "${TEMPLATE_PATH_W}" \
     "${TRANSFORMATION_TOOL_CPY_DIR}/ANS.TraductionsSIMED.exe.config" > "${TRANSFORMATION_TOOL_CPY_DIR}/ANS.TraductionsSIMED.exe.config.tmp" \
     && mv "${TRANSFORMATION_TOOL_CPY_DIR}/ANS.TraductionsSIMED.exe.config.tmp" "${TRANSFORMATION_TOOL_CPY_DIR}/ANS.TraductionsSIMED.exe.config"
"${TRANSFORMATION_TOOL_CPY_DIR}/ANS.TraductionsSIMED.exe" -TRADUCTION=O -CONTROLE=O
printf "Résultats de l'outil de transformation copiés dans : ${TRANSFORMATION_DIR}\n"
ls -l "${TRANSFORMATION_DIR}"

# Exécution du validateur
printf "\n#############################################################################\n"
printf "Exécution du validateur et copie des résultats dans le dossier de contrôle...\n"
VALIDATION_DIR="${CTRL_CURR_DIR}/04 - Validation"
rm -f output/*
mkdir -p "${VALIDATION_DIR}"
uv run \
    validateur_batch/main.py \
    "https://recette.phast.fr/resources-server/api/FHIR" \
    data/SnomedCT_ManagedServiceFR_PRODUCTION_FR1000315_20250621T120000Z/Snapshot/ \
    "20250621" \
    output/ \
    --add "`find "${TRANSFORMATION_DIR}" -iname 'Descriptions_Additions*'`" \
    --val "`find "${TRANSFORMATION_DIR}" -iname 'Concepts_Revus_Non_Modifiés*'`" \
    --rep "`find "${TRANSFORMATION_DIR}" -iname 'Descriptions_Replacements*'`" \
    --chg "`find "${TRANSFORMATION_DIR}" -iname 'Descriptions_Changes*'`" \
    --ina "`find "${TRANSFORMATION_DIR}" -iname 'Descriptions_Inactivations*'`" \
    --login "pierre-olivier.gregoire@phast.fr" \
    --pwd "Pierre-Olivier123*" \
    --cache "${CACHE_PATH}"
cp output/* "${VALIDATION_DIR}/"
printf "Résultats du validateur copiés dans : ${VALIDATION_DIR}\n"
ls -l "${VALIDATION_DIR}"

cp "${VALIDATION_DIR}/${PER_CONCEPT_RESULTS_FILENAME}" "`dirname "${PHAST_SOURCE_PATH}"`/check_results_per_concept.xlsx"
cp "${VALIDATION_DIR}/${PER_CONCEPT_RESULTS_FILENAME}" "`dirname "${SIMED_SOURCE_PATH}"`/check_results_per_concept.xlsx"