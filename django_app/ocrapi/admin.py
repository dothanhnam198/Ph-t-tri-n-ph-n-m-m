

from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from .models import *

# Register your models her

@admin.register(OCR_Nodes)
class OCR_NodesAdmin(admin.ModelAdmin):
    list_display = ("node_name", "url_api", "url_callback", "api_user", "api_pwd", "is_master", "is_active", ) # custom_column
    list_filter = (
        #('categories', admin.RelatedFieldListFilter),  # custom filter box theo list REF
    )
    search_fields = ["node_name", "url_api", "url_callback", "api_user", "api_pwd", "is_master", "is_active", ]

    none_type = type(None)
    date_hierarchy = None  #  filter cho các đối tượng DATE hoặc DATETIME

    def custom_column(self, obj):  # custom_column
        #return obj.categories.name
        return ""
    custom_column.short_description = _('Categories')  # Title trong list
    custom_column.admin_order_field = 'category__name'  # Order ref categories.name

    def get_list_display(self, request): # override
        if OCR_Nodes.objects.all().count() > 0:  # 2
            self.date_hierarchy = None # 'created_at'
        else:
            self.date_hierarchy = None

        return super(OCR_NodesAdmin, self).get_list_display(request)

    def get_form(self, request, obj=None, **kwargs): # override form new / edit
        request.obj = obj

        if isinstance(obj, self.none_type) is True:
            self.exclude = None # ("sort_order", )
            pass
        else:
            self.exclude = None
            pass

        return super(OCR_NodesAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # override
        if db_field.name == 'parent_category':
            if not isinstance(request.obj, self.none_type):
                #kwargs['queryset'] = OCR_Nodes.objects.filter(~Q(slug__exact=request.obj.slug), parent_category__isnull=True, slug__exact=request.obj.slug)
                pass
            elif request.method == 'GET':
                #kwargs['queryset'] = OCR_Nodes.objects.filter(parent_category__isnull=True)
                pass

        return super(OCR_NodesAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(OCR_Config)
class OCR_ConfigAdmin(admin.ModelAdmin):
    list_display = ("ftp_ip", "ftp_port", "ftp_user", "ftp_pwd", "api_user", "api_pwd", "is_public_ftp") # custom_column
    list_filter = (
        #('categories', admin.RelatedFieldListFilter),  # custom filter box theo list REF
    )
    search_fields = ["ftp_ip", "ftp_port", "ftp_user", "ftp_pwd", "api_user", "api_pwd", ]

    none_type = type(None)
    date_hierarchy = None  #  filter cho các đối tượng DATE hoặc DATETIME

    def custom_column(self, obj):  # custom_column
        #return obj.categories.name
        return ""
    custom_column.short_description = _('Categories')  # Title trong list
    custom_column.admin_order_field = 'category__name'  # Order ref categories.name

    def get_list_display(self, request): # override
        if OCR_Config.objects.all().count() > 0:  # 2
            self.date_hierarchy = None # 'created_at'
        else:
            self.date_hierarchy = None

        return super(OCR_ConfigAdmin, self).get_list_display(request)

    def get_form(self, request, obj=None, **kwargs): # override form new / edit
        request.obj = obj

        if isinstance(obj, self.none_type) is True:
            self.exclude = None # ("sort_order", )
            pass
        else:
            self.exclude = None
            pass

        return super(OCR_ConfigAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # override
        if db_field.name == 'parent_category':
            if not isinstance(request.obj, self.none_type):
                #kwargs['queryset'] = OCR_Config.objects.filter(~Q(slug__exact=request.obj.slug), parent_category__isnull=True, slug__exact=request.obj.slug)
                pass
            elif request.method == 'GET':
                #kwargs['queryset'] = OCR_Config.objects.filter(parent_category__isnull=True)
                pass

        return super(OCR_ConfigAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(OCR_Request)
class OCR_RequestAdmin(admin.ModelAdmin):
    list_display = ("config_ocr", "ftp_path", "file_ocr", ) # custom_column
    list_filter = (
        #('categories', admin.RelatedFieldListFilter),  # custom filter box theo list REF
    )
    search_fields = ["config_ocr", "ftp_path", "file_ocr", ]

    none_type = type(None)
    date_hierarchy = None  #  filter cho các đối tượng DATE hoặc DATETIME

    def custom_column(self, obj):  # custom_column
        #return obj.categories.name
        return ""
    custom_column.short_description = _('Categories')  # Title trong list
    custom_column.admin_order_field = 'category__name'  # Order ref categories.name

    def get_list_display(self, request): # override
        if OCR_Request.objects.all().count() > 0:  # 2
            self.date_hierarchy = None # 'created_at'
        else:
            self.date_hierarchy = None

        return super(OCR_RequestAdmin, self).get_list_display(request)

    def get_form(self, request, obj=None, **kwargs): # override form new / edit
        request.obj = obj

        if isinstance(obj, self.none_type) is True:
            self.exclude = None # ("sort_order", )
            pass
        else:
            self.exclude = None
            pass

        return super(OCR_RequestAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # override
        if db_field.name == 'parent_category':
            if not isinstance(request.obj, self.none_type):
                #kwargs['queryset'] = OCR_Request.objects.filter(~Q(slug__exact=request.obj.slug), parent_category__isnull=True, slug__exact=request.obj.slug)
                pass
            elif request.method == 'GET':
                #kwargs['queryset'] = OCR_Request.objects.filter(parent_category__isnull=True)
                pass

        return super(OCR_RequestAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(OCR_NodeRequest)
class OCR_NodeRequestAdmin(admin.ModelAdmin):
    list_display = ("node_id", "request_id", "file_ocr_input", "file_ocr_output", "file_ocr_pages", "status", "error_message", "access_time", ) # custom_column
    list_filter = (
        #('categories', admin.RelatedFieldListFilter),  # custom filter box theo list REF
    )
    search_fields = ["node_id", "request_id", "file_ocr_input", "file_ocr_output", "file_ocr_pages", "status", "error_message", "access_time", ]

    none_type = type(None)
    date_hierarchy = None  #  filter cho các đối tượng DATE hoặc DATETIME

    def custom_column(self, obj):  # custom_column
        #return obj.categories.name
        return ""
    custom_column.short_description = _('Categories')  # Title trong list
    custom_column.admin_order_field = 'category__name'  # Order ref categories.name

    def get_list_display(self, request): # override
        if OCR_NodeRequest.objects.all().count() > 0:  # 2
            self.date_hierarchy = None # 'created_at'
        else:
            self.date_hierarchy = None

        return super(OCR_NodeRequestAdmin, self).get_list_display(request)

    def get_form(self, request, obj=None, **kwargs): # override form new / edit
        request.obj = obj

        if isinstance(obj, self.none_type) is True:
            self.exclude = None # ("sort_order", )
            pass
        else:
            self.exclude = None
            pass

        return super(OCR_NodeRequestAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # override
        if db_field.name == 'parent_category':
            if not isinstance(request.obj, self.none_type):
                #kwargs['queryset'] = OCR_NodeRequest.objects.filter(~Q(slug__exact=request.obj.slug), parent_category__isnull=True, slug__exact=request.obj.slug)
                pass
            elif request.method == 'GET':
                #kwargs['queryset'] = OCR_NodeRequest.objects.filter(parent_category__isnull=True)
                pass

        return super(OCR_NodeRequestAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(OCR_Folder)
class OCR_FolderAdmin(admin.ModelAdmin):
    list_display = ("client_info", "folder", "create_time",)  # custom_column
    list_filter = ("client_info",
                   # ('categories', admin.RelatedFieldListFilter),  # custom filter box theo list REF
                   )
    search_fields = ["folder", "create_time", ]

    none_type = type(None)
    date_hierarchy = None  # filter cho các đối tượng DATE hoặc DATETIME

    def custom_column(self, obj):  # custom_column
        # return obj.categories.name
        return ""

    custom_column.short_description = _('Categories')  # Title trong list
    custom_column.admin_order_field = 'category__name'  # Order ref categories.name

    def get_list_display(self, request):  # override
        if OCR_Folder.objects.all().count() > 0:  # 2
            self.date_hierarchy = None  # 'created_at'
        else:
            self.date_hierarchy = None

        return super(OCR_FolderAdmin, self).get_list_display(request)

    def get_form(self, request, obj=None, **kwargs):  # override form new / edit
        request.obj = obj

        if isinstance(obj, self.none_type) is True:
            self.exclude = None  # ("sort_order", )
            pass
        else:
            self.exclude = None
            pass

        return super(OCR_FolderAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):  # override
        if db_field.name == 'parent_category':
            if not isinstance(request.obj, self.none_type):
                # kwargs['queryset'] = OCR_Folder.objects.filter(~Q(slug__exact=request.obj.slug), parent_category__isnull=True, slug__exact=request.obj.slug)
                pass
            elif request.method == 'GET':
                # kwargs['queryset'] = OCR_Folder.objects.filter(parent_category__isnull=True)
                pass

        return super(OCR_FolderAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)