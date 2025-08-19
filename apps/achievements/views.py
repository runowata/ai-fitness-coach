from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def achievements_list(request):
    """List user achievements"""
    context = {}
    return render(request, 'achievements/achievements_list.html', context)