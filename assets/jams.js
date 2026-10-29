/* Per-jam .ics download, generated client-side from the data-* attributes on each [data-ics] link. */
(function(){
  var esc=function(s){return String(s).replace(/\\/g,'\\\\').replace(/;/g,'\\;').replace(/,/g,'\\,').replace(/\r?\n/g,'\\n');};
  var fold=function(l){var o=[];while(l.length>73){o.push(l.slice(0,73));l=' '+l.slice(73);}o.push(l);return o.join('\r\n');};
  function ics(a){
    var d=a.dataset,name=d.name,url=d.url,now=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d+/,'');
    var uid=(url.replace(/^https?:\/\//,'').replace(/[^a-z0-9]+/gi,'-'))+'-'+d.start+'@frightqueue.thejurn.com';
    var L=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Fright Queue//Horror Game Jam Tracker//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH',
      'BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+now,'DTSTART:'+d.start,'DTEND:'+d.end,
      'SUMMARY:'+esc(name+' (horror game jam)'),'DESCRIPTION:'+esc('Horror game jam on itch.io: '+url+'\nTracked by Fright Queue: https://frightqueue.thejurn.com/jams/'),
      'URL:'+url,'LOCATION:'+esc(url),
      'BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:'+esc(name+' starts in 1 day'),'TRIGGER:-P1D','END:VALARM',
      'END:VEVENT','END:VCALENDAR'];
    return L.map(fold).join('\r\n')+'\r\n';
  }
  document.addEventListener('click',function(ev){
    var a=ev.target.closest&&ev.target.closest('a[data-ics]');if(!a)return;
    ev.preventDefault();
    var blob=new Blob([ics(a)],{type:'text/calendar;charset=utf-8'}),u=URL.createObjectURL(blob),l=document.createElement('a');
    l.href=u;l.download=(a.dataset.url.split('/').pop()||'horror-jam').replace(/[^a-z0-9_-]+/gi,'-')+'.ics';
    document.body.appendChild(l);l.click();l.remove();setTimeout(function(){URL.revokeObjectURL(u)},1000);
  });
})();
