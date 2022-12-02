from django import template
from TimeSheet.models import TimeSheetFact, BusyKeys

register = template.Library()

@register.filter
def get_fact_easy(value, p_uid):
    print(value)
    print(p_uid)
    obj = TimeSheetFact.objects.filter(p_uid=p_uid).first()
    print(obj)
    if obj == None:
        _fact = """<select name="form-0-busy_key_guid" id="id_form-0-busy_key_guid">
          <option value="">---------</option>
          <option value="5A688F00-74A8-11E8-80F9-3640B58B95BD" selected></option>
        </select>"""
        # return BusyKeys.objects.get(guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')
    else:
        _fact =  obj
    print(_fact)
    return _fact




register.filter('get_fact_easy', get_fact_easy)