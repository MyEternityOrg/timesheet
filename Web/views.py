from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import TimeSheetPlane, Enterprises, TimeSheetFact, BusyKeys, Persons, Shedules, persons_coworks, \
    Positions, PositionsReplacement, ProfileUser, persons_reworks, persons_audit, StaffHistory, SettingTableTemp, \
    enterprise_revision, SheduleHours, enterprise_revision_changes, persons_extended_info
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
# from django.views.generic import ListView
#
# from django.http import FileResponse
# from reportlab.pdfgen import canvas
# import io
# from easy_pdf.rendering import render_to_pdf


@login_required
def TimeSheet_list_view(request):
    profile = ProfileUser.get_profile(ProfileUser, request.user)

    if profile.revisor:
        return redirect('revision-list')

    if profile.entreprise != None:
        data = TimeSheetPlane.get_list_table_enterprise(TimeSheetPlane, profile.entreprise)
    else:
        data = TimeSheetPlane.get_all_list_table(request)
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

    return render(request, 'TimeSheet/work/timesheet_list.html',
                  {'data_set': data, 'sheet_shop': 'Список табелей', 'dict_month': dict_month})


@login_required
def TimeSheet_table_view(request, enterprise, year, month):
    if request.method == 'POST':
        return redirect('edit-table', enterprise=enterprise, pk=request.POST['date_edit'])

    else:
        print(datetime.today())
        query = Q(enterprise_guid=enterprise) & Q(year=year) & Q(month=month)
        data_sheet = TimeSheetPlane.objects.filter(query).exclude(person_guid='00000000-0000-0000-0000-000000000000').exclude(busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618').filter(suspicious=0)
        init_fact = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__year=year,
                                                 p_uid__month=month, p_uid__suspicious=0) #.exclude(p_uid__busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618')

        transposed = TimeSheetPlane.transposed_TimeSheetplan(data_sheet, init_fact)

        list_date = TimeSheetPlane.get_list_date(data_sheet)
        ent = Enterprises.objects.get(guid=enterprise)

        # date_t = datetime.combine(date(int(year), int(month), 1), time(1, 1)).strftime("%B %Y")
        date_t_f = datetime.combine(date(int(year), int(month), 1), time(1, 1))
        date_t = dateformat.format(date_t_f, "F Y")

        data_coworks = persons_coworks.get_context(date_t_f, enterprise)

        data_reworks = persons_reworks.get_context(date_t_f, enterprise)

        hidden_h = True
        day_open = 999
        last_day = 1
        today = datetime.today()
        to_day = today.day
        profile = ProfileUser.get_profile(ProfileUser, request.user)
        if profile.entreprise != None:
            hidden_h = False

            if today.year == int(year) and today.month == int(month):
                last_day = SettingTableTemp.objects.first().count_day_last
                if last_day == 1:
                    day_open = to_day
                else:
                    day_open = to_day - last_day
                    if day_open < 0:
                        day_open = 1
            else:
                day_open = 0
                to_day = 0

        dict_rem_pers = {i.person_guid: i.dts for i in persons_extended_info.objects.all()}
        print(datetime.today())

        return render(request, 'TimeSheet/test/timesheet_table_test.html',
                      {'data': transposed, 'sheet_shop': ent, 'list_date': list_date,
                       'enterprise': enterprise, 'date_sheet': date_t,
                       'data_coworks': data_coworks,
                       'data_reworks': data_reworks,
                       'hidden_h': hidden_h,
                       'day_open': day_open,
                       'today': to_day, 'year': year, 'month': month,
                       'dict_rem_pers': dict_rem_pers,
                       })


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

                    if f_model == None:
                        row_t_fact = TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                                    busy_key_fact=BusyKeys.objects.get(guid=f_busy),
                                                    amount=f_amount,
                                                    p_uid=time_plane,
                                                    record_fixed=1)
                        row_t_fact.save_history(user=request.user, f_uid=row_t_fact.uid)
                    else:
                        row_t_fact = f_model
                        row_t_fact.busy_key_fact = BusyKeys.objects.get(guid=f_busy)
                        row_t_fact.amount = f_amount
                        row_t_fact.p_uid = time_plane
                        row_t_fact.record_fixed = 1
                        row_t_fact.save()

                        row_t_fact.save_history(user=request.user.get_full_name(), f_uid=row_t_fact.uid)

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
        record_revision = enterprise_revision.objects.filter(enterprise_uid=enterprise, revision_date=dts_date-timedelta(days=1))
        if len(record_revision) == 0:
            disabled_revision = True

        return render(request, 'TimeSheet/test/timesheet_detail_test.html', {'formset': form,
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
        data_coworks = persons_coworks.get_context_day(date_t_f, enterprise)
        ent = Enterprises.objects.get(guid=enterprise)

        hidden_h = True
        profile = ProfileUser.get_profile(ProfileUser, request.user)
        if profile.entreprise != None:
            hidden_h = False

        return render(request, 'TimeSheet/work/timesheet_cowork.html', {'dataset': data_coworks, 'sheet_shop': ent,
                                                                        'dts': date_t_f, 'enterprise': enterprise,
                                                                        'hidden_h': hidden_h})


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

            # n_record_coworks = persons_coworks.objects.filter(dts=date_f,
            #                                         coworker_guid=coworker_guid,
            #                                         foworker_guid=foworker_guid,
            #                                         coworker_enterprise_guid=coworker_enterprise_guid,
            #                                         enterprise_guid=enterprise_guid,
            #                                         shedule_guid=shedule_guid,
            #                                         position_guid=position_guid)

            n_record_coworks = persons_coworks.objects.filter(dts=date_f,
                                                              coworker_guid=coworker_guid
                                                              )
            n_record_fact = TimeSheetFact.objects.filter(p_uid__dts=date_f,
                                                         p_uid__person_guid=coworker_guid,
                                                         busy_key_fact='5A688F01-74A8-11E8-80F9-3640B58B95BD'
                                                         )

            if len(n_record_coworks) == 0 and len(n_record_fact) == 0:

                if count_hours == 0:
                    qSet = SheduleHours.objects.filter(dts=date_f, shedule_guid=shedule_guid, busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')
                    if len(qSet) != 0:
                        count_hours = qSet[0].hours_lite

                persons_coworks.objects.create(
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
                    record_fixed=1
                )
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

        date_t_f = date(int(year), int(month), int(day))
        ent = Enterprises.objects.get(guid=enterprise)

        n_record_coworks = persons_coworks.objects.filter(dts=date_t_f,
                                                          cowork_state=0)
        list_exclude = []
        for i in n_record_coworks:
            list_exclude.append(i.foworker_guid)

        # list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6', '5A688F06-74A8-11E8-80F9-3640B58B95BD']
        list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6'] #Отпуск убрал

        init = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__dts=date_t_f,
                                            busy_key_fact__in=list_f_busy).exclude(p_uid__person_guid__in=list_exclude)
        init_en = Enterprises.get_list_shops(Enterprises)
        init_pos = Positions.objects.all()

        # {pers.p_uid.person_guid.guid}}|{{pers.p_uid.position_guid.guid}}|{{pers.p_uid.shedule_guid.guid}}|{{pers.p_uid.hours_all}

        init_work = []
        for i in init:
            new_dict = {'person_guid': i.p_uid.person_guid, 'position_guid': i.p_uid.position_guid,
                        'shedule_guid': i.p_uid.shedule_guid, 'hours_all': i.p_uid.hours_all}
            init_work.append(new_dict)

        init_vacancy = TimeSheetPlane.get_vacancy(enterprise=enterprise, date_f=date_t_f)
        if len(init_vacancy) > 0:
            pers_vacancy = Persons.objects.get(guid='00000000-0000-0000-0000-000000000000')
            for i in init_vacancy:
                init_work.append({'person_guid': pers_vacancy, 'position_guid': Positions.objects.get(guid=i[2]),
                             'shedule_guid': Shedules.objects.get(guid=i[3]), 'hours_all': i[5]})

        # init_0 = TimeSheetPlane.objects.filter(enterprise_guid__guid=enterprise, dts=date_t_f, person_guid='00000000-0000-0000-0000-000000000000')

        # init = init + init_0

        return render(request, 'TimeSheet/work/timesheet_create_cowork.html', {'sheet_shop': ent,
                                                                               'dts': date_t_f,
                                                                               'enterprise': enterprise,
                                                                               'init': init_work, 'init_en': init_en,
                                                                               'init_pos': init_pos,
                                                                               'cowork_state': cowork_state, })


@login_required
def TimeSheet_table_creat_rework(request, enterprise, year, month, day):
    if request.method == 'POST':
        if request.POST['close_table'] == "Сохранить":

            date_f = date(int(request.POST['year']), int(request.POST['month']), int(request.POST['day']))

            pers = Persons.objects.get(guid=request.POST['person_guid_to'])
            pos = StaffHistory.get_last_position(StaffHistory, date_f, pers)
            en = Enterprises.objects.get(guid=request.POST['enterprise_guid'])

            n_record = persons_reworks.objects.filter(dts=date_f, coworker_guid=pers, enterprise_guid=en,
                                                   position_guid=pos)

            if len(n_record) == 0:

                persons_reworks.objects.create(
                    dts=date_f,
                    coworker_guid=pers,
                    enterprise_guid=en,
                    position_guid=pos,
                    count_hours=11
                )
            else:
                messages.success(request, "Данный сотрудник уже есть в табеле")

        return redirect('table-sheet-rework', enterprise=request.POST['enterprise'], year=request.POST['year'],
                        month=request.POST['month'], day=request.POST['day'])
    else:

        date_t_f = date(int(year), int(month), int(day))
        ent = Enterprises.objects.get(guid=enterprise)

        init_en = Enterprises.get_list_shops(Enterprises)

        return render(request, 'TimeSheet/work/timesheet_create_rework.html', {'sheet_shop': ent,
                                                                               'dts': date_t_f,
                                                                               'enterprise': enterprise,
                                                                               'init_en': init_en, })


@login_required
def deleted_cowork(request, enterprise, person, year, month, day):
    date_f = date(int(year), int(month), int(day))

    n_record_coworks = persons_coworks.objects.filter(dts=date_f,
                                                      coworker_guid=person
                                                      )
    if len(n_record_coworks) > 0:
        n_record_coworks.delete()

    return redirect('table-sheet-cowork', enterprise, year, month, day) \


@login_required
def select_cowork_view(request, enterprise, position, year, month, day, filter_fact=0, p_uid=''):
    date_t_f = date(int(year), int(month), int(day))
    ent = Enterprises.objects.get(guid=enterprise)
    pos_en = PositionsReplacement.get_replace_positions(position, 0)
    # print(pos_en)
    # init = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__person_guid__guid=pos_en[0], p_uid__dts=date_t_f, busy_key_fact='5A688F12-74A8-11E8-80F9-3640B58B95BD')
    # init = TimeSheetFact.objects.filter(reduce(or_, [Q(p_uid__position_guid__guid=c) for c in pos_en])).filter(p_uid__enterprise_guid__guid=enterprise, p_uid__dts=date_t_f, busy_key_fact='5A688F12-74A8-11E8-80F9-3640B58B95BD')
    if pos_en == []:
        init = []
    else:
        if filter_fact==0:
            init_main = TimeSheetPlane.objects.filter(reduce(or_, [Q(position_guid__guid=c) for c in pos_en])).filter(
            enterprise_guid__guid=enterprise, dts=date_t_f, busy_key_guid__guid__in=(
                '5A688F12-74A8-11E8-80F9-3640B58B95BD', '5A688F01-74A8-11E8-80F9-3640B58B95BD', '5A688F06-74A8-11E8-80F9-3640B58B95BD')).exclude(
            person_guid='00000000-0000-0000-0000-000000000000')  #без отпуска, убрал отпуск

            init = []
            for i in init_main:
                init.append(
                    {'person_guid': i.person_guid, 'position_guid': i.position_guid, 'shedule_guid': i.shedule_guid})
        else:
            n_record_coworks = persons_coworks.objects.filter(dts=date_t_f,
                                                              cowork_state=0)
            list_exclude = []
            for i in n_record_coworks:
                list_exclude.append(i.foworker_guid)

            list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6', '5A688F06-74A8-11E8-80F9-3640B58B95BD']
            # list_f_busy = ['738B387C-17E4-11E9-80D0-E41F13C123D6']

            init_main = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__dts=date_t_f,
                                                busy_key_fact__in=list_f_busy,  p_uid__position_guid__guid__in=pos_en).exclude(
                                                p_uid__person_guid__in=list_exclude).exclude(p_uid__busy_key_guid='E1916359-15C4-11E9-8112-00155D6DE618')

            init = []
            for i in init_main:
                init.append({'person_guid': i.p_uid.person_guid, 'position_guid': i.p_uid.position_guid,
                             'shedule_guid': i.p_uid.shedule_guid})

            init_vacancy = TimeSheetPlane.get_vacancy(enterprise=enterprise, date_f=date_t_f)
            if len(init_vacancy)>0:
                pers_vacancy = Persons.objects.get(guid='00000000-0000-0000-0000-000000000000')
                for i in init_vacancy:
                    if i[2] in pos_en:
                        init.append({'person_guid': pers_vacancy, 'position_guid': Positions.objects.get(guid=i[2]),
                                     'shedule_guid': Shedules.objects.get(guid=i[3])})

    if p_uid == '' or p_uid == '0':
        person_guid = '0000'
    else:
        person_guid = TimeSheetPlane.objects.get(p_uid=p_uid).person_guid.guid

    return render(request, 'TimeSheet/work/select_cowork.html', {'sheet_shop': ent,
                                                                 'dts': date_t_f, 'enterprise': enterprise,
                                                                 'init': init,
                                                                 'person': person_guid,
                                                                 'p_uid': p_uid,
                                                                 })


@login_required
def select_rework_view(request, enterprise, year, month, day):
    date_t_f = date(int(year), int(month), int(day))
    ent = Enterprises.objects.get(guid=enterprise)
    pos_en = persons_audit.get_context(enterprise=ent)

    if len(pos_en) == 0:
        messages.success(request, "Задайте правила выхода в ревизию")
        return HttpResponse('<h1>TIME SHEET ERROR: нет правил выхода в ревизию</h1>')

    pers_reworks = persons_reworks.objects.filter(dts=date_t_f, enterprise_guid=ent)

    init = TimeSheetPlane.objects.filter(enterprise_guid__guid=enterprise, dts=date_t_f,
                                         busy_key_guid__guid='5A688F12-74A8-11E8-80F9-3640B58B95BD',
                                         position_guid__in=pos_en)

    if len(pers_reworks) > 0:
        init = init.exclude(person_guid__in=list((i.coworker_guid for i in pers_reworks)))

    return render(request, 'TimeSheet/work/select_cowork.html', {'sheet_shop': ent,
                                                                 'dts': date_t_f, 'enterprise': enterprise,
                                                                 'init': init, })


@login_required
def TimeSheet_table_print(request, enterprise, year, month):
    init_fact = TimeSheetFact.objects.filter(p_uid__enterprise_guid__guid=enterprise, p_uid__year=year,
                                             p_uid__month=month).exclude(
        p_uid__person_guid='00000000-0000-0000-0000-000000000000').order_by('p_uid__person_guid')

    any_day = date(int(year), int(month), 1)
    ent = Enterprises.objects.get(guid=enterprise)
    today = datetime.today()
    init_cowork = persons_coworks.get_context(any_day, enterprise)

    days_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    last_day_month = int(persons_coworks.last_day_of_month(any_day).day) + 1
    dict_moth = {a: days_week[date(int(year), int(month), a).weekday()] for a in range(1, last_day_month)}
    dict_fio = {}
    dict_total_pers = {}

    for element in init_fact:
        if dict_fio.get(element.p_uid.person_guid) == None:
            dict_fio[element.p_uid.person_guid] = {}

        if dict_fio[element.p_uid.person_guid].get(element.p_uid.dts.day) == None:
            dict_fio[element.p_uid.person_guid][element.p_uid.dts.day] = list(filter(lambda x:x.p_uid.person_guid == element.p_uid.person_guid and x.p_uid.dts.day == element.p_uid.dts.day, init_fact))


    dict_pos = {el: StaffHistory.get_last_position(StaffHistory, date(int(year), int(month), date.today().day), el) for
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

    # with open('example.pdf', 'wb') as f2:
    #     f2.write(render_to_pdf('TimeSheet/work/print_form/print_table.html', {'sheet_shop': ent,
    #                                                                       'dts': last_day_month,
    #                                                                       'enterprise': enterprise,
    #                                                                       'dict_fio': dict_fio,
    #                                                                       'dict_pos': dict_pos,
    #                                                                       'dict_moth': dict_moth,
    #                                                                       'dict_total_pers': dict_total_pers,
    #                                                                       'today': today,
    #                                                                       }, encoding=u'utf-8'))


    return render(request, 'TimeSheet/work/print_form/print_table.html', {'sheet_shop': ent,
                                                                          'dts': last_day_month,
                                                                          'enterprise': enterprise,
                                                                          'dict_fio': dict_fio,
                                                                          'dict_pos': dict_pos,
                                                                          'dict_moth': dict_moth,
                                                                          'dict_total_pers': dict_total_pers,
                                                                          'today': today,
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

    n_record = enterprise_revision.objects.get(enterprise_uid=enterprise, revision_date=date_f)
    n_record.delete()

    return redirect('revision-list')


@login_required
def revision_create(request):
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
        return render(request, 'TimeSheet/work/revision_edit.html', {'enterprise_uid': None,
                                                                     'revision_date': date.today().strftime('%Y-%m-%d'),
                                                                     'uid': None,
                                                                     'changetime':'',})


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
    begin_date = datetime.today().replace(day=1)
    end_date = persons_reworks.last_day_of_month(begin_date)

    return render(request, 'TimeSheet/work/divergence_table.html', {
        'dts_begin': begin_date.strftime('%Y-%m-%d'),
        'dts_end': end_date.strftime('%Y-%m-%d'),
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
    return record_date_create.changetime.strftime("%d-%m-%Y %H.%M.%S")


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

@login_required
def record_sheet(request):

    p_uid = TimeSheetPlane.objects.get(p_uid=request.POST['p_uid'])
    if request.POST['f_busy'] == 'selected':
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
                                     record_fixed=0)
    elif f_busy is None:
        if f_model is not None:
            f_model.delete()



    if f_model.busy_key_fact == busy_key_rv and busy_key_rv != f_busy: #удалим РВ если оно есть
        del_persons_coworks = persons_coworks.objects.filter(dts=p_uid.dts,
                                                             coworker_guid=p_uid.person_guid,
                                                             # coworker_enterprise_guid=p_uid.enterprise_guid,
                                                             # shedule_guid=p_uid.shedule_guid,
                                                             cowork_state=0,
                                                             cowork_local=1).first()

        if del_persons_coworks is not None:
            del_persons_coworks.delete()


    if f_busy is not None:
        f_model.busy_key_fact = f_busy
        f_model.amount = f_amount
        f_model.p_uid = p_uid
        f_model.record_fixed = 0
        f_model.save()

    # посмотрим, может ест Н часы
    busy_key_N = BusyKeys.objects.get(guid='E1916359-15C4-11E9-8112-00155D6DE618')
    plan_model = TimeSheetPlane.objects.filter(dts=p_uid.dts, person_guid=p_uid.person_guid, busy_key_guid=busy_key_N).first()

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
                                         record_fixed=0)
        else:

            f_model_N.busy_key_fact = f_busy
            f_model_N.amount = f_amount
            f_model_N.p_uid = plan_model
            f_model_N.record_fixed = 0
            f_model_N.save()


    return HttpResponse('True')

@login_required
def record_sheet_rv(request):

    pers = Persons.objects.get(guid=request.POST['pers'])
    shedule_guid = Shedules.objects.get(guid=request.POST['shedule'])
    date_f = request.POST['dts']
    enterprise = Enterprises.objects.get(guid=request.POST['enterprise'])
    position = Positions.objects.get(guid=request.POST['position'])
    pers_first = Persons.objects.get(guid=request.POST['pers_first'])

    qSet = SheduleHours.objects.filter(dts=date_f, shedule_guid=shedule_guid, busy_key_guid='5A688F00-74A8-11E8-80F9-3640B58B95BD')
    if len(qSet) != 0:
        count_hours = qSet[0].hours_lite


    persons_coworks.objects.create(
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
        record_fixed=0)

    p_uid = TimeSheetPlane.objects.get(p_uid=request.POST['p_uid'])
    f_busy = BusyKeys.objects.get(guid='738B3875-17E4-11E9-80D0-E41F13C123D6')

    f_model = TimeSheetFact.objects.filter(p_uid=p_uid.p_uid).first()

    if f_model == None:
        TimeSheetFact.objects.create(uid=str(uuid.uuid4()),
                                     busy_key_fact=f_busy,
                                     amount=count_hours,
                                     p_uid=p_uid,
                                     record_fixed=0)
    else:
        f_model.busy_key_fact = f_busy
        f_model.amount = count_hours
        f_model.p_uid = p_uid
        f_model.record_fixed = 0
        f_model.save()

    return HttpResponse('True')

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

    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("exec get_staff_work_report '" + request.POST['dts_begin'] + "', '" + request.POST['dts_end'] + "', '" + request.POST['enterprise_guid'] + "'")

            setobj = cursor.fetchall()
            new_list = []

            for i in setobj:
                dict = {'person_guid': Persons.objects.get(guid=i[1]),
                        'plan_amt_count': i[2],
                        'plan_amt_hours': i[5],
                        'fact_amt_count': i[3],
                        'fact_amt_hours': i[6],
                        'cowr_amt_count': i[4],
                        'cowr_amt_hours': i[7],
                        'total_hours': i[9]}

                new_list.append(dict)

        return render(request, 'TimeSheet/work/print_form/print_hours_worked.html', {'init': new_list,
                                                                                     'dts_begin': request.POST['dts_begin'],
                                                                                     'dts_end': request.POST['dts_end'],
                                                                                     'enterprise_guid': request.POST['enterprise_guid']})
    else:
        print_form = []
        return render(request, 'TimeSheet/work/print_form/print_hours_worked.html', {'init': print_form,
                                                                          })


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
    else:
        return None


def ajax_login_user(request):

    ip_adress = get_local_ip_client(request)

    to_user = get_user_ip(ip_adress)
    if to_user is not None:
        login(request, to_user)
        return redirect('table-list')

    return True

@register.filter
def this_around_the_clock(guid_sheduler, dts):

    obj_sh = Shedules.objects.get(guid=guid_sheduler)

    return obj_sh.sheduler_round_the_clock(dts)

