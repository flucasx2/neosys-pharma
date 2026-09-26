const api = "/api/v1";
const state = {products:[],articles:[],principles:[],brands:[],locations:[],stock:[],postes:[],suppliers:[],tariffs:[],purchases:[],organismes:[],loyaltyClients:[],loyaltyCards:[],accounts:[],caisses:[]};
let activePurchaseRow = null;
let activeView = window.sessionStorage.getItem("neosys-active-view") || "dashboard";
const $ = (id) => document.getElementById(id);
const money = (value) => `${Number(value).toLocaleString("fr-FR")} FCFA`;
const safe = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
document.addEventListener("submit", (event) => event.preventDefault(), true);

async function request(path, options = {}) {
  const response = await fetch(`${api}${path}`, {cache:"no-store", headers:{"Content-Type":"application/json"}, ...options});
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = Array.isArray(data?.detail) ? data.detail.map((item) => item.msg).join(" · ") : data?.detail;
    throw new Error(detail || "Une erreur est survenue.");
  }
  return data;
}
function flash(text, type = "success") {
  const node = $("flash"); node.textContent = text; node.className = `show ${type}`;
  window.clearTimeout(flash.timer); flash.timer = window.setTimeout(() => node.className = "", 5000);
}
function articleName(id) { const item = state.articles.find((a) => a.id === id); return item ? `${item.designation} — ${item.libelle}` : id.slice(0,8); }
function locationName(id) { const item = state.locations.find((a) => a.id === id); return item ? `${item.code} — ${item.libelle}` : id.slice(0,8); }
function supplierName(id) { const item = state.suppliers.find((a) => a.id === id); return item ? item.raison_sociale : id.slice(0,8); }
function stockForPack(id) { return state.stock.filter((row) => row.conditionnement_id === id && stockIsSellable(row)).reduce((sum,row) => sum + row.quantite_disponible,0); }
function stockIsSellable(row) {
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")}`;
  return row.etat_lot === "actif" && row.date_expiration >= today;
}

function showView(name) {
  if (!document.getElementById(`view-${name}`)) name = "dashboard";
  activeView = name;
  window.sessionStorage.setItem("neosys-active-view", name);
  document.querySelectorAll(".view").forEach((node) => node.classList.toggle("active", node.id === `view-${name}`));
  document.querySelectorAll(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.view === name));
  const titles = {dashboard:"Tableau de bord",catalogue:"Produits",stock:"Stock & lots",achats:"Commandes & réceptions",postes:"Postes de vente",fournisseurs:"Fournisseurs",couvertures:"Prises en charge",fidelite:"Fidélité clients",administration:"Administration"};
  $("page-title").textContent = titles[name];
}
document.querySelectorAll("[data-view]").forEach((node) => node.addEventListener("click", () => showView(node.dataset.view)));
document.querySelectorAll("[data-go]").forEach((node) => node.addEventListener("click", () => showView(node.dataset.go)));
document.querySelectorAll("[data-open]").forEach((node) => node.addEventListener("click", () => {
  if (node.dataset.open === "produit-dialog") prepareNewProduct();
  if (node.dataset.open === "fournisseur-dialog") prepareNewSupplier();
  if (node.dataset.open === "commande-dialog") prepareNewPurchase();
  if (node.dataset.open === "organisme-dialog") prepareNewOrganisme();
  if (node.dataset.open === "tarif-dialog") prepareNewTariff();
  if (node.dataset.open === "client-dialog") prepareNewClient();
  if (node.dataset.open === "carte-dialog") prepareNewCard();
  if (node.dataset.open === "compte-dialog") prepareNewAccount();
  if (node.dataset.open === "caisse-dialog") $("caisse-form").reset();
  $(node.dataset.open).showModal();
}));
document.querySelectorAll("[data-close]").forEach((node) => node.addEventListener("click", () => node.closest("dialog").close()));

function render() {
  $("metric-products").textContent = state.products.length;
  $("metric-articles").textContent = state.articles.length;
  $("metric-stock").textContent = state.stock.filter(stockIsSellable).reduce((sum, row) => sum + row.quantite_disponible, 0).toLocaleString("fr-FR");
  $("metric-postes").textContent = state.postes.length;
  $("stock-locations").textContent = state.locations.length;
  $("stock-lots").textContent = new Set(state.stock.map((row) => row.lot_id)).size;
  $("stock-available").textContent = state.stock.filter(stockIsSellable).reduce((sum, row) => sum + row.quantite_disponible, 0).toLocaleString("fr-FR");
  renderProducts(); renderStock(); renderPostes(); renderSuppliers(); renderTariffs(); renderPurchases(); renderOrganismes(); renderLoyalty(); renderAccounts(); renderCaisses(); renderSelects(); renderDashboardStock();
}
function renderProducts() {
  const term = $("product-search").value.trim().toLowerCase();
  const rows = state.articles.filter((a) => [a.reference,a.cip7,a.designation,a.code,a.libelle].some((v) => v.toLowerCase().includes(term)));
  $("product-count").textContent = `${state.products.length} produit${state.products.length > 1 ? "s" : ""} · ${rows.length} article${rows.length > 1 ? "s" : ""}`;
  $("products-table").innerHTML = rows.length ? rows.map((a) => `<tr><td><strong>${safe(a.reference)}</strong></td><td><strong>${safe(a.cip7 || "—")}</strong></td><td><strong>${safe(a.designation)}</strong><small>${safe(a.libelle)}</small></td><td><span class="tag">${a.type_produit === "medicament" ? "Médicament" : "Cosmétique"}</span></td><td>${safe(a.libelle)}</td><td>${safe(a.code)}</td><td class="quantity good">${stockForPack(a.id).toLocaleString("fr-FR")}</td><td><strong>${money(a.prix_vente)}</strong></td><td><div class="row-actions"><button class="row-action" data-view-product="${a.produit_id}" data-view-pack="${a.id}">Consulter</button><button class="row-action" data-edit-product="${a.produit_id}" data-edit-pack="${a.id}">Modifier</button></div></td></tr>`).join("") : '<tr class="empty-row"><td colspan="9">Aucun article. Créez votre premier produit.</td></tr>';
}
function renderStock() {
  $("stock-table").innerHTML = state.stock.length ? state.stock.map((row) => `<tr><td><strong>${safe(articleName(row.conditionnement_id))}</strong></td><td>${safe(row.numero_lot)}</td><td>${new Date(`${row.date_expiration}T00:00:00`).toLocaleDateString("fr-FR")}</td><td>${safe(locationName(row.emplacement_id))}</td><td>${row.quantite_physique}</td><td>${row.quantite_reservee}</td><td class="quantity ${stockIsSellable(row)?"good":""}">${stockIsSellable(row)?row.quantite_disponible:0}</td></tr>`).join("") : '<tr class="empty-row"><td colspan="7">Aucun lot réceptionné.</td></tr>';
}
function renderPostes() {
  $("postes-grid").innerHTML = state.postes.length ? state.postes.map((p) => `<article class="poste-card"><header><h3>${safe(p.code)}</h3><span class="status-pill">ACTIF</span></header><p>Emplacement de vente</p><strong>${safe(locationName(p.emplacement_id))}</strong></article>`).join("") : '<div class="coming-soon"><p>Aucun poste configuré.</p></div>';
}
function renderSuppliers() {
  $("supplier-count").textContent = state.suppliers.length;
  $("suppliers-table").innerHTML = state.suppliers.length ? state.suppliers.map((item) => `<tr><td><strong>${safe(item.code)}</strong></td><td><strong>${safe(item.raison_sociale)}</strong><small>${safe(item.email || "—")}</small></td><td>${safe(item.telephone || "—")}</td><td><span class="status-pill ${item.actif ? "" : "inactive"}">${item.actif ? "ACTIF" : "INACTIF"}</span></td><td><div class="row-actions"><button class="row-action" data-view-supplier="${item.id}">Consulter</button><button class="row-action" data-edit-supplier="${item.id}">Modifier</button></div></td></tr>`).join("") : '<tr class="empty-row"><td colspan="5">Aucun fournisseur enregistré.</td></tr>';
}
function renderTariffs() {
  $("tariff-count").textContent = state.tariffs.length;
  $("tariffs-table").innerHTML = state.tariffs.length ? state.tariffs.map((item) => {
    const article = state.articles.find((a) => a.id === item.conditionnement_id);
    const margin = article ? Number(article.prix_vente) - Number(item.prix_achat) : 0;
    return `<tr><td><strong>${safe(supplierName(item.fournisseur_id))}</strong></td><td><strong>${safe(articleName(item.conditionnement_id))}</strong></td><td>${safe(item.reference_fournisseur || "—")}</td><td>${money(item.prix_achat)}</td><td>${article ? money(article.prix_vente) : "—"}</td><td class="quantity good">${money(margin)}</td><td><button class="row-action" data-edit-tariff="${item.id}">Modifier</button></td></tr>`;
  }).join("") : '<tr class="empty-row"><td colspan="7">Aucun tarif fournisseur défini.</td></tr>';
}
function renderPurchases() {
  const total = state.purchases.reduce((sum, item) => sum + Number(item.total_general), 0);
  $("purchase-count").textContent = state.purchases.length;
  $("purchase-total").textContent = total.toLocaleString("fr-FR");
  $("last-purchase").textContent = state.purchases.at(-1)?.numero_interne || "—";
  $("purchases-table").innerHTML = state.purchases.length ? [...state.purchases].reverse().map((item) => `<tr><td><strong>${safe(item.numero_interne)}</strong></td><td>${safe(supplierName(item.fournisseur_id))}</td><td>${safe(item.numero_fournisseur || "—")}</td><td>${new Date(`${item.date_commande}T00:00:00`).toLocaleDateString("fr-FR")}</td><td>${new Date(`${item.date_arrivee}T00:00:00`).toLocaleDateString("fr-FR")}</td><td>${item.lignes.length}</td><td><strong>${money(item.total_general)}</strong></td><td><button class="row-action" data-view-purchase="${item.id}">Consulter</button></td></tr>`).join("") : '<tr class="empty-row"><td colspan="8">Aucune commande réceptionnée.</td></tr>';
}
function renderOrganismes() {
  $("organismes-table").innerHTML = state.organismes.length ? state.organismes.map((item) => `<tr><td><strong>${safe(item.code)}</strong></td><td><strong>${safe(item.nom)}</strong><small>${Number(item.taux_prise_en_charge).toLocaleString("fr-FR")} %</small></td><td><span class="tag">${safe(item.type_organisme.replace("_"," "))}</span></td><td class="wrap-cell">${item.documents_requis.length ? item.documents_requis.map((doc) => `<span class="document-pill">${safe(doc)}</span>`).join("") : "—"}</td><td><span class="status-pill ${item.actif ? "" : "inactive"}">${item.actif ? "ACTIF" : "INACTIF"}</span></td><td><div class="row-actions"><button class="row-action" data-view-organisme="${item.id}">Afficher</button><button class="row-action" data-edit-organisme="${item.id}">Modifier</button></div></td></tr>`).join("") : '<tr class="empty-row"><td colspan="6">Aucun organisme configuré.</td></tr>';
}
function loyaltyClientName(id) { const c=state.loyaltyClients.find((i)=>i.id===id); return c ? `${c.nom} ${c.prenom}`.trim() : "—"; }
function renderLoyalty() {
  $("loyalty-client-count").textContent=state.loyaltyClients.length;
  $("loyalty-card-count").textContent=state.loyaltyCards.filter((c)=>c.actif).length;
  $("loyalty-points").textContent=state.loyaltyCards.reduce((s,c)=>s+c.points,0).toLocaleString("fr-FR");
  $("loyalty-clients-table").innerHTML=state.loyaltyClients.length ? state.loyaltyClients.map((c)=>`<tr><td><strong>${safe(c.code)}</strong></td><td><strong>${safe(`${c.nom} ${c.prenom}`)}</strong><small>${safe(c.email||"—")}</small></td><td>${safe(c.telephone||"—")}</td><td><span class="status-pill ${c.actif?"":"inactive"}">${c.actif?"ACTIF":"INACTIF"}</span></td><td><button class="row-action" data-edit-client="${c.id}">Modifier</button></td></tr>`).join("") : '<tr class="empty-row"><td colspan="5">Aucun client fidélité.</td></tr>';
  $("loyalty-cards-table").innerHTML=state.loyaltyCards.length ? state.loyaltyCards.map((c)=>`<tr><td><strong>${safe(c.numero)}</strong></td><td>${safe(loyaltyClientName(c.client_id))}</td><td><span class="tag">${safe(c.type_carte)}</span></td><td><strong>${c.points}</strong></td><td><span class="status-pill ${c.actif?"":"inactive"}">${c.actif?"ACTIVE":"INACTIVE"}</span></td><td><div class="row-actions"><button class="row-action" data-points-card="${c.id}">Points</button><button class="row-action" data-edit-card="${c.id}">Modifier</button></div></td></tr>`).join("") : '<tr class="empty-row"><td colspan="6">Aucune carte émise.</td></tr>';
}
function renderAccounts(){const postName=(id)=>state.postes.find(p=>p.id===id)?.code||"—";$("accounts-table").innerHTML=state.accounts.length?state.accounts.map(a=>`<tr><td><strong>${safe(a.code)}</strong></td><td>${safe(a.nom)}</td><td><span class="tag">${safe(a.role)}</span></td><td>${safe(postName(a.poste_id))}</td><td><strong>${safe(a.caisse)}</strong></td><td><span class="status-pill ${a.actif?"":"inactive"}">${a.actif?"ACTIF":"INACTIF"}</span></td><td><button class="row-action" data-edit-account="${a.id}">Modifier</button></td></tr>`).join(""):'<tr class="empty-row"><td colspan="7">Aucun compte configuré.</td></tr>'}
function renderCaisses(){$("caisses-table").innerHTML=state.caisses.length?state.caisses.map(c=>`<tr><td><strong>${safe(c.code)}</strong></td><td>${safe(c.libelle)}</td><td><span class="status-pill">ACTIF</span></td></tr>`).join(""):'<tr class="empty-row"><td colspan="3">Créez la première caisse.</td></tr>'}
function showDetail(title, rows) {
  $("detail-title").textContent = title;
  $("detail-content").innerHTML = rows.map(([label,value]) => `<div class="detail-row"><span>${safe(label)}</span><strong>${safe(value || "—")}</strong></div>`).join("");
  $("detail-dialog").showModal();
}
function viewProduct(productId, packId) {
  const product = state.products.find((item) => item.id === productId);
  const pack = product?.conditionnements.find((item) => item.id === packId);
  if (!product || !pack) return;
  const packIds = product.conditionnements.map((item) => item.id);
  const stockRows = state.stock.filter((item) => packIds.includes(item.conditionnement_id));
  const physicalStock = stockRows.reduce((sum,item) => sum + item.quantite_physique,0);
  const reservedStock = stockRows.reduce((sum,item) => sum + item.quantite_reservee,0);
  const sellableStock = stockRows.filter(stockIsSellable).reduce((sum,item) => sum + item.quantite_disponible,0);
  const tariffs = state.tariffs.filter((item) => packIds.includes(item.conditionnement_id));
  const priceRows = tariffs.length ? tariffs.map((item) => { const article = state.articles.find((a) => a.id === item.conditionnement_id); return `<tr><td>${safe(supplierName(item.fournisseur_id))}</td><td>${safe(article?.libelle || "—")}</td><td>${safe(item.reference_fournisseur || "—")}</td><td><strong>${money(item.prix_achat)}</strong></td></tr>`; }).join("") : '<tr class="empty-row"><td colspan="4">Aucun prix fournisseur enregistré.</td></tr>';
  $("detail-title").textContent = product.designation;
  const stockDetails = stockRows.length ? stockRows.map((item) => { const article=state.articles.find((a)=>a.id===item.conditionnement_id); const status=stockIsSellable(item)?"VENDABLE":item.etat_lot!=="actif"?item.etat_lot.toUpperCase():"PÉRIMÉ"; return `<tr><td>${safe(article?.libelle||"—")}</td><td>${safe(locationName(item.emplacement_id))}</td><td>${safe(item.numero_lot)}</td><td>${new Date(`${item.date_expiration}T00:00:00`).toLocaleDateString("fr-FR")}</td><td>${item.quantite_physique}</td><td>${item.quantite_reservee}</td><td><strong>${stockIsSellable(item)?item.quantite_disponible:0}</strong></td><td><span class="status-pill ${stockIsSellable(item)?"":"inactive"}">${status}</span></td></tr>`; }).join("") : '<tr class="empty-row"><td colspan="8">Aucun stock enregistré.</td></tr>';
  $("detail-content").innerHTML = `<div class="detail-grid"><div class="detail-row"><span>Référence</span><strong>${safe(product.reference)}</strong></div><div class="detail-row"><span>CIP7</span><strong>${safe(product.cip7 || "—")}</strong></div><div class="detail-row"><span>Type</span><strong>${product.type === "medicament" ? "MÉDICAMENT" : "COSMÉTIQUE"}</strong></div><div class="detail-row"><span>${product.type === "medicament" ? "Principe actif" : "Marque"}</span><strong>${safe(product.information)}</strong></div><div class="detail-row"><span>Stock physique</span><strong>${physicalStock.toLocaleString("fr-FR")}</strong></div><div class="detail-row"><span>Stock réservé</span><strong>${reservedStock.toLocaleString("fr-FR")}</strong></div><div class="detail-row"><span>Stock vendable</span><strong>${sellableStock.toLocaleString("fr-FR")}</strong></div><div class="detail-row"><span>Prise en charge CNAMGS</span><strong>${product.pris_en_charge_cnamgs ? `${Number(product.taux_prise_en_charge_cnamgs).toLocaleString("fr-FR")} %` : "NON"}</strong></div></div><h3 class="detail-subtitle">Stock par lot et emplacement</h3><div class="table-wrap detail-table"><table><thead><tr><th>Conditionnement</th><th>Emplacement</th><th>Lot</th><th>Péremption</th><th>Physique</th><th>Réservé</th><th>Vendable</th><th>État</th></tr></thead><tbody>${stockDetails}</tbody></table></div><h3 class="detail-subtitle">Prix d'achat par fournisseur</h3><div class="table-wrap detail-table"><table><thead><tr><th>Fournisseur</th><th>Conditionnement</th><th>Réf. fournisseur</th><th>Prix d'achat</th></tr></thead><tbody>${priceRows}</tbody></table></div>`;
  $("detail-dialog").showModal();
}
function viewPurchase(id) {
  const item = state.purchases.find((purchase) => purchase.id === id); if (!item) return;
  const lines = item.lignes.map((line) => `<tr><td><strong>${safe(line.designation)}</strong><small>CIP7 ${safe(line.cip7 || "—")}</small></td><td>${line.quantite_commandee}</td><td>${line.quantite_recue}</td><td>${safe(line.numero_lot)}</td><td>${new Date(`${line.date_expiration}T00:00:00`).toLocaleDateString("fr-FR")}</td><td>${money(line.prix_unitaire)}</td><td><strong>${money(line.total)}</strong></td></tr>`).join("");
  $("detail-title").textContent = `Commande ${item.numero_interne}`;
  $("detail-content").innerHTML = `<div class="detail-grid"><div class="detail-row"><span>Fournisseur</span><strong>${safe(supplierName(item.fournisseur_id))}</strong></div><div class="detail-row"><span>N° fournisseur</span><strong>${safe(item.numero_fournisseur || "—")}</strong></div><div class="detail-row"><span>Date de commande</span><strong>${new Date(`${item.date_commande}T00:00:00`).toLocaleDateString("fr-FR")}</strong></div><div class="detail-row"><span>Date d'arrivée</span><strong>${new Date(`${item.date_arrivee}T00:00:00`).toLocaleDateString("fr-FR")}</strong></div></div><div class="table-wrap detail-table"><table><thead><tr><th>Produit</th><th>Commandée</th><th>Reçue</th><th>Lot</th><th>Péremption</th><th>Prix unitaire</th><th>Total</th></tr></thead><tbody>${lines}</tbody><tfoot><tr><th colspan="6">Total général</th><th>${money(item.total_general)}</th></tr></tfoot></table></div>`;
  $("detail-dialog").showModal();
}
function viewSupplier(id) {
  const item = state.suppliers.find((supplier) => supplier.id === id); if (!item) return;
  const tarifs = state.tariffs.filter((tarif) => tarif.fournisseur_id === id).length;
  showDetail(item.raison_sociale, [["Code",item.code],["Téléphone",item.telephone],["E-mail",item.email],["État",item.actif ? "ACTIF" : "INACTIF"],["Articles tarifés",String(tarifs)]]);
}
function renderDashboardStock() {
  const rows = [...state.stock].sort((a,b) => a.date_expiration.localeCompare(b.date_expiration)).slice(0,4);
  $("dashboard-stock").className = rows.length ? "" : "list-placeholder";
  $("dashboard-stock").innerHTML = rows.length ? rows.map((r) => `<div class="stock-preview"><div><strong>${safe(articleName(r.conditionnement_id))}</strong><small>Lot ${safe(r.numero_lot)} · expire le ${new Date(`${r.date_expiration}T00:00:00`).toLocaleDateString("fr-FR")}</small></div><b>${r.quantite_disponible}</b></div>`).join("") : "Aucune donnée de stock.";
}
function renderSelects() {
  const articles = state.articles.map((a) => `<option value="${a.id}">${safe(a.designation)} — ${safe(a.libelle)}</option>`).join("");
  const locations = state.locations.map((l) => `<option value="${l.id}">${safe(l.code)} — ${safe(l.libelle)}</option>`).join("");
  $("product-principle").innerHTML = state.principles.map((p) => `<option value="${p.id}">${safe(p.libelle)}</option>`).join("") + '<option value="__new__">＋ Ajouter un autre principe actif…</option>';
  $("product-brand").innerHTML = state.brands.map((item) => `<option value="${item.id}">${safe(item.libelle)}</option>`).join("") + '<option value="__new__">＋ Ajouter une autre marque…</option>';
  $("reception-article").innerHTML = articles || '<option value="">Créez d’abord un article</option>';
  $("reception-location").innerHTML = locations || '<option value="">Créez d’abord un emplacement</option>';
  $("poste-location").innerHTML = state.locations.filter((l) => l.autorise_vente).map((l) => `<option value="${l.id}">${safe(l.code)} — ${safe(l.libelle)}</option>`).join("") || '<option value="">Aucun emplacement de vente</option>';
  $("poste-caisse").innerHTML=state.caisses.filter(c=>c.actif).map(c=>`<option value="${c.id}">${safe(c.code)} — ${safe(c.libelle)}</option>`).join("")||'<option value="">Créez d’abord une caisse</option>';
  $("tariff-article").innerHTML = articles || '<option value="">Créez d’abord un article</option>';
  $("tariff-supplier").innerHTML = state.suppliers.filter((s) => s.actif).map((s) => `<option value="${s.id}">${safe(s.code)} — ${safe(s.raison_sociale)}</option>`).join("") || '<option value="">Créez d’abord un fournisseur</option>';
  $("catalogue-import-supplier").innerHTML = state.suppliers.filter((s) => s.actif).map((s) => `<option value="${s.id}">${safe(s.code)} — ${safe(s.raison_sociale)}</option>`).join("") || '<option value="">Créez d’abord un fournisseur</option>';
  $("purchase-supplier").innerHTML = state.suppliers.filter((s) => s.actif).map((s) => `<option value="${s.id}">${safe(s.code)} — ${safe(s.raison_sociale)}</option>`).join("") || '<option value="">Créez d’abord un fournisseur</option>';
  $("purchase-location").innerHTML = locations || '<option value="">Créez d’abord un emplacement</option>';
  $("loyalty-card-client").innerHTML = state.loyaltyClients.filter((c)=>c.actif).map((c)=>`<option value="${c.id}">${safe(c.code)} — ${safe(`${c.nom} ${c.prenom}`)}</option>`).join("") || '<option value="">Créez d’abord un client</option>';
  $("account-poste").innerHTML='<option value="">AUCUN</option>'+state.postes.map(p=>`<option value="${p.id}">${safe(p.code)}</option>`).join("");
  $("account-caisse").innerHTML=state.caisses.filter(c=>c.actif).map(c=>`<option value="${safe(c.code)}">${safe(c.code)} — ${safe(c.libelle)}</option>`).join("")||'<option value="">Créez d’abord une caisse</option>';
}
async function loadAll() {
  [state.products,state.articles,state.principles,state.brands,state.locations,state.stock,state.postes,state.suppliers,state.tariffs,state.purchases,state.organismes,state.loyaltyClients,state.loyaltyCards,state.accounts,state.caisses] = await Promise.all([
    request("/catalogue/produits"),request("/catalogue/articles"),request("/catalogue/principes-actifs"),request("/catalogue/marques"),request("/stock/emplacements"),request("/stock/etat"),request("/ventes/postes"),request("/achats/fournisseurs"),request("/achats/tarifs"),request("/achats/commandes-receptions"),request("/prises-en-charge/organismes"),request("/fidelite/clients"),request("/fidelite/cartes"),request("/administration/comptes"),request("/administration/caisses")
  ]); render();
}
async function finishSave(form, message) {
  const dialog = form.closest("dialog");
  if (dialog?.open && typeof dialog.close === "function") dialog.close();
  dialog?.removeAttribute("open");
  form.reset();
  try { await refreshAfterSave(form.id); flash(message); }
  catch (error) { flash(`Enregistrement effectué. Actualisation impossible : ${error.message}`, "error"); }
}

async function refreshAfterSave(formId) {
  const get = async (key,path) => { state[key]=await request(path); };
  if (formId === "product-form" || formId === "catalogue-import-form") {
    await Promise.all([get("products","/catalogue/produits"),get("articles","/catalogue/articles"),get("tariffs","/achats/tarifs")]);
    renderProducts(); renderTariffs(); renderSelects();
  } else if (formId === "supplier-form") {
    await get("suppliers","/achats/fournisseurs"); renderSuppliers(); renderSelects();
  } else if (formId === "tariff-form") {
    await get("tariffs","/achats/tarifs"); renderTariffs();
  } else if (formId === "purchase-form" || formId === "reception-form") {
    await Promise.all([get("purchases","/achats/commandes-receptions"),get("stock","/stock/etat"),get("tariffs","/achats/tarifs")]);
    renderPurchases(); renderStock(); renderTariffs(); renderDashboardStock();
  } else if (formId === "location-form") {
    await get("locations","/stock/emplacements"); renderSelects();
  } else if (formId === "poste-form") {
    await get("postes","/ventes/postes"); renderPostes(); renderSelects();
  } else if (formId === "caisse-form") {
    await get("caisses","/administration/caisses"); renderCaisses(); renderSelects();
  } else if (formId === "account-form") {
    await get("accounts","/administration/comptes"); renderAccounts();
  } else if (formId === "organisme-form") {
    await get("organismes","/prises-en-charge/organismes"); renderOrganismes();
  } else if (["client-form","carte-form","points-form"].includes(formId)) {
    await Promise.all([get("loyaltyClients","/fidelite/clients"),get("loyaltyCards","/fidelite/cartes")]);
    renderLoyalty(); renderSelects();
  } else await loadAll();
}

function setProductKind(type) {
  const medication = type === "medicament";
  $("principle-field").classList.toggle("hidden", !medication);
  $("brand-field").classList.toggle("hidden", medication);
  $("product-principle").required = medication;
  $("product-brand").required = !medication;
}
function prepareNewProduct() {
  const form = $("product-form"); form.reset(); form.elements.product_id.value = ""; form.elements.conditionnement_id.value = ""; form.elements.type.disabled = false;
  form.elements.pris_en_charge_cnamgs.checked = false; form.elements.taux_prise_en_charge_cnamgs.value = "80"; toggleCnamgsRate();
  $("product-dialog-title").textContent = "Nouveau produit"; $("product-submit").textContent = "Créer le produit"; setProductKind("medicament");
}
function editProduct(productId, packId) {
  const product = state.products.find((p) => p.id === productId); const pack = product?.conditionnements.find((p) => p.id === packId);
  if (!product || !pack) return;
  const form = $("product-form"); form.elements.product_id.value = product.id; form.elements.conditionnement_id.value = pack.id; form.elements.type.value = product.type; form.elements.type.disabled = true; form.elements.reference.value = product.reference; form.elements.cip7.value = product.cip7; form.elements.designation.value = product.designation; form.elements.code.value = pack.code; form.elements.libelle.value = pack.libelle; form.elements.prix_vente.value = pack.prix_vente;
  form.dataset.packSnapshot = JSON.stringify({code:pack.code,libelle:pack.libelle,prix_vente:Number(pack.prix_vente)});
  form.elements.pris_en_charge_cnamgs.checked = product.pris_en_charge_cnamgs; form.elements.taux_prise_en_charge_cnamgs.value = product.taux_prise_en_charge_cnamgs || "80"; toggleCnamgsRate();
  if (product.type === "medicament") {
    const legacyPrinciple = state.principles.find((item) => item.libelle === product.information);
    form.elements.principe_actif_id.value = product.principe_actif_id || legacyPrinciple?.id || "";
  } else {
    const legacyBrand = state.brands.find((item) => item.libelle === product.information);
    form.elements.marque_id.value = product.marque_id || legacyBrand?.id || "";
  }
  setProductKind(product.type); $("product-dialog-title").textContent = "Modifier le produit"; $("product-submit").textContent = "Enregistrer les modifications"; $("produit-dialog").showModal();
}
function toggleCnamgsRate() {
  const checked = $("product-cnamgs").checked;
  $("cnamgs-rate-field").classList.toggle("hidden", !checked);
  $("product-form").elements.taux_prise_en_charge_cnamgs.required = checked;
}
function prepareNewSupplier() {
  const form = $("supplier-form"); form.reset(); form.elements.fournisseur_id.value = ""; form.elements.actif.checked = true; $("supplier-dialog-title").textContent = "Nouveau fournisseur"; $("supplier-submit").textContent = "Créer le fournisseur";
}
function requiredDocumentTemplate(value = "") { return `<div class="document-row"><input class="required-document" maxlength="200" value="${safe(value)}" placeholder="EX. CARTE CNAMGS EN COURS DE VALIDITÉ" required><button type="button" class="remove-document" aria-label="Supprimer">×</button></div>`; }
function addRequiredDocument(value = "") { $("required-documents").insertAdjacentHTML("beforeend",requiredDocumentTemplate(value)); }
function prepareNewOrganisme() { const form = $("organisme-form"); form.reset(); form.elements.organisme_id.value = ""; form.elements.code.readOnly = true; form.elements.actif.checked = true; form.elements.taux_prise_en_charge.value="0"; $("organisme-dialog-title").textContent = "Nouvel organisme"; $("organisme-submit").textContent = "Créer l'organisme"; $("required-documents").innerHTML = ""; addRequiredDocument(); }
function prepareNewClient(){const f=$("client-form");f.reset();f.elements.client_id.value="";f.elements.actif.checked=true;$("client-dialog-title").textContent="Nouveau client";}
function prepareNewCard(){const f=$("carte-form");f.reset();f.elements.carte_id.value="";f.elements.client_id_select.disabled=false;f.elements.actif.checked=true;$("carte-dialog-title").textContent="Nouvelle carte";}
function prepareNewAccount(){const f=$("account-form");f.reset();f.elements.compte_id.value="";f.elements.actif.checked=true;$("account-dialog-title").textContent="Nouveau compte";}
function editAccount(id){const a=state.accounts.find(i=>i.id===id);if(!a)return;const f=$("account-form");f.reset();for(const k of ["compte_id","code","nom","role","poste_id","caisse"])if(f.elements[k])f.elements[k].value=k==="compte_id"?a.id:(a[k]||"");f.elements.actif.checked=a.actif;$("account-dialog-title").textContent="Modifier le compte";$("compte-dialog").showModal()}
function editClient(id){const c=state.loyaltyClients.find((i)=>i.id===id);if(!c)return;const f=$("client-form");f.reset();f.elements.client_id.value=c.id;f.elements.code.value=c.code;f.elements.nom.value=c.nom;f.elements.prenom.value=c.prenom;f.elements.telephone.value=c.telephone;f.elements.email.value=c.email;f.elements.actif.checked=c.actif;$("client-dialog-title").textContent="Modifier le client";$("client-dialog").showModal();}
function editCard(id){const c=state.loyaltyCards.find((i)=>i.id===id);if(!c)return;const f=$("carte-form");f.reset();f.elements.carte_id.value=c.id;f.elements.client_id_select.value=c.client_id;f.elements.client_id_select.disabled=true;f.elements.type_carte.value=c.type_carte;f.elements.actif.checked=c.actif;$("carte-dialog-title").textContent="Modifier la carte";$("carte-dialog").showModal();}
function editOrganisme(id) {
  const item = state.organismes.find((organisme) => organisme.id === id); if (!item) return;
  const form = $("organisme-form"); form.reset(); form.elements.organisme_id.value = item.id; form.elements.code.value = item.code; form.elements.code.readOnly = false; form.elements.nom.value = item.nom; form.elements.type_organisme.value = item.type_organisme; form.elements.taux_prise_en_charge.value=item.taux_prise_en_charge; form.elements.actif.checked = item.actif; $("required-documents").innerHTML = ""; item.documents_requis.forEach(addRequiredDocument); if (!item.documents_requis.length) addRequiredDocument(); $("organisme-dialog-title").textContent = "Modifier l'organisme"; $("organisme-submit").textContent = "Enregistrer les modifications"; $("organisme-dialog").showModal();
}
function viewOrganisme(id) {
  const item = state.organismes.find((organisme) => organisme.id === id); if (!item) return;
  showDetail(item.nom, [["Code",item.code],["Type",item.type_organisme.replace("_"," ")],["Taux",`${Number(item.taux_prise_en_charge).toLocaleString("fr-FR")} %`],["État",item.actif ? "ACTIF" : "INACTIF"],["Documents / informations requis",item.documents_requis.join(" · ") || "AUCUN"]]);
}
function prepareNewTariff() { const form = $("tariff-form"); form.reset(); form.elements.tarif_id.value = ""; form.elements.fournisseur_id.disabled = false; form.elements.conditionnement_id.disabled = false; $("tariff-dialog-title").textContent = "Définir un tarif fournisseur"; $("tariff-submit").textContent = "Enregistrer le tarif"; }
function editTariff(id) {
  const item = state.tariffs.find((tarif) => tarif.id === id); if (!item) return;
  const form = $("tariff-form"); form.elements.tarif_id.value = item.id; form.elements.fournisseur_id.value = item.fournisseur_id; form.elements.conditionnement_id.value = item.conditionnement_id; form.elements.fournisseur_id.disabled = true; form.elements.conditionnement_id.disabled = true; form.elements.prix_achat.value = item.prix_achat; form.elements.reference_fournisseur.value = item.reference_fournisseur; $("tariff-dialog-title").textContent = "Modifier le tarif fournisseur"; $("tariff-submit").textContent = "Enregistrer les modifications"; $("tarif-dialog").showModal();
}
function editSupplier(id) {
  const item = state.suppliers.find((s) => s.id === id); if (!item) return;
  const form = $("supplier-form"); form.elements.fournisseur_id.value = item.id; form.elements.code.value = item.code; form.elements.raison_sociale.value = item.raison_sociale; form.elements.telephone.value = item.telephone; form.elements.email.value = item.email; form.elements.actif.checked = item.actif; $("supplier-dialog-title").textContent = "Modifier le fournisseur"; $("supplier-submit").textContent = "Enregistrer les modifications"; $("fournisseur-dialog").showModal();
}

function purchaseLineTemplate() {
  return `<tr data-conditionnement-id=""><td><input class="line-product" placeholder="SAISIR 3 CARACTÈRES…" autocomplete="off" required></td><td><input class="line-cip7" readonly></td><td><input class="line-ordered numeric" type="number" min="1" value="1" required></td><td><input class="line-received numeric" type="number" min="0" value="1" required></td><td><input class="line-lot" maxlength="100" required></td><td><input class="line-expiry" type="date" required></td><td><input class="line-price numeric" type="number" min="1" step="1" required></td><td><strong class="line-total">0 FCFA</strong></td><td><button type="button" class="remove-line" aria-label="Supprimer">×</button></td></tr>`;
}
function addPurchaseLine() {
  $("purchase-lines").insertAdjacentHTML("beforeend", purchaseLineTemplate());
  $("purchase-lines").lastElementChild.querySelector(".line-product").focus();
}
function prepareNewPurchase() {
  const form = $("purchase-form"); form.reset(); $("purchase-lines").innerHTML = "";
  const today = new Date().toISOString().slice(0,10);
  form.elements.date_commande.value = today; form.elements.date_arrivee.value = today;
  addPurchaseLine(); updatePurchaseTotals();
}
function updatePurchaseTotals() {
  let grandTotal = 0;
  $("purchase-lines").querySelectorAll("tr").forEach((row) => {
    const total = Number(row.querySelector(".line-received").value || 0) * Number(row.querySelector(".line-price").value || 0);
    row.querySelector(".line-total").textContent = money(total); grandTotal += total;
  });
  $("purchase-grand-total").textContent = money(grandTotal);
}
function searchArticles(term) {
  const needle = term.trim().toLowerCase();
  const rows = state.articles.filter((item) => item.designation.toLowerCase().startsWith(needle) || item.cip7.startsWith(needle) || item.reference.toLowerCase().includes(needle) || item.code.toLowerCase().includes(needle));
  $("article-search-results").innerHTML = rows.length ? rows.map((item) => `<button type="button" class="search-result" data-pick-article="${item.id}"><span><strong>${safe(item.designation)}</strong><small>${safe(item.libelle)}</small></span><span><b>CIP7 ${safe(item.cip7 || "—")}</b><small>${safe(item.code)}</small></span></button>`).join("") : '<div class="list-placeholder">Aucun produit correspondant.</div>';
}
function openArticleSearch(row, term) {
  activePurchaseRow = row; const input = $("article-search-modal"); input.value = term;
  searchArticles(term); $("article-search-dialog").showModal();
  requestAnimationFrame(() => { input.focus(); input.setSelectionRange(input.value.length,input.value.length); });
}
function pickArticle(id) {
  const article = state.articles.find((item) => item.id === id); if (!article || !activePurchaseRow) return;
  activePurchaseRow.dataset.conditionnementId = article.id;
  activePurchaseRow.querySelector(".line-product").value = `${article.designation} — ${article.libelle}`;
  activePurchaseRow.querySelector(".line-cip7").value = article.cip7 || "";
  const supplierId = $("purchase-form").elements.fournisseur_id.value;
  const tariff = state.tariffs.find((item) => item.fournisseur_id === supplierId && item.conditionnement_id === article.id);
  activePurchaseRow.querySelector(".line-price").value = tariff?.prix_achat || "";
  $("article-search-dialog").close(); updatePurchaseTotals(); activePurchaseRow.querySelector(".line-ordered").focus();
}

$("product-type").addEventListener("change", (event) => setProductKind(event.target.value));
$("product-cnamgs").addEventListener("change", toggleCnamgsRate);
$("product-principle").addEventListener("change", async (event) => {
  if (event.target.value !== "__new__") return;
  const libelle = window.prompt("Nom du nouveau principe actif :");
  if (!libelle?.trim()) { event.target.value = state.principles[0]?.id || ""; return; }
  try { const created = await request("/catalogue/principes-actifs",{method:"POST",body:JSON.stringify({libelle})}); await loadAll(); $("product-principle").value = created.id; } catch(error) { flash(error.message,"error"); }
});
$("product-brand").addEventListener("change", async (event) => {
  if (event.target.value !== "__new__") return;
  const libelle = window.prompt("Nom de la nouvelle marque :");
  if (!libelle?.trim()) { event.target.value = state.brands[0]?.id || ""; return; }
  try { const created = await request("/catalogue/marques",{method:"POST",body:JSON.stringify({libelle})}); await loadAll(); $("product-brand").value = created.id; } catch(error) { flash(error.message,"error"); }
});
$("product-search").addEventListener("input", renderProducts);
$("products-table").addEventListener("click", (event) => {
  const edit = event.target.closest("[data-edit-product]"); const view = event.target.closest("[data-view-product]");
  if (edit) editProduct(edit.dataset.editProduct, edit.dataset.editPack);
  if (view) viewProduct(view.dataset.viewProduct, view.dataset.viewPack);
});
document.querySelectorAll("tbody").forEach((body) => {
  body.addEventListener("click", (event) => {
    const row = event.target.closest("tr"); if (!row || row.classList.contains("empty-row")) return;
    body.querySelectorAll(".row-selected").forEach((item) => item.classList.remove("row-selected"));
    row.classList.add("row-selected");
  });
  body.addEventListener("dblclick", (event) => {
    if (event.target.closest("button,input,select,a")) return;
    const row = event.target.closest("tr");
    const action = row?.querySelector("[data-edit-product],[data-edit-supplier],[data-edit-tariff],[data-edit-organisme],[data-edit-client],[data-edit-card],[data-edit-account],[data-view-purchase]");
    action?.click();
  });
});
$("suppliers-table").addEventListener("click", (event) => {
  const edit = event.target.closest("[data-edit-supplier]"); const view = event.target.closest("[data-view-supplier]");
  if (edit) editSupplier(edit.dataset.editSupplier); if (view) viewSupplier(view.dataset.viewSupplier);
});
$("tariffs-table").addEventListener("click", (event) => { const edit = event.target.closest("[data-edit-tariff]"); if (edit) editTariff(edit.dataset.editTariff); });
$("organismes-table").addEventListener("click", (event) => { const view = event.target.closest("[data-view-organisme]"); const edit = event.target.closest("[data-edit-organisme]"); if (view) viewOrganisme(view.dataset.viewOrganisme); if (edit) editOrganisme(edit.dataset.editOrganisme); });
$("loyalty-clients-table").addEventListener("click",(event)=>{const b=event.target.closest("[data-edit-client]");if(b)editClient(b.dataset.editClient);});
$("loyalty-cards-table").addEventListener("click",(event)=>{const e=event.target.closest("[data-edit-card]");const p=event.target.closest("[data-points-card]");if(e)editCard(e.dataset.editCard);if(p){const f=$("points-form");f.reset();f.elements.carte_id.value=p.dataset.pointsCard;$("points-dialog").showModal();}});
$("accounts-table").addEventListener("click",e=>{const b=e.target.closest("[data-edit-account]");if(b)editAccount(b.dataset.editAccount)});
$("purchases-table").addEventListener("click", (event) => { const view = event.target.closest("[data-view-purchase]"); if (view) viewPurchase(view.dataset.viewPurchase); });
$("add-required-document").addEventListener("click", () => addRequiredDocument());
$("required-documents").addEventListener("click", (event) => { const remove = event.target.closest(".remove-document"); if (!remove) return; remove.closest(".document-row").remove(); if (!$("required-documents").children.length) addRequiredDocument(); });
$("add-purchase-line").addEventListener("click", addPurchaseLine);
$("purchase-lines").addEventListener("input", (event) => {
  const row = event.target.closest("tr");
  if (event.target.classList.contains("line-product") && event.target.value.trim().length >= 3) {
    row.dataset.conditionnementId = ""; openArticleSearch(row,event.target.value);
  }
  updatePurchaseTotals();
});
$("purchase-lines").addEventListener("click", (event) => {
  const remove = event.target.closest(".remove-line"); if (!remove) return;
  remove.closest("tr").remove(); if (!$("purchase-lines").children.length) addPurchaseLine(); updatePurchaseTotals();
});
$("article-search-modal").addEventListener("input", (event) => searchArticles(event.target.value));
$("article-search-results").addEventListener("click", (event) => { const choice = event.target.closest("[data-pick-article]"); if (choice) pickArticle(choice.dataset.pickArticle); });

document.addEventListener("input", (event) => {
  const input = event.target;
  if (!(input instanceof HTMLInputElement) && !(input instanceof HTMLTextAreaElement)) return;
  if (input.type === "email" || input.type === "date" || input.type === "number" || input.dataset.preserveCase !== undefined) return;
  const start = input.selectionStart; const end = input.selectionEnd; input.value = input.value.toUpperCase();
  if (start !== null && end !== null) input.setSelectionRange(start,end);
});

$("product-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const target = event.currentTarget; const form = new FormData(target); const type = target.elements.type.value; const productId = form.get("product_id"); const packId = form.get("conditionnement_id");
  try {
    const covered = target.elements.pris_en_charge_cnamgs.checked;
    const productPayload = {reference:form.get("reference"),designation:form.get("designation"),cip7:form.get("cip7"),pris_en_charge_cnamgs:covered,taux_prise_en_charge_cnamgs:covered ? Number(form.get("taux_prise_en_charge_cnamgs")) : 0};
    if (type === "medicament") productPayload.principe_actif_id = form.get("principe_actif_id"); else productPayload.marque_id = form.get("marque_id");
    const packPayload = {code:form.get("code"),libelle:form.get("libelle"),prix_vente:Number(form.get("prix_vente"))};
    if (productId) {
      const updatePayload = {reference:productPayload.reference,designation:productPayload.designation,cip7:productPayload.cip7,information:"",pris_en_charge_cnamgs:productPayload.pris_en_charge_cnamgs,taux_prise_en_charge_cnamgs:productPayload.taux_prise_en_charge_cnamgs};
      if (type === "medicament") updatePayload.principe_actif_id = productPayload.principe_actif_id;
      else updatePayload.marque_id = productPayload.marque_id;
      await request(`/catalogue/produits/${productId}`,{method:"PUT",body:JSON.stringify(updatePayload)});
      const initialPack = JSON.parse(target.dataset.packSnapshot || "null");
      if (!initialPack || JSON.stringify(packPayload) !== JSON.stringify(initialPack)) await request(`/catalogue/conditionnements/${packId}`,{method:"PUT",body:JSON.stringify(packPayload)});
    } else {
      const product = await request(`/catalogue/${type === "medicament" ? "medicaments" : "cosmetiques"}`,{method:"POST",body:JSON.stringify(productPayload)});
      await request(`/catalogue/produits/${product.id}/conditionnements`,{method:"POST",body:JSON.stringify(packPayload)});
    }
    await finishSave(target,productId ? "Produit et conditionnement modifiés." : "Produit et conditionnement créés.");
  } catch (error) { flash(error.message, "error"); }
});
$("supplier-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const target = event.currentTarget; const form = new FormData(target); const id = form.get("fournisseur_id"); const payload = {code:form.get("code"),raison_sociale:form.get("raison_sociale"),telephone:form.get("telephone"),email:form.get("email")}; if (id) payload.actif = form.get("actif") === "on";
  try { await request(id ? `/achats/fournisseurs/${id}` : "/achats/fournisseurs",{method:id ? "PUT" : "POST",body:JSON.stringify(payload)}); await finishSave(target,id ? "Fournisseur modifié." : "Fournisseur créé."); } catch(error) { flash(error.message,"error"); }
});
$("tariff-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const target = event.currentTarget; const form = new FormData(target); const fields = target.elements;
  try { await request("/achats/tarifs",{method:"PUT",body:JSON.stringify({fournisseur_id:fields.fournisseur_id.value,conditionnement_id:fields.conditionnement_id.value,prix_achat:Number(form.get("prix_achat")),reference_fournisseur:form.get("reference_fournisseur")})}); await finishSave(target,form.get("tarif_id") ? "Tarif fournisseur modifié." : "Tarif fournisseur enregistré."); } catch(error) { flash(error.message,"error"); }
});
function toggleCatalogueResetWarning() {
  const destructive = $("catalogue-import-mode").value === "MISE_EN_PLACE";
  $("catalogue-reset-warning").classList.toggle("hidden", !destructive);
  const confirmation = $("catalogue-import-form").elements.confirmer_mise_en_place;
  confirmation.required = destructive;
  if (!destructive) confirmation.checked = false;
}
$("catalogue-import-mode").addEventListener("change", toggleCatalogueResetWarning);
$("catalogue-import-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = event.currentTarget; const data = new FormData(form); const file = data.get("catalogue");
  if (!(file instanceof File) || !file.size) return flash("Sélectionnez un catalogue CSV.","error");
  const destructive = data.get("mode") === "MISE_EN_PLACE";
  if (destructive && !form.elements.confirmer_mise_en_place.checked) return flash("Confirmez le remplacement complet du catalogue.","error");
  if (destructive && !window.confirm("Cette mise en place supprimera le catalogue, les stocks, les commandes et les préparations existants. Continuer ?")) return;
  const button = $("catalogue-import-submit"); button.disabled = true; button.textContent = "Import en cours…";
  try {
    const result = await request("/achats/catalogues/import",{method:"POST",body:JSON.stringify({fournisseur_id:data.get("fournisseur_id"),mode:data.get("mode"),contenu_csv:await file.text(),confirmer_mise_en_place:destructive})});
    const warning = result.lignes_ignorees ? ` · ${result.lignes_ignorees} ligne(s) ignorée(s)` : "";
    const reset = result.produits_supprimes ? `${result.produits_supprimes} ancien(s) produit(s) supprimé(s) · ` : "";
    await finishSave(form,`${reset}${result.produits_crees} produit(s) créé(s), ${result.produits_mis_a_jour} tarif(s) de vente mis à jour, ${result.tarifs_enregistres} tarif(s) fournisseur enregistré(s)${warning}.`);
  } catch(error) { flash(error.message,"error"); }
  finally { button.disabled=false; button.textContent="Importer le catalogue"; toggleCatalogueResetWarning(); }
});
$("purchase-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const target = event.currentTarget; const form = new FormData(target);
  try {
    const lignes = [...$("purchase-lines").querySelectorAll("tr")].map((row) => {
      if (!row.dataset.conditionnementId) throw new Error("Sélectionnez chaque produit dans la fenêtre de recherche.");
      return {conditionnement_id:row.dataset.conditionnementId,quantite_commandee:Number(row.querySelector(".line-ordered").value),quantite_recue:Number(row.querySelector(".line-received").value),numero_lot:row.querySelector(".line-lot").value,date_expiration:row.querySelector(".line-expiry").value,prix_unitaire:Number(row.querySelector(".line-price").value)};
    });
    const purchase = await request("/achats/commandes-receptions",{method:"POST",body:JSON.stringify({fournisseur_id:form.get("fournisseur_id"),emplacement_id:form.get("emplacement_id"),date_commande:form.get("date_commande"),date_arrivee:form.get("date_arrivee"),numero_fournisseur:form.get("numero_fournisseur"),lignes})});
    await finishSave(target,`Commande ${purchase.numero_interne} validée. Stock et tarifs actualisés.`);
  } catch(error) { flash(error.message,"error"); }
});
$("location-form").addEventListener("submit", async (event) => { event.preventDefault(); const target=event.currentTarget,form=new FormData(target); try { await request("/stock/emplacements",{method:"POST",body:JSON.stringify({code:form.get("code"),libelle:form.get("libelle"),autorise_vente:form.get("autorise_vente") === "on"})}); await finishSave(target,"Emplacement créé."); } catch(error){flash(error.message,"error");} });
$("reception-form").addEventListener("submit", async (event) => { event.preventDefault(); const target=event.currentTarget,form=new FormData(target); try { await request("/stock/receptions",{method:"POST",body:JSON.stringify({conditionnement_id:form.get("conditionnement_id"),numero_lot:form.get("numero_lot"),date_expiration:form.get("date_expiration"),emplacement_id:form.get("emplacement_id"),quantite:Number(form.get("quantite")),motif:form.get("motif")})}); await finishSave(target,"Lot réceptionné et stock mis à jour."); } catch(error){flash(error.message,"error");} });
$("poste-form").addEventListener("submit", async (event) => { event.preventDefault(); const target=event.currentTarget,form=new FormData(target); try { await request("/ventes/postes",{method:"POST",body:JSON.stringify({code:form.get("code"),secteur_id:crypto.randomUUID(),emplacement_id:form.get("emplacement_id"),caisse_id:form.get("caisse_id")})}); await finishSave(target,"Poste de vente créé."); } catch(error){flash(error.message,"error");} });
$("caisse-form").addEventListener("submit",async e=>{e.preventDefault();const target=e.currentTarget,d=new FormData(target);try{await request("/administration/caisses",{method:"POST",body:JSON.stringify({code:d.get("code"),libelle:d.get("libelle")})});await finishSave(target,"Caisse créée.")}catch(error){flash(error.message,"error")}});
$("organisme-form").addEventListener("submit", async (event) => { event.preventDefault(); const target=event.currentTarget,form = new FormData(target); const id = form.get("organisme_id"); const documents_requis = [...$("required-documents").querySelectorAll(".required-document")].map((input) => input.value.trim()).filter(Boolean); const payload = {code:form.get("code"),nom:form.get("nom"),type_organisme:form.get("type_organisme"),taux_prise_en_charge:Number(form.get("taux_prise_en_charge")),documents_requis}; if (id) payload.actif = target.elements.actif.checked; try { await request(id ? `/prises-en-charge/organismes/${id}` : "/prises-en-charge/organismes",{method:id ? "PUT" : "POST",body:JSON.stringify(payload)}); await finishSave(target,id ? "Organisme modifié." : "Organisme et pièces requises enregistrés."); } catch(error){flash(error.message,"error");} });
$("client-form").addEventListener("submit",async(event)=>{event.preventDefault();const f=event.currentTarget,d=new FormData(f),id=d.get("client_id"),payload={nom:d.get("nom"),prenom:d.get("prenom"),telephone:d.get("telephone"),email:d.get("email")};if(id)payload.actif=f.elements.actif.checked;try{await request(id?`/fidelite/clients/${id}`:"/fidelite/clients",{method:id?"PUT":"POST",body:JSON.stringify(payload)});await finishSave(f,id?"Client modifié.":"Client créé.");}catch(error){flash(error.message,"error");}});
$("carte-form").addEventListener("submit",async(event)=>{event.preventDefault();const f=event.currentTarget,d=new FormData(f),id=d.get("carte_id"),payload={type_carte:d.get("type_carte")};if(id)payload.actif=f.elements.actif.checked;else payload.client_id=f.elements.client_id_select.value;try{await request(id?`/fidelite/cartes/${id}`:"/fidelite/cartes",{method:id?"PUT":"POST",body:JSON.stringify(payload)});await finishSave(f,id?"Carte modifiée.":"Carte créée.");}catch(error){flash(error.message,"error");}});
$("points-form").addEventListener("submit",async(event)=>{event.preventDefault();const f=event.currentTarget,d=new FormData(f);try{await request(`/fidelite/cartes/${d.get("carte_id")}/mouvements`,{method:"POST",body:JSON.stringify({points:Number(d.get("points")),motif:d.get("motif")})});await finishSave(f,"Solde de points actualisé.");}catch(error){flash(error.message,"error");}});
$("account-form").addEventListener("submit",async e=>{e.preventDefault();const f=e.currentTarget,d=new FormData(f),id=d.get("compte_id"),payload={code:d.get("code"),nom:d.get("nom"),role:d.get("role"),poste_id:d.get("poste_id")||null,caisse:d.get("caisse")};if(id)payload.actif=f.elements.actif.checked;try{await request(id?`/administration/comptes/${id}`:"/administration/comptes",{method:id?"PUT":"POST",body:JSON.stringify(payload)});await finishSave(f,id?"Compte modifié.":"Compte créé.")}catch(error){flash(error.message,"error")}});

$("demo-data").addEventListener("click", async () => {
  if (state.products.length || state.locations.length || state.postes.length) return flash("Des données existent déjà. Ajoutez les éléments manquants avec les formulaires.","error");
  const button = $("demo-data"); button.disabled = true; button.textContent = "Création en cours…";
  try {
    await request("/stock/emplacements",{method:"POST",body:JSON.stringify({code:"RESERVE",libelle:"Réserve principale",autorise_vente:false})});
    const rayon = await request("/stock/emplacements",{method:"POST",body:JSON.stringify({code:"RAYON-01",libelle:"Rayon de vente principal",autorise_vente:true})});
    const supplier = await request("/achats/fournisseurs",{method:"POST",body:JSON.stringify({code:"FOUR-001",raison_sociale:"Pharma Distribution Gabon",telephone:"+241 01 23 45 67",email:"commandes@pharmadistribution.ga"})});
    const demos = [
      ["medicaments",{reference:"",designation:"PARACÉTAMOL 500 MG",cip7:"3232018",principe_actif:"Paracétamol"},{code:"",libelle:"BOÎTE DE 20 COMPRIMÉS",prix_vente:1500},"LOT-PARA-001","2028-12-31",100,900],
      ["medicaments",{reference:"",designation:"AMOXICILLINE 500 MG",cip7:"3307199",principe_actif:"Amoxicilline"},{code:"",libelle:"BOÎTE DE 12 GÉLULES",prix_vente:4500},"LOT-AMOX-001","2028-06-30",60,3100],
      ["cosmetiques",{reference:"",designation:"LAIT CORPOREL HYDRATANT",cip7:"7654321",marque:"NEOCARE"},{code:"",libelle:"FLACON DE 250 ML",prix_vente:4000},"LOT-LAIT-001","2029-03-31",40,2600]
    ];
    for (const [kind,productPayload,pack,lot,expiry,qty,purchasePrice] of demos) {
      const product = await request(`/catalogue/${kind}`,{method:"POST",body:JSON.stringify(productPayload)});
      const item = await request(`/catalogue/produits/${product.id}/conditionnements`,{method:"POST",body:JSON.stringify(pack)});
      await request("/achats/tarifs",{method:"PUT",body:JSON.stringify({fournisseur_id:supplier.id,conditionnement_id:item.id,prix_achat:purchasePrice,reference_fournisseur:`PDG-${item.code}`})});
      await request("/stock/receptions",{method:"POST",body:JSON.stringify({conditionnement_id:item.id,numero_lot:lot,date_expiration:expiry,emplacement_id:rayon.id,quantite:qty,motif:"Données de démonstration"})});
    }
    await request("/ventes/postes",{method:"POST",body:JSON.stringify({code:"POSTE-01",secteur_id:crypto.randomUUID(),emplacement_id:rayon.id})});
    await loadAll(); flash("Données de démonstration créées. Catalogue, achats et console sont prêts.");
  } catch(error){flash(error.message,"error");} finally {button.disabled=false;button.textContent="Charger les données de démonstration";}
});

$("today").textContent = new Intl.DateTimeFormat("fr-FR",{dateStyle:"long"}).format(new Date());
setProductKind("medicament");
showView(activeView);
loadAll().then(() => showView(activeView)).catch((error) => flash(error.message,"error"));
