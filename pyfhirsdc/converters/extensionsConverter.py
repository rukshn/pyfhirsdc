import re
from distutils.util import strtobool

from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.extension import Extension
from fhir.resources.fhirtypes import Canonical, ExpressionType, QuantityType

from pyfhirsdc.config import get_fhir_cfg
from pyfhirsdc.converters.utils import (clean_name, get_fpath,
                                        get_resource_url, inject_config)


def get_dropdown_ext():
 return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
    valueCodeableConcept = CodeableConcept(
            coding = [Coding( 
                system = "http://hl7.org/fhir/questionnaire-item-control",
                code = "drop-down",
                display = "Drop down")],
            text ="Drop down")
)
 
 
def get_subquestionnaire_ext(questionnaire_id):
 return Extension(
    url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-subQuestionnaire",
    valueCanonical = Canonical(get_resource_url('Questionnaire',questionnaire_id))
    )


def get_open_choice_ext():
 return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
    valueCodeableConcept = CodeableConcept(
            coding = [Coding( 
                system = "http://hl7.org/fhir/questionnaire-item-control",
                code = "open-choice",
                display = "Open choice")],
            text ="Open choice")
)    


def get_variable_extension(name,expression,df_questions):
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/variable",
        valueExpression = ExpressionType(
                name = name,
                language = "text/fhirpath",
                expression = convert_reference_to_firepath(expression, df_questions)))


def get_candidate_expression_ext(desc, uri):
    if desc is not None and uri is not None:
        return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-candidateExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "application/x-fhir-query",
                expression = uri))
    else:
        return None

def get_choice_column_ext(path, label, width, for_display):
    if path is not None and label is not None:
        choice_extension = Extension(
            url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-choiceColumn",
            extension = [
                Extension( 
                    url = "path",
                    valueString = path),
                Extension(
                    url = "label",
                    valueString = label)            
            ])
        if width is not None:
            choice_extension.extension.append(Extension( 
                url = "width",
                valueQuantity = QuantityType (
                    value = width,
                    system = "http://unitsofmeasure.org",
                    code = "%"
                )))
        if for_display is not None:
            choice_extension.extension.append(Extension( 
                url = "forDisplay",
                valueBoolean = bool(strtobool(str(for_display)) )))
        return choice_extension
    else:
        return None

def get_structure_map_extension(extentions, uri):
    if extentions is None:
        extentions = []
    if  uri is not None:
        sm_ext = Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-targetStructureMap",
        valueCanonical=  Canonical(uri)
        )
        if extentions is None or len(extentions) == 0:
            return [sm_ext]
        else:
            append_unique(extentions, sm_ext, True)
    return extentions
# exp  expression::severity
# message human::requirements
def get_constraint_exp_ext(id,expr, human):
    expr_parts = expr.split('::')
    human_parts = human.split('::')
    if len(human_parts)==2:
        human = human_parts[0]
        severity = human_parts[1]
    elif len(human_parts)==1:
        severity = 'error'
    else:
        print("Error, missing constraint message")
    if len(expr_parts)==2:
        expr = expr_parts[0]
        requirements = expr_parts[1]
    elif len(expr_parts)==1:
        requirements = None
    else:
        print("Error, missing constraint message")        

    
    ext =  Extension(
            url ="http://hl7.org/fhir/StructureDefinition/questionnaire-constraint",
            extension = [
                Extension( 
                    url = "key",
                    valueId= id),
                Extension( 
                    url = "expression",
                    valueExpression= ExpressionType(
                language = "text/fhirpath",
                expression = expr)),
                Extension( 
                    url = "severity",
                    valueCode= severity),
                Extension( 
                    url = "human",
                    valueString= severity) 
            ])
    if requirements is not None:
        ext.extension.append(Extension( 
                    url = "requirements",
                    valueString= requirements))
    return ext

def append_unique(extentions, new_ext, replace = False):
    nofound = True
    for ext in extentions:
        if replace and ext.url == new_ext.url:
            extentions.remove(ext)
        elif ext == new_ext:
            nofound = False
    if nofound:
        extentions.append(new_ext) 

def get_checkbox_ext():
    return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
    valueCodeableConcept = CodeableConcept(
            coding = [Coding( 
                system = "http://hl7.org/fhir/questionnaire-item-control",
                code = "check-box",
                display = "Check-box")],
            text ="Check-box")
    )
def get_unit_ext(unit):
    #https://build.fhir.org/valueset-http://unitsofmeasure.org
    # value set https://build.fhir.org/valueset-ucum-common.html
    unit_part = unit.split('::')
    if len(unit_part) == 2:
        return Extension(
            url ="http://hl7.org/fhir/StructureDefinition/questionnaire-unit",
            valueCoding = Coding(
                system = "http://unitsofmeasure.org",
                code = unit_part[1],

            )
        )
# slider_part[1] : min
# slider_part[2] : increment
# slider_part[3] : max
def get_slider_ext(slider,label):
    slider_part = slider.split('::')
    if len(slider_part) == 4:
        return [Extension(
            url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
            valueCodeableConcept = CodeableConcept(
                coding = [Coding(
                 system = "http://hl7.org/fhir/questionnaire-item-control",
                code = 'slider'
                )],
                text=label

            )
        ),
        Extension(
            url="http://hl7.org/fhir/StructureDefinition/minValue",
            valueInteger= slider_part[1]
        ),
        Extension(
            url="http://hl7.org/fhir/StructureDefinition/questionnaire-sliderStepValue",
            valueInteger= slider_part[2]
        ),
        Extension(
            url="http://hl7.org/fhir/StructureDefinition/maxValue",
            valueInteger=slider_part[3]
        )
        ]

def get_hidden_ext():
    return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-hidden",
    valueBoolean = True
    )

    # if yes recursive call until no parent or loop
QUESTIONNAIE_ITEM_ANSWER_VALUE_SECTION = ['code', 'not','display']

def convert_reference_to_firepath(expression, df_questions):
    # find all the reference
    matches = re.findall(pattern = r'"(?P<linkid>[^"]+)"(?:\.(?P<sufix>\w+))?', string = expression)
    
    for match in matches:
        fpath = []
        linkid = match[0]
        sufix = match[1]  
        # find all the parent
        if df_questions is None:
            print("warning: cannot resolve the expression {} because not questions df avaiable".format(expression))
            fpath = [linkid]       
        else:
            fpath = get_fpath(df_questions, linkid, fpath)
        # do the replaces : if prefix and prefix != code replace with answers else repalce with value
        path = ''
        for elm in fpath:
            path= ".repeat(item).where(linkId='{}')".format(elm) +path
        # addin the answer
        path = path + ".answer.first()"
        if sufix == '' or sufix in QUESTIONNAIE_ITEM_ANSWER_VALUE_SECTION:
            path = path + ".value"     
        if sufix != '':
            term_q = '"{0}".{1}'.format(linkid, sufix)
            #term = "${{{0}}}.{1}".format(linkid, sufix)
            replace = "%resource"+path+"."+sufix
        else:
            term_q = '"{0}"'.format(linkid, sufix)
            #term = "${{{0}}}".format(linkid)
            replace = "%resource"+path
        expression = expression.replace(term_q,replace ) 
        #expression = expression.replace(term,replace )


    return inject_config(expression) 

def get_enable_when_expression_ext(expression, df_questions, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-enableWhenExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/fhirpath",
                expression = convert_reference_to_firepath(expression, df_questions)))

def get_calculated_expression_ext(expression, df_questions, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-calculatedExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/fhirpath",
                expression = convert_reference_to_firepath(expression, df_questions)))

def get_initial_expression_ext(expression, df_questions, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/cql-expression",
                expression = convert_reference_to_firepath(expression, df_questions)))

def get_initial_expression_identifier_ext(quesiton_id, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/cql-identifier",
                expression = str(quesiton_id).lower()))
   
def get_questionnaire_library(library):
    if not re.search("$https?\:\/\/", library):
        library = get_fhir_cfg().canonicalBase + "Library/{}".format(clean_name(library))
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/cqf-library",
        valueCanonical  = library)
        
def add_library_extentions(resource, library):
    if resource.extension == None:
        resource.extension = []
    resource.extension.append(get_questionnaire_library(library))