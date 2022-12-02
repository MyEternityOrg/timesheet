from django.urls import path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from .views import TimeSheet_list_view, TimeSheet_table_view, TimeSheet_detail_View, TimeSheet_table_view_cowork, \
    TimeSheet_table_creat_cowork, select_cowork_view, TimeSheet_table_view_rework, \
    TimeSheet_table_creat_rework, select_rework_view, deleted_cowork, TimeSheet_table_print, revision_list, \
    revision_edit, revision_deleted, revision_create, select_enterprise, print_divergence_table, divergence_table, \
    test_call, record_sheet, record_sheet_rv, fill_table, edit_remove_person, print_hours_worked, print_hours_worked_ex,messages_over, \
    ajax_login_user, info_history_table_personel, filter_table_list, select_all_persons, deleted_rework, \
    Shift_data_f_checksListView, Shift_data_f_checksUpdateView, EditTimeSheetPersonalList, EditTimeSheetPersonalCreate,\
    record_service_note, print_cowork_noshows, Trained_staff_EditView, Trained_staff_deleted, Trained_staff_ListView,\
    Trained_staff_CreateView, select_all_staff, print_suspicious_facts, info_history_table_cowork, add_image, print_route_sheets, \
    print_excess_rv_i, dashboard, mtv_cachier_header, shift_data_f_check_count_new, ajax_save_change_rework, person_covid

# , user_login

urlpatterns = [
                  path('', dashboard, name='dashboard'),
                  path('table_list/', TimeSheet_list_view, name='table-list'),
                  path('select_enterprise/', select_enterprise, name='select-enterprise'),
                  path('revision_list/', revision_list, name='revision-list'),
                  path('revision_create/', revision_create, name='revision-create'),
                  path('revision_edit/<str:enterprise>/<str:dts>/', revision_edit, name='revision-edit'),
                  path('revision_deleted/<str:enterprise>/<str:dts>/', revision_deleted, name='revision-deleted'),
                  path('print_divergence_table/<str:dts_begin>/<str:dts_end>/', print_divergence_table,
                       name='print-divergence-table'),
                  path('print_hours_worked/', print_hours_worked, name='print-hours-worked'),
                  path('print_hours_worked_ex/', print_hours_worked_ex, name='print-hours-worked-ex'),
                  path('divergence_table/', divergence_table, name='divergence-table'),
                  path('edit_remove_person/<str:person>/<str:enterprise>/', edit_remove_person,
                       name='edit-remove-person'),
                  path('shift_data_f_checks/', Shift_data_f_checksListView.as_view(), name='shift_data_f_checks'),
                  path('shift_data_f_checks-update/<str:pk>/', Shift_data_f_checksUpdateView.as_view(),
                       name='shift_data_f_checks_update'),
                  path('edit-time-sheet-personal-List/<str:pers>/<str:ent>/<int:year>/<int:month>/',
                       EditTimeSheetPersonalList.as_view(), name='edit_time_sheet_personal_List'),
                  path('edit-time-sheet-personal-create/<str:p_uid>/<int:state>', EditTimeSheetPersonalCreate.as_view(),
                       name='edit_time_sheet_personal_create'),
                  path('deleted_trained_staff/<str:pk>/', Trained_staff_deleted.as_view(),
                       name='deleted_trained_staff'),
                  path('list_trained_staff/', Trained_staff_ListView.as_view(), name='list_trained_staff'),
                  path('edit_trained_staff_create/<str:guid>/', Trained_staff_EditView.as_view(),
                       name='edit_trained_staff'),
                  path('create_trained_staff/', Trained_staff_CreateView.as_view(), name='create_trained_staff'),
                  path('<str:enterprise>/<str:year>/<str:month>/', TimeSheet_table_view, name='table-sheet'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:day>/cowork/', TimeSheet_table_view_cowork,
                       name='table-sheet-cowork'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:day>/rework/', TimeSheet_table_view_rework,
                       name='table-sheet-rework'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:day>/<str:cowork_state>/cowork_create/',
                       TimeSheet_table_creat_cowork, name='create-cowork'),
                  path('<str:pk>/<str:enterprise>/<str:person>/<str:year>/<str:month>/<str:day>/deleted_create/', deleted_cowork,
                       name='deleted_cowork'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:day>/rework/rework_create/',
                       TimeSheet_table_creat_rework, name='create-rework'),
                  path('<str:enterprise>/<str:pk>/', TimeSheet_detail_View, name='edit-table'),
                  path('<str:enterprise>/<str:position>/<str:year>/<str:month>/<str:day>/select_cowork/<int:filter_fact>/<str:p_uid>',
                      select_cowork_view, name='select-cowork'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:day>/select_rework/', select_rework_view,
                       name='select-rework'),
                  path('<str:enterprise>/<str:year>/<str:month>/table_print/', TimeSheet_table_print,
                       name='table-print'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:personal>/info_history_table/',
                       info_history_table_personel,
                       name='info-history-table'),
                  path('<str:enterprise>/<str:year>/<str:month>/info_history_cowork/',
                       info_history_table_cowork,
                       name='info-history-cowork'),
                  path('<str:enterprise>/<str:year>/<str:month>/<str:day>/select_rework/', select_rework_view,
                       name='select-rework'),
                  path('my_ajax_test/', test_call),
                  path('ajax_record_sheet/', record_sheet),
                  path('ajax_record_service_note/', record_service_note),
                  path('ajax_record_sheet_rv/', record_sheet_rv),
                  path('ajax_fill_table/', fill_table),
                  path('ajax_messages/', messages_over),
                  path('ajax_login_user/', ajax_login_user),
                  path('filter/', filter_table_list),
                  path('select_all_persons/', select_all_persons, name='select_all_persons'),
                  path('<str:enterprise>/<str:person>/<str:year>/<str:month>/<str:day>/deleted_rework/', deleted_rework,
                       name='deleted_rework'),
                  path('print_cowork_no_shows/', print_cowork_noshows,
                       name='print_cowork_no-shows'),
                  path('select_all_staff/', select_all_staff, name='select_all_staff'),
                  path('print_suspicious_facts/', print_suspicious_facts, name='print_suspicious_facts'),
                  path('print_route_sheets/', print_route_sheets, name='print_route_sheets'),
                  path('print_excess_rv_i/', print_excess_rv_i, name='print_excess_rv_i'),
                  path('add_image/', add_image, name='add_image'),
                  path('mtv/', mtv_cachier_header, name='mtv_cachier_header'),
                  path('ajax_count_correct/', shift_data_f_check_count_new),
                  path('ajax_save_change_rework/', ajax_save_change_rework),
                  path('person_covid/', person_covid, name='person_covid'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
