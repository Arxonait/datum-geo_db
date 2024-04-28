from django.contrib import admin

from geo_db.models import Country


class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)


admin.site.register(Country, CountryAdmin)
