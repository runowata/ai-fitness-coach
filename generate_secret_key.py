#!/usr/bin/env python
"""
Utility script to generate Django SECRET_KEY
"""

from django.core.management.utils import get_random_secret_key

if __name__ == '__main__':
    print("Generated SECRET_KEY:")
    print(get_random_secret_key())