
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *


class OCR_NodesSerializer(serializers.ModelSerializer):
    #id = serializers.CharField()
    #gio_hoi_cung = serializers.CharField()
    #gio_bat_dau = serializers.CharField()
    #gio_ket_thuc = serializers.CharField()
    pham_nhan_id = serializers.CharField()
    dieu_tra_vien_id = serializers.CharField()

    class Meta:
        model = OCR_Nodes
        fields = ("ma_so_phien", "ten_phien", "mo_ta", "ngay_hoi_cung", "gio_hoi_cung", "gio_bat_dau", "gio_ket_thuc", "pham_nhan_id", "dieu_tra_vien_id")


