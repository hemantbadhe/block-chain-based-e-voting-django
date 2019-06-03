from django.contrib import admin
from django.apps import apps

# for model in apps.get_app_config('simulation').models.values():
from simulation.models import *

admin.site.register(Vote)
admin.site.register(Block)
admin.site.register(VoteBackup)
