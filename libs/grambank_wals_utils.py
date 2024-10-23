from libs import wals_utils as wu, grambank_utils as gu

def get_palue_name_from_value_code(code):
    if code[:2] == "GB":
        return gu.grambank_vname_by_vid[code]
    else:
        return wu.get_careful_name_of_de_pk(code)