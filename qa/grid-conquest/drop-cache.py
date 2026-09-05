"""Simulate only an inventoried QA board's hot-state loss."""

import os
import sys

import frappe

os.chdir("/home/minte/projects/training-apps/sites")
frappe.init(site="training.localhost")
frappe.connect()
from quizzly.games import engine

name = sys.argv[1]
doc = frappe.get_doc("GP Session", name)
assert doc.host == "church-browser-qa@circle.localhost" and doc.game_key == "grid-conquest"
assert doc.status == "Active"
frappe.cache.delete_value(engine.state_key(name))
print("Removed QA board cache; database snapshot retained")
frappe.destroy()
