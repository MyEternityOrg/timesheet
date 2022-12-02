from django import forms
from django.forms import formset_factory, inlineformset_factory, modelformset_factory
from .models import TimeSheetPlane, TimeSheetFact, BusyKeysReplacement, persons_coworks, enterprise_revision, Shift_data_f_checks


class TimeSheetPlanFull(forms.Form):
    person = forms.CharField(label='Сотрудник')
    position = forms.CharField(label='Должность')
    shedule = forms.CharField(label='График')

    busy_key1 = forms.CharField(max_length=5)
    busy_key2 = forms.CharField(max_length=5)
    busy_key3 = forms.CharField(max_length=5)
    busy_key4 = forms.CharField(max_length=5)
    busy_key5 = forms.CharField(max_length=5)
    busy_key6 = forms.CharField(max_length=5)
    busy_key7 = forms.CharField(max_length=5)
    busy_key8 = forms.CharField(max_length=5)
    busy_key9 = forms.CharField(max_length=5)
    busy_key10 = forms.CharField(max_length=5)
    busy_key11 = forms.CharField(max_length=5)
    busy_key12 = forms.CharField(max_length=5)
    busy_key13 = forms.CharField(max_length=5)
    busy_key14 = forms.CharField(max_length=5)
    busy_key15 = forms.CharField(max_length=5)
    busy_key16 = forms.CharField(max_length=5)
    busy_key17 = forms.CharField(max_length=5)
    busy_key18 = forms.CharField(max_length=5)
    busy_key19 = forms.CharField(max_length=5)
    busy_key20 = forms.CharField(max_length=5)
    busy_key21 = forms.CharField(max_length=5)
    busy_key22 = forms.CharField(max_length=5)
    busy_key23 = forms.CharField(max_length=5)
    busy_key24 = forms.CharField(max_length=5)
    busy_key25 = forms.CharField(max_length=5)
    busy_key26 = forms.CharField(max_length=5)
    busy_key27 = forms.CharField(max_length=5)
    busy_key28 = forms.CharField(max_length=5)
    busy_key29 = forms.CharField(max_length=5)
    busy_key30 = forms.CharField(max_length=5)
    busy_key31 = forms.CharField(max_length=5)

    hours_all1 = forms.DecimalField()
    hours_all2 = forms.DecimalField()
    hours_all3 = forms.DecimalField()
    hours_all4 = forms.DecimalField()
    hours_all5 = forms.DecimalField()
    hours_all6 = forms.DecimalField()
    hours_all7 = forms.DecimalField()
    hours_all8 = forms.DecimalField()
    hours_all9 = forms.DecimalField()
    hours_all10 = forms.DecimalField()
    hours_all11 = forms.DecimalField()
    hours_all12 = forms.DecimalField()
    hours_all13 = forms.DecimalField()
    hours_all14 = forms.DecimalField()
    hours_all15 = forms.DecimalField()
    hours_all16 = forms.DecimalField()
    hours_all17 = forms.DecimalField()
    hours_all18 = forms.DecimalField()
    hours_all19 = forms.DecimalField()
    hours_all20 = forms.DecimalField()
    hours_all21 = forms.DecimalField()
    hours_all22 = forms.DecimalField()
    hours_all23 = forms.DecimalField()
    hours_all24 = forms.DecimalField()
    hours_all25 = forms.DecimalField()
    hours_all26 = forms.DecimalField()
    hours_all27 = forms.DecimalField()
    hours_all28 = forms.DecimalField()
    hours_all29 = forms.DecimalField()
    hours_all30 = forms.DecimalField()
    hours_all31 = forms.DecimalField()

    #######################
    busy_key_f1 = forms.CharField(max_length=5)
    busy_key_f2 = forms.CharField(max_length=5)
    busy_key_f3 = forms.CharField(max_length=5)
    busy_key_f4 = forms.CharField(max_length=5)
    busy_key_f5 = forms.CharField(max_length=5)
    busy_key_f6 = forms.CharField(max_length=5)
    busy_key_f7 = forms.CharField(max_length=5)
    busy_key_f8 = forms.CharField(max_length=5)
    busy_key_f9 = forms.CharField(max_length=5)
    busy_key_f10 = forms.CharField(max_length=5)
    busy_key_f11 = forms.CharField(max_length=5)
    busy_key_f12 = forms.CharField(max_length=5)
    busy_key_f13 = forms.CharField(max_length=5)
    busy_key_f14 = forms.CharField(max_length=5)
    busy_key_f15 = forms.CharField(max_length=5)
    busy_key_f16 = forms.CharField(max_length=5)
    busy_key_f17 = forms.CharField(max_length=5)
    busy_key_f18 = forms.CharField(max_length=5)
    busy_key_f19 = forms.CharField(max_length=5)
    busy_key_f20 = forms.CharField(max_length=5)
    busy_key_f21 = forms.CharField(max_length=5)
    busy_key_f22 = forms.CharField(max_length=5)
    busy_key_f23 = forms.CharField(max_length=5)
    busy_key_f24 = forms.CharField(max_length=5)
    busy_key_f25 = forms.CharField(max_length=5)
    busy_key_f26 = forms.CharField(max_length=5)
    busy_key_f27 = forms.CharField(max_length=5)
    busy_key_f28 = forms.CharField(max_length=5)
    busy_key_f29 = forms.CharField(max_length=5)
    busy_key_f30 = forms.CharField(max_length=5)
    busy_key_f31 = forms.CharField(max_length=5)

    hours_all_f1 = forms.DecimalField()
    hours_all_f2 = forms.DecimalField()
    hours_all_f3 = forms.DecimalField()
    hours_all_f4 = forms.DecimalField()
    hours_all_f5 = forms.DecimalField()
    hours_all_f6 = forms.DecimalField()
    hours_all_f7 = forms.DecimalField()
    hours_all_f8 = forms.DecimalField()
    hours_all_f9 = forms.DecimalField()
    hours_all_f10 = forms.DecimalField()
    hours_all_f11 = forms.DecimalField()
    hours_all_f12 = forms.DecimalField()
    hours_all_f13 = forms.DecimalField()
    hours_all_f14 = forms.DecimalField()
    hours_all_f15 = forms.DecimalField()
    hours_all_f16 = forms.DecimalField()
    hours_all_f17 = forms.DecimalField()
    hours_all_f18 = forms.DecimalField()
    hours_all_f19 = forms.DecimalField()
    hours_all_f20 = forms.DecimalField()
    hours_all_f21 = forms.DecimalField()
    hours_all_f22 = forms.DecimalField()
    hours_all_f23 = forms.DecimalField()
    hours_all_f24 = forms.DecimalField()
    hours_all_f25 = forms.DecimalField()
    hours_all_f26 = forms.DecimalField()
    hours_all_f27 = forms.DecimalField()
    hours_all_f28 = forms.DecimalField()
    hours_all_f29 = forms.DecimalField()
    hours_all_f30 = forms.DecimalField()
    hours_all_f31 = forms.DecimalField()


class TimeSheet_detail_plan(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TimeSheet_detail_plan, self).__init__(*args, **kwargs)

        query_rep = BusyKeysReplacement.objects.filter(f_key=self.instance.busy_key_guid)
        self.fields['busy_key_guid'].queryset = query_rep

    class Meta:
        model = TimeSheetPlane
        fields = '__all__'


class TimeSheet_detail_fact(forms.ModelForm):
    class Meta:
        model = TimeSheetFact
        fields = '__all__'


class TimeSheet_detail_cowork(forms.ModelForm):
    model = persons_coworks
    class Meta:
        fields = '__all__'


class revisor_detail(forms.ModelForm):

    class Meta:
        model = enterprise_revision
        fields = '__all__'


# class ShiftDataChecksForm(forms.ModelForm):
#     # форма эксперемент
#     class Meta:
#         model = Shift_data_f_checks
#         # fields = ['busy_key_f',
#         #       'busy_key_t',
#         #       ]
#
#     def is_valid(self):
#
#         return True

    # def __init__(self, *args, **kwargs):
    #     super(ShiftDataChecksForm, self).__init__(*args, **kwargs)


# TimeSheet_plan_fact = inlineformset_factory(TimeSheetPlane, TimeSheetFact, fields=('enterprise_guid', 'person_guid', 'dts'))

# TimeSheetPlanFullSet = formset_factory(TimeSheetPlanFull, fields=('busy_key1', 'hours_all_1'), extra=0)
# TimeSheetFormSet_full = formset_factory(TimeSheetPlanFull)

TimeSheetFormSet_full = modelformset_factory(TimeSheetPlane, fields=('busy_key_guid', 'hours_all', 'p_uid'), extra=0)
# TimeSheetFormSet_full = formset_factory(TimeSheet_detail_plan, extra=0)
TimeSheetFormSet_full_fact = modelformset_factory(TimeSheetFact, exclude=(), extra=0)
persons_coworks_day = modelformset_factory(persons_coworks, exclude=(), extra=0)
