from django.contrib import admin
from django.forms import SelectMultiple

from .models import TimeSheetPlane, ProfileUser, BusyKeysReplacement, persons_audit, Enterprises, SettingTableTemp, \
    enterprise_revision, PositionsReplacement, PositionsReplacementAdmin, PositionsWhitelist, Trained_staff


admin.site.register(TimeSheetPlane)
admin.site.register(ProfileUser)
admin.site.register(BusyKeysReplacement)
admin.site.register(persons_audit)
admin.site.register(Enterprises)
admin.site.register(SettingTableTemp)
admin.site.register(enterprise_revision)
admin.site.register(PositionsReplacement, PositionsReplacementAdmin)
admin.site.register(PositionsWhitelist)
admin.site.register(Trained_staff)

