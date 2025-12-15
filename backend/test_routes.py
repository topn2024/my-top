#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify registered routes
"""
import app_factory

app = app_factory.create_app('development')

print("Registered routes with 'prompts':")
with app.app_context():
    for rule in app.url_map.iter_rules():
        if 'prompts' in str(rule):
            print(f"  {rule}")
