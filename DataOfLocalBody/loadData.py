import csv
import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Service_Manpower.settings')
django.setup()

from users.models import Province, District, Municipality


def load_csv_data():
    with open('provinces.csv') as f:
        for row in csv.DictReader(f):
            Province.objects.get_or_create(name = row['name'])

    with open('districts1.csv') as f:
        for row in csv.DictReader(f):
            District.objects.get_or_create(name = row['name'], province_id = row['province_id'])

    with open('municipalities.csv') as f:
        for row in csv.DictReader(f):
            Municipality.objects.get_or_create(name = row['name'], district_id = row['district_id'], ward = row['wards'])

load_csv_data()