// Utilidades fetch
async function api(path, opts={}){
  opts.headers = opts.headers || {'Content-Type':'application/json'};
  if(opts.body && typeof opts.body === 'object') opts.body = JSON.stringify(opts.body);
  const res = await fetch(path, opts);
  if(res.status === 401){ throw new Error('no autorizado'); }
  return res.json ? res.json() : res;
}

// Login
document.getElementById('btnLogin').onclick = async ()=>{
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;
  try{
    const r = await api('/api/login', {method:'POST', body:{username:u,password:p}});
    if(r.ok){ document.getElementById('login').style.display='none'; document.getElementById('main').style.display='block'; loadAll(); }
    else{ document.getElementById('loginErr').innerText = r.error || 'Error'; }
  }catch(e){ document.getElementById('loginErr').innerText = e.message }
}

// Logout
document.getElementById('btnLogout').onclick = async ()=>{
  await fetch('/api/logout',{method:'POST'});
  document.getElementById('main').style.display='none'; document.getElementById('login').style.display='block';
}

// Cargar datos
async function loadAll(){ await loadUsers(); await loadPayments(); }

async function loadUsers(){
  const users = await api('/api/users');
  const tbody = document.querySelector('#usersTable tbody'); tbody.innerHTML='';
  const sel = document.getElementById('paymentUser'); sel.innerHTML='';
  users.forEach(u=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${u.id}</td><td>${u.name}</td><td>${u.active? 'Activo':'Corte'}</td><td>
      <button class="btnEdit" data-id="${u.id}">Editar</button>
      <button class="btnDel" data-id="${u.id}">Borrar</button>
      <button class="btnToggle" data-id="${u.id}">${u.active? 'Desactivar':'Activar'}</button>
    </td>`;
    tbody.appendChild(tr);

    const opt = document.createElement('option'); opt.value = u.id; opt.text = u.name; sel.appendChild(opt);
  });
  // bind
  document.querySelectorAll('.btnDel').forEach(b=>b.onclick = async ()=>{ if(confirm('Borrar usuario y sus pagos?')){ await api('/api/users/'+b.dataset.id,{method:'DELETE'}); loadAll(); }});
  document.querySelectorAll('.btnToggle').forEach(b=>b.onclick = async ()=>{ await api('/api/users/'+b.dataset.id+'/toggle',{method:'POST'}); loadAll(); });
  document.querySelectorAll('.btnEdit').forEach(b=>b.onclick = async ()=>{
    const id = b.dataset.id; const name = prompt('Nuevo nombre'); if(name) await api('/api/users/'+id,{method:'PUT', body:{name, active:1}}); loadAll();
  });
}

// agregar usuario
document.getElementById('btnAddUser').onclick = async ()=>{
  const name = document.getElementById('newUserName').value.trim(); if(!name){ alert('Ingrese nombre'); return; }
  await api('/api/users',{method:'POST', body:{name}});
  document.getElementById('newUserName').value=''; loadAll();
}

// pagos
async function loadPayments(){
  const payments = await api('/api/payments');
  const tb = document.querySelector('#paymentsTable tbody'); tb.innerHTML='';
  payments.forEach(p=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${p.id}</td><td>${p.user_name}</td><td>${p.amount}</td><td>${p.date}</td><td>${p.notes||''}</td><td>
      <button class="btnPayEdit" data-id="${p.id}">Editar</button>
      <button class="btnPayDel" data-id="${p.id}">Borrar</button>
    </td>`;
    tb.appendChild(tr);
  });
  document.querySelectorAll('.btnPayDel').forEach(b=>b.onclick = async ()=>{ if(confirm('Borrar pago?')){ await api('/api/payments/'+b.dataset.id,{method:'DELETE'}); loadAll(); }});
  document.querySelectorAll('.btnPayEdit').forEach(b=>b.onclick = async ()=>{
    const id = b.dataset.id; const amount = prompt('Nuevo monto'); const date = prompt('Fecha (YYYY-MM-DD)'); const notes = prompt('Notas');
    if(amount && date) await api('/api/payments/'+id,{method:'PUT', body:{amount, date, notes}});
    loadAll();
  });
}

document.getElementById('btnAddPayment').onclick = async ()=>{
  const user_id = document.getElementById('paymentUser').value;
  const amount = document.getElementById('paymentAmount').value || 0;
  const date = document.getElementById('paymentDate').value;
  const notes = document.getElementById('paymentNotes').value;
  if(!user_id || !date){ alert('Seleccione usuario y fecha'); return; }
  await api('/api/payments',{method:'POST', body:{user_id, amount, date, notes}});
  document.getElementById('paymentAmount').value=''; document.getElementById('paymentNotes').value='';
  loadAll();
}
