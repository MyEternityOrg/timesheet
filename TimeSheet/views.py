import calendar

import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import TimeSheetPlane, Enterprises, TimeSheetFact, BusyKeys, Persons, Shedules, persons_coworks, \
    persons_coworks_history, \
    Positions, PositionsReplacement, ProfileUser, persons_reworks, persons_reworks_history, persons_audit, StaffHistory, \
    enterprise_revision, SheduleHours, enterprise_revision_changes, persons_extended_info, shift_data_f_history, \
    setting_filter, Shift_data_f_checks, BusyKeysReplacement, Check_names, Shift_data_f_checks_statuses, \
    Check_relations, Trained_staff, StaffVacancy, ImageCoworks, Route_sheets, Mtv_cashier, Mtv_header, PersonShedule, persons_covid19, covid19_reply_codes
from django.contrib import messages
from .forms import TimeSheetFormSet_full, TimeSheetFormSet_full_fact, revisor_detail
from datetime import datetime, date, time, timedelta
from django.db.models import Q
from django.utils import dateformat
import uuid
from django.contrib.auth.decorators import login_required
from operator import or_, not_, and_
from functools import reduce
from django.db import connection

from django.template.defaulttags import register
import socket
from django.contrib.auth import authenticate, login
import json
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView

from django.urls import reverse_lazy, reverse

from .decorator_ts import timeover_timeshift
from django.core.paginator import Paginator
from django import forms

from django.db.models import Max, Count
import base64
from PIL import Image
from io import BytesIO
# import datauri

#
# from django.http import FileResponse
# from reportlab.pdfgen import canvas
# import io
# from easy_pdf.rendering import render_to_pdf


from .utils import render_to_pdf


@login_required
def dashboard(request):
    return render(request, 'TimeSheet/dashboard.html')


@login_required
def TimeSheet_list_view(request):
    profile = ProfileUser.get_profile(ProfileUser, request.user)

    if not profile.user.is_superuser:
        if profile.revisor:
            return redirect('revision-list')
        elif profile.sb:
            return redirect('shift_data_f_checks')

    # if profile.entreprise != None:
    #     data = TimeSheetPlane.get_list_table_enterprise(TimeSheetPlane, profile.entreprise)
    # else:
    #     data = TimeSheetPlane.get_all_list_table(request)

    data = TimeSheetPlane.get_table_list(request, profile.entreprise)
    # data = TimeSheetPlane.objects.all().values_list('enterprise_guid', 'month', 'year')

    dict_month = {1: 'Январь',
                  2: 'Февраль',
                  3: 'Март',
                  4: 'Апрель',
                  5: 'Май',
                  6: 'Июнь',
                  7: 'Июль',
                  8: 'Август',
                  9: 'Сентябрь',
                  10: 'Октябрь',
                  11: 'Ноябрь',
                  12: 'Декабрь'}

    str_filter = setting_filter.get_str(request.user.id)

    return render(request, 'TimeSheet/test/timesheet_list.html',
                  {'data_set': data, 'sheet_shop': 'Список табелей', 'dict_month': dict_month,
                   'str_filter': str_filter,
                   'otiz': profile.otiz}, )


# @timeover_timeshift
@login_required
def TimeSheet_table_view(request, enterprise, year, month):
    if request.method == 'POST':
        return redirect('edit-table', enterprise=enterprise, pk=request.POST['date_edit'])

    else:
        # print(datetime.now())

        field_search = request.GET.get('field_search')
        if field_search is None:

            select_pers_work = TimeSheetPlane.objects.values('person_guid').filter(enterprise_guid=enterprise,
                                                                                   year=year,
                                                                                   month=month).exclude(
                person_guid='00000000-0000-0000-0000-000000000000').exclude(
                busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618').filter(suspicious=0).order_by(
                'person_guid__full_name').annotate(
                total=Count('person_guid'))

            field_search = ''
        else:
            select_pers_work = TimeSheetPlane.objects.values('person_guid').filter(enterprise_guid=enterprise,
                                                                                   year=year, month=month, ).filter(
                person_guid__full_name__contains=field_search).exclude(
                person_guid='00000000-0000-0000-0000-000000000000').exclude(
                busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618').filter(suspicious=0).order_by(
                'person_guid__full_name').annotate(
                total=Count('person_guid'))

        ## Пагинатор
        paginator = Paginator(select_pers_work, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # print(datetime.now())

        list_pers_guid_work = list(map(lambda i: i['person_guid'], page_obj.object_list))
        data_sheet = TimeSheetPlane.objects.filter(enterprise_guid=enterprise, year=year, month=month).exclude(
            person_guid='00000000-0000-0000-0000-000000000000').exclude(
            busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618').filter(suspicious=0).filter(
            person_guid__guid__in=list_pers_guid_work).order_by(
            'person_guid__full_name')

        init_fact = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__year=year,
                                                 p_uid__month=month,
                                                 p_uid__suspicious=0,
                                                 p_uid__person_guid__guid__in=list_pers_guid_work)  # .exclude(p_uid__busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618')

        # транспонирование
        interval_month = calendar.monthrange(int(year), int(month))
        # print('------------1')
        # print(datetime.now())
        # transposed = TimeSheetPlane.transposed_TimeSheetplan(data_sheet, init_fact, date(int(year), int(month),
        #                                                                                  interval_month[1]))
        # print(datetime.now())
        # print('------------1')
        # #
        # print('------------2')
        # print(datetime.now())
        transposed = TimeSheetPlane.transposed_table_fast(data_sheet, init_fact, date(int(year), int(month),
                                                                                      interval_month[1]))
        # print(datetime.now())
        # print('------------2')

        # print(datetime.now())

        # list_date = TimeSheetPlane.get_list_date(data_sheet)
        list_date = TimeSheetPlane.get_list_date_day(date(int(year), int(month), 1))
        ent = Enterprises.objects.get(guid=enterprise)

        # date_t = datetime.combine(date(int(year), int(month), 1), time(1, 1)).strftime("%B %Y")
        date_t_f = datetime.combine(date(int(year), int(month), 1), time(1, 1))
        date_t = dateformat.format(date_t_f, "F Y")

        data_coworks = persons_coworks.get_context(date_t_f, enterprise)
        imgcowork = ImageCoworks.objects.filter(persons_coworks__in=[i.guid for i in data_coworks])
        data_coworks = list(map(lambda i: {
            'guid': i.guid,
            'dts': i.dts,
            'coworker_guid': i.coworker_guid,
            'foworker_guid': i.foworker_guid,
            'coworker_enterprise_guid': i.coworker_enterprise_guid,
            'enterprise_guid': i.enterprise_guid,
            'shedule_guid': i.shedule_guid,
            'position_guid': i.position_guid,
            'count_hours': i.count_hours,
            'cowork_state': i.cowork_state,
            'cowork_local': i.cowork_local,
            'record_fixed': i.record_fixed,
            'note': i.note,
            'is_deleted': i.is_deleted,
            'service_note': i.service_note,
            'img': list(filter(lambda x: x.persons_coworks == i, imgcowork))
        }, data_coworks))

        data_reworks = persons_reworks.get_context(date_t_f, enterprise)

        hidden_h = True
        profile = ProfileUser.get_profile(ProfileUser, request.user)
        day_open = ent.get_list_open_day(date_t_f, profile)
        if profile.entreprise != None:
            hidden_h = False

        dict_rem_pers = {i.person_guid: i.dts for i in persons_extended_info.objects.all()}
        # print(datetime.now())

        if profile.readly_only:
            day_open = []

        return render(request, 'TimeSheet/test/timesheet_table_test.html',
                      {'data': transposed, 'sheet_shop': ent, 'list_date': list_date,
                       'enterprise': enterprise, 'date_sheet': date_t,
                       'data_coworks': data_coworks,
                       'data_reworks': data_reworks,
                       'hidden_h': hidden_h,
                       'day_open': day_open,
                       'year': year, 'month': month,
                       'dict_rem_pers': dict_rem_pers,
                       'page_obj': page_obj,
                       'field_search': field_search})


def TimeSheet_table_view_full(request):
    if request.method == 'POST':
        return HttpResponse('Done')
    else:

        data_sheet = TimeSheetPlane.objects.all()[:100]

        list_date = TimeSheetPlane.get_list_date(data_sheet)
        print(list_date)

        print(datetime.today())
        formSet = TimeSheetFormSet_full(queryset=data_sheet)
        print(datetime.today())

        return render(request, 'TimeSheet/timesheet_test_copy.html', {'formset': formSet, 'list_date': list_date})


@timeover_timeshift
@login_required
def TimeSheet_detail_View(request, enterprise, pk):
    if request.method == 'POST':

        this_shop = False
        profile = ProfileUser.get_profile(ProfileUser, request.user)
        if profile.entreprise != None:
            this_shop = True

        if request.POST['close_table'] == "Сохранить" or request.POST['close_table'] == "Подработки/Совмещения" or \
                request.POST['close_table'] == "Ревизия":
            fl_save = False
            for i in range(int(request.POST['len_str'])):
                str_name = 'form-' + str(i)
                p_uid_temp = request.POST[str_name + '-p_uid']
                f_busy = request.POST['form-busy_key_guid_' + str(i)]
                f_amount = request.POST['form_fact_amount_' + str(i)]

                busy_key_nigth = BusyKeys.objects.get(guid='E1916359-15C4-11E9-8112-00155D6DE618')

                if f_busy != 'selected':

                    time_plane = TimeSheetPlane.objects.get(p_uid=p_uid_temp)

                    if str(f_busy) == '5A688F01-74A8-11E8-80F9-3640B58B95BD':
                        n_record_coworks = persons_coworks.objects.filter(dts=time_plane.dts,
                                                                          coworker_guid=time_plane.person_guid
                                                                          ).exclude(
                            enterprise_guid=request.POST['enterprise'])
                        n_record_fact = TimeSheetFact.objects.filter(p_uid__dts=time_plane.dts,
                                                                     p_uid__person_guid=time_plane.person_guid,
                                                                     busy_key_fact='5A688F01-74A8-11E8-80F9-3640B58B95BD').exclude(
                            p_uid__enterprise_guid=request.POST['enterprise'])

                        if len(n_record_coworks) != 0:
                            messages.warning(request,
                                             f'Сотрудник {time_plane.person_guid} уже табелирован в {n_record_coworks[0].enterprise_guid} и не будет сохранен!')
                            continue
                        elif len(n_record_fact) != 0:
                            messages.warning(request,
                                             f'Сотрудник {time_plane.person_guid} уже табелирован в {n_record_fact[0].p_uid.enterprise_guid} и не будет сохранен!')
                            continue

                        if this_shop:
                            nigth_hour = TimeSheetPlane.objects.filter(dts=time_plane.dts,
                                                                       person_guid=time_plane.person_guid,
                                                                       enterprise_guid=request.POST['enterprise'],
                                                                       busy_key_guid=busy_key_nigth).first()

                            if nigth_hour != None:
                                f_model_nigth = TimeSheetFact.objects.filter(p_uid=nigth_hour.p_uid).first()

                                if f_model_nigth == None:
                                    TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                                                 busy_key_fact=busy_key_nigth,
                                                                 amount=nigth_hour.hours_all,
                                                                 p_uid=nigth_hour,
                                                                 record_fixed=1)
                                else:
                                    row_t_fact_nigth = f_model_nigth
                                    row_t_fact_nigth.amount = nigth_hour.hours_all
                                    row_t_fact_nigth.p_uid = nigth_hour
                                    row_t_fact_nigth.record_fixed = 1
                                    row_t_fact_nigth.save()

                    f_model = TimeSheetFact.objects.filter(p_uid=p_uid_temp).first()

                    if f_model is None:
                        if '' == f_busy:
                            continue

                        row_t_fact = TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                                                  busy_key_fact=BusyKeys.objects.get(guid=f_busy),
                                                                  amount=f_amount,
                                                                  p_uid=time_plane,
                                                                  record_fixed=1)
                        row_t_fact.save_history(user=request.user.username, f_uid=row_t_fact.uid)
                    else:
                        if '' == f_busy:
                            continue

                        row_t_fact = f_model
                        row_t_fact.busy_key_fact = BusyKeys.objects.get(guid=f_busy)
                        row_t_fact.amount = f_amount
                        row_t_fact.p_uid = time_plane
                        row_t_fact.record_fixed = 1
                        row_t_fact.save()

                        row_t_fact.save_history(user=request.user.username, f_uid=row_t_fact.uid)

                    fl_save = True

            if fl_save == True:
                messages.success(request, "Табель записан!")
            else:
                messages.warning(request, "Табель заполнен не полностью!")

            if request.POST['close_table'] == "Подработки/Совмещения":
                messages.success(request, "Подработки/Совмещения")

                return redirect('table-sheet-cowork', enterprise=request.POST['enterprise'], year=request.POST['year'],
                                month=request.POST['month'], day=request.POST['day'])

            elif request.POST['close_table'] == "Ревизия":
                return redirect('table-sheet-rework', enterprise=request.POST['enterprise'], year=request.POST['year'],
                                month=request.POST['month'], day=request.POST['day'])
            else:
                return redirect('table-sheet', enterprise=request.POST['enterprise'], year=request.POST['year'],
                                month=request.POST['month'])

        elif request.POST['close_table'] == "Закрыть":
            messages.info(request, "Табель не записан!")

            return redirect('table-sheet', enterprise=request.POST['enterprise'], year=request.POST['year'],
                            month=request.POST['month'])

        return HttpResponse('<h1>TIME SHEET ERROR</h1>')
    else:

        hidden_h = True
        profile = ProfileUser.get_profile(ProfileUser, request.user)

        if profile.readly_only:
            return redirect('dashboard')

        if profile.entreprise != None:
            hidden_h = False

        dts_date = date(int(pk[:4]), int(pk[5:7]), int(pk[8:10]))
        query = Q(enterprise_guid=enterprise) & Q(dts=dts_date)

        if hidden_h:
            init = TimeSheetPlane.objects.filter(query).exclude(
                person_guid='00000000-0000-0000-0000-000000000000').exclude(suspicious=1)
        else:
            init = TimeSheetPlane.objects.filter(query).exclude(
                person_guid='00000000-0000-0000-0000-000000000000').exclude(suspicious=1).exclude(
                busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618')

        init2 = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__dts=dts_date)
        form = TimeSheetFormSet_full(queryset=init)
        formfact = TimeSheetFormSet_full_fact(queryset=init2)
        ent = Enterprises.objects.get(guid=enterprise)

        tag_fact = TimeSheetFact.get_fact_detail(init, init2)

        disabled_revision = False
        record_revision = enterprise_revision.objects.filter(enterprise_uid=enterprise,
                                                             revision_date=dts_date - timedelta(days=1))
        if len(record_revision) == 0:
            disabled_revision = True

        return render(request, 'TimeSheet/test/timesheet_detail_test_modal.html', {'formset': form,
                                                                                   'sheet_shop': ent,
                                                                                   'dts': dts_date,
                                                                                   'enterprise': enterprise,
                                                                                   'len_str': len(init),
                                                                                   'form_fact': formfact,
                                                                                   'tag_fact': tag_fact,
                                                                                   'hidden_h': hidden_h,
                                                                                   'disabled_revision': disabled_revision,
                                                                                   'enterprise_code': ent.enterprise_code,
                                                                                   })


@timeover_timeshift
@login_required
def TimeSheet_table_view_cowork(request, enterprise, year, month, day):
    if request.method == 'POST':
        if request.POST['close_table'] == "Добавить Подработку":
            return redirect('create-cowork', enterprise=request.POST['enterprise'], year=year,
                            month=month, day=day, cowork_state=0)
        elif request.POST['close_table'] == "Добавить Совмещение":
            return redirect('create-cowork', enterprise=request.POST['enterprise'], year=request.POST['year'],
                            month=request.POST['month'], day=request.POST['day'], cowork_state=1)
        elif request.POST['close_table'] == "Табель":

            dts_date = date(int(request.POST['year']), int(request.POST['month']), int(request.POST['day']))

            return redirect('edit-table', enterprise=enterprise, pk=dts_date)
        else:
            return redirect('table-sheet', enterprise=request.POST['enterprise'], year=request.POST['year'],
                            month=request.POST['month'])
    else:

        date_t_f = date(int(year), int(month), int(day))
        data_coworks = list(persons_coworks.get_context_day(date_t_f, enterprise))
        ent = Enterprises.objects.get(guid=enterprise)

        # картинки
        imgcowork = ImageCoworks.objects.filter(persons_coworks__in=[i.guid for i in data_coworks])
        # data_coworks = list(map(lambda i: i['image'] = list(filter(lambda x: x.guid==i.guid, imgcowork)), data_coworks))
        data_coworks = list(map(lambda i: {
            'guid': i.guid,
            'dts': i.dts,
            'coworker_guid': i.coworker_guid,
            'foworker_guid': i.foworker_guid,
            'coworker_enterprise_guid': i.coworker_enterprise_guid,
            'enterprise_guid': i.enterprise_guid,
            'shedule_guid': i.shedule_guid,
            'position_guid': i.position_guid,
            'count_hours': i.count_hours,
            'cowork_state': i.cowork_state,
            'cowork_local': i.cowork_local,
            'record_fixed': i.record_fixed,
            'note': i.note,
            'is_deleted': i.is_deleted,
            'service_note': i.service_note,
            'img': list(filter(lambda x: x.persons_coworks == i, imgcowork))
        }, data_coworks))

        hidden_h = True
        profile = ProfileUser.get_profile(ProfileUser, request.user)
        if profile.entreprise != None:
            hidden_h = False

        return render(request, 'TimeSheet/work/timesheet_cowork.html', {'dataset': data_coworks, 'sheet_shop': ent,
                                                                        'dts': date_t_f, 'enterprise': enterprise,
                                                                        'hidden_h': hidden_h})


@timeover_timeshift
@login_required
def TimeSheet_table_view_rework(request, enterprise, year, month, day):
    if request.method == 'POST':
        if request.POST['close_table'] == "Добавить":
            return redirect('create-rework', enterprise=request.POST['enterprise'], year=request.POST['year'],
                            month=request.POST['month'], day=request.POST['day'])
        elif request.POST['close_table'] == "Табель":

            dts_date = date(int(request.POST['year']), int(request.POST['month']), int(request.POST['day']))

            return redirect('edit-table', enterprise=enterprise, pk=dts_date)
        else:
            return redirect('table-sheet', enterprise=request.POST['enterprise'], year=request.POST['year'],
                            month=request.POST['month'])
    else:

        date_t_f = date(int(year), int(month), int(day))
        data_coworks = persons_reworks.get_context_day(date_t_f, enterprise)
        ent = Enterprises.objects.get(guid=enterprise)

        hidden_h = True
        profile = ProfileUser.get_profile(ProfileUser, request.user)
        if profile.entreprise != None:
            hidden_h = False

        return render(request, 'TimeSheet/work/timesheet_rework.html', {'dataset': data_coworks, 'sheet_shop': ent,
                                                                        'dts': date_t_f, 'enterprise': enterprise,
                                                                        'hidden_h': hidden_h})


@timeover_timeshift
@login_required
def TimeSheet_table_creat_cowork(request, enterprise, year, month, day, cowork_state):
    if request.method == 'POST':
        if request.POST['close_table'] == "Сохранить":

            date_f = date(int(request.POST['year']), int(request.POST['month']), int(request.POST['day']))

            coworker_guid = Persons.objects.get(guid=request.POST['person_guid_to'])
            foworker_guid = Persons.objects.get(guid=request.POST['foworker_guid'])
            coworker_enterprise_guid = Enterprises.objects.get(guid=request.POST['enterprise_guid'])
            enterprise_guid = Enterprises.objects.get(guid=request.POST['enterprise'])
            shedule_guid = Shedules.objects.get(guid=request.POST['shedule_guid'])
            position_guid = Positions.objects.get(guid=request.POST['position_guid_to_val'])
            count_hours = float(request.POST['count_hours'].replace(",", "."))
            cowork_state = int(request.POST['cowork_state'])
            note = str(request.POST['note'])

            qSet = SheduleHours.objects.filter(dts__lte=date_f, shedule_guid=shedule_guid,
                                               busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD').order_by(
                "-dts").first()
            if qSet is not None:
                count_hours = qSet.hours_full if qSet.hours_full != 0 else qSet.hours_lite

            n_record_coworks = persons_coworks.objects.filter(dts=date_f,
                                                              coworker_guid=coworker_guid,
                                                              cowork_state=cowork_state)
            n_record_fact = []
            if cowork_state == 0:
                n_record_fact = TimeSheetFact.objects.filter(p_uid__dts=date_f,
                                                             p_uid__person_guid=coworker_guid,
                                                             busy_key_fact='5A688F01-74A8-11E8-80F9-3640B58B95BD'
                                                             )

            if len(n_record_coworks) == 0 and len(n_record_fact) == 0:

                if count_hours == 0:
                    qSet = SheduleHours.objects.filter(dts__lte=date_f, shedule_guid=shedule_guid,
                                                       busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD').order_by(
                        "-dts").first()
                    if qSet is not None:
                        count_hours = qSet.hours_full if qSet.hours_full != 0 else qSet.hours_lite

                new_obj = persons_coworks.objects.create(
                    guid=str(uuid.uuid4()),
                    dts=date_f,
                    coworker_guid=coworker_guid,
                    foworker_guid=foworker_guid,
                    coworker_enterprise_guid=coworker_enterprise_guid,
                    enterprise_guid=enterprise_guid,
                    shedule_guid=shedule_guid,
                    position_guid=position_guid,
                    count_hours=count_hours,
                    cowork_state=cowork_state,
                    cowork_local=0,
                    record_fixed=1,
                    note=note
                )
                persons_coworks_history.save_history(new_obj, request.user.username)

                if len(request.FILES) > 0:
                    ImageCoworks.save_optimal_size(new_obj, request.FILES['uploader'], False, False)
                # ImageCoworks.save_optimal_size(new_obj.guid, Image.frombytes("L", (3, 2), base64.b64decode(request.POST['imagebase64'])), False, False)
                # ImageCoworks.save_optimal_size(new_obj.guid, Image.frombytes("L", (3, 2), base64.b64decode(request.POST['imagebase64'])), False, False)
                # ImageCoworks.save_optimal_size(new_obj.guid, request.POST['imagebase64'], False, False)

            else:
                print(n_record_coworks, n_record_fact)
                if len(n_record_coworks) != 0 and n_record_coworks[0].enterprise_guid == enterprise_guid:
                    messages.error(request, 'Данный сотрудник уже есть в текущем табеле')
                elif len(n_record_coworks) != 0 and n_record_coworks[0].enterprise_guid != enterprise_guid:
                    messages.error(request, f'Данный сотрудник уже есть в табеле {n_record_coworks[0].enterprise_guid}')
                elif len(n_record_fact) != 0 and n_record_fact[0].p_uid.enterprise_guid == enterprise_guid:
                    messages.error(request,
                                   f'Данный сотрудник уже есть в табеле {n_record_fact[0].p_uid.enterprise_guid}')
                elif len(n_record_fact) != 0 and n_record_fact[0].p_uid.enterprise_guid != enterprise_guid:
                    messages.error(request,
                                   f'Данный сотрудник уже есть в табеле {n_record_fact[0].p_uid.enterprise_guid}')
                else:
                    messages.error(request, f'Данный сотрудник уже есть в табеле')

        return redirect('table-sheet-cowork', enterprise=request.POST['enterprise'], year=request.POST['year'],
                        month=request.POST['month'], day=request.POST['day'])
    else:

        profile = ProfileUser.get_profile(ProfileUser, request.user)
        fl_otiz = 1 if profile.otiz else 0

        if profile.readly_only:
            return redirect('dashboard')

        date_t_f = date(int(year), int(month), int(day))
        ent = Enterprises.objects.get(guid=enterprise)

        n_record_coworks = persons_coworks.objects.filter(dts=date_t_f,
                                                          cowork_state__in=[0, 1])
        list_exclude = []
        for i in n_record_coworks:
            list_exclude.append(i.foworker_guid)

        list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6', '5A688F06-74A8-11E8-80F9-3640B58B95BD',
                       '738B3878-17E4-11E9-80D0-E41F13C123D6',
                       '5A688F13-74A8-11E8-80F9-3640B58B95BD',
                       '5A688F03-74A8-11E8-80F9-3640B58B95BD',  # командировка/
                       '5A688F0C-74A8-11E8-80F9-3640B58B95BD',
                       '5A688F0B-74A8-11E8-80F9-3640B58B95BD',
                       '5A688F0A-74A8-11E8-80F9-3640B58B95BD',
                       '5A688F08-74A8-11E8-80F9-3640B58B95BD',  # учебный
                       ]
        # list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6'] #Отпуск убрал

        list_shedule_work = SheduleHours.get_list_shedules_work(date_t_f)

        init = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__dts=date_t_f,
                                            busy_key_fact__in=list_f_busy,
                                            p_uid__shedule_guid__in=list_shedule_work).exclude(
            p_uid__person_guid__in=list_exclude)
        init_en = Enterprises.get_list_shops(Enterprises)
        init_pos = Positions.objects.all()

        # {pers.p_uid.person_guid.guid}}|{{pers.p_uid.position_guid.guid}}|{{pers.p_uid.shedule_guid.guid}}|{{pers.p_uid.hours_all}

        init_work = []
        for i in init:
            new_dict = {'person_guid': i.p_uid.person_guid, 'position_guid': i.p_uid.position_guid,
                        'shedule_guid': i.p_uid.shedule_guid, 'hours_all': i.p_uid.hours_all}
            init_work.append(new_dict)

        init_vacancy = TimeSheetPlane.get_vacancy(enterprise=enterprise, date_f=date_t_f, user=request.user)
        if len(init_vacancy) > 0:
            pers_vacancy = Persons.objects.get(guid='00000000-0000-0000-0000-000000000000')
            for i in init_vacancy:
                init_work.append({'person_guid': pers_vacancy, 'position_guid': Positions.objects.get(guid=i[2]),
                                  'shedule_guid': Shedules.objects.get(guid=i[3]), 'hours_all': i[5]})

        if request.user.profileuser.otiz == 0:
            active_vacancy = StaffVacancy.check_over_state(ent, date_t_f)
            l_index = []
            for i in init_work:
                pos = active_vacancy.get(i['position_guid'])
                if pos is not None:
                    count_pos = pos.get(i['shedule_guid'])
                    if count_pos is None or count_pos <= 0:
                        l_index.append(init_work.index(i))

            for i in l_index[::-1]:
                init_work.pop(i)

        if ent.enterprise_code == 2 and fl_otiz:
            now_shedule = list({sh.shedule_guid.guid for sh in SheduleHours.objects.filter(dts=date_t_f,
                                                                                           busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')})
            pers_vacancy = Persons.objects.get(guid='10000000-0000-0000-0000-000000000000')  # внешние вакансии

            now_shift = TimeSheetPlane.objects.filter(enterprise_guid=enterprise, dts=date_t_f,
                                                      shedule_guid__in=now_shedule)
            set_shift = {}
            for sh in now_shift:
                if set_shift.get(sh.position_guid) is None:
                    set_shift[sh.position_guid] = [sh.shedule_guid, sh.hours_all]

            for k in set_shift:
                l_value = set_shift.get(k)
                init_work.append({'person_guid': pers_vacancy, 'position_guid': k, 'shedule_guid': l_value[0],
                                  'hours_all': l_value[1]})

        return render(request, 'TimeSheet/test/timesheet_create_cowork_modal.html', {'sheet_shop': ent,
                                                                                     'dts': date_t_f,
                                                                                     'enterprise': enterprise,
                                                                                     'init': init_work,
                                                                                     'init_en': init_en,
                                                                                     'init_pos': init_pos,
                                                                                     'cowork_state': cowork_state, })


def can_add_position_audit(obj_pos, pos_en, list_position_reworks):
    max_count_pos = pos_en.get(obj_pos)
    max_count_pos = 0 if max_count_pos is None else max_count_pos
    count_pos = list_position_reworks.count(obj_pos.guid)
    if max_count_pos > count_pos:
        return True
    else:
        return False


def get_position_audit_replace(position_personel, date_f, en):
    list_replace_pos = PositionsReplacement.get_replace_positions(position_personel.guid, 2)
    pos_en = persons_audit.get_context(persons_audit, enterprise=en, dts=date_f)
    list_position_reworks = list(
        persons_reworks.objects.filter(dts_audit=date_f, enterprise_guid=en).values_list('position_guid', flat=True))

    list_staff_vacancy = [i for i in StaffVacancy.get_active_state(en, date_f)]

    if len(list_replace_pos) > 0:
        if can_add_position_audit(position_personel, pos_en, list_position_reworks):
            return position_personel

        for pos in list_replace_pos:
            if pos in list_staff_vacancy:
                # obj_pos = Positions.objects.filter(guid=pos).first()
                if can_add_position_audit(pos, pos_en, list_position_reworks):
                    return pos

            # max_count_pos = pos_en.get(obj_pos)
            # count_pos = list_position_reworks.count(pos)
            # if max_count_pos > count_pos:
            #     position_personel = obj_pos
            #     break

    return position_personel


@timeover_timeshift
@login_required
def TimeSheet_table_creat_rework(request, enterprise, year, month, day):
    if request.method == 'POST':
        if request.POST['close_table'] == "Сохранить":

            date_f = date(int(request.POST['year']), int(request.POST['month']), int(request.POST['day']))

            pers = Persons.objects.get(guid=request.POST['person_guid_to'])
            pos_pers = StaffHistory.get_last_position(date_f, pers)
            en = Enterprises.objects.get(guid=enterprise)

            pos = get_position_audit_replace(pos_pers, date_f, en)  # подмена должности если ЗУМ или УМ

            # n_record = persons_reworks.objects.filter(dts=date_f, coworker_guid=pers, enterprise_guid=en,
            #                                        position_guid=pos)
            n_record = persons_reworks.objects.filter(dts_audit=date_f, coworker_guid=pers, enterprise_guid=en,
                                                      position_guid=pos)

            date_free_timesheet = persons_reworks.get_date_free_timesheet_fact(date_f, pers)

            if len(n_record) == 0:

                new_obj = persons_reworks.objects.create(
                    guid=str(uuid.uuid4()),
                    dts=date_free_timesheet,
                    coworker_guid=pers,
                    enterprise_guid=en,
                    position_guid=pos,
                    count_hours=11,
                    dts_audit=date_f,
                    is_deleted=0
                )
                persons_reworks_history.save_history(new_obj, request.user.username)
            else:
                messages.success(request, "Данный сотрудник уже есть в табеле")

        return redirect('table-sheet-rework', enterprise=request.POST['enterprise'], year=request.POST['year'],
                        month=request.POST['month'], day=request.POST['day'])
    else:

        profile = ProfileUser.get_profile(ProfileUser, request.user)
        if profile.readly_only:
            return redirect('dashboard')

        date_t_f = date(int(year), int(month), int(day))
        ent = Enterprises.objects.get(guid=enterprise)

        # init_en = Enterprises.get_list_shops(Enterprises)
        init_en = []

        return render(request, 'TimeSheet/work/timesheet_create_rework.html', {'sheet_shop': ent,
                                                                               'dts': date_t_f,
                                                                               'enterprise': enterprise,
                                                                               'init_en': init_en, })


@login_required
def deleted_cowork(request, pk, enterprise, person, year, month, day):
    date_f = date(int(year), int(month), int(day))

    n_record_coworks = persons_coworks.objects.get(guid=pk)
    if n_record_coworks is not None:
        persons_coworks_history.save_history(n_record_coworks, request.user.username, True)
        n_record_coworks.delete()

    return redirect('table-sheet-cowork', enterprise, year, month, day)


@login_required
def deleted_rework(request, enterprise, person, year, month, day):
    date_f = date(int(year), int(month), int(day))

    n_record_coworks = persons_reworks.objects.filter(dts_audit=date_f,
                                                      coworker_guid=person
                                                      )
    if len(n_record_coworks) > 0:
        n_record_coworks.delete()

    return redirect('table-sheet-rework', enterprise, year, month, day)


@login_required
def select_cowork_view(request, enterprise, position, year, month, day, filter_fact=0, p_uid=''):
    date_t_f = date(int(year), int(month), int(day))
    ent = Enterprises.objects.get(guid=enterprise)
    cowork_status = 0
    teached_person = 0
    if p_uid != '' and len(p_uid) == 1:
        cowork_status = int(p_uid)
    elif len(p_uid) > 1:
        cowork_status = 0
        obj_plan = TimeSheetPlane.objects.get(p_uid=p_uid)
        if obj_plan is not None:
            teached_person = Trained_staff.get_sign_teached(obj_plan.person_guid)

    fl_RC = False
    profile = ProfileUser.get_profile(ProfileUser, request.user)
    fl_otiz = 1 if profile.otiz else 0
    if (profile.entreprise is not None and profile.entreprise.enterprise_code == 2) or (
            ent.enterprise_code == 2 and (request.user.is_superuser or fl_otiz)):
        pos_en = list({p[0] for p in
                       TimeSheetPlane.objects.filter(enterprise_guid__guid=enterprise, dts=date_t_f).values_list(
                           'position_guid')})
        fl_RC = True
    elif filter_fact == 0 and p_uid != '1':
        pos_en = PositionsReplacement.get_replace_positions_to(position, cowork_status, -1, fl_otiz, 0)
    else:
        pos_en = PositionsReplacement.get_replace_positions(position, cowork_status, -1, fl_otiz, teached_person)

    if pos_en == []:
        init = []
    else:
        if filter_fact == 0:

            if cowork_status != 1:
                list_busy_cowork = ['5A688F12-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F01-74A8-11E8-80F9-3640B58B95BD',
                                    # '5A688F06-74A8-11E8-80F9-3640B58B95BD',
                                    '738B3878-17E4-11E9-80D0-E41F13C123D6',
                                    '5A688F13-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F03-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F0C-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F0C-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F0B-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F0A-74A8-11E8-80F9-3640B58B95BD',
                                    '5A688F08-74A8-11E8-80F9-3640B58B95BD', ]
                init_main = TimeSheetPlane.objects.filter(reduce(or_, [Q(position_guid=c) for c in pos_en])).filter(
                    enterprise_guid__guid=enterprise, dts=date_t_f, busy_key_guid__guid__in=(list_busy_cowork)).exclude(
                    person_guid='00000000-0000-0000-0000-000000000000').exclude(person_guid__guid__in=list(
                    persons_coworks.objects.values_list('coworker_guid', flat=True).filter(
                        dts=date_t_f, cowork_state=0).exclude(
                        coworker_guid__in=['00000000-0000-0000-0000-000000000000',
                                           '10000000-0000-0000-0000-000000000000']).annotate(
                        total=Count('coworker_guid'))))

                init = []
                for i in init_main:
                    init.append(
                        {'person_guid': i.person_guid, 'position_guid': i.position_guid,
                         'shedule_guid': i.shedule_guid})

            else:
                list_busy_cowork = ['5A688F01-74A8-11E8-80F9-3640B58B95BD',
                                    '738B3875-17E4-11E9-80D0-E41F13C123D6', ]
                init_main = TimeSheetFact.objects.filter(p_uid__position_guid__in=pos_en,
                                                         p_uid__enterprise_guid__guid=enterprise, p_uid__dts=date_t_f,
                                                         busy_key_fact__guid__in=list_busy_cowork).exclude(
                    p_uid__person_guid='00000000-0000-0000-0000-000000000000')

                init = []
                for i in init_main:
                    init.append(
                        {'person_guid': i.p_uid.person_guid, 'position_guid': i.p_uid.position_guid,
                         'shedule_guid': i.p_uid.shedule_guid})

                init_cowork_st = persons_coworks.objects.filter(coworker_enterprise_guid__guid=enterprise, dts=date_t_f,
                                                                position_guid__in=pos_en, )
                for i in init_cowork_st:
                    init.append(
                        {'person_guid': i.coworker_guid, 'position_guid': i.position_guid,
                         'shedule_guid': i.shedule_guid})

            teached_person_all = [i.person_guid for i in Trained_staff.objects.all()]
            teached_person_ent = TimeSheetPlane.objects.filter(enterprise_guid__guid=enterprise, dts=date_t_f,
                                                               busy_key_guid__guid__in=(
                                                                   '5A688F12-74A8-11E8-80F9-3640B58B95BD',
                                                                   '5A688F01-74A8-11E8-80F9-3640B58B95BD',
                                                                   '5A688F06-74A8-11E8-80F9-3640B58B95BD',
                                                                   '738B3878-17E4-11E9-80D0-E41F13C123D6',
                                                                   '5A688F13-74A8-11E8-80F9-3640B58B95BD',
                                                                   '5A688F03-74A8-11E8-80F9-3640B58B95BD',
                                                                   '5A688F0C-74A8-11E8-80F9-3640B58B95BD',
                                                                   '5A688F0C-74A8-11E8-80F9-3640B58B95BD'
                                                               ), person_guid__in=teached_person_all)

            for i in teached_person_ent:
                init.append(
                    {'person_guid': i.person_guid, 'position_guid': i.position_guid, 'shedule_guid': i.shedule_guid})

        else:
            n_record_coworks = persons_coworks.objects.filter(dts=date_t_f,
                                                              cowork_state__in=[0, 1])
            list_exclude = [i.foworker_guid for i in n_record_coworks]

            list_f_busy = [
                '738B387C-17E4-11E9-80D0-E41F13C123D6', '5A688F06-74A8-11E8-80F9-3640B58B95BD',
                '738B3878-17E4-11E9-80D0-E41F13C123D6',
                '5A688F13-74A8-11E8-80F9-3640B58B95BD',
                '5A688F03-74A8-11E8-80F9-3640B58B95BD',  # командировка
                '5A688F0C-74A8-11E8-80F9-3640B58B95BD',
                '5A688F0B-74A8-11E8-80F9-3640B58B95BD',
                '5A688F0A-74A8-11E8-80F9-3640B58B95BD',
                '5A688F08-74A8-11E8-80F9-3640B58B95BD',  # учебный
            ]
            # list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6']

            now_shedule = list({sh.shedule_guid.guid for sh in SheduleHours.objects.filter(dts=date_t_f,
                                                                                           busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')})  # рабочие графики тек дня

            init_main = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__dts=date_t_f,
                                                     busy_key_fact__in=list_f_busy,
                                                     p_uid__position_guid__in=pos_en,
                                                     p_uid__shedule_guid__in=now_shedule).exclude(
                p_uid__person_guid__in=list_exclude).exclude(
                p_uid__busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618')

            init = [{'person_guid': i.p_uid.person_guid, 'position_guid': i.p_uid.position_guid,
                     'shedule_guid': i.p_uid.shedule_guid} for i in init_main]

            init_vacancy = TimeSheetPlane.get_vacancy(enterprise=enterprise, date_f=date_t_f, user=request.user)

            if len(init_vacancy) > 0:
                pers_vacancy = Persons.objects.get(guid='00000000-0000-0000-0000-000000000000')
                for i in init_vacancy:
                    v_pos = Positions.objects.get(guid=i[2])
                    if fl_RC or fl_otiz:
                        init.append({'person_guid': pers_vacancy, 'position_guid': v_pos,
                                     'shedule_guid': Shedules.objects.get(guid=i[3])})
                    else:
                        if v_pos in pos_en:
                            init.append({'person_guid': pers_vacancy, 'position_guid': v_pos,
                                         'shedule_guid': Shedules.objects.get(guid=i[3])})

            if fl_RC and fl_otiz:
                pers_vacancy = Persons.objects.get(guid='10000000-0000-0000-0000-000000000000')  # внешние вакансии
                now_position = Positions.objects.get(guid=position)
                shedule_shift = list({sh.shedule_guid for sh in
                                      TimeSheetPlane.objects.filter(enterprise_guid=enterprise, dts=date_t_f,
                                                                    position_guid=position,
                                                                    shedule_guid__in=now_shedule)})
                for sh in shedule_shift:
                    init.append({'person_guid': pers_vacancy, 'position_guid': now_position,
                                 'shedule_guid': sh})

    if fl_otiz == 0 and filter_fact > 0:
        # # Попробуем убрать лишних сотрудников которые в РВ на другом магазине
        # l_person_cowork_today = list(
        #     persons_coworks.objects.values_list('coworker_guid', flat=True).filter(
        #         coworker_guid__in=[i['person_guid'] for i in init],
        #         dts=date_t_f, cowork_state=0).exclude(
        #         coworker_guid__in=['00000000-0000-0000-0000-000000000000',
        #                            '10000000-0000-0000-0000-000000000000']).annotate(total=Count('coworker_guid')))
        #
        # l_index_del = list(
        #     map(lambda i: init.index(i), list(filter(lambda x: x['person_guid'].guid in l_person_cowork_today, init))))
        # for i in l_index_del[::-1]:
        #     init.pop(i)

        # убираем лишние вакаснии)
        active_vacancy = StaffVacancy.check_over_state(ent, date_t_f)
        l_index = []
        for i in init:
            pos = active_vacancy.get(i['position_guid'])
            if pos is not None:
                count_pos = pos.get(i['shedule_guid'])
                if count_pos is None or count_pos <= 0:
                    l_index.append(init.index(i))

        for i in l_index[::-1]:
            init.pop(i)

    if p_uid == '' or p_uid == '0' or p_uid == '1':
        person_guid = '0000'
    else:
        person_guid = TimeSheetPlane.objects.get(p_uid=p_uid).person_guid.guid

    return render(request, 'TimeSheet/test/select_cowork_modal.html', {'sheet_shop': ent,
                                                                       'dts': date_t_f, 'enterprise': enterprise,
                                                                       'init': init,
                                                                       'person': person_guid,
                                                                       'p_uid': p_uid,
                                                                       })


@login_required
def select_rework_view(request, enterprise, year, month, day):
    date_t_f = date(int(year), int(month), int(day))
    ent = Enterprises.objects.get(guid=enterprise)
    pos_en = persons_audit.get_context(persons_audit, enterprise=ent, dts=date_t_f)

    # pers_reworks = persons_reworks.objects.filter(dts=date_t_f, enterprise_guid=ent)
    pers_reworks = persons_reworks.objects.filter(dts_audit=date_t_f, enterprise_guid=ent)

    another_enterprise = -1
    profile = ProfileUser.get_profile(ProfileUser, request.user)
    if profile.entreprise != None and profile.entreprise == ent:
        another_enterprise = 0

    position_not_exclude = []
    list_position_reworks = list(pers_reworks.values_list('position_guid', flat=True))
    for k, v in pos_en.items():
        count_pos = list_position_reworks.count(k.guid)
        if count_pos < v:
            # position_not_exclude.append(k)

            list_pos_replace_to = PositionsReplacement.get_replace_positions_to(k.guid, 2, another_enterprise)
            for i_pos in list_pos_replace_to:
                position_not_exclude.append(i_pos)

    if profile.otiz or ent.enterprise_code == 2:
        init = TimeSheetPlane.objects.filter(enterprise_guid__guid=enterprise, dts=date_t_f)
    else:
        init = TimeSheetPlane.objects.filter(enterprise_guid__guid=enterprise, dts=date_t_f,
                                             # busy_key_guid__guid='5A688F12-74A8-11E8-80F9-3640B58B95BD', сказали выводим всех, а там разбрасываем
                                             # position_guid__in=list(pos_en.keys()))
                                             position_guid__in=position_not_exclude)

    if len(pers_reworks) > 0:
        init = init.exclude(person_guid__in=list((i.coworker_guid for i in pers_reworks)))

    return render(request, 'TimeSheet/work/select_cowork.html', {'sheet_shop': ent,
                                                                 'dts': date_t_f, 'enterprise': enterprise,
                                                                 'init': init, })


@login_required
def TimeSheet_table_print(request, enterprise, year, month):
    init_fact = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__year=year,
                                             p_uid__month=month, p_uid__suspicious=0).exclude(
        p_uid__person_guid='00000000-0000-0000-0000-000000000000').order_by('p_uid__person_guid')

    any_day = date(int(year), int(month), 1)
    ent = Enterprises.objects.get(guid=enterprise)
    today = datetime.today()
    init_cowork = persons_coworks.get_context(any_day, enterprise).filter(cowork_local=0)

    days_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    last_day_month = int(persons_coworks.last_day_of_month(any_day).day) + 1
    dict_moth = {a: days_week[date(int(year), int(month), a).weekday()] for a in range(1, last_day_month)}
    dict_fio = {}
    dict_total_pers = {}

    dict_shedule = {}

    for element in init_fact:
        if dict_fio.get(element.p_uid.person_guid) == None:
            dict_fio[element.p_uid.person_guid] = {}

        if dict_fio[element.p_uid.person_guid].get(element.p_uid.dts.day) == None:
            dict_fio[element.p_uid.person_guid][element.p_uid.dts.day] = list(filter(
                lambda x: x.p_uid.person_guid == element.p_uid.person_guid and x.p_uid.dts.day == element.p_uid.dts.day,
                init_fact))

    for element in init_fact:
        dict_shedule[element.p_uid.person_guid] = PersonShedule.objects.filter(person_guid=element.p_uid.person_guid, begin_date__lte=today).last().shedule_guid

    dict_pos = {el: StaffHistory.get_last_position(date(int(year), int(month), date.today().day), el) for
                el in dict_fio}

    for el in dict_fio:
        dict_busykey = dict_fio[el]
        dict_total = {}
        for i in dict_busykey:
            for l in dict_busykey[i]:
                if dict_total.get(l.busy_key_fact) == None:
                    dict_total[l.busy_key_fact] = 1
                else:
                    dict_total[l.busy_key_fact] = dict_total.get(l.busy_key_fact) + 1
            dict_fio[el][i] = '/'.join(list(map(lambda x: str(x.busy_key_fact), dict_busykey[i])))
        dict_total_pers[el] = dict_total

    dict_day_cowork = list(map(lambda i: {'person': i, 'total_day': len(
        list(filter(lambda t: t.coworker_guid.full_name == i, init_cowork))), 'day_work': [j.dts.day for j in list(
        filter(lambda t: t.coworker_guid.full_name == i, init_cowork))]},
                               sorted(set(map(lambda x: x.coworker_guid.full_name, init_cowork)))))

    # pdf = render_to_pdf('TimeSheet/work/print_form/print_table.html', {'sheet_shop': ent,
    #                                                                       'dts': last_day_month,
    #                                                                       'enterprise': enterprise,
    #                                                                       'dict_fio': dict_fio,
    #                                                                       'dict_pos': dict_pos,
    #                                                                       'dict_moth': dict_moth,
    #                                                                       'dict_total_pers': dict_total_pers,
    #                                                                       'today': today,
    #                                                                       })
    #
    # if pdf:
    #     # response = HttpResponse(pdf, content_type='application/pdf')
    #     response = pdf
    #     filename = "Invoice_%s.pdf" % ("12341231")
    #     content = "inline; filename='%s'" % (filename)
    #     download = request.GET.get("download")
    #     if download:
    #         content = "attachment; filename='%s'" % (filename)
    #     response['Content-Disposition'] = content
    #     return response
    return render(request, 'TimeSheet/work/print_form/print_table.html', {'sheet_shop': ent,
                                                                          'dts': last_day_month,
                                                                          'enterprise': enterprise,
                                                                          'dict_fio': dict_fio,
                                                                          'dict_pos': dict_pos,
                                                                          'dict_moth': dict_moth,
                                                                          'dict_total_pers': dict_total_pers,
                                                                          'today': today,
                                                                          'dict_day_cowork': dict_day_cowork,
                                                                          'dict_shedule':dict_shedule,
                                                                          })


@login_required
def revision_list(request):
    revisor_data = enterprise_revision.objects.all()
    return render(request, 'TimeSheet/work/revisor_list.html', {"data": revisor_data})


@login_required
def revision_edit(request, enterprise, dts):
    if request.method == 'POST':
        if request.POST['close_revision'] == "Сохранить":

            en = Enterprises.objects.get(guid=request.POST['ent_uid'])
            date_f = date(int(request.POST['revision_date'][:4]), int(request.POST['revision_date'][5:7]),
                          int(request.POST['revision_date'][8:10]))

            if request.POST['uid'] == 'None':
                enterprise_revision.objects.create(uid=str(uuid.uuid4()), enterprise_uid=en, revision_date=date_f)
            else:
                n_record = enterprise_revision.objects.get(uid=request.POST['uid'])
                n_record.enterprise_uid = en
                n_record.revision_date = date_f
                n_record.save()

            return redirect('revision-list')
        else:
            return redirect('revision-list')
    else:
        date_f = date(int(dts[:4]), int(dts[5:7]), int(dts[8:10]))
        revisor_data = enterprise_revision.objects.get(enterprise_uid__guid=enterprise, revision_date=date_f)

        record_date_create = enterprise_revision_changes.objects.get(uid=revisor_data.uid, changetype='insert')
        str_date_create = f'Дата создания: {record_date_create.changetime.strftime("%d-%m-%Y %H.%M.%S")}'

        return render(request, 'TimeSheet/work/revision_edit.html', {'enterprise_uid': revisor_data.enterprise_uid,
                                                                     'revision_date': date_f.strftime('%Y-%m-%d'),
                                                                     'uid': revisor_data.uid,
                                                                     'changetime': str_date_create, })


@login_required
def revision_deleted(request, enterprise, dts):
    date_f = date(int(dts[:4]), int(dts[5:7]), int(dts[8:10]))

    list_record = enterprise_revision.objects.filter(enterprise_uid=enterprise, revision_date=date_f)

    for n_record in list_record:
        n_record.delete()

    return redirect('revision-list')


@login_required
def revision_create(request):
    if request.method == 'POST':
        if request.POST['close_revision'] == "Сохранить":

            en = Enterprises.objects.get(guid=request.POST['ent_uid'])
            date_f = date(int(request.POST['revision_date'][:4]), int(request.POST['revision_date'][5:7]),
                          int(request.POST['revision_date'][8:10]))

            n_rec_en = enterprise_revision.objects.filter(enterprise_uid=en, revision_date=date_f).first()

            if n_rec_en is None:
                enterprise_revision.objects.create(uid=str(uuid.uuid4()), enterprise_uid=en, revision_date=date_f)
            else:
                messages.warning(request, f'{en} уже занесен в список ревизий!')
            # else:
            #     n_record = enterprise_revision.objects.get(uid=request.POST['uid'])
            #     n_record.enterprise_uid = en
            #     n_record.revision_date = date_f
            #     n_record.save()

            return redirect('revision-list')
        else:
            return redirect('revision-list')
    else:
        return render(request, 'TimeSheet/work/revision_edit.html', {'enterprise_uid': None,
                                                                     'revision_date': date.today().strftime('%Y-%m-%d'),
                                                                     'uid': None,
                                                                     'changetime': '', })


@login_required
def print_divergence_table(request, dts_begin, dts_end):
    date_f = date(int(dts_begin[:4]), int(dts_begin[5:7]), int(dts_begin[8:10]))
    date_s = date(int(dts_end[:4]), int(dts_end[5:7]), int(dts_end[8:10]))
    init = get_divergence_table(date_f, date_s)

    return render(request, 'TimeSheet/work/print_form/print_divergence_table.html', {'init': init,
                                                                                     'dts_begin': date_f,
                                                                                     'dts_end': date_s,
                                                                                     })


@login_required
def divergence_table(request):

    dts_begin = request.GET.get("dts_begin")
    dts_end = request.GET.get("dts_end")

    if dts_begin is None or dts_end is None:
        begin_date = datetime.today().replace(day=1)
        end_date = persons_reworks.last_day_of_month(begin_date)

        return render(request, 'TimeSheet/work/divergence_table.html', {
            'dts_begin': begin_date.strftime('%Y-%m-%d'),
            'dts_end': end_date.strftime('%Y-%m-%d'),
        })

    date_f = date(int(dts_begin[:4]), int(dts_begin[5:7]), int(dts_begin[8:10]))
    date_s = date(int(dts_end[:4]), int(dts_end[5:7]), int(dts_end[8:10]))
    init = get_divergence_table(date_f, date_s)

    return render(request, 'TimeSheet/work/print_form/print_divergence_table.html', {'init': init,
                                                                                     'dts_begin': date_f,
                                                                                     'dts_end': date_s,
                                                                                     })

@login_required
def select_enterprise(request):
    init = Enterprises.objects.filter(enterprise_code__gt=0).order_by('enterprise_code')
    return render(request, 'TimeSheet/work/select_enterprise.html', {'init': init, })


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_create_date_revision(uid):
    record_date_create = enterprise_revision_changes.objects.get(uid=uid, changetype='insert')
    # return record_date_create.changetime.strftime("%d-%m-%Y %H.%M.%S")
    return record_date_create.changetime.strftime("%Y-%m-%d")


@register.filter
def person_table(dictionary, key):
    return dictionary.get(key)


@register.filter
def person_table_key(key, dictionary):
    set_pers = dictionary.get(key)

    if set_pers == None:
        return False
    else:
        return True


@register.filter
def init_number(num):
    return str(num)


def get_divergence_table(dts_begin, dts_end):
    with connection.cursor() as cursor:
        cursor.execute(
            "exec get_staff_suspect '" + dts_begin.strftime("%Y/%m/%d") + "', '" + dts_end.strftime("%Y/%m/%d") + "'")
        setobj = cursor.fetchall()
        new_list = []

        for i in setobj:
            list_str = []
            list_str.append(i[0])
            list_str.append(Enterprises.objects.get(guid=i[1]))
            list_str.append(Positions.objects.get(guid=i[2]))
            list_str.append(Shedules.objects.get(guid=i[3]))
            list_str.append(Persons.objects.get(guid=i[4]))
            list_str.append(BusyKeys.objects.get(guid=i[5]))
            list_str.append(BusyKeys.objects.get(guid=i[6]))
            list_str.append(i[10])
            list_str.append(i[11])

            new_list.append(list_str)

        return new_list


def get_time_worked(dts_begin, dts_end):
    return "true"


def test_call(request):
    return HttpResponse(request.POST['text'])


@timeover_timeshift
@login_required
def record_sheet(request):
    p_uid = TimeSheetPlane.objects.get(p_uid=request.POST['p_uid'])
    if request.POST['f_busy'] == 'selected' or request.POST['f_busy'] == '':
        f_busy = None
    else:
        f_busy = BusyKeys.objects.get(guid=request.POST['f_busy'])

    f_amount = request.POST['f_amount']

    busy_key_rv = BusyKeys.objects.get(guid='738B3875-17E4-11E9-80D0-E41F13C123D6')

    f_model = TimeSheetFact.objects.filter(p_uid=p_uid.p_uid).first()

    if f_model is None and f_busy is not None:
        TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                     busy_key_fact=f_busy,
                                     amount=f_amount,
                                     p_uid=p_uid,
                                     record_fixed=1)
    elif f_busy is None:
        if f_model is not None:
            # f_model.delete()
            TimeSheetFact.objects.filter(p_uid=p_uid.p_uid).delete()

    if f_model is not None:
        del_persons_coworks = None
        if f_model.busy_key_fact == busy_key_rv and busy_key_rv != f_busy:  # удалим РВ если оно есть
            del_persons_coworks = persons_coworks.objects.filter(dts=p_uid.dts,
                                                                 coworker_guid=p_uid.person_guid,
                                                                 # coworker_enterprise_guid=p_uid.enterprise_guid,
                                                                 # shedule_guid=p_uid.shedule_guid,
                                                                 cowork_state__in=[0, 1],
                                                                 cowork_local=1).first()

        if del_persons_coworks is not None:
            rv_cowork = persons_coworks.objects.filter(dts=p_uid.dts,
                                                       coworker_guid=p_uid.person_guid,
                                                       cowork_state__in=[0, 1],
                                                       cowork_local=1)
            for i in rv_cowork:
                persons_coworks_history.save_history(i, request.user.username, True)
            rv_cowork.delete()

    #     проверим вышел кто за него
    rv_fowork = persons_coworks.objects.filter(dts=p_uid.dts,
                                               foworker_guid=p_uid.person_guid,
                                               cowork_state__in=[0, 1],
                                               cowork_local=1)
    if len(rv_fowork) > 0:
        for i in rv_fowork:
            TimeSheetFact.objects.filter(p_uid__dts=p_uid.dts,
                                         busy_key_fact=busy_key_rv,
                                         p_uid__person_guid=i.coworker_guid).delete()

            persons_coworks_history.save_history(i, request.user.username, True)
        rv_fowork.delete()

    if f_busy is not None and f_model is not None:
        f_model.busy_key_fact = f_busy
        f_model.amount = f_amount
        f_model.p_uid = p_uid
        f_model.record_fixed = 1
        f_model.save()

    # посмотрим, может ест Н часы
    busy_key_N = BusyKeys.objects.get(guid='E1916359-15C4-11E9-8112-00155D6DE618')
    plan_model = TimeSheetPlane.objects.filter(dts=p_uid.dts, person_guid=p_uid.person_guid,
                                               busy_key_guid=busy_key_N).first()

    if plan_model is not None:

        if p_uid.busy_key_guid == f_busy:
            f_busy = busy_key_N
            f_amount = plan_model.hours_all
        else:
            f_busy = f_busy
            f_amount = 0

        f_model_N = TimeSheetFact.objects.filter(p_uid=plan_model.p_uid).first()
        if f_model_N is None:
            TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                         busy_key_fact=f_busy,
                                         amount=f_amount,
                                         p_uid=plan_model,
                                         record_fixed=1)
        else:

            f_model_N.busy_key_fact = f_busy
            f_model_N.amount = f_amount
            f_model_N.p_uid = plan_model
            f_model_N.record_fixed = 1
            f_model_N.save()

    return HttpResponse('True')


@timeover_timeshift
@login_required
def record_sheet_rv(request):
    pers = Persons.objects.get(guid=request.POST['pers'])
    shedule_guid = Shedules.objects.get(guid=request.POST['shedule'])
    date_f = request.POST['dts']
    enterprise = Enterprises.objects.get(guid=request.POST['enterprise'])
    position = Positions.objects.get(guid=request.POST['position'])
    pers_first = Persons.objects.get(guid=request.POST['pers_first'])

    qSet = SheduleHours.objects.filter(dts__lte=date_f, shedule_guid=shedule_guid,
                                       busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD').order_by("-dts").first()
    count_hours = 0
    if qSet is not None:
        count_hours = qSet.hours_full if qSet.hours_full != 0 else qSet.hours_lite

    c_model = persons_coworks.objects.filter(dts=date_f,
                                             coworker_guid=pers_first,
                                             cowork_state=0).first()

    if c_model is None:
        new_obj = persons_coworks.objects.create(
            guid=str(uuid.uuid4()),
            dts=date_f,
            coworker_guid=pers_first,
            foworker_guid=pers,
            coworker_enterprise_guid=enterprise,
            enterprise_guid=enterprise,
            shedule_guid=shedule_guid,
            position_guid=position,
            count_hours=count_hours,
            cowork_state=0,
            cowork_local=1,
            record_fixed=1)
        persons_coworks_history.save_history(new_obj, request.user.username)
    else:
        c_model.foworker_guid = pers
        c_model.coworker_enterprise_guid = enterprise
        c_model.enterprise_guid = enterprise
        c_model.shedule_guid = shedule_guid
        c_model.position_guid = position
        c_model.count_hours = count_hours
        c_model.cowork_local = 1
        c_model.record_fixed = 1
        c_model.save()

    p_uid = TimeSheetPlane.objects.get(p_uid=request.POST['p_uid'])
    f_busy = BusyKeys.objects.get(guid='738B3875-17E4-11E9-80D0-E41F13C123D6')

    f_model = TimeSheetFact.objects.filter(p_uid=p_uid.p_uid).first()

    if f_model == None:
        TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                     busy_key_fact=f_busy,
                                     amount=count_hours,
                                     p_uid=p_uid,
                                     record_fixed=1)
    else:
        f_model.busy_key_fact = f_busy
        f_model.amount = count_hours
        f_model.p_uid = p_uid
        f_model.record_fixed = 1
        f_model.save()

    return HttpResponse(count_hours)


@login_required
def fill_table(request):
    date_f = request.POST['dts']
    enterprise = Enterprises.objects.get(guid=request.POST['enterprise'])

    with connection.cursor() as cursor:
        cursor.execute(
            "exec fill_division_plan_by_fact '" + enterprise.guid + "', '" + date_f + "', 1")

        cursor.execute(
            "exec fill_division_plan_by_fact '" + enterprise.guid + "', '" + date_f + "', 2")

    return HttpResponse('True')


@login_required
def messages_over(request):
    messages.success(request, request.POST['messages'])

    return HttpResponse('True')


@login_required
def edit_remove_person(request, person, enterprise):
    if request.method == 'POST':
        today_r = datetime.today()
        if request.POST['close_table'] == "Сохранить":
            return redirect('table-sheet', enterprise=enterprise, year=today_r.year,
                            month=today_r.month)
        elif request.POST['close_table'] == "Закрыть":
            messages.info(request, "Табель не записан!")

            return redirect('table-sheet', enterprise=enterprise, year=today_r.year,
                            month=today_r.month)

        return HttpResponse('True')
    else:
        init = TimeSheetPlane.objects.filter(dts__gt=datetime.today(), person_guid=person)
        init2 = TimeSheetFact.objects.filter(p_uid__person_guid=person, p_uid__dts__gt=datetime.today())
        tag_fact = TimeSheetFact.get_fact_detail(init, init2)

        person_obj = Persons.objects.get(guid=person)
        return render(request, 'TimeSheet/test/table_detail_person.html', {'init': init,
                                                                           'person': person_obj,
                                                                           'position': init[0].position_guid,
                                                                           'tag_fact': tag_fact})


@login_required
def print_hours_worked(request):
    print_form = []
    dts_begin = request.GET.get('dts_begin')
    dts_end = request.GET.get('dts_end')
    enterprise_guid = request.GET.get('enterprise_guid')
    personal_guid = request.GET.get('pers_guid')

    if dts_begin is None and dts_end is None and enterprise_guid is None:
        return render(request, 'TimeSheet/work/print_form/print_hours_worked.html', {'init': print_form,
                                                                                     })
    all_person = {i.guid: i.full_name for i in Persons.objects.all()}

    enterprise_guid = None if enterprise_guid == '' else enterprise_guid
    personal_guid = None if personal_guid == '' else personal_guid

    with connection.cursor() as cursor:
        cursor.execute(
            "exec get_staff_work_report %s, %s, %s, %s", [dts_begin, dts_end, enterprise_guid, personal_guid])

        setobj = cursor.fetchall()
        new_list = []

        for i in setobj:
            # dict = {'person_guid': Persons.objects.get(guid=i[1]),
            dict = {'person_guid': all_person.get(i[1]),
                    'plan_amt_count': i[2],
                    'plan_amt_hours': i[5],
                    'fact_amt_count': i[3],
                    'fact_amt_hours': i[6],
                    'cowr_amt_count': i[4],
                    'cowr_amt_hours': i[7],
                    'total_hours': i[9]}

            new_list.append(dict)
    print(datetime.now())
    return render(request, 'TimeSheet/part_form/part_print_hours_worked.html', {'init': new_list,
                                                                                'dts_begin': dts_begin,
                                                                                'dts_end': dts_end,
                                                                                'enterprise_guid': enterprise_guid})


@login_required
def print_hours_worked_ex(request):
    print_form = []
    dts_begin = request.GET.get('dts_begin')
    dts_end = request.GET.get('dts_end')
    enterprise_guid = request.GET.get('enterprise_guid')
    personal_guid = request.GET.get('pers_guid')

    if dts_begin is None and dts_end is None and enterprise_guid is None:
        return render(request, 'TimeSheet/work/print_form/print_hours_worked_ex.html', {'init': print_form,
                                                                                        })

    enterprise_guid = None if enterprise_guid == '' else enterprise_guid
    personal_guid = None if personal_guid == '' else personal_guid

    if personal_guid:
        obj_person = Persons.objects.get(guid=personal_guid)
        all_person = {obj_person.guid: obj_person.full_name}
        all_person['00000000-0000-0000-0000-000000000000'] = '(Вакансия)'
    else:
        all_person = {i.guid: i.full_name for i in Persons.objects.all()}

    all_ent = {i.guid: i.name for i in Enterprises.objects.all()}
    all_position = {i.guid: i.full_name for i in Positions.objects.all()}

    with connection.cursor() as cursor:
        cursor.execute(
            "exec get_staff_work_report_ex %s, %s, %s, %s", [dts_begin, dts_end, enterprise_guid, personal_guid])

        setobj = cursor.fetchall()
        new_list = []

        for i in setobj:
            pers = all_person.get(i[0])
            ent = all_ent.get(i[1])
            pos = all_position.get(i[2])
            days_cnt = i[5]
            cw_data = i[6]

            dict_detail = {
                'person_guid': pers,
                'enterprise': ent,
                'position': pos,
                'days_cnt': days_cnt,
                'cw_data': cw_data,
            }

            element = list(filter(lambda item: item['person_guid'] == pers, new_list))

            if len(element) == 0:
                new_list.append({'person_guid': pers,
                                 'enterprise': ent,
                                 'position': pos,
                                 'days_cnt': days_cnt,
                                 'detail': [dict_detail]})
            else:
                element[0]['days_cnt'] += days_cnt
                element[0]['detail'].append(dict_detail)

    return render(request, 'TimeSheet/part_form/part_print_hours_worked_ex.html',
                  {'init': sorted(new_list, key=lambda x: x['person_guid']),
                   'dts_begin': dts_begin,
                   'dts_end': dts_end,
                   'enterprise_guid': enterprise_guid})


@login_required
def print_cowork_noshows(request):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("exec report_busykeys_deviation %s, %s",
                           [request.POST['dts_begin'], request.POST['dts_end']])
            setobj = cursor.fetchall()
            new_list = []

            for i in setobj:
                dict = {'person_name': i[2],
                        'dts': i[0],
                        'e1n': i[8],
                        'bk1n': i[3],
                        'e2n': i[10],
                        'bk2n': i[5],
                        'service_note': i[11]}

                new_list.append(dict)

        return render(request, 'TimeSheet/work/print_form/print_cowork_no-shows.html', {'init': new_list,
                                                                                        'dts_begin': request.POST[
                                                                                            'dts_begin'],
                                                                                        'dts_end': request.POST[
                                                                                            'dts_end'],
                                                                                        })
    else:
        print_form = []
        return render(request, 'TimeSheet/work/print_form/print_cowork_no-shows.html', {'init': print_form,
                                                                                        })


@login_required
def info_history_table_personel(request, enterprise, year, month, personal):
    if request.method == 'POST':
        pass
    else:

        en = Enterprises.objects.get(guid=enterprise)
        en_pers = Persons.objects.get(guid=personal)

        s_date = date(int(year), int(month), 1)
        qset = shift_data_f_history.get_history(personal, enterprise, s_date)

        return render(request, 'TimeSheet/work/version_timesheet.html', {'sheet_shop': en,
                                                                         'dts': s_date,
                                                                         'en_person': en_pers,
                                                                         'init': qset,
                                                                         })


@login_required
def info_history_table_cowork(request, enterprise, year, month):
    if request.method == 'POST':
        pass
    else:

        en = Enterprises.objects.get(guid=enterprise)

        s_date = date(int(year), int(month), 1)
        qset = persons_coworks_history.get_history(enterprise, s_date)

        return render(request, 'TimeSheet/work/version_timesheet_cowork.html', {'sheet_shop': en,
                                                                                'dts': s_date,
                                                                                'init': qset,
                                                                                })


@login_required
def filter_table_list(request):
    if request.method == 'POST':
        if request.POST['close_filter'] == "OK":

            set_filter = setting_filter.objects.filter(user_id=request.user.id).first()
            if set_filter != None:
                set_filter.delete()

            if request.POST['person_guid_to'] != '' or request.POST['enterprise_guid'] != '':
                personel = '00000000-0000-0000-0000-000000000000' if request.POST['person_guid_to'] == '' else \
                    request.POST['person_guid_to']
                enterprise = '00000000-0000-0000-0000-000000000000' if request.POST['enterprise_guid'] == '' else \
                    request.POST['enterprise_guid']
                dts = datetime(1, 1, 1)

                setting_filter.objects.create(user_id=request.user.id,
                                              persons=personel,
                                              enterprise=enterprise,
                                              dts=dts)

        return HttpResponse(True)
    else:

        set_filter = setting_filter.objects.filter(user_id=request.user.id).first()

        if set_filter == None:
            enterptise = '--Подразделение--'
            person = '--Выберите сотрудника--'
        else:
            # empty_date = datetime.date(1, 1, 1)
            enterptise = '--Подразделение--' if set_filter.enterprise == '00000000-0000-0000-0000-000000000000' else Enterprises.objects.get(
                guid=set_filter.enterprise)
            person = '--Выберите сотрудника--' if set_filter.persons == '00000000-0000-0000-0000-000000000000' else Persons.objects.get(
                guid=set_filter.persons)
            # m = '----' if set_filter.dts == empty_date else set_filter.dts.mont

        return render(request, 'TimeSheet/work/filter.html', {'ent': enterptise,
                                                              'pers': person,
                                                              })


@login_required
def select_all_persons(request):
    init = Persons.objects.filter(marked=0, archived=0)

    return render(request, 'TimeSheet/work/select_all_personsk.html', {'init': init, })


@register.filter
def chect_user(user):
    if user == None:
        return False

    profile = ProfileUser.get_profile(ProfileUser, user)
    if profile.entreprise != None:
        return False
    else:
        return True


def get_local_ip_client(request):
    return request.META['REMOTE_ADDR']


def get_user_ip(ip_adress):
    
    profil_user = ProfileUser.objects.filter(ip_shop=ip_adress).first()
    if profil_user != None:
        return profil_user.user

    part_ip = '.'.join(str(ip_adress).split('.')[0:3]) + '.'
    profil_user = ProfileUser.objects.filter(ip_shop__contains=part_ip).first()

    if profil_user != None:
        return profil_user.user
    else:
        return None


def ajax_login_user(request):
    ip_adress = get_local_ip_client(request)

    to_user = get_user_ip(ip_adress)
    if to_user is not None:
        login(request, to_user)
        # return redirect('table-list')
        return HttpResponse('true')

    return HttpResponse('false')


@register.filter
def this_around_the_clock(guid_sheduler, dts):
    obj_sh = Shedules.objects.get(guid=guid_sheduler)

    return obj_sh.sheduler_round_the_clock(dts)


@register.filter
def get_sts_ShCh(shift_Check_f):
    last_status = shift_Check_f.get_last_record_status()
    return last_status.status_id if last_status is not None else 'Error'


@login_required
def record_service_note(request):
    record_model = persons_coworks.objects.get(guid=request.POST['guid'])
    record_model.service_note = 1 if record_model.service_note == 0 else 0
    record_model.save()

    return HttpResponse('true')


def diff_list_dict(diff1, diff2, diff=[]):
    del_diff1 = []
    for l in range(len(diff1)):
        diff1_keys = list(diff1[l].keys())
        for k in diff1_keys:
            del_diff2 = []
            for s in range(len(diff2)):
                diff2_val = diff2[s].get(k)
                diff1_val = diff1[l].get(k)
                if diff2_val is None:
                    continue

                tm_diff = diff1_val - diff2_val
                # diff2[s].pop(k)
                del_diff2.append(s)
                del_diff1.append(l)
                diff.append({k: tm_diff})

            for i in del_diff2[::-1]:
                diff2.pop(i)

    for i in del_diff1[::-1]:
        diff1.pop(i)


def print_route_sheets(request):
    dts_begin = request.GET.get('dts_begin')
    dts_end = request.GET.get('dts_end')
    enterprise_guid = request.GET.get('enterprise_guid')
    personal_guid = request.GET.get('pers_guid')
    if dts_begin is None or dts_end is None:
        return render(request, 'TimeSheet/work/print_form/print_route_sheets.html', )

    dts_begin = date(int(dts_begin[:4]), int(dts_begin[5:7]), int(dts_begin[8:10]))
    dts_end = date(int(dts_end[:4]), int(dts_end[5:7]), int(dts_end[8:10]))

    delta_date = dts_end - dts_begin

    rangedate = [dts_begin + timedelta(i) for i in range(delta_date.days + 1)]
    init_plane = TimeSheetPlane.objects.filter(dts__gte=dts_begin, dts__lte=dts_end, suspicious=0, record_type=2)

    enterprise_guid = None if enterprise_guid == '' else enterprise_guid
    personal_guid = None if personal_guid == '' else personal_guid

    if personal_guid:
        init_plane = init_plane.filter(person_guid=personal_guid)

    if enterprise_guid:
        init_plane = init_plane.filter(enterprise_guid=enterprise_guid)

    init_fact = TimeSheetFact.objects.filter(p_uid__p_uid__in=[i.p_uid for i in init_plane])

    init = list(map(lambda y: {'person_guid': y['person_guid'], 'data': list(map(lambda c: {'enterprise': c,
                                                                                            'list_date': list(
                                                                                                map(lambda j: {
                                                                                                    'dts': j.dts,
                                                                                                    'bk': j.busy_key_guid,
                                                                                                    'position': j.position_guid},
                                                                                                    list(filter(lambda
                                                                                                                    t: t.person_guid ==
                                                                                                                       y[
                                                                                                                           'person_guid'] and t.enterprise_guid == c,
                                                                                                                init_plane)))),
                                                                                            'list_date_f': list(
                                                                                                map(lambda j: {
                                                                                                    'dts': j.p_uid.dts,
                                                                                                    'bk': j.busy_key_fact
                                                                                                },
                                                                                                    list(filter(lambda
                                                                                                                    t: t.p_uid.person_guid ==
                                                                                                                       y[
                                                                                                                           'person_guid'] and t.p_uid.enterprise_guid == c,
                                                                                                                init_fact))))

                                                                                            },
                                                                                 list(y['enterprise'])))}, list(
        map(lambda i: {'person_guid': i, 'enterprise': set(
            map(lambda j: j.enterprise_guid, list(filter(lambda t: t.person_guid == i, init_plane))))},
            set(map(lambda x: x.person_guid, init_plane))))))

    for i in init:
        for j in i['data']:
            total_p = list({i.short_name: len(list(filter(lambda x: x['bk'] == i, j['list_date'])))} for i in
                           set(map(lambda x: x['bk'], j['list_date'])))
            total_f = list({i.short_name: len(list(filter(lambda x: x['bk'] == i, j['list_date_f'])))} for i in
                           set(map(lambda x: x['bk'], j['list_date_f'])))
            j['total_p'] = ', '.join(map(str, total_p))
            j['total_f'] = ', '.join(map(str, total_f))

            diff1 = list(filter(lambda x: x not in total_f, total_p))
            diff2 = list(filter(lambda x: x not in total_p, total_f))

            diff = []
            diff_list_dict(diff1, diff2, diff)
            diff_list_dict(diff2, diff1, diff)

            j['total_diff'] = ', '.join(map(str, diff + diff2 + diff1))
            # diff = []
            # for d in diff1:
            #     for d2 in diff2:
            #         if d.Я

    return render(request, 'TimeSheet/part_form/part_print_route_sheets.html',
                  {'init': init,
                   'dts_begin': dts_begin,
                   'dts_end': dts_end,
                   'rangedate': rangedate,
                   })


class Shift_data_f_checksListView(ListView):
    model = Shift_data_f_checks
    template_name = 'TimeSheet/work/shift_data_f_checks/shift_data_f_checksListView.html'
    context_object_name = 'shift_checks'

    def get_queryset(self):
        user = self.request.user
        profileuser = user.profileuser
        ent = profileuser.entreprise

        st_id_filter = self.request.GET.get('status_id')
        if not st_id_filter is None:
            self.template_name = 'TimeSheet/part_form/part_shift_data_f.html'

        if ent is None:
            # return self.model.get_shift_data_f_shecks()
            if profileuser.otiz or user.is_superuser:
                if st_id_filter is None:
                    return self.model.objects.all()
                else:
                    return self.model.objects.filter(uid__in=[i['data_f_check_uid'] for i in list(
                        Shift_data_f_checks_statuses.objects.values('data_f_check_uid').annotate(max_dts=Max('dts'),
                                                                                                 status=Max(
                                                                                                     'status_id__id')).filter(
                            status=int(st_id_filter)))])
            if profileuser.sb:
                if st_id_filter is None:
                    list_st = list(Check_names.objects.only('id').filter(belong_to__in=['sb', 'sb/otiz']))
                else:
                    list_st = list(Check_names.objects.only('id').filter(id=int(st_id_filter)))
                list_ch_st = [i.data_f_check_uid.uid for i in
                              Shift_data_f_checks_statuses.objects.filter(status_id__in=list_st)]
                return self.model.objects.filter(uid__in=list_ch_st)

        else:
            # return self.model.get_shift_data_f_shecks(ent.guid)
            return self.model.objects.filter(enterprise=ent)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(Shift_data_f_checksListView, self).get_context_data(**kwargs)
        context['title'] = 'Корретировки табеля'

        user = self.request.user
        profileuser = user.profileuser
        ent = profileuser.entreprise
        list_status = []
        if ent is None:
            if profileuser.otiz or user.is_superuser:
                list_status = list(Check_names.objects.all())
            elif profileuser.sb:
                list_status = list(Check_names.objects.filter(belong_to__contains='sb'))

        context['list_status'] = list_status

        return context

    # def get(self, request, *args, **kwargs):
    #     return super(Shift_data_f_checksListView, self).get(request, *args, **kwargs)


class Shift_data_f_checksUpdateView(UpdateView):
    model = Shift_data_f_checks
    template_name = 'TimeSheet/work/shift_data_f_checks/shift_data_f_checksUpdateView.html'
    # form_class = ShiftDataChecksForm
    fields = '__all__'
    success_url = reverse_lazy('shift_data_f_checks')
    context_object_name = 'edit_sheet'

    def get_object(self, queryset=None):
        return get_object_or_404(Shift_data_f_checks, uid=self.kwargs.get('pk'))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(Shift_data_f_checksUpdateView, self).get_context_data(**kwargs)
        context['title'] = 'Корректировка табеля'

        if context['edit_sheet'].type == 0:
            context['link_obj'] = TimeSheetFact.objects.get(uid=context['edit_sheet'].link_uid)
        else:
            pass

        all_status = self.object.get_all_record_status()

        # now_status = self.object.get_last_record_status()
        now_status = all_status.last()
        context['now_status'] = {'comment': "", 'status_id': ''} if now_status is None else now_status
        context['all_status'] = list(all_status)
        context['list_checks_name_next'] = [] if now_status is None else now_status.status_id.get_next_statuses()
        return context

    def post(self, request, *args, **kwargs):

        obj = self.get_object()
        last_status = obj.get_last_record_status()

        if not last_status.status_id.finished:
            new_status = Check_names.objects.get(id=int(request.POST.get('status_check')))
            new_comment = request.POST.get('matcher_note')
            if last_status is not None and last_status.status_id != new_status:
                Shift_data_f_checks_statuses.objects.create(
                    uid=str(uuid.uuid4()),
                    data_f_check_uid=obj,
                    dts=datetime.now(),
                    status_id=new_status,
                    comment=new_comment
                )

                if new_status.finished == 1 and new_status.result == 1:
                    if obj.type == 0:
                        record_tf = TimeSheetFact.objects.get(uid=obj.link_uid)
                        if obj.busy_key_t == '738B3875-17E4-11E9-80D0-E41F13C123D6':
                            new_obj = persons_coworks.objects.create(
                                guid=str(uuid.uuid4()),
                                dts=record_tf.dts,
                                coworker_guid=record_tf.p_uid.person_guid,
                                foworker_guid=obj.foworker_guid,
                                coworker_enterprise_guid=record_tf.p_uid.enterprise_guid,
                                enterprise_guid=record_tf.p_uid.enterprise_guid,
                                shedule_guid=obj.shedule_guid,
                                position_guid=obj.position_guid,
                                count_hours=obj.amount,
                                cowork_state=0,
                                cowork_local=1,
                                record_fixed=1)
                            persons_coworks_history.save_history(new_obj, request.user.username)
                        elif record_tf.busy_key_fact == '738B3875-17E4-11E9-80D0-E41F13C123D6':
                            record_rv = persons_coworks.objects.filter(dts=record_tf.dts,
                                                                       coworker_guid=obj.record_tf.person_guid,
                                                                       cowork_state=0,
                                                                       cowork_local=1)
                            record_rv.is_deleted = True
                            record_rv.save()

                        record_tf.busy_key_fact = obj.busy_key_t
                        record_tf.amount = obj.amount
                        record_tf.record_fixed = 1
                        record_tf.save()
                        record_tf.save_history(request.user.username, record_tf.uid)
                messages.success(request, f'Статус документа обновлен: {new_status}')
            else:
                messages.error(request, f'НЕ обновлен статус документа, его нет или совпадает')
        else:
            messages.error(request, f'НЕ обновлен статус документа, документ закрыт')

        return redirect('shift_data_f_checks')


class EditTimeSheetPersonalList(ListView):
    # model = TimeSheetFact
    template_name = 'TimeSheet/work/shift_data_f_checks/edit_time_sheet_personal_List.html'
    context_object_name = 'edit_sheet'

    def get_queryset(self):
        data_coworks = persons_coworks.objects.filter(coworker_guid=self.kwargs.get('pers'),
                                                      dts__month=self.kwargs.get('month'),
                                                      dts__year=self.kwargs.get('year'),
                                                      cowork_local=0,
                                                      is_deleted=0).order_by('dts')

        data_reworks = persons_reworks.objects.filter(coworker_guid=self.kwargs.get('pers'),
                                                      dts__month=self.kwargs.get('month'),
                                                      dts__year=self.kwargs.get('year'),
                                                      is_deleted=0).order_by('dts')

        data_timesheet = TimeSheetFact.objects.filter(p_uid__person_guid=self.kwargs.get('pers'),
                                                      p_uid__enterprise_guid=self.kwargs.get('ent'),
                                                      p_uid__year=self.kwargs.get('year'),
                                                      p_uid__month=self.kwargs.get('month'),
                                                      p_uid__suspicious=0).order_by('p_uid__dts')

        return {'data_coworks': data_coworks,
                'data_reworks': data_reworks,
                'data_timesheet': data_timesheet}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(EditTimeSheetPersonalList, self).get_context_data(**kwargs)
        context['title'] = 'Доступные даты корректировки'
        # context['list_shift'] = Shift_data_f_checks.objects.filter(shift_data_f_uid__p_uid__enterprise_guid=self.kwargs.get('ent'))
        return context


class EditTimeSheetPersonalCreate(CreateView):
    model = Shift_data_f_checks
    # form_class = ShiftDataChecksForm
    template_name = 'TimeSheet/work/shift_data_f_checks/edit_time_sheet_personal_Create.html'
    fields = '__all__'
    context_object_name = 'edit_sheet'

    # success_url = reverse_lazy('table-sheet')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(EditTimeSheetPersonalCreate, self).get_context_data(**kwargs)
        context['title'] = 'Заявка на корректировку'

        if self.kwargs.get('state') == 0:
            context['time_sheet_fact'] = TimeSheetFact.objects.get(p_uid=self.kwargs.get('p_uid'))
            context['list_busy_key'] = BusyKeysReplacement.get_busy_key_replace(
                context['time_sheet_fact'].p_uid.busy_key_guid)
        elif self.kwargs.get('state') == 1:
            context['time_sheet_fact'] = persons_coworks.objects.get(guid=self.kwargs.get('p_uid'))
        else:
            context['time_sheet_fact'] = persons_reworks.objects.get(guid=self.kwargs.get('p_uid'))

        context['state'] = self.kwargs.get('state')
        if self.kwargs.get('state') == 2:
            context['pos'] = PositionsReplacement.objects.filter(replacement_type=2)

        return context

    def post(self, request, *args, **kwargs):

        type_state = self.kwargs.get('state')
        check_name_st = Check_names.objects.get(id=0)
        position_guid = Positions.get_empty_position()
        shedule_guid = Shedules.get_empty_shedule()
        foworker_guid = Persons.get_empty_person()

        user = self.request.user
        profileuser = user.profileuser
        ent = profileuser.entreprise

        timesheet_fact = None

        if type_state == 0:
            timesheet_fact = TimeSheetFact.objects.get(p_uid=self.kwargs.get('p_uid'))
            timesheet_plan = timesheet_fact.p_uid

            link_uid = timesheet_fact.uid

            position_guid = request.POST['position']
            shedule_guid = request.POST['shedule']
            foworker_guid = request.POST['foworker']

            qSet = SheduleHours.objects.filter(dts=timesheet_plan.dts, shedule_guid=shedule_guid,
                                               busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')
            count_hours = qSet[0].hours_lite if len(qSet) != 0 else 0

        uid_record_checks = str(uuid.uuid4())

        if ent is None and timesheet_fact is not None:
            ent = timesheet_fact.p_uid.enterprise_guid

        obj_record = Shift_data_f_checks.objects.create(
            uid=uid_record_checks,
            link_uid=link_uid,
            position_guid=Positions.objects.get(guid=position_guid),
            shedule_guid=Shedules.objects.get(guid=shedule_guid),
            foworker_guid=Persons.objects.get(guid=foworker_guid),
            dd=datetime.now(),
            dt=datetime.now(),
            busy_key_f=timesheet_fact.busy_key_fact,
            busy_key_t=BusyKeys.objects.get(guid=request.POST['list_busy_key']),
            amount=count_hours,
            type=type_state,
            enterprise=ent,
            number_doc=Shift_data_f_checks.get_number()
        )

        Shift_data_f_checks_statuses.objects.create(
            uid=str(uuid.uuid4()),
            data_f_check_uid=obj_record,
            dts=datetime.now(),
            status_id=check_name_st,
            comment=request.POST['comment']
        )

        # return redirect('edit_time_sheet_personal_List', pers=timesheet_plan.person_guid.guid,
        #                     ent=timesheet_plan.enterprise_guid.guid, year=timesheet_plan.year, month=timesheet_plan.month)

        messages.success(request, f'Создан документ: {obj_record}')

        return redirect('table-sheet', enterprise=timesheet_plan.enterprise_guid.guid, year=timesheet_plan.year,
                        month=timesheet_plan.month)


class Trained_staff_ListView(ListView):
    model = Trained_staff
    template_name = 'TimeSheet/work/trained_staff/trained_staffListView.html'
    context_object_name = 'trained_staff'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(Trained_staff_ListView, self).get_context_data(**kwargs)
        context['title'] = 'Обученные сотрудники'
        return context


class Trained_staff_EditView(UpdateView):
    model = Trained_staff
    template_name = 'TimeSheet/work/trained_staff/trained_staffUpdateCreateView.html'
    context_object_name = 'trained_staff'

    def get_object(self, queryset=None):
        return get_object_or_404(Trained_staff_EditView, uid=self.kwargs.get('guid'))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(Trained_staff_EditView, self).get_context_data(**kwargs)
        context['title'] = 'Редактирование'
        return context

    def post(self, request, *args, **kwargs):
        person_guid = self.kwargs.get('person_guid')
        position_guid = self.kwargs.get('position_guid')

        self.object = get_object_or_404(Trained_staff_EditView, uid=self.kwargs.get('guid'))
        self.object.person_guid = person_guid
        self.object.position_guid = position_guid
        self.object.save()


class Trained_staff_CreateView(CreateView):
    model = Trained_staff
    template_name = 'TimeSheet/work/trained_staff/trained_staffUpdateCreateView.html'
    fields = "__all__"
    context_object_name = 'trained_staff'
    success_url = reverse_lazy('list_trained_staff')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(Trained_staff_CreateView, self).get_context_data(**kwargs)
        context['title'] = 'Создание'
        list_position = ['28643AE3-FADD-11E0-B937-74EA3A956901',
                         'CD9EE5FF-AA16-11EA-80D8-4C5262022228']  # пока должности ЗУМ,ТВ
        context['init_pos'] = Positions.objects.filter(guid__in=list_position)
        return context

    def post(self, request, *args, **kwargs):
        person_guid = Persons.objects.get(guid=request.POST['person_guid_guid'])
        position_guid = Positions.objects.get(guid=request.POST['position_guid'])

        Trained_staff.objects.create(person_guid=person_guid,
                                     position_guid=position_guid,
                                     guid=str(uuid.uuid4()))

        return redirect('list_trained_staff')


class Trained_staff_deleted(DeleteView):
    model = Trained_staff
    context_object_name = 'trained_staff'
    success_url = reverse_lazy('list_trained_staff')
    template_name = 'TimeSheet/work/trained_staff/trained_staff_delete.html'

    def delete(self, request, *args, **kwargs):
        Trained_staff.objects.get(guid=self.kwargs.get('pk')).delete()
        return redirect('list_trained_staff')

    def get_object(self, queryset=None):
        return Trained_staff.objects.get(guid=self.kwargs.get('pk'))


def select_all_staff(request):
    date_now = date.today()
    init = TimeSheetPlane.objects.filter(month=date_now.month, year=date_now.year, dts=date_now, suspicious=0,
                                         enterprise_guid__enterprise_code__gt=2).values('person_guid__full_name',
                                                                                        'person_guid',
                                                                                        'position_guid__full_name',
                                                                                        'position_guid',
                                                                                        'shedule_guid__full_name',
                                                                                        'shedule_guid')

    return render(request, 'TimeSheet/work/trained_staff/select_all_staff_modal.html', {'init': init, })


def print_suspicious_facts(request):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("exec autofill_suspicious_facts %s, %s, %s",
                           [request.POST['dts_begin'], request.POST['dts_end'], 1])
            setobj = cursor.fetchall()
            new_list = []

            for i in setobj:
                dict = {'person_name': i[2],
                        'dts': i[0],
                        'en': i[1],
                        'bk_tp': i[3],
                        'bk_f': i[4],
                        'amount': i[5]}

                new_list.append(dict)

            new_list = sorted(new_list, key=lambda x: x['dts'])
        return render(request, 'TimeSheet/work/print_form/print_suspicious_facts.html', {'init': new_list,
                                                                                         'dts_begin': request.POST[
                                                                                             'dts_begin'],
                                                                                         'dts_end': request.POST[
                                                                                             'dts_end'], })
    else:
        init = []
        return render(request, 'TimeSheet/work/print_form/print_suspicious_facts.html', {'init': init, })


def add_image(request):
    guid_person_cowork = request.GET.get('guid')
    if request.method == 'POST':
        if len(request.FILES) > 0:
            obj_cowork = persons_coworks.objects.get(guid=guid_person_cowork)
            ImageCoworks.save_optimal_size(obj_cowork, request.FILES['uploader'], False, False)
        # return render(request, 'TimeSheet/work/upload_file.html', {'guid': guid_person_cowork, })
        obj_omg = ImageCoworks.objects.filter(persons_coworks=obj_cowork)
        return render(request, 'TimeSheet/part_form/part_timesheet_cowork.html',
                      {'img_url': obj_omg[0].image.url, 'img_guid': guid_person_cowork})
    else:
        return render(request, 'TimeSheet/work/upload_file.html', {'guid': guid_person_cowork, })


@login_required
def print_excess_rv_i(request):
    print_form = []
    dts_begin = request.GET.get('dts_begin')
    dts_end = request.GET.get('dts_end')
    enterprise_guid = request.GET.get('enterprise_guid')
    personal_guid = request.GET.get('pers_guid')

    if dts_begin is None and dts_end is None:
        return render(request, 'TimeSheet/work/print_form/print_excess_rv_i.html', {'init': print_form,
                                                                                    })

    enterprise_guid = None if enterprise_guid == '' else enterprise_guid
    personal_guid = None if personal_guid == '' else personal_guid

    list_bk = ['5A688F01-74A8-11E8-80F9-3640B58B95BD', '738B3875-17E4-11E9-80D0-E41F13C123D6']

    init = TimeSheetFact.objects.filter(p_uid__dts__gte=dts_begin, p_uid__dts__lte=dts_end, p_uid__suspicious=0,
                                        busy_key_fact__in=list_bk)

    if personal_guid:
        init = init.filter(p_uid__person_guid=personal_guid)

    if enterprise_guid:
        init = init.filter(p_uid__enterprise_guid=enterprise_guid)

    init_rv = init.filter(busy_key_fact='738B3875-17E4-11E9-80D0-E41F13C123D6').values('p_uid__person_guid').annotate(
        count_bk_rv=Count('busy_key_fact'))
    init_i = init.filter(busy_key_fact='5A688F01-74A8-11E8-80F9-3640B58B95BD').values('p_uid__person_guid').annotate(
        count_bk_i=Count('busy_key_fact'))

    diff = list(filter(lambda s: s['count_bk_rv'] != [] and s['count_bk_i'] < s['count_bk_rv'][0]['count_bk_rv'], list(
        map(lambda t: {'person_guid': t['p_uid__person_guid'], 'count_bk_i': t['count_bk_i'], 'count_bk_rv': list(
            filter(lambda x: t['p_uid__person_guid'] == x['p_uid__person_guid'], init_rv))}, init_i))))

    diff = list(map(lambda x: {'person_guid': x['person_guid'], 'count_bk_i': x['count_bk_i'],
                               'count_bk_rv': x['count_bk_rv'][0]['count_bk_rv']}, diff))

    person_list = {i.guid: i for i in Persons.objects.filter(guid__in=[i['person_guid'] for i in diff])}

    list_ent = {i.guid: i for i in Enterprises.objects.all()}
    list_pos = {i.guid: i for i in Positions.objects.all()}

    ent_pos = {x['p_uid__person_guid']: {'ent': list_ent.get(x['max_en']), 'pos': list_pos.get(x['max_pos'])} for x in
               init.values('p_uid__person_guid').annotate(max_en=Max('p_uid__enterprise_guid'),
                                                          max_pos=Max('p_uid__position_guid'))}

    diff = list(map(lambda x: {'person': person_list.get(x['person_guid']), 'ent': ent_pos.get(x['person_guid'])['ent'],
                               'pos': ent_pos.get(x['person_guid'])['pos'], 'person_guid': x['person_guid'],
                               'count_bk_i': x['count_bk_i'], 'count_bk_rv': x['count_bk_rv']}, diff))

    return render(request, 'TimeSheet/part_form/part_print_excess_rv.html', {'init': diff,
                                                                             'dts_begin': dts_begin,
                                                                             'dts_end': dts_end,
                                                                             'enterprise_guid': enterprise_guid})


@login_required
def mtv_cachier_header(request):
    print_form = []
    resigned_list = []
    dts_month = request.GET.get('dts_month')
    dts_year = request.GET.get('dts_year')
    enterprise_guid = request.GET.get('enterprise_guid')
    personal_guid = request.GET.get('pers_guid')
    check_mtv = request.GET.get('check_mtv')

    today = datetime.today()

    fl_full_tamplate = True if dts_month == None else False

    if not request.user.profileuser.entreprise is None:
        dts_month = today.month if dts_month == None else dts_month
        dts_year = today.year if dts_year == None else dts_year
        enterprise_guid = request.user.profileuser.entreprise if enterprise_guid == None or enterprise_guid == '' else enterprise_guid

    dict_month = {1: 'Январь',
                  2: 'Февраль',
                  3: 'Март',
                  4: 'Апрель',
                  5: 'Май',
                  6: 'Июнь',
                  7: 'Июль',
                  8: 'Август',
                  9: 'Сентябрь',
                  10: 'Октябрь',
                  11: 'Ноябрь',
                  12: 'Декабрь'}

    today_year = today.year
    list_year = [today_year - 1, today_year, today_year + 1]

    if dts_month is None and dts_year is None:
        return render(request, 'TimeSheet/work/mtv/mtv_v2.html', {'init': print_form, 'dict_month': dict_month,
                                                               'list_year': list_year, 'year': today.year,
                                                               'month': today.month})

    init = Mtv_cashier.objects.filter(year=dts_year, month=dts_month)
    init_header = Mtv_header.objects.filter(year=dts_year, month=dts_month)

    enterprise_guid = None if enterprise_guid == '' else enterprise_guid
    personal_guid = None if personal_guid == '' else personal_guid
    check_mtv = None if check_mtv == '' else check_mtv

    if personal_guid:
        init = init.filter(person_guid=personal_guid)
        init_header = init_header.filter(person_guid=personal_guid)

    if enterprise_guid:
        init = init.filter(enterprise_guid=enterprise_guid)
        init_header = init_header.filter(enterprise_guid=enterprise_guid)

    if check_mtv == 'true':
        init = init.filter(ml__gt=0)
        init_header = init_header.filter(ml__gt=0)

    init = init.order_by('enterprise_guid__name', 'person_guid__full_name')

    for i in init:
        if i.person_guid.person_statuses_set.filter(work_status_id=27).first():
            resigned_list.append(i.person_guid)

    for i in init_header:
        if i.person_guid.person_statuses_set.filter(work_status_id=27).first():
            resigned_list.append(i.person_guid)

    # if not request.user.profileuser.entreprise is None:
    if fl_full_tamplate:
        return render(request, 'TimeSheet/work/mtv/mtv_v2.html',
                      {'init': init, 'init_header': init_header, 'dict_month': dict_month, 'list_year': list_year,
                       'year': today.year, 'month': today.month, 'resigned_list': resigned_list,
                       'l_yel': [2, 6, 10, 14], 'l_grn': [1, 3, 5, 7, 9, 11, 13, 15]})
    else:
        return render(request, 'TimeSheet/work/mtv/part_mtv_v2.html', {'init': init, 'init_header': init_header,
                                                                    'resigned_list': resigned_list,
                                                                'l_yel': [2, 6, 10, 14], 'l_grn': [1, 3, 5, 7, 9, 11, 13, 15]})


def shift_data_f_check_count_new(request):

    if request.user.profileuser.otiz:
        st_id_filter = 0 # Требуется решение
        list_doc = Shift_data_f_checks_statuses.objects.values('data_f_check_uid').annotate(max_dts=Max('dts'),
                                                            status=Max('status_id__id')).filter(status=int(st_id_filter))

        return HttpResponse(len(list_doc))
    else:
        return HttpResponse(0)


def ajax_save_change_rework(request):

    guid_row = request.POST.get('guid')
    dts_row = request.POST.get('dts')

    date_row = date(int(dts_row[0:4]), int(dts_row[5:7]), int(dts_row[8:10]))

    if guid_row == "":
        return HttpResponse('false')

    record_rew = persons_reworks.objects.get(guid=guid_row)
    if record_rew:

        fact_timesheet = TimeSheetFact.objects.filter(p_uid__dts=date_row,
                                                      p_uid__person_guid=record_rew.coworker_guid,
                                                      busy_key_fact='5A688F01-74A8-11E8-80F9-3640B58B95BD')

        if len(fact_timesheet) > 0:
            record_rew.dts = date_row
            record_rew.save()
            return JsonResponse({'result': 0,
                                 'message': '' + date_row.strftime("%Y-%m-%d") + ' в этой дате сотрудник находится в состоянии Я',
                                 'dts_return': record_rew.dts})


        record_rew.dts = date_row
        record_rew.save()
    else:
        return JsonResponse({'result': 0,
                                 'message': 'Ошибка записи новых данных....',
                                 'dts_return': record_rew.dts})

    return JsonResponse({'result': 1,})


def person_covid(request):
    if request.method == 'POST':

        if request.POST['close_save'] == "Сохранить":

            for i in range(int(request.POST['len_list'])):
                enterprise = Enterprises.objects.get(guid=request.POST['enterprise'])
                # vaccinated = request.POST['vaccinated' + str(i)]
                # contraindications = request.POST['contraindications' + str(i)]
                # having_qr_code = request.POST['having_qr_code' + str(i)]
                reply_code = request.POST['reply_code' + str(i)]
                person_covid = Persons.objects.get(guid=request.POST['person_guid' + str(i)])
                dts = datetime.today()
                last_week_checkin = request.POST['last_week_checkin' + str(i)]

                # if vaccinated == '--------' or contraindications == '--------':
                #     messages.warning(request, "ОШИБКА! нет данных! сотрудник: " + str(person_covid))
                #     continue

                find_row = persons_covid19.objects.filter(enterprise_guid=enterprise,
                                                          person_guid=person_covid,
                                                          dts=dts).first()

                # if find_row == None:
                #     persons_covid19.objects.create(
                #         uid=str(uuid.uuid4()),
                #         enterprise_guid=enterprise,
                #         person_guid=person_covid,
                #         dts=dts,
                #         vaccination_type=0 if vaccinated == 'true' else 1,
                #         vaccination_declined=1 if contraindications == 'true' else 0,
                #         having_qr_code=1 if having_qr_code == 'true' else 0,
                #     )
                # else:
                #     find_row.enterprise_guid = enterprise
                #     find_row.person_guid = person_covid
                #     find_row.dts = dts
                #     find_row.vaccination_type = 0 if vaccinated == 'true' else 1
                #     find_row.vaccination_declined = 1 if contraindications == 'true' else 0
                #     find_row.having_qr_code = 1 if having_qr_code == 'true' else 0
                #     find_row.save()

                if find_row == None:
                    persons_covid19.objects.create(
                        uid=str(uuid.uuid4()),
                        enterprise_guid=enterprise,
                        person_guid=person_covid,
                        dts=dts,
                        vaccination_type=0,
                        vaccination_declined=0,
                        having_qr_code=0,
                        reply_code=reply_code,
                        last_week_checkin=1 if last_week_checkin == 'true' else 0,
                    )
                else:
                    find_row.enterprise_guid = enterprise
                    find_row.person_guid = person_covid
                    find_row.dts = dts
                    find_row.vaccination_type = 0
                    find_row.vaccination_declined = 0
                    find_row.having_qr_code = 0
                    find_row.reply_code = reply_code
                    find_row.last_week_checkin = 1 if last_week_checkin == 'true' else 0
                    find_row.save()

            return redirect('dashboard')

    else:

        this_enterprise = request.user.profileuser.entreprise

        this_today = datetime.today()
        list_obj = TimeSheetPlane.objects.filter(enterprise_guid=this_enterprise, dts=this_today, suspicious=0).exclude(
            busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618').distinct()

        list_codes = covid19_reply_codes.objects.all()

        return render(request, 'TimeSheet/person_covid_v2.html', {'list_obj': list_obj,
                                                           'enterprise': this_enterprise,
                                                           'len_list': len(list_obj),
                                                           'list_codes': list_codes})
