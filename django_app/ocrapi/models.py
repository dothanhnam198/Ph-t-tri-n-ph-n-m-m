
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.utils.text import slugify
from datetime import date
#from __future__ import unicode_literals
from django.conf import settings

from django.db import models
from django.utils.encoding import smart_text as smart_unicode
from django.utils.translation import ugettext_lazy as _

from json import JSONEncoder
import json

# Create models here.

# Create models here.


class OCR_Nodes(models.Model):

    node_name = models.CharField(max_length=2000, verbose_name=_("Tên máy API OCR"))
    #slug = models.SlugField(max_length=254, unique=True, blank=True, editable=False)
    url_api = models.CharField(max_length=2000, verbose_name=_("Link API OCR"))
    url_callback = models.CharField(blank=True, null=True, max_length=2000, verbose_name=_("Link Callback của API OCR Master"))
    api_user = models.CharField(max_length=50, verbose_name=_("Tài khoản đăng nhập API"))
    api_pwd = models.CharField(max_length=50, verbose_name=_("Mật khẩu"))
    is_master = models.BooleanField(blank=True, null=True, default=0, verbose_name=_("Là API OCR Master"))
    is_active = models.BooleanField(blank=True, null=True, default=0, verbose_name=_("Đang hoạt động"))
    time_avg_page = models.DecimalField(blank=True, null=True, default=0, max_digits=5, decimal_places=2, verbose_name=_("Thời gian giây trung bình 1 trang"))
    waiting_page = models.IntegerField(blank=True, null=True, default=0, verbose_name=_("Số trang chờ xử lý"))
    cpu_no = models.IntegerField(blank=True, null=True, default=0, verbose_name=_("Số CPU cores"))


    def default(self, object):
        if isinstance(object, OCR_Nodes):
            return object.__dict__
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)

    def __str__(self):
        if self.node_name is None:
            return ""
        else:
            return self.node_name

    @staticmethod
    def extra_filters(obj):
        #if not obj.parent_category:
        #    return {'parent_category__isnull': True}
        #return {'parent_category': obj.parent_category}
        pass

    def save(self, *args, **kwargs):
        #self.slug = slugify(self.node_name)

        super(OCR_Nodes, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return 'node_name'

    class Meta:
        verbose_name = _('Các Node chạy API OCR')
        verbose_name_plural = _('Các Node chạy API OCR')
        #ordering = ['sort_order']
        #get_latest_by = 'created_at'



class OCR_Config(models.Model):

    ftp_ip = models.CharField(max_length=50, verbose_name=_("IP của FTP"))
    ftp_port = models.IntegerField(default=0, verbose_name=_("Port của FTP"))
    ftp_user = models.CharField(max_length=50, verbose_name=_("Tài khoản đăng nhập FTP"))
    ftp_pwd = models.CharField(max_length=50, verbose_name=_("Mật khẩu"))
    api_user = models.CharField(max_length=50, verbose_name=_("Tài khoản đăng nhập API"))
    api_pwd = models.CharField(max_length=50, verbose_name=_("Mật khẩu"))
    is_public_ftp = models.BooleanField(blank=True, null=True, default=0, verbose_name=_("La FTP public"))

    def default(self, object):
        if isinstance(object, OCR_Config):
            return object.__dict__
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)

    def __str__(self):
        if self.ftp_ip is None:
            return ""
        else:
            return self.ftp_ip

    @staticmethod
    def extra_filters(obj):
        #if not obj.parent_category:
        #    return {'parent_category__isnull': True}
        #return {'parent_category': obj.parent_category}
        pass

    def save(self, *args, **kwargs):
        #self.slug = slugify(self.node_name)

        super(OCR_Config, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return 'ftp_ip'

    class Meta:
        verbose_name = _('Cấu hình chung')
        verbose_name_plural = _('Cấu hình chung')
        #ordering = ['sort_order']
        #get_latest_by = 'created_at'



class OCR_Request(models.Model):

    config_ocr = models.TextField(verbose_name=_("Nội dung cấu hình OCR"))
    ftp_path = models.CharField(max_length=2000, verbose_name=_("Thư mục FTP"))
    file_ocr = models.CharField(max_length=2000, verbose_name=_("File yêu cầu OCR gốc"))

    def default(self, object):
        if isinstance(object, OCR_Request):
            return object.__dict__
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)

    def __str__(self):
        if self.file_ocr is None:
            return ""
        else:
            return self.file_ocr

    @staticmethod
    def extra_filters(obj):
        #if not obj.parent_category:
        #    return {'parent_category__isnull': True}
        #return {'parent_category': obj.parent_category}
        pass

    def save(self, *args, **kwargs):
        #self.slug = slugify(self.node_name)

        super(OCR_Request, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return 'file_ocr'

    class Meta:
        verbose_name = _('Lịch sử yêu cầu OCR')
        verbose_name_plural = _('Lịch sử yêu cầu OCR')
        #ordering = ['sort_order']
        #get_latest_by = 'created_at'



class OCR_NodeRequest(models.Model):

    node_id = models.ForeignKey(OCR_Nodes, on_delete=models.CASCADE, null=True, verbose_name=_("Node API OCR thực hiện"))
    request_id = models.ForeignKey(OCR_Request, on_delete=models.CASCADE, null=True, verbose_name=_("Yêu cầu OCR"))
    file_ocr_input = models.CharField(max_length=2000, verbose_name=_("File OCR đầu vào"))
    file_ocr_output = models.CharField(max_length=2000, verbose_name=_("File OCR đầu ra"))
    file_ocr_pages = models.IntegerField(default=0, verbose_name=_("Tổng số trang"))
    file_ocr_page_start = models.IntegerField(default=0, verbose_name=_("Số trang bat dau"))
    file_ocr_page_size = models.IntegerField(default=0, verbose_name=_("Số trang size"))
    status = models.IntegerField(blank=True, null=True, default=0, verbose_name=_("Trạng thái"))
    error_message = models.TextField(blank=True, null=True, verbose_name=_("Thông tin lỗi"))
    access_time = models.DateField(blank=True, null=True, verbose_name=_("Thời gian xử lý"))  # , auto_now_add=True)

    def default(self, object):
        if isinstance(object, OCR_NodeRequest):
            return object.__dict__
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)

    def __str__(self):
        if self.file_ocr_input is None:
            return ""
        else:
            return self.file_ocr_input

    @staticmethod
    def extra_filters(obj):
        #if not obj.parent_category:
        #    return {'parent_category__isnull': True}
        #return {'parent_category': obj.parent_category}
        pass

    def save(self, *args, **kwargs):
        #self.slug = slugify(self.node_name)

        super(OCR_NodeRequest, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return 'file_ocr_input'

    class Meta:
        verbose_name = _('Xử lý OCR song song')
        verbose_name_plural = _('Xử lý OCR song song')
        #ordering = ['sort_order']
        #get_latest_by = 'created_at'


class OCR_Folder(models.Model):

    client_info = models.TextField(blank=True, null=True, verbose_name=_("Thông tin client"))
    folder = models.TextField(max_length=1000, verbose_name=_("Đường dẫn làm việc"))
    create_time = models.DateField(blank=True, null=True, verbose_name=_("Thời gian khởi tạo")) # , auto_now_add=True)


    def default(self, object):
        if isinstance(object, OCR_Folder):
            return object.__dict__
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)

    def __str__(self):
        if self.folder is None:
            return ""
        else:
            return self.folder

    @staticmethod
    def extra_filters(obj):
        #if not obj.parent_category:
        #    return {'parent_category__isnull': True}
        #return {'parent_category': obj.parent_category}
        pass

    def save(self, *args, **kwargs):
        #self.slug = slugify(self.node_name)

        super(OCR_Folder, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return 'node_name'

    class Meta:
        verbose_name = _('Lưu thư mục làm việc tạm của user')
        verbose_name_plural = _('Lưu thư mục làm việc tạm của user')
        #ordering = ['sort_order']
        #get_latest_by = 'created_at'
