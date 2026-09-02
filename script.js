const $=(s,c=document)=>c.querySelector(s);const $$=(s,c=document)=>[...c.querySelectorAll(s)];
const body=document.body,menu=$('#menuButton'),sidebar=$('#sidebar'),theme=$('#themeButton');
menu.addEventListener('click',()=>{const open=sidebar.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));});
$$('#sectionNav a').forEach(a=>a.addEventListener('click',()=>{sidebar.classList.remove('open');menu.setAttribute('aria-expanded','false');}));
const savedTheme=localStorage.getItem('biztrust-theme');if(savedTheme==='dark'||(!savedTheme&&matchMedia('(prefers-color-scheme:dark)').matches))body.classList.add('dark');
theme.addEventListener('click',()=>{body.classList.toggle('dark');localStorage.setItem('biztrust-theme',body.classList.contains('dark')?'dark':'light');});
const sections=$$('main>section[id]'),links=$$('#sectionNav a');
const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id));}})},{rootMargin:'-25% 0px -65% 0px'});sections.forEach(s=>observer.observe(s));
addEventListener('scroll',()=>{const d=document.documentElement;const p=d.scrollTop/(d.scrollHeight-d.clientHeight)*100;$('#readingProgress').style.width=Math.min(100,p)+'%';},{passive:true});
$$('.copy').forEach(btn=>btn.addEventListener('click',async()=>{const el=document.getElementById(btn.dataset.copy);await navigator.clipboard.writeText(el.innerText);const old=btn.textContent;btn.textContent='Copied';setTimeout(()=>btn.textContent=old,1400);}));
const overlay=$('#searchOverlay'),input=$('#searchInput'),results=$('#searchResults');
function openSearch(){overlay.hidden=false;input.value='';results.innerHTML='<p>Start typing to search the implementation guide.</p>';setTimeout(()=>input.focus(),20)}function closeSearch(){overlay.hidden=true}
$('#searchButton').addEventListener('click',openSearch);overlay.addEventListener('click',e=>{if(e.target===overlay)closeSearch()});
addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openSearch()}if(e.key==='Escape')closeSearch()});
input.addEventListener('input',()=>{const q=input.value.trim().toLowerCase();if(!q){results.innerHTML='<p>Start typing to search the implementation guide.</p>';return}const found=sections.filter(s=>(s.dataset.search+' '+s.innerText).toLowerCase().includes(q));results.innerHTML=found.length?found.map(s=>{const h=$('h2',s)?.textContent||s.id;const text=s.innerText.replace(/\s+/g,' ').slice(0,125);return `<a class="search-result" href="#${s.id}"><strong>${h}</strong><span>${text}…</span></a>`}).join(''):'<p>No matching sections found.</p>';$$('.search-result',results).forEach(a=>a.addEventListener('click',closeSearch));});
