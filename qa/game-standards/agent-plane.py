import os, json
import frappe
os.chdir('/home/minte/projects/training-apps/sites')
frappe.init(site='training.localhost', sites_path='/home/minte/projects/training-apps/sites')
frappe.connect()
frappe.set_user('church-browser-qa@circle.localhost')
from agent_plane.runtime.tools import browser_tools as browser
r = browser.browser_start_session(base_url='http://127.0.0.1:8081', artifact_root='/tmp/gp-arc-after', timeout_ms=20000, options={'viewport': {'width': 1440, 'height': 1000}})
assert r.get('ok'), r.get('error')
sid = r['session_id']
print(json.dumps({'run': r.get('browser_session_run')}), flush=True)
frappe.db.commit()
try:
    for action in [{'action':'open_url','url':'/play/games/crowd-compass','wait_until':'domcontentloaded'}, {'action':'wait_for','selector':'button[role="combobox"]'},  {'action':'screenshot','name':'after-crowd-progression.png','full_page':True}, {'action':'get_console_errors'}, {'action':'get_network_errors'}]:
        result = browser.browser_session_action(sid, action)
        print(json.dumps({'action': action['action'], 'ok': result.get('ok'), 'artifacts': (result.get('result') or {}).get('artifacts'), 'errors': (result.get('result') or {}).get('value') if action['action'].startswith('get_') else None}, default=str), flush=True)
        assert result.get('ok'), result.get('error')
        frappe.db.commit()
finally:
    browser.browser_close_session(sid)
    frappe.db.commit()
    frappe.destroy()
