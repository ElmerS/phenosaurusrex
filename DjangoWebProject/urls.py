"""
Definition of urls for DjangoWebProject.
"""
from datetime import datetime
from django.conf.urls import url, handler400, handler403, handler404, handler500
from uniqueref.generalforms.login import BootstrapAuthenticationForm
import uniqueref.views as aviews
from django.contrib.auth import views
from django.urls import reverse_lazy

from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)

# Serve static files during development
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.contrib import admin
admin.autodiscover()

admin.site.site_header = 'Phenosaurus management tool'

handler400 = 'uniqueref.views.bad_request'
handler403 = 'uniqueref.views.permission_denied'
handler404 = 'uniqueref.views.page_not_found'
handler500 = 'uniqueref.views.server_error'

urlpatterns = [
    # Account editing form
    url(r'^edit_account/$', aviews.edit_account, name='edit_account'),

    # Change password forms
    url(r'^password_change/$', PasswordChangeView.as_view(template_name='accounts/password_change_form.html'),
        name='password_change'),
    url(r'^password_change/done/$', PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done'),

    # Password reset views
    url(r'^password_reset/$', PasswordResetView.as_view(template_name='accounts/password_reset_form.html'),
        name='password_reset'),
    url(r'^password_reset/done/$', PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
        name='password_reset_confirm'),
    url(r'^reset/done/$', PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete'),

    # Landing page
    url(r'^$', aviews.home, name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^contact$', aviews.contact, name='contact'),
    url(r'^about', aviews.about, name='about'),
    url(r'^uniqueref/', include('uniqueref.urls')),
    url(r'^login/$',
        views.login,
        {
            'template_name': 'uniqueref/account/login.html',
            'authentication_form': BootstrapAuthenticationForm,
            'extra_context':
            {
                'title':'Log in',
               'year':datetime.now().year,
            }
        },
        name='login'),
    url(r'^logout$', LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    # Url patterns for password change and reset, see https://docs.djangoproject.com/en/1.10/topics/auth/default/
    url('^', include('uniqueref.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
