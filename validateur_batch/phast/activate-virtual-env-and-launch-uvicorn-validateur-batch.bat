c:
cd C:\Environnements virtuels Python\ValidateurBatch314\Scripts
call activate 
d:
cd D:\tools\TERMINOLOGIE\DEV\SNOMED\interop-outil-nrc-validateur-batch\validateur_batch\phast
call uvicorn.exe api:app --host 0.0.0.0 --port 8004 > D:\Logs\Terminologie\DEV\ValidateurBatch\api-uvicorn.log

