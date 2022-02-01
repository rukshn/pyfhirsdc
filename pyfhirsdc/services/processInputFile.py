from pyfhirsdc.serializers.inputFile import read_input_file, parse_sheets
from pyfhirsdc.serializers.json import read_json
from pyfhirsdc.config import *
from pyfhirsdc.services.generateCodeSystem import generate_custom_code_system
from .generateQuestionnaires import generate_questionnaires
import os
import pandas as pd
import re



def process_input_file(conf):
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        input_file = read_input_file(get_processor_cfg().inputFile)
        if input_file is not None:
            dfs_questionnaire, dfs_decision_table,\
                df_value_set, df_care_plan,\
                df_choice_column, df_cql = parse_sheets(input_file, get_processor_cfg().excudedWorksheets)        
            # generate questionnaire
            generate_questionnaires(dfs_questionnaire, df_value_set, df_choice_column)

            # generate profiles

            # generate the CodeSystem
            generate_custom_code_system(dfs_questionnaire, df_value_set)   
            # generate the valueSet

            # generate conceptMap

            # generate the DE CQL 

            # generate the Concept CQL 

            # generate planDefinition


            # generate carePlane


