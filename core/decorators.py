from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if getattr(request.user, 'role', None) != 'ADMIN':
            messages.error(request, 'Admin access required.')
            return HttpResponseForbidden('Admin access required.')
        return view_func(request, *args, **kwargs)
    return _wrapped


def user_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if getattr(request.user, 'role', None) != 'USER':
            messages.error(request, 'User access required.')
            return HttpResponseForbidden('User access required.')
        return view_func(request, *args, **kwargs)
    return _wrapped
