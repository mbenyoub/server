from django.http import HttpResponse

from xlsxwriter.workbook import Workbook
import StringIO

def your_view():
    # your view logic here

    # create a workbook in memory
    output = StringIO.StringIO()

    book = Workbook(output)
    sheet = book.add_worksheet('test')
    sheet.write(0, 0, 'Hello, world!')
    book.close()

    # construct response
    output.seek(0)
    response = HttpResponse(output.read(),content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=test.xlsx"

    return response

your_view()