import logging
import re
from distutils.util import strtobool

from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from pyfhirsdc.serializers.xkcd import XKCD
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.fhirtypes import Canonical, ExpressionType, QuantityType
from fhirpathpy import compile, evaluate
from pyfhirsdc.config import get_dict_df, get_fhir_cfg
from pyfhirsdc.converters.utils import (clean_name, get_custom_codesystem_url,
                                        get_fpath, get_resource_url,
                                        inject_config)

logger = logging.getLogger("default")

def get_background_color_style_ext(color_str):
    if color_str in list(XKCD):
        hex_str = XKCD[color_str]
    else:
        hex_str=color_str
    
    return get_rendering_style_ext(f"style::background-color: {hex_str};")

def get_rendering_style_ext(style_str):
    return Extension( 
        url = "http://hl7.org/fhir/StructureDefinition/rendering-style",
        valueString= style_str
        )

# default is   vertical
def get_horizontal_ext():
    return Extension( 
        url = "http://hl7.org/fhir/StructureDefinition/questionnaire-choiceOrientation",
        valueCode= "horizontal"
        )

def get_regex_ext(regex):
    return Extension( 
        url = "http://hl7.org/fhir/StructureDefinition/regex",
        valueCode= "regex"
        )

def get_number_only_ext():
 return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
    valueCodeableConcept = CodeableConcept(
            coding = [Coding( 
                system = "http://hl7.org/fhir/questionnaire-item-control",
                code = "number-only",
                display = "Number Only")],
            text ="Number Only")
)

def get_item_media_ext(media_type,media_url , option = False):
    # https://terminology.hl7.org/1.0.0/CodeSystem-v3-mediatypes.html
    if media_type == 'png':
        media_type = 'image/png'
    elif media_type == 'jpg' or media_type == 'jpeg':
        media_type = 'image/jpeg'
        
    #TODO: #36 support, URL, FHIRBinaries, includedB64
    
    urlExt = "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-itemAnswerMedia" if option == True else "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-itemMedia"
    
    return Extension(
        url = urlExt,
        valueAttachment = Attachment(
            contentType = media_type,
            url = media_url
        )
    )
    
def get_popup_ext():
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
        valueCodeableConcept = CodeableConcept(
                coding = [Coding( 
                    system = "http://hl7.org/fhir/questionnaire-item-control",
                    code = "popup",
                    display = "Popup")],
                text ="Popup")   
    )
    
    

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
 
def get_radio_ext():
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
        valueCodeableConcept = CodeableConcept(
                coding = [Coding( 
                    system = "http://hl7.org/fhir/questionnaire-item-control",
                    code = "radio-button",
                    display = "Radio Button")],
                text ="Radio Button")
        )
 
def get_help_ext():
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
        valueCodeableConcept = CodeableConcept(
                coding = [Coding( 
                    system = "http://hl7.org/fhir/questionnaire-item-control",
                    code = "help")
                ]
        )
)
 
def get_instruction_ext():
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-displayCategory",
        valueCodeableConcept = CodeableConcept(
                coding = [Coding( 
                    system = "http://hl7.org/fhir/questionnaire-display-category",
                    code = "instructions")
                ]
        )
    )
    
def get_security_ext():
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-displayCategory",
        valueCodeableConcept = CodeableConcept(
                coding = [Coding( 
                    system = "http://hl7.org/fhir/questionnaire-display-category",
                    code = "security")
                ]
        )
    )     

def get_toggle_ext(in_code, expression, df_question):
    a_code = in_code.split('|')
    if len(a_code) == 1:
        code = in_code
        system = get_custom_codesystem_url()
    else:
        code = a_code[1]
        system = a_code[0]
        
    return Extension(
            url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-answerOptionsToggleExpression",
            extension = [
                Extension( 
                    url = "option" ,
                    valueCoding = Coding(
                        system = system,
                        code = code
                        )
                ),
                Extension(
                    url = "expression",
                    valueExpression = ExpressionType(
                        language = "text/fhirpath",
                        expression = convert_reference_to_fhirpath(expression, df_question)
                    ))            
            ])
 
 
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
    language, expression = get_expression_language(expression)
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/variable",
        valueExpression = ExpressionType(
                name = name,
                language = language ,
                expression = convert_reference_to_fhirpath(expression, df_questions)))


def get_candidate_expression_ext(desc, uri):
    if desc is not None and uri is not None:
        return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-answerExpression",
        #url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-candidateExpression",
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

def get_structure_map_extension(extensions, uri):
    if extensions is None:
        extensions = []
    if  uri is not None:
        sm_ext = Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-targetStructureMap",
        valueCanonical=  Canonical(uri)
        )
        if extensions is None or len(extensions) == 0:
            return [sm_ext]
        else:
            append_unique(extensions, sm_ext, True)
    return extensions
# exp  expression::severity
# message human::requirements
def get_quantity(str_qty):
    arr_qty = str_qty.split("'")
    if len(arr_qty) !=3:
        logger.error(f"quantity {str_qty} not parsable")
        return None 
    value = arr_qty[0].strip()
    code = arr_qty[1].strip()
    system = arr_qty[2].strip() 
    
    return QuantityType(
        value = value,
        system = system if system != '' else 'http://unitsofmeasure.org',
        code = code
        
    )

def get_constraint_exp_ext(id,expr, human,df_questions = None):
    expr_parts = expr.split('::')
    expr = None
    if expr_parts[0] == "MinMax":
        df_q  =df_questions[df_questions.id == id]
        if len(df_q)>0 and df_q.iloc[0]['type'] in ('decimal', 'integer','date', 'dateTime', 'time','quantity'):
            q_type = df_q.iloc[0]['type']
            min_max_exts = [Extension(
                url = "http://hl7.org/fhir/StructureDefinition/minValue",
                valueDecimal = expr_parts[1] if q_type == 'decimal' else None,
                valueInteger = expr_parts[1] if q_type == 'integer' else None,
                valueDate = expr_parts[1] if q_type == 'date' else None,
                valueTime = expr_parts[1] if q_type == 'time' else None,
                valueDateTime = expr_parts[1] if q_type == 'dateTime' else None,
                valueQuantity = get_quantity(expr_parts[1])if q_type == 'quantity' else None,
                
            )]
            if len(expr_parts)>2:
              min_max_exts.append(Extension(
                url = "http://hl7.org/fhir/StructureDefinition/maxValue",
                valueDecimal = expr_parts[2] if q_type == 'decimal' else None,
                valueInteger = expr_parts[2] if q_type == 'integer' else None,
                valueDate = expr_parts[2] if q_type == 'date' else None,
                valueTime = expr_parts[2] if q_type == 'time' else None,
                valueDateTime = expr_parts[2] if q_type == 'dateTime' else None,
                valueQuantity = get_quantity(expr_parts[2])if q_type == 'quantity' else None,
                               ))
            return min_max_exts
        else:
            expr = "answer.first() >= {} and answer.first() <= {}".format(expr_parts[1],expr_parts[2])
            requirements = None
    human_parts = human.split('::')
    if len(human_parts)==2:
        human = human_parts[0]
        severity = human_parts[1]
    elif len(human_parts)==1:
        severity = 'error'
    else:
        logger.error("missing constraint message")    

    if expr is not None:
        if len(expr_parts)==2:
            expr = expr_parts[0]
            requirements = expr_parts[1]
        elif len(expr_parts)==1:
            requirements = None
        else:
            logger.error("missing expresison")        
    
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
                expression = convert_reference_to_fhirpath(expr, df_questions))),
                Extension( 
                    url = "severity",
                    valueCode= severity),
                Extension( 
                    url = "human",
                    valueString= human) 
            ])
    if requirements is not None:
        ext.extension.append(Extension( 
                    url = "requirements",
                    valueString= requirements))
    return [ext]

def append_unique(extensions, new_ext, replace = False):
    nofound = True
    for ext in extensions:
        if replace and ext.url == new_ext.url:
            extensions.remove(ext)
        elif ext == new_ext:
            nofound = False
    if nofound:
        extensions.append(new_ext) 

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
    if unit in ['month','months','year','years']:
        return Extension(
            #        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-unitOption",
            url ="http://hl7.org/fhir/StructureDefinition/questionnaire-unit",
            valueCoding = Coding(
                system = "http://hl7.org/fhirpath/CodeSystem/calendar-units",
                code = unit,

            )
        )
    else:
        return Extension(
            #        url ="http://hl7.org/fhir/StructureDefinition/questionnaire-unitOption",
            url ="http://hl7.org/fhir/StructureDefinition/questionnaire-unit",
            valueCoding = Coding(
                system = "http://unitsofmeasure.org",
                code = unit,

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

FHIRPATH_FUNCTION = ['where', 'last', 'first']

def convert_reference_to_fhirpath(expression, df_questions):
    # find all the reference
    expression = str(expression)
    changes = []
    matches = re.findall(pattern = r'(?P<op> *!?<< *| *!?= *)?"(?P<linkid>[^"]+)"(?:\.(?P<sufix>\w+))?(?P<op2> *!= *(?:true|false))?', string = str(expression))
    
    for match in matches:
        null_or_path = None
        fpath = []
        path = ''
        Iscode = False
        elm = None
        op = match[0]
        linkid = match[1]
        sufix = match[2]
        null_or =   match[3]
        # find all the parent
        if df_questions is None:
            logger.warning("cannot resolve the expression {} because not questions df avaiable".format(expression))
            fpath = [linkid]       
   
        df_valueset = get_dict_df()['valueset']
        value = df_valueset[(df_valueset.valueSet != "condition") & (df_valueset.valueSet != "observation") & ((df_valueset.code == linkid)|(df_valueset.display == linkid))]
        #not in
        if len(value)>0 and "!<<" in op:
            value = value.iloc[0]
            term_q = '.first().value{0}"{1}"'.format(op, linkid)
            replace = ".where(value.code = '{}').empty()".format(value['code'])
        # in
        elif len(value)>0 and "<<" in op:
            value = value.iloc[0]
            term_q = '.first().value{0}"{1}"'.format(op, linkid)
            replace = ".where(value.code = '{}').exists()".format(value['code'])
        # equal or not equal
        elif op != '' and len(value)>0:
            value = value.iloc[0]
            term_q = '{0}"{1}"'.format(op, linkid)
            replace = ".code{}'{}'".format(op,value['code'])
        # reference to a questions
        else:
            question = df_questions[(df_questions['id'] == linkid) | (df_questions['label'] == linkid) ]
            if   len(question)>0:
                fpath = get_fpath(df_questions, linkid, fpath)
                for elm in fpath:
                    path= ".repeat(item).where(linkId='{}')".format(elm) +path
                path += ".answer"
                if  len(null_or)>0:
                    null_or_path = path + ".empty() "
                if sufix not in FHIRPATH_FUNCTION:
                    path +=".first()"
                if sufix == '' or sufix in QUESTIONNAIE_ITEM_ANSWER_VALUE_SECTION:
                    path += ".value"     
                if sufix != '':
                    term_q = '"{0}".{1}'.format(linkid, sufix)
                    #term = "${{{0}}}.{1}".format(linkid, sufix)
                    replace = "%resource"+path+"."+sufix
                else:
                    term_q = '"{0}"'.format(linkid, sufix)
                    #term = "${{{0}}}".format(linkid)
                    replace = "%resource"+path
            elif  len(value)>0:
                Iscode = True
                value = value.iloc[0]
                term_q = '{0}"{1}"'.format(op, linkid)
                replace = "{0}'{1}'".format(op,value['code'])
                
            else:
                logger.error("{} not found in question nor valueset".format(linkid))
                exit()
        # do the replaces : if prefix and prefix != code replace with answers else repalce with value
        if term_q+null_or not in changes:
            changes.append(term_q)
            if null_or_path is not None:
                if "true" in null_or:
                    expression = expression.replace(term_q+null_or,"( %resource" + null_or_path +" or " + replace + "=false )")
                else:
                    expression = expression.replace(term_q+null_or,"( %resource" + null_or_path +" or " + replace + "=true )")
            else: 
                expression = expression.replace(term_q,replace ) 
    # remove the new lines
    expression = expression.replace('\n','')
    # replace the {{}}
    final = inject_config(expression)
    # validate fhirparse grammar
    node = compile([], final)
    if node is not None:
        return final


def get_enable_when_expression_ext(expression, df_questions, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-enableWhenExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/fhirpath",
                expression = convert_reference_to_fhirpath(expression, df_questions)))

CALCUALTED_EXPRESSION_LANGUAGE = {
    
    'fhirpath':'text/fhirpath',
    'fhir-x-query':'application/x-fhir-query'
}

def get_expression_language(expression):
    # find language
    language = "text/fhirpath"
    parts =  expression.split('::')
    if len(parts)>1 and parts[0] in CALCUALTED_EXPRESSION_LANGUAGE:
        language = CALCUALTED_EXPRESSION_LANGUAGE[parts[0]]
        expression = "::".join(parts[1:]) 
    return language, expression

def get_calculated_expression_ext(expression, df_questions, desc = None ):
    language, expression = get_expression_language(expression)
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-calculatedExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = language,
                expression = convert_reference_to_fhirpath(expression, df_questions)))

def get_initial_expression_ext(expression, df_questions, desc = None ):
    language, expression = get_expression_language(expression)
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = language,
                expression = convert_reference_to_fhirpath(expression, df_questions)))



def get_cql_epression(id, desc = None):
    return ExpressionType(
                description = desc,
                language = "text/cql-identifier",
                expression = str(id))

def get_initial_expression_identifier_ext(quesiton_id, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
        valueExpression = get_cql_epression(quesiton_id, desc)
    )
def get_questionnaire_library(library):

    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/cqf-library",
        valueCanonical  = library)
        
def add_library_extensions(resource, library):
    if resource.extension == None:
        resource.extension = []
    resource.extension.append(get_questionnaire_library(library))