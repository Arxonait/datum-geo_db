from django.contrib import admin

from geo_db.models import Country, City, Photo, Capital


class PhotoInline(admin.TabularInline):
    fk_name = 'city'
    model = Photo


class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)


class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country")
    list_display_links = ("id", "name")
    inlines = [PhotoInline, ]
    search_fields = ("name",)


class CapitalAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)


admin.site.register(Country, CountryAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Capital, CapitalAdmin)

