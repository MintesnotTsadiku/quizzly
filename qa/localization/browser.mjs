import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {chromium} from '/home/minte/projects/training-apps/apps/agent_harness/node_modules/playwright/index.mjs';
const out=new URL('../../docs/localization/evidence/',import.meta.url).pathname;
const b=await chromium.launch();const errors=[],checks=[];let p;
try{
 const c=await b.newContext({baseURL:'http://127.0.0.1:8081',viewport:{width:1440,height:1000},colorScheme:'light'});p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
 await p.goto('/play/?lang=am');await p.locator('h1').waitFor();await p.evaluate(()=>document.fonts.ready);
 assert.equal(await p.locator('html').getAttribute('lang'),'am');assert.match(await p.locator('h1').innerText(),/[\u1200-\u137f]/);
 await p.screenshot({path:out+'landing-am.png'});
 await p.getByRole('button',{name:'English',exact:true}).click();assert.equal(await p.locator('html').getAttribute('lang'),'en');
 await p.getByRole('button',{name:'አማርኛ',exact:true}).click();await p.goto('/play/explore');await p.locator('.gp-game-card').first().waitFor();assert.equal(await p.locator('html').getAttribute('lang'),'am');
 await p.locator('.gp-game-card').first().waitFor();assert.equal(await p.locator('.gp-game-card').count(),6);
 for(const game of ['common-ground','bluffline','crowd-compass']){
  await p.goto('/play/games/'+game);await p.getByRole('combobox').waitFor();await p.evaluate(()=>document.fonts.ready);
  assert.match(await p.getByRole('combobox').innerText(),/[\u1200-\u137f]/);
  if(game==='common-ground')assert.match(await p.locator('.gp-game-illustration img').getAttribute('src'),/ethiopian-v2/);
  if(game==='bluffline')assert.match(await p.locator('.gp-game-illustration img').getAttribute('src'),/ethiopian-v1/);
  await p.getByRole('combobox').focus();await p.keyboard.press('ArrowDown');await p.getByRole('listbox').waitFor();await p.keyboard.press('End');await p.keyboard.press('Enter');assert.equal(await p.getByRole('listbox').count(),0);
  await p.screenshot({path:out+game+'-am.png'});
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await p.screenshot({path:out+game+'-am-mobile.png'});await p.setViewportSize({width:1440,height:1000});
 }
 checks.push('English/Amharic switch persists across navigation; six curated games; Amharic pack picker with keyboard controls; latest artwork selected; 390px layout fits');
 const result=await p.evaluate(async()=>{const m=await import('/src/i18n/index.js');localStorage.removeItem('gatherplay-language');history.replaceState({},'', '/play/');m.initializeLanguage('am');const site=m.locale.value;m.inheritLanguage('en');const inherited=m.locale.value;m.setLanguage('am');m.inheritLanguage('en');const chosen=m.locale.value;const url=m.languageUrl('/play/join?pin=123456');return{site,inherited,chosen,url,fallback:m.t('My personal pack title'),param:m.t('{count} sec',{count:15})};});
 assert.deepEqual(result,{site:'am',inherited:'en',chosen:'am',url:'/play/join?pin=123456&lang=am',fallback:'My personal pack title',param:'15 ሰከንድ'});
 checks.push('Site default, trusted-parent inheritance, explicit preference precedence, invite links, parameters and untranslated user-copy fallback');
 await p.goto('/play/join?lang=am');await p.locator('form').waitFor();await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await p.screenshot({path:out+'join-am-mobile.png'});
 await p.goto('/play/access?lang=am');await p.locator('h1').waitFor();await p.screenshot({path:out+'access-am-mobile.png'});checks.push('Amharic join and access pages render on phones');
 console.log(checks.join('\n'));assert.equal(errors.length,0);
} catch(e){console.error(e);process.exitCode=1;if(p)await p.screenshot({path:out+'browser-failure.png'});}finally{await fs.writeFile(out+'browser-results.json',JSON.stringify({checks,errors,passed:!process.exitCode},null,2));await b.close();}
