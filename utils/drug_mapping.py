import re
import pandas as pd

from config import LABEL_CSV_PATH

#######################################################################################################
# CALIBRATION DRUG MAP
#######################################################################################################

calibration_map={
    "001001":"DMSO","001002":"DMSO","001023":"DMSO","001024":"DMSO",
    "002001":"DMSO","002002":"DMSO","002023":"DMSO","002024":"DMSO",
    "003001":"ActD_0.3","003002":"ActD_0.3","003023":"ActD_0.3","003024":"ActD_0.3",
    "004001":"BMH-21_2","004002":"BMH-21_2","004023":"BMH-21_2","004024":"BMH-21_2",
    "005001":"CAM_25","005002":"CAM_25","005023":"CAM_25","005024":"CAM_25",
    "006001":"CX-5461_10","006002":"CX-5461_10","006023":"CX-5461_10","006024":"CX-5461_10",
    "007001":"DIN_5","007002":"DIN_5","007023":"DIN_5","007024":"DIN_5",
    "008001":"DOX_5","008002":"DOX_5","008023":"DOX_5","008024":"DOX_5",
    "009001":"DRB_200","009002":"DRB_200","009023":"DRB_200","009024":"DRB_200",
    "010001":"ETO_500","010002":"ETO_500","010023":"ETO_500","010024":"ETO_500",
    "011001":"FLA_1.2","011002":"FLA_1.2","011023":"FLA_1.2","011024":"FLA_1.2",
    "012001":"HES_5","012002":"HES_5","012023":"HES_5","012024":"HES_5",
    "013001":"MEN_40","013002":"MEN_40","013023":"MEN_40","013024":"MEN_40",
    "014001":"MIT_3","014002":"MIT_3","014023":"MIT_3","014024":"MIT_3",
    "015001":"PLU_20","015002":"PLU_20","015023":"PLU_20","015024":"PLU_20",
    "016001":"t-BHP_100","016002":"t-BHP_100","016023":"t-BHP_100","016024":"t-BHP_100"
}

#######################################################################################################
# LOAD AHA DRUG MAP
#######################################################################################################

def load_aha_drug_map():

    df=pd.read_csv(LABEL_CSV_PATH)
    drug_map={}

    for _,row in df.iterrows():

        well=str(int(row["well_index"]))

        for plate in df.columns:

            if plate=="well_index":
                continue

            drug=str(row[plate]).strip()

            if drug!="" and drug!="?" and drug.lower()!="nan":
                drug_map[(plate,well)]=drug

    return drug_map

#######################################################################################################
# PARSE LABEL
#######################################################################################################

def parse_label(label):

    label=str(label)
    parts=label.split("_")

    if len(parts)<3:
        return None,None,None

    experiment=parts[0]
    well=parts[-1]
    plate="_".join(parts[1:-1])

    plate=re.sub(r"_\d+$","",plate)

    try:
        well=str(int(well))
    except Exception:
        pass

    return experiment,plate,well

#######################################################################################################
# GET AHA DRUG NAME
#######################################################################################################

def get_aha_drug_name(label,aha_drug_map):

    experiment,plate,well=parse_label(label)

    if experiment!="AHA":
        return None

    if plate is None or well is None:
        return None

    return aha_drug_map.get((plate,well),None)

#######################################################################################################
# GET CALIBRATION DRUG NAME
#######################################################################################################

def get_calibration_drug_name(label):

    experiment,plate,well=parse_label(label)

    if experiment not in ["AHA","AEB","AEC","ALB"]:
        return None

    label=str(label)
    matches=re.findall(r"(?<!\d)(\d{6})(?!\d)",label)

    if len(matches)>0:

        drug=calibration_map.get(matches[-1],None)

        if drug is not None:
            return drug

    if well is None:
        return None

    return calibration_map.get(str(well).zfill(6),None)

#######################################################################################################
# GET DRUG DISPLAY INFO
#######################################################################################################

def get_drug_display_info(label,aha_drug_map):

    drug=get_calibration_drug_name(label)

    if drug is not None:
        return drug,"green"

    drug=get_aha_drug_name(label,aha_drug_map)

    if drug is not None:
        return drug,"blue"

    return None,None

#######################################################################################################
# GET DRUG NAME
#######################################################################################################

def get_drug_name(label,aha_drug_map):

    drug,color=get_drug_display_info(label,aha_drug_map)

    return drug

#######################################################################################################
# FORMAT LABEL WITH DRUG
#######################################################################################################

def format_label_with_drug(label,aha_drug_map):

    drug,color=get_drug_display_info(label,aha_drug_map)

    if drug is None:
        return label

    return f'{label} <span style="color:{color};">({drug})</span>'