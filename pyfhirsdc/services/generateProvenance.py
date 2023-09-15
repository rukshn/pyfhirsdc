from pyfhirsdc.services.generateChanges import parseChanges
from pyfhirsdc.config import get_defaut_fhir
from pyfhirsdc.serializers.utils import write_resource, get_resource_path
import datetime
import logging
import json

'''
    This generates the provanence resource, that will be used to track the changes in the ImplementationGuide resrouce
    The ImplementationGuide resource will track the details of the IG
    '''
logger = logging.getLogger("default")

def generateProvenance():
    dfs_changes = parseChanges()
    currentDateTime = datetime.datetime.now()
    currentDateTime = str(currentDateTime).strip()
    provenanceResrouce = get_defaut_fhir("Provenance")

    if dfs_changes is not None: 
        for index, row in dfs_changes.iterrows():
            provenanceResrouce['id'] = "Provenance-{0}".format(row['date'])
            provenanceResrouce['target'][0]['reference']  = "ImplementationGuide/_history/{0}".format(str(row['version']))
            provenanceResrouce['recorded'] = row['date'] 
            provenanceResrouce['occurredDateTime'] = row['date']
            provenanceResrouce['activity']['text'] = row['change']
            logger.info("Processing provenance resrouce {0}".format(row['version']))
            filePath = get_resource_path("Provenance", row['date'])
            write_resource(filePath, json.dumps(provenanceResrouce), encoding='str')