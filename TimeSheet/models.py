import sys
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from django.db import connection
from django.contrib import admin
import pandas as pd
from datetime import datetime, date, timedelta, time

from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.forms.models import model_to_dict

from django.utils import dateformat
from .utils import dict_fetchall, named_tuple_fetchall
import calendar

import uuid

import math

from PIL import Image


class Persons(models.Model):
    guid = models.CharField(primary_key=True, unique=True, editable=False, max_length=64)
    first_name = models.CharField(max_length=128)
    middle_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    full_name = models.CharField(max_length=400)
    gender_female = models.IntegerField()
    snils_document = models.CharField(max_length=128)
    tab_number = models.CharField(max_length=128)
    marked = models.IntegerField()
    archived = models.IntegerField()

    def __str__(self):
        return f'{self.full_name} ({self.tab_number})'

    def isdeleted(persons, dts):
        fl = False

        qset = person_statuses.objects.filter(person_guid=persons.guid, work_status_id=27, f_date__month=dts.month)
        if len(qset) > 0:
            fl = True

        return fl

    class Meta:
        db_table = 'persons'
        managed = False
        ordering = ['full_name']

    def get_last_Shedule(self, dts):
        init = PersonShedule.objects.filter(begin_date__lte=dts, person_guid=self).order_by('-begin_date')
        if len(init) == 0:
            return None
        return init[0].shedule_guid

    @staticmethod
    def get_empty_person():
        return Persons.objects.get(guid='00000000-0000-0000-0000-000000000000')


class person_statuses(models.Model):
    person_guid = models.ForeignKey(Persons, primary_key=True, on_delete=models.CASCADE, db_column='person_guid')
    work_status_id = models.IntegerField()
    f_date = models.DateField()
    e_date = models.DateField()

    class Meta:
        db_table = 'person_statuses'
        managed = False
        unique_together = (('person_guid'),)


class Positions(models.Model):
    guid = models.CharField(primary_key=True, unique=True, max_length=64)
    full_name = models.CharField(max_length=400)
    short_name = models.CharField(max_length=64)
    mobile = models.IntegerField()
    istech = models.IntegerField()

    def __str__(self):
        return self.full_name

    @staticmethod
    def get_empty_position():
        return Positions.objects.get(guid='00000000-0000-0000-0000-000000000000')

    class Meta:
        db_table = 'positions'
        managed = False
        ordering = ['full_name']


class PositionsReplacement(models.Model):
    '''
    replacement_type - имеет 3 варинта
    0 - правила замены для основного табеля
    1 - правила совмещения
    2 - правила замены в ревизии
    '''

    REPLACE_TYPE_CHOICES = (
        (0, 'Правила замены'),
        (1, 'Правила совмещения'),
        (2, 'Правила замены ревизии')
    )

    ANOTHER_CHOICES = (
        (0, 'Нет'),
        (1, 'Да'),
    )

    guid = models.CharField(primary_key=True, unique=True, max_length=64, default=str(uuid.uuid4()))
    position_guid_from = models.ForeignKey(Positions, related_name='position_guid_from', on_delete=models.CASCADE,
                                           max_length=64, db_column='position_guid_from', verbose_name='Должность с')
    position_guid_to = models.ForeignKey(Positions, related_name='position_guid_to', on_delete=models.CASCADE,
                                         db_column='position_guid_to', verbose_name='Должность на')

    # position_guid_from = models.CharField(primary_key=True, unique=True, max_length=64, db_column='position_guid_from')
    # position_guid_to = models.CharField(max_length=64, unique=True, db_column='position_guid_to')

    replacement_type = models.IntegerField(db_column='replacement_type', choices=REPLACE_TYPE_CHOICES,
                                           verbose_name='Тип праивла')
    another_enterprise = models.IntegerField(db_column='another_enterprise', choices=ANOTHER_CHOICES,
                                             verbose_name='Другое подразделение')
    teached_person_only = models.IntegerField(db_column='teached_person_only', choices=ANOTHER_CHOICES,
                                              verbose_name='Только обученные')
    otiz_only = models.IntegerField(db_column='otiz_only', choices=ANOTHER_CHOICES, verbose_name='Только для ОТИЗ')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        obj_empty = PositionsReplacement.objects.filter(position_guid_from=self.position_guid_from,
                                                        position_guid_to=self.position_guid_to,
                                                        replacement_type=self.replacement_type).first()
        if obj_empty is None:
            self.guid = str(uuid.uuid4())
        super(PositionsReplacement, self).save()

    @staticmethod
    def get_replace_positions(pos, type, another_enterprise=-1, with_otiz=0, teached_person_only=0):
        replace_pos = []
        choice_pos = Positions.objects.get(guid=pos) if isinstance(pos, str) else pos
        init = PositionsReplacement.objects.filter(position_guid_from=choice_pos, replacement_type=type)

        if another_enterprise >= 0:
            init = init.filter(another_enterprise=another_enterprise)

        if with_otiz == 0:
            init = init.filter(otiz_only=0)

        if teached_person_only == 0:
            init = init.filter(teached_person_only=0)

        for i in init:
            replace_pos.append(i.position_guid_to)

        return replace_pos

    @staticmethod
    def get_replace_positions_to(pos, type, another_enterprise=-1, with_otiz=0, teached_person_only=0):
        replace_pos = []
        choice_pos = Positions.objects.get(guid=pos) if isinstance(pos, str) else pos
        init = PositionsReplacement.objects.filter(position_guid_to=choice_pos, replacement_type=type)

        if another_enterprise >= 0:
            init = init.filter(another_enterprise=another_enterprise)

        if with_otiz == 0:
            init = init.filter(otiz_only=0)

        if teached_person_only == 0:
            init = init.filter(teached_person_only=0)

        for i in init:
            replace_pos.append(i.position_guid_from)

        return replace_pos

    # def __str__(self):
    #     # return f'{Positions.objects.get(guid=self.position_guid_from)} ({Positions.objects.get(guid=self.position_guid_to)}) тип {self.replacement_type}'
    #     return f'{self.position_guid_from} ({self.position_guid_to}) тип {self.REPLACE_TYPE_CHOICES[self.replacement_type][1]}'

    class Meta:
        db_table = 'positions_replacement'
        managed = False
        unique_together = ('position_guid_from', 'position_guid_to', 'replacement_type')
        verbose_name = 'Правило замены должности'
        verbose_name_plural = 'Правила замены должностей'
        ordering = ['position_guid_from', ]


class PositionsReplacementAdmin(admin.ModelAdmin):
    list_display = (
        'position_guid_from', 'position_guid_to', 'replacement_type', 'another_enterprise', 'teached_person_only',
        'otiz_only')
    search_fields = ['position_guid_from__full_name', 'position_guid_to__full_name', 'teached_person_only', ]


class Shedules(models.Model):
    guid = models.CharField(primary_key=True, unique=True, max_length=64)
    full_name = models.CharField(max_length=400)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'shedules'
        managed = False

    @staticmethod
    def get_empty_shedule():
        return Shedules.objects.get(guid='00000000-0000-0000-0000-000000000000')

    def sheduler_round_the_clock(self, date):
        list_hours = SheduleHours.objects.filter(dts=date, shedule_guid=self).exclude(
            shedule_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')

        if len(list_hours) > 2:
            return True
        else:
            return False


class PersonShedule(models.Model):
    # guid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='guid')
    person_guid = models.ForeignKey(Persons, primary_key=True, on_delete=models.CASCADE, db_column='person_guid')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')
    begin_date = models.DateTimeField(db_column='begin_date')

    class Meta:
        db_table = 'person_shedule'
        managed = False
        unique_together = ('person_guid', 'shedule_guid', 'begin_date')


class BusyKeys(models.Model):
    guid = models.CharField(primary_key=True, unique=True, max_length=64)
    short_name = models.CharField(max_length=64)
    full_name = models.CharField(max_length=400)

    def __str__(self):
        return self.short_name

    class Meta:
        db_table = 'busy_keys'
        managed = False


class SheduleHours(models.Model):
    dts = models.DateField(db_column='dts')
    busy_key_guid = models.ForeignKey(BusyKeys, primary_key=True, unique=True, on_delete=models.CASCADE,
                                      db_column='busy_key_guid')
    hours_full = models.SmallIntegerField(db_column='hours_full')
    hours_lite = models.SmallIntegerField(db_column='hours_lite')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')

    class Meta:
        db_table = 'shedule_hours'
        managed = False

    @staticmethod
    def get_list_shedules_work(dts):
        list_shedule = [i.shedule_guid for i in SheduleHours.objects.filter(dts=dts,
                                                                            busy_key_guid__guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')]
        return list_shedule


class BusyKeysReplacement(models.Model):
    guid = models.CharField(primary_key=True, max_length=64, unique=True, db_column='guid')
    f_key = models.ForeignKey(BusyKeys, on_delete=models.CASCADE, related_name='f_key', db_column='f_key')
    t_key = models.ForeignKey(BusyKeys, on_delete=models.CASCADE, related_name='t_key', db_column='t_key')

    @staticmethod
    def get_replace_busy_key(busy_key, f_select):

        replace_key = []

        init = BusyKeysReplacement.objects.filter(f_key=busy_key)

        replace_key.append({'guid': "", 'key': "------", 'select': 1})
        if len(init) > 0:
            for k in init:
                _select = 0
                if f_select == k.t_key: _select = 1
                replace_key.append({'guid': k.t_key.guid, 'key': k.t_key.short_name, 'select': _select})
        else:
            _select = 0
            if f_select == busy_key: _select = 1
            replace_key.append({'guid': busy_key.guid, 'key': busy_key.short_name, 'select': _select})
        return replace_key

    @staticmethod
    def get_busy_key_replace(busy_key):

        qset = BusyKeysReplacement.objects.filter(f_key=busy_key)
        dict_busy_key = {}
        if len(qset) == 0:
            dict_busy_key[1] = "нет записей"
        else:
            i = 0
            for j in qset:
                dict_busy_key[i] = j.t_key
                i = +1

        return dict_busy_key

    class Meta:
        db_table = 'busy_keys_replacement'
        managed = False
        unique_together = (('f_key', 't_key'),)


class Enterprises(models.Model):
    guid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='guid')
    name = models.CharField(max_length=400, db_column='name')
    enterprise_code = models.IntegerField(db_column='enterprise_code')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'enterprises'
        managed = False
        ordering = ['enterprise_code']

    def get_list_shops(self):
        return Enterprises.objects.filter(enterprise_code__gte=3, enterprise_code__lte=999)

    def get_status_open_or_close(enterprise, date_f):
        with connection.cursor() as cursor:
            text_req = '''SELECT
                                pdb_guid,  
                                min(event_date) as min_date,
                                max(event_date) as max_date
                            FROM [Personnel].[dbo].[enterprises_history]
                            where pdb_guid = ''' + "'" + enterprise + "'" + '''
                            group by pdb_guid'''
            cursor.execute(text_req)
            setobj = cursor.fetchall()
        if len(setobj) == 0:
            if Enterprises.objects.get(guid=enterprise).enterprise_code == 2:
                return True
            else:
                return False

        min_date = setobj[0][1]
        max_date = setobj[0][2]
        delta_date = date_f - max_date
        if date_f <= min_date:
            return True
        elif min_date != max_date and (delta_date.days <= 7 or (delta_date.days <= 0 and delta_date.days > -7)):
            return True

        return False

    def time_close_table(self):
        now_date = datetime.today()

        time_close = SettingTableTemp.get_time_close_table(self)
        if time_close <= now_date.hour and now_date.minute > 0:
            return True

        return False

    def get_list_open_day(self, current_period, profile):
        list_day = []
        now_date = datetime.today()

        if self.time_close_table() and profile.entreprise is not None:
            return list_day

        if SettingTableTemp.get_sign_of_closing_timesheet_on_date(self, current_period):
            return list_day

        if profile.otiz:
            interval_month = calendar.monthrange(current_period.year - 1, 12) if current_period.month == 1 else \
                calendar.monthrange(current_period.year, current_period.month)
            last_day_month = interval_month[1]
            first_day_month = 1
            list_day = [i for i in range(first_day_month, last_day_month + 1)]
            return list_day

        open_day = SettingTableTemp.get_open_day_table(self)
        if current_period.month == now_date.month:
            if open_day == 1:
                list_day.append(now_date.day)
            else:
                delta = now_date.day - open_day
                first_day = 1 if delta <= 0 else delta + 1

                list_day = [i for i in range(first_day, now_date.day + 1)]
        else:
            delta = now_date.day - open_day
            if delta < 0:
                last_day_month = calendar.monthrange(now_date.year - 1, 12)[1] if now_date.month == 1 else \
                    calendar.monthrange(now_date.year, now_date.month - 1)[1]
                list_day = [i for i in range(last_day_month + delta + 1, last_day_month + 1)]

        return list_day


class StaffHistory(models.Model):
    dts_f = models.DateTimeField(db_column='dts_f')
    dts_t = models.DateTimeField(db_column='dts_t')

    person_guid = models.ForeignKey(Persons, primary_key=True, on_delete=models.CASCADE, db_column='person_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    rate = models.FloatField(db_column='rate')
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')

    # def get_all(models):
    #    with connection.cursor() as cursor:
    #        cursor.execute("SELECT guid, guid_type, dts, person_guid, position_guid, rate, enterprise_guid FROM staff_history")
    #        return cursor.fetchall()

    class Meta:
        db_table = 'staff_history'
        managed = False

    @staticmethod
    def get_last_position(dts, person):
        init = StaffHistory.objects.filter(dts_f__lte=dts, person_guid=person).order_by('-dts_f')
        if len(init) == 0:
            return None
        return init[0].position_guid


class StaffVacancy(models.Model):
    guid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='guid')
    begin_date = models.DateField(db_column='begin_date')
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')
    amount = models.FloatField(db_column='amount')

    class Meta:
        db_table = 'staff_vacancy'
        managed = False

    @staticmethod
    def get_active_state(ent, dts):
        active_state_ent = {}
        dts_end = StaffVacancy.objects.filter(enterprise_guid=ent, begin_date__lte=dts).order_by('-begin_date').first()
        if dts_end is not None:
            state_ent = StaffVacancy.objects.filter(enterprise_guid=ent, begin_date=dts_end.begin_date)
            sh_en = [i.shedule_guid for i in state_ent]
            sh_en_active = SheduleHours.objects.filter(shedule_guid__in=sh_en, dts=dts,
                                                       busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')

            for i in state_ent:
                list_sh_en_active = [s.shedule_guid for s in sh_en_active]
                if i.shedule_guid in list_sh_en_active:
                    if active_state_ent.get(i.position_guid) is None:
                        active_state_ent[i.position_guid] = {i.shedule_guid: i.amount}
                    else:
                        if active_state_ent[i.position_guid].get(i.shedule_guid) is None:
                            active_state_ent[i.position_guid][i.shedule_guid] = i.amount
                        else:
                            active_state_ent[i.position_guid][i.shedule_guid] += i.amount

        return active_state_ent

    @staticmethod
    def check_over_state(ent, dts):
        bk_work = BusyKeys.objects.get(guid='5A688F01-74A8-11E8-80F9-3640B58B95BD')
        # bk_cowork = BusyKeys.objects.get('738B3875-17E4-11E9-80D0-E41F13C123D6')
        state_active = StaffVacancy.get_active_state(ent, dts)
        tm_fact = TimeSheetFact.objects.filter(p_uid__dts=dts, p_uid__enterprise_guid=ent, busy_key_fact=bk_work)
        tm_cowork = persons_coworks.objects.filter(enterprise_guid=ent, dts=dts)

        for i in tm_fact:
            if state_active.get(i.p_uid.position_guid) is not None:
                if state_active[i.p_uid.position_guid].get(i.p_uid.shedule_guid) is not None:
                    state_active[i.p_uid.position_guid][i.p_uid.shedule_guid] -= 1

        for i in tm_cowork:
            if state_active.get(i.position_guid) is not None:
                if state_active[i.position_guid].get(i.shedule_guid) is not None:
                    state_active[i.position_guid][i.shedule_guid] -= 1

        return state_active


class TimeSheetPlane(models.Model):
    p_uid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='uid')
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')
    person_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='person_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')

    dts = models.DateField()
    busy_key_guid = models.ForeignKey(BusyKeys, on_delete=models.CASCADE, db_column='busy_key_guid', verbose_name='Код')

    hours_all = models.FloatField(verbose_name='Часы')
    month = models.IntegerField(db_column='m')
    year = models.IntegerField(db_column='y')

    istech = models.IntegerField(db_column='istech')
    suspicious = models.IntegerField(db_column='suspicious')
    record_type = models.IntegerField(db_column='record_type')

    # def __str__(self):
    # date = self.dts.strftime('%B %Y')
    # return f'Табель "{self.enterprise_guid}" за {date}'
    # return f'Табель "{self.enterprise_guid}"'

    class Meta:
        db_table = 'shift_data_p'
        managed = False
        unique_together = (('p_uid', 'enterprise_guid', 'person_guid', 'dts', 'busy_key_guid'),)
        ordering = ['person_guid', 'dts']

    # def get_absolute_url(self):
    #     return reverse('sheet', kwargs={'guid': self.enterprise_guid, 'month': self.month, 'year': self.year})

    @staticmethod
    def get_table_list(request, ent=None):

        if ent is None:
            set_filter = setting_filter.objects.filter(user_id=request.user.id).first()
            if set_filter is not None:
                empty_guid = '00000000-0000-0000-0000-000000000000'
                if set_filter.persons != empty_guid and set_filter.enterprise != empty_guid:
                    return TimeSheetPlane.objects.values('enterprise_guid', 'enterprise_guid__name', 'month',
                                                         'year').filter(
                        person_guid=set_filter.persons, enterprise_guid=set_filter.enterprise).annotate(
                        total=Count('enterprise_guid')).order_by('-year', '-month', 'enterprise_guid__enterprise_code')
                elif set_filter.persons != empty_guid:
                    return TimeSheetPlane.objects.values('enterprise_guid', 'enterprise_guid__name', 'month',
                                                         'year').filter(
                        person_guid=set_filter.persons).annotate(total=Count('enterprise_guid')).order_by('-year',
                                                                                                          '-month',
                                                                                                          'enterprise_guid__enterprise_code')
                elif set_filter.enterprise != empty_guid:
                    return TimeSheetPlane.objects.values('enterprise_guid', 'enterprise_guid__name', 'month',
                                                         'year').filter(
                        enterprise_guid=set_filter.enterprise).annotate(total=Count('enterprise_guid')).order_by(
                        '-year',
                        '-month',
                        'enterprise_guid__enterprise_code')
            else:
                return TimeSheetPlane.objects.values('enterprise_guid', 'enterprise_guid__name', 'month',
                                                     'year').annotate(
                    total=Count('enterprise_guid')).order_by('-year', '-month', 'enterprise_guid__enterprise_code')
        else:
            return TimeSheetPlane.objects.values('enterprise_guid', 'enterprise_guid__name', 'month', 'year').filter(
                enterprise_guid=ent).annotate(total=Count('enterprise_guid')).order_by('-year',
                                                                                       '-month',
                                                                                       'enterprise_guid__enterprise_code')

    @staticmethod
    def get_all_list_table(request):

        # setobj = TimeSheetPlane.objects.values_list('enterprise_guid', 'month', 'year').distinct()

        set_filter = setting_filter.objects.filter(user_id=request.user.id).first()

        str_f = ''
        if set_filter != None:
            str_f = "Where "
            op = ""
            try:
                if set_filter.persons != '00000000-0000-0000-0000-000000000000':
                    str_f = str_f + " person_guid = '" + set_filter.persons + "'"
                    op = ' and '
            except:
                pass

            try:
                if set_filter.enterprise != '00000000-0000-0000-0000-000000000000':
                    str_f = str_f + op + " enterprise_guid = '" + set_filter.enterprise + "'"
                    op = ' and '
            except:
                pass

            try:
                if set_filter.dts != None:
                    str_f = str_f + op + " dts = '" + set_filter.dts + "'"
            except:
                pass

        with connection.cursor() as cursor:
            cursor.execute(
                "select [enterprise_guid], p.name,[m],[y] from [shift_data_p] as h left join [enterprises] as p on h.enterprise_guid = p.guid " + str_f + " group by [enterprise_guid], p.name,[m],[y]")
            setobj = cursor.fetchall()
            return setobj

    def get_list_table_enterprise(self, enterprise):
        with connection.cursor() as cursor:
            cursor.execute(
                "select [enterprise_guid], p.name,[m],[y] from [shift_data_p] as h left join [enterprises] as p on h.enterprise_guid = p.guid Where [enterprise_guid]='" + enterprise.guid + "' group by [enterprise_guid], p.name,[m],[y]")
            setobj = cursor.fetchall()
            return setobj

    @staticmethod
    def max_append_vacancy(setobj, list_pos, enterprise, date_f):
        fl = False
        for i in setobj:
            if i[2] in list_pos:
                fl = True
                break
        if not fl:
            obj_first = StaffVacancy.objects.filter(enterprise_guid=enterprise,
                                                    position_guid__guid__in=list_pos,
                                                    begin_date__lte=date_f).order_by("-begin_date").first()
            # obj_first = TimeSheetPlane.objects.filter(enterprise_guid=enterprise,
            #                                           position_guid__guid__in=list_pos,
            #                                           month=date_f.month, year=date_f.year,
            #                                           hours_all__gte=0).order_by('-dts').first()
            if obj_first is not None:
                setobj.append((1, enterprise, obj_first.position_guid.guid, obj_first.shedule_guid.guid, 0, 0))
        return setobj

    @staticmethod
    def get_vacancy(enterprise, date_f, user=None):

        role_max_vacancy = False
        if user is not None and user.profileuser.max_vacancy:
            role_max_vacancy = True

        if Enterprises.get_status_open_or_close(enterprise, date_f) or role_max_vacancy:
            with connection.cursor() as cursor:
                text_req = TimeSheetPlane.get_text_dop_vacancy(enterprise, date_f.strftime("%Y-%m-%d"))
                cursor.execute(text_req)
                setobj = cursor.fetchall()

                if role_max_vacancy:  # Добавлю УМа)
                    list_pos = ('28643AE2-FADD-11E0-B937-74EA3A956901', 'AA933F2D-AA16-11EA-80D8-4C5262022228')
                    setobj = TimeSheetPlane.max_append_vacancy(setobj, list_pos, enterprise, date_f)

                    list_pos = ('CD9EE5FF-AA16-11EA-80D8-4C5262022228', '28643AE3-FADD-11E0-B937-74EA3A956901')
                    setobj = TimeSheetPlane.max_append_vacancy(setobj, list_pos, enterprise, date_f)

                return setobj
        else:
            with connection.cursor() as cursor:
                cursor.execute("select * from [dbo].[get_staff_vacancy] ('" + enterprise + "', '" + date_f.strftime(
                    "%Y-%m-%d") + "')")
                setobj = cursor.fetchall()
                return setobj

    @staticmethod
    def get_text_dop_vacancy(ent_guid, dts_format):
        return '''select
                        v.amount,
                        v.enterprise_guid,
                        v.position_guid,
                        v.shedule_guid,
                        v.amount,
                        max(h.hours_full) as hours_full
                    from [dbo].[get_staff_laststate] (''' + "'" + ent_guid + "'" + ''', ''' + "'" + dts_format + "'" + ''') as v
                    left join shedule_hours as h with (nolock) on v.shedule_guid = h.shedule_guid and h.dts = ''' + "'" + dts_format + "'" + '''
                    left join busy_keys as b with (nolock) on h.busy_key_guid = b.guid
                    left join positions as pp on v.position_guid = pp.guid
                    left join shedules as ss on v.shedule_guid = ss.guid
                    where 
                        v.amount > 0
                        and v.active > 0
                        and h.busy_key_guid = '5A688F00-74A8-11E8-80F9-3640B58B95BD'
                        and pp.istech = 0
                    group by
                        v.enterprise_guid,
                        v.position_guid,
                        v.shedule_guid,
                        v.amount'''

    @staticmethod
    def transposed_TimeSheetplan(tplane, init_fact, dts=None):

        empty_busy = BusyKeys.objects.get(guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')

        # initial2 = {}
        # for t in init_fact:
        #     initial2[t.p_uid.p_uid] = {"busy_key_fact": t.busy_key_fact, "hours_fact": t.amount}
        initial2 = {i.p_uid.p_uid: {"busy_key_fact": i.busy_key_fact, "hours_fact": i.amount} for i in init_fact}

        initial = []
        transposed = {}

        for t in tplane:
            transposed.setdefault(t.person_guid, {}).update(
                {t.dts: [t.busy_key_guid, t.hours_all, t.p_uid]})

        i_temp = []
        for tperson in tplane:

            if tperson.person_guid not in i_temp:

                b_color = '#000000'
                if Persons.isdeleted(tperson.person_guid, tperson.dts):
                    b_color = '#FF3B55'
                elif tperson.record_type == 2 or tperson.record_type == 3:
                    b_color = '#049DFF'

                i_temp.append(tperson.person_guid)
                initial_detail = {"person": tperson.person_guid,
                                  "position": StaffHistory.get_last_position(datetime.today() if dts is None else dts,
                                                                             tperson.person_guid),
                                  "shedule": tperson.person_guid.get_last_Shedule(
                                      datetime.today() if dts is None else dts), 'record_type': tperson.record_type,
                                  'istech': tperson.istech, 'b_color': b_color, "date": [], "Outcome": '',
                                  "Outcome_f": ''}

                # for i_dts in sorted(transposed[tperson.person_guid])
                for i_dts in TimeSheetPlane.get_list_date(tplane):
                    get_date = i_dts.get('date')

                    get_date_data = transposed[tperson.person_guid].get(get_date)

                    if get_date_data is not None:

                        f_sheet = initial2.get(transposed[tperson.person_guid][get_date][2])
                        f_busy_key = empty_busy
                        f_amount = 0
                        if f_sheet is not None:
                            f_busy_key = f_sheet['busy_key_fact']
                            f_amount = f_sheet['hours_fact']

                        initial_detail["date"].append({"busy_key": transposed[tperson.person_guid][get_date][0]
                                                          , "hours": transposed[tperson.person_guid][get_date][1]
                                                          , "day_week": get_date.weekday()
                                                          , "busy_key_fact": f_busy_key
                                                          , "hours_fact": f_amount
                                                          , "day": get_date})
                    else:
                        initial_detail["date"].append({"busy_key": empty_busy
                                                          , "hours": 0
                                                          , "day_week": get_date.weekday()
                                                          , "busy_key_fact": empty_busy
                                                          , "hours_fact": 0
                                                          , "day": get_date})

                dict_busykey = []
                dict_busykey_f = []
                for i in initial_detail["date"]:
                    dict_busykey.append(i.get("busy_key"))
                    dict_busykey_f.append(i.get("busy_key_fact"))

                obj_BusyKey = BusyKeys.objects.all()
                for busy_f in obj_BusyKey:
                    ct = dict_busykey.count(busy_f)
                    if ct > 0:
                        initial_detail["Outcome"] = initial_detail["Outcome"] + str(busy_f) + ' ' + '(' + str(
                            ct) + 'дн); '
                    ct_f = dict_busykey_f.count(busy_f)
                    if ct > 0:
                        initial_detail["Outcome_f"] = initial_detail["Outcome_f"] + str(busy_f) + ' ' + '(' + str(
                            ct_f) + 'дн); '

                initial.append(initial_detail)
        return initial

    @staticmethod
    def transposed_table_fast(tplane, init_fact, dts=None):

        empty_busy = BusyKeys.objects.get(guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')
        range_dts = datetime.today() if dts == None else dts

        last_date_month = persons_coworks.last_day_of_month(range_dts)
        list_day_month = list(range(1, last_date_month.day + 1))
        last_date_month = list(filter(lambda x: x.month == range_dts.month,
                                      list(calendar.Calendar().itermonthdates(range_dts.year, range_dts.month))))

        init_sh_night = list(filter(lambda x: x['total'] > 1, list(
            SheduleHours.objects.values('dts', 'shedule_guid').filter(dts__in=last_date_month).exclude(
                busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD').annotate(total=Count('busy_key_guid')))))

        initial = list(map(lambda i: {'p_uid': i.p_uid.p_uid, "busy_key_fact": i.busy_key_fact, "hours_fact": i.amount},
                           init_fact))

        # print('------1-------')
        # print(datetime.now())
        # transposed = list({'person': i,
        #                    'person_full_name': i.full_name,
        #                    'date': sorted(list(
        #                         {'record_type': t.record_type,
        #                          'busy_key': t.busy_key_guid,
        #                          'hours': t.hours_all,
        #                          'day': t.dts,
        #                          'sh_night': True if list(filter(lambda x: x['dts'] == t.dts and x['shedule_guid'] == t.shedule_guid.guid, init_sh_night)) else False,
        #                          'day_dts': t.dts.day,
        #                          'day_week': t.dts.weekday(),
        #                          'busy_key_fact': list(filter(lambda x: x['p_uid'] == t.p_uid, initial))[0]['busy_key_fact'] if len(list(filter(lambda x: x['p_uid'] == t.p_uid, initial))) > 0 else empty_busy,
        #                          'hours_fact': list(filter(lambda x: x['p_uid'] == t.p_uid, initial))[0]['hours_fact'] if len(list(filter(lambda x: x['p_uid'] == t.p_uid, initial))) > 0 else empty_busy,} for t in
        #                         list(filter(lambda x: x.person_guid == i, list(tplane)))), key=lambda x: x['day'])} for i in
        #                                        set(map(lambda x: x.person_guid, list(tplane))))запустил

        transposed = list(map(lambda i: {'person': i,
                                         'person_full_name': i.full_name,
                                         'date': sorted(list(map(lambda t:
                                                                 {'record_type': t.record_type,
                                                                  'busy_key': t.busy_key_guid,
                                                                  'hours': t.hours_all,
                                                                  'day': t.dts,
                                                                  'sh_night': True if list(filter(
                                                                      lambda x: x['dts'] == t.dts and x[
                                                                          'shedule_guid'] == t.shedule_guid.guid,
                                                                      init_sh_night)) else False,
                                                                  'day_dts': t.dts.day,
                                                                  'day_week': t.dts.weekday(),
                                                                  'busy_key_fact': list(
                                                                      filter(lambda x: x['p_uid'] == t.p_uid, initial))[
                                                                      0]['busy_key_fact'] if len(list(
                                                                      filter(lambda x: x['p_uid'] == t.p_uid,
                                                                             initial))) > 0 else empty_busy,
                                                                  'hours_fact': list(
                                                                      filter(lambda x: x['p_uid'] == t.p_uid, initial))[
                                                                      0]['hours_fact'] if len(list(
                                                                      filter(lambda x: x['p_uid'] == t.p_uid,
                                                                             initial))) > 0 else empty_busy, }, list(
                                             filter(lambda x: x.person_guid == i, list(tplane))))),
                                                        key=lambda x: x['day'])},
                              set(map(lambda x: x.person_guid, list(tplane)))))

        # print(datetime.now())
        # print('------1-------')
        #
        # print('------2-------')
        # print(datetime.now())
        for t_row in transposed:

            s_record_type = t_row['date'][0]['record_type']
            b_color = '#000000'
            if Persons.isdeleted(t_row['person'], range_dts):
                b_color = '#FF3B55'
            elif s_record_type == 2 or s_record_type == 3:
                b_color = '#049DFF'

            t_row["position"] = StaffHistory.get_last_position(range_dts, t_row['person'])
            t_row["shedule"] = t_row['person'].get_last_Shedule(range_dts)
            t_row['record_type'] = s_record_type
            t_row['istech'] = t_row["position"].istech if t_row["position"] is not None else 0
            t_row['b_color'] = b_color
            t_row["Outcome"] = ', '.join(map(str, list(
                {i.short_name: len(list(filter(lambda x: x['busy_key'] == i, t_row['date'])))} for i in
                set(map(lambda x: x['busy_key'], t_row['date'])) if i != empty_busy)))
            t_row["Outcome_f"] = ', '.join(map(str, list(
                {i.short_name: len(list(filter(lambda x: x['busy_key_fact'] == i, t_row['date'])))} for i in
                set(map(lambda x: x['busy_key_fact'], t_row['date'])) if i != empty_busy)))

            for t in list(filter(lambda x: x not in set(map(lambda x: x['day_dts'], t_row['date'])), list_day_month)):
                day_empty = datetime(range_dts.year, range_dts.month, t)
                t_row['date'].insert(t - 1, {
                    'record_type': 0,
                    'busy_key': empty_busy,
                    'hours': 0,
                    'day': day_empty,
                    'day_dts': t,
                    'day_week': day_empty.weekday(),
                    'busy_key_fact': empty_busy,
                    'hours_fact': 0
                })

        # print(datetime.now())
        # print('------2-------')

        # t_row['date'] = sorted(t_row['date'], key=lambda x: x['day'])

        return sorted(transposed, key=lambda x: x['person_full_name'])

    @staticmethod
    def transposed_TimeSheetplan_full(tplane):

        initial = []
        transposed = {}

        for t in tplane:
            transposed.setdefault(t.person_guid, {}).update(
                {t.dts: [t.busy_key_guid, t.hours_all]})

        i_temp = ''
        for tperson in tplane:

            if tperson.person_guid != i_temp:
                i_temp = tperson.person_guid
                initial_detail = {"person": tperson.person_guid,
                                  "position": tperson.position_guid,
                                  "shedule": tperson.shedule_guid}

                for i_dts in sorted(transposed[tperson.person_guid]):
                    busy_key_pass = "busy_key" + str(i_dts.day)
                    hours_all_pass = "hours_all" + str(i_dts.day)

                    initial_detail[busy_key_pass] = transposed[tperson.person_guid][i_dts][0]
                    initial_detail[hours_all_pass] = transposed[tperson.person_guid][i_dts][1]

                    busy_key_pass_f = "busy_key_f" + str(i_dts.day)
                    hours_all_pass_f = "hours_all_f" + str(i_dts.day)

                    initial_detail[busy_key_pass_f] = []
                    initial_detail[hours_all_pass_f] = []

                initial.append(initial_detail)

        return initial

    @staticmethod
    def get_list_date_day(dts):
        range_dts = datetime.today() if dts == None else dts
        days_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        date_month = list(map(lambda i: {'date': i, 'day_week': days_week[i.weekday()]}, list(
            filter(lambda x: x.month == range_dts.month,
                   list(calendar.Calendar().itermonthdates(range_dts.year, range_dts.month))))))

        return date_month

    @staticmethod
    def get_list_date(data_sheet):
        list_date = set()
        days_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for date in data_sheet:
            list_date.add(date.dts)

        list_date_temp = sorted(list_date)

        list_date = []
        for date in list_date_temp:
            list_date.append({'date': date, 'day_week': days_week[date.weekday()]})

        return list_date


class TimeSheetFact(models.Model):
    uid = models.CharField(primary_key=True, unique=True, max_length=64)
    p_uid = models.ForeignKey(TimeSheetPlane, related_name='time_sheet_fact', on_delete=models.CASCADE,
                              db_column='p_uid')
    busy_key_fact = models.ForeignKey(BusyKeys, on_delete=models.CASCADE, db_column='busy_key_guid')
    amount = models.FloatField()
    record_fixed = models.IntegerField()

    def is_model_find(f_uid):
        return TimeSheetFact.objects.get(p_uid=f_uid)

    def save(self, *args, **kwargs):
        super(TimeSheetFact, self).save(*args, **kwargs)

    def save_history(self, user, f_uid):
        with connection.cursor() as cursor:
            cursor.execute("exec write_shift_f_history '" + user + "', '" + f_uid + "'")

    def get_fact_detail(initPlan, initFact):

        dict = {}

        initial2 = {}
        for t in initFact:
            initial2[t.p_uid.p_uid] = {"busy_key_fact": t.busy_key_fact, "hours_fact": t.amount}

        for detail in initPlan:
            f_sheet = initial2.get(detail.p_uid)
            f_select = None
            f_amount = 0
            if f_sheet != None:
                f_select = f_sheet['busy_key_fact']
                f_amount = f_sheet['hours_fact']

            dict[detail.p_uid] = [BusyKeysReplacement.get_replace_busy_key(detail.busy_key_guid, f_select), f_amount]

        return dict

    def __str__(self):
        return f'{self.p_uid.dts.strftime("%d-%m-%Y")} | {self.p_uid.person_guid} | {self.busy_key_fact}'

    class Meta:
        db_table = 'shift_data_f'
        managed = False
        unique_together = ('p_uid',)


class persons_coworks(models.Model):
    guid = models.CharField(primary_key=True, max_length=64, db_column='guid', default=str(uuid.uuid4()))
    dts = models.DateField(db_column='dts')
    coworker_guid = models.ForeignKey(Persons, related_name='coworker_guid', on_delete=models.CASCADE,
                                      db_column='coworker_guid')
    foworker_guid = models.ForeignKey(Persons, related_name='foworker_guid', on_delete=models.CASCADE,
                                      db_column='foworker_guid')
    coworker_enterprise_guid = models.ForeignKey(Enterprises, related_name='coworker_enterprise_guid',
                                                 on_delete=models.CASCADE, db_column='coworker_enterprise_guid')
    enterprise_guid = models.ForeignKey(Enterprises, related_name='enterprise_guid', on_delete=models.CASCADE,
                                        db_column='enterprise_guid')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    count_hours = models.FloatField(db_column='count_hours')
    cowork_state = models.IntegerField(db_column='cowork_state')
    cowork_local = models.IntegerField(db_column='cowork_local')
    record_fixed = models.IntegerField(db_column='record_fixed')
    note = models.CharField(max_length=256, db_column='note')
    is_deleted = models.IntegerField(db_column='is_deleted', default=0)
    service_note = models.IntegerField(db_column='service_note', default=0)

    def last_day_of_month(any_day):
        if any_day.month == 12:
            return date(any_day.year + 1, 1, 1) - timedelta(days=1)
        return date(any_day.year, any_day.month + 1, 1) - timedelta(days=1)

    def get_context(dts, enterprise):
        begin_date = dts.replace(day=1)
        end_date = persons_coworks.last_day_of_month(dts)

        return persons_coworks.objects.filter(dts__range=(begin_date, end_date), enterprise_guid=enterprise).order_by(
            'dts')

    def get_context_day(dts, enterprise):
        return persons_coworks.objects.filter(dts=dts, enterprise_guid=enterprise)

    # def save(self, *args, **kwargs):
    #     super(persons_coworks, self).save(*args, **kwargs)

    class Meta:
        db_table = 'persons_coworks'
        managed = False
        # unique_together = ('dts', 'enterprise_guid', 'coworker_guid', 'foworker_guid', 'coworker_enterprise_guid')


class persons_coworks_history(models.Model):
    TYPE_CHOICES = (
        (0, 'изменение'),
        (1, 'удаление'),
    )

    guid = models.CharField(primary_key=True, max_length=64, db_column='guid', default=str(uuid.uuid4()))
    dts = models.DateField(db_column='dts')
    record_date = models.DateTimeField(db_column='record_date')
    cowork_guid = models.CharField(max_length=64, db_column='cowork_guid')
    coworker_guid = models.ForeignKey(Persons, related_name='coworker', on_delete=models.CASCADE,
                                      db_column='coworker_guid')
    foworker_guid = models.ForeignKey(Persons, related_name='foworker', on_delete=models.CASCADE,
                                      db_column='foworker_guid')
    coworker_enterprise_guid = models.ForeignKey(Enterprises, related_name='coworker_enterprise',
                                                 on_delete=models.CASCADE, db_column='coworker_enterprise_guid')
    enterprise_guid = models.ForeignKey(Enterprises, related_name='enterprise', on_delete=models.CASCADE,
                                        db_column='enterprise_guid')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    count_hours = models.FloatField(db_column='count_hours')
    cowork_state = models.IntegerField(db_column='cowork_state')
    cowork_local = models.IntegerField(db_column='cowork_local')
    record_fixed = models.IntegerField(db_column='record_fixed')
    note = models.CharField(max_length=256, db_column='note')
    is_deleted = models.IntegerField(db_column='is_deleted', default=0)
    service_note = models.IntegerField(db_column='service_note', default=0)
    author = models.CharField(max_length=128, db_column='author')
    change_status = models.IntegerField(db_column='change_status', choices=TYPE_CHOICES, default=0)

    class Meta:
        db_table = 'persons_coworks_history'
        managed = False
        # unique_together = ('dts', 'enterprise_guid', 'coworker_guid', 'foworker_guid', 'coworker_enterprise_guid')

    @staticmethod
    def save_history(pc, author, deleted=False):
        persons_coworks_history.objects.create(
            guid=str(uuid.uuid4()),
            cowork_guid=pc.guid,
            dts=pc.dts,
            record_date=datetime.today(),
            foworker_guid=pc.foworker_guid,
            coworker_guid=pc.coworker_guid,
            coworker_enterprise_guid=pc.coworker_enterprise_guid,
            enterprise_guid=pc.enterprise_guid,
            shedule_guid=pc.shedule_guid,
            position_guid=pc.position_guid,
            count_hours=pc.count_hours,
            cowork_state=pc.cowork_state,
            cowork_local=pc.cowork_local,
            record_fixed=pc.record_fixed,
            note=pc.record_fixed,
            is_deleted=pc.is_deleted,
            service_note=pc.service_note,
            author=author,
            change_status=deleted
        )

    @staticmethod
    def get_history(enterprise, dts):
        begin_date = dts.replace(day=1)
        end_date = persons_reworks.last_day_of_month(dts)

        return persons_coworks_history.objects.filter(dts__range=(begin_date, end_date),
                                                      enterprise_guid=enterprise).order_by('-dts')


class ImageCoworks(models.Model):
    guid = models.CharField(primary_key=True, max_length=64, db_column='guid', default=str(uuid.uuid4()))
    persons_coworks = models.ForeignKey(persons_coworks, related_name='image_cowork', on_delete=models.CASCADE,
                                        db_column='persons_coworks')
    image = models.ImageField(upload_to='image_cowork/%Y%m/')
    deleted_cowork = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)

    @staticmethod
    def save_optimal_size(obj_pcowork, image, deleted, confirm):
        image_cowork = ImageCoworks.objects.filter(persons_coworks=obj_pcowork)
        image.name = obj_pcowork.guid + '.jpg'
        if len(image_cowork) == 0:
            ImageCoworks.objects.create(guid=str(uuid.uuid4()),
                                        persons_coworks=obj_pcowork,
                                        image=image,
                                        deleted_cowork=deleted,
                                        confirmed=confirm)
        else:
            # ImageCoworks.objects.update(guid=image_cowork[0].guid,
            #                             persons_coworks=obj_pcowork,
            #                             image=image,
            #                             deleted_cowork=deleted,
            #                             confirmed=confirm)
            image_cowork[0].image = image
            image_cowork[0].save()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        temp_image = Image.open(self.image)
        output = BytesIO()
        temp_image.save(output, format="JPEG", quality=30)
        output.seek(0)

        self.image = InMemoryUploadedFile(output, 'ImageField', "%s.jpg" % self.image.name.split('.')[0], 'image/jpeg',
                                          sys.getsizeof(output), None)

        super(ImageCoworks, self).save()

    class Meta:
        db_table = 'image_coworks'
        managed = False


class persons_reworks(models.Model):
    guid = models.CharField(primary_key=True, max_length=64, db_column='guid', default=str(uuid.uuid4()))
    dts = models.DateField(db_column='dts')
    coworker_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='coworker_guid')
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    count_hours = models.FloatField(db_column='count_hours')
    dts_audit = models.DateField(db_column='dts_audit')
    is_deleted = models.IntegerField(db_column='is_deleted')

    class Meta:
        db_table = 'persons_reworks'
        managed = False

    def last_day_of_month(any_day):
        if any_day.month == 12:
            return date(any_day.year + 1, 1, 1) - timedelta(days=1)
        return date(any_day.year, any_day.month + 1, 1) - timedelta(days=1)

    def get_context(dts, enterprise):

        begin_date = dts.replace(day=1)
        end_date = persons_reworks.last_day_of_month(dts)

        return persons_reworks.objects.filter(dts_audit__range=(begin_date, end_date), enterprise_guid=enterprise)

    def get_context_day(dts, enterprise):
        return persons_reworks.objects.filter(dts_audit=dts, enterprise_guid=enterprise)

    def get_date_free_timesheet_fact(end_date, personel):
        begin_date = date(end_date.year, end_date.month, 1)

        qset_nofree_date_rework = persons_reworks.objects.filter(dts__range=(begin_date, end_date),
                                                                 coworker_guid=personel)
        qset_nofree_date_cowork = persons_reworks.objects.filter(dts__range=(begin_date, end_date),
                                                                 coworker_guid=personel)

        list_nofree_date = []
        if len(qset_nofree_date_rework) > 0:
            list_nofree_date = [i.dts for i in qset_nofree_date_rework]

        if len(qset_nofree_date_cowork) > 0:
            list_nofree_date = list_nofree_date + [i.dts for i in qset_nofree_date_cowork]

        data_free_date = TimeSheetFact.objects.filter(p_uid__dts__range=(begin_date, end_date),
                                                      p_uid__person_guid=personel, p_uid__suspicious=0,
                                                      busy_key_fact__guid='5A688F12-74A8-11E8-80F9-3640B58B95BD').exclude(
            p_uid__dts__in=list_nofree_date).order_by('-p_uid__dts').first()

        if data_free_date == None:
            return end_date
        else:
            return data_free_date.p_uid.dts


class persons_reworks_history(models.Model):
    guid = models.CharField(primary_key=True, max_length=64, db_column='guid', default=str(uuid.uuid4()))
    rework_guid = models.ForeignKey(persons_reworks, on_delete=models.CASCADE, db_column='rework_guid')
    dts = models.DateField(db_column='dts')
    record_date = models.DateField(db_column='[record_date]')
    coworker_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='coworker_guid')
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    count_hours = models.FloatField(db_column='count_hours')
    dts_audit = models.DateField(db_column='dts_audit')
    is_deleted = models.IntegerField(db_column='is_deleted')
    author = models.CharField(max_length=128, db_column='author')

    class Meta:
        db_table = 'persons_reworks_history'
        managed = False

    @staticmethod
    def save_history(persons_reworks, author):
        persons_reworks_history.objects.create(
            guid=str(uuid.uuid4()),
            dts=persons_reworks.dts,
            rework_guid=persons_reworks,
            record_date=datetime.today(),
            coworker_guid=persons_reworks.coworker_guid,
            enterprise_guid=persons_reworks.enterprise_guid,
            position_guid=persons_reworks.position_guid,
            count_hours=persons_reworks.count_hours,
            dts_audit=persons_reworks.dts_audit,
            is_deleted=persons_reworks.is_deleted,
            author=author
        )


class persons_audit(models.Model):
    uid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='uid')
    change_date = models.DateField(db_column='change_date')
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    count_state = models.FloatField(db_column='count_state')
    count_staff = models.FloatField(db_column='count_staff')

    def __str__(self):
        return '' + str(self.enterprise_guid) + '/' + str(self.position_guid)

    class Meta:
        db_table = 'persons_audit'
        managed = False
        unique_together = ('change_date', 'enterprise_guid', 'position_guid')

    def get_state_on_audit(slef, enterprise, position, count_state, dts):
        count_personel = 0

        with connection.cursor() as cursor:
            cursor.execute(
                "select position_guid, SUM (amount) from [get_staff_laststate] ('" + enterprise.guid + "', '" + str(
                    dts) + "') where position_guid = '" + position.guid + "'  group by position_guid")

            setobj = cursor.fetchall()
            if len(setobj) == 0:
                count_personel = 1
            else:
                count_personel = math.ceil(float(setobj[0][1]) * count_state / 100)

        return count_personel

    def get_context(self, enterprise, dts):
        replace_en = {}
        init = persons_audit.objects.filter(enterprise_guid=enterprise)

        if len(init) == 0:
            init = persons_audit.objects.filter(enterprise_guid='00000000-0000-0000-0000-000000000000')

        for i in init:
            count_personel = 0
            if i.count_staff > 0:
                count_personel = int(i.count_staff)

            if i.count_state > 0:
                count_personel = self.get_state_on_audit(self, enterprise, i.position_guid, i.count_state, dts)

            replace_en[i.position_guid] = count_personel

        return replace_en


class enterprise_revision(models.Model):
    uid = models.CharField(primary_key=True, unique=True, max_length=64)
    enterprise_uid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_uid')
    revision_date = models.DateField(db_column='revision_date')

    class Meta:
        db_table = 'enterprise_revision'
        managed = False
        ordering = ['-revision_date']


class enterprise_revision_changes(models.Model):
    uid = models.CharField(primary_key=True, unique=True, max_length=64)
    changetype = models.CharField(max_length=64, db_column='changetype')
    changetime = models.DateField(db_column='changetime')

    class Meta:
        db_table = 'enterprise_revision_changes'
        managed = False


class persons_extended_info(models.Model):
    person_guid = models.ForeignKey(Persons, primary_key=True, on_delete=models.CASCADE, db_column='person_guid')
    dts = models.DateField(db_column='dts')
    status_id = models.IntegerField(db_column='status_id')

    class Meta:
        db_table = 'persons_extended_info'
        managed = False


class ProfileUser(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Enterprises, on_delete=models.CASCADE, null=True, blank=True)
    ip_shop = models.CharField(max_length=30, blank=True)
    revisor = models.BooleanField(null=True)
    otiz = models.BooleanField(null=False, default=False)
    sb = models.BooleanField(null=False, default=False)
    max_vacancy = models.BooleanField(null=False, default=False)
    readly_only = models.BooleanField(null=False, default=False)

    def __str__(self):
        return str(self.user)

    def get_profile(self, user):
        return ProfileUser.objects.get(user=user)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            ProfileUser.objects.create(user=instance)


class SettingTableTemp(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    count_day_last = models.IntegerField(db_column='count_day_last')
    time_close_table = models.IntegerField(db_column='time_close_table')
    enterprise = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise')
    close_date_full_table = models.DateField(db_column='close_date_full_table')

    def __str__(self):
        return f'Общие настройки' if self.enterprise.guid == '00000000-0000-0000-0000-000000000000' else f'Настройки {self.enterprise}'

    class Meta:
        managed = False
        db_table = 'TimeSheet_settingtabletemp'

    @staticmethod
    def get_time_close_table(ent):

        temp_setting = SettingTableTemp.objects.filter(enterprise=ent).first()
        if temp_setting is not None:
            return temp_setting.time_close_table

        temp_setting = SettingTableTemp.objects.filter(enterprise='00000000-0000-0000-0000-000000000000').first()
        if temp_setting is not None:
            return temp_setting.time_close_table

        return 11

    @staticmethod
    def get_open_day_table(ent):

        temp_setting = SettingTableTemp.objects.filter(enterprise=ent).first()
        if temp_setting is not None:
            return temp_setting.count_day_last

        temp_setting = SettingTableTemp.objects.filter(enterprise='00000000-0000-0000-0000-000000000000').first()
        if temp_setting is not None:
            return temp_setting.count_day_last

        return 1

    @staticmethod
    def get_sign_of_closing_timesheet_on_date(ent, dts):
        temp_setting = SettingTableTemp.objects.filter(enterprise=ent).first()
        if temp_setting is not None:
            if temp_setting.close_date_full_table is None:
                return 0

            if temp_setting.close_date_full_table.year > dts.year:
                return 1
            elif temp_setting.close_date_full_table.month >= dts.month:
                return 1
            else:
                return 0

        temp_setting = SettingTableTemp.objects.filter(enterprise='00000000-0000-0000-0000-000000000000').first()
        if temp_setting is not None:
            if temp_setting.close_date_full_table is None:
                return 0

            if temp_setting.close_date_full_table.year > dts.year:
                return 1
            elif temp_setting.close_date_full_table.month >= dts.month and temp_setting.close_date_full_table.year >= dts.year:
                return 1
            else:
                return 0

        return 0


class shift_data_f_history(models.Model):
    uid = models.CharField(primary_key=True, unique=True, max_length=64)
    dts = models.DateField(db_column='dts')
    author = models.CharField(max_length=64, db_column='author')
    f_plan_uid = models.ForeignKey(TimeSheetFact, on_delete=models.CASCADE, db_column='f_plan_uid')
    f_busy_key_uid = models.ForeignKey(BusyKeys, on_delete=models.CASCADE, db_column='f_busy_key_uid')
    f_amount = models.FloatField(db_column='f_amount')
    p_person_guid = models.ForeignKey(Persons, related_name='person_guid', on_delete=models.CASCADE,
                                      db_column='p_person_guid')
    p_enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='p_enterprise_guid')
    p_shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='p_shedule_guid')
    p_busy_key_guid = models.ForeignKey(BusyKeys, related_name='p_busy_key_guid', on_delete=models.CASCADE,
                                        db_column='p_busy_key_guid')
    p_suspicious = models.IntegerField(db_column='p_suspicious')

    def get_history(person, enterprise, dts):
        begin_date = dts.replace(day=1)
        end_date = persons_reworks.last_day_of_month(dts)

        return shift_data_f_history.objects.filter(f_plan_uid__p_uid__dts__range=(begin_date, end_date),
                                                   p_enterprise_guid=enterprise, p_person_guid=person).order_by('-dts')

    class Meta:
        db_table = 'shift_data_f_history'
        managed = False


class setting_filter(models.Model):
    user_id = models.IntegerField(primary_key=True, unique=True, db_column='user_id')
    persons = models.CharField(max_length=64, db_column='persons')
    enterprise = models.CharField(max_length=64, db_column='enterprise')
    dts = models.DateField(db_column='dts')

    def get_str(id):
        set_user = setting_filter.objects.filter(user_id=id).first()

        str_f = ''
        if set_user != None:
            if set_user.enterprise != '00000000-0000-0000-0000-000000000000':
                str_f += f' Подразделение: {Enterprises.objects.get(guid=set_user.enterprise)}'

            if set_user.persons != '00000000-0000-0000-0000-000000000000':
                str_f += f' Сотрудник: {Persons.objects.get(guid=set_user.persons)}'

        return str_f

    class Meta:
        db_table = 'setting_filter'
        managed = False


class PositionsWhitelist(models.Model):
    position_guid = models.ForeignKey(Positions, primary_key=True, on_delete=models.CASCADE, db_column='position_guid',
                                      verbose_name='Должность')

    def __str__(self):
        return self.position_guid.full_name

    class Meta:
        managed = False
        db_table = 'positions_whitelist'
        verbose_name_plural = 'Разрешенные должности'
        verbose_name = 'Разрешенная должность'


class Trained_staff(models.Model):
    guid = models.CharField(max_length=64, db_column='guid')
    person_guid = models.ForeignKey(Persons, primary_key=True, on_delete=models.CASCADE,
                                    verbose_name='Сотрудник', db_column='person_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE,
                                      verbose_name='Должность', db_column='position_guid')

    def __str__(self):
        return f'{self.person_guid}({self.position_guid})'

    @staticmethod
    def get_sign_teached(person):
        obj = Trained_staff.objects.filter(person_guid=person)
        if len(obj) > 0:
            return 1
        else:
            return 0

    class Meta:
        managed = False
        db_table = 'trained_staff'
        verbose_name_plural = 'Обученные сотрудники'
        verbose_name = 'Обученный сотрудник'


class Check_names(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, db_column='id')
    name = models.CharField(max_length=256, db_column='name')
    belong_to = models.CharField(max_length=16, db_column='belong_to')
    finished = models.IntegerField(db_column='finished')
    result = models.IntegerField(db_column='result')

    def get_next_statuses(self):
        check_rel = Check_relations.objects.filter(check_id_f=self.id)
        list_check_name = [i.check_id_t for i in check_rel]
        return list_check_name

    class Meta:
        db_table = 'check_names'
        managed = False

    def __str__(self):
        return f'{self.name}'


class Check_relations(models.Model):
    check_id_f = models.ForeignKey(Check_names, related_name='check_id_f', on_delete=models.CASCADE, primary_key=True,
                                   db_column='check_id_f')
    check_id_t = models.ForeignKey(Check_names, related_name='check_id_t', on_delete=models.CASCADE,
                                   db_column='check_id_t')

    class Meta:
        db_table = 'check_relations'
        managed = False
        unique_together = ('check_id_f', 'check_id_t')


class Shift_data_f_checks(models.Model):
    '''
       type - имеет 3 варинта
       0 - табель факт
       1 - табель подработки
       2 - табель ревизии
    '''

    TYPE_CHOICES = (
        (0, 'корректировка факта'),
        (1, 'корретировка подработок/совмещений'),
        (2, 'корректировка ревизии')
    )

    uid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='uid')
    link_uid = models.CharField(max_length=64, db_column='link_uid')
    dd = models.DateField(db_column='dd')
    dt = models.TimeField(db_column='dt')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    shedule_guid = models.ForeignKey(Shedules, on_delete=models.CASCADE, db_column='shedule_guid')
    foworker_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='foworker_guid')
    busy_key_f = models.ForeignKey(BusyKeys, related_name='busy_key_f', on_delete=models.CASCADE,
                                   db_column='busy_key_f')
    busy_key_t = models.ForeignKey(BusyKeys, related_name='busy_key_t', on_delete=models.CASCADE,
                                   db_column='busy_key_t')
    amount = models.FloatField(db_column='amount')
    cowork_state = models.IntegerField(db_column='cowork_state', default=0)
    type = models.IntegerField(db_column='type', choices=TYPE_CHOICES, default=0)
    enterprise = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise')
    number_doc = models.IntegerField(db_column='number_doc', default=1)

    def __str__(self):
        tf = TimeSheetFact.objects.get(uid=self.link_uid)
        return f'{tf.p_uid.person_guid} за {dateformat.format(tf.p_uid.dts, "d F Y")} №{self.number_doc}'

    def get_last_record_status(self):
        return Shift_data_f_checks_statuses.objects.filter(data_f_check_uid=self.uid).order_by('-dts').first()

    def get_all_record_status(self):
        return Shift_data_f_checks_statuses.objects.filter(data_f_check_uid=self.uid).order_by('dts')

    @staticmethod
    def get_text_query_all():
        return '''SELECT sh.*, sh_st.status_id
                  FROM shift_data_f_checks as sh
                    left join (select data_f_check_uid, max(dts) as dts from shift_data_f_checks_statuses group by data_f_check_uid) as sh_st_max on sh.uid = sh_st_max.data_f_check_uid
                        left join shift_data_f_checks_statuses as sh_st on sh_st_max.dts = sh_st.dts and sh_st_max.data_f_check_uid = sh_st.data_f_check_uid'''

    @staticmethod
    def get_text_query_enterprise():
        return '''SELECT sh.*, sh_st.status_id
                  FROM shift_data_f_checks as sh
                    left join (select data_f_check_uid, max(dts) as dts from shift_data_f_checks_statuses group by data_f_check_uid) as sh_st_max on sh.uid = sh_st_max.data_f_check_uid
                        left join shift_data_f_checks_statuses as sh_st on sh_st_max.dts = sh_st.dts and sh_st_max.data_f_check_uid = sh_st.data_f_check_uid
                    inner join shift_data_f as f on f.uid = sh.shift_data_f_uid
                        inner join shift_data_p as pl on pl.uid = f.p_uid and pl.enterprise_guid = %s'''

    @staticmethod
    def get_shift_data_f_shecks(enterprise=None):

        with connection.cursor() as cursor:
            if enterprise == None:
                cursor.execute(Shift_data_f_checks.get_text_query_all())
            else:
                cursor.execute(Shift_data_f_checks.get_text_query_enterprise(), enterprise.guid)

            # cursor.fetchall()
            setobj = named_tuple_fetchall(cursor)

        return setobj

    @staticmethod
    def get_number():

        record_last = Shift_data_f_checks.objects.all().order_by('-number_doc').first()
        if record_last is None:
            return 1

        return record_last.number_doc + 1

    class Meta:
        db_table = 'shift_data_f_checks'
        managed = False


class Shift_data_f_checks_statuses(models.Model):
    uid = models.CharField(primary_key=True, unique=True, max_length=64, db_column='uid')
    data_f_check_uid = models.ForeignKey(Shift_data_f_checks, related_name='data_f_check_detail',
                                         on_delete=models.CASCADE, db_column='data_f_check_uid')
    dts = models.DateTimeField(db_column='dts')
    status_id = models.ForeignKey(Check_names, on_delete=models.CASCADE, db_column='status_id')
    comment = models.CharField(max_length=512, db_column='comment')

    class Meta:
        db_table = 'shift_data_f_checks_statuses'
        managed = False


class Route_sheets(models.Model):
    enterprise_guid = models.ForeignKey(Enterprises, primary_key=True, on_delete=models.CASCADE,
                                        db_column='enterprise_guid')
    person_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='person_guid')
    fd = models.DateTimeField(db_column='fd')
    td = models.DateTimeField(db_column='td')

    class Meta:
        db_table = 'route_sheets'
        managed = False


class Mtv_cashier(models.Model):
    year = models.IntegerField(db_column='y')
    month = models.IntegerField(db_column='m')
    enterprise_guid = models.ForeignKey(Enterprises, primary_key=True, on_delete=models.CASCADE,
                                        db_column='enterprise_guid')
    person_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='person_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    checks_count = models.IntegerField(db_column='checks_count')
    speed_avg = models.FloatField(db_column='speed_avg')
    p_amt = models.IntegerField(db_column='p_amt')
    f_amt = models.IntegerField(db_column='f_amt')
    efficiency = models.FloatField(db_column='efficiency')
    checks_avg = models.FloatField(db_column='checks_avg')
    prize = models.FloatField(db_column='prize')
    prize_view = models.FloatField(db_column='prize_view')
    ml = models.IntegerField(db_column='ml')
    mc = models.IntegerField(db_column='mc')

    class Meta:
        db_table = 'mtv_cashier'
        managed = False


class Mtv_header(models.Model):
    year = models.IntegerField(db_column='y')
    month = models.IntegerField(db_column='m')
    enterprise_guid = models.ForeignKey(Enterprises, primary_key=True, on_delete=models.CASCADE,
                                        db_column='enterprise_guid')
    person_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='person_guid')
    position_guid = models.ForeignKey(Positions, on_delete=models.CASCADE, db_column='position_guid')
    p_amt = models.IntegerField(db_column='p_amt')
    f_amt = models.IntegerField(db_column='f_amt')
    # checks_avg = models.FloatField(db_column='checks_avg')
    prize = models.FloatField(db_column='prize')
    speed_avg = models.FloatField(db_column='speed_avg')
    ml = models.IntegerField(db_column='ml')
    prize_view = models.FloatField(db_column='prize_view')
    mc = models.IntegerField(db_column='mc')

    class Meta:
        db_table = 'mtv_header'
        managed = False


class persons_covid19(models.Model):
    uid = models.CharField(primary_key=True, unique=True, editable=False, max_length=64)
    enterprise_guid = models.ForeignKey(Enterprises, on_delete=models.CASCADE, db_column='enterprise_guid')
    person_guid = models.ForeignKey(Persons, on_delete=models.CASCADE, db_column='person_guid')
    dts = models.DateField(db_column='dts')
    vaccination_type = models.IntegerField()
    vaccination_declined = models.IntegerField()
    having_qr_code = models.IntegerField(db_column='having_qr_code')
    reply_code = models.IntegerField(db_column='reply_code')
    last_week_checkin = models.IntegerField(db_column='last_week_checkin')

    class Meta:
        db_table = 'persons_covid19'
        managed = False


class covid19_dtype(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    descr = models.CharField(max_length=512)

    class Meta:
        db_table = 'covid19_dtype'
        managed = False


class covid19_vtype(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    descr = models.CharField(max_length=512)

    class Meta:
        db_table = 'covid19_vtype'
        managed = False


class covid19_reply_codes(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    descr = models.CharField(max_length=128)

    class Meta:
        db_table = 'covid19_reply_codes'
        managed = False
