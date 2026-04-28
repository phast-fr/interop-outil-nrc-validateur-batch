import os
import time
from typing import List
import re
import json
import pandas as pd
from validateur_batch import io
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from validateur_batch.object import server
from validateur_batch.control import editorial_check, format_check
from validateur_batch.phast import utils


# Load configuration
config_path = os.path.join(os.path.dirname(__file__), "config_api.json")
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

fts = server.Server(config['endpoint'], config['login'], config['pwd'], versioning=config.get("versioning", False), international=config.get("international", None))
desc_act_fr = io.read_active_desc_in_fr_ed(config['snapshot'], config['date'])
rules = pd.read_csv(config["rules"],  dtype={"en": "string", "fr": "string", "id": "string", "pt": "Int64", "syn": "Int64"}, sep=";")
terminology_anatomica = pd.read_csv(config["terminology_anatomica"], dtype=str, sep=";")

ecl_body_surface_region = fts.ecl("<< 127947003")
ecl_anatomical_structure = fts.ecl("<< 91723000")
ecl_pharmaceutical_biological_product = fts.ecl("<< 373873005")
ecl_physical_object = fts.ecl("<< 260787004")

app = FastAPI(
    title="Validateur Batch API",
    description="API pour la validation des libellés de concepts SNOMED CT en utilisant les règles définies pour le projet Validateur Batch",
    version="1.0.0"
)

class ConceptAControler(BaseModel):
    DescriptionId: str
    ConceptId: str
    Active: bool
    FSN: str
    PreferredTermEn: str
    Term: str
    CaseSignificanceId: str
    AcceptabilityId: str

class InputConceptDetails(BaseModel):
    Concepts: List[ConceptAControler]

class ControlledConcept(BaseModel):
    ConceptId: str
    RulesOnError: str

class ControlerLibellesResult(BaseModel):
    Success: bool
    Message: str
    StatusCode: int
    Result: List[ControlledConcept]

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Validateur Batch"}


@app.post("/controler_libelles", 
            response_model=ControlerLibellesResult,
            response_model_exclude_none=True,
            response_model_exclude_unset=True,)
async def controler_libelles(concepts_details: InputConceptDetails) -> ControlerLibellesResult:
    response = ControlerLibellesResult(Success=True, Message="Ok", StatusCode=200, Result=[])
    try:
        start = time.time()
        colonnes = ["id", "active", "conceptId", "FSN", "FSN_no_sem", "PT_EN", "term", "caseSignificanceId", "acceptabilityId"]
        preview = pd.DataFrame(columns=colonnes)

        for c in concepts_details.Concepts:
            preview = pd.concat([preview, pd.DataFrame([{
                "id": c.DescriptionId,
                "active": "1" if c.Active else "0",
                "conceptId": c.ConceptId,
                "FSN": c.FSN,
                "FSN_no_sem": re.sub(r'[\(\[].*[\)\]]$', "", c.FSN),
                "PT_EN": c.PreferredTermEn,
                "term": c.Term,
                "caseSignificanceId": c.CaseSignificanceId,
                "acceptabilityId": c.AcceptabilityId
            }])])
        
        preview.set_index("id", inplace=True)
        preview = editorial_check.run_editorial_check(preview, rules, terminology_anatomica, fts, desc_act_fr, ecl_body_surface_region, ecl_anatomical_structure, ecl_pharmaceutical_biological_product, ecl_physical_object)
        preview = format_check.check_pt(preview)
        combined = utils.combine_results(preview)

        response.Result = [
            ControlledConcept(ConceptId=row.Index, RulesOnError=str(row.errors))
            for row in combined.itertuples(index=True)
        ]
        print(time.time() - start)
    except Exception as ex:
        error_message = f"Erreur lors du contrôle des libellés : {ex}"
        response.Success = False
        response.Message = error_message
        response.StatusCode = 500

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)