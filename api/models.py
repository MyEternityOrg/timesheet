from django.db import models


class PersonalCashes(models.Model):
    data_XMl = models.FileField()


    class Meta:
        abstract = True