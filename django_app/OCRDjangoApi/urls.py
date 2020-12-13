"""OCRDjangoApi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls import url

from ocrapi.views import ocr_api_view, ocr_form_view, callback_api_view, ftp_api_view


urlpatterns = [
    re_path(r'^jet/', include('jet.urls', 'jet')),
    path('admin/', admin.site.urls),
    url(r'^ocr/', ocr_api_view, name='ocr_api_view'),
    url(r'^$', ocr_form_view, name='ocr_form_view'),
    url(r'^api_fake_ftp/', ftp_api_view, name='ftp_api_view'),
    url(r'^api/api-token-auth', ftp_api_view, name='ftp_api_view'),
    url(r'^api/', callback_api_view, name='callback_api_view'),
    url(r'^api-token-auth', ftp_api_view, name='ftp_api_view'),
]

