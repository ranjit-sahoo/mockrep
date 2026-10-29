// Share-card page: report objectionable content (Google Play UGC policy).
(function(){
  var a = document.getElementById('cardReport');
  if (!a) return;
  a.addEventListener('click', function(ev){
    ev.preventDefault();
    if (a.dataset.done) return;
    a.dataset.done = '1';
    fetch('/api/content-report', {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({kind: 'card', reason: 'Reported from the public card page.', excerpt: a.dataset.token || ''})
    }).catch(function(){}).then(function(){
      var d = document.getElementById('cardReported');
      if (d) d.style.display = 'inline';
      a.style.display = 'none';
    });
  });
})();
