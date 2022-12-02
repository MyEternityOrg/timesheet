from io import BytesIO, StringIO

from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa

import sys
import locale

from collections import namedtuple


def render_to_pdf(template_src, context_dict={}):
    print(sys.getfilesystemencoding())
    print(locale.getpreferredencoding())

    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(StringIO(html), dest=result, encoding='UTF-8', debug=1)
    if not pdf.err:
        # return HttpResponse(result.getvalue(), content_type='application/pdf')
        return HttpResponse(result.getvalue())

    return None


def dict_fetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def named_tuple_fetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

