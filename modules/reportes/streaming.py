import csv
import io


def csv_generator(data_generator):
    csvfile = io.BytesIO()
    csvwriter = csv.writer(csvfile)

    def read_and_flush():
        csvfile.seek(0)
        data = csvfile.read()
        csvfile.seek(0)
        csvfile.truncate()
        return data

    for row in data_generator:
        csvwriter.writerow(row)
        yield read_and_flush()


def csv_stream_response(response, iterator, file_name="xxxx.csv"):

    response.content_type = 'text/csv'
    response.content_disposition = 'attachment;filename="' + file_name + '"'
    response.charset = 'utf8'
    response.content_encoding = 'utf8'
    response.app_iter = csv_generator(iterator)

    return response