import io

from django.http.response import HttpResponse

from xlsxwriter.workbook import Workbook


def your_view():

    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'Hello, world!')
    workbook.close()
    output.write('hello')
    output.seek(0)

    response = HttpResponse(output.read(), content_type="text/csv")
    response['Content-Disposition'] = "attachment; filename=test.csv"

    return response

your_view()