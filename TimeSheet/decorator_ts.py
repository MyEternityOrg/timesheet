from django.contrib import messages
from django.shortcuts import redirect
from datetime import datetime, date
from .models import SettingTableTemp


def timeover_timeshift(func):
    def wrapper(*args, **kwargs):

        if len(args) == 0:
            pass
        else:
            current_user = args[0].user
            if current_user is None:
                return redirect('table-list')
            else:
                if not current_user.is_superuser and current_user.profileuser.entreprise is not None:
                    now_date = datetime.now()
                    current_enterprise = current_user.profileuser.entreprise
                    reqeust_enterprise = kwargs.get('enterprise')
                    if reqeust_enterprise is not None and current_enterprise.guid != reqeust_enterprise:
                        messages.warning(args[0],
                                         f'Попытка зайти в табель другого подразделение. Данные отправлены на рассмотрение администрацией!')

                        return redirect('table-sheet', enterprise=current_enterprise.guid, year=now_date.year,
                                        month=now_date.month)
                    if current_enterprise.time_close_table():
                        messages.warning(args[0],
                                         f'Табель уже закрыт!')
                        #
                        # return redirect('table-sheet', enterprise=current_enterprise.guid, year=now_date.year,
                        #                 month=now_date.month)
                        return redirect('table-list')

                    date_change_timesheet = now_date
                    if args[0].resolver_match.url_name == 'edit-table':
                        pk_date = kwargs.get('pk')
                        if pk_date is not None:
                            date_change_timesheet = date(int(pk_date[:4]), int(pk_date[5:7]), int(pk_date[8:10]))

                    if kwargs.get('month') is not None:
                        date_change_timesheet = date(int(kwargs.get('year')), int(kwargs.get('month')), int(kwargs.get('day')))

                    count_day = SettingTableTemp.get_open_day_table(current_enterprise)
                    if (now_date.day - count_day + 1) > date_change_timesheet.day:
                        messages.warning(args[0],
                                         f'Табель закрыт для редактирования!')

                        return redirect('table-sheet', enterprise=current_enterprise.guid, year=now_date.year,
                                        month=now_date.month)
                elif not current_user.is_superuser and current_user.profileuser.entreprise is None:
                    now_date = datetime.now()
                    if kwargs.get('month') is not None and kwargs.get('year') is not None:
                        date_change_timesheet = date(int(kwargs.get('year')), int(kwargs.get('month')), 1)
                        close_timesheet = SettingTableTemp.get_sign_of_closing_timesheet_on_date(None, date_change_timesheet)

                        if close_timesheet:
                            messages.warning(args[0],
                                             f'Табель закрыт для редактирования!')

                            return redirect('table-list')


        return func(*args, **kwargs)

    return wrapper
