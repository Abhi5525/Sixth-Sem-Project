import csv
import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Service_Manpower.settings')
django.setup()

from users.models import Province, District, Municipality, Ward


def load_csv_data():
    with open('provinces.csv') as f:
        for row in csv.DictReader(f):
            Province.objects.get_or_create(name = row['name'])

load_csv_data()