import fs from 'node:fs/promises';import assert from 'node:assert/strict';
import {chromium} from '/home/minte/projects/training-apps/apps/agent_harness/node_modules/playwright/index.mjs';
const root=new URL('../../',import.meta.url).pathname,am=JSON.parse(await fs.readFile(root+'frontend/src/i18n/am.json','utf8'));
const config=JSON.parse(await fs.readFile('/home/minte/projects/training-apps/sites/training.localhost/site_config.json','utf8'));
const b=await chromium.launch(),c=await b.newContext({baseURL:'http://127.0.0.1:8081',viewport:{width:1440,height:1000}}),errors=[],checks=[];let pack;
try{
 assert.equal((await c.request.post('/api/method/login',{form:{usr:'church-browser-qa@circle.localhost',pwd:config.church_browser_qa_password}})).status(),200);
 const p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
 for(const route of ['/play/host/content/crowd-compass?lang=am','/play/host/quizzes/new?lang=am']){await p.goto(route);await p.locator(route.includes('/quizzes/') ? 'input.field' : 'h1').first().waitFor();assert.equal(await p.locator('html').getAttribute('lang'),'am');}
 checks.push('Legacy pack and quiz editors open in Amharic without initialization errors');
 await p.goto('/play/create?lang=am');await p.locator('form input[maxlength="100"]').fill('QA የቤተሰብ ምርጫ');
 await p.getByRole('button',{name:am['Save my pack'],exact:true}).click();await p.locator('.gp-notice').waitFor();
 pack=await p.evaluate(async()=>{const r=await fetch('/api/method/quizzly.access.my_packs',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':window.csrf_token},body:'{}'});const j=await r.json();return j.message.find(x=>x.title==='QA የቤተሰብ ምርጫ')?.name;});assert.ok(pack);
 const doc=await p.evaluate(async name=>{const r=await fetch('/api/method/frappe.client.get',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':window.csrf_token},body:JSON.stringify({doctype:'GP Crowd Pack',name})});return(await r.json()).message;},pack);
 assert.equal(doc.content_language,'am');assert.match(doc.prompts[0].prompt_text,/[\u1200-\u137f]/);assert.equal(doc.is_demo,0);
 await p.getByRole('button',{name:'English',exact:true}).click();assert.match(await p.locator('form textarea').inputValue(),/[\u1200-\u137f]/);await p.screenshot({path:root+'docs/localization/evidence/authoring-preserves-content.png'});
 checks.push('Amharic private pack saved with correct language; changing the interface to English preserves authored questions');assert.equal(errors.length,0);console.log(checks.join('\n'));
} catch(e){console.error(e);process.exitCode=1;}finally{if(pack)await fs.writeFile('/tmp/gp-am-pack.json',JSON.stringify([pack]));await fs.writeFile(root+'docs/localization/evidence/authoring-results.json',JSON.stringify({checks,errors,passed:!process.exitCode},null,2));await c.close();await b.close();}
