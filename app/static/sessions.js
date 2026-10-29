(()=>{'use strict';
// Practice Sessions: pick a job, press Start, practise real questions with model answers.
// No resume, no login, no AI calls: all content comes from /static/practice-pack.json (also works offline).
const $=id=>document.getElementById(id);
const STYLE=`body[data-view=sessions] .layout{display:none}#sessRoot{display:none}body[data-view=sessions] #sessRoot{display:block}
#sessRoot .card{margin:12px 0}#sessRoot h2{margin:0 0 4px;font-size:22px}#sessRoot h3{margin:16px 0 8px;font-size:16px;color:var(--mute);font-weight:700;text-transform:none}
#sessRoot .rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
#sessRoot .rbtn{display:block;text-align:left;margin:0;width:100%;min-height:64px;background:var(--card2);color:var(--ink);border:1px solid var(--line);box-shadow:none;padding:12px 14px;font-weight:600}
#sessRoot .rbtn small{display:block;color:var(--mute);font-weight:400;font-size:13px;margin-top:2px}
#sessRoot .rbtn.on{border-color:var(--acc);box-shadow:0 0 0 2px rgba(118,185,0,.35);background:rgba(118,185,0,.1)}
#sessRoot .rbtn:hover:not(:disabled){transform:none;border-color:var(--acc2)}
#sessRoot input[type=text]{width:100%;margin:8px 0 4px}
#sessRoot .startbar{position:sticky;bottom:0;z-index:6;margin:14px -4px 0;padding:10px 4px calc(10px + env(safe-area-inset-bottom));background:linear-gradient(180deg,rgba(11,16,32,0),rgba(11,16,32,.96) 28%)}
#sessRoot .startbar button{width:100%;margin:0;font-size:18px;padding:16px}
#sessRoot .qtext{font-size:20px;line-height:1.4;margin:10px 0 12px;font-weight:700}
#sessRoot .sbar{height:8px;border-radius:99px;background:var(--card2);border:1px solid var(--line);overflow:hidden;margin:8px 0}
#sessRoot .sbar i{display:block;height:100%;background:linear-gradient(90deg,#8fd400,#6ba800)}
#sessRoot .ans{border-left:4px solid var(--acc);background:var(--card2);border-radius:12px;padding:12px 14px;margin:12px 0}
#sessRoot .ans.look{border-left-color:var(--acc2)}#sessRoot .ans.hi{border-left-color:var(--warn)}
#sessRoot .ans b{display:block;margin-bottom:4px;font-size:14px;color:var(--mute)}#sessRoot .ans p{margin:0;white-space:pre-wrap}
#sessRoot .row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}#sessRoot .row button{margin:6px 8px 0 0;min-height:48px}
#sessRoot textarea{width:100%;min-height:96px;margin-top:6px}
#sessRoot .opts{display:grid;gap:6px;margin-top:8px}#sessRoot .chips button{min-height:44px}
#sessRoot .big{font-size:17px;padding:14px 22px}#sessRoot .mine{background:var(--card2);border:1px dashed var(--line);border-radius:12px;padding:10px 12px;margin:10px 0}
@media(max-width:560px){#sessRoot .qtext{font-size:18px}#sessRoot .row button{flex:1 1 44%}}`;
function h(tag,attrs,...kids){const e=document.createElement(tag);for(const k in(attrs||{})){const v=attrs[k];if(v==null||v===false)continue;if(k==='class')e.className=v;else if(k.startsWith('on'))e[k]=v;else e.setAttribute(k,v===true?'':v)}
  for(const c of kids.flat()){if(c==null||c===false)continue;e.append(c.nodeType?c:document.createTextNode(String(c)))}return e}
const LV={easy:0,medium:1,hard:2},LVN={easy:'Easy',medium:'Medium',hard:'Hard'},TYN={technical:'Technical',behavioral:'Behavioural',scenario:'Scenario'};
let PACK=null,loadErr='',S={role:null,fl:'all',ft:'all',shuffle:false,list:[],i:0,st:{},q:''};
const KEY_ROLE='ip_sess_role',KEY_MARK='ip_sess_marks';
const lsGet=(k,d)=>{try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}};
const lsSet=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
let marks=lsGet(KEY_MARK,{});if(!marks||typeof marks!=='object')marks={};
const root=()=>$('sessRoot');
async function load(){if(PACK)return PACK;
  const r=await fetch('/static/practice-pack.json');if(!r.ok)throw new Error('The practice questions could not be loaded. Check your internet and try again.');
  const p=await r.json();if(!p||!Array.isArray(p.roles)||!p.qs)throw new Error('The practice questions could not be read. Please reload the page.');PACK=p;return p}
const roleById=id=>PACK.roles.find(r=>r.id===id);
const Q=id=>Object.assign({id},PACK.qs[id]);
function roleQs(r){return r.qs.map(Q)}
function show(node){const r=root();if(!r)return;r.replaceChildren(node);}
// ---------- picker
function matches(r,q){q=q.trim().toLowerCase();if(!q)return true;const hay=(r.name+' '+r.blurb+' '+r.keys).toLowerCase();return q.split(/\s+/).every(w=>hay.includes(w))}
function picker(){
  const wrap=h('div',{});
  wrap.append(h('div',{class:'card'},h('h2',{},'Practice Sessions'),
    h('p',{class:'note',style:'margin:4px 0 0'},'Pick the job you want to apply for, press Start, and practise the questions that are asked for that job. Every question has a model answer and what interviewers look for. No resume, no login, free.')));
  const search=h('input',{type:'text',inputmode:'search',id:'sessSearch',placeholder:'Search a job, e.g. receptionist, data entry, java',maxlength:'60',autocomplete:'off','aria-label':'Search jobs',value:S.q});
  const list=h('div',{id:'sessList'});const startHolder=h('div',{id:'sessStart'});
  const draw=()=>{list.replaceChildren();let any=false;
    for(const g of PACK.groups){const rs=PACK.roles.filter(r=>r.group===g.id&&matches(r,S.q));if(!rs.length)continue;any=true;
      list.append(h('h3',{},g.name),h('div',{class:'rgrid'},rs.map(r=>h('button',{type:'button',class:'rbtn'+(S.role===r.id?' on':''),'aria-pressed':S.role===r.id?'true':'false','data-role':r.id,onclick:()=>{if(S.role!==r.id){S.fl='all';S.ft='all'}S.role=r.id;lsSet(KEY_ROLE,r.id);draw();drawStart();const sb=$('sessStartBtn');if(sb&&sb.scrollIntoView)sb.scrollIntoView({block:'nearest',behavior:'smooth'})}},r.name,h('small',{},r.qs.length+' questions - '+r.blurb)))))}
    if(!any)list.append(h('p',{class:'note'},'No job matches "'+S.q.trim()+'". Try a simpler word, for example "hotel", "sales", "java" or "accounts".'));};
  const drawStart=()=>{startHolder.replaceChildren();const r=S.role&&roleById(S.role);if(!r)return;
    const lvls=[...new Set(roleQs(r).map(q=>q.l))].sort((a,b)=>LV[a]-LV[b]),types=[...new Set(roleQs(r).map(q=>q.t))];
    const chip=(label,on,fn)=>h('button',{type:'button',class:on?'on':'','aria-pressed':on?'true':'false',onclick:fn},label);
    const opts=h('details',{class:'card'},h('summary',{style:'cursor:pointer;min-height:44px;display:flex;align-items:center'},'Options (optional)'),
      h('div',{class:'opts'},h('div',{class:'note'},'Level'),h('div',{class:'chips'},[chip('All levels',S.fl==='all',()=>{S.fl='all';drawStart()}),...lvls.map(l=>chip(LVN[l],S.fl===l,()=>{S.fl=l;drawStart()}))]),
        h('div',{class:'note'},'Type'),h('div',{class:'chips'},[chip('All types',S.ft==='all',()=>{S.ft='all';drawStart()}),...types.map(t=>chip(TYN[t]||t,S.ft===t,()=>{S.ft=t;drawStart()}))]),
        h('div',{class:'note'},'Order'),h('div',{class:'chips'},[chip('Easy to hard',!S.shuffle,()=>{S.shuffle=false;drawStart()}),chip('Shuffle',S.shuffle,()=>{S.shuffle=true;drawStart()})])));
    if(S.open)opts.open=true;opts.addEventListener('toggle',()=>{S.open=opts.open});
    const n=filtered(r).length;
    startHolder.append(opts,h('div',{class:'startbar'},h('button',{type:'button',id:'sessStartBtn',class:'big',disabled:n?null:true,onclick:()=>start(r)},n?'Start: '+r.name+' ('+n+' questions)':'No questions match these options'),
      n?null:h('p',{class:'err',role:'alert'},'Choose All levels or All types to see questions.')))};
  search.oninput=()=>{S.q=search.value;draw()};
  wrap.append(h('div',{class:'card'},search),list,startHolder);
  const saved=lsGet(KEY_ROLE,null);if(!S.role&&saved&&roleById(saved))S.role=saved;
  draw();drawStart();show(wrap);
}
function filtered(r){return roleQs(r).filter(q=>(S.fl==='all'||q.l===S.fl)&&(S.ft==='all'||q.t===S.ft))}
function order(qs){const a=qs.slice();if(S.shuffle){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
  const about=x=>/^tell me about yourself/i.test(x.q)?0:1;return a.map((q,i)=>[q,i]).sort((x,y)=>about(x[0])-about(y[0])||LV[x[0].l]-LV[y[0].l]||x[1]-y[1]).map(x=>x[0])}
function start(r){S.list=order(filtered(r));S.i=0;S.st={};if(!S.list.length)return;card()}
// ---------- practice
const SR=window.SpeechRecognition||window.webkitSpeechRecognition,TTS=window.speechSynthesis;
let rec=null;
function stopMic(){if(rec){try{rec.stop()}catch(e){}rec=null}}
const SPK_FILLERS=['um','uh','erm','you know','i mean','basically','actually','like','sort of','kind of','so yeah','right'];
function spkAnalyze(text,ms){const words=(text.toLowerCase().match(/[a-z']+/g))||[];const n=words.length;
  if(!n)return null;const joined=' '+words.join(' ')+' ';const found={};
  SPK_FILLERS.forEach(f=>{let k;if(f.indexOf(' ')>-1){k=(joined.split(' '+f+' ').length-1)}else k=words.filter(w=>w===f).length;if(k)found[f]=k});
  const ft=Object.values(found).reduce((a,b)=>a+b,0);
  const wpm=(ms>=5000&&n>=8)?Math.round(n/(ms/60000)):null;
  return {wc:n,ft,fillers:found,wpm}}
function spkTip(m){if(!m)return '';
  if(!m.wpm)return 'Speak a little longer (at least 5 seconds) to get a pace score.';
  let t=m.wpm<120?'A bit slow - aim for 120 to 160 words per minute.':(m.wpm>160?'A bit fast - slow down toward 120 to 160 words per minute.':'Good pace (120 to 160 words per minute).');
  if(m.ft>0)t+=' Try to cut filler words like '+Object.keys(m.fillers).slice(0,3).map(f=>'"'+f+'"').join(', ')+'.';
  return t}
function speak(text){if(!TTS)return;TTS.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='en-IN';u.rate=1;TTS.speak(u)}
function card(){stopMic();if(TTS)TTS.cancel();const r=roleById(S.role),q=S.list[S.i],n=S.list.length;
  const st=S.st[q.id]||(S.st[q.id]={tried:'',shown:false,mark:null});
  const wrap=h('div',{});
  const head=h('div',{class:'card'},h('div',{class:'row'},h('b',{},r.name),h('span',{class:'note',style:'margin-left:auto'},'Question '+(S.i+1)+' of '+n)),
    h('div',{class:'sbar',role:'progressbar','aria-valuemin':'0','aria-valuemax':String(n),'aria-valuenow':String(S.i+1)},h('i',{style:'width:'+Math.round((S.i+1)/n*100)+'%'})),
    h('span',{class:'pill'},TYN[q.t]||q.t),h('span',{class:'pill'},LVN[q.l]||q.l),
    h('p',{class:'qtext',id:'sessQ',tabindex:'-1'},q.q));
  const ta=h('textarea',{id:'sessTry',maxlength:'3000',placeholder:'Type or speak your own answer here first (optional). It stays on your phone and is not sent anywhere.','aria-label':'Your answer (optional)'});ta.value=st.tried;ta.oninput=()=>{st.tried=ta.value};
  const err=h('div',{class:'err',role:'alert'});
  const tryBox=h('div',{},h('label',{for:'sessTry',class:'note'},'Try it yourself'),ta);
  const row1=h('div',{class:'row'});
  const ANDROID=/Android/i.test(navigator.userAgent||'');
  if(SR){let base='',wantMic=false,micFinal='',micGot=false,micRetries=0,micErr='',spoken='',spkT0=0;
    const paint=interim=>{ta.value=[base,micFinal,interim||''].filter(x=>x&&x.trim()).join(' ').trim();st.tried=ta.value};
    const beginRec=()=>{let rec0;
      try{rec0=new SR();rec0.lang='en-IN';rec0.continuous=!ANDROID;rec0.interimResults=true;rec0.maxAlternatives=1}catch(e){rec=null;wantMic=false;mic.textContent='Speak my answer';err.textContent='Speaking is not available in this browser. Please type your answer.';return}
      rec=rec0;micErr='';let done=0;
      rec0.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){const r=e.results[i],t=r&&r[0]&&r[0].transcript?r[0].transcript.trim():'';if(!t)continue;
        if(r.isFinal){if(i>=done){micFinal=(micFinal?micFinal+' ':'')+t;spoken=(spoken?spoken+' ':'')+t;micGot=true;done=i+1}}else interim+=' '+t}
        paint(interim)};
      rec0.onerror=e=>{const c=e&&e.error;micErr=c||'error';if(c==='aborted'||c==='no-speech')return;
        err.textContent=(c==='not-allowed'||c==='service-not-allowed')?'Microphone access was blocked. Please allow the microphone for this site and try again, or type your answer.':'Speaking did not work ('+(c||'error')+'). Please type your answer.'};
      rec0.onend=()=>{if(rec===rec0)rec=null;
        if(rec)return;
        if(!wantMic||!ta.isConnected||micErr==='not-allowed'||micErr==='service-not-allowed'||micErr==='audio-capture'){wantMic=false;mic.textContent='Speak my answer';paint();return}
        if(micErr==='no-speech'&&!micGot&&++micRetries>=2){wantMic=false;mic.textContent='Speak my answer';err.textContent='No speech was heard. Try again in a quiet place.';paint();return}
        base=[base,micFinal].filter(x=>x&&x.trim()).join(' ');micFinal='';micErr='';
        setTimeout(()=>{if(wantMic&&ta.isConnected&&!rec){try{beginRec()}catch(x){wantMic=false;mic.textContent='Speak my answer';err.textContent='Could not restart the microphone. Please type your answer.'}}},ANDROID?250:0)};
      try{rec0.start()}catch(e){if(rec===rec0)rec=null;wantMic=false;mic.textContent='Speak my answer';err.textContent='Could not start the microphone. Please type your answer.'}};
    const mic=h('button',{type:'button',class:'alt',id:'sessMic',onclick:()=>{
      if(rec){wantMic=false;stopMic();mic.textContent='Speak my answer';paint();spkShow();return}
      if(wantMic){wantMic=false;mic.textContent='Speak my answer';paint();return}
      err.textContent='';base=ta.value.trim();micFinal='';micGot=false;micRetries=0;spoken='';spkT0=Date.now();spkBox.replaceChildren();wantMic=true;mic.textContent='Stop';beginRec()}},'Speak my answer');row1.append(mic)}
  const spkBox=h('div',{id:'sessSpk','aria-live':'polite'});
  const spkShow=()=>{spkBox.replaceChildren();const m=spkAnalyze(spoken,Date.now()-spkT0);if(!m)return;
    st.speaking={wpm:m.wpm,fillers:m.ft,words:m.wc};
    const fl=Object.entries(m.fillers).map(([k,v])=>'"'+k+'" x'+v).join(', ');
    spkBox.append(h('div',{class:'mine'},h('b',{class:'note'},'Speaking: '),
      (m.wpm?('Pace '+m.wpm+' words/min · '):'')+m.wc+' words · '+m.ft+' filler words'+(fl?' ('+fl+')':'')+'. ',
      h('span',{class:'note'},spkTip(m)),
      h('span',{class:'note',style:'display:block'},'Measured on your phone only; your words are not sent anywhere.')));
    try{fetch('/api/progress/speaking',{method:'POST',credentials:'same-origin',headers:{'content-type':'application/json'},body:JSON.stringify({wpm:m.wpm,fillers:m.ft,words:m.wc})}).catch(()=>{})}catch(e){}};
  const reveal=h('button',{type:'button',class:'big',id:'sessShow',onclick:()=>{st.shown=true;drawAns()}},'Show model answer');
  row1.append(reveal);
  function drawAns(){ansBox.replaceChildren();if(!st.shown){reveal.classList.remove('hide');return}reveal.classList.add('hide');
    const own=/\[|use your own/i.test(q.a);
    ansBox.append(...[h('div',{class:'ans'},h('b',{},'Model answer'),h('p',{},q.a)),
      own?h('p',{class:'note'},'Words in [brackets] and "use your own" examples are placeholders. Replace them with your real details. Never claim experience you do not have.'):null,
      q.w?h('div',{class:'ans look'},h('b',{},'What interviewers look for'),h('p',{},q.w)):null,
      q.h?h('div',{class:'ans hi'},h('b',{},'Hindi tip'),h('p',{},q.h)):null,
      st.tried.trim()?h('div',{class:'mine'},h('b',{class:'note'},'Your answer: '),st.tried.trim()):null,
      h('div',{class:'row'},TTS?h('button',{type:'button',class:'ghost',onclick:()=>speak(q.a)},'Read it aloud'):null,
        h('button',{type:'button',class:st.mark==='ok'?'':'ghost',onclick:()=>{st.mark='ok';delete marks[q.id];lsSet(KEY_MARK,marks);drawAns()}},st.mark==='ok'?'Marked: I know this':'I know this'),
        h('button',{type:'button',class:st.mark==='again'?'alt':'ghost',onclick:()=>{st.mark='again';marks[q.id]=1;trim();lsSet(KEY_MARK,marks);drawAns()}},st.mark==='again'?'Marked: practise again':'Practise this again')),
      h('p',{class:'note'},h('a',{href:'#',onclick:ev=>{ev.preventDefault();flag(q,ev.target)},style:'color:var(--acc2)'},'Report a mistake in this answer'))].filter(Boolean))}
  const nav=h('div',{class:'row'},
    h('button',{type:'button',class:'ghost',disabled:S.i?null:true,onclick:()=>{S.i--;card()}},'Previous'),
    h('button',{type:'button',class:'alt',onclick:()=>{if(S.i+1<n){S.i++;card()}else done()}},S.i+1<n?'Next question':'Finish'),
    h('button',{type:'button',class:'ghost',onclick:()=>{stopMic();if(TTS)TTS.cancel();S.list=[];picker()}},'Change job'));
  wrap.append(head,h('div',{class:'card'},tryBox,err,row1,spkBox,ansBox),nav);
  drawAns();show(wrap);const qq=$('sessQ');if(qq&&qq.focus)qq.focus({preventScroll:true});window.scrollTo({top:0,behavior:'auto'})}
function trim(){const k=Object.keys(marks);if(k.length>400)for(const x of k.slice(0,k.length-400))delete marks[x]}
async function flag(q,el){if(el.dataset.sent)return;el.dataset.sent='1';el.textContent='Sending...';
  try{const r=await fetch('/api/content-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'practice-session',reason:'Practice Sessions answer reported by user',excerpt:q.q.slice(0,300)})});
    el.textContent=r.ok?'Thank you. We will review this answer.':'Could not send. Please email us from the menu.'}catch(e){el.textContent='Could not send. Please check your internet.';delete el.dataset.sent}}
function done(){stopMic();if(TTS)TTS.cancel();const r=roleById(S.role),n=S.list.length;
  const seen=S.list.filter(q=>S.st[q.id]&&S.st[q.id].shown).length,tried=S.list.filter(q=>S.st[q.id]&&S.st[q.id].tried.trim()).length;
  const again=S.list.filter(q=>S.st[q.id]&&S.st[q.id].mark==='again');
  const wrap=h('div',{},h('div',{class:'card'},h('h2',{},'Session complete'),h('p',{},r.name+': '+n+' questions.'),
    h('p',{},'You tried '+tried+' answers yourself and opened '+seen+' model answers.'+(again.length?' '+again.length+' marked to practise again.':'')),
    h('p',{class:'note'},'Tip: say your answers out loud. The real interview is spoken.'),
    h('div',{class:'row'},again.length?h('button',{type:'button',onclick:()=>{S.list=again;S.i=0;card()}},'Practise the '+again.length+' marked'):null,
      h('button',{type:'button',class:'alt',onclick:()=>{S.list=order(filtered(r));S.i=0;S.st={};card()}},'Start again'),
      h('button',{type:'button',class:'ghost',onclick:()=>{S.list=[];picker()}},'Choose another job'),
      h('button',{type:'button',class:'ghost',onclick:()=>{if(window.__mr)window.__mr.setView('interview')}},'Try a full mock interview'))));
  show(wrap);window.scrollTo({top:0,behavior:'auto'})}
// ---------- wiring
async function render(){const r=root();if(!r)return;r.replaceChildren(h('p',{class:'note'},'Loading...'));
  try{await load();if(S.list.length&&S.role&&roleById(S.role))card();else picker()}
  catch(e){r.replaceChildren(h('div',{class:'card'},h('p',{class:'err',role:'alert'},e.message||'Something went wrong.'),h('button',{type:'button',onclick:render},'Try again')))}}
function onView(){if(document.body.dataset.view==='sessions'){$('viewTitle').textContent='Practice Sessions';render()}else{stopMic();if(TTS)TTS.cancel()}}
function init(){const M=window.__mr;if(!M)return;document.head.append(h('style',{},STYLE));
  const hr=h('div',{id:'sessRoot','aria-live':'off'});const lay=document.querySelector('.layout');lay.before(hr);
  M.TITLES.sessions='Practice Sessions';
  new MutationObserver(onView).observe(document.body,{attributes:true,attributeFilter:['data-view']});
  if((window.__startHash||'')==='sessions')M.setView('sessions',false)}
if(window.__mr)init();else window.addEventListener('mr:ready',init);
})();
