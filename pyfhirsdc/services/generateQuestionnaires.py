"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""


import numpy as np

from pyfhirsdc.config import get_dict_df, get_processor_cfg
from pyfhirsdc.converters.mappingConverter import (add_mapping_url,
                                                   get_questionnaire_mapping)
from pyfhirsdc.converters.questionnaireItemConverter import (
    convert_df_to_questionitems, init_questionnaire)
from pyfhirsdc.serializers.librarySerializer import generate_plan_defnition_lib
from pyfhirsdc.serializers.utils import get_resource_path, write_resource


def generate_questionnaires():
    dfs_questionnaire = get_dict_df()['questionnaires']

    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions)

## generate questinnaire and questionnaire response
def generate_questionnaire( name ,df_questions) :
    
    # try to load the existing questionnaire
    fullpath = get_resource_path("Questionnaire", name)
    print('processing quesitonnaire {0}'.format(name))
    # read file content if it exists
    questionnaire = init_questionnaire(fullpath, name)
    # clean the data frame
    
    df_questions_item = df_questions[df_questions.type != 'mapping'].dropna(axis=0, subset=['id']).set_index('id')
    df_questions_mapping = df_questions.dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_resource']).set_index('id')
    df_questions_lib = df_questions

    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    questionnaire = convert_df_to_questionitems(questionnaire, df_questions_item, strategy = 'overwriteDraft')
    #### StructureMap ####
    #structure_maps = get_structure_map_bundle(name, df_questions)
    #structure_maps = get_structure_maps(name, df_questions)
    mapping = get_questionnaire_mapping(name, df_questions_mapping)
    questionnaire = add_mapping_url(questionnaire, mapping)
    library = generate_plan_defnition_lib(questionnaire,df_questions_lib,'q')

    # write file
    write_resource(fullpath, questionnaire, get_processor_cfg().encoding)
    
    
    #CQL files 


    






