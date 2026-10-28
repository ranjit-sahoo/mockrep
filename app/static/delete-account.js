(async()=>{
const $=id=>document.getElementById(id);
let me=null;
try{const j=await(await fetch('/api/auth/me',{credentials:'same-origin'})).json();me=j.user}catch(e){}
if(me){$('signedIn').classList.remove('hide');$('who').textContent=me.email}else{$('signedOut').classList.remove('hide')}
$('delBtn').onclick=async()=>{
  if(!confirm('Delete your account and everything saved? This cannot be undone.'))return;
  $('delBtn').disabled=true;$('delErr').textContent='';
  try{
    const r=await fetch('/api/auth/account',{method:'DELETE',credentials:'same-origin'});
    if(!r.ok){const j=await r.json().catch(()=>({}));throw new Error(j.detail||'Could not delete the account.')}
    try{localStorage.clear();sessionStorage.clear()}catch(e){}
    $('signedIn').classList.add('hide');$('done').classList.remove('hide');
  }catch(e){$('delErr').textContent=e.message;$('delBtn').disabled=false}
};
})();
